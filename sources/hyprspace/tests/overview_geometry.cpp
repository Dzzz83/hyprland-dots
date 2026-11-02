#include "../src/OverviewGeometry.hpp"
#include <cassert>
#include <cmath>
#include <limits>

static bool near(double left, double right) { return std::abs(left - right) < 0.001; }

int main() {
    const auto panel = centeredOverviewPanel(1920, 1080, 270, 21.6, 4);
    assert(near(panel.width, 1720.8));
    assert(near(panel.x, 99.6));
    assert(near(panel.y, 405));
    assert(near(panel.x + panel.width / 2, 960));
    assert(near(panel.y + panel.height / 2, 540));

    const auto one = centeredOverviewPanel(1920, 1080, 270, 21.6, 1);
    assert(one.width < panel.width);
    const auto overflow = centeredOverviewPanel(1920, 1080, 270, 21.6, std::numeric_limits<size_t>::max());
    assert(near(overflow.width, 1920 - 43.2));
    const auto portrait = centeredOverviewPanel(720, 1280, 2000, 18, 3);
    assert(portrait.y >= 18 && portrait.x >= 18);
    assert(portrait.height <= 1280 - 36 && portrait.width <= 720 - 36);
    const auto empty = centeredOverviewPanel(1920, 1080, 270, 21.6, 0);
    assert(near(empty.width, one.width));
    const auto tiny = centeredOverviewPanel(10, 10, -20, 50, 3);
    assert(tiny.width > 0 && tiny.height > 0 && tiny.x >= 0 && tiny.y >= 0);
    assert(centeredOverviewPanel(0, 0, 270, 18, 4).width == 0);
}
