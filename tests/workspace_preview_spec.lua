local function new_preview()
    local commands = {}
    local focuses = {}
    local styles = {}
    local now_ms = 0
    local timer
    local callbacks = {}
    local did_selection_move = true
    local can_begin_selection = true
    local other_modifier_down = false
    local api = {
        on = function(event, callback) callbacks[event] = callback end,
        is_key_down = function() return other_modifier_down end,
        dsp = {
            focus = function(target) return target end,
        },
        dispatch = function(command)
            table.insert(focuses, command.workspace)
        end,
        plugin = { overview = {
            begin_selection = function()
                if can_begin_selection then table.insert(commands, "show") end
                return can_begin_selection
            end,
            move_selection = function(direction)
                table.insert(commands, direction)
                return did_selection_move
            end,
            finish_selection = function(commit)
                table.insert(commands, commit and "commit" or "cancel")
                return commit and 2 or nil
            end,
        } },
        timer = function(callback, options)
            assert(options.timeout == 1000 and options.type == "repeat")
            timer = {
                callback = callback,
                deadline_ms = now_ms + options.timeout,
                set_enabled = function(self, enabled)
                    self.deadline_ms = enabled and (now_ms + options.timeout) or nil
                end,
            }
            return timer
        end,
    }
    local environment = setmetatable({
        hl = api,
        require = function(name)
            assert(name == "config.animations")
            return { set_workspace_style = function(style) table.insert(styles, style) end }
        end,
    }, { __index = _G })
    local preview = assert(loadfile(arg[1] or "config/workspace_preview.lua", "t", environment))()
    return {
        key = function(code, state) callbacks["input.keyboard.key"](code, 0, state) end,
        unload = function() callbacks["config.unload"]() end,
        set_selection_moved = function(value) did_selection_move = value end,
        set_can_begin = function(value) can_begin_selection = value end,
        remove_backend = function() api.plugin.overview = {} end,
        move = preview.move,
        move_workspace = preview.move_workspace,
        commands = commands,
        focuses = focuses,
        styles = styles,
        advance = function(duration_ms)
            now_ms = now_ms + duration_ms
            if timer.deadline_ms and now_ms >= timer.deadline_ms then
                timer.deadline_ms = now_ms + 1000
                timer.callback()
            end
        end,
        set_other_modifier = function(value) other_modifier_down = value end,
    }
end

local function assert_commands(preview, expected)
    assert(table.concat(preview.commands, ",") == expected, table.concat(preview.commands, ","))
end

-- Exact threshold, preview navigation, and both release orders.
for _, alt_first in ipairs({ false, true }) do
    local preview = new_preview()
    preview.advance(6000)
    assert_commands(preview, "")
    preview.key(64, 1)
    preview.advance(999)
    assert_commands(preview, "")
    preview.advance(1)
    preview.key(114, 1)
    preview.move("right")
    if alt_first then preview.key(64, 0) else preview.key(114, 0) end
    assert_commands(preview, "show,right")
    if alt_first then preview.key(114, 0) else preview.key(64, 0) end
    assert_commands(preview, "show,right,commit")
end

-- Either Alt key can sustain the same countdown.
local preview = new_preview()
preview.key(64, 1)
preview.advance(500)
preview.key(108, 1)
preview.key(64, 0)
preview.advance(500)
assert_commands(preview, "show")
preview.key(108, 0)
assert_commands(preview, "show,commit")

-- Tab resets the countdown, including repeated presses and Tab held before Alt.
for _, tab_first in ipairs({ false, true }) do
    preview = new_preview()
    if tab_first then preview.key(23, 1) end
    preview.key(64, 1)
    preview.advance(999)
    if not tab_first then preview.key(23, 1) end
    preview.advance(6000)
    assert_commands(preview, "")
    preview.key(23, 0)
    preview.advance(999)
    assert_commands(preview, "")
    preview.key(23, 1)
    preview.key(23, 0)
    preview.advance(999)
    assert_commands(preview, "")
    preview.advance(1)
    assert_commands(preview, "show")
    preview.advance(6000)
    assert_commands(preview, "show")
end

