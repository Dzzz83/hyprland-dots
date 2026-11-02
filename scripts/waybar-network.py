#!/usr/bin/env python3
"""Stream physical-network and VPN connection changes from NetworkManager."""

import html
import json
import sys

import gi

gi.require_version("NM", "1.0")
from gi.repository import Gio, GLib, NM


def indicator(connections, is_nm_running=True):
    wifi_name = None
    ethernet_name = None
    vpn_name = None
    is_proton = False
    for connection in connections:
        if connection.get_state() != NM.ActiveConnectionState.ACTIVATED:
            continue
        connection_type = connection.get_connection_type()
        name = connection.get_id()
        if connection_type in ("vpn", "wireguard"):
            is_proton_connection = name.casefold().startswith("proton") or any(
                device.get_iface() == "proton0" for device in connection.get_devices()
            )
            if vpn_name is None or is_proton_connection:
                vpn_name = name
                is_proton = is_proton_connection
        elif connection_type == "802-11-wireless":
            wifi_name = name
            for device in connection.get_devices():
                if device.get_device_type() == NM.DeviceType.WIFI:
                    access_point = device.get_active_access_point()
                    if access_point is not None and access_point.get_ssid() is not None:
                        wifi_name = NM.utils_ssid_to_utf8(access_point.get_ssid().get_data())
                        break
        elif connection_type == "802-3-ethernet":
            ethernet_name = name

    details = []
    if wifi_name:
        details.append(f"Wi-Fi: {wifi_name}")
    if ethernet_name:
        details.append(f"Ethernet: {ethernet_name}")
    if vpn_name:
        label = wifi_name or ("Ethernet" if ethernet_name else None)
        if label is None:
            label = "Proton VPN" if is_proton else "VPN"
        text = f"󰦝  {label}"
        state = "vpn"
        details.append(f"VPN: {vpn_name}")
    elif wifi_name:
        text, state = f"  {wifi_name}", "wifi"
        details.append("VPN: disconnected")
    elif ethernet_name:
        text, state = "  Ethernet", "ethernet"
        details.append("VPN: disconnected")
    else:
        text, state = "  Disconnected", "disconnected"
    if not is_nm_running:
        text, state = "  Network unavailable", "unavailable"
        details = ["NetworkManager is unavailable"]
    details.append("Click for Wi-Fi / Bluetooth")
    return {
        "text": html.escape(text),
        "class": state,
        "tooltip": html.escape("\n".join(details)),
    }


def main():
    client = NM.Client.new(None)
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    loop = GLib.MainLoop()
    previous = None
    is_refresh_pending = False

    def refresh():
        nonlocal previous, is_refresh_pending
        is_refresh_pending = False
        value = indicator(client.get_active_connections(), client.get_nm_running())
        if value != previous:
            try:
                print(json.dumps(value, ensure_ascii=False), flush=True)
            except BrokenPipeError:
                loop.quit()
                return GLib.SOURCE_REMOVE
            previous = value
        return GLib.SOURCE_REMOVE

    def schedule_refresh(*_args):
        nonlocal is_refresh_pending
        if not is_refresh_pending:
            is_refresh_pending = True
            # Let libnm finish updating its cache before reading changed objects.
            GLib.idle_add(refresh)

    subscription = bus.signal_subscribe(
        "org.freedesktop.NetworkManager",
        "org.freedesktop.DBus.Properties",
        "PropertiesChanged",
        None,
        None,
        Gio.DBusSignalFlags.NONE,
        schedule_refresh,
    )
    client.connect("notify::nm-running", schedule_refresh)
    refresh()
    try:
        loop.run()
    finally:
        bus.signal_unsubscribe(subscription)


if __name__ == "__main__":
    try:
        main()
    except (GLib.Error, OSError) as error:
        print(json.dumps(indicator([], False)), flush=True)
        print(f"Network indicator: {error}", file=sys.stderr)
        sys.exit(1)
