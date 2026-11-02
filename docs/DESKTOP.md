# Desktop details

Behavior and implementation notes for the current setup. For installation, see
[the README](../README.md) and [deployment notes](MIGRATION.md).

## Screen capture

HyprCapture opens a shared capture toolbar with `Super + Shift + S`. Drag a
region or select a window for a screenshot, then press Enter after editing to
save and copy it. Click the record circle to switch to video before selecting
the target. To stop, reopen the overlay and click the checked record circle.
Screenshots save to `~/Pictures/Screenshots`; videos save to
`~/Videos/Screenrecords`. Sound defaults to Off; select System, Microphone or Mix
in the recording toolbar when needed. Escape cancels capture. The local helper
uses Catppuccin Mocha with green selections, soft white text and rounded
toolbars; active recording stays red. Its palette is in
`sources/hyprcapture/src/ui/desktop_theme.hpp` in this repository.

The local build targets Hyprland 0.57.0 and supports PNG screenshots and video;
HDR HEIC export and the optional neural echo canceller are not installed.
`config/capture.lua` loads it and falls back to Hyprshot if loading fails.
Rebuild after Hyprland or Qt updates. Build, validation and rollback details are
in [deployment notes](MIGRATION.md). Super + Shift + R retains the previous recorder.

## Power and battery

Waybar's leftmost power circle shows the Lenovo mode: red for Performance,
white for Normal / Balanced, and blue for Quiet. Custom or unavailable modes
use gray. Its tooltip names the mode, and clicking still opens the power menu.
The helper in `scripts/waybar-power-mode.py` waits for kernel profile-change
notifications without periodic checks. If the profile interface is unavailable,
Waybar retries the helper after five seconds.

The battery indicator shows lightning (``) while charging, a plug (``)
when AC is connected without charging (including charging paused or full),
and a charge-level battery icon when unplugged. At 30% or below while
unplugged, it uses a low-battery icon in yellow; at 15% or below, red. Quiet /
power-saving mode adds a leaf (``) beside the source icon. Hover for the
charging state, AC status, power mode and a remaining/full time estimate when
UPower supplies one. `scripts/waybar-battery.py` listens to UPower D-Bus changes
and Lenovo platform-profile notifications; it does not poll on a timer.

Click the battery indicator for a matching GTK popup beneath it. Escape,
an outside click, or a second click on the indicator dismisses it. The
three-position Lenovo slider selects Quiet (power saving), Normal or Performance
and stays synchronized with Fn+Q changes and the bar indicators. The charging slider selects
Standard, Fast or Conservation (around 60%, controlled by Lenovo firmware).

The popup and bar share `scripts/power_backend.py`. Conservation uses UPower's
charging-limit API so its persistent policy agrees with the firmware; Fast
uses the installed `pkexec /usr/bin/legion_cli` control and may require system
authentication. The installed KDE Polkit agent starts at login with software
rendering and the Fusion style, avoiding the authentication-dialog crash seen
with the session's default rendering/theme settings. No passwordless sudo rule
or new privileged service is installed.

Battery runtime uses UPower's estimate while discharging. A measured discharge
rate is cached in `$XDG_CACHE_HOME/hypr/battery-use.json` (normally `~/.cache/hypr/`)
for up to 24 hours, allowing a clearly labeled estimate on AC with the sample's
age and power mode. With no usable sample, the popup hides the runtime estimate. Hover over an
estimate for its source, the percentage for battery health and cycle count, or
the charging slider for the Conservation charge-limit explanation.

## Network

Waybar's network indicator shows `󰦝 <network name>` while NetworkManager reports
a VPN tunnel as activated, and ` <network name>` on Wi-Fi without a VPN.
Wired connections use `Ethernet` beside the appropriate icon. If no physical
connection is available, an active VPN uses `Proton VPN` or `VPN` as its label.
Hover for the Wi-Fi network and VPN connection name; clicking opens the
Wi-Fi / Bluetooth popup. `scripts/waybar-network.py` listens for NetworkManager
D-Bus changes through Python GObject / libnm, with no periodic polling. Dummy
kill-switch and bridge interfaces do not count as VPN or physical connections.

Proton's own application tray icon remains separate from the network indicator.
`scripts/proton-tray-watch.py` starts at login and listens for tray-host and
Proton tray-service registration events. It re-registers the app's existing
tray item after Waybar restarts or reloads, without restarting Proton or
changing its VPN connection. It does not create an icon when Proton is closed.

## Sound and notifications

Click Waybar's volume indicator to toggle the Sound popup. It provides speaker
and microphone volume, mute, and device selection. Escape or an outside click
closes it; Advanced settings opens the full mixer. Rebuild and rollback notes
are in [deployment notes](MIGRATION.md); historical changes are in `sources/wifi-manager/LOCAL-CHANGES.md`.

The Wi-Fi / Bluetooth popup contains connection controls only; its former
sliders and session/power buttons are removed. Open the notification center
with `Super + N` for Brightness and Warm light. Warm light runs from 0% (6500 K,
cool/neutral) to 100% (3000 K, warm), and remains applied when the center is
closed. Volume stays in the separate Sound popup. Brightness uses the laptop's
`nvidia_0` backlight, with a 5% minimum.

