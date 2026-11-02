#include "Overview.hpp"
#include "Globals.hpp"
#include "PreviewNavigation.hpp"
#include "OverviewGeometry.hpp"

#include <cmath>
#include <climits>
#include <algorithm>

double CHyprspaceWidget::panelTravelDistance() {
    const auto owner = getOwner();
    return std::max(1.0, double(config.panelHeight->value() + config.reservedArea->value()) * (owner ? owner->m_scale : 1.0));
}

CBox CHyprspaceWidget::panelBox(size_t workspaceCount) {
    const auto owner = getOwner();
    if (!owner)
        return {{0, 0}, {0, 0}};
    if (config.centered->value()) {
        const auto panel = centeredOverviewPanel(owner->m_transformedSize.x, owner->m_transformedSize.y,
            config.panelHeight->value() * owner->m_scale, config.workspaceMargin->value() * owner->m_scale, workspaceCount);
        const double openingOffset = std::clamp<double>(curYOffset->value(), 0, panelTravelDistance()) * 0.1;
        return {panel.x, panel.y + openingOffset, panel.width, panel.height};
    }
    const double height = config.panelHeight->value() * owner->m_scale;
    const double reserved = config.reservedArea->value() * owner->m_scale;
    const double y = config.onBottom->value() ? owner->m_transformedSize.y - height - reserved + curYOffset->value()
                                            : reserved - curYOffset->value();
    return {0, y, owner->m_transformedSize.x, height};
}

std::vector<SOverviewWorkspace> CHyprspaceWidget::workspaceTiles() {
    const auto owner = getOwner();
    if (!owner)
        return {};

    std::vector<SOverviewWorkspace> tiles;
    if (config.showSpecialWorkspace->value()) {
        const auto special = findDefaultSpecialWorkspace();
        if (!config.onlyOccupiedWorkspaces->value() || (special && special->getWindowCount() > 0))
            tiles.push_back({.special = true});
    }

    int lowestID = INT_MAX;
    int highestID = 1;
    for (auto& workspace : State::workspaceState()->workspaces()) {
        if (!workspace || !workspace->m_monitor || workspace->m_monitor->m_id != ownerID)
            continue;
        const auto id = workspace->numberedID();
        if (!id || *id < 1 || (config.onlyOccupiedWorkspaces->value() && workspace->getWindowCount() == 0))
            continue;
        tiles.push_back({.numbered = *id});
        lowestID = std::min(lowestID, static_cast<int>(*id));
        highestID = std::max(highestID, static_cast<int>(*id));
    }

    if (!config.onlyOccupiedWorkspaces->value() && config.showEmptyWorkspace->value()) {
        int first = 1;
        int last = highestID;
        if (numWorkspaces > 0) {
            first = std::min<int>(numWorkspaces * ownerID + 1, lowestID);
            last = std::max<int>(numWorkspaces * ownerID + 1, highestID);
        }
        for (int id = first; id <= last; ++id) {
            if (!findNumberedWorkspace(id))
                tiles.push_back({.numbered = static_cast<Workspace::WorkspaceIDContainer>(id)});
        }
    }
    if (!config.onlyOccupiedWorkspaces->value() && config.showNewWorkspace->value()) {
        while (findNumberedWorkspace(highestID))
            ++highestID;
        tiles.push_back({.numbered = static_cast<Workspace::WorkspaceIDContainer>(highestID)});
    }
    std::sort(tiles.begin(), tiles.end(), [](const auto& left, const auto& right) {
        if (left.special != right.special)
            return left.special;
        return left.numbered < right.numbered;
    });
    return tiles;
}

std::vector<Workspace::WorkspaceIDContainer> CHyprspaceWidget::selectionWorkspaces() {
    std::vector<Workspace::WorkspaceIDContainer> ids;
    for (const auto& tile : workspaceTiles()) {
        const auto workspace = tile.special ? nullptr : findNumberedWorkspace(tile.numbered);
        if (workspace && workspace->getWindowCount() > 0)
            ids.push_back(tile.numbered);
    }
    return ids;
}

bool CHyprspaceWidget::beginSelection() {
    const auto owner = getOwner();
    const auto ids = selectionWorkspaces();
    if (!owner || ids.empty())
        return false;
    const auto current = owner->m_activeWorkspace ? owner->m_activeWorkspace->numberedID() : std::nullopt;
    selectedWorkspaceID = current && std::find(ids.begin(), ids.end(), *current) != ids.end() ? *current : ids.front();
    isKeyboardPreview = true;
    show();
    return true;
}

bool CHyprspaceWidget::moveSelection(std::string_view direction) {
    const auto owner = getOwner();
    const auto ids = selectionWorkspaces();
    if (!owner || !active || !isKeyboardPreview || ids.empty())
        return false;
    const auto selected = std::find(ids.begin(), ids.end(), selectedWorkspaceID.value_or(0));
    const size_t index = selected == ids.end() ? 0 : std::distance(ids.begin(), selected);
    const auto panel = panelBox(workspaceTiles().size());
    const double tileHeight = std::max(1.0, panel.h / owner->m_scale - 2 * config.workspaceMargin->value());
    const double tileWidth = tileHeight * owner->m_transformedSize.x / owner->m_transformedSize.y;
    const size_t pageSize = static_cast<size_t>(std::max(1.0, std::floor((panel.w / owner->m_scale) /
                                                                     (tileWidth + config.workspaceMargin->value()))));
    const auto next = ids[previewSelectionIndex(index, ids.size(), pageSize, direction)];
    if (selectedWorkspaceID == next)
        return false;
    selectedWorkspaceID = next;
    owner->scheduleFrame();
    return true;
}

std::optional<Workspace::WorkspaceIDContainer> CHyprspaceWidget::finishSelection(bool commit) {
    const auto ids = selectionWorkspaces();
    std::optional<Workspace::WorkspaceIDContainer> result;
    if (commit && active && isKeyboardPreview && selectedWorkspaceID &&
        std::find(ids.begin(), ids.end(), *selectedWorkspaceID) != ids.end())
        result = selectedWorkspaceID;
    hide();
    return result;
}