-- Tab closes an open preview without committing its selection, then rearms.
preview = new_preview()
preview.key(64, 1)
preview.advance(1000)
preview.move("right")
preview.key(23, 1)
assert_commands(preview, "show,right,cancel")
assert(#preview.focuses == 0)
preview.advance(6000)
assert_commands(preview, "show,right,cancel")
preview.key(23, 0)
preview.advance(1000)
assert_commands(preview, "show,right,cancel,show")

-- Arrows neither reset Alt's countdown nor switch workspaces before preview.
for _, move in ipairs({
    { key = 113, direction = "left", workspace = "-1", style = "slide" },
    { key = 114, direction = "right", workspace = "+1", style = "slide" },
    { key = 111, direction = "up", workspace = "+10", style = "slidevert top" },
    { key = 116, direction = "down", workspace = "-10", style = "slidevert bottom" },
}) do
    preview = new_preview()
    preview.key(64, 1)
    preview.advance(500)
    preview.key(move.key, 1)
    preview.move(move.direction)
    assert(#preview.focuses == 0)
    preview.advance(500)
    assert_commands(preview, "show")
    preview.move(move.direction)
    assert_commands(preview, "show," .. move.direction)
    preview.key(move.key, 0)
    preview.key(64, 0)
    assert(table.concat(preview.styles, ",") == move.style .. ",slide")

    -- Super navigation stays immediate regardless of hold duration.
    preview = new_preview()
    preview.key(133, 1)
    preview.advance(6000)
    preview.key(move.key, 1)
    preview.move_workspace(move.direction)
    preview.move_workspace(move.direction)
    preview.key(133, 0)
    preview.key(move.key, 0)
    assert_commands(preview, "")
    assert(#preview.focuses == 2 and preview.focuses[1] == move.workspace)
    assert(table.concat(preview.styles, ",") == move.style .. ",slide," .. move.style .. ",slide")
end

-- Releasing Alt cancels a pending delay; repressing starts a full second.
preview = new_preview()
preview.key(64, 1)
preview.advance(500)
preview.key(64, 0)
preview.advance(6000)
assert_commands(preview, "")
preview.key(64, 1)
preview.advance(999)
assert_commands(preview, "")
preview.advance(1)
assert_commands(preview, "show")

-- Other Alt shortcuts cancel pending and open previews; Tab cannot rearm them.
for _, delay in ipairs({ 500, 1000 }) do
    for _, key in ipairs({ 9, 65, 50, 133 }) do
        preview = new_preview()
        preview.key(64, 1)
        preview.advance(delay)
        preview.key(key, 1)
        preview.key(23, 1)
        preview.key(23, 0)
        preview.advance(6000)
        preview.move("right")
        assert_commands(preview, delay == 1000 and "show,cancel" or "")
        assert(#preview.focuses == 0)
    end
end

preview = new_preview()
preview.set_other_modifier(true)
preview.key(64, 1)
preview.advance(6000)
assert_commands(preview, "")

-- Escape still cancels after Alt release when an arrow remains held.
preview = new_preview()
preview.key(64, 1)
preview.advance(1000)
preview.key(114, 1)
preview.key(64, 0)
preview.key(9, 1)
preview.key(114, 0)
assert_commands(preview, "show,cancel")

-- A boundary key preserves the last successful selection's animation axis.
preview = new_preview()
preview.key(64, 1)
preview.advance(1000)
preview.move("right")
preview.set_selection_moved(false)
preview.move("up")
preview.key(64, 0)
assert(table.concat(preview.styles, ",") == "slide,slide")

for _, delay in ipairs({ 500, 1000 }) do
    preview = new_preview()
    preview.key(64, 1)
    preview.advance(delay)
    preview.unload()
    preview.advance(6000)
    assert_commands(preview, delay == 1000 and "show,cancel" or "")
end

-- Empty monitors or unavailable plugins do not interfere with Super navigation.
for _, unavailable in ipairs({ "empty", "unloaded" }) do
    preview = new_preview()
    if unavailable == "empty" then preview.set_can_begin(false) else preview.remove_backend() end
    preview.key(64, 1)
    preview.advance(1000)
    preview.move("right")
    preview.key(64, 0)
    preview.move_workspace("right")
    assert_commands(preview, "")
    assert(preview.focuses[1] == "+1")
end

preview = new_preview()
preview.key(64, 1)
preview.advance(1000)
preview.remove_backend()
preview.move("right")
preview.key(64, 0)
assert_commands(preview, "show")
assert(#preview.focuses == 0)

print("Alt hold, Tab reset, preview navigation, Super navigation, cancellation, reload, and fallback checks passed.")
