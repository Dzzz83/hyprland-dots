#!/usr/bin/env bash

SCHEME="prefer-dark"
THEME="Catppuccin-Mauve-Dark"
ICONS="Papirus-Dark"

SCHEMA="gsettings set org.gnome.desktop.interface"

apply_themes() {
    ${SCHEMA} color-scheme "$SCHEME"
    ${SCHEMA} gtk-theme "$THEME"
    ${SCHEMA} icon-theme "$ICONS"
    "$(dirname "$0")/setcursor.sh"
}

apply_themes
