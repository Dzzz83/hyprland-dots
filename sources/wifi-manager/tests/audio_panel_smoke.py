#!/usr/bin/env python3
"""Exercise the visible sound popup through AT-SPI; restore audio settings.

Requires python-gobject, at-spi2-core and pactl. Run while audio-panel is open.
Creates disposable virtual devices to verify selectors without real headphones.
Pass --wtype /path/to/wtype for native Wayland dropdown activation.
"""
import argparse
import json
import subprocess
import time
import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi, GLib


def pactl(*args):
    return subprocess.check_output(["pactl", *args], text=True).strip()


def wait_for(predicate, description):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError(description)


def descendants(node):
    yield node
    for index in range(node.get_child_count()):
        yield from descendants(node.get_child_at_index(index))


def nodes():
    desktop = Atspi.get_desktop(0)
    for index in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(index)
        if app.get_name() == "audio-panel":
            return list(descendants(app))
    raise AssertionError("Open audio-panel before running this test")


def find(role, name):
    return next(node for node in nodes()
                if node.get_role_name() == role and node.get_name() == name)


def click(node):
    action = node.get_action_iface()
    assert action and action.get_n_actions() > 0, node.get_name()
    assert action.do_action(0)


def set_slider(name, value):
    assert find("slider", name).get_value_iface().set_current_value(value)


def slider_value(name):
    return find("slider", name).get_value_iface().get_current_value()


def select_device(combo_index, description):
    combo = [node for node in nodes() if node.get_role_name() == "combo box"][combo_index]
    click(combo.get_child_at_index(0))
    wait_for(lambda: any(node.get_role_name() == "list item" for node in descendants(combo)),
             "Device selector did not open")
    rows = [row for row in descendants(combo) if row.get_role_name() == "list item"]
    for index, row in enumerate(rows):
        if any(child.get_name() == description for child in descendants(row)):
            # GTK exposes listitem.scroll-to through AT-SPI, not activation.
            # Exercise normal keyboard activation in the focused popover.
            keys = ["-k", "Home"] + [key for _ in range(index) for key in ("-k", "Down")] + ["-k", "Return"]
            subprocess.run([WTYPE, *keys], check=True)
            return
    raise AssertionError(f"Missing device: {description}")


def snapshot(kind, name):
    devices = json.loads(pactl("--format=json", "list", kind))
    return next(device for device in devices if device["name"] == name)


def restore(kind, device):
    pactl(f"set-{kind}-volume", device["name"],
          *[str(channel["value"]) for channel in device["volume"].values()])
    pactl(f"set-{kind}-mute", device["name"], "1" if device["mute"] else "0")


def main():
    output = pactl("get-default-sink")
    input_device = pactl("get-default-source")
    saved_output = snapshot("sinks", output)
    saved_input = snapshot("sources", input_device)
    modules = []
    try:
        # Exercise the actual GTK sliders and mute buttons, not a separate API.
        set_slider("Output volume", 79)
        wait_for(lambda: "79%" in pactl("get-sink-volume", output), "Output slider failed")
        set_slider("Microphone volume", 89)
        wait_for(lambda: "89%" in pactl("get-source-volume", input_device), "Microphone slider failed")
        for kind, title, saved in [("sink", "output", saved_output), ("source", "microphone", saved_input)]:
            action = "Unmute" if saved["mute"] else "Mute"
            click(find("button", f"{action} {title}"))
            expected = "no" if saved["mute"] else "yes"
            wait_for(lambda: pactl(f"get-{kind}-mute", saved["name"]) == f"Mute: {expected}",
                     f"{title} mute failed")
        pactl("set-sink-volume", output, "77%")
        wait_for(lambda: round(slider_value("Output volume")) == 77, "External output update failed")
        pactl("set-source-volume", input_device, "87%")
        wait_for(lambda: round(slider_value("Microphone volume")) == 87, "External input update failed")
        print("Sliders, mute buttons, and external volume synchronization passed.")

        modules.append(pactl("load-module", "module-null-sink", "sink_name=audio_panel_test",
                             "sink_properties=device.description=AudioPanelTest"))
        wait_for(lambda: len(json.loads(pactl("--format=json", "list", "sinks"))) > 1,
                 "Virtual output was not created")
        select_device(0, "AudioPanelTest")
        wait_for(lambda: pactl("get-default-sink") == "audio_panel_test", "Output selection failed")
        modules.append(pactl("load-module", "module-remap-source", "master=audio_panel_test.monitor",
                             "source_name=audio_panel_test_input",
                             "source_properties=device.description=AudioPanelTestMic"))
        # Wait for the backend's event-driven device enumeration.
        time.sleep(0.5)
        select_device(1, "AudioPanelTestMic")
        wait_for(lambda: pactl("get-default-source") == "audio_panel_test_input", "Input selection failed")
        print("Output and microphone device selection passed with virtual devices.")
        pactl("set-default-sink", output)
        pactl("set-default-source", input_device)
        while modules:
            pactl("unload-module", modules.pop())
        wait_for(lambda: all("AudioPanelTest" not in node.get_name() for node in nodes()),
                 "Removed devices remained in the popup")
        print("Device removal and fallback passed.")
    finally:
        pactl("set-default-sink", output)
        pactl("set-default-source", input_device)
        for module in reversed(modules):
            pactl("unload-module", module)
        restore("sink", saved_output)
        restore("source", saved_input)
        print("Original audio defaults, channel volumes, and mute states restored.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wtype", default="wtype")
    WTYPE = parser.parse_args().wtype
    main()
