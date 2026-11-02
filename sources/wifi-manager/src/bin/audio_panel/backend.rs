//! Event-driven PulseAudio / PipeWire-Pulse device and volume controls.
use gtk4::glib;
use libpulse_binding::{
    callbacks::ListResult,
    context::{
        Context, FlagSet, State,
        subscribe::{Facility, InterestMaskSet},
    },
    volume::{ChannelVolumes, Volume},
};
use libpulse_glib_binding::Mainloop;
use std::{
    cell::{Cell, RefCell},
    rc::Rc,
    time::Duration,
};

#[derive(Clone, Copy)]
pub enum Direction {
    Output,
    Input,
}

#[derive(Clone)]
pub struct Device {
    pub index: u32,
    pub name: String,
    pub description: String,
    pub volume: ChannelVolumes,
    pub muted: bool,
}

impl Device {
    pub fn percent(&self) -> f64 {
        f64::from(self.volume.max().0) * 100.0 / f64::from(Volume::NORMAL.0)
    }
}

#[derive(Clone, Default)]
pub struct AudioState {
    pub connected: bool,
    pub outputs: Vec<Device>,
    pub inputs: Vec<Device>,
    pub default_output: Option<String>,
    pub default_input: Option<String>,
    pub error: Option<String>,
}

impl AudioState {
    pub fn devices(&self, direction: Direction) -> &[Device] {
        match direction {
            Direction::Output => &self.outputs,
            Direction::Input => &self.inputs,
        }
    }
    pub fn selected(&self, direction: Direction) -> Option<&Device> {
        let name = match direction {
            Direction::Output => &self.default_output,
            Direction::Input => &self.default_input,
        };
        self.devices(direction)
            .iter()
            .find(|device| Some(&device.name) == name.as_ref())
    }
}

pub struct AudioBackend {
    context: RefCell<Context>,
    state: RefCell<AudioState>,
    on_change: Box<dyn Fn(&AudioState)>,
    observed_state: Cell<State>,
    // Rust drops fields in declaration order: keep the loop after its context.
    _mainloop: Mainloop,
}

impl AudioBackend {
    pub fn new(on_change: impl Fn(&AudioState) + 'static) -> Result<Rc<Self>, String> {
        let mainloop = Mainloop::new(None).ok_or("Cannot create audio mainloop")?;
        let context =
            Context::new(&mainloop, "audio-panel").ok_or("Cannot create audio context")?;
        let backend = Rc::new(Self {
            _mainloop: mainloop,
            context: RefCell::new(context),
            state: RefCell::new(AudioState::default()),
            on_change: Box::new(on_change),
            observed_state: Cell::new(State::Unconnected),
        });
        let weak = Rc::downgrade(&backend);
        backend
            .context
            .borrow_mut()
            .set_state_callback(Some(Box::new(move || {
                let weak = weak.clone();
                // connect/disconnect may call this synchronously while the context
                // is borrowed. Handle the transition after returning to GLib.
                glib::idle_add_local_once(move || {
                    if let Some(backend) = weak.upgrade() {
                        backend.connection_changed();
                    }
                });
            })));
        backend.connect();
        Ok(backend)
    }

    fn connect(self: &Rc<Self>) {
        if let Err(error) = self
            .context
            .borrow_mut()
            .connect(None, FlagSet::NOFLAGS, None)
        {
            self.report_error(&format!("Audio unavailable: {error}"));
        }
    }

    fn connection_changed(self: &Rc<Self>) {
        let state = self.context.borrow().get_state();
        if self.observed_state.replace(state) == state {
            return;
        }
        match state {
            State::Ready => {
                self.state.borrow_mut().connected = true;
                self.state.borrow_mut().error = None;
                let weak = Rc::downgrade(self);
                self.context
                    .borrow_mut()
                    .set_subscribe_callback(Some(Box::new(move |facility, _, _| {
                        if matches!(
                            facility,
                            Some(Facility::Sink | Facility::Source | Facility::Server)
                        ) && let Some(backend) = weak.upgrade()
                        {
                            backend.refresh();
                        }
                    })));
                let weak = Rc::downgrade(self);
                self.context.borrow_mut().subscribe(
                    InterestMaskSet::SINK | InterestMaskSet::SOURCE | InterestMaskSet::SERVER,
                    move |success| {
                        if !success && let Some(backend) = weak.upgrade() {
                            backend.report_error("Cannot subscribe to audio changes");
                        }
                    },
                );
                self.refresh();
            }
            State::Failed | State::Terminated => {
                *self.state.borrow_mut() = AudioState::default();
                self.report_error("Audio unavailable. Reconnecting…");
                let weak = Rc::downgrade(self);
                glib::timeout_add_local_once(Duration::from_secs(2), move || {
                    if let Some(backend) = weak.upgrade() {
                        backend.context.borrow_mut().disconnect();
                        backend.connect();
                    }
                });
            }
            _ => {}
        }
    }

