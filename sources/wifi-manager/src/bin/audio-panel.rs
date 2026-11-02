//! Compact audio controls using the same GTK/layer-shell stack as wifi-manager.
#[path = "audio_panel/backend.rs"]
mod backend;
#[path = "audio_panel/popup.rs"]
mod popup;

use gtk4::{glib, prelude::*};
use std::{cell::RefCell, rc::Rc};

fn main() -> glib::ExitCode {
    env_logger::init();
    let app = gtk4::Application::builder()
        .application_id("com.local.AudioPanel")
        .build();
    app.add_main_option(
        "toggle",
        glib::Char(0),
        glib::OptionFlags::NONE,
        glib::OptionArg::None,
        "Toggle the sound popup",
        None,
    );
    let popup = Rc::new(RefCell::new(None::<popup::Popup>));
    app.connect_activate(move |app| {
        let mut popup = popup.borrow_mut();
        if popup.is_none() {
            *popup = Some(popup::Popup::new(app));
        }
        popup.as_ref().unwrap().toggle();
    });
    for signal in [2, 15] {
        let app = app.downgrade();
        glib::unix_signal_add_local(signal, move || {
            if let Some(app) = app.upgrade() {
                app.quit();
            }
            glib::ControlFlow::Break
        });
    }
    // Keep the popup available when hidden; GApplication forwards subsequent
    // launches to this instance instead of opening duplicate panels.
    app.run()
}
