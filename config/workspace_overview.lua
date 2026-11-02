-- Built for the installed Hyprland revision; rebuild after compositor updates.
hl.plugin.load(os.getenv("HOME") .. "/.config/hypr/plugins/Hyprspace.so")

if not (hl.plugin.overview and hl.plugin.overview.begin_selection) then
    return
end

hl.config({ plugin = { overview = {
    centered = true,
    panelColor = "rgba(1e1e2ee0)",
    panelBorderColor = "rgba(585b7080)",
    backdropColor = "rgba(11111b66)",
    panelBorderWidth = 1,
    workspaceActiveBackground = "rgba(a6e3a119)",
    workspaceInactiveBackground = "rgba(18182580)",
    workspaceActiveBorder = "rgba(a6e3a1ff)",
    workspaceInactiveBorder = "rgba(585b7080)",
    workspaceBorderSize = 2,
    panelHeight = 225,
    reservedArea = 0,
    workspaceMargin = 18,
    centerAligned = true,
    hideRealLayers = false,
    hideTopLayers = true,
    hideOverlayLayers = true,
    drawActiveWorkspace = true,
    affectStrut = false,
    overrideGaps = false,
    onlyOccupiedWorkspaces = true,
    showNewWorkspace = false,
    showEmptyWorkspace = false,
    showSpecialWorkspace = false,
    disableGestures = true,
    disableBlur = false,
    exitOnSwitch = true,
    autoScroll = false,
    -- The hold controller handles Escape, including either key-release order.
    exitKey = "",
} } })
