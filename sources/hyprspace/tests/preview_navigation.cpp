#include "../src/PreviewNavigation.hpp"
#include <cassert>
#include <limits>

int main() {
    assert(previewSelectionIndex(0, 4, 3, "left") == 0);
    assert(previewSelectionIndex(3, 4, 3, "right") == 3);
    assert(previewSelectionIndex(0, 4, 3, "right") == 1);
    assert(previewSelectionIndex(2, 4, 3, "left") == 1);
    assert(previewSelectionIndex(0, 8, 3, "down") == 3);
    assert(previewSelectionIndex(7, 8, 3, "up") == 4);
    assert(previewSelectionIndex(6, 8, 3, "down") == 7);
    assert(previewSelectionIndex(1, 8, 3, "up") == 0);
    assert(previewSelectionIndex(0, 0, 3, "right") == 0);
    assert(previewSelectionIndex(0, 1, 3, "down") == 0);
    assert(previewSelectionIndex(99, 4, 0, "left") == 2);
    assert(previewSelectionIndex(1, 4, std::numeric_limits<size_t>::max(), "down") == 3);
    assert(previewSelectionIndex(1, 4, 3, "invalid") == 1);
}
