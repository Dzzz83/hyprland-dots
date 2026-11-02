#pragma once

#include <algorithm>
#include <cstddef>
#include <string_view>

// The strip is linear: horizontal arrows move one tile, vertical arrows one page.
inline size_t previewSelectionIndex(size_t selected, size_t count, size_t pageSize, std::string_view direction) {
    if (count == 0)
        return 0;
    selected = std::min(selected, count - 1);
    const size_t distance = (direction == "up" || direction == "down") ? std::max(size_t{1}, pageSize) : 1;
    if (direction == "left" || direction == "up")
        return selected - std::min(selected, distance);
    if (direction == "right" || direction == "down")
        return selected + std::min(count - 1 - selected, distance);
    return selected;
}
