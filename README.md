# 🪟 Dzzz83 Hyprland Dotfiles

A modular, Lua-based Hyprland configuration running on CachyOS. 
This setup features a custom 2D workspace grid, a dedicated Workspace 9 dashboard, Catppuccin Mocha theming, and consolidated configs for Waybar, Rofi, Wlogout, and Cava using symlinks for easy dotfile management.

## 🖥️ Environment & OS
*   **OS:** CachyOS (Arch Linux)
*   **Compositor:** Hyprland 0.56.1+ (Using the **new Lua config API**)
*   **Shell:** fish
*   **Terminal:** Ghostty
*   **Bar / Launcher:** Waybar, Rofi, SwayNC
*   **Theme:** Catppuccin Mocha

### 🌳 Branch Guide
*   `main`: Base config / Old Laptop (Lenovo Legion 5, 1920x1080 @ 1.2 scale)
*   `slim-pro-9i`: New Laptop (Lenovo Slim Pro 9i, 3200x2000 @ 1.67 scale)

---

## 🚀 Full Installation Guide (Fresh Install)

1. **Clone the correct branch:**
   ```bash
   # For the new laptop:
   git clone -b slim-pro-9i https://github.com/Dzzz83/hyprland-dots.git ~/.config/hypr
   ```

2. **Install Core Dependencies (pacman):**
   ```bash
   sudo pacman -S hyprland waybar rofi swaync ghostty wlogout cava tty-clock fcitx5 nm-connection-editor nemo wl-clipboard hyprshot gtk3 playerctl brightnessctl hyprlock wev inotify-tools xdotool
   ```
   *(Note: `wev` and `inotify-tools` are used for debugging brightness/hardware keys).*

3. **Install AUR Dependencies (paru):**
   First, install `paru` if you don't have it:
   ```bash
   sudo pacman -S --needed base-devel git
   cd ~/Downloads && git clone https://aur.archlinux.org/paru.git && cd paru && makepkg -si
   ```
   Then install the AUR packages:
   ```bash
   paru -S cbonsai networkmanager-dmenu-git
   ```

4. **Install Fonts & Icons:**
   ```bash
   sudo pacman -S ttf-jetbrains-mono-nerd whitesur-icon-theme-dark
   ```

5. **Create Symlinks for External Apps:**
   Since Waybar, Rofi, Wlogout, and Cava look for their configs in `~/.config/`, you must symlink them to this repo:
   ```bash
   ln -s ~/.config/hypr/waybar ~/.config/waybar
   ln -s ~/.config/hypr/rofi ~/.config/rofi
   ln -s ~/.config/hypr/wlogout ~/.config/wlogout
   ln -s ~/.config/hypr/cava ~/.config/cava
   ln -s ~/.config/hypr/scripts ~/.config/viegphunt
   ```

6. **Configure Network Manager Dmenu:**
   Create the config file so the Waybar Wi-Fi button opens a themed Rofi menu:
   ```bash
   mkdir -p ~/.config/networkmanager-dmenu
   echo -e '[dmenu]\ndmenu_command = rofi -dmenu -i -theme ~/.config/hypr/rofi/network.rasi\n\n[editor]\nterminal = ghostty\ngui_if_available = False' > ~/.config/networkmanager-dmenu/config.ini
   ```

7. **Ensure Colors Exist (CRITICAL):**
   Waybar and Rofi import colors from `~/.config/colors/`. If this is a fresh install, Waybar will crash. Create the files and populate them with Catppuccin Mocha:
   ```bash
   mkdir -p ~/.config/colors
   # Create colors.rasi and colors.css with Catppuccin Mocha variables (see repo files for reference)
   ```

---

## ⌨️ Shortcut Guide (Keybindings)

*Main modifier is `SUPER` (Windows key).*

### Window & System Actions
| Shortcut | Action |
| :--- | :--- |
| `Super + Return` | Open Ghostty Terminal |
| `Super + Q` | Close active window |
| `Super + F` | Toggle floating |
| `Super + P` | Toggle pseudo tiling |
| `Super + J` | Toggle split (dwindle) |
| `Super + Shift + Q` | Kill window via hyprctl (force quit) |
| `Super + Shift + Ctrl + Esc` | Exit Hyprland |
| `Ctrl + Shift + Escape` | Open btop in floating Ghostty |

### App Launchers
| Shortcut | Action |
| :--- | :--- |
| `Super + Space` | Rofi (App Launcher) |
| `Super + E` | Nemo File Manager |
| `Super + B` | Brave Browser |
| `Super + V` | Clipboard Manager |
| `Super + Period` | Emoji Picker |
| `Super + Shift + W` | Random Wallpaper |
| `Super + Shift + S` | Screenshot Region |
| `Super + H` | Key Hints Popup |
| `Super + L` | Lock Session |
| `Super + N` | Toggle SwayNC Notifications |

### 2D Workspace Navigation
| Shortcut | Action |
| :--- | :--- |
| `Super + Left / Right` | Cycle previous / next workspace |
| `Super + Up / Down` | Jump 10 workspaces up/down instantly (2D Grid) |
| `Super + Shift + Left / Right`| Move active window to next/prev workspace AND follow it |
| `Alt + Tab` | Go to previous workspace |
| `Super + [0-9]` | Switch to workspace 1-10 |
| `Super + Shift + [0-9]` | Move active window to workspace 1-10 |
| `Super + Mouse Wheel` | Cycle workspaces |

---

## 📊 Workspace 9 Dashboard Layout

Workspace 9 is a dedicated dashboard that auto-launches on startup. 

*   **Top-Left (Firefox YouTube):** `[float; size 920 727; move 20 50; workspace 9 silent]`
*   **Bottom-Left (Cava):** `class = com.dash.cava`, `size = 1200 377`, `move = 20 799`
*   **Top-Right (cbonsai):** `class = com.dash.rain`, `size = 920 666`, `move = 980 50`
*   **Bottom-Right (tty-clock):** `class = com.dash.clock`, `size = 600 311`, `move = 1300 866`

---

## ⚠️ Known Bugs & Workarounds (Hyprland 0.56.1)

1.  **Waybar Workspace Clicking Broken:** Waybar's native `hyprland/workspaces` module does not work with the Lua IPC. 
    *   *Fix:* Waybar uses the `ext/workspaces` module, and workspaces are made persistent in `config/workspaces.lua`.
2.  **Workspace Jump Freezes:** Calling `hyprctl activeworkspace` from inside a keybind causes an IPC deadlock. 
    *   *Fix:* The "2D Workspace Grid" uses a pure Lua `for` loop in `binds.lua`.
3.  **Cava Scrollbar/Gap Bug:** Cava miscalculates terminal height in Ghostty using `noncurses` output.
    *   *Fix:* Cava `config` is explicitly set to `method = ncurses` under `[output]`.
4.  **Lenovo BIOS Stealing Brightness Keys:** F5/F6 brightness keys are intercepted by firmware, bypassing `brightnessctl` and `systemd-logind`.
    *   *Fix:* Mapped brightness to `Super + Page Up` / `Super + Page Down` using `brightnessctl -d intel_backlight`.

---

## 🎨 Theming
*   **Catppuccin Mocha** is the primary color palette.
*   **Cava** uses a custom cold color gradient with `bars = 0` (auto-fill width) and `sensitivity = 50`.
*   **GTK Theming:** Applied automatically on startup via `~/.config/hypr/scripts/gtkthemes.sh`.