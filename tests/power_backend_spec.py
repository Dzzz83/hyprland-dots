"""Charging write validation, failed changes and battery-runtime estimates."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import power_backend as power


class PowerBackendTests(unittest.TestCase):
    def test_charging_modes_are_read_from_the_selected_firmware_value(self):
        for text, expected in [("Fast [Standard] Long_Life", "standard"),
                               ("[Fast] Standard Long_Life", "fast"),
                               ("Fast Standard [Long_Life]", "conservation"),
                               ("Fast Standard Long_Life", "unknown"),
                               ("[Fast] [Long_Life]", "unknown")]:
            self.assertEqual(power.charge_mode(text), expected)

    def test_unsupported_changes_never_execute_a_command(self):
        with patch.object(power, "run_command") as run:
            for function in (power.set_charge_mode, power.set_profile):
                with self.assertRaises(ValueError):
                    function("arbitrary-command")
            run.assert_not_called()

    def test_failed_or_rejected_charge_change_is_not_reported_as_success(self):
        with patch.object(power, "set_conservation_enabled"), patch.object(power, "run_command", side_effect=RuntimeError("Authentication cancelled")):
            with self.assertRaisesRegex(RuntimeError, "Authentication cancelled"):
                power.set_charge_mode("fast")
        with patch.object(power, "set_conservation_enabled"), patch.object(power, "run_command"), patch.object(power, "read_charge_mode", return_value="standard"):
            with self.assertRaisesRegex(RuntimeError, "firmware did not accept"):
                power.set_charge_mode("conservation")

    def test_current_and_cached_estimates_have_distinct_labels(self):
        text, detail = power.unplugged_estimate(2, 7200, 40, None, 1000)
        self.assertIn("2h 00m remaining", text)
        sample = {"timestamp": 700, "rate_w": 20, "profile": "balanced"}
        text, detail = power.unplugged_estimate(5, 0, 40, sample, 1000)
        self.assertIn("2h 00m if unplugged", text)
        self.assertIn("5 min ago", detail)
        self.assertIn("balanced", detail)
        text, _ = power.unplugged_estimate(2, 0, 40, sample, 1000)
        self.assertIn("remaining", text)

    def test_cancelled_fast_authentication_restores_conservation(self):
        with patch.object(power, "set_conservation_enabled") as set_limit, \
             patch.object(power, "run_command", side_effect=RuntimeError("Authentication cancelled")), \
             patch.object(power, "read_charge_mode", side_effect=["conservation", "standard", "conservation"]):
            with self.assertRaisesRegex(RuntimeError, "Authentication cancelled"):
                power.set_charge_mode("fast")
            self.assertEqual([call.args[0] for call in set_limit.call_args_list], [False, True])

    def test_unusable_estimates_are_not_invented(self):
        for sample in (None, {"timestamp": 0, "rate_w": 20},
                       {"timestamp": 99999, "rate_w": 0},
                       {"timestamp": 99999, "rate_w": float("nan")},
                       {"timestamp": 100001, "rate_w": 20}):
            text, _ = power.unplugged_estimate(5, 0, 40, sample, 100000)
            self.assertIn("available after unplugged use", text)

    def test_invalid_cached_data_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = power.PowerMonitor.__new__(power.PowerMonitor)
            monitor.cache_path = Path(directory) / "sample.json"
            for contents in ("bad json", "[]", '{"timestamp": "bad", "rate_w": 20}'):
                monitor.cache_path.write_text(contents)
                self.assertIsNone(monitor.load_sample())


if __name__ == "__main__":
    unittest.main(buffer=True)
