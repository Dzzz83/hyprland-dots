#include "Overview.hpp"
#include "Globals.hpp"
#include <hyprland/src/desktop/view/window/WindowPresentation.hpp>
#include <hyprland/src/render/Context.hpp>
#include <hyprland/src/helpers/memory/Memory.hpp>
#include <hyprland/src/config/shared/complex/ComplexDataTypes.hpp>
#include <hyprland/src/render/pass/RectPassElement.hpp>
#include <hyprland/src/render/pass/BorderPassElement.hpp>
#include <hyprland/src/render/pass/SurfacePassElement.hpp>
#include <hyprland/src/render/pass/RendererHintsPassElement.hpp>
#include <hyprland/src/state/WorkspaceState.hpp>
#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprlang.hpp>
#include <hyprutils/utils/ScopeGuard.hpp>
#include <algorithm>


static Render::CRenderContext* g_overviewContext = nullptr;

static Render::CRenderContext& overviewContext() {
    return g_overviewContext ? *g_overviewContext : g_pHyprRenderer->context();
}

static Render::CRenderPass& overviewPass() {
    return Render::IHyprRenderer::currentPass(overviewContext());
}

void renderRect(CBox box, CHyprColor color, int rounding = 0) {
    CRectPassElement::SRectData rectdata;
    rectdata.color = color;
    rectdata.box = box;
    rectdata.round = rounding;
    rectdata.clipBox = overviewContext().m_data.clipBox;
    overviewPass().add(makeUnique<CRectPassElement>(rectdata));
}

void renderRectWithBlur(CBox box, CHyprColor color, int rounding = 0, float blurStrength = 1.F) {
    CRectPassElement::SRectData rectdata;
    rectdata.color = color;
    rectdata.box = box;
    rectdata.blur = true;
    rectdata.round = rounding;
    rectdata.blurA = blurStrength;
    rectdata.clipBox = overviewContext().m_data.clipBox;
    overviewPass().add(makeUnique<CRectPassElement>(rectdata));
}

void renderBorder(CBox box, const Config::CGradientValueData& gradient, int size, int rounding = 0) {
    CBorderPassElement::SBorderData data;
    data.box = box;
    data.grad1 = gradient;
    data.round = rounding;
    data.a = 1.f;
    data.borderSize = size;
    overviewPass().add(makeUnique<CBorderPassElement>(data));
}

void renderWindowStub(PHLWINDOW pWindow, PHLMONITOR pMonitor, PHLWORKSPACE pWorkspaceOverride, CBox rectOverride, CBox clipBox, const Time::steady_tp& time) {
    if (!pWindow || !pMonitor || !pWorkspaceOverride) return;
    if (!pWindow->mapped() || !pWindow->wlSurface() || !pWindow->wlSurface()->resource()) return;

    Render::SRenderModifData renderModif;

    const auto oRealPosition = pWindow->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT);
    const auto oSize = pWindow->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT);
    const float    logicalW = std::max((float)oSize.x, 5.F);
    const float    scaleMod = rectOverride.w / std::max(logicalW * pMonitor->m_scale, 5.F);
    if (!(scaleMod > 0.F) || !(rectOverride.w > 0 && rectOverride.h > 0)) return;

    const Vector2D logicalTL = oRealPosition + pWindow->presentation().floatingOffset();
    const Vector2D scaledTL  = (logicalTL - pMonitor->m_position) * pMonitor->m_scale;
    const Vector2D translate = rectOverride.pos() / scaleMod - scaledTL;

    renderModif.modifs.push_back(std::make_pair(Render::SRenderModifData::eRenderModifType::RMOD_TYPE_TRANSLATE, std::any(translate)));
    renderModif.modifs.push_back(std::make_pair(Render::SRenderModifData::eRenderModifType::RMOD_TYPE_SCALE, std::any(scaleMod)));
    renderModif.enabled = true;

    overviewPass().add(makeUnique<CRendererHintsPassElement>(CRendererHintsPassElement::SData{.renderModif = renderModif}));
    Hyprutils::Utils::CScopeGuard x([] {
        overviewPass().add(makeUnique<CRendererHintsPassElement>(CRendererHintsPassElement::SData{.renderModif = Render::SRenderModifData{}}));
    });

    g_pHyprRenderer->damageWindow(pWindow);

    CSurfacePassElement::SRenderData renderdata = {pMonitor, time};
    renderdata.pos                  = oRealPosition + pWindow->presentation().floatingOffset();
    renderdata.w                    = std::max(oSize.x, 5.0);
    renderdata.h                    = std::max(oSize.y, 5.0);
    renderdata.surface              = pWindow->wlSurface()->resource();
    renderdata.dontRound            = Fullscreen::controller()->isFullscreen(pWindow, Fullscreen::FSMODE_FULLSCREEN);
    renderdata.fadeAlpha            = 1.F;
    renderdata.alpha                = 0.999F;
    renderdata.decorate             = false;
    renderdata.rounding             = renderdata.dontRound ? 0 : pWindow->presentation().rounding() * scaleMod * pMonitor->m_scale;
    renderdata.roundingPower        = renderdata.dontRound ? 2.0F : pWindow->presentation().roundingPower();
    renderdata.blur                 = false;
    renderdata.pWindow              = pWindow;
    renderdata.clipBox              = clipBox;
    renderdata.useNearestNeighbor   = false;
    renderdata.squishOversized      = true;
    renderdata.surfaceCounter       = 0;

    pWindow->wlSurface()->resource()->breadthfirst(
        [&renderdata, &pWindow](SP<CWLSurfaceResource> s, const Vector2D& offset, void* data) {
            if (!s || !s->m_current.texture)
                return;

            if (s->m_current.size.x < 1 || s->m_current.size.y < 1)
                return;

            renderdata.localPos    = offset;
            renderdata.texture     = s->m_current.texture;
            renderdata.surface     = s;
            renderdata.mainSurface = s == pWindow->wlSurface()->resource();
            overviewPass().add(makeUnique<CSurfacePassElement>(renderdata));
            renderdata.surfaceCounter++;
        },
        nullptr);
}

