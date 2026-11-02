#!/usr/bin/env python3
"""Render nm-applet's exported D-Bus menu from the Waybar network module."""

import os
import shutil
import sys

# Waybar runs this helper as a fresh process. Use XWayland when available so
# GTK can position a standalone popup without Wayland's original click serial.
if os.environ.get("DISPLAY"):
    os.environ["GDK_BACKEND"] = "x11"

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Dbusmenu", "0.4")
gi.require_version("DbusmenuGtk3", "0.4")
from gi.repository import DbusmenuGtk3, Gio, GLib, Gtk

WATCHER = "org.kde.StatusNotifierWatcher"
WATCHER_PATH = "/StatusNotifierWatcher"
PROPERTIES = "org.freedesktop.DBus.Properties"
ITEM_INTERFACES = (
    "org.kde.StatusNotifierItem",
    "org.freedesktop.StatusNotifierItem",
)


def notify(message):
    if shutil.which("notify-send"):
        import subprocess

        subprocess.run(
            ["notify-send", "NetworkManager", message],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        print(f"NetworkManager: {message}", file=sys.stderr)


def get_dbus_menu():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def call(destination, object_path, interface, method, parameters):
        return bus.call_sync(
            destination,
            object_path,
            interface,
            method,
            parameters,
            None,
            Gio.DBusCallFlags.NONE,
            3000,
            None,
        )

    items_reply = call(
        WATCHER,
        WATCHER_PATH,
        PROPERTIES,
        "Get",
        GLib.Variant("(ss)", (WATCHER, "RegisteredStatusNotifierItems")),
    )
    registered_items = items_reply.get_child_value(0).get_variant().unpack()

    matches = []
    for registered_item in registered_items:
        service, separator, item_path = registered_item.partition("/")
        if not service:
            continue
        object_path = f"/{item_path}" if separator else "/StatusNotifierItem"

        for item_interface in ITEM_INTERFACES:
            try:
                properties_reply = call(
                    service,
                    object_path,
                    PROPERTIES,
                    "GetAll",
                    GLib.Variant("(s)", (item_interface,)),
                )
            except GLib.Error:
                continue

            properties = properties_reply.get_child_value(0).unpack()
            item_id = str(properties.get("Id", "")).casefold()
            icon_name = str(properties.get("IconName", "")).casefold()
            menu_path = properties.get("Menu")
            if not menu_path or menu_path == "/NO_DBUSMENU":
                continue

            if item_id == "nm-applet":
                matches.append((2, service, str(menu_path)))
                break
            if icon_name.startswith("nm-signal"):
                matches.append((1, service, str(menu_path)))
                break

    if not matches:
        raise RuntimeError("Could not find nm-applet's exported D-Bus menu.")

    score = max(match[0] for match in matches)
    best = {(service, menu_path) for rank, service, menu_path in matches if rank == score}
    if len(best) != 1:
        raise RuntimeError("Found more than one NetworkManager tray menu.")
    return next(iter(best))


def main():
    try:
        service, menu_path = get_dbus_menu()
    except (GLib.Error, RuntimeError) as error:
        notify(f"Could not find the NetworkManager menu: {error}")
        return 1

    try:
        Gtk.init([])
        menu = DbusmenuGtk3.Menu.new(service, menu_path)
        client = menu.get_client()
        state = {"opened": False, "timeout": None}

        def open_when_ready(*_args):
            if state["opened"] or client.get_root() is None:
                return
            state["opened"] = True
            if state["timeout"] is not None:
                GLib.source_remove(state["timeout"])
                state["timeout"] = None
            menu.show_all()
            menu.popup_at_pointer(None)

        def layout_timeout():
            if not state["opened"]:
                notify("NetworkManager's menu did not respond.")
                Gtk.main_quit()
            return GLib.SOURCE_REMOVE

        client.connect("layout-updated", open_when_ready)
        menu.connect("deactivate", lambda *_args: Gtk.main_quit())
        state["timeout"] = GLib.timeout_add(3000, layout_timeout)
        Gtk.main()
        return 0 if state["opened"] else 1
    except (GLib.Error, RuntimeError) as error:
        notify(f"Could not display the NetworkManager menu: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
