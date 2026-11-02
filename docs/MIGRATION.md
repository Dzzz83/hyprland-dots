# Repository layout and deployment

The checkout is the canonical home of desktop configuration, active themes,
icons, wallpapers, and custom source. `install/deploy.py` backs up existing files
under `~/.local/state/hypr-dots-backups/<timestamp>` before linking normal app
locations to the checkout. Git tracks the real files, not links to external
source directories. The old `~/.config/viegphunt` script alias is retired;
commands use `~/.config/hypr/scripts` directly. The ViegPhunt inspiration credits
are preserved in the README.

## Mapping

| Repository | Installed location |
| --- | --- |
| `waybar`, `rofi`, `swaync`, `wlogout`, `cava` | Same name under `~/.config` |
| `ghostty`, `colors`, `gtk-3.0`, `gtk-4.0` | Same name under `~/.config` |
| `Thunar`, `fontconfig`, `wifi-manager` | Same name under `~/.config` |
| `pavucontrol.ini` | `~/.config/pavucontrol.ini` |
| `fish` selected files/directories | `~/.config/fish` (secrets and universal variables stay local) |
| `ohmyposh`, `fcitx5` | Optional matching config directories |
| `assets/icons/*`, `assets/themes/*` | Matching paths under `~/.local/share` |
| `assets/wallpapers` | Used directly; `~/Desktop/Wallpapers` is a compatibility link |
| `xfce4/.../thunar.xml` | Preferences imported through `xfconf-query`, not a linked live database |
| `build/cargo/release/{wifi-manager,audio-panel}` | `~/.local/bin` links after building |
| `scripts/screen-record` | `~/.local/bin/screen-record` |

`gtk-3.0/bookmarks.template` and `swaync/config.json.in` generate ignored local
files in `build/runtime`. Their installed names are links to those generated
files. `config/local.lua` records the chosen machine profile and is ignored.
Never commit secrets, cache, `fish_variables`, generated build output, compiled
plugins, or screenshot/recording output.

## Hardware and optional components

The Lenovo profile preserves the current 1.2 display scale, mirrored external
outputs and Workspace 9 dashboard. The generic profile uses an automatic
monitor and disables that fixed-geometry dashboard. Adjust a new profile to fit
another machine before enabling it. Backlight selection is detected or can be
specified with `--backlight DEVICE`; no brightness widget is generated when no
backlight exists. Lenovo fast/conservation charging requires compatible
firmware, UPower support and `legion_cli`; it is not a universal laptop feature.

Package-owned files under `/usr` are not moved. Install matching packages instead.
Plasma Login Manager needs system-readable wallpapers before login; its optional
installer is under `optional/login-wallpaper`. It is not applied by deployment.
Optional MIME associations, autostart overrides and reminder units are examples
for manual review, not automatically enabled services. AGS, old hyprexpose builds,
other icon collections and app-specific gaming/development settings are not part
of the active Hyprland desktop.

## Building and updates

Native plugins must match the running Hyprland revision and dependency ABI.
This source snapshot was verified with Hyprland 0.57.0. The capture helper also
uses Qt private headers, so rebuild after Qt upgrades. Start with matching
installed/running Hyprland versions. Build before the first config reload.

Never replace a loaded `.so`. For a later rebuild, first close capture overlays,
stop recordings, and unload that component (or build while logged out of
Hyprland). Replacing only the standalone UI helper does not require unloading
the compositor plugin. Keep application data, accounts and credentials local.

The capture source includes a local nlohmann/json 3.12.0 header-only dependency
and its license. Rust uses Cargo.lock; rain uses the upstream installation
recipe. Build caches and third-party compiler outputs are intentionally absent.

## Rollback

Backups preserve each replaced file at its original path relative to HOME.
Close affected apps before restoring backups; unlink only a link created by
this installer, then move its saved original back. Reload the desktop after
restoring configuration. The pre-consolidation Hyprland archive and original
source Git histories are retained locally outside this public checkout.
