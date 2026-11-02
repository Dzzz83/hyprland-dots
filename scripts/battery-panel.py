#!/usr/bin/env python3
"""Battery popup matching the desktop's GTK layer-shell controls."""

import math
import os
from pathlib import Path
import signal
import sys
import threading

# gtk4-layer-shell must interpose Wayland symbols before GTK loads them.
if __name__ == "__main__" and "libgtk4-layer-shell.so.0" not in os.environ.get("LD_PRELOAD", ""):
    environment = os.environ.copy()
    environment["LD_PRELOAD"] = "libgtk4-layer-shell.so.0" + (
        ":" + environment["LD_PRELOAD"] if environment.get("LD_PRELOAD") else ""
    )
    os.execve(sys.executable, [sys.executable, "-B", *sys.argv], environment)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
# Load layer-shell before GTK/Wayland so its Wayland hooks are installed first.
from gi.repository import Gtk4LayerShell
from gi.repository import Gdk, Gio, GLib, Gtk

from power_backend import PowerMonitor, PROFILES, duration, set_charge_mode, set_profile

CHARGE_MODES = ("standard", "fast", "conservation")

MODE_NAMES = {"low-power": "Quiet", "quiet": "Quiet", "balanced": "Normal",
              "performance": "Performance", "custom": "Custom"}
STATUS_NAMES = {1: "Charging", 2: "Discharging", 3: "Empty", 4: "Fully charged",
                5: "Charging paused", 6: "Pending discharge"}


def label(text="", css=None):
    widget = Gtk.Label(label=text, xalign=0)
    if css:
        widget.add_css_class(css)
    return widget


