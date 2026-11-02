"""Battery status priorities, warning boundaries, and power-saving badges."""

import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "battery_indicator", Path(__file__).resolve().parents[1] / "scripts/waybar-battery.py"
)
battery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(battery)


class BatteryIndicatorTests(unittest.TestCase):
    def test_charging_and_ac_paused_or_full_have_distinct_icons(self):
        self.assertEqual(battery.indicator(58, 1, True, "balanced")["text"], " 58%")
        for state, percentage in [(5, 58), (4, 100), (2, 58)]:
            with self.subTest(state=state):
                value = battery.indicator(percentage, state, True, "performance")
                self.assertEqual(value["text"], f" {percentage}%")
                self.assertIn("AC connected", value["tooltip"])

    def test_warning_boundaries_and_charging_priority(self):
        for percentage, severity in [(31, None), (30, "warning"), (16, "warning"),
                                     (15, "critical"), (0, "critical")]:
            with self.subTest(percentage=percentage):
                classes = battery.indicator(percentage, 2, False, "balanced")["class"]
                self.assertEqual("warning" in classes, severity == "warning")
                self.assertEqual("critical" in classes, severity == "critical")
        for state in (1, 5):
            classes = battery.indicator(10, state, True, "balanced")["class"]
            self.assertNotIn("critical", classes)
            self.assertNotIn("warning", classes)

    def test_leaf_preserves_source_icon_and_low_battery_warning(self):
        for profile in ("quiet", "low-power"):
            self.assertEqual(battery.indicator(58, 5, True, profile)["text"], "  58%")
            self.assertEqual(battery.indicator(58, 1, True, profile)["text"], "  58%")
            value = battery.indicator(10, 2, False, profile)
            self.assertEqual(value["text"], "  10%")
            self.assertIn("critical", value["class"])
        self.assertNotIn("", battery.indicator(58, 2, False, "unknown")["text"])

    def test_time_estimates_and_unavailable_data(self):
        self.assertIn("1h 01m until full", battery.indicator(58, 1, True, "balanced", 3660)["tooltip"])
        self.assertIn("0h 30m remaining", battery.indicator(58, 2, False, "balanced", 1800)["tooltip"])
        self.assertNotIn("until full", battery.indicator(58, 5, True, "balanced", 3660)["tooltip"])
        for percentage in (float("nan"), float("inf"), -1, 101):
            self.assertEqual(battery.indicator(percentage, 0, False, "unknown")["class"], ["unavailable"])
        self.assertEqual(battery.indicator(0, 0, False, "unknown", is_present=False)["class"], ["unavailable"])


if __name__ == "__main__":
    unittest.main(buffer=True)
