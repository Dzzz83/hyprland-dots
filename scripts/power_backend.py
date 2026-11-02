"""Shared battery observation and Lenovo power controls for Waybar and its popup."""

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time

from gi.repository import Gio, GLib

UPOWER = "org.freedesktop.UPower"
ROOT = "/org/freedesktop/UPower"
DEVICE = UPOWER + ".Device"
PROFILE_PATH = Path("/sys/firmware/acpi/platform_profile")
CHARGE_PATH = Path("/sys/class/power_supply/BAT0/charge_types")
BATTERY_PATH = CHARGE_PATH.parent
CHARGE_MODES = {"Standard": "standard", "Fast": "fast", "Long_Life": "conservation"}
PROFILES = ("low-power", "balanced", "performance")


def charge_mode(text):
    selected = [word[1:-1] for word in text.split() if word.startswith("[") and word.endswith("]")]
    return CHARGE_MODES.get(selected[0], "unknown") if len(selected) == 1 else "unknown"


def duration(seconds):
    minutes = max(1, round(seconds / 60))
    return f"{minutes // 60}h {minutes % 60:02d}m"


def read_charge_mode():
    try:
        return charge_mode(CHARGE_PATH.read_text())
    except OSError:
        return "unknown"


def run_command(arguments, timeout=15):
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "The change was not authorized.")


def set_profile(profile):
    if profile not in PROFILES:
        raise ValueError("Unsupported power profile")
    command_profile = "power-saver" if profile == "low-power" else profile
    run_command(["/usr/bin/powerprofilesctl", "set", command_profile])
    if PROFILE_PATH.read_text().strip() != profile:
        raise RuntimeError("The firmware did not accept that power mode.")


def set_conservation_enabled(is_enabled):
    battery = Gio.DBusProxy.new_for_bus_sync(
        Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
        UPOWER, ROOT + "/devices/battery_BAT0", DEVICE, None,
    )
    battery.call_sync("EnableChargeThreshold", GLib.Variant("(b)", (is_enabled,)),
                      Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, 180000, None)


def _apply_charge_mode(mode):
    # Keep UPower's persistent policy synchronized with the firmware's Long_Life mode.
    set_conservation_enabled(mode == "conservation")
    if mode == "fast":
        run_command(["/usr/bin/pkexec", "/usr/bin/legion_cli", "rapid-charging-enable"], timeout=180)
    elif mode == "standard" and read_charge_mode() != "standard":
        run_command(["/usr/bin/pkexec", "/usr/bin/legion_cli", "rapid-charging-disable"], timeout=180)
    if read_charge_mode() != mode:
        raise RuntimeError("The firmware did not accept that charging mode.")


def set_charge_mode(mode):
    if mode not in ("standard", "fast", "conservation"):
        raise ValueError("Unsupported charging mode")
    previous = read_charge_mode()
    try:
        _apply_charge_mode(mode)
    except Exception as error:
        # Cancelling Fast authentication must not leave Conservation switched off.
        if previous in ("standard", "fast", "conservation") and read_charge_mode() != previous:
            try:
                _apply_charge_mode(previous)
            except Exception as restore_error:
                raise RuntimeError(f"{error}\nCould not restore the previous charging mode: {restore_error}") from error
        raise


