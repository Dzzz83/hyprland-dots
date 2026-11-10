//! D-Bus daemon service — exposes Toggle/Show/Hide methods on the session bus.
//!
//! This allows `wifi-manager --toggle` to control a running instance.
//! The interface is registered at `com.github.wifi_manager.Daemon`
//! on the session bus at path `/com/github/wifi_manager/Daemon`.

use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

use gtk4::glib;
use zbus::{fdo, interface};

/// The D-Bus interface name and path.
pub const DBUS_NAME: &str = "com.github.wifi_manager.Daemon";
pub const DBUS_PATH: &str = "/com/github/wifi_manager/Daemon";

pub enum PanelCommand {
    Toggle,
    Show,
    Hide,
    Reload,
}

type Dispatch = Arc<dyn Fn(PanelCommand) -> glib::JoinHandle<()> + Send + Sync>;

/// State shared between the D-Bus service and the GTK window.
/// Must be Send + Sync because zbus runs on its own async runtime.
#[derive(Clone)]
pub struct PanelState {
    /// Whether the panel is currently visible.
    pub visible: Arc<AtomicBool>,
    dispatch: Dispatch,
}

impl PanelState {
    pub fn new(dispatch: impl Fn(PanelCommand) -> glib::JoinHandle<()> + Send + Sync + 'static) -> Self {
        Self {
            visible: Arc::new(AtomicBool::new(false)),
            dispatch: Arc::new(dispatch),
        }
    }

    async fn dispatch(&self, command: PanelCommand) -> fdo::Result<()> {
        (self.dispatch)(command)
            .await
            .map_err(|error| fdo::Error::Failed(error.to_string()))
    }
}

/// D-Bus interface implementation — exposed on the session bus.
struct DaemonInterface {
    state: PanelState,
}

#[interface(name = "com.github.wifi_manager.Daemon")]
impl DaemonInterface {
    /// Toggle panel visibility.
    async fn toggle(&self) -> fdo::Result<()> {
        log::info!("D-Bus Toggle() called");
        self.state.dispatch(PanelCommand::Toggle).await
    }

    /// Show the panel.
    async fn show(&self) -> fdo::Result<()> {
        log::info!("D-Bus Show() called");
        self.state.dispatch(PanelCommand::Show).await
    }

    /// Hide the panel.
    async fn hide(&self) -> fdo::Result<()> {
        log::info!("D-Bus Hide() called");
        self.state.dispatch(PanelCommand::Hide).await
    }

    /// Reload config and CSS.
    async fn reload(&self) -> fdo::Result<()> {
        log::info!("D-Bus Reload() called");
        self.state.dispatch(PanelCommand::Reload).await
    }

    /// Check if the panel is visible.
    #[zbus(property)]
    fn visible(&self) -> bool {
        self.state.visible.load(Ordering::Relaxed)
    }
}

/// Register the D-Bus service on the session bus.
/// Returns the connection (keep alive for the daemon's lifetime).
pub async fn register_service(state: PanelState) -> zbus::Result<zbus::Connection> {
    let iface = DaemonInterface { state };

    let conn = zbus::connection::Builder::session()?
        .name(DBUS_NAME)?
        .serve_at(DBUS_PATH, iface)?
        .build()
        .await?;

    log::info!("D-Bus daemon service registered: {DBUS_NAME}");
    Ok(conn)
}

/// Check if another instance is already running (name is taken on session bus).
pub async fn is_instance_running() -> bool {
    let conn = match zbus::Connection::session().await {
        Ok(c) => c,
        Err(_) => return false,
    };

    let result = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some("org.freedesktop.DBus.Peer"),
            "Ping",
            &(),
        )
        .await;

    result.is_ok()
}

/// Send a Toggle() call to the running daemon instance.
pub async fn send_toggle() -> zbus::Result<()> {
    let conn = zbus::Connection::session().await?;

    conn.call_method(Some(DBUS_NAME), DBUS_PATH, Some(DBUS_NAME), "Toggle", &())
        .await?;

    log::info!("Toggle sent to running instance");
    Ok(())
}

/// Send Reload() to the running daemon.
pub async fn send_reload() -> zbus::Result<()> {
    let conn = zbus::Connection::session().await?;

    conn.call_method(Some(DBUS_NAME), DBUS_PATH, Some(DBUS_NAME), "Reload", &())
        .await?;

    log::info!("Reload sent to running instance");
    Ok(())
}
