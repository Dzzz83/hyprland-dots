hl.config({
    general = {
        gaps_in = 2,
        gaps_out = 5,
        border_size = 2,
        col = {
            active_border = "rgba(cdd6f4aa)",
            inactive_border = "rgba(595959aa)",
        },
        resize_on_border = true,
        allow_tearing = false,
        layout = "dwindle",
    },
})

hl.config({
    decoration = {
        rounding = 10,
        active_opacity = 0.95,
        inactive_opacity = 0.85,
        fullscreen_opacity = 1.0,
        dim_inactive = true,
        dim_strength = 0.1,
        shadow = {
            enabled = true,
            range = 15,
            render_power = 3,
            color = "rgba(1a1a1aee)",
        },
        blur = {
            enabled = true,
            size = 6,
            passes = 3,
            new_optimizations = true,
            xray = false,
            ignore_opacity = true,
        },
    },
})

hl.config({
    dwindle = {
        preserve_split = true,
    },
    master = {
        new_status = "master",
    },
})

hl.config({
    misc = {
        force_default_wallpaper = 0,
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
        initial_workspace_tracking = 1,
    },
})
