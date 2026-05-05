# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

"""
EncoderAutoFilterComponent — TRACK CONTROL MODE 2 (Shift + Send A).

Replaces the old "Alternate Device Mode" with a focused Auto Filter cockpit.
When the selected track contains a Live AutoFilter device, the 8 Track
Control encoders + 4 bank buttons (Pan / Send A / B / C) re-bind to that
device's most-used parameters:

  Top row    [0=Drive   ][1=Env Atk ][2=Env Rel ][3=LFO Rate ]
  Bottom row [4=Frequency][5=Resonance][6=Env Amt][7=LFO Amt ]
  Bank btns  [Pan=Slope↻][SndA=LFO On][SndB=Type↻][SndC=Sidech]

Pan / Send B step their respective enum parameters (Filter Slope,
Filter Type) one step per press; Send A / Send C toggle their boolean
parameters (LFO On, Side Chain On). Bank-button LEDs reflect the
parameter's current value.

Tracks without an AutoFilter leave all encoders / buttons released and
LEDs off — same fail-quiet behavior as EQ Smart Control on tracks
without an EQ device.

Parameter names are best-effort; on first detection this component logs
the actual parameter list to Live's Log.txt under '[AutoFilter]' so any
name mismatch (e.g. 'Filter Slope' vs 'Slope', 'LFO On' vs 'LFO On/Off')
can be patched after one UAT round.
"""

import Live
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ButtonElement import ButtonElement
from _Framework.MixerComponent import MixerComponent
from _Generic.Devices import *


# Parameter names — verified via the Log.txt dump on first activation
# (now removed). Live 11+ AutoFilter2 uses no-period 'Env Attack' /
# 'Env Release' / 'Env Amount' and exposes 'S/C On' / 'Soft Clip On' as
# the natural performance toggles (there is no 'LFO On' param).
AUTOFILTER_PARAMS = {
    # Static encoders (don't change with filter type or LFO mode)
    'Drive':       'Drive',
    'EnvAttack':   'Env Attack',
    'EnvRelease':  'Env Release',
    'EnvAmount':   'Env Amount',
    'LFOAmount':   'LFO Amount',
    # Filter-type-dependent encoders (resolved at setup-time):
    'Frequency':   'Frequency',   # default
    'Resonance':   'Resonance',   # default
    'Pitch':       'Pitch',       # Vowel filter
    'Formant':     'Formant',     # Vowel filter
    'Control':     'Control',     # DJ filter
    # LFO-T-Mode-dependent encoder 3 (AutoFilter2 has four rate params, one per
    # mode; the GUI knob shows whichever is active — see _resolve_lfo_rate_param):
    'LFOTMode':    'LFO T Mode',
    'LFOFreq':     'LFO Freq',    # Hz mode
    'LFOTime':     'LFO Time',    # S mode (seconds)
    'LFORate':     'LFO Rate',    # 4 mode (4-bar sync)
    'LFO16th':     'LFO 16th',    # 16 mode (16th-note sync)
    # Buttons
    'Slope':       'Filter Slope',
    'FilterType':  'Filter Type',
    'SidechainOn': 'S/C On',       # toggle (the LFO has no on/off; sidechain does)
    'SoftClipOn':  'Soft Clip On', # toggle
}

# Encoder index → AUTOFILTER_PARAMS key. Order: top row 0..3, bottom row 4..7.
# Encoders 3, 4, 5 are dynamic and not in this static map:
#   - 3 wired by _bind_lfo_rate_encoder (resolves via LFO T Mode → LFO Freq / Time / Rate / 16th)
#   - 4, 5 wired by _bind_freq_reso_encoders (Vowel → Pitch/Formant; DJ → Control/—; else → Frequency/Resonance)
ENCODER_MAP = (
    (0, 'Drive'),
    (1, 'EnvAttack'),
    (2, 'EnvRelease'),
    (6, 'EnvAmount'),
    (7, 'LFOAmount'),
)

