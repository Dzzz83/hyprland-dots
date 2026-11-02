"""Mapping, notification, and failure checks for the Waybar mode indicator."""

import importlib.util
from pathlib import Path
import select
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "power_mode", Path(__file__).resolve().parents[1] / "scripts/waybar-power-mode.py"
)
power_mode = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(power_mode)


class PowerModeTests(unittest.TestCase):
    def test_mode_mapping_and_neutral_fallback(self):
        for profile, expected in [
            ("performance", "performance"), ("balanced", "balanced"),
            ("low-power", "quiet"), ("quiet", "quiet"),
            ("custom", "custom"), ("other", "unknown"), (None, "unavailable"),
        ]:
            with self.subTest(profile=profile):
                self.assertEqual(power_mode.indicator(profile)["class"], expected)
        self.assertIn("&lt;other&gt;", power_mode.indicator("<other>")["tooltip"])

    def test_notifications_reread_file_and_suppress_duplicates(self):
        emitted = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile"
            path.write_text("performance\n")

            class FakePoll:
                def __init__(self):
                    self.changes = iter(["performance", "balanced", "low-power"])

                def register(self, descriptor, flags):
                    assert descriptor >= 0
                    assert flags == select.POLLPRI | select.POLLERR

                def poll(self):
                    # No timeout argument: a periodic polling loop fails here.
                    try:
                        path.write_text(next(self.changes) + "\n")
                        return [(0, select.POLLPRI | select.POLLERR)]
                    except StopIteration:
                        return [(0, select.POLLHUP)]

            with self.assertRaisesRegex(OSError, "disconnected"):
                power_mode.watch_profile(path, emitted.append, FakePoll)
        self.assertEqual([entry["class"] for entry in emitted],
                         ["performance", "balanced", "quiet"])

    def test_missing_or_empty_profile_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile"
            with self.assertRaises(FileNotFoundError):
                power_mode.watch_profile(path, self.fail)
            path.touch()
            with self.assertRaisesRegex(OSError, "empty"):
                power_mode.watch_profile(path, self.fail)


if __name__ == "__main__":
    unittest.main(buffer=True)
