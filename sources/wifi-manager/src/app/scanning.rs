//! Scanning — initial state, automatic scans, and manual scan button.

use std::cell::RefCell;
use std::rc::Rc;

use gtk4::glib;
use gtk4::prelude::*;

use crate::ui::window::PanelWidgets;

use super::{AppState, get_wifi, refresh_list};

const WIFI_SCAN_RESULT_WAIT_MS: u64 = 2500;
const WIFI_AUTO_SCAN_INTERVAL_MS: u64 = 15000;
/// Interval for the background reconnect scan when panel is hidden and disconnected.
const WIFI_BG_RECONNECT_INTERVAL_MS: u64 = 60_000;

struct ScanGuard(Rc<RefCell<AppState>>);

impl ScanGuard {
    fn start(state: &Rc<RefCell<AppState>>) -> Option<Self> {
        let mut app = state.borrow_mut();
        if app.wifi_scan_in_progress {
            return None;
        }
        app.wifi_scan_in_progress = true;
        Some(Self(Rc::clone(state)))
    }
}

impl Drop for ScanGuard {
    fn drop(&mut self) {
        self.0.borrow_mut().wifi_scan_in_progress = false;
    }
}

/// Initial state: check WiFi status and trigger first scan.
pub(super) fn setup_initial_state(widgets: &PanelWidgets, state: Rc<RefCell<AppState>>) {
    let switch = widgets.wifi_switch.clone();
    let status = widgets.status_label.clone();
    let list_box = widgets.network_list_box.clone();
    let spinner = widgets.spinner.clone();
    let scrolled = widgets.network_scroll.clone();

    let Some(scan) = ScanGuard::start(&state) else {
        return;
    };
    glib::spawn_future_local(async move {
        let _scan = scan;
        let wifi = get_wifi(&state);

        // Set WiFi switch to current state
        match wifi.is_wifi_enabled().await {
            Ok(enabled) => switch.set_active(enabled),
            Err(e) => log::error!("Failed to get WiFi state: {e}"),
        }

        // Trigger initial scan
        if let Err(e) = wifi.request_scan().await {
            log::warn!("Initial scan failed: {e}");
        }

        // Brief delay to let NM populate APs after scan
        glib::timeout_future(std::time::Duration::from_millis(WIFI_SCAN_RESULT_WAIT_MS)).await;
        refresh_list(&state, &list_box, &status).await;

        // Hide spinner, show network list
        spinner.set_spinning(false);
        spinner.set_visible(false);
        scrolled.set_visible(true);
    });
}

/// Run a manual Wi-Fi scan (spinner visible, list hidden).
pub(super) fn run_manual_scan(
    state: Rc<RefCell<AppState>>,
    list_box: gtk4::ListBox,
    status: gtk4::Label,
    scan_btn: gtk4::Button,
    spinner: gtk4::Spinner,
    scrolled: gtk4::ScrolledWindow,
) {
    // Set scan button as default focus to avoid accidental WiFi toggle
    scan_btn.grab_focus();
    scan_btn.set_sensitive(false);

    glib::spawn_future_local(async move {
        run_wifi_scan(
            state,
            list_box,
            status,
            Some(ManualWifiScanUi {
                scan_btn,
                spinner,
                scrolled,
            }),
        )
        .await;
    });
}

pub(super) fn start_wifi_auto_scan(
    state: Rc<RefCell<AppState>>,
    wifi_tab: gtk4::ToggleButton,
    list_box: gtk4::ListBox,
    status: gtk4::Label,
) {
    if state.borrow().wifi_auto_scan_source.is_some() {
        return;
    }

    // Immediate background scan when tab activates
    glib::spawn_future_local({
        let state = Rc::clone(&state);
        let list_box = list_box.clone();
        let status = status.clone();
        async move {
            run_wifi_scan(state, list_box, status, None).await;
        }
    });

    let scan_id = glib::timeout_add_local(
        std::time::Duration::from_millis(WIFI_AUTO_SCAN_INTERVAL_MS),
        {
            let state = Rc::clone(&state);
            let list_box = list_box.clone();
            let status = status.clone();
            let wifi_tab = wifi_tab.clone();
            move || {
                if !wifi_tab.is_active() {
                    state.borrow_mut().wifi_auto_scan_source = None;
                    return glib::ControlFlow::Break;
                }
                glib::spawn_future_local({
                    let state = Rc::clone(&state);
                    let list_box = list_box.clone();
                    let status = status.clone();
                    async move {
                        run_wifi_scan(state, list_box, status, None).await;
                    }
                });
                glib::ControlFlow::Continue
            }
        },
    );

    state.borrow_mut().wifi_auto_scan_source = Some(scan_id);
    log::info!("Fast UI Wi-Fi scan loop started (interval: 15 s)");
}

