#pragma once

#include <QColor>
#include <QPalette>

namespace hyprcapture::ui::theme {

inline constexpr auto base = "#1e1e2e";
inline constexpr auto mantle = "#181825";
inline constexpr auto surface = "#313244";
inline constexpr auto border = "#585b70";
inline constexpr auto text = "#cdd6f4";
inline constexpr auto muted = "#a6adc8";
inline constexpr auto green = "#a6e3a1";
inline constexpr auto selected = "#405145";
inline constexpr auto red = "#f38ba8";

inline QPalette palette() {
    QPalette colors;
    colors.setColor(QPalette::Window, QColor(base));
    colors.setColor(QPalette::WindowText, QColor(text));
    colors.setColor(QPalette::Base, QColor(mantle));
    colors.setColor(QPalette::AlternateBase, QColor(surface));
    colors.setColor(QPalette::Text, QColor(text));
    colors.setColor(QPalette::Button, QColor(surface));
    colors.setColor(QPalette::ButtonText, QColor(text));
    colors.setColor(QPalette::Highlight, QColor(green));
    colors.setColor(QPalette::Accent, QColor(green));
    colors.setColor(QPalette::HighlightedText, QColor(base));
    colors.setColor(QPalette::ToolTipBase, QColor(mantle));
    colors.setColor(QPalette::ToolTipText, QColor(text));
    colors.setColor(QPalette::PlaceholderText, QColor(muted));
    colors.setColor(QPalette::Link, QColor(green));
    colors.setColor(QPalette::Light, QColor(border));
    colors.setColor(QPalette::Mid, QColor(border));
    colors.setColor(QPalette::Dark, QColor(mantle));
    for (auto role : {QPalette::WindowText, QPalette::Text, QPalette::ButtonText})
        colors.setColor(QPalette::Disabled, role, QColor(muted));
    return colors;
}

} // namespace hyprcapture::ui::theme
