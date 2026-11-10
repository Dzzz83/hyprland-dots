-- config/autostart.lua

hl.on("hyprland.start", function()
    -- Core Bars and System Indicators
    -- The local Waybar build can hide Steam's original tray menu.
    hl.exec_cmd([[
        waybar_dir="$HOME/.config/hypr"
        if [ -x "$waybar_dir/build/runtime/waybar-steam" ]; then
            exec "$waybar_dir/build/runtime/waybar-steam" -c "$waybar_dir/waybar/steam.jsonc"
        fi
        exec waybar
    ]])
    hl.exec_cmd("python3 $HOME/.config/hypr/scripts/proton-tray-watch.py")
    hl.exec_cmd("swaync")
    -- Use the tested rendering path for Lenovo's system-authentication dialog.
    hl.exec_cmd("env QT_QUICK_BACKEND=software QT_STYLE_OVERRIDE=Fusion QT_QPA_PLATFORMTHEME=gtk3 /usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("python3 $HOME/.config/hypr/scripts/display-temperature.py start")
    hl.exec_cmd("$HOME/.local/bin/wifi-manager")

    -- Wallpaper Engine
    hl.exec_cmd("awww-daemon")
    hl.exec_cmd("sleep 1 && awww img ~/.config/hypr/assets/wallpapers/wallhaven-lyjldl_1920x1080.png")

    -- Setup fcitx5
    hl.exec_cmd("fcitx5")

    -- Setup screen sharing
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")

    -- Setup clipboard
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")

    -- Setup themes
    hl.exec_cmd("~/.config/hypr/scripts/gtkthemes.sh")

    -- ==========================================
    -- Workspace 9 Dashboard Layout
    -- ==========================================
    
    if require("config.machine").dashboard then
    -- Launch Firefox with exact inline dashboard geometry silently on Workspace 9
    hl.exec_cmd("[float; size 1008 584; move 16 40; workspace 9 silent] firefox --new-window https://www.youtube.com")
    
    -- Launch terminal dashboard apps
    hl.exec_cmd("ghostty --class=com.dash.cava --window-padding-x=0 -e cava")
    hl.exec_cmd("ghostty --class=com.dash.rain -e env TERM=xterm-256color $HOME/.local/bin/terminal-rain")
    hl.exec_cmd("ghostty --class=com.dash.clock -e tty-clock -c")
    end
end)
