#pragma once

#include <algorithm>
#include <cstddef>

struct SOverviewPanelRect {
    double x = 0, y = 0, width = 0, height = 0;
};

// All dimensions are in monitor-local physical pixels.
inline SOverviewPanelRect centeredOverviewPanel(double monitorWidth, double monitorHeight, double requestedHeight,
                                               double padding, size_t workspaceCount) {
    if (monitorWidth <= 0 || monitorHeight <= 0)
        return {};
    padding = std::clamp(padding, 0.0, std::min(monitorWidth, monitorHeight) / 4.0);
    const double availableHeight = monitorHeight - 2 * padding;
    const double minimumHeight = std::min(availableHeight, 2 * padding + 1);
    const double height = std::clamp(requestedHeight, minimumHeight, availableHeight);
    const double tileWidth = std::max(1.0, height - 2 * padding) * monitorWidth / monitorHeight;
    const double count = std::max(size_t{1}, workspaceCount);
    const double width = std::min(monitorWidth - 2 * padding, count * tileWidth + (count + 1) * padding);
    return {(monitorWidth - width) / 2, (monitorHeight - height) / 2, width, height};
}