class BatteryPopup:
    def __init__(self, app):
        self.state = None
        self.is_rendering = False
        self.is_busy = False
        self.is_authorizing = False
        self.pending_profile = None
        self.pending_charge = None
        provider = Gtk.CssProvider()
        provider.load_from_path(str(Path(__file__).resolve().parents[1] / "waybar/battery-panel.css"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.window = Gtk.ApplicationWindow(application=app, title="Battery")
        Gtk4LayerShell.init_for_window(self.window)
        Gtk4LayerShell.set_namespace(self.window, "battery-panel")
        Gtk4LayerShell.set_layer(self.window, Gtk4LayerShell.Layer.OVERLAY)
        Gtk4LayerShell.set_keyboard_mode(self.window, Gtk4LayerShell.KeyboardMode.NONE)
        Gtk4LayerShell.set_exclusive_zone(self.window, -1)
        for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM,
                     Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
            Gtk4LayerShell.set_anchor(self.window, edge, True)
        self.panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.panel.add_css_class("battery-panel")
        self.panel.set_size_request(330, -1)
        self.panel.set_halign(Gtk.Align.END)
        self.panel.set_valign(Gtk.Align.START)
        self.panel.set_margin_top(34)
        self.panel.set_margin_end(142)
        overlay = Gtk.Overlay()
        overlay.set_child(Gtk.DrawingArea())
        overlay.add_overlay(self.panel)
        self.window.set_child(overlay)

        summary = self.section("battery-header")
        heading = Gtk.Box(spacing=12)
        icon = Gtk.Image.new_from_icon_name("battery-good-symbolic")
        icon.set_pixel_size(28)
        icon.add_css_class("accent")
        heading.append(icon)
        title = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        title.set_hexpand(True)
        title.append(label("Battery", "header-title"))
        self.subtitle = label("Reading…", "subtitle")
        title.append(self.subtitle)
        heading.append(title)
        self.percentage = label("—", "battery-percentage")
        heading.append(self.percentage)
        summary.append(heading)
        self.level = Gtk.LevelBar(min_value=0, max_value=100)
        summary.append(self.level)
        self.estimate = label("", "estimate")
        self.estimate.set_wrap(True)
        self.estimate.set_max_width_chars(34)
        summary.append(self.estimate)
        self.separator()

        power = self.section()
        power.append(label("Power mode", "section-title"))
        self.mode = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 2, 1)
        self.mode.set_draw_value(False)
        self.mode.set_round_digits(0)
        self.mode.update_property([Gtk.AccessibleProperty.LABEL], ["Lenovo mode"])
        for position, name in enumerate(("Quiet", "Normal", "Performance")):
            self.mode.add_mark(position, Gtk.PositionType.BOTTOM, name)
        self.mode.connect("value-changed", self.mode_changed)
        power.append(self.mode)
        self.separator()

        charging = self.section()
        charging.append(label("Charging mode", "section-title"))
        self.charge_mode = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 2, 1)
        self.charge_mode.set_draw_value(False)
        self.charge_mode.set_round_digits(0)
        self.charge_mode.update_property([Gtk.AccessibleProperty.LABEL], ["Charging mode"])
        for position, name in enumerate(("Standard", "Fast", "Conservation")):
            self.charge_mode.add_mark(position, Gtk.PositionType.BOTTOM, name)
        self.charge_mode.set_tooltip_text("Conservation limits charging to around 60% to preserve battery health")
        self.charge_mode.connect("value-changed", self.charge_changed)
        charging.append(self.charge_mode)
        self.message = label("", "status-message")
        self.message.set_wrap(True)
        self.message.set_max_width_chars(36)
        self.message.set_visible(False)
        charging.append(self.message)

        self.setup_dismissal()
        self.monitor = PowerMonitor(self.render)

    def section(self, css="battery-section"):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.add_css_class(css)
        self.panel.append(box)
        return box

    def separator(self):
        self.panel.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

    def render(self, state):
        self.state = state
        self.is_rendering = True
        try:
            is_available = state.is_present and math.isfinite(state.percentage)
            self.percentage.set_label(f"{round(state.percentage)}%" if is_available else "Unavailable")
            self.level.set_value(state.percentage if is_available else 0)
            status = STATUS_NAMES.get(state.state, "Status unknown")
            if state.is_ac_online and state.state != 1:
                status = "Plugged in · " + status.lower()
            self.subtitle.set_label(status if is_available else "No battery detected")
            estimate = ""
            if is_available:
                if state.state == 1 and state.seconds > 0:
                    estimate = f"{duration(state.seconds)} until full"
                elif state.estimate.startswith("About "):
                    estimate = state.estimate.removeprefix("About ")
                if state.state in (1, 2) and state.rate_w > 0:
                    estimate = " · ".join(filter(None, (estimate, f"{state.rate_w:.1f} W")))
            self.estimate.set_label(estimate)
            self.estimate.set_visible(bool(estimate))
            self.estimate.set_tooltip_text(state.estimate_detail)
            self.mode.set_tooltip_text(MODE_NAMES.get(state.profile, "Unknown"))
            if self.pending_profile is None and state.profile in PROFILES:
                self.mode.set_value(PROFILES.index(state.profile))
            if self.pending_charge is None and state.charging_mode in CHARGE_MODES:
                self.charge_mode.set_value(CHARGE_MODES.index(state.charging_mode))
            details = []
            if state.health is not None:
                details.append(f"Health: {state.health:.0f}%")
            if state.cycles is not None:
                details.append(f"{state.cycles} cycles")
            self.percentage.set_tooltip_text(" · ".join(details) or "Battery health unavailable")
            self.update_sensitivity()
        finally:
            self.is_rendering = False

    def update_sensitivity(self):
        self.mode.set_sensitive(not self.is_busy)
        self.charge_mode.set_sensitive(not self.is_busy and self.state is not None
                                       and self.state.charging_mode in CHARGE_MODES)

    def mode_changed(self, scale):
        if self.is_rendering or self.is_busy:
            return
        if self.pending_profile is not None:
            GLib.source_remove(self.pending_profile)
        target = PROFILES[round(scale.get_value())]
        def apply():
            self.pending_profile = None
            self.apply_profile(target)
            return GLib.SOURCE_REMOVE
        self.pending_profile = GLib.timeout_add(180, apply)

    def apply_profile(self, target):
        if self.is_busy:
            return
        if self.state is not None and self.state.profile != target:
            self.run_action(lambda: set_profile(target), False)

    def charge_changed(self, scale):
        if self.is_rendering or self.is_busy or self.state is None:
            return
        if self.pending_charge is not None:
            GLib.source_remove(self.pending_charge)
        target = CHARGE_MODES[round(scale.get_value())]
        def apply():
            self.pending_charge = None
            if self.state.charging_mode != target:
                self.run_action(lambda: set_charge_mode(target), True)
            return GLib.SOURCE_REMOVE
        self.pending_charge = GLib.timeout_add(180, apply)

    def run_action(self, action, requires_authentication):
        if self.pending_charge is not None:
            GLib.source_remove(self.pending_charge)
            self.pending_charge = None
        if self.pending_profile is not None:
            GLib.source_remove(self.pending_profile)
            self.pending_profile = None
        self.is_busy = True
        self.update_sensitivity()
        self.message.set_label("Applying…")
        self.message.set_visible(True)
        self.is_authorizing = requires_authentication
        if requires_authentication:
            # Release the overlay and keyboard while the system asks for authentication.
            self.hide()
        def work():
            error = None
            try:
                action()
            except Exception as failure:
                error = str(failure)
            GLib.idle_add(finish, error)
        def finish(error):
            self.is_busy = False
            self.is_authorizing = False
            self.monitor.refresh()
            self.message.set_label(error[-600:] if error else "Setting applied")
            self.message.set_visible(True)
            if requires_authentication:
                self.show()
            return GLib.SOURCE_REMOVE
        threading.Thread(target=work, daemon=True).start()

    def setup_dismissal(self):
        key = Gtk.EventControllerKey()
        key.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        def pressed(_controller, keyval, _keycode, _state):
            if keyval == Gdk.KEY_Escape:
                self.hide()
                return True
            return False
        key.connect("key-pressed", pressed)
        self.window.add_controller(key)
        click = Gtk.GestureClick()
        click.set_button(0)
        click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        def outside(gesture, _count, x, y):
            has_bounds, bounds = self.panel.compute_bounds(self.window)
            if has_bounds and not (bounds.get_x() <= x <= bounds.get_x() + bounds.get_width()
                                   and bounds.get_y() <= y <= bounds.get_y() + bounds.get_height()):
                gesture.set_state(Gtk.EventSequenceState.CLAIMED)
                self.hide()
        click.connect("pressed", outside)
        self.window.add_controller(click)
        self.window.connect("close-request", lambda _window: (self.hide(), True)[1])

    def hide(self):
        self.window.set_visible(False)
        Gtk4LayerShell.set_keyboard_mode(self.window, Gtk4LayerShell.KeyboardMode.NONE)

    def show(self):
        self.monitor.refresh()
        Gtk4LayerShell.set_keyboard_mode(self.window, Gtk4LayerShell.KeyboardMode.EXCLUSIVE)
        self.window.present()

    def toggle(self):
        if not self.is_authorizing:
            self.hide() if self.window.get_visible() else self.show()


def main():
    app = Gtk.Application(application_id="com.local.BatteryPanel")
    app.add_main_option("toggle", 0, GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
                        "Toggle battery controls", None)
    popup = None
    def activate(app):
        nonlocal popup
        if popup is None:
            popup = BatteryPopup(app)
        popup.toggle()
    app.connect("activate", activate)
    app.connect("shutdown", lambda _app: popup.monitor.close() if popup else None)
    for number in (signal.SIGINT, signal.SIGTERM):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, number, lambda: (app.quit(), False)[1])
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
