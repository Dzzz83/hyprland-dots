//! Layer-shell popup, styled and dismissed like the Wi-Fi panel.
use super::backend::{AudioBackend, AudioState, Direction};
use gtk4::{
    Align, Application, ApplicationWindow, Box as GtkBox, Button, DropDown, Label, Orientation,
    Scale, StringList, gdk, gio, glib, prelude::*,
};
use gtk4_layer_shell::{Edge, KeyboardMode, Layer, LayerShell};
use std::{
    cell::{Cell, RefCell},
    rc::Rc,
};

#[derive(Clone)]
struct DeviceControls {
    container: GtkBox,
    devices: DropDown,
    device_names: Rc<RefCell<Vec<String>>>,
    volume: Scale,
    percentage: Label,
    mute: Button,
    muted_icon: gio::Icon,
    audible_icon: gio::Icon,
    icon: gtk4::Image,
    updating: Rc<Cell<bool>>,
    title: &'static str,
}

impl DeviceControls {
    fn new(title: &'static str, audible_icon: gio::Icon, muted_icon: gio::Icon) -> Self {
        let container = GtkBox::new(Orientation::Vertical, 12);
        container.add_css_class("audio-section");
        let heading = GtkBox::new(Orientation::Horizontal, 8);
        let label = Label::new(Some(title));
        label.add_css_class("section-title");
        label.set_hexpand(true);
        label.set_xalign(0.0);
        let percentage = Label::new(Some("—"));
        percentage.add_css_class("percentage");
        heading.append(&label);
        heading.append(&percentage);
        container.append(&heading);

        let devices = DropDown::from_strings(&[]);
        devices.set_hexpand(true);
        devices.set_tooltip_text(Some(&format!("Select {title} device")));
        devices.update_property(&[gtk4::accessible::Property::Label(&format!(
            "{title} device"
        ))]);
        // Long device names must not force the compact popup off screen.
        for is_list_factory in [false, true] {
            let factory = gtk4::SignalListItemFactory::new();
            factory.connect_setup(|_, item| {
                let item = item.downcast_ref::<gtk4::ListItem>().unwrap();
                let label = Label::new(None);
                label.set_xalign(0.0);
                label.set_ellipsize(gtk4::pango::EllipsizeMode::End);
                label.set_max_width_chars(25);
                item.set_child(Some(&label));
            });
            factory.connect_bind(|_, item| {
                let item = item.downcast_ref::<gtk4::ListItem>().unwrap();
                let object = item
                    .item()
                    .unwrap()
                    .downcast::<gtk4::StringObject>()
                    .unwrap();
                let label = item.child().unwrap().downcast::<Label>().unwrap();
                label.set_label(&object.string());
                label.set_tooltip_text(Some(&object.string()));
            });
            if is_list_factory {
                devices.set_list_factory(Some(&factory));
            } else {
                devices.set_factory(Some(&factory));
            }
        }
        container.append(&devices);

        let row = GtkBox::new(Orientation::Horizontal, 10);
        let mute = Button::new();
        let icon = gtk4::Image::from_gicon(&audible_icon);
        icon.set_pixel_size(18);
        mute.set_child(Some(&icon));
        mute.add_css_class("mute-button");
        mute.set_tooltip_text(Some(&format!("Mute {title}")));
        let volume = Scale::with_range(Orientation::Horizontal, 0.0, 100.0, 1.0);
        volume.set_draw_value(false);
        volume.set_hexpand(true);
        volume.set_round_digits(0);
        volume.update_property(&[gtk4::accessible::Property::Label(&format!(
            "{title} volume"
        ))]);
        row.append(&mute);
        row.append(&volume);
        container.append(&row);
        container.set_sensitive(false);
        Self {
            container,
            devices,
            device_names: Rc::new(RefCell::new(Vec::new())),
            volume,
            percentage,
            mute,
            muted_icon,
            audible_icon,
            icon,
            updating: Rc::new(Cell::new(false)),
            title,
        }
    }

