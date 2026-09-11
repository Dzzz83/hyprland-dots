-- config/autostart.lua

hl.on("hyprland.start", function()
    -- Core Bars and System Indicators
    hl.exec_cmd("waybar")
    hl.exec_cmd("swaync")
    hl.exec_cmd("nm-applet --indicator")

    -- Wallpaper Engine
    hl.exec_cmd("awww-daemon")
    hl.exec_cmd("sleep 1 && awww img ~/Pictures/wallhaven-lyjldl_1920x1080.png")

    -- Setup fcitx5
    hl.exec_cmd("fcitx5")

    -- Setup screen sharing
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")

    -- Setup clipboard
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")

    -- Setup themes
    hl.exec_cmd("~/.config/viegphunt/gtkthemes.sh")

    -- ==========================================
    -- Workspace 9 Dashboard Layout
    -- ==========================================
    
    -- Launch Firefox with exact inline dashboard geometry silently on Workspace 9
    -- Height scaled 655 * 1.11 = 727. Y scaled 45 * 1.11 = 50.
    hl.exec_cmd("[float; size 920 727; move 20 50; workspace 9 silent] firefox --new-window https://www.youtube.com")
    
    -- Launch terminal dashboard apps
    hl.exec_cmd("ghostty --class=com.dash.cava -e cava")
    hl.exec_cmd("ghostty --class=com.dash.rain -e cbonsai -li")
    hl.exec_cmd("ghostty --class=com.dash.clock -e tty-clock -c")
end)