    fn emit(&self) {
        (self.on_change)(&self.state.borrow());
    }
    fn report_error(&self, message: &str) {
        log::warn!("{message}");
        self.state.borrow_mut().error = Some(message.to_string());
        self.emit();
    }
    pub fn refresh(self: &Rc<Self>) {
        if self.context.borrow().get_state() != State::Ready {
            return;
        }
        let weak = Rc::downgrade(self);
        self.context
            .borrow()
            .introspect()
            .get_server_info(move |info| {
                if let Some(backend) = weak.upgrade() {
                    let mut state = backend.state.borrow_mut();
                    state.default_output = info.default_sink_name.as_deref().map(str::to_owned);
                    state.default_input = info.default_source_name.as_deref().map(str::to_owned);
                    drop(state);
                    backend.emit();
                }
            });
        let weak = Rc::downgrade(self);
        let mut devices = Vec::new();
        self.context
            .borrow()
            .introspect()
            .get_sink_info_list(move |result| {
                if let Some(backend) = weak.upgrade() {
                    match result {
                        ListResult::Item(info) => {
                            if let Some(name) = info.name.as_deref() {
                                devices.push(Device {
                                    index: info.index,
                                    name: name.to_string(),
                                    description: info
                                        .description
                                        .as_deref()
                                        .unwrap_or(name)
                                        .to_string(),
                                    volume: info.volume,
                                    muted: info.mute,
                                });
                            }
                        }
                        ListResult::End => {
                            devices.sort_by(|a, b| a.name.cmp(&b.name));
                            backend.state.borrow_mut().outputs = std::mem::take(&mut devices);
                            backend.emit();
                        }
                        ListResult::Error => backend.report_error("Cannot read output devices"),
                    }
                }
            });
        let weak = Rc::downgrade(self);
        let mut devices = Vec::new();
        self.context
            .borrow()
            .introspect()
            .get_source_info_list(move |result| {
                if let Some(backend) = weak.upgrade() {
                    match result {
                        ListResult::Item(info) => {
                            // Playback monitor sources are not microphones.
                            if info.monitor_of_sink.is_none()
                                && let Some(name) = info.name.as_deref()
                            {
                                devices.push(Device {
                                    index: info.index,
                                    name: name.to_string(),
                                    description: info
                                        .description
                                        .as_deref()
                                        .unwrap_or(name)
                                        .to_string(),
                                    volume: info.volume,
                                    muted: info.mute,
                                });
                            }
                        }
                        ListResult::End => {
                            devices.sort_by(|a, b| a.name.cmp(&b.name));
                            backend.state.borrow_mut().inputs = std::mem::take(&mut devices);
                            backend.emit();
                        }
                        ListResult::Error => backend.report_error("Cannot read input devices"),
                    }
                }
            });
    }

    fn operation_result(self: &Rc<Self>, message: &'static str) -> Box<dyn FnMut(bool)> {
        let weak = Rc::downgrade(self);
        Box::new(move |success| {
            if let Some(backend) = weak.upgrade() {
                if success {
                    backend.state.borrow_mut().error = None;
                    backend.refresh();
                } else {
                    backend.report_error(message);
                }
            }
        })
    }

    pub fn set_volume(self: &Rc<Self>, direction: Direction, percent: f64) {
        if !self.state.borrow().connected {
            return;
        }
        let Some(device) = self.state.borrow().selected(direction).cloned() else {
            return;
        };
        let mut volume = device.volume;
        // Preserve channel balance while keeping the loudest channel <= 100%.
        volume.scale(volume_from_percent(percent));
        let mut introspect = self.context.borrow().introspect();
        let callback = Some(self.operation_result("Cannot change volume"));
        match direction {
            Direction::Output => {
                introspect.set_sink_volume_by_index(device.index, &volume, callback);
            }
            Direction::Input => {
                introspect.set_source_volume_by_index(device.index, &volume, callback);
            }
        }
    }

