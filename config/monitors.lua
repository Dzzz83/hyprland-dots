local machine = require("config.machine")
dofile(os.getenv("HOME") .. "/.config/hypr/machine-profiles/" .. machine.profile .. ".lua")
