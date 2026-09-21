-- Laptop display
hl.monitor({
    output   = "eDP-1",
    mode     = "preferred",
    position = "0x0",
    scale    = 1.2,
})

-- Mirror laptop on external displays
hl.monitor({
    output   = "",
    mode     = "preferred",
    position = "auto",
    scale    = 1,
    mirror   = "eDP-1",
})