# http://remotescripts.blogspot.com
"""
Customized APC40 control surface script
Copyright (C) 2010 Hanz Petrov <hanz.petrov@gmail.com>
Additional modification for Ableton Live 9 - Fabrizio Poce 2013 - <http://www.fabriziopoce.com/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# emacs-mode: -*- python-*-
# http://remotescripts.blogspot.com

import Live
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ButtonElement import ButtonElement
from _Framework.EncoderElement import EncoderElement
from _Framework.MixerComponent import MixerComponent 

from _Generic.Devices import *

# 4 ticks x 100ms/tick = 400ms, matching ToggleMomentaryChannelStripComponent.py:8
# so the EQ kill-switch dual behavior feels identical to the v1.0 Solo / Mute one.
LONG_PRESS_DELAY = 4

EQ_DEVICES = {'Eq8': {'Gains': [ ('%i Gain A' % (index + 1)) for index in range(8) ],
                      'Cuts': [ ('%i Filter On A' % (index + 1)) for index in range(8) ]},
              'FilterEQ3': {'Gains': ['GainLo','GainMid','GainHi'],
                            'Cuts': ['LowOn','MidOn','HighOn']},
              'AudioEffectGroupDevice': {'Gains': [('Macro %i' % (index + 2)) for index in range(3) ], #last 3 buttons of top row
                                         'Cuts': [('Macro %i' % (index + 6)) for index in range(3) ]}, #last 3 buttons of bottom row
              # Channel EQ (Live 11+) — band gains land on the same encoders as FilterEQ3 (5/6/7) for muscle-memory
              # consistency. Channel EQ has no per-band on/off, so 'Cuts' is empty and the kill buttons stay dark.
              # Mid Freq / Output Gain / Highpass On are wired separately by EncoderEQComponent (see CHANNEL_EQ_EXTRAS).
              'ChannelEq': {'Gains': ['Low Gain', 'Mid Gain', 'High Gain'],
                            'Cuts': []},
              }

# Channel EQ extras — controls that don't fit the gain/cut shape:
#   - Encoder 0 ("very first encoder in the first row")    → Mid Freq (the user's "split frequency")
#   - Encoder 4 ("encoder to the left" of the band knobs)  → Output (output trim)
#   - Pan button (buttons[0], directly below encoder 4)    → Highpass on/off (replaces the lock button while ChannelEq is active)
# Parameter names verified via Log.txt dump on UAT 2026-05-04 — the output trim
# is named 'Output' (not 'Output Gain' as initially guessed).
CHANNEL_EQ_EXTRAS = {
    'Output': 'Output',
    'MidFreq': 'Mid Freq',
    'HighpassOn': 'Highpass On',
}
FILTER_DEVICES = {'AutoFilter': {'Frequency': 'Frequency',
                                 'Resonance': 'Resonance'},
                  'Operator': {'Frequency': 'Filter Freq',
                               'Resonance': 'Filter Res'},
                  'OriginalSimpler': {'Frequency': 'Filter Freq',
                                      'Resonance': 'Filter Res'},
                  'MultiSampler': {'Frequency': 'Filter Freq',
                                   'Resonance': 'Filter Res'},
                  'UltraAnalog': {'Frequency': 'F1 Freq',
                                  'Resonance': 'F1 Resonance'},
                  'StringStudio': {'Frequency': 'Filter Freq',
                                   'Resonance': 'Filter Reso'},
                  'AudioEffectGroupDevice': {'Frequency': 'Macro 1',
                                             'Resonance': 'Macro 5'}}#,
                  #'FilterEQ3': {'Frequency': 'FreqLo',
                                #'Resonance': 'FreqHi'}}

class TrackEQComponent(ControlSurfaceComponent):
    """ Class representing a track's EQ, it attaches to the last EQ device in the track """

    def __init__(self):
        ControlSurfaceComponent.__init__(self)
        self._track = None
        self._device = None
        self._gain_controls = None
        self._cut_buttons = None
        return

    def disconnect(self):
        if self._gain_controls != None:
            for control in self._gain_controls:
                control.release_parameter()

            self._gain_controls = None
        if self._cut_buttons != None:
            for button in self._cut_buttons:
                button.remove_value_listener(self._cut_value)

        self._cut_buttons = None
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            self._track = None
        self._device = None
        if self._device != None:
            device_dict = EQ_DEVICES[self._device.class_name]
            if 'Cuts' in list(device_dict.keys()):
                cut_names = device_dict['Cuts']
                for cut_name in cut_names:
                    parameter = get_parameter_by_name(self._device, cut_name)
                    if parameter != None and parameter.value_has_listener(self._on_cut_changed):
                        parameter.remove_value_listener(self._on_cut_changed)

        return

    def on_enabled_changed(self):
        self.update()

    def set_track(self, track):
        if not (track == None or isinstance(track, Live.Track.Track)):
            raise AssertionError
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            if self._gain_controls != None and self._device != None:
                for control in self._gain_controls:
                    control.release_parameter()

        self._track = track
        self._track != None and self._track.add_devices_listener(self._on_devices_changed)
        self._on_devices_changed()
        return

    def set_cut_buttons(self, buttons):
        if not (buttons == None or isinstance(buttons, tuple)):
            raise AssertionError
        if buttons != self._cut_buttons and self._cut_buttons != None:
            for button in self._cut_buttons:
                button.remove_value_listener(self._cut_value)

        self._cut_buttons = buttons
        if self._cut_buttons != None:
            for button in self._cut_buttons:
                button.add_value_listener(self._cut_value, identify_sender=True)

        self.update()
        return

    def set_gain_controls(self, controls):
        if not (controls == None or isinstance(controls, tuple)):
            raise AssertionError
        if self._device != None and self._gain_controls != None:
            for control in self._gain_controls:
                control.release_parameter()

        if controls != None:
            for control in controls:
                if not isinstance(control, EncoderElement):
                    raise AssertionError

        self._gain_controls = controls
        self.update()
        return

    def update(self):
        super(TrackEQComponent, self).update()
        if self.is_enabled() and self._device != None:
            device_dict = EQ_DEVICES[self._device.class_name]
            if self._gain_controls != None:
                gain_names = device_dict['Gains']
                for index in range(len(self._gain_controls)):
                    self._gain_controls[index].release_parameter()
                    if len(gain_names) > index:
                        parameter = get_parameter_by_name(self._device, gain_names[index])
                        if parameter != None:
                            self._gain_controls[index].connect_to(parameter)

            if self._cut_buttons != None and 'Cuts' in list(device_dict.keys()):
                cut_names = device_dict['Cuts']
                for index in range(len(self._cut_buttons)):
                    self._cut_buttons[index].turn_off()
                    if len(cut_names) > index:
                        parameter = get_parameter_by_name(self._device, cut_names[index])
                        if parameter != None:
                            if parameter.value == 0.0:
                                self._cut_buttons[index].turn_on()
                            if not parameter.value_has_listener(self._on_cut_changed):
                                parameter.add_value_listener(self._on_cut_changed)

        else:
            if self._cut_buttons != None:
                for button in self._cut_buttons:
                    if button != None:
                        button.turn_off()

            if self._gain_controls != None:
                for control in self._gain_controls:
                    control.release_parameter()

        return

    def _cut_value(self, value, sender):
        if not sender in self._cut_buttons:
            raise AssertionError
        if not value in range(128):
            raise AssertionError
        if self.is_enabled() and self._device != None:
            if not sender.is_momentary() or value != 0:
                device_dict = EQ_DEVICES[self._device.class_name]
                if 'Cuts' in list(device_dict.keys()):
                    cut_names = device_dict['Cuts']
                    index = list(self._cut_buttons).index(sender)
                    parameter = index in range(len(cut_names)) and get_parameter_by_name(self._device, cut_names[index])
                    parameter.value = parameter != None and parameter.is_enabled and float(int(parameter.value + 1) % 2)
        return

    def _on_devices_changed(self):
        if self._device != None:
            device_dict = EQ_DEVICES[self._device.class_name]
            if 'Cuts' in list(device_dict.keys()):
                cut_names = device_dict['Cuts']
                for cut_name in cut_names:
                    parameter = get_parameter_by_name(self._device, cut_name)
                    if parameter != None and parameter.value_has_listener(self._on_cut_changed):
                        parameter.remove_value_listener(self._on_cut_changed)

        self._device = None
        if self._track != None:
            for index in range(len(self._track.devices)):
                device = self._track.devices[-1 * (index + 1)]
                if device.class_name in list(EQ_DEVICES.keys()):
                    self._device = device
                    break

        self.update()
        return

    def _on_cut_changed(self):
        if not self._device != None:
            raise AssertionError
        raise 'Cuts' in list(EQ_DEVICES[self._device.class_name].keys()) or AssertionError
        cut_names = self.is_enabled() and self._cut_buttons != None and EQ_DEVICES[self._device.class_name]['Cuts']
        for index in range(len(self._cut_buttons)):
            self._cut_buttons[index].turn_off()
            if len(cut_names) > index:
                parameter = get_parameter_by_name(self._device, cut_names[index])
                if parameter != None and parameter.value == 0.0:
                    self._cut_buttons[index].turn_on()

        return