# LFO T Mode value-items label → AUTOFILTER_PARAMS key for the active rate param.
# Verified via Log.txt diagnostic on AutoFilter2 (Live 11+):
#   value_items = ['Rate', 'Time', 'Synced', 'Triplet', 'Dotted', 'Sixteenth']
# 'Rate'/'Time' are free-running modes (Hz / seconds); 'Synced'/'Triplet'/'Dotted'
# all use the same LFO Rate beat-subdivision param (the T Mode picks the timing
# interpretation, the param picks the subdivision); 'Sixteenth' uses LFO 16th.
LFO_T_MODE_PARAM_KEYS = {
    'Rate':      'LFOFreq',    # Hz / free-running
    'Time':      'LFOTime',    # seconds
    'Synced':    'LFORate',    # beat-synced subdivisions
    'Triplet':   'LFORate',    # triplet timing on the same subdivision selector
    'Dotted':    'LFORate',    # dotted timing on the same subdivision selector
    'Sixteenth': 'LFO16th',    # 16th-note multiples (separate param)
}

# Button index → (AUTOFILTER_PARAMS key, mode 'cycle' | 'toggle')
BUTTON_MAP = (
    (0, 'Slope', 'cycle'),
    (1, 'SidechainOn', 'toggle'),
    (2, 'FilterType', 'cycle'),
    (3, 'SoftClipOn', 'toggle'),
)

# Filter-type label → (freq-encoder-param-key, reso-encoder-param-key).
# Lookup is by the label string from the parameter's value_items, so it works
# regardless of which integer index Live assigns to each filter type in a
# given build. None means "leave the encoder unbound for this filter type"
# (no equivalent control on the device).
FILTER_TYPE_PARAM_OVERRIDES = {
    'Vowel': ('Pitch',   'Formant'),
    'DJ':    ('Control', None),
}


