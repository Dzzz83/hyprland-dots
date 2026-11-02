-- Keep selection separate from workspace focus until the navigation keys are released.
local animations = require("config.animations")
local pressed = {}
local is_preview_active = false
local is_canceled = false
local preview_style = "slide"
local alt_keys = { [64] = true, [108] = true }
local arrow_keys = { [111] = true, [113] = true, [114] = true, [116] = true }
local immediate_moves = {
    left = { workspace = "-1", style = "slide" },
    right = { workspace = "+1", style = "slide" },
    up = { workspace = "+10", style = "slidevert top" },
    down = { workspace = "-10", style = "slidevert bottom" },
}

local function switch_workspace(workspace, style)
    animations.set_workspace_style(style)
    hl.dispatch(hl.dsp.focus({ workspace = workspace }))
    -- Dispatch captures the animation direction before restoring the default.
    animations.set_workspace_style("slide")
end

local function has_navigation_key_down()
    for key in pairs(pressed) do
        if alt_keys[key] or arrow_keys[key] or key == 23 then
            return true
        end
    end
    return false
end

local function has_other_modifier_down()
    for _, key in ipairs({ "Super_L", "Super_R", "Control_L", "Control_R", "Shift_L", "Shift_R" }) do
        if hl.is_key_down(key) then
            return true
        end
    end
    return false
end

-- A repeat timer can be disabled and restarted; native one-shot timers expire.
local hold_timer
hold_timer = hl.timer(function()
    hold_timer:set_enabled(false)
    if (pressed[64] or pressed[108]) and not pressed[23] and not is_canceled then
        local overview = hl.plugin.overview
        if overview and overview.begin_selection then
            preview_style = "slide"
            is_preview_active = overview.begin_selection()
        end
    end
end, { timeout = 1000, type = "repeat" })
hold_timer:set_enabled(false)

local function cancel()
    hold_timer:set_enabled(false)
    if is_preview_active then
        local overview = hl.plugin.overview
        if overview and overview.finish_selection then
            overview.finish_selection(false)
        end
        is_preview_active = false
    end
    is_canceled = true
end

hl.on("input.keyboard.key", function(key, _, state)
    local was_alt_down = pressed[64] or pressed[108]
    if alt_keys[key] or arrow_keys[key] or key == 23 then
        pressed[key] = state ~= 0 or nil
    end

    if state == 1 and alt_keys[key] and not was_alt_down and not is_preview_active and not is_canceled then
        if has_other_modifier_down() then
            is_canceled = true
        elseif not pressed[23] then
            hold_timer:set_enabled(true)
        end
    elseif key == 23 and was_alt_down and not is_canceled then
        -- Alt+Tab keeps its native workspace toggle, even during a preview.
        if is_preview_active then
            cancel()
            is_canceled = false
        end
        hold_timer:set_enabled(false)
        if state == 0 then
            hold_timer:set_enabled(true)
        end
    elseif state == 1 and not alt_keys[key] and not arrow_keys[key] and key ~= 23 and (was_alt_down or is_preview_active) then
        -- Other Alt shortcuts keep their normal behavior.
        cancel()
    end

    if not (pressed[64] or pressed[108]) then
        hold_timer:set_enabled(false)
    end

    if not has_navigation_key_down() then
        if is_preview_active then
            local overview = hl.plugin.overview
            local target = overview and overview.finish_selection and overview.finish_selection(true)
            if target then
                switch_workspace(target, preview_style)
            end
            is_preview_active = false
        end
        is_canceled = false
    end
end)

hl.on("config.unload", cancel)

return {
    move = function(direction)
        if is_canceled or not (pressed[64] or pressed[108]) or not is_preview_active then
            return
        end
        local overview = hl.plugin.overview
        if overview and overview.move_selection and overview.move_selection(direction) then
            preview_style = immediate_moves[direction].style
        end
    end,
    move_workspace = function(direction)
        local move = immediate_moves[direction]
        switch_workspace(move.workspace, move.style)
    end,
}
