#!/bin/bash

DEVICE="intel_backlight"
MAX_BRIGHTNESS=$(cat /sys/class/backlight/$DEVICE/max_brightness)
CURRENT_BRIGHTNESS=$(cat /sys/class/backlight/$DEVICE/brightness)

# Calculate 10% of the max brightness
STEP=$((MAX_BRIGHTNESS / 10))

if [ "$1" == "up" ]; then
    NEW_BRIGHTNESS=$((CURRENT_BRIGHTNESS + STEP))
    # Don't exceed max
    if [ "$NEW_BRIGHTNESS" -gt "$MAX_BRIGHTNESS" ]; then
        NEW_BRIGHTNESS=$MAX_BRIGHTNESS
    fi
elif [ "$1" == "down" ]; then
    NEW_BRIGHTNESS=$((CURRENT_BRIGHTNESS - STEP))
    # Enforce minimum of 1
    if [ "$NEW_BRIGHTNESS" -lt 1 ]; then
        NEW_BRIGHTNESS=1
    fi
fi

# Send the change through systemd-logind so SwayNC gets the D-Bus signal!
busctl call org.freedesktop.login1 /org/freedesktop/login1/session/auto org.freedesktop.login1.Session SetBrightness "su" $DEVICE $NEW_BRIGHTNESS