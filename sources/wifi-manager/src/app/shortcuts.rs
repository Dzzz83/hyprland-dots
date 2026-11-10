//! Shortcuts — keyboard and D-Bus triggered actions (Escape, reload).

use std::cell::RefCell;
use std::rc::Rc;

use gtk4::{gio, glib, prelude::*};

use crate::ui::window::{PanelWidgets, set_panel_visible};

use super::{AppState, refresh_list};

/// Dismiss the panel through Escape or a click outside its visible bounds.
pub(super) fn setup_dismissal(widgets: &PanelWidgets) {
    use gtk4::{ApplicationWindow, EventControllerKey, gdk};
    
    let key_controller = EventControllerKey::new();
    key_controller.set_propagation_phase(gtk4::PropagationPhase::Capture);
    let window = widgets.window.downgrade();
    key_controller.connect_key_pressed(move |_, key, _, _| {
        if key == gdk::Key::Escape {
            if let Some(window) = window.upgrade() {
                set_panel_visible(&window, false);
            }
            return glib::Propagation::Stop;
        }
        glib::Propagation::Proceed
    });
    widgets.window.add_controller(key_controller);

    let outside_click = gtk4::GestureClick::new();
    outside_click.set_button(0); // Any mouse button outside dismisses the panel.
    outside_click.set_propagation_phase(gtk4::PropagationPhase::Capture);
    let panel = widgets.panel.clone();
    outside_click.connect_pressed(move |gesture, _, x, y| {
        let Some(window) = gesture.widget().and_downcast::<ApplicationWindow>() else {
            return;
        };
        let Some(bounds) = panel.compute_bounds(&window) else { return; };
        if !bounds.contains_point(&gtk4::graphene::Point::new(x as f32, y as f32)) {
            gesture.set_state(gtk4::EventSequenceState::Claimed);
            set_panel_visible(&window, false);
        }
    });
    widgets.window.add_controller(outside_click);
}

pub(super) fn setup_reload_on_request(widgets: &PanelWidgets, state: Rc<RefCell<AppState>>) {
    let list_box = widgets.network_list_box.clone();
    let status = widgets.status_label.clone();

    let refresh = gio::SimpleAction::new("refresh-networks", None);
    refresh.connect_activate(move |_, _| {
        let state = Rc::clone(&state);
        let list_box = list_box.clone();
        let status = status.clone();
        glib::spawn_future_local(async move {
            refresh_list(&state, &list_box, &status).await;
        });
    });
    widgets.window.add_action(&refresh);
}
