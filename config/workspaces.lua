local machine = require("config.machine")
for i = 1, 20 do
    hl.workspace_rule({ workspace = tostring(i), monitor = machine.primary_monitor })
end