void renderLayerStub(PHLLS pLayer, PHLMONITOR pMonitor, CBox rectOverride, CBox clipBox, const Time::steady_tp& time) {
    if (!pLayer || !pMonitor) return;

    if (!pLayer->mapped() || !pLayer->m_layerSurface || !pLayer->wlSurface() || !pLayer->wlSurface()->resource()) return;

    Vector2D oRealPosition = pLayer->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT);
    Vector2D oSize = pLayer->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT);

    const float curScaling = rectOverride.w / (oSize.x);
    if (!(curScaling > 0.F) || !(rectOverride.w > 0 && rectOverride.h > 0)) return;

    Render::SRenderModifData renderModif;

    renderModif.modifs.push_back(std::make_pair(Render::SRenderModifData::eRenderModifType::RMOD_TYPE_TRANSLATE, std::any(pMonitor->m_position + (rectOverride.pos() / curScaling) - oRealPosition)));
    renderModif.modifs.push_back(std::make_pair(Render::SRenderModifData::eRenderModifType::RMOD_TYPE_SCALE, std::any(curScaling)));
    renderModif.enabled = true;

    overviewPass().add(makeUnique<CRendererHintsPassElement>(CRendererHintsPassElement::SData{.renderModif = renderModif}));
    Hyprutils::Utils::CScopeGuard x([] {
        overviewPass().add(makeUnique<CRendererHintsPassElement>(CRendererHintsPassElement::SData{.renderModif = Render::SRenderModifData{}}));
    });

    CSurfacePassElement::SRenderData renderdata = {pMonitor, time, oRealPosition};
    renderdata.fadeAlpha                        = 1.F;
    renderdata.alpha                            = 0.999F;
    renderdata.blur                             = false;
    renderdata.surface                          = pLayer->wlSurface()->resource();
    renderdata.decorate                         = false;
    renderdata.w                                = oSize.x;
    renderdata.h                                = oSize.y;
    renderdata.pLS                              = pLayer;
    renderdata.clipBox                          = clipBox;
    renderdata.surfaceCounter                   = 0;

    pLayer->wlSurface()->resource()->breadthfirst(
        [&renderdata, &pLayer](SP<CWLSurfaceResource> s, const Vector2D& offset, void* data) {
            if (!s || !s->m_current.texture)
                return;

            if (s->m_current.size.x < 1 || s->m_current.size.y < 1)
                return;

            renderdata.localPos    = offset;
            renderdata.texture     = s->m_current.texture;
            renderdata.surface     = s;
            renderdata.mainSurface = s == pLayer->wlSurface()->resource();
            overviewPass().add(makeUnique<CSurfacePassElement>(renderdata));
            renderdata.surfaceCounter++;
        },
        &renderdata);
}