pub(super) fn stop_wifi_auto_scan(state: &Rc<RefCell<AppState>>) {
    let mut st = state.borrow_mut();
    if let Some(id) = st.wifi_auto_scan_source.take() {
        id.remove();
        log::info!("Fast UI Wi-Fi scan loop stopped");
    }
}

pub(super) fn reconnect_when_hidden(
    state: Rc<RefCell<AppState>>,
    window: &gtk4::ApplicationWindow,
) {
    let window = window.downgrade();
    glib::spawn_future_local(async move {
        let Some(window) = window.upgrade().filter(|window| !window.is_visible()) else {
            return;
        };
        let wifi = get_wifi(&state);
        let is_connected = wifi.has_active_connection().await.unwrap_or(false);
        if !window.is_visible() && !is_connected {
            start_wifi_bg_reconnect(state);
        }
    });
}

/// Start a slow background scan loop (every 60 s) to help NetworkManager
/// find and autoconnect to saved networks while the panel is hidden.
///
/// Fires an immediate scan first so the first reconnect attempt is instant,
/// not delayed by the full interval. No UI updates are performed — NM's own
/// autoconnect logic handles the actual connection once it sees the network.
pub(super) fn start_wifi_bg_reconnect(state: Rc<RefCell<AppState>>) {
    // Guard: only one background loop at a time.
    if state.borrow().wifi_bg_reconnect_source.is_some() {
        return;
    }

    let scan_id = glib::timeout_add_local(
        std::time::Duration::from_millis(WIFI_BG_RECONNECT_INTERVAL_MS),
        {
            let state = Rc::clone(&state);
            move || {
                glib::spawn_future_local(run_reconnect_scan(Rc::clone(&state)));
                glib::ControlFlow::Continue
            }
        },
    );
    state.borrow_mut().wifi_bg_reconnect_source = Some(scan_id);
    glib::spawn_future_local(run_reconnect_scan(state));
    log::info!("BG reconnect loop started (interval: 60 s)");
}

async fn run_reconnect_scan(state: Rc<RefCell<AppState>>) {
    // A visibility or connection change may have stopped the loop since this was queued.
    if state.borrow().wifi_bg_reconnect_source.is_none() {
        return;
    }
    let Some(_scan) = ScanGuard::start(&state) else {
        return;
    };
    if let Err(error) = get_wifi(&state).request_scan().await {
        log::debug!("BG reconnect scan failed: {error}");
    }
}

/// Stop the background reconnect scan loop.
pub(super) fn stop_wifi_bg_reconnect(state: &Rc<RefCell<AppState>>) {
    let mut st = state.borrow_mut();
    if let Some(id) = st.wifi_bg_reconnect_source.take() {
        id.remove();
        log::info!("BG reconnect loop stopped");
    }
}

struct ManualWifiScanUi {
    scan_btn: gtk4::Button,
    spinner: gtk4::Spinner,
    scrolled: gtk4::ScrolledWindow,
}

async fn run_wifi_scan(
    state: Rc<RefCell<AppState>>,
    list_box: gtk4::ListBox,
    status: gtk4::Label,
    manual_ui: Option<ManualWifiScanUi>,
) {
    if manual_ui.is_none() && state.borrow().wifi_auto_scan_source.is_none() {
        return;
    }
    let Some(_scan) = ScanGuard::start(&state) else {
        if let Some(ui) = manual_ui {
            ui.scan_btn.set_sensitive(true);
        }
        return;
    };

    let wifi = get_wifi(&state);
    match wifi.is_wifi_enabled().await {
        Ok(false) => {
            if let Some(ui) = manual_ui {
                ui.spinner.set_spinning(false);
                ui.spinner.set_visible(false);
                ui.scrolled.set_visible(true);
                ui.scan_btn.set_sensitive(true);
            }
            status.set_text("Wi-Fi is disabled");
            return;
        }
        Err(e) => {
            log::error!("Failed to get WiFi state: {e}");
        }
        _ => {}
    }

    if let Some(ref ui) = manual_ui {
        ui.spinner.set_visible(true);
        ui.spinner.set_spinning(true);
        ui.scrolled.set_visible(false);
    }

    if let Err(e) = wifi.request_scan().await {
        log::error!("Scan failed: {e}");
        if let Some(ui) = manual_ui {
            status.set_text("Scan failed");
            ui.spinner.set_spinning(false);
            ui.spinner.set_visible(false);
            ui.scrolled.set_visible(true);
            ui.scan_btn.set_sensitive(true);
        } else {
            // NetworkManager can rate-limit scans. Show the networks it already knows about.
            refresh_list(&state, &list_box, &status).await;
        }
        return;
    }

    glib::timeout_future(std::time::Duration::from_millis(WIFI_SCAN_RESULT_WAIT_MS)).await;
    refresh_list(&state, &list_box, &status).await;

    if let Some(ui) = manual_ui {
        ui.spinner.set_spinning(false);
        ui.spinner.set_visible(false);
        ui.scrolled.set_visible(true);
        ui.scan_btn.set_sensitive(true);
    }
}
