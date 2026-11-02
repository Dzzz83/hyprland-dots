-- config/binds.lua
local mainMod = "SUPER"
local workspace_preview = require("config.workspace_preview")
local capture = require("config.capture")

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
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd("~/.config/hypr/scripts/clipboard_launcher.sh"))
hl.bind(mainMod .. " + Period", hl.dsp.exec_cmd("~/.config/hypr/scripts/emoji_launcher.sh"))
hl.bind(mainMod .. " + SHIFT + W", hl.dsp.exec_cmd("~/.config/hypr/scripts/wallpaper_random.sh"))
hl.bind(mainMod .. " + SHIFT + S", capture.open)
hl.bind(mainMod .. " + SHIFT + R", hl.dsp.exec_cmd("~/.local/bin/screen-record"))
hl.bind(mainMod .. " + H", hl.dsp.exec_cmd("~/.config/hypr/scripts/key_hints.sh"))
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("loginctl lock-session"))
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("swaync-client -t -sw"))
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.exec_cmd("hyprctl activewindow | grep pid | tr -d 'pid:' | xargs kill"))
hl.bind("CTRL + SHIFT + Escape", hl.dsp.exec_cmd("ghostty --class=floating_btop -e btop"))

-- ==========================================
-- 2D Workspace Navigation (Native & Dynamic)
-- ==========================================

-- Super arrows always switch workspaces; Alt arrows select an open preview.
for _, direction in ipairs({ "left", "right", "up", "down" }) do
    hl.bind(mainMod .. " + " .. direction, function()
        workspace_preview.move_workspace(direction)
    end, { repeating = true })
    hl.bind("ALT + " .. direction, function()
        workspace_preview.move(direction)
    end, { repeating = true })
end
hl.bind("ALT + Escape", hl.dsp.no_op())

-- Super + Shift + Left/Right: Move active window to next/prev workspace and follow it
hl.bind(mainMod .. " + SHIFT + left", function()
    hl.dispatch(hl.dsp.window.move({ workspace = "-1" }))
end)

hl.bind(mainMod .. " + SHIFT + right", function()
    hl.dispatch(hl.dsp.window.move({ workspace = "+1" }))
end)

-- Alt+Tab: Toggle the two most recently focused workspaces.
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
