#include "Overview.hpp"
#include "Globals.hpp"
#include <hyprland/src/config/shared/workspace/WorkspaceRuleManager.hpp>
#include <hyprland/src/state/WorkspaceState.hpp>

static void applyGapsRule(Workspace::WorkspaceIDContainer id, const Config::CCssGapData& gapsIn, const Config::CCssGapData& gapsOut) {
    Config::CWorkspaceRule rule;

    // replaceOrAdd() matches on m_workspaceString. 0.57 rules no longer store a parsed id.
    rule.m_workspaceString = std::to_string(id);
    rule.m_gapsIn          = gapsIn;
    rule.m_gapsOut         = gapsOut;

    Config::workspaceRuleMgr()->replaceOrAdd(std::move(rule));
}

// FIXME: preserve original workspace rules
void CHyprspaceWidget::updateLayout() {

    const bool affectsLayout = config.affectStrut->value() && !config.centered->value();
    if (!affectsLayout && !originalReservedArea) return;

    const auto currentHeight = config.panelHeight->value() + config.reservedArea->value();
    const auto pMonitor = getOwner();
    if (!pMonitor) return;

    static auto PGAPSINDATA  = CConfigValue<Config::IComplexConfigValue>("general:gaps_in");
    static auto PGAPSOUTDATA = CConfigValue<Config::IComplexConfigValue>("general:gaps_out");
    if (!PGAPSINDATA.good() || !PGAPSOUTDATA.good()) return;

    const auto PGAPSINBASE  = PGAPSINDATA.ptr();
    const auto PGAPSOUTBASE = PGAPSOUTDATA.ptr();
    if (!PGAPSINBASE || !PGAPSOUTBASE || PGAPSINBASE->getDataType() != Config::CVD_TYPE_CSS_VALUE || PGAPSOUTBASE->getDataType() != Config::CVD_TYPE_CSS_VALUE) return;

    auto* const PGAPSIN  = static_cast<Config::CCssGapData*>(PGAPSINBASE);
    auto* const PGAPSOUT = static_cast<Config::CCssGapData*>(PGAPSOUTBASE);

    // Arrange real panels with their original reservation. Reserving overview
    // space first would move a top-anchored Waybar below the overview itself.
    if (originalReservedArea)
        pMonitor->m_reservedArea = *originalReservedArea;
    g_pHyprRenderer->arrangeLayersForMonitor(ownerID);
    if (active && affectsLayout) {
        originalReservedArea = pMonitor->m_reservedArea;
        const auto& area = *originalReservedArea;
        const double top = config.onBottom->value() ? area.top() : std::max<double>(currentHeight, area.top());
        const double bottom = config.onBottom->value() ? std::max<double>(currentHeight, area.bottom()) : area.bottom();
        pMonitor->m_reservedArea = Desktop::CReservedArea(top, area.right(), bottom, area.left());
    } else {
        originalReservedArea.reset();
    }

    // gaps are created via workspace rules
    // there are no way to write to m_dWorkspaceRules directly
    // and we want to refrain from using function hooks
    // so we create a workspace rule for ALL workspaces through handleWorkspaceRules
    // Geneva Convention violation type hack but idc atm
    if (active && affectsLayout) {
        const auto oActiveWorkspace = pMonitor->m_activeWorkspace;
        if (!oActiveWorkspace) return;
        const auto oActiveID = oActiveWorkspace->numberedID();

        for (auto& ws : State::workspaceState()->workspaces()) { // HACK: recalculate other workspaces without reserved area
            const auto wsID = ws && ws->numberedID() ? ws->numberedID() : std::nullopt;
            if (ws && wsID && ws->m_monitor && ws->m_monitor->m_id == ownerID && (!oActiveID || *wsID != *oActiveID)) {
                pMonitor->m_activeWorkspace = ws.lock();
                if (config.overrideGaps->value()) {
                    applyGapsRule(*wsID, *PGAPSIN, *PGAPSOUT);
                }
                g_layoutManager->recalculateMonitor(pMonitor);
            }
        }
        pMonitor->m_activeWorkspace = oActiveWorkspace;

        if (config.overrideGaps->value() && oActiveID) {
            applyGapsRule(*oActiveID, config.gapsIn->value(), config.gapsOut->value());
        }
        g_layoutManager->recalculateMonitor(pMonitor);

    }
    else {
        for (auto& ws : State::workspaceState()->workspaces()) {
            const auto wsID = ws && ws->numberedID() ? ws->numberedID() : std::nullopt;
            if (wsID && ws->m_monitor && ws->m_monitor->m_id == ownerID) {
                if (config.overrideGaps->value()) {
                    applyGapsRule(*wsID, *PGAPSIN, *PGAPSOUT);
                }
            }
        }
        g_layoutManager->recalculateMonitor(pMonitor);
    }
}
