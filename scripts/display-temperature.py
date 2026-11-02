#!/usr/bin/env python3
"""Bridge SwayNC's warmth percentage to hyprsunset's temperature IPC."""

import argparse
import math
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "get", "set"))
    parser.add_argument("warmth", nargs="?", type=float)
    args = parser.parse_args()
    if args.action == "set":
        if (
            args.warmth is None
            or not math.isfinite(args.warmth)
            or not 0 <= args.warmth <= 100
        ):
            parser.error("warmth must be a finite percentage between 0 and 100")
    elif args.warmth is not None:
        parser.error("only set accepts a warmth percentage")

    if args.action == "start":
        executable = Path.home() / ".local/bin/hyprsunset"
        os.execv(executable, [str(executable), "-t", "6500"])

    command = ["hyprctl", "hyprsunset", "temperature"]
    if args.action == "set":
        # 0% is neutral 6500 K; each percent lowers temperature by 35 K.
        command.append(str(round(6500 - 35 * args.warmth)))
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=3)
    if args.action == "get":
        temperature_kelvin = int(result.stdout.strip())
        print(round(max(0, min(100, (6500 - temperature_kelvin) / 35))))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Display temperature: {error}", file=sys.stderr)
        sys.exit(1)
