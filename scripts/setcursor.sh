#!/usr/bin/env bash
set -euo pipefail
cursor_theme="${1:-breeze_cursors}"
gsettings set org.gnome.desktop.interface cursor-theme "$cursor_theme"