    pub fn toggle_mute(self: &Rc<Self>, direction: Direction) {
        if !self.state.borrow().connected {
            return;
        }
        let Some(device) = self.state.borrow().selected(direction).cloned() else {
            return;
        };
        let mut introspect = self.context.borrow().introspect();
        let callback = Some(self.operation_result("Cannot change mute"));
        match direction {
            Direction::Output => {
                introspect.set_sink_mute_by_index(device.index, !device.muted, callback);
            }
            Direction::Input => {
                introspect.set_source_mute_by_index(device.index, !device.muted, callback);
            }
        }
    }

    pub fn select_device(self: &Rc<Self>, direction: Direction, name: &str) {
        if !self.state.borrow().connected {
            return;
        }
        let state = self.state.borrow();
        let previous = state.selected(direction).map(|device| device.index);
        let Some(target) = state
            .devices(direction)
            .iter()
            .find(|device| device.name == name)
            .cloned()
        else {
            return;
        };
        if Some(target.index) == previous {
            return;
        }
        drop(state);
        let weak = Rc::downgrade(self);
        let callback = move |success| {
            if let Some(backend) = weak.upgrade() {
                if success {
                    backend.move_streams(direction, previous, target.index);
                    backend.state.borrow_mut().error = None;
                    backend.refresh();
                } else {
                    backend.report_error("Cannot switch audio device");
                }
            }
        };
        match direction {
            Direction::Output => {
                self.context.borrow_mut().set_default_sink(name, callback);
            }
            Direction::Input => {
                self.context.borrow_mut().set_default_source(name, callback);
            }
        }
    }

    fn move_streams(self: &Rc<Self>, direction: Direction, previous: Option<u32>, target: u32) {
        let Some(previous) = previous else {
            return;
        };
        let weak = Rc::downgrade(self);
        match direction {
            Direction::Output => {
                self.context
                    .borrow()
                    .introspect()
                    .get_sink_input_info_list(move |result| {
                        if let ListResult::Item(stream) = result
                            && stream.sink == previous
                            && let Some(backend) = weak.upgrade()
                        {
                            backend
                                .context
                                .borrow()
                                .introspect()
                                .move_sink_input_by_index(
                                    stream.index,
                                    target,
                                    Some(backend.operation_result("Cannot move playback")),
                                );
                        }
                    });
            }
            Direction::Input => {
                self.context
                    .borrow()
                    .introspect()
                    .get_source_output_info_list(move |result| {
                        if let ListResult::Item(stream) = result
                            && stream.source == previous
                            && let Some(backend) = weak.upgrade()
                        {
                            backend
                                .context
                                .borrow()
                                .introspect()
                                .move_source_output_by_index(
                                    stream.index,
                                    target,
                                    Some(backend.operation_result("Cannot move recording")),
                                );
                        }
                    });
            }
        }
    }
}

fn volume_from_percent(percent: f64) -> Volume {
    let percent = if percent.is_finite() {
        percent.clamp(0.0, 100.0)
    } else {
        0.0
    };
    Volume((percent * f64::from(Volume::NORMAL.0) / 100.0).round() as u32)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn volume_limits_do_not_allow_amplification_or_invalid_values() {
        assert_eq!(volume_from_percent(-1.0), Volume::MUTED);
        assert_eq!(volume_from_percent(0.0), Volume::MUTED);
        assert_eq!(volume_from_percent(100.0), Volume::NORMAL);
        assert_eq!(volume_from_percent(150.0), Volume::NORMAL);
        assert_eq!(volume_from_percent(f64::NAN), Volume::MUTED);
        assert_eq!(volume_from_percent(f64::INFINITY), Volume::MUTED);
    }
    #[test]
    fn missing_default_device_does_not_target_an_arbitrary_device() {
        let state = AudioState {
            outputs: vec![Device {
                index: 1,
                name: "speaker".into(),
                description: "Speaker".into(),
                volume: ChannelVolumes::default(),
                muted: false,
            }],
            default_output: Some("disconnected-headset".into()),
            ..Default::default()
        };
        assert!(state.selected(Direction::Output).is_none());
        assert!(state.selected(Direction::Input).is_none());
    }
}
