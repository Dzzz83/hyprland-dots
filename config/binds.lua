-- config/binds.lua
local mainMod = "SUPER"

hl.bind(mainMod .. " + Return", hl.dsp.exec_cmd("ghostty"))

-- Window & System Actions
hl.bind(mainMod .. " + Q", hl.dsp.window.close())
hl.bind(mainMod .. " + SHIFT + CTRL + Escape", hl.dsp.exit())
hl.bind(mainMod .. " + F", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo())
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))

-- App Launchers
hl.bind(mainMod .. " + Space", hl.dsp.exec_cmd("rofi -show drun"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd("nemo"))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd("brave"))
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd("~/.config/viegphunt/clipboard_launcher.sh"))
hl.bind(mainMod .. " + Period", hl.dsp.exec_cmd("~/.config/viegphunt/emoji_launcher.sh"))
hl.bind(mainMod .. " + SHIFT + W", hl.dsp.exec_cmd("~/.config/viegphunt/wallpaper_random.sh"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.exec_cmd("hyprshot -m region -o $HOME/Pictures/Screenshots"))
hl.bind(mainMod .. " + H", hl.dsp.exec_cmd("~/.config/viegphunt/key_hints.sh"))
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("loginctl lock-session"))
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("swaync-client -t -sw"))
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.exec_cmd("hyprctl activewindow | grep pid | tr -d 'pid:' | xargs kill"))
hl.bind("CTRL + SHIFT + Escape", hl.dsp.exec_cmd("ghostty --class=floating_btop -e btop"))

-- ==========================================
-- 2D Workspace Navigation (Native & Dynamic)
-- ==========================================

-- Super + Left/Right: Cycle previous/next workspace
hl.bind(mainMod .. " + left",  hl.dsp.focus({ workspace = "-1" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ workspace = "+1" }))

-- Super + Shift + Left/Right: Move active window to next/prev workspace and follow it
hl.bind(mainMod .. " + SHIFT + left", function()
    hl.dispatch(hl.dsp.window.move({ workspace = "-1" }))
end)

hl.bind(mainMod .. " + SHIFT + right", function()
    hl.dispatch(hl.dsp.window.move({ workspace = "+1" }))
end)

-- Super + Up/Down: Jump 10 workspaces by triggering +1 ten times instantly
hl.bind(mainMod .. " + up", function()
    for _ = 1, 10 do
        hl.dispatch(hl.dsp.focus({ workspace = "+1" }))
    end
end)

hl.bind(mainMod .. " + down", function()
    for _ = 1, 10 do
        hl.dispatch(hl.dsp.focus({ workspace = "-1" }))
    end
end)

-- Alt+Tab: Go to previous workspace
hl.bind("ALT + Tab", hl.dsp.focus({ workspace = "previous" }))

-- Super + [0-9]: Switch to workspaces 1-10
-- Super + Shift + [0-9]: Move active window to workspaces 1-10
for i = 1, 10 do
    local key = i % 10
    hl.bind(mainMod .. " + " .. key,         hl.dsp.focus({ workspace = i }))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

-- Mouse Binds
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "+1" }), { mouse = true })
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "-1" }), { mouse = true })
hl.bind(mainMod .. " + mouse:272",  hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273",  hl.dsp.window.resize(), { mouse = true })

-- Media & Hardware Keys
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),         { locked = true, repeating = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),       { locked = true })
hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),     { locked = true })
hl.bind("XF86MonBrightnessUp",  hl.dsp.exec_cmd("brightnessctl set +10%"),                           { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown",hl.dsp.exec_cmd("brightnessctl set 10%-"),                           { locked = true, repeating = true })

hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })