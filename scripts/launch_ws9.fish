#!/usr/bin/env fish
# Launch Firefox with exact inline dashboard geometry silently on Workspace 9
hyprctl dispatch exec "[float; size 920 655; move 20 45; workspace 9 silent] firefox --new-window https://www.youtube.com"

# Launch terminal dashboard apps
ghostty --class=com.dash.cava -e cava &
ghostty --class=com.dash.btop -e btop &
ghostty --class=com.dash.clock -e tty-clock -c &
