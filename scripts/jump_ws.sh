#!/bin/bash
dir="$1"

# Get the actual current workspace ID directly from Hyprland
id=$(hyprctl activeworkspace | awk '/workspace ID/ {print $3}')

if [ -z "$id" ]; then
    exit 0
fi

if [ "$dir" = "up" ]; then
    target=$((id + 10))
elif [ "$dir" = "down" ]; then
    target=$((id - 10))
fi

if [ "$target" -ge 1 ] && [ "$target" -le 20 ]; then
    hyprctl dispatch workspace "$target"
fi
