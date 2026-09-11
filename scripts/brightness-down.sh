#!/bin/bash
CURRENT=$(brightnessctl -d intel_backlight get)
if [ "$CURRENT" -gt 1 ]; then
    brightnessctl -d intel_backlight set 5%-
else
    brightnessctl -d intel_backlight set 1
fi