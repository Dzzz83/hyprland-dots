local path = os.getenv("HOME") .. "/.config/hypr/config/local.lua"
local file = io.open(path, "r")
if file then
    file:close()
    return dofile(path)
end
return { profile = "generic", dashboard = false }