class TrackFilterComponent(ControlSurfaceComponent):
    """ Class representing a track's filter, attaches to the last filter in the track """

    def __init__(self):
        ControlSurfaceComponent.__init__(self)
        self._track = None
        self._device = None
        self._freq_control = None
        self._reso_control = None
        return

    def disconnect(self):
        if self._freq_control != None:
            self._freq_control.release_parameter()
            self._freq_control = None
        if self._reso_control != None:
            self._reso_control.release_parameter()
            self._reso_control = None
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            self._track = None
        self._device = None
        return

    def on_enabled_changed(self):
        self.update()

    def set_track(self, track):
        if not (track == None or isinstance(track, Live.Track.Track)):
            raise AssertionError
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            if self._device != None:
                if self._freq_control != None:
                    self._freq_control.release_parameter()
                if self._reso_control != None:
                    self._reso_control.release_parameter()
        self._track = track
        self._track != None and self._track.add_devices_listener(self._on_devices_changed)
        self._on_devices_changed()
        return

    def set_filter_controls(self, freq, reso):
        if not isinstance(freq, EncoderElement):
            raise AssertionError
        if not isinstance(freq, EncoderElement):
            raise AssertionError
        if self._device != None:
            self._freq_control != None and self._freq_control.release_parameter()
        self._reso_control != None and self._reso_control.release_parameter()
        self._freq_control = freq
        self._reso_control = reso
        self.update()
        return

    def update(self):
        super(TrackFilterComponent, self).update()
        if self.is_enabled() and self._device != None:
            device_dict = FILTER_DEVICES[self._device.class_name]
            if self._freq_control != None:
                self._freq_control.release_parameter()
                parameter = get_parameter_by_name(self._device, device_dict['Frequency'])
                if parameter != None:
                    self._freq_control.connect_to(parameter)
            if self._reso_control != None:
                self._reso_control.release_parameter()
                parameter = get_parameter_by_name(self._device, device_dict['Resonance'])
                if parameter != None:
                    self._reso_control.connect_to(parameter)
        return

    def _on_devices_changed(self):
        self._device = None
        if self._track != None:
            for index in range(len(self._track.devices)):
                device = self._track.devices[-1 * (index + 1)]
                if device.class_name in list(FILTER_DEVICES.keys()):
                    self._device = device
                    break

        self.update()
        return

