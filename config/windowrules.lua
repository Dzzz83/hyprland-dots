-- config/windowrules.lua

-- 1. Bottom-Left: Cava Audio Visualizer
hl.window_rule({
    match = { class = "com.dash.cava" },
    float = true,
    size = { 960, 272 },   -- Reduced 20% from 1200x340
    move = { 16, 576 },    -- Reduced 20% from 20x720
    workspace = "9 silent",
})

-- 2. Top-Right: Bonsai Tree
hl.window_rule({
    match = { class = "com.dash.rain" },
    float = true,
    size = { 736, 480 },
    move = { 784, 36 },
    workspace = "9 silent",
})

-- 3. Bottom-Right: tty-clock
hl.window_rule({
    match = { class = "com.dash.clock" },
    float = true,
    size = { 480, 224 },   -- Reduced 20% from 600x280
    move = { 1040, 624 },  -- Reduced 20% from 1300x780
    workspace = "9 silent",
})