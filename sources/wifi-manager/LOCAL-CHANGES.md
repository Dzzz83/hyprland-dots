> Historical development/validation notes. Current installation, paths and rebuild steps are in the repository root `README.md` and `docs/MIGRATION.md`.

# Local dismissal behavior

Base revision: `554787423accc3abab5257653e6f74722971ef8d`.

The panel uses a transparent layer-shell surface covering its monitor. The
visible panel keeps its configured alignment, margins, colors, and rounding.
A click outside the panel closes the surface and consumes that click. Clicks
inside the panel continue to its controls.

Opening the panel requests exclusive keyboard focus. Escape is handled in
the capture phase, including when a child control has focus. Hiding the
surface releases keyboard focus and removes its input area.

Build with `cargo build --release --locked --offline` from this directory.
Install `target/release/wifi-manager` at `~/.local/bin/wifi-manager`, then
restart the daemon. The source changes remain as a local patch to the pinned
revision; do not discard them when updating upstream.

Verified on the current single-monitor Hyprland session: Escape immediately
after opening, inside clicks, scrolling, outside clicks on all four sides,
repeated opening/closing, and the existing toggle command. Wi-Fi remained
connected. Password entry, pairing, and separate multi-monitor layouts were
not exercised.

The previous binary and installation notes are saved in
`~/.local/state/hypr-wifi-backups/20261031-115707-before-dismissal-patch/`.
To undo this behavior change, stop wifi-manager, restore that binary to
`~/.local/bin/wifi-manager`, and start it again.

The Wi-Fi / Bluetooth popup no longer includes the collapsible footer,
brightness/volume/temperature sliders, or session/power buttons. Its UI and
controller modules have been removed, so their hardware watchers are not
started by Wi-Fi. Brightness and Warmth now live in SwayNC, configured in
`~/.config/hypr/swaync/config.json`; Warmth uses the independently running
hyprsunset utility through `~/.config/hypr/scripts/display-temperature.py`.

## Sound popup

The separate `audio-panel` binary uses GTK4, layer-shell, and the existing
libpulse dependencies; Wi-Fi network behavior is unchanged.
Waybar's volume button invokes `~/.local/bin/audio-panel --toggle`. The first
click starts a single instance on demand; later launches toggle that instance.
No login service is needed. The popup uses the Wi-Fi palette, font, rounded
corners and top-right placement, with a yellow accent for audio.

Speaker and microphone controls expose 0–100% volume, mute, and default-device
selection. Playback monitor sources are excluded from the microphone list.
Changing defaults also moves streams from the previous default device.
PulseAudio/PipeWire-Pulse subscriptions refresh state for volume keys, mute,
and device connection/removal. A disconnected audio server is retried after
two seconds. Escape, a second toggle, or an outside click
hides the popup and releases keyboard focus. Opening Sound hides Wi-Fi.
Advanced settings opens the existing pavucontrol mixer.

Build and install from this directory:

```sh
cargo build --release --locked --offline --bin audio-panel
install -m755 target/release/audio-panel ~/.local/bin/audio-panel
```

Rebuild after changing `src/bin/audio-panel.rs`, `src/bin/audio_panel/`, or
`resources/audio-panel.css`. The CSS and microphone icons are embedded.
Stop the running audio-panel before replacing an installed build.

Checks:

```sh
cargo test --locked --offline --bin audio-panel
cargo clippy --release --locked --offline --bin audio-panel -- -D warnings
# With the sound popup open, and wtype available:
python tests/audio_panel_smoke.py --wtype /path/to/wtype
```

The smoke test uses AT-SPI and keyboard input to exercise the real sliders,
mute buttons, live volume synchronization, device selectors, and removal of
virtual audio devices. It restores defaults, per-channel volumes and mute
states in a finally block and unloads its virtual devices. Use a quiet session;
it briefly changes volume and default devices.

To roll back, restore the pulseaudio module's `on-click` to `pavucontrol` in
`~/.config/hypr/waybar/config`, reload Waybar, and stop audio-panel. Existing
scroll-to-change-volume behavior remains provided by Waybar.
