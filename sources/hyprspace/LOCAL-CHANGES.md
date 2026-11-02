> Historical development/validation notes. Current installation, paths and rebuild steps are in the repository root `README.md` and `docs/MIGRATION.md`.

# Hyprspace with Super-hold workspace selection

Upstream: https://github.com/KZDKM/Hyprspace
Base revision: `8345bf6f623d486ca3f87f416ccf1412416eef08`.
Built against Hyprland 0.57.0, commit
`0aa6745f705f2c4b0a5004eb019ef76e5bbdb426`, and its installed headers.

## Behavior

Hold either Super key for three seconds to open the native horizontal overview.
Only normal workspaces containing windows appear, including when empty
workspaces are persistent. Left/Right selects an adjacent preview; Up/Down
selects the previous/next page of previews. Selection scrolls into view and
stays separate from the active workspace. Edges do not wrap.

Releasing both Super keys and every held arrow closes the overview and switches
once. Escape or another Super shortcut cancels the selection. Alt+Tab still
toggles the two most recently focused workspaces. Before the overview opens,
Left/Right switches one workspace immediately and Up/Down jumps forward/back
ten with vertical animations. Selecting inside the overview does not alter
workspace history; only the committed switch does.

The horizontal panel floats in the center of the monitor, with rounded corners,
Catppuccin colors, and a green selection border. It fits the occupied previews
up to the available screen width; longer strips scroll within its bounds.
A live full-screen blur and dark tint sit behind the sharp desktop previews.
Both fade away on close. The panel does not reserve space or resize windows.
Native Hyprspace rendering preserves desktop proportions and updates previews
live. Workspace gap overrides are disabled to preserve existing workspace
rules. The old `workspace-preview.toml`
file and hyprexpose source are retained for rollback and are no longer active.

## Responsibilities

- `config/workspace_overview.lua` loads the plugin and applies its appearance.
- `config/workspace_preview.lua` owns the three-second timer, key state,
  cancellation, release ordering, immediate navigation, and commit animation.
- `src/Preview.cpp` filters workspace tiles and manages the selected workspace
  ID and shared panel bounds. `PreviewNavigation.hpp` implements bounded
  adjacent/page navigation; `OverviewGeometry.hpp` computes centered bounds.
- `src/Lua.cpp` adds `begin_selection()`, `move_selection(direction)`, and
  `finish_selection(commit)`. The final function hides the overview and returns
  the selected workspace ID only if it is still occupied. Lua then dispatches
  the actual focus change with the appropriate animation.
- `src/Render.cpp` draws the selection independently of the active workspace,
  keeps it visible, and draws the blurred backdrop before sharp previews.
- `src/Layout.cpp` arranges real panels before reserving overview space, so
  Waybar stays anchored at the top in the optional edge-panel mode. Centered
  mode leaves the desktop's reserved space unchanged.
- Unloading an open plugin restores fullscreen and layer/layout state. An ABI
  guard rejects loading a binary built against a different compositor revision
  or incompatible dependency versions.

No per-key subprocesses or synchronous IPC reads run in compositor handlers.
The old hyprexpose daemon is removed from autostart.

## Build, checks, and installation

```sh
make all
make test
```

From `/home/dzzz83/.config/hypr`:

```sh
luac -p config/workspace_overview.lua config/workspace_preview.lua config/binds.lua
lua tests/workspace_preview_spec.lua
```

The installed binary is:
`/home/dzzz83/.config/hypr/plugins/Hyprspace-0.57.0.so`.
Keep the source checkout and rebuild after Hyprland updates. For a rebuild
while the plugin is running, first unload the installed library, then install
the new build and reload the configuration:

```sh
hyprctl plugin unload /home/dzzz83/.config/hypr/plugins/Hyprspace-0.57.0.so
install -m755 Hyprspace.so /home/dzzz83/.config/hypr/plugins/Hyprspace-0.57.0.so
hyprctl plugin load /home/dzzz83/.config/hypr/plugins/Hyprspace-0.57.0.so
hyprctl reload
```

Run the install command from this source directory. Adjust the library name
and loader configuration together when moving to another Hyprland version.
Do not overwrite a loaded shared library in place.

The Lua regression checks cover the 2999/3000 ms boundary, both release orders,
overlapping Super keys, arrow repeats, animation-axis boundaries, cancellation,
configuration unload, empty monitors, and unavailable/unloaded plugins. The
C++ checks cover adjacent/page navigation, empty/singleton lists, boundaries,
invalid directions, and large page sizes. Geometry checks cover centering,
display scale, one/zero/many workspaces, constrained screens, and portrait bounds.

The original strip migration was verified with actual virtual-keyboard events
in a separate Hyprland 0.57.0
session: delayed opening, selection without focus changes, both release
orders, several held arrows, adjacent/page navigation, exclusion of persistent
empty workspaces, Escape cancellation after releasing Super, all four immediate
navigation offsets, repeated Alt+Tab, Super+Space opening Rofi, fullscreen
restoration, reload while open, and a selected workspace closing before commit.
With a top-anchored Waybar, the bar remains at y=0 during the overview and the
original 24-pixel reservation returns after close or unload. The unload check
also confirmed no remaining configuration errors.

That initial build was also checked in the main eDP-1 session at scale
1.2: three-second opening, green selection without changing focus, release
commit, Waybar staying at y=0, restoration of the original reserved area, and
no configuration errors.

The centered mode adds `plugin.overview.centered` and
`plugin.overview.backdropColor`. Its backdrop uses live compositor blur, with
`decoration.blur` controlling the blur appearance. `disableBlur` disables both
the panel and backdrop blur. The existing edge-panel mode remains available
by setting `centered=false` and enabling `affectStrut`.

Centered mode was verified in a disposable 0.57.0 session: sharp previews over
a blurred background, adjacent/page selection, overflow scrolling, stable
window positions and sizes, unchanged reserved space, reload, fullscreen
restoration, and removing the blur on unload. A text-edge measurement outside
the panel dropped from 21.30 to 1.08 while open and recovered after unload,
confirming live blur rather than tint alone. The nested display used its current
preferred mode so reload did not independently resize the test output.

The installed build was visually checked on eDP-1 at scale 1.2. Selection stayed
separate from focus; closing restored all window geometry/fullscreen state and
the original reserved area. Lua checks and C++ navigation/geometry checks passed.
The three-second hold controller was not changed for this appearance update.

Fresh-login startup in the main desktop and separate multi-monitor layouts
remain untested. Startup loading was exercised in fresh nested sessions.

## Rollback

The earlier top strip, including its binary, loader configuration, and a source
snapshot, is preserved in
`/home/dzzz83/Documents/ChatGPT/Hyperland + CachyOS/backups/20261031-hyprspace-centered/`.
Unload the plugin before restoring its binary; then reload the restored plugin
and configuration.

Pre-migration configuration is in:
`/home/dzzz83/Documents/ChatGPT/Hyperland + CachyOS/backups/20261031-hyprspace/`.

Unload the installed plugin, restore `hyprland.lua`, `config/autostart.lua`,
`config/workspace_preview.lua`, `tests/workspace_preview_spec.lua`, and README
from that backup, preserving any later user changes. Reload Hyprland and start:

```sh
env HYPREXPOSE_CONFIG=/home/dzzz83/.config/hypr/workspace-preview.toml /home/dzzz83/.local/bin/hyprexpose --super-preview
```

The previous binary and its configuration have been preserved.
