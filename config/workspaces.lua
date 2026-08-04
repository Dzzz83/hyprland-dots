-- config/workspaces.lua

-- Create 20 persistent workspaces on your laptop monitor
for i = 1, 20 do
    hl.workspace_rule({ workspace = tostring(i), monitor = "eDP-1"})
end