    fn render(&self, state: &AudioState, direction: Direction) {
        self.updating.set(true);
        let devices = state.devices(direction);
        let names: Vec<_> = devices.iter().map(|device| device.name.clone()).collect();
        // Rebuild only for device/description changes, never on slider events.
        let descriptions: Vec<_> = devices
            .iter()
            .map(|device| device.description.as_str())
            .collect();
        let model = self.devices.model().and_downcast::<StringList>();
        let model_matches = model.as_ref().is_some_and(|model| {
            model.n_items() == descriptions.len() as u32
                && descriptions
                    .iter()
                    .enumerate()
                    .all(|(index, text)| model.string(index as u32).as_deref() == Some(*text))
        });
        if !model_matches || *self.device_names.borrow() != names {
            *self.device_names.borrow_mut() = names;
            self.devices
                .set_model(Some(&StringList::new(&descriptions)));
        }
        let selected = state.selected(direction);
        let selected_index = selected.and_then(|selected| {
            devices
                .iter()
                .position(|device| device.name == selected.name)
        });
        self.devices
            .set_selected(selected_index.map_or(gtk4::INVALID_LIST_POSITION, |index| index as u32));
        self.container
            .set_sensitive(state.connected && !devices.is_empty());
        self.volume.set_sensitive(selected.is_some());
        self.mute.set_sensitive(selected.is_some());
        if let Some(device) = selected {
            self.volume.set_value(device.percent().clamp(0.0, 100.0));
            self.percentage.set_label(&format!(
                "{:.0}%{}",
                device.percent(),
                if device.muted { " · Muted" } else { "" }
            ));
            self.icon.set_from_gicon(if device.muted {
                &self.muted_icon
            } else {
                &self.audible_icon
            });
            let action = if device.muted { "Unmute" } else { "Mute" };
            let label = format!("{action} {}", self.title.to_lowercase());
            self.mute.set_tooltip_text(Some(&label));
            self.mute
                .update_property(&[gtk4::accessible::Property::Label(&label)]);
            if device.muted {
                self.mute.add_css_class("muted");
            } else {
                self.mute.remove_css_class("muted");
            }
        } else {
            self.percentage.set_label(if state.connected {
                "No device"
            } else {
                "Unavailable"
            });
        }
        self.updating.set(false);
    }

    fn connect(&self, backend: &Rc<AudioBackend>, direction: Direction) {
        let weak = Rc::downgrade(backend);
        let updating = self.updating.clone();
        self.volume.connect_value_changed(move |scale| {
            if !updating.get()
                && let Some(backend) = weak.upgrade()
            {
                backend.set_volume(direction, scale.value());
            }
        });
        let weak = Rc::downgrade(backend);
        self.mute.connect_clicked(move |_| {
            if let Some(backend) = weak.upgrade() {
                backend.toggle_mute(direction);
            }
        });
        let names = self.device_names.clone();
        let updating = self.updating.clone();
        let weak = Rc::downgrade(backend);
        self.devices.connect_selected_notify(move |dropdown| {
            if !updating.get()
                && let Some(name) = names.borrow().get(dropdown.selected() as usize)
                && let Some(backend) = weak.upgrade()
            {
                backend.select_device(direction, name);
            }
        });
    }
}

pub struct Popup {
    window: ApplicationWindow,
    backend: Option<Rc<AudioBackend>>,
}