// NOTE: rects and clipbox positions are relative to the monitor, while damagebox and layers are not, what the fuck? xd
void CHyprspaceWidget::draw(Render::CRenderContext& ctx) {
    g_overviewContext = &ctx;
    Hyprutils::Utils::CScopeGuard resetContext([] { g_overviewContext = nullptr; });

    workspaceBoxes.clear();

    if (!active && !curYOffset->isBeingAnimated()) return;

    auto owner = getOwner();

    if (!owner) return;

    // Full-monitor clip in monitor-local coords. Never use default CBox() to "clear" clipBox —
    // hyprutils::CBox() only sets w/h to 0 and leaves x/y uninitialized, which corrupts scissor state.
    const CBox monitorClip = {{0, 0}, owner->m_transformedSize};

    const auto time = Time::steadyNow();

    owner->m_blurFBShouldRender = true;

    const auto workspaces = workspaceTiles();
    const auto widgetBox = panelBox(workspaces.size());
    const bool isCentered = config.centered->value();
    const double padding = config.workspaceMargin->value() * owner->m_scale;
    const int rounding = isCentered ? static_cast<int>(20 * owner->m_scale) : 0;
    overviewContext().m_data.clipBox = monitorClip;

    if (isCentered) {
        const float progress = 1.F - std::clamp<double>(curYOffset->value() / panelTravelDistance(), 0, 1);
        auto backdrop = CHyprColor(config.backdropColor->value());
        backdrop.a *= progress;
        // Live blur samples the desktop already drawn, before sharp previews.
        if (!config.disableBlur->value())
            renderRectWithBlur(monitorClip, backdrop, 0, progress);
        else
            renderRect(monitorClip, backdrop);
    }

    if (!config.disableBlur->value())
        renderRectWithBlur(widgetBox, config.panelBaseColor->value(), rounding);
    else
        renderRect(widgetBox, config.panelBaseColor->value(), rounding);

    if (config.panelBorderWidth->value() > 0) {
        if (isCentered)
            renderBorder(widgetBox, Config::CGradientValueData(config.panelBorderColor->value()), config.panelBorderWidth->value(), rounding);
        else {
            const double edgeY = config.onBottom->value() ? widgetBox.y : widgetBox.y + widgetBox.h;
            renderRect({widgetBox.x, edgeY, widgetBox.w, double(config.panelBorderWidth->value())}, config.panelBorderColor->value());
        }
    }

    const CBox contentClip = isCentered ? CBox{widgetBox.x + padding / 2, widgetBox.y + padding / 2,
                                               widgetBox.w - padding, widgetBox.h - padding} : monitorClip;
    overviewContext().m_data.clipBox = contentClip;
    g_pHyprRenderer->damageMonitor(owner);

    // render workspace boxes
    int wsCount = workspaces.size();
    double monitorSizeScaleFactor = std::max(1.0, widgetBox.h - 2 * padding) / owner->m_transformedSize.y;
    double workspaceBoxW = owner->m_transformedSize.x * monitorSizeScaleFactor;
    double workspaceBoxH = owner->m_transformedSize.y * monitorSizeScaleFactor;
    double workspaceGroupWidth = workspaceBoxW * wsCount + (config.workspaceMargin->value() * owner->m_scale) * (wsCount - 1);
    const double stripOriginX = widgetBox.x + (config.centerAligned->value() ? (widgetBox.w - workspaceGroupWidth) / 2. : padding);
    double curWorkspaceRectOffsetY = widgetBox.y + padding;
    double workspaceOverflowSize = std::max<double>(((workspaceGroupWidth - widgetBox.w) / 2) + (config.workspaceMargin->value() * owner->m_scale), 0);

    double scrollGoal = workspaceScrollOffset->goal();
    if (isKeyboardPreview && selectedWorkspaceID) {
        const auto selected = std::find_if(workspaces.begin(), workspaces.end(), [&](const auto& tile) {
            return !tile.special && tile.numbered == selectedWorkspaceID;
        });
        if (selected != workspaces.end()) {
            const double left = stripOriginX + scrollGoal + std::distance(workspaces.begin(), selected) *
                                (workspaceBoxW + config.workspaceMargin->value() * owner->m_scale);
            const double margin = config.workspaceMargin->value() * owner->m_scale;
            if (left < widgetBox.x + margin)
                scrollGoal += widgetBox.x + margin - left;
            else if (left + workspaceBoxW > widgetBox.x + widgetBox.w - margin)
                scrollGoal -= left + workspaceBoxW - (widgetBox.x + widgetBox.w - margin);
        }
    }
    *workspaceScrollOffset = std::clamp(scrollGoal, -workspaceOverflowSize, workspaceOverflowSize);
    double curWorkspaceRectOffsetX = stripOriginX + workspaceScrollOffset->value();

    if (!(workspaceBoxW > 0 && workspaceBoxH > 0)) return;
    for (const auto& tile : workspaces) {
        const auto ws = tile.special ? findDefaultSpecialWorkspace() : findNumberedWorkspace(tile.numbered);
        const bool activeTile = tile.special ? (ws && ws == owner->m_activeSpecialWorkspace) : (ws == owner->m_activeWorkspace);
        CBox curWorkspaceBox = {curWorkspaceRectOffsetX, curWorkspaceRectOffsetY, workspaceBoxW, workspaceBoxH};
        const auto tileClip = curWorkspaceBox.intersection(contentClip);
        if (tileClip.empty()) {
            curWorkspaceRectOffsetX += workspaceBoxW + padding;
            continue;
        }
        const bool isTileFullyVisible = curWorkspaceBox.x >= contentClip.x &&
                                        curWorkspaceBox.x + curWorkspaceBox.w <= contentClip.x + contentClip.w;

        // workspace background rect (NOT background layer) and border
        const bool highlightedTile = isKeyboardPreview ? (!tile.special && selectedWorkspaceID == tile.numbered) : activeTile;
        if (highlightedTile) {
            if (isTileFullyVisible && config.workspaceBorderSize->value() >= 1 && CHyprColor(config.workspaceActiveBorder->value()).a > 0) {
                renderBorder(curWorkspaceBox, Config::CGradientValueData(config.workspaceActiveBorder->value()), config.workspaceBorderSize->value());
            }
            if (!config.disableBlur->value()) {
                renderRectWithBlur(curWorkspaceBox, config.workspaceActiveBackground->value()); // cant really round it until I find a proper way to clip windows to a rounded rect
            }
            else {
                renderRect(curWorkspaceBox, config.workspaceActiveBackground->value());
            }
        }
        else {
            if (isTileFullyVisible && config.workspaceBorderSize->value() >= 1 && CHyprColor(config.workspaceInactiveBorder->value()).a > 0) {
                renderBorder(curWorkspaceBox, Config::CGradientValueData(config.workspaceInactiveBorder->value()), config.workspaceBorderSize->value());
            }
            if (!config.disableBlur->value()) {
                renderRectWithBlur(curWorkspaceBox, config.workspaceInactiveBackground->value());
            }
            else {
                renderRect(curWorkspaceBox, config.workspaceInactiveBackground->value());
            }
        }

        if (activeTile && !config.drawActiveWorkspace->value()) {
            curWorkspaceRectOffsetX += workspaceBoxW + config.workspaceMargin->value() * owner->m_scale;
            continue;
        }

        // background and bottom layers
        if (!config.hideBackgroundLayers->value()) {
            for (auto& ls : owner->m_layerSurfaceLayers[0]) {
                CBox layerBox = {curWorkspaceBox.pos() + (ls->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT) - owner->m_position) * monitorSizeScaleFactor, ls->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT) * monitorSizeScaleFactor};
                renderLayerStub(ls.lock(), owner, layerBox, tileClip, time);
            }
            for (auto& ls : owner->m_layerSurfaceLayers[1]) {
                CBox layerBox = {curWorkspaceBox.pos() + (ls->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT) - owner->m_position) * monitorSizeScaleFactor, ls->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT) * monitorSizeScaleFactor};
                renderLayerStub(ls.lock(), owner, layerBox, tileClip, time);
            }
        }

        // the mini panel to cover the awkward empty space reserved by the panel
        if (owner->m_activeWorkspace == ws && config.affectStrut->value() && !isCentered) {
            CBox miniPanelBox = {curWorkspaceRectOffsetX, curWorkspaceRectOffsetY, widgetBox.w * monitorSizeScaleFactor, widgetBox.h * monitorSizeScaleFactor};
            if (config.onBottom->value()) miniPanelBox = {curWorkspaceRectOffsetX, curWorkspaceRectOffsetY + workspaceBoxH - widgetBox.h * monitorSizeScaleFactor, widgetBox.w * monitorSizeScaleFactor, widgetBox.h * monitorSizeScaleFactor};

            if (!config.disableBlur->value()) {
                renderRectWithBlur(miniPanelBox, CHyprColor(0, 0, 0, 0));
            }
            else {
                // what
                renderRect(miniPanelBox, CHyprColor(0, 0, 0, 0));
            }

        }

        if (ws != nullptr) {
            // draw tiled windows
            for (auto& w : Desktop::windowState()->windows()) {
                if (!w) continue;
                if (w->m_workspace == ws && !w->isFloating()) {
                    double wX = curWorkspaceRectOffsetX + ((w->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x - owner->m_position.x) * monitorSizeScaleFactor * owner->m_scale);
                    double wY = curWorkspaceRectOffsetY + ((w->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y - owner->m_position.y) * monitorSizeScaleFactor * owner->m_scale);
                    double wW = w->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x * monitorSizeScaleFactor * owner->m_scale;
                    double wH = w->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y * monitorSizeScaleFactor * owner->m_scale;
                    if (!(wW > 0 && wH > 0)) continue;
                    CBox curWindowBox = {wX, wY, wW, wH};
                    //g_pHyprOpenGL->renderRectWithBlur(&curWindowBox, CHyprColor(0, 0, 0, 0));
                    renderWindowStub(w, owner, owner->m_activeWorkspace, curWindowBox, tileClip, time);
                }
            }
            // draw floating windows
            for (auto& w : Desktop::windowState()->windows()) {
                if (!w) continue;
                if (w->m_workspace == ws && w->isFloating() && ws->getLastFocusedWindow() != w) {
                    double wX = curWorkspaceRectOffsetX + ((w->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x - owner->m_position.x) * monitorSizeScaleFactor * owner->m_scale);
                    double wY = curWorkspaceRectOffsetY + ((w->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y - owner->m_position.y) * monitorSizeScaleFactor * owner->m_scale);
                    double wW = w->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x * monitorSizeScaleFactor * owner->m_scale;
                    double wH = w->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y * monitorSizeScaleFactor * owner->m_scale;
                    if (!(wW > 0 && wH > 0)) continue;
                    CBox curWindowBox = {wX, wY, wW, wH};
                    //g_pHyprOpenGL->renderRectWithBlur(&curWindowBox, CHyprColor(0, 0, 0, 0));
                    renderWindowStub(w, owner, owner->m_activeWorkspace, curWindowBox, tileClip, time);
                }
            }
            // draw last focused floating window on top
            if (ws->getLastFocusedWindow())
                if (ws->getLastFocusedWindow()->isFloating()) {
                    const auto w = ws->getLastFocusedWindow();
                    double wX = curWorkspaceRectOffsetX + ((w->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x - owner->m_position.x) * monitorSizeScaleFactor * owner->m_scale);
                    double wY = curWorkspaceRectOffsetY + ((w->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y - owner->m_position.y) * monitorSizeScaleFactor * owner->m_scale);
                    double wW = w->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).x * monitorSizeScaleFactor * owner->m_scale;
                    double wH = w->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT).y * monitorSizeScaleFactor * owner->m_scale;
                    if (!(wW > 0 && wH > 0)) continue;
                    CBox curWindowBox = {wX, wY, wW, wH};
                    //g_pHyprOpenGL->renderRectWithBlur(&curWindowBox, CHyprColor(0, 0, 0, 0));
                    renderWindowStub(w, owner, owner->m_activeWorkspace, curWindowBox, tileClip, time);
                }
        }

        if (owner->m_activeWorkspace != ws || !config.hideRealLayers->value()) {
            // this layer is hidden for real workspace when panel is displayed
            if (!config.hideTopLayers->value())
                for (auto& ls : owner->m_layerSurfaceLayers[2]) {
                    CBox layerBox = {curWorkspaceBox.pos() + (ls->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT) - owner->m_position) * monitorSizeScaleFactor, ls->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT) * monitorSizeScaleFactor};
                    renderLayerStub(ls.lock(), owner, layerBox, tileClip, time);
                }

            if (!config.hideOverlayLayers->value())
                for (auto& ls : owner->m_layerSurfaceLayers[3]) {
                    CBox layerBox = {curWorkspaceBox.pos() + (ls->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT) - owner->m_position) * monitorSizeScaleFactor, ls->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT) * monitorSizeScaleFactor};
                    renderLayerStub(ls.lock(), owner, layerBox, tileClip, time);
                }
        }


        // Resets workspaceBox to scaled absolute coordinates for input detection.
        // While rendering is done in pixel coordinates, input detection is done in
        // scaled coordinates, taking into account monitor scaling.
        // Since the monitor position is already given in scaled coordinates,
        // we only have to scale all relative coordinates, then add them to the
        // monitor position to get a scaled absolute position.
        auto inputBox = tileClip;
        inputBox.scale(1 / owner->m_scale);

        inputBox.x += owner->m_position.x;
        inputBox.y += owner->m_position.y;
        workspaceBoxes.emplace_back(std::make_tuple(tile, inputBox));

        // set the current position to the next workspace box
        curWorkspaceRectOffsetX += workspaceBoxW + config.workspaceMargin->value() * owner->m_scale;
    }

    overviewContext().m_data.clipBox = monitorClip;
}
