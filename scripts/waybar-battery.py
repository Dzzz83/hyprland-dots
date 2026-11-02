#!/usr/bin/env python3
"""Stream battery, AC and Lenovo power-profile changes to Waybar."""

import html
import json
import math
import sys

from gi.repository import GLib


PROFILE_NAMES = {
    "performance": "Performance",
    "balanced": "Normal / Balanced",
    "low-power": "Quiet / Power saving",
    "quiet": "Quiet / Power saving",
    "custom": "Custom",
}
STATE_NAMES = {
    1: "Charging", 2: "Discharging", 3: "Empty", 4: "Fully charged",
    5: "Charging paused", 6: "Pending discharge",
}


def indicator(percentage, state, is_ac_online, profile, seconds=0, is_present=True):
    if not is_present or not math.isfinite(percentage) or not 0 <= percentage <= 100:
        return {"text": "  Battery unavailable", "class": ["unavailable"],
                "tooltip": "Battery information is unavailable"}
    capacity = round(percentage)
    classes = []
    if state == 1:
        icon, status = "", "charging"
    elif is_ac_online:
        icon, status = "", "plugged"
    elif percentage <= 30:
        icon, status = "", "discharging"
    else:
        icons = ("", "", "", "", "")
        icon, status = icons[min(int(percentage // 20), 4)], "discharging"
    classes.append(status)
    if state != 1 and not is_ac_online and percentage <= 30:
        classes.append("critical" if percentage <= 15 else "warning")
    is_power_saving = profile in ("low-power", "quiet")
    if is_power_saving:
        classes.append("power-saver")
    text = f"{icon} {' ' if is_power_saving else ''}{capacity}%"
    details = [f"Battery: {capacity}% — {STATE_NAMES.get(state, 'Status unknown')}",
               "AC connected" if is_ac_online else "Running on battery",
               f"Power mode: {PROFILE_NAMES.get(profile, 'Unknown')}"]
    if seconds > 0 and state in (1, 2):
        minutes = max(1, round(seconds / 60))
        estimate = "until full" if state == 1 else "remaining"
        details.append(f"{minutes // 60}h {minutes % 60:02d}m {estimate}")
    return {"text": text, "class": classes, "tooltip": html.escape("\n".join(details))}


def main():
    from power_backend import PowerMonitor

    loop = GLib.MainLoop()
    previous = None

    def render(state):
        nonlocal previous
        value = indicator(state.percentage, state.state, state.is_ac_online,
                          state.profile, state.seconds, state.is_present)
        if value != previous:
            try:
                print(json.dumps(value, ensure_ascii=False), flush=True)
            except BrokenPipeError:
                loop.quit()
            previous = value

    monitor = PowerMonitor(render)
    try:
        loop.run()
    finally:
        monitor.close()


if __name__ == "__main__":
    try:
        main()
    except (GLib.Error, OSError) as error:
        print(json.dumps(indicator(float("nan"), 0, False, "unknown")), flush=True)
        print(f"Battery indicator: {error}", file=sys.stderr)
        sys.exit(1)
