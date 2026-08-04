#!/bin/sh
WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
STATE_FILE="/tmp/last_wallpaper.txt"

# Read the last chosen wallpaper
if [ -f "$STATE_FILE" ]; then
    LAST_WALL=$(cat "$STATE_FILE")
else
    LAST_WALL=""
fi

# Pick a wallpaper that is NOT the current one
NEW_WALL=$(find "$WALLPAPER_DIR" -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" -o -name "*.webp" \) | grep -F -v "$LAST_WALL" | shuf -n 1)

# Fallback if only 1 wallpaper exists in total
if [ -z "$NEW_WALL" ]; then
    NEW_WALL=$(find "$WALLPAPER_DIR" -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" -o -name "*.webp" \) | shuf -n 1)
fi

# Save state and apply transition
if [ -n "$NEW_WALL" ]; then
    echo "$NEW_WALL" > "$STATE_FILE"
    awww img "$NEW_WALL" --transition-type outer --transition-fps 60 --transition-step 255
fi
