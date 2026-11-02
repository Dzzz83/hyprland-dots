#!/usr/bin/env bash
set -euo pipefail

# Run this as your normal desktop user from a terminal. sudo will prompt there.
if [[ ${EUID} -eq 0 ]]; then
    echo "Run this script as your normal user; it requests sudo when needed." >&2
    exit 1
fi

wallpaper_source="${HOME}/Pictures/Wallpapers/wallhaven-lyjldl_1920x1080.png"
wallpaper_target="/var/lib/plasmalogin/wallpaper.png"
config="/etc/plasmalogin.conf"

if [[ ! -r "$wallpaper_source" ]]; then
    echo "Wallpaper not found or unreadable: $wallpaper_source" >&2
    exit 1
fi
if ! getent passwd plasmalogin >/dev/null; then
    echo "The plasmalogin greeter account was not found; no changes made." >&2
    exit 1
fi
if [[ ! -f "$config" ]]; then
    echo "Login manager configuration not found: $config" >&2
    exit 1
fi

echo "This will configure Plasma Login Manager to show the selected wallpaper and clock."
echo "A dated backup of $config will be created. The change appears when the greeter next starts."
sudo -v

sudo install -d -o plasmalogin -g plasmalogin -m 0750 /var/lib/plasmalogin
sudo install -o plasmalogin -g plasmalogin -m 0644 "$wallpaper_source" "$wallpaper_target"

sudo python3 - "$config" <<'PY'
import os
import shutil
import stat
import sys
import tempfile
import time

config = sys.argv[1]
begin = "# BEGIN managed Plasma Login Manager appearance"
end = "# END managed Plasma Login Manager appearance"
managed = """# BEGIN managed Plasma Login Manager appearance
[Greeter]
ShowClock=true
WallpaperPluginId=org.kde.image

[Greeter][Wallpaper][org.kde.image][General]
Blur=true
FillMode=0
Image=file:///var/lib/plasmalogin/wallpaper.png
# END managed Plasma Login Manager appearance
"""

with open(config, "r", encoding="utf-8") as source_file:
    original = source_file.read()

if (begin in original) != (end in original):
    raise SystemExit("Managed settings markers are incomplete; refusing to edit the config.")

# Remove a previous copy of this script's block so re-running is clean.
if begin in original:
    before, remainder = original.split(begin, 1)
    _, after = remainder.split(end, 1)
    original = before + after.lstrip("\r\n")

updated = original.rstrip("\r\n") + "\n\n" + managed
metadata = os.stat(config)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = f"{config}.codex-backup-{stamp}"
suffix = 1
while os.path.exists(backup):
    backup = f"{config}.codex-backup-{stamp}-{suffix}"
    suffix += 1
shutil.copy2(config, backup)

directory = os.path.dirname(config)
fd, temporary = tempfile.mkstemp(prefix=".plasmalogin.", dir=directory, text=True)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as target_file:
        target_file.write(updated)
        target_file.flush()
        os.fsync(target_file.fileno())
    os.chown(temporary, metadata.st_uid, metadata.st_gid)
    os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
    os.replace(temporary, config)
except BaseException:
    try:
        os.unlink(temporary)
    except FileNotFoundError:
        pass
    raise

print(f"Updated: {config}")
print(f"Backup:  {backup}")
PY

echo "Done. Reboot when convenient to see the new login screen."