impl Popup {
    pub fn new(app: &Application) -> Self {
        let provider = gtk4::CssProvider::new();
        provider.load_from_string(include_str!("../../../resources/audio-panel.css"));
        gtk4::style_context_add_provider_for_display(
            &gdk::Display::default().unwrap(),
            &provider,
            gtk4::STYLE_PROVIDER_PRIORITY_APPLICATION,
        );

        let window = ApplicationWindow::builder()
            .application(app)
            .title("Sound")
            .build();
        window.init_layer_shell();
        window.set_namespace(Some("audio-panel"));
        window.set_layer(Layer::Overlay);
        window.set_keyboard_mode(KeyboardMode::None);
        window.set_exclusive_zone(-1);
        for edge in [Edge::Top, Edge::Bottom, Edge::Left, Edge::Right] {
            window.set_anchor(edge, true);
        }

        let panel = GtkBox::new(Orientation::Vertical, 0);
        panel.add_css_class("audio-panel");
        panel.set_size_request(340, -1);
        panel.set_halign(Align::End);
        panel.set_valign(Align::Start);
        panel.set_margin_top(34);
        // At scale 1.2, the speaker glyph is centered at logical x=1343.
        // A 340px panel on the 1600px bar therefore needs an 87px right margin.
        panel.set_margin_end(87);

        let header = GtkBox::new(Orientation::Horizontal, 12);
        header.add_css_class("audio-header");
        let icon = gtk4::Image::from_icon_name("audio-volume-high-symbolic");
        icon.add_css_class("header-icon");
        icon.set_pixel_size(22);
        header.append(&icon);
        let heading = GtkBox::new(Orientation::Vertical, 3);
        heading.set_hexpand(true);
        let title = Label::new(Some("Sound"));
        title.add_css_class("header-title");
        title.set_xalign(0.0);
        let subtitle = Label::new(Some("Speakers & microphone"));
        subtitle.add_css_class("subtitle");
        subtitle.set_xalign(0.0);
        heading.append(&title);
        heading.append(&subtitle);
        header.append(&heading);
        panel.append(&header);
        panel.append(&gtk4::Separator::new(Orientation::Horizontal));

        let output = DeviceControls::new(
            "Output",
            gio::ThemedIcon::new("audio-volume-high-symbolic").upcast(),
            gio::ThemedIcon::new("audio-volume-muted-symbolic").upcast(),
        );
        let input = DeviceControls::new(
            "Microphone",
            gio::BytesIcon::new(&glib::Bytes::from_static(include_bytes!(
                "../../../resources/audio-icons/microphone.svg"
            )))
            .upcast(),
            gio::BytesIcon::new(&glib::Bytes::from_static(include_bytes!(
                "../../../resources/audio-icons/microphone-muted.svg"
            )))
            .upcast(),
        );
        panel.append(&output.container);
        panel.append(&gtk4::Separator::new(Orientation::Horizontal));
        panel.append(&input.container);
        let status = Label::new(Some("Connecting to audio…"));
        status.add_css_class("audio-status");
        status.set_wrap(true);
        status.set_max_width_chars(36);
        panel.append(&status);
        let advanced = Button::with_label("Advanced settings  ↗");
        advanced.add_css_class("advanced-button");
        let weak = window.downgrade();
        let status_clone = status.clone();
        advanced.connect_clicked(move |_| {
            match std::process::Command::new("pavucontrol").spawn() {
                Ok(mut child) => {
                    std::thread::spawn(move || {
                        let _ = child.wait();
                    });
                    if let Some(window) = weak.upgrade() {
                        hide(&window);
                    }
                }
                Err(error) => {
                    status_clone.set_label(&format!("Cannot open advanced settings: {error}"));
                    status_clone.set_visible(true);
                }
            }
        });
        panel.append(&advanced);

        let backdrop = gtk4::Overlay::new();
        backdrop.set_child(Some(&gtk4::DrawingArea::new()));
        backdrop.add_overlay(&panel);
        window.set_child(Some(&backdrop));
        setup_dismissal(&window, &panel);

        let output_view = output.clone();
        let input_view = input.clone();
        let status_view = status.clone();
        let backend = AudioBackend::new(move |state| {
            output_view.render(state, Direction::Output);
            input_view.render(state, Direction::Input);
            let message = state.error.as_deref().unwrap_or(if state.connected {
                ""
            } else {
                "Connecting to audio…"
            });
            status_view.set_label(message);
            status_view.set_visible(!message.is_empty());
        });
        let backend = match backend {
            Ok(backend) => {
                output.connect(&backend, Direction::Output);
                input.connect(&backend, Direction::Input);
                Some(backend)
            }
            Err(error) => {
                status.set_label(&error);
                None
            }
        };
        Self { window, backend }
    }

    pub fn toggle(&self) {
        if self.window.is_visible() {
            hide(&self.window);
        } else {
            hide_wifi_panel();
            if let Some(backend) = &self.backend {
                backend.refresh();
            }
            self.window.set_keyboard_mode(KeyboardMode::Exclusive);
            self.window.present();
        }
    }
}

fn hide(window: &ApplicationWindow) {
    window.set_visible(false);
    window.set_keyboard_mode(KeyboardMode::None);
}

fn setup_dismissal(window: &ApplicationWindow, panel: &GtkBox) {
    let key = gtk4::EventControllerKey::new();
    key.set_propagation_phase(gtk4::PropagationPhase::Capture);
    let weak = window.downgrade();
    key.connect_key_pressed(move |_, pressed, _, _| {
        if pressed == gdk::Key::Escape {
            if let Some(window) = weak.upgrade() {
                hide(&window);
            }
            glib::Propagation::Stop
        } else {
            glib::Propagation::Proceed
        }
    });
    window.add_controller(key);
    let outside = gtk4::GestureClick::new();
    outside.set_button(0);
    outside.set_propagation_phase(gtk4::PropagationPhase::Capture);
    let panel = panel.clone();
    outside.connect_pressed(move |gesture, _, x, y| {
        let Some(window) = gesture.widget().and_downcast::<ApplicationWindow>() else {
            return;
        };
        let Some(bounds) = panel.compute_bounds(&window) else {
            return;
        };
        if !bounds.contains_point(&gtk4::graphene::Point::new(x as f32, y as f32)) {
            gesture.set_state(gtk4::EventSequenceState::Claimed);
            hide(&window);
        }
    });
    window.add_controller(outside);
    window.connect_close_request(|window| {
        hide(window);
        glib::Propagation::Stop
    });
}

fn hide_wifi_panel() {
    glib::spawn_future_local(async {
        if let Ok(connection) = zbus::Connection::session().await {
            let _ = connection
                .call_method(
                    Some("com.github.wifi_manager.Daemon"),
                    "/com/github/wifi_manager/Daemon",
                    Some("com.github.wifi_manager.Daemon"),
                    "Hide",
                    &(),
                )
                .await;
        }
    });
}
