> Historical installation notes. Use the root README and install/build-native.sh for the consolidated setup.

# Wi-Fi panel installation

Source: https://github.com/Vijay-papanaboina/wifi-manager
Pinned revision: 554787423accc3abab5257653e6f74722971ef8d
Source checkout: $HOME/.config/hypr/sources/wifi-manager
Build: cargo build --release --locked
Binary: $HOME/.local/bin/wifi-manager

The pinned revision preserves the Wi-Fi/Bluetooth preview layout.
Configuration and color overrides are beside this file. Restart wifi-manager
after editing settings; CSS can also be refreshed with wifi-manager --reload.
Waybar toggles the panel; Hyprland config/autostart.lua starts the daemon.

Previous configuration and Rofi Wi-Fi files: $HOME/.local/state/hypr-wifi-backups/20261031-111924-before-wifi-manager
To roll back, restore waybar/config, config/autostart.lua, scripts/wifi-menu.sh,
rofi/wifi.ini and rofi/wifi.rasi from that directory into ~/.config/hypr,
and networkmanager_dmenu into ~/.local/bin. Stop wifi-manager and reload Waybar.

## Local dismissal patch

The pinned source now includes a local patch for Escape and outside-click
dismissal. See LOCAL-CHANGES.md in the source checkout for behavior, checks,
and rollback instructions. The patch is also saved as dismissal.patch beside
this file. Keep these changes when rebuilding the pinned revision.
