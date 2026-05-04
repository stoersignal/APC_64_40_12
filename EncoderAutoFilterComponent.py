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


# Parameter-name guesses — verified via Log.txt dump on first activation.
AUTOFILTER_PARAMS = {
    # Encoders (top row → bottom row)
    'Drive':       'Drive',
    'EnvAttack':   'Env. Attack',
    'EnvRelease':  'Env. Release',
    'LFORate':     'LFO Rate',
    'Frequency':   'Frequency',
    'Resonance':   'Resonance',
    'EnvAmount':   'Env. Amount',
    'LFOAmount':   'LFO Amount',
    # Buttons
    'Slope':       'Filter Slope',
    'LFOOn':       'LFO On',
    'FilterType':  'Filter Type',
    'SidechainOn': 'Sidechain Mix',  # falls back gracefully when absent
}

# Encoder index → AUTOFILTER_PARAMS key. Order: top row 0..3, bottom row 4..7.
ENCODER_MAP = (
    (0, 'Drive'),
    (1, 'EnvAttack'),
    (2, 'EnvRelease'),
    (3, 'LFORate'),
    (4, 'Frequency'),
    (5, 'Resonance'),
    (6, 'EnvAmount'),
    (7, 'LFOAmount'),
)

# Button index → (AUTOFILTER_PARAMS key, mode 'cycle' | 'toggle')
BUTTON_MAP = (
    (0, 'Slope', 'cycle'),
    (1, 'LFOOn', 'toggle'),
    (2, 'FilterType', 'cycle'),
    (3, 'SidechainOn', 'toggle'),
)


class EncoderAutoFilterComponent(ControlSurfaceComponent):
    """ Encoder mode that maps the 8 Track Control encoders + 4 bank buttons to AutoFilter. """

    def __init__(self, mixer, parent):
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
        # One-shot Log.txt dump of param names on first AutoFilter detection.
        self._autofilter_logged = False

    def disconnect(self):
        self._teardown_bindings()
        self._param_controls = None
        self._buttons = None
        self._mixer = None
        self._parent = None
        self._track = None
        self._device = None
        self._lock_button = None

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
        if device is None:
            return  # no AutoFilter on this track — fail quiet, all controls dark

        # One-shot Log.txt dump for parameter-name verification (mirrors the
        # ChannelEq / FilterEQ3 / Eq8 pattern; a few missed names are caught
        # in one UAT round instead of multiple).
        if not self._autofilter_logged:
            self._autofilter_logged = True
            try:
                self._parent.log_message('[AutoFilter] params on detected device:')
                for p in device.parameters:
                    self._parent.log_message('[AutoFilter]   ' + repr(p.name))
            except Exception as e:
                self._parent.log_message('[AutoFilter] params introspection failed: ' + str(e))

        # Bind 8 encoders.
        for idx, key in ENCODER_MAP:
            try:
                self._param_controls[idx].release_parameter()
            except Exception:
                pass
            param = get_parameter_by_name(device, AUTOFILTER_PARAMS[key])
            if param is not None:
                try:
                    self._param_controls[idx].connect_to(param)
                except Exception:
                    pass

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

    def _teardown_bindings(self):
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

    # --- Button handlers -------------------------------------------------

    def _toggle_param(self, param, value):
        if self._ignore_buttons or value == 0:
            return
        try:
            cur = float(param.value)
            param.value = 0.0 if cur > 0 else 1.0
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
