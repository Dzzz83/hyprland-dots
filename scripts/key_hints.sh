#!/usr/bin/env bash
hints="SUPER + ENTER        : Ghostty Terminal
SUPER + SPACE        : App Launcher
SUPER + Q            : Kill Active Window
SUPER + V            : Clipboard History
SUPER + W            : Select Wallpaper
SUPER + SHIFT + W    : Random Wallpaper
SUPER + SHIFT + S    : Screenshot Region
SUPER + N            : SwayNC Panel
SUPER + E            : File Manager
SUPER + B            : Browser
SUPER + L            : Lock Screen"

echo "$hints" | rofi -dmenu -i -p "Keybindings"

