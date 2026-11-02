#include "Lua.hpp"
#include "Globals.hpp"
#include "Overview.hpp"
#include <hyprland/src/desktop/state/FocusState.hpp>
#include <hyprland/src/config/ConfigManager.hpp>

extern "C" {
    #include <lua.h>
    #include <lauxlib.h>
}

template <SDispatchResult (*DispatcherFunc)(std::string)>
int luaDispatcherWrapper(lua_State* L) {
    const std::string arg = luaL_optstring(L, 1, "");
    SDispatchResult result = DispatcherFunc(arg);
    lua_pushboolean(L, result.success);
    if (!result.success) {
        lua_pushstring(L, result.error.c_str());
        return 2;
    }
    return 1;
}

extern std::vector<std::shared_ptr<CHyprspaceWidget>> g_overviewWidgets;

static std::shared_ptr<CHyprspaceWidget> selectionWidget() {
    for (const auto& widget : g_overviewWidgets) {
        if (widget->hasKeyboardPreview())
            return widget;
    }
    return nullptr;
}

static int beginSelection(lua_State* L) {
    const auto monitor = Desktop::focusState()->monitor();
    for (const auto& widget : g_overviewWidgets) {
        if (widget->getOwner() == monitor) {
            lua_pushboolean(L, widget->beginSelection());
            return 1;
        }
    }
    lua_pushboolean(L, false);
    return 1;
}

static int moveSelection(lua_State* L) {
    const auto direction = luaL_checkstring(L, 1);
    const auto widget = selectionWidget();
    lua_pushboolean(L, widget && widget->moveSelection(direction));
    return 1;
}

static int finishSelection(lua_State* L) {
    luaL_checktype(L, 1, LUA_TBOOLEAN);
    const auto widget = selectionWidget();
    const auto target = widget ? widget->finishSelection(lua_toboolean(L, 1)) : std::nullopt;
    if (target)
        lua_pushinteger(L, *target);
    else
        lua_pushnil(L);
    return 1;
}

void registerLuaBindings(HANDLE handle) {
    if (Config::mgr() && Config::mgr()->type() == Config::CONFIG_LUA) {
        HyprlandAPI::addLuaFunction(handle, "overview", "toggle", luaDispatcherWrapper<Dispatchers::dispatchToggleOverview>);
        HyprlandAPI::addLuaFunction(handle, "overview", "open", luaDispatcherWrapper<Dispatchers::dispatchOpenOverview>);
        HyprlandAPI::addLuaFunction(handle, "overview", "close", luaDispatcherWrapper<Dispatchers::dispatchCloseOverview>);
        HyprlandAPI::addLuaFunction(handle, "overview", "begin_selection", beginSelection);
        HyprlandAPI::addLuaFunction(handle, "overview", "move_selection", moveSelection);
        HyprlandAPI::addLuaFunction(handle, "overview", "finish_selection", finishSelection);
    }
}
