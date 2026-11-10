mod app;
mod config;
mod daemon;
mod dbus;
mod ui;

use clap::Parser;
use std::sync::atomic::Ordering;

use daemon::PanelCommand;
use gtk4::Application;
use gtk4::glib;
use gtk4::prelude::*;
use ui::window::set_panel_visible;

/// A floating WiFi manager for Wayland compositors (Hyprland/Sway)
#[derive(Parser, Debug)]
#[command(name = "wifi-manager", version, about)]
struct Args {
    /// Toggle the panel visibility (sends signal to running daemon)
    #[arg(long)]
    toggle: bool,

    /// Reload config and CSS (sends signal to running daemon)
    #[arg(long)]
    reload: bool,
}

const APP_ID: &str = "com.github.wifi_manager.WifiManager";

fn main() {
    // Initialize logging
    env_logger::init();

    let args = Args::parse();

    if args.toggle {
        // Send Toggle() to running daemon and exit
        let rt = glib::MainContext::default();
        rt.block_on(async {
            if daemon::is_instance_running().await {
                match daemon::send_toggle().await {
                    Ok(_) => log::info!("Toggle sent to running instance"),
                    Err(e) => {
                        log::error!("Failed to send toggle: {e}");
                        eprintln!("Error: could not toggle — is wifi-manager running?");
                    }
                }
            } else {
                eprintln!("No running instance found. Start with: wifi-manager");
            }
        });
        return;
    }

    if args.reload {
        // Send Reload() to running daemon and exit
        let rt = glib::MainContext::default();
        rt.block_on(async {
            if daemon::is_instance_running().await {
                match daemon::send_reload().await {
                    Ok(_) => {
                        log::info!("Reload sent to running instance");
                        println!("Config and CSS reloaded");
                    }
                    Err(e) => {
                        log::error!("Failed to send reload: {e}");
                        eprintln!("Error: could not reload — is wifi-manager running?");
                    }
                }
            } else {
                eprintln!("No running instance found. Start with: wifi-manager");
            }
        });
        return;
    }

    // Start the GTK application (daemon mode)
    log::info!("Starting wifi-manager daemon");

    let app = Application::builder().application_id(APP_ID).build();

    // Catch kill signals to cleanly shut down GTK and drop hardware locks
    const SIGINT: i32 = 2;
    const SIGTERM: i32 = 15;

    let app_clone = app.clone();
    glib::unix_signal_add_local(SIGTERM, move || { // SIGTERM
        log::info!("Received SIGTERM, gracefully shutting down");
        app_clone.quit();
        glib::ControlFlow::Break
    });
    
    let app_clone2 = app.clone();
    glib::unix_signal_add_local(SIGINT, move || { // SIGINT
        log::info!("Received SIGINT, gracefully shutting down");
        app_clone2.quit();
        glib::ControlFlow::Break
    });

    app.connect_activate(|app| {
        log::info!("Application activated");

        // Build the UI (starts hidden)
        let widgets = ui::window::build_window(app);

        let window_ref = glib::SendWeakRef::from(widgets.window.downgrade());
        let panel_state = daemon::PanelState::new(move |command| {
            let window_ref = window_ref.clone();
            // Resolve toggles against the actual window on the GTK thread.
            glib::MainContext::default().spawn(async move {
                if let Some(window) = window_ref.upgrade() {
                    match command {
                        PanelCommand::Toggle => set_panel_visible(&window, !window.is_visible()),
                        PanelCommand::Show => set_panel_visible(&window, true),
                        PanelCommand::Hide => set_panel_visible(&window, false),
                        PanelCommand::Reload => {
                            ui::window::reload_css();
                            if let Some(action) = window.lookup_action("refresh-networks") {
                                action.activate(None);
                            }
                        }
                    }
                }
            })
        });
        let visible = panel_state.visible.clone();
        widgets.window.connect_visible_notify(move |window| {
            visible.store(window.is_visible(), Ordering::Relaxed);
        });

        // Register the D-Bus daemon service
        let panel_state_clone = panel_state.clone();
        glib::spawn_future_local(async move {
            match daemon::register_service(panel_state_clone).await {
                Ok(_conn) => {
                    log::info!("Daemon D-Bus service ready");
                    // _conn is kept alive by the async task
                    // It will be dropped when the app exits
                    std::future::pending::<()>().await;
                }
                Err(e) => {
                    log::error!("Failed to register D-Bus service: {e}");
                }
            }
        });

        // Connect to NetworkManager and set up the app controller
        glib::spawn_future_local(async move {
            match dbus::network_manager::WifiManager::new().await {
                Ok(wifi) => {
                    log::info!("NetworkManager D-Bus connection established");
                    let config = config::Config::load();
                    app::setup(&widgets, wifi, panel_state.visible);

                    // Only show panel on start if configured
                    if config.show_on_start {
                        set_panel_visible(&widgets.window, true);
                    }
                }
                Err(e) => {
                    log::error!("Failed to connect to NetworkManager: {e}");
                    widgets
                        .status_label
                        .set_text("Error: NetworkManager unavailable");
                    // Still show the panel so user sees the error
                    set_panel_visible(&widgets.window, true);
                }
            }
        });
    });

    app.run();
    
    // Allow pending D-Bus responses and GTK callbacks to complete before process exit.
    // Iterating the main context processes the teardown events gracefully.
    let ctx = glib::MainContext::default();
    let start = std::time::Instant::now();
    let timeout = std::time::Duration::from_millis(150);
    
    while ctx.pending() && start.elapsed() < timeout {
        ctx.iteration(false);
    }
}