class EncoderAutoFilterComponent(ControlSurfaceComponent):
    """ Encoder mode that maps the 8 Track Control encoders + 4 bank buttons to AutoFilter. """

    def __init__(self, mixer, parent, messenger=None):
        ControlSurfaceComponent.__init__(self)
        assert isinstance(mixer, MixerComponent)
        self._mixer = mixer
        self._parent = parent
        self._param_controls = None
        self._buttons = None
        self._track = None
        self._device = None  # active AutoFilter
        self._lock_button = None
        # Mode-3 ("user mode") sets this True so encoder/button events go nowhere.
        self._ignore_buttons = False
        # Per-button listener bookkeeping. Each entry: (button, callback).
        self._button_bindings = []
        # Per-parameter LED feedback listeners. Each entry: (parameter, callback).
        self._led_listeners = []
        # Status-bar messenger + transition tracker (quick-260505-sb9).
        # AutoFilter Mode has no _engage/_disengage path -- it activates
        # implicitly when _update_controls_and_buttons finds an AutoFilter
        # device on the selected track. _last_active_device tracks whether
        # we've already messaged "AutoFilter Mode" for the current device
        # so flipping a track that has multiple AutoFilters doesn't
        # spam the bar (the dedup window in the messenger covers that
        # too, but the explicit transition gate keeps the intent clear).
        self._messenger = messenger
        self._last_active_device = None
        # Hardware-side param-message listeners (quick-260505-sb9 Task 3).
        # Each entry: (control, callback). Hooks the EncoderElement's
        # value listener -- fires only on incoming MIDI from the APC40.
        # Built per encoder in _update_controls_and_buttons + the dynamic
        # rebind paths (_bind_lfo_rate_encoder / _bind_freq_reso_encoders);
        # torn down in _teardown_bindings.
        self._param_message_listeners = []
        # Filter-type listener so encoders 4/5 swap when user picks Vowel / DJ.
        self._filter_type_listener_param = None
        # LFO T Mode listener so encoder 3 swaps among LFO Freq / Time / Rate / 16th.
        self._lfo_t_mode_listener_param = None
        # One-shot Log.txt dump of the detected AutoFilter's parameter list, so any
        # original_name vs GUI-label mismatch (the cause of the LFO Rate = 'LFO Frequency'
        # bug) surfaces immediately on first activation. Same pattern as
        # EncoderEQComponent._setup_slope_button (FilterEQ3 dump).
        self._params_logged = False
        # One-shot dump of LFO T Mode's value_items so any unmatched mode label
        # (e.g. 'Hertz' vs 'Hz', 'Time' vs 'S') surfaces on first resolution.
        self._lfo_modes_logged = False

    def disconnect(self):
        self._teardown_bindings()
        self._param_controls = None
        self._buttons = None
        self._mixer = None
        self._parent = None
        self._track = None
        self._device = None
        self._lock_button = None
        self._messenger = None
        self._last_active_device = None
        # _teardown_bindings already drained _param_message_listeners; null
        # the list ref so any dangling refs are clearly dead.
        self._param_message_listeners = []

    def update(self):
        pass

    def set_controls_and_buttons(self, controls, buttons):
        # EncoderUserModesComponent passes _modes_buttons as a Python list (built
        # via .append in set_mode_buttons), not a tuple — so accept any sized
        # sequence and just verify the length downstream code requires.
        assert ((controls is None) or (len(controls) == 8))
        assert ((buttons is None) or (len(buttons) == 4))
        self._param_controls = controls
        self._buttons = buttons
        self._update_controls_and_buttons()

    def on_enabled_changed(self):
        if self.is_enabled():
            self._update_controls_and_buttons()
        else:
            # When the EncoderUserModesComponent disables this sub-mode
            # (user flips Shift+Send A away to a different shift mode),
            # treat it as a mode-exit for status-bar purposes if we were
            # previously messaged-as-active. Mirrors the device-disappear
            # path in _update_controls_and_buttons.
            if self._messenger is not None and self._last_active_device is not None:
                try:
                    self._messenger.show_mode('AutoFilter Mode', False)
                except Exception:
                    pass
            self._last_active_device = None
            self._teardown_bindings()

    def set_lock_button(self, button):
        # Compat shim — the EncoderUserModesComponent calls set_lock_button(None)
        # during mode teardown. AutoFilter mode has no lock function (lock is on
        # the regular Track Control mode), so this is a quiet no-op.
        self._lock_button = button

    def on_track_list_changed(self):
        self.on_selected_track_changed()

    def on_selected_track_changed(self):
        if self.is_enabled():
            self._update_controls_and_buttons()

    # --- Internal --------------------------------------------------------

    # Live 9/10 class_name was 'AutoFilter'; Live 11+ ships a new generation as
    # 'AutoFilter2'. Accept both so the mode works regardless of Live version.
    AUTOFILTER_CLASS_NAMES = ('AutoFilter', 'AutoFilter2')

    def _detect_autofilter(self):
        if self._track is None:
            return None
        try:
            devices = list(self._track.devices)
        except Exception:
            return None
        for device in reversed(devices):
            if getattr(device, 'class_name', None) in self.AUTOFILTER_CLASS_NAMES:
                return device
        return None

    def _update_controls_and_buttons(self):
        if self._param_controls is None or self._buttons is None:
            return
        self._teardown_bindings()
        self._track = self.song().view.selected_track
        device = self._detect_autofilter()
        self._device = device
        # Status-bar feedback (quick-260505-sb9). AutoFilter Mode has no
        # explicit _engage/_disengage path -- the mode "enters" when an
        # AutoFilter device first appears under the selected track and
        # "exits" when it goes away (track switch / device deletion).
        # Track _last_active_device so the messenger fires once per real
        # transition; the dedup window in the messenger covers any spurious
        # double-fires from rapid update calls.
        if self._messenger is not None:
            try:
                if device is not None and self._last_active_device is None:
                    self._messenger.show_mode('AutoFilter Mode', True)
                elif device is None and self._last_active_device is not None:
                    self._messenger.show_mode('AutoFilter Mode', False)
                # device is not None and last_active is also not None ->
                # may be the same or different AutoFilter; we don't message
                # mid-stream device swaps within the mode (would be noisy).
            except Exception:
                pass
        self._last_active_device = device
        if device is None:
            return  # no AutoFilter on this track — fail quiet, all controls dark
        # Self-verifying param dump on first detection (sister-component pattern).
        if not self._params_logged:
            self._params_logged = True
            try:
                cls = getattr(device, 'class_name', '?')
                self._parent.log_message('[AutoFilter] detected device class: ' + repr(cls))
                for prm in device.parameters:
                    nm = getattr(prm, 'name', '?')
                    on = getattr(prm, 'original_name', nm)
                    self._parent.log_message('[AutoFilter]   name=' + repr(nm) + '  original_name=' + repr(on))
            except Exception as e:
                try:
                    self._parent.log_message('[AutoFilter] params dump failed: ' + str(e))
                except Exception:
                    pass

        # Bind static encoders (0/1/2/6/7).
        for idx, key in ENCODER_MAP:
            try:
                self._param_controls[idx].release_parameter()
            except Exception:
                pass
            param = get_parameter_by_name(device, AUTOFILTER_PARAMS[key])
            if param is not None:
                try:
                    self._param_controls[idx].connect_to(param)
                    self._attach_param_message_listener(self._param_controls[idx], param)
                except Exception:
                    pass

        # LFO-T-Mode-dependent encoder 3 (LFO Freq / Time / Rate / 16th).
        self._bind_lfo_rate_encoder(device)
        self._attach_lfo_t_mode_listener(device)

        # Filter-type-dependent encoders 4 and 5 (Frequency/Resonance ↔ Pitch/Formant ↔ Control).
        self._bind_freq_reso_encoders(device)
        self._attach_filter_type_listener(device)

        # Bind 4 bank buttons (cycle / toggle handlers + LED listeners).
        for btn_idx, key, kind in BUTTON_MAP:
            button = self._buttons[btn_idx]
            param_name = AUTOFILTER_PARAMS[key]
            param = get_parameter_by_name(device, param_name)
            if param is None:
                # Parameter doesn't exist on this AutoFilter build — leave dark.
                try:
                    button.turn_off()
                except Exception:
                    pass
                continue
            # Closures: capture loop vars via default args.
            if kind == 'toggle':
                callback = (lambda value, p=param: self._toggle_param(p, value))
            else:  # cycle
                callback = (lambda value, p=param: self._cycle_param(p, value))
            try:
                button.add_value_listener(callback)
                self._button_bindings.append((button, callback))
            except Exception:
                pass
            # LED listener so the bank-button LED tracks the parameter.
            led_cb = (lambda b=button, p=param: self._refresh_button_led(b, p))
            try:
                if hasattr(param, 'add_value_listener'):
                    param.add_value_listener(led_cb)
                    self._led_listeners.append((param, led_cb))
            except Exception:
                pass
            # Initial LED paint.
            self._refresh_button_led(button, param)

    def _attach_param_message_listener(self, control, param):
        """Hook a hardware-side value listener on `control` so APC40
        encoder turns emit a status-bar message reading param's
        str_for_value at fire-time. Bookkept in
        self._param_message_listeners; torn down in _teardown_bindings.
        Uses the messenger's factory so the cb resolves the param at
        fire-time (correct for dynamic rebinds via filter-type / LFO
        T Mode listeners). Project idiom: wrap framework calls."""
        if self._messenger is None or control is None or param is None:
            return
        try:
            cb = self._messenger.make_hardware_value_callback(lambda p=param: p)
            control.add_value_listener(cb)
            self._param_message_listeners.append((control, cb))
        except Exception:
            pass

    def _detach_param_message_listener(self, control):
        """Remove any (control, cb) entry whose control matches; used by
        the dynamic rebind paths (filter-type / LFO-T-Mode) so the new
        param's listener doesn't stack on top of the old one."""
        if control is None:
            return
        kept = []
        for ctrl, cb in self._param_message_listeners:
            if ctrl is control:
                try:
                    ctrl.remove_value_listener(cb)
                except Exception:
                    pass
            else:
                kept.append((ctrl, cb))
        self._param_message_listeners = kept

    def _teardown_bindings(self):
        # Status-bar param-message listeners (quick-260505-sb9). Tear down
        # FIRST so a stale listener can't fire on a half-released encoder.
        for ctrl, cb in self._param_message_listeners:
            try:
                ctrl.remove_value_listener(cb)
            except Exception:
                pass
        self._param_message_listeners = []
        # Encoders.
        if self._param_controls is not None:
            for idx in range(8):
                try:
                    self._param_controls[idx].release_parameter()
                except Exception:
                    pass
        # Button listeners.
        for button, callback in self._button_bindings:
            try:
                button.remove_value_listener(callback)
            except Exception:
                pass
            try:
                button.turn_off()
            except Exception:
                pass
        self._button_bindings = []
        # Param LED listeners.
        for param, callback in self._led_listeners:
            try:
                param.remove_value_listener(callback)
            except Exception:
                pass
        self._led_listeners = []
        # Filter-type listener.
        self._detach_filter_type_listener()
        # LFO T Mode listener.
        self._detach_lfo_t_mode_listener()

    # --- Filter-type-dependent freq/reso binding ------------------------

    def _resolve_freq_reso_params(self, device):
        """ Return (freq_param, reso_param) based on the current Filter Type label.
        Vowel → (Pitch, Formant); DJ → (Control, None); otherwise → (Frequency, Resonance). """
        ft_param = get_parameter_by_name(device, AUTOFILTER_PARAMS['FilterType'])
        label = None
        if ft_param is not None:
            try:
                value = int(round(float(ft_param.value)))
                items = list(getattr(ft_param, 'value_items', []))
                if 0 <= value < len(items):
                    label = str(items[value]).strip()
            except Exception:
                label = None
        override = FILTER_TYPE_PARAM_OVERRIDES.get(label) if label else None
        if override is None:
            freq_key, reso_key = 'Frequency', 'Resonance'
        else:
            freq_key, reso_key = override
        freq_param = get_parameter_by_name(device, AUTOFILTER_PARAMS[freq_key]) if freq_key else None
        reso_param = get_parameter_by_name(device, AUTOFILTER_PARAMS[reso_key]) if reso_key else None
        return freq_param, reso_param

    def _bind_freq_reso_encoders(self, device):
        for idx in (4, 5):
            try:
                self._param_controls[idx].release_parameter()
            except Exception:
                pass
            # Drop any prior hardware-side message listener on this
            # encoder before re-binding (quick-260505-sb9). Filter-type
            # rebinds happen mid-mode without a full _teardown_bindings,
            # so the targeted scrub here keeps listener bookkeeping
            # accurate across Vowel / DJ / default switches.
            self._detach_param_message_listener(self._param_controls[idx])
        freq_param, reso_param = self._resolve_freq_reso_params(device)
        if freq_param is not None:
            try:
                self._param_controls[4].connect_to(freq_param)
                self._attach_param_message_listener(self._param_controls[4], freq_param)
            except Exception:
                pass
        if reso_param is not None:
            try:
                self._param_controls[5].connect_to(reso_param)
                self._attach_param_message_listener(self._param_controls[5], reso_param)
            except Exception:
                pass

    def _attach_filter_type_listener(self, device):
        self._detach_filter_type_listener()
        ft_param = get_parameter_by_name(device, AUTOFILTER_PARAMS['FilterType'])
        if ft_param is None or not hasattr(ft_param, 'add_value_listener'):
            return
        try:
            ft_param.add_value_listener(self._on_filter_type_changed)
            self._filter_type_listener_param = ft_param
        except Exception:
            self._filter_type_listener_param = None

    def _detach_filter_type_listener(self):
        if self._filter_type_listener_param is not None:
            try:
                self._filter_type_listener_param.remove_value_listener(self._on_filter_type_changed)
            except Exception:
                pass
            self._filter_type_listener_param = None

    def _on_filter_type_changed(self):
        # User flipped Filter Type — re-evaluate encoders 4/5 only (other
        # encoders + button bindings are static).
        if self._device is not None:
            self._bind_freq_reso_encoders(self._device)

    # --- LFO-T-Mode-dependent rate binding ------------------------------

    def _resolve_lfo_rate_param(self, device):
        """ Return the active LFO-rate Parameter based on LFO T Mode.
        AutoFilter2 has four independent rate params (LFO Freq / LFO Time /
        LFO Rate / LFO 16th); only the one matching the current T Mode is
        wired to the visible 'LFO Rate' GUI knob. """
        mode_param = get_parameter_by_name(device, AUTOFILTER_PARAMS['LFOTMode'])
        label = None
        items = []
        if mode_param is not None:
            try:
                value = int(round(float(mode_param.value)))
                items = list(getattr(mode_param, 'value_items', []))
                if 0 <= value < len(items):
                    label = str(items[value]).strip()
            except Exception:
                label = None
        # One-shot diagnostic — surface the actual mode labels so any future
        # unmatched label is obvious in Log.txt rather than producing a silent
        # wrong binding.
        if not self._lfo_modes_logged:
            self._lfo_modes_logged = True
            try:
                self._parent.log_message('[AutoFilter] LFO T Mode value_items: ' + repr(items))
            except Exception:
                pass
        rate_key = LFO_T_MODE_PARAM_KEYS.get(label) if label else None
        if rate_key is None:
            # Unmatched mode label. Log the surprise so we can patch
            # LFO_T_MODE_PARAM_KEYS, and fall back to the first existing rate
            # param so the encoder isn't dead. Hz is AutoFilter2's default.
            try:
                self._parent.log_message(
                    '[AutoFilter] unmatched LFO T Mode label ' + repr(label) +
                    ' — falling back. Add a prefix to LFO_T_MODE_PARAM_KEYS.')
            except Exception:
                pass
            for key in ('LFOFreq', 'LFORate', 'LFOTime', 'LFO16th'):
                p = get_parameter_by_name(device, AUTOFILTER_PARAMS[key])
                if p is not None:
                    return p
            return None
        return get_parameter_by_name(device, AUTOFILTER_PARAMS[rate_key])

    def _bind_lfo_rate_encoder(self, device):
        try:
            self._param_controls[3].release_parameter()
        except Exception:
            pass
        # Drop any prior hardware-side message listener on encoder 3
        # before re-binding (quick-260505-sb9). LFO-T-Mode rebinds
        # happen mid-mode without full teardown.
        self._detach_param_message_listener(self._param_controls[3])
        rate_param = self._resolve_lfo_rate_param(device)
        if rate_param is not None:
            try:
                self._param_controls[3].connect_to(rate_param)
                self._attach_param_message_listener(self._param_controls[3], rate_param)
            except Exception:
                pass

    def _attach_lfo_t_mode_listener(self, device):
        self._detach_lfo_t_mode_listener()
        mode_param = get_parameter_by_name(device, AUTOFILTER_PARAMS['LFOTMode'])
        if mode_param is None or not hasattr(mode_param, 'add_value_listener'):
            return
        try:
            mode_param.add_value_listener(self._on_lfo_t_mode_changed)
            self._lfo_t_mode_listener_param = mode_param
        except Exception:
            self._lfo_t_mode_listener_param = None

    def _detach_lfo_t_mode_listener(self):
        if self._lfo_t_mode_listener_param is not None:
            try:
                self._lfo_t_mode_listener_param.remove_value_listener(self._on_lfo_t_mode_changed)
            except Exception:
                pass
            self._lfo_t_mode_listener_param = None

    def _on_lfo_t_mode_changed(self):
        # User flipped LFO T Mode — re-bind encoder 3 to the now-active rate param.
        if self._device is not None:
            self._bind_lfo_rate_encoder(self._device)

    # --- Button handlers -------------------------------------------------

    def _toggle_param(self, param, value):
        if self._ignore_buttons or value == 0:
            return
        try:
            cur = float(param.value)
            param.value = 0.0 if cur > 0 else 1.0
        except Exception:
            pass
        # Status-bar feedback (quick-260505-sb9). Read the parameter's
        # POST-toggle value so the message reflects the new state.
        if self._messenger is not None:
            try:
                nm = (getattr(param, 'name', None)
                      or getattr(param, 'original_name', '?'))
                on = float(param.value) > 0
                self._messenger.show_event(nm + ': ' + ('on' if on else 'off'))
            except Exception:
                pass

    def _cycle_param(self, param, value):
        # Step through an enum parameter (Filter Slope, Filter Type) one step
        # per press; wrap around at the parameter's max value.
        if self._ignore_buttons or value == 0:
            return
        try:
            cur = int(round(float(param.value)))
            top = int(round(float(param.max)))
        except Exception:
            return
        try:
            param.value = float((cur + 1) if cur < top else int(round(float(param.min))))
        except Exception:
            pass
        # Status-bar feedback (quick-260505-sb9). Look up the new value's
        # value_items label so the message reads e.g. 'Filter Type: Lowpass'.
        if self._messenger is not None:
            try:
                nm = (getattr(param, 'name', None)
                      or getattr(param, 'original_name', '?'))
                items = list(getattr(param, 'value_items', []))
                idx = int(round(float(param.value)))
                if 0 <= idx < len(items):
                    label = str(items[idx])
                else:
                    label = str(param.value)
                self._messenger.show_event(nm + ': ' + label)
            except Exception:
                pass

    def _refresh_button_led(self, button, param):
        if button is None or param is None:
            return
        try:
            if float(param.value) > 0:
                button.turn_on()
            else:
                button.turn_off()
        except Exception:
            pass


# local variables:
# tab-width: 4