def unplugged_estimate(state, seconds, energy_wh, last_sample, now):
    if state == 2 and seconds > 0:
        return f"About {duration(seconds)} remaining", "Based on current battery use"
    if last_sample:
        age_seconds = now - last_sample.get("timestamp", 0)
        rate_w = last_sample.get("rate_w", 0)
        if 0 <= age_seconds < 86400 and math.isfinite(rate_w) and rate_w > 0 and energy_wh > 0:
            age_minutes = max(0, int(age_seconds // 60))
            profile = last_sample.get("profile", "unknown")
            time_label = "remaining" if state == 2 else "if unplugged"
            return (f"About {duration(energy_wh / rate_w * 3600)} {time_label}",
                    f"Last measured use: {age_minutes} min ago · {profile}")
    return "Estimate available after unplugged use", "A brief battery session is needed to measure consumption"


@dataclass
class PowerState:
    percentage: float
    state: int
    is_ac_online: bool
    profile: str
    seconds: int
    is_present: bool
    charging_mode: str
    rate_w: float
    health: float | None
    cycles: int | None
    estimate: str
    estimate_detail: str


class PowerMonitor:
    def __init__(self, on_change, cache_path=None):
        self.on_change = on_change
        self.cache_path = cache_path or Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "hypr/battery-use.json"
        self.last_sample = self.load_sample()
        self.profile = "unknown"
        self.profile_file = None
        self.profile_watch = None
        self.is_refresh_pending = False
        self.adapters = []
        self.root = self.proxy(ROOT, UPOWER)
        self.battery = self.proxy(ROOT + "/devices/battery_BAT0", DEVICE)
        self.root.connect("g-signal", self.devices_changed)
        self.battery.connect("g-properties-changed", self.schedule_refresh)
        self.update_adapters()
        try:
            self.profile_file = PROFILE_PATH.open(encoding="utf-8")
            self.profile_changed()
            self.profile_watch = GLib.io_add_watch(
                self.profile_file.fileno(), GLib.IOCondition.PRI | GLib.IOCondition.ERR,
                self.profile_changed,
            )
        except OSError:
            self.profile = "unknown"

    @staticmethod
    def proxy(path, interface):
        return Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None,
            UPOWER, path, interface, None,
        )

    @staticmethod
    def value(device, name, default):
        value = device.get_cached_property(name)
        return value.unpack() if value is not None else default

    def load_sample(self):
        try:
            sample = json.loads(self.cache_path.read_text())
            if (isinstance(sample, dict)
                    and isinstance(sample.get("timestamp"), (int, float))
                    and isinstance(sample.get("rate_w"), (int, float))
                    and isinstance(sample.get("profile"), str)):
                return sample
        except (OSError, ValueError):
            pass
        return None

    def devices_changed(self, _proxy, _sender, signal, _args):
        if signal in ("DeviceAdded", "DeviceRemoved"):
            self.update_adapters()

    def update_adapters(self):
        paths = self.root.call_sync("EnumerateDevices", None, Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
        self.adapters.clear()
        for path in paths:
            device = self.proxy(path, DEVICE)
            if self.value(device, "Type", 0) == 1:
                device.connect("g-properties-changed", self.schedule_refresh)
                self.adapters.append(device)
        self.schedule_refresh()

    def profile_changed(self, _channel=None, condition=None):
        try:
            if condition and condition & (GLib.IOCondition.HUP | GLib.IOCondition.NVAL):
                raise OSError("Profile interface disconnected")
            self.profile_file.seek(0)
            self.profile = self.profile_file.read().strip()
        except OSError:
            self.profile = "unknown"
            self.schedule_refresh()
            return GLib.SOURCE_REMOVE
        self.schedule_refresh()
        return GLib.SOURCE_CONTINUE

    def schedule_refresh(self, *_args):
        if not self.is_refresh_pending:
            self.is_refresh_pending = True
            GLib.idle_add(self.refresh)

    def refresh(self):
        self.is_refresh_pending = False
        state = self.value(self.battery, "State", 0)
        seconds = self.value(self.battery, "TimeToFull" if state == 1 else "TimeToEmpty", 0)
        energy_wh = self.value(self.battery, "Energy", 0.0)
        rate_w = self.value(self.battery, "EnergyRate", 0.0)
        now = time.time()
        measured_at = self.value(self.battery, "UpdateTime", 0)
        if (state == 2 and math.isfinite(rate_w) and rate_w > 0 and measured_at > 0
                and (not self.last_sample or measured_at != self.last_sample["timestamp"])):
            self.last_sample = {"timestamp": measured_at, "rate_w": rate_w, "profile": self.profile}
            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode="w", dir=self.cache_path.parent,
                                                 prefix=".battery-use-", delete=False) as output:
                    temporary = Path(output.name)
                    try:
                        output.write(json.dumps(self.last_sample))
                        output.close()
                        temporary.replace(self.cache_path)
                    finally:
                        temporary.unlink(missing_ok=True)
            except OSError:
                pass  # Live estimates remain available if the cache cannot be saved.
        estimate, detail = unplugged_estimate(state, seconds, energy_wh, self.last_sample, now)
        try:
            full = float((BATTERY_PATH / "energy_full").read_text())
            design = float((BATTERY_PATH / "energy_full_design").read_text())
            health = full / design * 100 if design > 0 else None
            cycles = int((BATTERY_PATH / "cycle_count").read_text())
        except (OSError, ValueError):
            health, cycles = None, None
        self.on_change(PowerState(
            self.value(self.battery, "Percentage", float("nan")), state,
            any(self.value(adapter, "Online", False) for adapter in self.adapters),
            self.profile, seconds, self.value(self.battery, "IsPresent", False),
            read_charge_mode(), rate_w, health, cycles, estimate, detail,
        ))
        return GLib.SOURCE_REMOVE

    def close(self):
        if self.profile_watch is not None and GLib.MainContext.default().find_source_by_id(self.profile_watch):
            GLib.source_remove(self.profile_watch)
        if self.profile_file is not None:
            self.profile_file.close()
