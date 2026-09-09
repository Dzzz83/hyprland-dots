# Hyprland Dotfiles

A modular, Lua-based Hyprland configuration running on CachyOS. 
This setup features a custom 2D workspace grid, a dedicated Workspace 9 dashboard, Catppuccin Mocha theming, and consolidated configs for Waybar, Rofi, Wlogout, and Cava using symlinks for easy dotfile management.

## 🖥️ Environment & OS
*   **OS:** CachyOS (Arch Linux)
*   **Compositor:** Hyprland 0.56.1 (Using the **new Lua config API**)
*   **Shell:** fish
*   **Terminal:** Ghostty
*   **Bar / Launcher:** Waybar, Rofi, SwayNC
*   **Theme:** Catppuccin Mocha

---

## 🚀 Installation Guide (Fresh Install / New Machine)

If you are setting this up on a new laptop (like the Lenovo Slim Pro 9i) or starting fresh:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Dzzz83/hyprland-dots.git ~/.config/hypr
   ```

2. **Create Symlinks for External Apps:**
   Since Waybar, Rofi, Wlogout, and Cava look for their configs in `~/.config/`, you must symlink them to this repo:
   ```bash
   ln -s ~/.config/hypr/waybar ~/.config/waybar
   ln -s ~/.config/hypr/rofi ~/.config/rofi
   ln -s ~/.config/hypr/wlogout ~/.config/wlogout
   ln -s ~/.config/hypr/cava ~/.config/cava
   ln -s ~/.config/hypr/scripts ~/.config/viegphunt
   ```

3. **Ensure Colors Exist (CRITICAL):**
   Waybar and Rofi import colors from `~/.config/colors/`. If this is a fresh install, Waybar will crash. Create dummy files:
   ```bash
   mkdir -p ~/.config/colors
   touch ~/.config/colors/colors.css
   touch ~/.config/colors/colors.rasi
   ```

4. **Workspace 9 Dashboard Dependencies:**
   The autostart launches a custom dashboard. Ensure these are installed:
   ```bash
   sudo pacman -S firefox cava cbonsai tty-clock
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
*(Sizes below are for the old laptop. Scale up ~11% in Y-coordinates for the new 1.67 scale laptop).*

*   **Top-Left (Firefox YouTube):** `[float; size 736 524; move 16 36; workspace 9 silent]`
*   **Bottom-Left (Cava):** `class = com.dash.cava`, `size = 960 272`, `move = 16 576`
*   **Top-Right (cbonsai):** `class = com.dash.rain`, `size = 736 480`, `move = 784 36`
*   **Bottom-Right (tty-clock):** `class = com.dash.clock`, `size = 480 224`, `move = 1040 624`

---

## ⚠️ Known Bugs & Workarounds (Hyprland 0.56.1)

We spent hours debugging these issues in Hyprland 0.56.1. **DO NOT revert these fixes:**

1.  **Waybar Workspace Clicking Broken:** Waybar's native `hyprland/workspaces` module does not work with Hyprland 0.56's Lua IPC. 
    *   *Fix:* Waybar uses the `ext/workspaces` module, and workspaces are made persistent in `config/workspaces.lua`.
2.  **Workspace Jump Freezes:** Calling `hyprctl activeworkspace` from inside a Hyprland keybind causes an IPC deadlock and freezes the laptop. 
    *   *Fix:* The "2D Workspace Grid" (jumping 10 workspaces up/down) uses a pure Lua `for` loop in `binds.lua`.
3.  **Cava Scrollbar/Gap Bug:** Cava miscalculates terminal height in Ghostty using the `noncurses` output, causing a scrollbar and a top gap.
    *   *Fix:* Cava `config` is explicitly set to `method = ncurses` under `[output]`.

---

## 🎨 Theming

*   **Catppuccin Mocha** is the primary color palette.
*   **Cava** uses a custom cold color gradient (greens, teals, blues) with `bars = 0` (auto-fill width) and `sensitivity = 50`.
*   **GTK Theming:** Applied automatically on startup via `~/.config/hypr/scripts/gtkthemes.sh`.