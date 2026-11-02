-- Rebuild this plugin after Hyprland updates; see the source LOCAL-CHANGES.md.
local home = assert(os.getenv("HOME"))
local root = home .. "/.config/hypr"
hl.plugin.load(root .. "/build/hyprcapture/libhyprcapture.so")

if hl.plugin.hyprcapture then
    hl.config({ plugin = { hyprcapture = {
        helper = root .. "/build/hyprcapture/hyprcapture-ui",
        record_window_backend = "compositor",
        save_dir = home .. "/Pictures/Screenshots",
        record_save_dir = home .. "/Videos/Screenrecords",
    } } })
end

local function open()
    if hl.plugin.hyprcapture and hl.plugin.hyprcapture.open_editor then
        hl.plugin.hyprcapture.open_editor()
    else
        -- Keep screenshot capture available if an update prevents plugin loading.
        hl.exec_cmd("hyprshot -m region -o $HOME/Pictures/Screenshots")
    end
end

return { open = open }