class SpecialTrackEQComponent(TrackEQComponent): #added to override _cut_value

    def __init__(self, parent):
        TrackEQComponent.__init__(self)
        self._ignore_cut_buttons = False
        self._parent = parent
        # Toggle / momentary state for the EQ kill switches in TRACK CONTROL MODE 3
        # (Shift + Send B). Mirrors the v1.0 Solo / Mute state machine in
        # ToggleMomentaryChannelStripComponent. State arrays are sized to match
        # the wired cut-button count by set_cut_buttons.
        self._cut_ticks_delay = []
        self._cut_state_before_press = []
        self._cut_momentary_active = []
        self._register_timer_callback(self._on_timer)

    def disconnect(self):
        # Revert any in-flight momentary holds so the parameter doesn't get stuck
        # in the just-pressed state.
        if self._cut_buttons is not None and self._device is not None:
            device_dict = EQ_DEVICES.get(self._device.class_name, {})
            cut_names = device_dict.get('Cuts', [])
            for i in range(len(self._cut_buttons)):
                if i < len(self._cut_momentary_active) and self._cut_momentary_active[i]:
                    if i < len(cut_names):
                        parameter = get_parameter_by_name(self._device, cut_names[i])
                        if parameter is not None:
                            try:
                                parameter.value = self._cut_state_before_press[i]
                            except Exception:
                                pass
                    self._cut_momentary_active[i] = False
        try:
            self._unregister_timer_callback(self._on_timer)
        except Exception:
            pass
        TrackEQComponent.disconnect(self)

    def set_cut_buttons(self, buttons):
        # Revert any momentary hold on the OUTGOING buttons before swapping —
        # otherwise the captured state gets dropped when the array is resized.
        if self._cut_buttons is not None and self._device is not None:
            device_dict = EQ_DEVICES.get(self._device.class_name, {})
            cut_names = device_dict.get('Cuts', [])
            for i in range(len(self._cut_buttons)):
                if i < len(self._cut_momentary_active) and self._cut_momentary_active[i]:
                    if i < len(cut_names):
                        parameter = get_parameter_by_name(self._device, cut_names[i])
                        if parameter is not None:
                            try:
                                parameter.value = self._cut_state_before_press[i]
                            except Exception:
                                pass
        TrackEQComponent.set_cut_buttons(self, buttons)
        n = len(buttons) if buttons is not None else 0
        self._cut_ticks_delay = [-1] * n
        self._cut_state_before_press = [0.0] * n
        self._cut_momentary_active = [False] * n

    def _on_timer(self):
        if not self.is_enabled():
            return
        for i in range(len(self._cut_ticks_delay)):
            if self._cut_ticks_delay[i] > -1:
                if self._cut_ticks_delay[i] == 0:
                    self._cut_momentary_active[i] = True
                self._cut_ticks_delay[i] -= 1

    def _cut_value(self, value, sender):
        assert (sender in self._cut_buttons)
        assert (value in range(128))
        if self._ignore_cut_buttons:
            return
        if not (self.is_enabled() and self._device is not None):
            return
        device_dict = EQ_DEVICES[self._device.class_name]
        if 'Cuts' not in device_dict:
            return
        cut_names = device_dict['Cuts']
        index = list(self._cut_buttons).index(sender)
        if index >= len(cut_names) or index >= len(self._cut_ticks_delay):
            return
        parameter = get_parameter_by_name(self._device, cut_names[index])
        if parameter is None:
            return
        if value != 0:
            # Press — capture pre-press state, toggle, start countdown.
            try:
                self._cut_state_before_press[index] = float(parameter.value)
            except Exception:
                return
            if parameter.value > 0:
                parameter.value = 0
            else:
                parameter.value = 1
            if self._device.class_name == 'AudioEffectGroupDevice':
                parameter.value = parameter.value * 127
            self._cut_ticks_delay[index] = LONG_PRESS_DELAY
        else:
            # Release — if hold crossed the threshold, revert to captured state.
            if self._cut_momentary_active[index]:
                try:
                    parameter.value = self._cut_state_before_press[index]
                except Exception:
                    pass
                self._cut_momentary_active[index] = False
            self._cut_ticks_delay[index] = -1



    def update(self):
        if (self.is_enabled() and (self._device != None)):
            device_dict = EQ_DEVICES[self._device.class_name]
            if (self._gain_controls != None):
                gain_names = device_dict['Gains']
                for index in range(len(self._gain_controls)):
                    self._gain_controls[index].release_parameter()
                    if (len(gain_names) > index):
                        parameter = get_parameter_by_name(self._device, gain_names[index])
                        if (parameter != None):
                            self._gain_controls[index].connect_to(parameter)

            if ((self._cut_buttons != None) and ('Cuts' in list(device_dict.keys()))):
                cut_names = device_dict['Cuts']
                for index in range(len(self._cut_buttons)):
                    self._cut_buttons[index].turn_off()
                    if (len(cut_names) > index):
                        parameter = get_parameter_by_name(self._device, cut_names[index])
                        if (parameter != None):
                            if self._device.class_name == 'FilterEQ3':
                                if (parameter.value == 0.0):
                                    self._cut_buttons[index].turn_on()
                            else:
                                if (parameter.value > 0.0):
                                    self._cut_buttons[index].turn_on()
                            if (not parameter.value_has_listener(self._on_cut_changed)):
                                parameter.add_value_listener(self._on_cut_changed)

        else:
            if (self._cut_buttons != None):
                for button in self._cut_buttons:
                    if (button != None):
                        button.turn_off()

            if (self._gain_controls != None):
                for control in self._gain_controls:
                    control.release_parameter()

        #self._rebuild_callback()

    def _on_cut_changed(self):
        assert (self._device != None)
        assert ('Cuts' in list(EQ_DEVICES[self._device.class_name].keys()))
        if (self.is_enabled() and (self._cut_buttons != None)):
            cut_names = EQ_DEVICES[self._device.class_name]['Cuts']
            for index in range(len(self._cut_buttons)):
                self._cut_buttons[index].turn_off()
                if (len(cut_names) > index):
                    parameter = get_parameter_by_name(self._device, cut_names[index])
                    if (parameter != None):
                        if self._device.class_name == 'FilterEQ3':
                            if (parameter.value == 0.0):
                                self._cut_buttons[index].turn_on()
                        else:
                            if (parameter.value > 0.0):
                                self._cut_buttons[index].turn_on()

    def _on_devices_changed(self):
        if (self._device != None):
            device_dict = EQ_DEVICES[self._device.class_name]
            if ('Cuts' in list(device_dict.keys())):
                cut_names = device_dict['Cuts']
                for cut_name in cut_names:
                    parameter = get_parameter_by_name(self._device, cut_name)
                    if ((parameter != None) and parameter.value_has_listener(self._on_cut_changed)):
                        parameter.remove_value_listener(self._on_cut_changed)

        self._device = None
        if (self._track != None):
            for index in range(len(self._track.devices)):
                device = self._track.devices[(-1 * (index + 1))]
                if (device.class_name in list(EQ_DEVICES.keys())):
                    self._device = device
                    break

        self.update()

