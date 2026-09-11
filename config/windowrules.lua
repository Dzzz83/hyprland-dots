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

-- ==========================================
-- Workspace 9 - Dashboard Layout (Scaled for 3200x2000 @ 1.67)
-- Widths kept original, Heights scaled by 1.11
-- ==========================================

-- 1. Bottom-Left: Cava Audio Visualizer
hl.window_rule({
    match = { class = "com.dash.cava" },
    float = true,
    size = { 1200, 377 },   -- Height scaled 340 * 1.11
    move = { 20, 799 },      -- Y scaled 720 * 1.11
    workspace = "9 silent",
})

-- 2. Top-Right: Bonsai Tree (com.dash.rain)
hl.window_rule({
    match = { class = "com.dash.rain" },
    float = true,
    size = { 920, 666 },    -- Height scaled 600 * 1.11
    move = { 980, 50 },     -- Y scaled 45 * 1.11
    workspace = "9 silent",
})

-- 3. Bottom-Right: tty-clock
hl.window_rule({
    match = { class = "com.dash.clock" },
    float = true,
    size = { 600, 311 },    -- Height scaled 280 * 1.11
    move = { 1300, 866 },   -- Y scaled 780 * 1.11
    workspace = "9 silent",
})