Color temperature uses [hyprsunset](https://github.com/hyprwm/hyprsunset)
0.4.0, installed at `~/.local/bin/hyprsunset`. The helper
`scripts/display-temperature.py` starts it at login at 6500 K and translates
the notification center's warmth percentage to its IPC temperature setting.
It does not schedule automatic temperature changes or save warmth across logins.

## Workspace preview

The preview uses a locally adapted [Hyprspace](https://github.com/KZDKM/Hyprspace)
plugin with a centered, rounded horizontal strip of sharp desktop previews over
a blurred, dimmed desktop. It floats without resizing windows. Catppuccin Mocha
styling is in `config/workspace_overview.lua`. Empty workspaces are excluded,
including persistent ones. The one-second delay starts on the first Alt press.
Pressing Tab resets it; a fresh countdown starts after Tab is released while Alt
remains held. Alt+Tab still toggles the two most recent workspaces, closing any
open preview first. Releasing both Alt keys cancels the countdown. Arrow keys do
not reset it. Super+arrows always switch workspaces and Super never opens the
preview. Other Alt shortcuts cancel the pending
delay or open preview and perform their usual action. The active workspace
stays unchanged while selecting. On commit,
Up/Down use vertical slides and Left/Right use horizontal slides.

Source and build notes are in
`sources/hyprspace/LOCAL-CHANGES.md` (historical notes); current build instructions
are in `docs/MIGRATION.md`.
The plugin must be rebuilt against the running compositor after Hyprland updates.

---

## Workspace 9 dashboard

Workspace 9 is a dedicated dashboard that starts with the Lenovo profile;
the generic profile leaves it disabled. The layout
uses two aligned columns with 16 logical pixels between panels and around the
edges below Waybar. Coordinates fit the 1920×1080 laptop display at scale 1.2
(1600×900 logical pixels).

*   **Top-Left (Firefox YouTube):** `[float; size 1008 584; move 16 40; workspace 9 silent]`
*   **Bottom-Left (Cava):** `class = com.dash.cava`, `size = 1010 244`, `move = 16 640`
*   **Top-Right (Terminal Rain):** `class = com.dash.rain`, `size = 544 584`, `move = 1040 40`
*   **Bottom-Right (tty-clock):** `class = com.dash.clock`, `size = 544 244`, `move = 1040 640`

---

## Compatibility notes

These workarounds are part of the current Hyprland 0.57.0 setup.

1.  **Waybar Workspace Clicking Broken:** Waybar's native `hyprland/workspaces` module does not work with Hyprland 0.56's Lua IPC.
    *   *Fix:* Waybar uses the `ext/workspaces` module, and workspaces are made persistent in `config/workspaces.lua`.
2.  **Workspace Jump Freezes:** Calling `hyprctl activeworkspace` from inside a Hyprland keybind causes an IPC deadlock and freezes the laptop.
    *   *Fix:* Key handlers use native Lua APIs and Hyprspace's selection functions. The selected workspace stays separate from focus until all navigation keys are released; no synchronous IPC reads run inside compositor callbacks.
3.  **Cava Scrollbar/Gap Bug:** Cava miscalculates terminal height in Ghostty using the `noncurses` output, causing a scrollbar and a top gap.
    *   *Fix:* Cava `config` is explicitly set to `method = ncurses` under `[output]`. Its dashboard terminal launches with `--window-padding-x=0` with a 1010-pixel logical window width so the current bar grid fills the available width. Other window sizes or display scales may leave unused columns.

---

## Theming

*   **Catppuccin Mocha** is the primary color palette.
*   **Cava** uses a custom cold color gradient (greens, teals, blues) with `bars = 0` (auto-fill width) and `sensitivity = 50`.
*   **GTK Theming:** Catppuccin Mocha with mauve accents (`Catppuccin-Mauve-Dark`) and `Papirus-Dark` icons, applied automatically on startup via `~/.config/hypr/scripts/gtkthemes.sh`. Theme assets are installed per user under `~/.local/share/themes` and `~/.local/share/icons`; GTK 3 and GTK 4 settings use the same theme and icons. Breeze cursors (`breeze_cursors`) use size 24 across GTK, GSettings, Xcursor and KDE settings. Existing fonts are preserved.
*   **Thunar:** Darker surfaces are scoped to Thunar in `~/.config/gtk-3.0/thunar.css`, imported by `gtk.css`: a near-black `#11111b` file area and `#181825` sidebar and toolbar. Detailed List is the default, with small icons, Name / Size / Type / Date Modified columns, folders first, alphabetical sorting, an editable full-path location bar (`ThunarLocationEntry`), and a 210-pixel sidebar. Documents, Downloads, Pictures, Music, Videos, and Projects are bookmarked. Preferences live in `~/.config/xfce4/xfconf/xfce-perchannel-xml/thunar.xml`; bookmarks live in `~/.config/gtk-3.0/bookmarks`. The source preferences and CSS are now stored in this repository; the deployer backs up existing target files.
