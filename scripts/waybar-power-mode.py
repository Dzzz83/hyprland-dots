#!/usr/bin/env python3
"""Stream Lenovo platform-profile changes to Waybar without periodic polling."""

import argparse
import html
import json
import select
import sys
from pathlib import Path

PROFILE_PATH = Path("/sys/firmware/acpi/platform_profile")
MODES = {
    "performance": ("performance", "Performance"),
    "balanced": ("balanced", "Normal / Balanced"),
    "low-power": ("quiet", "Quiet"),
    "quiet": ("quiet", "Quiet"),
    "custom": ("custom", "Custom"),
}


def indicator(profile):
    """Keep unrecognized or unavailable modes distinct from Normal."""
    mode, label = MODES.get(profile, ("unknown", f"Unknown ({profile})"))
    if profile is None:
        mode, label = "unavailable", "Unavailable"
    return {
        "text": "●",
        "class": mode,
        "tooltip": f"Lenovo mode: {html.escape(label)}\nClick for power menu",
    }


def watch_profile(path, emit, poll_factory=select.poll):
    # Sysfs POLLPRI/POLLERR wakes on sysfs_notify. Seeking and reading the
    # attribute acknowledges the notification before the next blocking wait.
    with path.open("r", encoding="utf-8") as profile_file:
        poller = poll_factory()
        poller.register(profile_file.fileno(), select.POLLPRI | select.POLLERR)
        previous = None
        while True:
            profile_file.seek(0)
            profile = profile_file.read().strip()
            if not profile:
                raise OSError("Platform profile is empty")
            if profile != previous:
                emit(indicator(profile))
                previous = profile
            events = poller.poll()  # No timeout: remain asleep until notified.
            if any(flags & (select.POLLNVAL | select.POLLHUP) for _, flags in events):
                raise OSError("Platform profile monitor disconnected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=PROFILE_PATH)
    args = parser.parse_args()

    def emit(value):
        print(json.dumps(value, ensure_ascii=False), flush=True)

    try:
        watch_profile(args.profile, emit)
    except BrokenPipeError:
        return 0
    except OSError as error:
        emit(indicator(None))
        print(f"Lenovo mode indicator: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