class SpecialTrackFilterComponent(TrackFilterComponent): #added to override _cut_value
    __module__ = __name__
    __doc__ = " Class representing a track's filter, attaches to the last filter in the track "

    def __init__(self, parent):
        TrackFilterComponent.__init__(self)
        self._parent = parent                        


    def update(self):
        if (self.is_enabled() and (self._device != None)):
            device_dict = FILTER_DEVICES[self._device.class_name]
            if (self._freq_control != None):
                self._freq_control.release_parameter()
                parameter = get_parameter_by_name(self._device, device_dict['Frequency'])
                if (parameter != None):
                    self._freq_control.connect_to(parameter)
            if (self._reso_control != None):
                self._reso_control.release_parameter()
                parameter = get_parameter_by_name(self._device, device_dict['Resonance'])
                if (parameter != None):
                    self._reso_control.connect_to(parameter)
        #self._rebuild_callback()


    def _on_devices_changed(self):
        self._device = None
        if (self._track != None):
            for index in range(len(self._track.devices)):
                device = self._track.devices[(-1 * (index + 1))]
                if (device.class_name in list(FILTER_DEVICES.keys())):
                    self._device = device
                    break

        self.update()        

class EncoderEQComponent(ControlSurfaceComponent):
    __module__ = __name__
    __doc__ = " Class representing encoder EQ component "

    def __init__(self, mixer, parent):
        ControlSurfaceComponent.__init__(self)
        assert isinstance(mixer, MixerComponent)
        self._param_controls = None
        self._mixer = mixer
        self._buttons = []
        self._param_controls = None
        self._lock_button = None
        self._last_mode = 0
        self._is_locked = False
        self._ignore_buttons = False
        self._track = None
        self._strip = None
        self._parent = parent
        self._track_eq = SpecialTrackEQComponent(parent)
        self._track_filter = SpecialTrackFilterComponent(parent)
        # Channel EQ (Live 11+) state — extras that don't fit the gain/cut shape.
        self._channel_eq_device = None
        self._highpass_button = None
        self._highpass_parameter = None
        self._highpass_listener_attached = False

    def disconnect(self):
        self._teardown_channel_eq_extras()
        self._param_controls = None
        self._mixer = None
        self._buttons = None
        self._param_controls = None
        self._lock_button = None
        self._track = None
        self._strip = None
        self._parent = None
        self._track_eq = None
        self._track_filter = None
        self._channel_eq_device = None

    def update(self):
        pass


    def set_controls_and_buttons(self, controls, buttons):
        assert ((controls == None) or (isinstance(controls, tuple) and (len(controls) == 8)))
        self._param_controls = controls
        assert ((buttons == None) or (isinstance(buttons, tuple)) or (len(buttons) == 4))
        self._buttons = buttons
        # NB: Pan button (buttons[0]) wiring is decided per-track inside
        # _update_controls_and_buttons so Channel EQ can claim it as the
        # Highpass switch — non-ChannelEq tracks fall back to lock.
        self._update_controls_and_buttons()


    def _update_controls_and_buttons(self):
        if self._param_controls is None or self._buttons is None:
            return
        if self._is_locked != True:
            self._track = self.song().view.selected_track

        # EQ + sends wiring (always on, regardless of EQ device subclass).
        self._track_eq.set_track(self._track)
        cut_buttons = [self._buttons[1], self._buttons[2], self._buttons[3]]
        self._track_eq.set_cut_buttons(tuple(cut_buttons))
        self._track_eq.set_gain_controls(tuple([
            self._param_controls[5], self._param_controls[6], self._param_controls[7]
        ]))

        # Channel EQ wins on encoders 0/4 + Pan button when present;
        # otherwise fall back to AutoFilter on encoders 0/4 and lock on Pan.
        channel_eq = self._detect_channel_eq()
        if channel_eq is not None:
            self._track_filter.set_track(None)
            self._teardown_channel_eq_extras()
            self._channel_eq_device = channel_eq
            self._setup_channel_eq_extras(channel_eq)
            self.set_lock_button(None)
        else:
            self._teardown_channel_eq_extras()
            self._channel_eq_device = None
            self._track_filter.set_track(self._track)
            self._track_filter.set_filter_controls(
                self._param_controls[0], self._param_controls[4]
            )
            self.set_lock_button(self._buttons[0])

        if self._is_locked != True:
            self._strip = self._mixer._selected_strip
        if self._strip is not None:
            self._strip.set_send_controls(tuple([
                self._param_controls[1], self._param_controls[2], self._param_controls[3]
            ]))


    # --- Channel EQ helpers (Live 11+) -----------------------------------

    def _detect_channel_eq(self):
        if self._track is None:
            return None
        try:
            devices = list(self._track.devices)
        except Exception:
            return None
        for device in reversed(devices):
            if getattr(device, 'class_name', None) == 'ChannelEq':
                return device
        return None

    def _setup_channel_eq_extras(self, channel_eq):
        try:
            self._param_controls[0].release_parameter()
        except Exception:
            pass
        try:
            self._param_controls[4].release_parameter()
        except Exception:
            pass
        midfreq = get_parameter_by_name(channel_eq, CHANNEL_EQ_EXTRAS['MidFreq'])
        if midfreq is not None:
            try:
                self._param_controls[0].connect_to(midfreq)
            except Exception:
                pass
        output = get_parameter_by_name(channel_eq, CHANNEL_EQ_EXTRAS['Output'])
        if output is not None:
            try:
                self._param_controls[4].connect_to(output)
            except Exception:
                pass
        self._setup_highpass_button(self._buttons[0], channel_eq)

    def _teardown_channel_eq_extras(self):
        if self._param_controls is not None:
            try:
                self._param_controls[0].release_parameter()
            except Exception:
                pass
            try:
                self._param_controls[4].release_parameter()
            except Exception:
                pass
        self._teardown_highpass_button()

    def _setup_highpass_button(self, button, channel_eq):
        self._teardown_highpass_button()
        if button is None or channel_eq is None:
            return
        hp = get_parameter_by_name(channel_eq, CHANNEL_EQ_EXTRAS['HighpassOn'])
        if hp is None:
            return
        self._highpass_button = button
        self._highpass_parameter = hp
        try:
            button.add_value_listener(self._highpass_value)
        except Exception:
            pass
        try:
            hp.add_value_listener(self._on_highpass_changed)
            self._highpass_listener_attached = True
        except Exception:
            pass
        self._update_highpass_led()

    def _teardown_highpass_button(self):
        if self._highpass_button is not None:
            try:
                self._highpass_button.remove_value_listener(self._highpass_value)
            except Exception:
                pass
            self._highpass_button = None
        if self._highpass_listener_attached and self._highpass_parameter is not None:
            try:
                self._highpass_parameter.remove_value_listener(self._on_highpass_changed)
            except Exception:
                pass
        self._highpass_listener_attached = False
        self._highpass_parameter = None

    def _highpass_value(self, value):
        if value == 0:
            return
        if self._highpass_parameter is None:
            return
        try:
            cur = float(self._highpass_parameter.value)
            self._highpass_parameter.value = 0.0 if cur > 0 else 1.0
        except Exception:
            pass

    def _on_highpass_changed(self):
        self._update_highpass_led()

    def _update_highpass_led(self):
        if self._highpass_button is None or self._highpass_parameter is None:
            return
        try:
            if float(self._highpass_parameter.value) > 0:
                self._highpass_button.turn_on()
            else:
                self._highpass_button.turn_off()
        except Exception:
            pass


    def on_track_list_changed(self):
        self.on_selected_track_changed()


    def on_selected_track_changed(self):
        if self.is_enabled():
            if self._is_locked != True:
                self._update_controls_and_buttons()


    def on_enabled_changed(self):
        self.update()  

    def set_lock_button(self, button):
        assert ((button == None) or isinstance(button, ButtonElement))
        if (self._lock_button != None):
            self._lock_button.remove_value_listener(self._lock_value)
            self._lock_button = None
        self._lock_button = button
        if (self._lock_button != None):
            self._lock_button.add_value_listener(self._lock_value)
            if self._is_locked:
                self._lock_button.turn_on()
            else:
                self._lock_button.turn_off()            


    def _lock_value(self, value):
        assert (self._lock_button != None)
        assert (value != None)
        assert isinstance(value, int)
        if ((not self._lock_button.is_momentary()) or (value != 0)):
        #if (value != 0):
            if self._ignore_buttons == False:
                if self._is_locked:
                    self._is_locked = False
                    self._mixer._is_locked = False
                    self._lock_button.turn_off()
                    self._mixer.on_selected_track_changed()
                    self.on_selected_track_changed()
                else:
                    self._is_locked = True
                    self._mixer._is_locked = True
                    self._lock_button.turn_on()



# local variables:
# tab-width: 4
