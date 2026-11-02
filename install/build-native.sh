#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
component=${1:-all}
case "$component" in all|capture|workspace|network) ;; *) echo 'Choose all, capture, workspace or network' >&2; exit 2;; esac
ensure_unloaded() {
    if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && command -v hyprctl >/dev/null; then
        local loaded
        loaded=$(hyprctl plugin list)
        if [[ "$loaded" == *"Plugin $1 by"* ]]; then
            echo "Unload $1 or log out of Hyprland before rebuilding its library." >&2
            exit 1
        fi
    fi
}
if [[ "$component" == all || "$component" == capture ]]; then
    ensure_unloaded HyprCapture
    cmake -S "$repo/sources/hyprcapture" -B "$repo/build/hyprcapture" \
        -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DHYPRCAPTURE_GAINMAP_HEIC=OFF \
        -DCMAKE_PREFIX_PATH="$repo/sources/hyprcapture/vendor/nlohmann_json" \
        -DHYPRCAPTURE_DEFAULT_HELPER_PATH="$repo/build/hyprcapture/hyprcapture-ui"
    cmake --build "$repo/build/hyprcapture" --parallel 6 --target hyprcapture hyprcapture-ui hyprcapture-config-test hyprcapture-security-test hyprcapture-annotation-editor-test
fi
if [[ "$component" == all || "$component" == workspace ]]; then
    ensure_unloaded Hyprspace
    mkdir -p "$repo/build/hyprspace" "$repo/plugins"
    # Never replace a plugin while it is loaded in the compositor.
    make -C "$repo/sources/hyprspace" TARGET="$repo/build/hyprspace/Hyprspace.so"
    install -m755 "$repo/build/hyprspace/Hyprspace.so" "$repo/plugins/Hyprspace.so"
fi
if [[ "$component" == all || "$component" == network ]]; then
    cargo build --manifest-path "$repo/sources/wifi-manager/Cargo.toml" \
        --target-dir "$repo/build/cargo" --release --locked --bins
fi
