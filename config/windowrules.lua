-- config/windowrules.lua

-- 1. Bottom-Left: Cava Audio Visualizer
hl.window_rule({
    match = { class = "com.dash.cava" },
    float = true,
    size = { 1010, 244 },
    move = { 16, 640 },
    workspace = "9 silent",
})

-- 2. Top-Right: Terminal Rain
hl.window_rule({
    match = { class = "com.dash.rain" },
    float = true,
    size = { 544, 584 },
    move = { 1040, 40 },
    workspace = "9 silent",
})

-- 3. Bottom-Right: tty-clock
hl.window_rule({
    match = { class = "com.dash.clock" },
    float = true,
    size = { 544, 244 },
    move = { 1040, 640 },
    workspace = "9 silent",
})
