-- config/windowrules.lua

-- Ignore maximize requests from apps
hl.window_rule({
    name = "suppress-maximize-events",
    match = { class = ".*" },
    suppress_event = "maximize",
})

-- Fix some dragging issues with XWayland
hl.window_rule({
    name = "fix-xwayland-drags",
    match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
    no_focus = true,
})

-- Disable blur for floating XWayland windows
hl.window_rule({
    name = "no-blur-xwayland-float",
    match = { xwayland = true, float = true },
    no_blur = true,
})

-- 1. Bottom-Left: Cava Audio Visualizer
hl.window_rule({
    match = { class = "com.dash.cava" },
    float = true,
    size = { 1200, 340 },
    move = { 20, 720 },
    workspace = "9 silent",
})

-- 2. Top-Right: btop System Monitor
hl.window_rule({
    match = { class = "com.dash.btop" },
    float = true,
    size = { 920, 600 },
    move = { 980, 45 },
    workspace = "9 silent",
})

-- 3. Bottom-Right: tty-clock
hl.window_rule({
    match = { class = "com.dash.clock" },
    float = true,
    size = { 600, 280 },
    move = { 1300, 780 },
    workspace = "9 silent",
})