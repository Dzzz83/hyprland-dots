> Historical development/validation notes. Current installation, paths and rebuild steps are in the repository root `README.md` and `docs/MIGRATION.md`.

# Local HyprCapture installation

Installed on 2026-11-02 for the CachyOS Hyprland session.

## Source and build

- Upstream: https://github.com/gfhdhytghd/HyprCapture
- Revision: `fd465d85d953592862e30b296dd69ad746bc79af` (0.5.0).
- Built against installed Hyprland 0.57.0 headers, matching running revision
  `0aa6745f705f2c4b0a5004eb019ef76e5bbdb426` and its library ABI.
- Local toolbar theme changes are described below. No system packages were changed.
- nlohmann/json v3.12.0 is installed locally under `local-deps/install` from
  source revision `55f93686c01528224f448c19128836e7df245f72`.
- OpenCV 5 is found through its existing system CMake package.
- PNG screenshots and video are supported. Optional HDR gain-map HEIC export
  is disabled; the optional TensorFlow Lite echo-cancellation runtime/model
  was not installed.
- The plugin and helper run directly from `build-local`. Keep this checkout
  and its build directory; deleting them disables the new capture tool.

Reconfigure from this directory, with matching installed Hyprland headers:

```bash
cmake -S . -B build-local -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DHYPRCAPTURE_GAINMAP_HEIC=OFF -DOpenCV_DIR=/usr/lib/cmake/opencv5 '-DCMAKE_PREFIX_PATH=$HOME/.config/hypr/sources/hyprcapture/local-deps/install' '-DHYPRCAPTURE_DEFAULT_HELPER_PATH=$HOME/.config/hypr/sources/hyprcapture/build-local/hyprcapture-ui'
cmake --build build-local --parallel 6 --target hyprcapture hyprcapture-ui hyprcapture-config-test hyprcapture-security-test
```

After a Hyprland update, restart into the installed version before rebuilding.
Qt updates also require rebuilding because the helper uses Qt private headers.
Do not rebuild/replace the shared library while it is loaded. Close the overlay
and stop any recording first. Temporarily remove the `capture` require from
`config/binds.lua` and restore its previous screenshot binding (below), reload
Hyprland, and verify `hyprctl plugin list` no longer lists HyprCapture. Rebuild,
restore the capture require and binding, and reload again. Do not unload or
alter Hyprspace.

## Local desktop theme

The helper uses a local Catppuccin Mocha palette with green highlights and soft
white text. This is applied only inside HyprCapture; other Qt applications and
the desktop environment variables are unchanged. Active recording remains red.

- `src/ui/desktop_theme.hpp` holds the colors and Qt palette.
- `src/ui/main.cpp` applies the Fusion widget style and dark color scheme.
- `src/ui/capture_overlay.cpp` uses the green palette for selected capture and
  recording modes, themed borders, rounded corners and a red active recorder.
- `src/ui/annotation_editor.cpp` uses the same dark colors for the annotation
  strip, popups, text controls and tool highlights. The existing Light option
  remains available; a fresh editor defaults to the application dark palette.
  Annotation drawing colors and screenshot pixels are unchanged.

Rebuild the helper after editing these files:

```bash
cmake --build build-local --parallel 6 --target hyprcapture-ui hyprcapture-annotation-editor-test
ctest --test-dir build-local --output-on-failure -R '^(annotation-editor|session-startup-ui)$'
```

Close the capture overlay before rebuilding. The compositor plugin itself was
not rebuilt or replaced for the theme change. Both existing checks passed, and
the capture and annotation toolbars were visually checked together in the live
session. Preserve this header and these changes when updating the checkout.

## Desktop integration

`~/.config/hypr/config/capture.lua` loads the plugin, sets the helper path,
selects the compositor recording backend, and sets output directories.
`config/binds.lua` requires that module and binds Super + Shift + S to
`capture.open`, which opens `hl.plugin.hyprcapture.open_editor()`.
The shared overlay supports screenshot and recording selection. Reopen it and
click the checked record circle to stop recording. Sound defaults to Off;
choose System, Microphone or Mix when needed. Super + Shift + R keeps the
previous recorder.

Screenshots: `~/Pictures/Screenshots`. Videos: `~/Videos/Screenrecords`.
If the plugin cannot load, the shortcut falls back to the previous Hyprshot
region capture. This fallback provides screenshots only.

## Verification

- Plugin and helper built successfully; plugin loaded alongside Hyprspace.
- Lua syntax and `git diff --check` passed; Hyprland reported no config errors.
- Shared overlay was opened through the exact function used by the binding
  and visually inspected; screenshot and recording controls were present.
- Ten focused upstream CTest checks passed: capture-render, config-reload,
  offscreen-render-scope, session-lock, capture-integration,
  hyprcapture-config-test, hyprcapture-security-test, recording-transcode,
  recording-permissions, session-startup-ui. The last three required execution
  outside the sandbox because they bind private Unix sockets.
- Live fullscreen PNG save and clipboard output passed; previous clipboard
  content was restored after validation.
- A roughly three-second region MP4 with a system-audio track finalized and
  decoded successfully through FFmpeg. Audio finalization is asynchronous;
  a readable video file can briefly exist before its audio track is muxed.
- Microphone capture and HDR output were not tested. Mouse-driven selection
  and annotation were not automated end to end.
- Temporary validation scripts and captures were removed.

## Rollback

In `~/.config/hypr/config/binds.lua`, remove
`local capture = require("config.capture")` and replace the screenshot binding
with:

```lua
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.exec_cmd("hyprshot -m region -o $HOME/Pictures/Screenshots"))
```

Reload with `hyprctl reload`, and verify the plugin is absent from
`hyprctl plugin list`. The unused `config/capture.lua` and this checkout can
then be removed if desired. Keep user-created screenshots and recordings.
