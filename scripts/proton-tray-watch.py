#!/usr/bin/env python3
"""Re-register Proton's existing tray item when the tray host restarts."""

import sys

from gi.repository import Gio, GLib

WATCHER = "org.kde.StatusNotifierWatcher"
WATCHER_PATH = "/StatusNotifierWatcher"
PROTON_PREFIX = "org.kde.StatusNotifierItem-proton.vpn.app.gtk-"


def main():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    loop = GLib.MainLoop()
    is_restore_pending = False

    def call(service, path, interface, method, parameters=None):
        return bus.call_sync(
            service, path, interface, method, parameters, None,
            Gio.DBusCallFlags.NONE, 3000, None,
        ).unpack()

    def restore():
        nonlocal is_restore_pending
        is_restore_pending = False
        try:
            names = call(
                "org.freedesktop.DBus", "/org/freedesktop/DBus",
                "org.freedesktop.DBus", "ListNames",
            )[0]
            if WATCHER not in names:
                return GLib.SOURCE_REMOVE
            registered = call(
                WATCHER, WATCHER_PATH, "org.freedesktop.DBus.Properties", "Get",
                GLib.Variant("(ss)", (WATCHER, "RegisteredStatusNotifierItems")),
            )[0]
            registered_services = {item.partition("/")[0] for item in registered}
            for name in names:
                if name.startswith(PROTON_PREFIX) and name not in registered_services:
                    call(
                        WATCHER, WATCHER_PATH, WATCHER, "RegisterStatusNotifierItem",
                        GLib.Variant("(s)", (name,)),
                    )
        except GLib.Error as error:
            print(f"Proton tray registration: {error.message}", file=sys.stderr)
        return GLib.SOURCE_REMOVE

    def schedule_restore(*_args):
        nonlocal is_restore_pending
        if not is_restore_pending:
            is_restore_pending = True
            GLib.idle_add(restore)

    def name_changed(_bus, _sender, _path, _interface, _signal, parameters, _data):
        name, _old_owner, new_owner = parameters.unpack()
        if new_owner and (name == WATCHER or name.startswith(PROTON_PREFIX)):
            schedule_restore()

    subscriptions = [
        bus.signal_subscribe(
            "org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
            "/org/freedesktop/DBus", None, Gio.DBusSignalFlags.NONE, name_changed,
        ),
        bus.signal_subscribe(
            WATCHER, WATCHER, "StatusNotifierHostRegistered", WATCHER_PATH,
            None, Gio.DBusSignalFlags.NONE, schedule_restore,
        ),
    ]
    schedule_restore()
    try:
        loop.run()
    finally:
        for subscription in subscriptions:
            bus.signal_unsubscribe(subscription)


if __name__ == "__main__":
    main()
