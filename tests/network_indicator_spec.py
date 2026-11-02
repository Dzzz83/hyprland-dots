"""VPN selection, physical-network fallback, and label escaping checks."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

SPEC = importlib.util.spec_from_file_location(
    "network_indicator", Path(__file__).resolve().parents[1] / "scripts/waybar-network.py"
)
network = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(network)


def connection(name, connection_type, state=None, interfaces=()):
    value = Mock()
    value.get_id.return_value = name
    value.get_connection_type.return_value = connection_type
    value.get_state.return_value = (
        network.NM.ActiveConnectionState.ACTIVATED if state is None else state
    )
    devices = []
    for interface in interfaces:
        device = Mock()
        device.get_iface.return_value = interface
        devices.append(device)
    value.get_devices.return_value = devices
    return value


class NetworkIndicatorTests(unittest.TestCase):
    def test_proton_tunnel_takes_priority_over_physical_and_dummy_connections(self):
        connections = [
            connection("Home", "802-11-wireless"),
            connection("pvpn-killswitch-ipv6", "dummy"),
            connection("docker0", "bridge"),
            connection("ProtonVPN NL-FREE#235", "wireguard", interfaces=("proton0",)),
        ]
        value = network.indicator(connections)
        self.assertEqual(value["text"], "󰦝  Home")
        self.assertIn("Wi-Fi: Home", value["tooltip"])
        self.assertIn("VPN: ProtonVPN NL-FREE#235", value["tooltip"])
        self.assertEqual(network.indicator(connections[:3])["text"], "  Home")

    def test_connecting_tunnel_does_not_claim_vpn_is_connected(self):
        value = network.indicator([
            connection("Home", "802-11-wireless"),
            connection("ProtonVPN", "wireguard", network.NM.ActiveConnectionState.ACTIVATING),
        ])
        self.assertEqual(value["class"], "wifi")

    def test_wifi_uses_actual_ssid_and_escapes_markup(self):
        wifi = connection("Renamed profile", "802-11-wireless", interfaces=("wlan0",))
        device = wifi.get_devices()[0]
        device.get_device_type.return_value = network.NM.DeviceType.WIFI
        access_point = device.get_active_access_point.return_value
        access_point.get_ssid.return_value = network.GLib.Bytes.new(b"Home <&>")
        self.assertEqual(network.indicator([wifi])["text"], "  Home &lt;&amp;&gt;")
        vpn = connection("ProtonVPN", "wireguard")
        self.assertEqual(network.indicator([wifi, vpn])["text"], "󰦝  Home &lt;&amp;&gt;")

    def test_other_vpn_ethernet_disconnected_and_unavailable_states(self):
        self.assertEqual(network.indicator([connection("Work", "vpn")])["text"], "󰦝  VPN")
        self.assertEqual(network.indicator([
            connection("ProtonVPN", "wireguard"),
            connection("Wired", "802-3-ethernet"),
        ])["text"], "󰦝  Ethernet")
        self.assertEqual(network.indicator([connection("Wired", "802-3-ethernet")])["class"], "ethernet")
        dummy = connection("pvpn-killswitch-ipv6", "dummy")
        self.assertEqual(network.indicator([dummy])["class"], "disconnected")
        self.assertEqual(network.indicator([], False)["class"], "unavailable")


if __name__ == "__main__":
    unittest.main(buffer=True)
