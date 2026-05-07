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

import Live 
from _Framework.ModeSelectorComponent import ModeSelectorComponent 
from _Framework.ButtonElement import ButtonElement
from _Framework.DeviceComponent import DeviceComponent

class EncoderUserModesComponent(ModeSelectorComponent):
    ' SelectorComponent that assigns encoders to different user functions '
    __module__ = __name__

    def __init__(self, parent, encoder_modes, param_controls, bank_buttons, mixer, device, encoder_device_modes, encoder_eq_modes): #, mixer, sliders):
        assert (len(bank_buttons) == 4)
        ModeSelectorComponent.__init__(self)
        self._parent = parent
        self._encoder_modes = encoder_modes  
        self._param_controls = param_controls
        self._bank_buttons = bank_buttons
        self._mixer = mixer
        self._device = device
        self._encoder_device_modes = encoder_device_modes
        self._encoder_eq_modes = encoder_eq_modes
        self._mode_index = 0
        self._modes_buttons = []
        self._user_buttons = []
        self._last_mode = 0


    def disconnect(self):
        ModeSelectorComponent.disconnect(self)
        self._parent = None
        self._encoder_modes = None
        self._param_controls = None
        self._bank_buttons = None
        self._mixer = None
        self._device = None
        self._encoder_device_modes = None
        self._encoder_eq_modes = None
        self._modes_buttons = None
        self._user_buttons = None

    def on_enabled_changed(self):
        pass

    def set_mode(self, mode):
        assert isinstance(mode, int)
        assert (mode in range(self.number_of_modes()))
        if (self._mode_index != mode):
            self._last_mode = 0 # self._mode_index # keep track of previous mode, to allow conditional actions
            self._mode_index = mode
            self._set_modes()


    def set_mode_buttons(self, buttons):
        assert isinstance(buttons, (tuple,
                                    type(None)))
        for button in self._modes_buttons:
            button.remove_value_listener(self._mode_value)

        self._modes_buttons = []
        if (buttons != None):
            for button in buttons:
                assert isinstance(button, ButtonElement)
                identify_sender = True
                button.add_value_listener(self._mode_value, identify_sender)
                self._modes_buttons.append(button)
            assert (self._mode_index in range(self.number_of_modes()))
            # Quick-260505-lqz: refresh LEDs to reflect current _mode_index
            # immediately on Shift-press. Calling _refresh_mode_leds (not
            # _set_modes) so we don't re-attach sub-components — in modes
            # that remap these buttons (e.g. EQ kill-switches in mode 2),
            # _set_modes would re-bind the sub-component which then reclaims
            # the LEDs and overwrites the single-active-LED scheme.
            self._refresh_mode_leds()
        else:
            # Quick-260505-lqz: Shift-release. Ask the active sub-component
            # to repaint button LEDs so the single-active-LED state we set
            # during Shift hold is replaced by the sub-component's own
            # scheme. Currently only mode 2 (EQ Smart Control) has button-
            # LED ownership that needs immediate restoration. Without this,
            # kill-state LEDs would stay overridden until the next kill
            # toggle / parameter listener fire.
            if self._mode_index == 2 and self._encoder_eq_modes is not None:
                self._encoder_eq_modes.refresh_button_leds()


    def number_of_modes(self):
        return 4


    def update(self):
        pass


    def _mode_value(self, value, sender):
        assert (len(self._modes_buttons) > 0)
        assert isinstance(value, int)
        assert isinstance(sender, ButtonElement)
        assert (self._modes_buttons.count(sender) == 1)
        if ((value != 0) or (not sender.is_momentary())):
            idx = self._modes_buttons.index(sender)
            # Toggle (quick-260505-tg2): re-pressing the same Shift+<mode-button>
            # combo while already in that non-default mode exits back to mode 0
            # (Pan). Mode 0 itself is exempt — Shift+Pan in Pan mode stays a
            # no-op (set_mode is idempotent on identical index).
            if idx == self._mode_index and idx != 0:
                self.set_mode(0)
            else:
                self.set_mode(idx)


    def _refresh_mode_leds(self):
        # Quick-260505-lqz: single-active-LED indicator while Shift is held.
        # Mode 0 (no Shift-mode active) → all 4 LEDs OFF;
        # modes 1/2/3 → only the matching Shift+X button (SendA/B/C) lit.
        # Called in two paths:
        #   1. set_mode_buttons (Shift-press): refresh LEDs without re-running
        #      mode setup — preserves sub-component bindings.
        #   2. _set_modes (mode change): runs LAST so this scheme overrides
        #      any LEDs set by sub-component setup (e.g. EQ kill-switches in
        #      mode 2 set kill-state LEDs via SpecialTrackEQComponent.update).
        if not self.is_enabled():
            return
        for index in range(len(self._modes_buttons)):
            if self._mode_index != 0 and index == self._mode_index:
                self._modes_buttons[index].turn_on()
            else:
                self._modes_buttons[index].turn_off()


    def _set_modes(self):
        if self.is_enabled():
            assert (self._mode_index in range(self.number_of_modes()))
            for button in self._modes_buttons:
                button.release_parameter()
                button.use_default_message()
            for control in self._param_controls:
                control.release_parameter()
                control.use_default_message()
                #control.set_needs_takeover(False)
            self._encoder_modes.set_enabled(False)
            
            # Mode 2 (Shift + Send A) is now AutoFilter mode (was Alternate Device Mode).
            # The new EncoderAutoFilterComponent self-cleans via on_enabled_changed —
            # no _alt_device sub-component to tear down.
            self._encoder_device_modes.set_lock_button(None)
            self._encoder_device_modes.set_enabled(False)
            
            self._encoder_eq_modes.set_enabled(False)
            self._encoder_eq_modes.set_lock_button(None)
            if self._encoder_eq_modes._track_eq != None:
                self._encoder_eq_modes._track_eq.set_cut_buttons(None)
                if self._encoder_eq_modes._track_eq._gain_controls != None:
                    for control in self._encoder_eq_modes._track_eq._gain_controls:
                        control.release_parameter()  
            if self._encoder_eq_modes._strip != None:
                self._encoder_eq_modes._strip.set_send_controls(None)              
            
            self._user_buttons = []

            if (self._mode_index == 0):               
                self._encoder_modes.set_enabled(True)

            elif (self._mode_index == 1):
                self._encoder_device_modes.set_enabled(True)
                self._encoder_device_modes.set_controls_and_buttons(self._param_controls, self._modes_buttons)

            elif (self._mode_index == 2):
                self._encoder_eq_modes.set_enabled(True)
                self._encoder_eq_modes.set_controls_and_buttons(self._param_controls, self._modes_buttons)


            elif (self._mode_index == 3):
                self._encoder_eq_modes._ignore_buttons = True
                if self._encoder_eq_modes._track_eq != None:
                    self._encoder_eq_modes._track_eq._ignore_cut_buttons = True
                self._encoder_device_modes._ignore_buttons = True
                for button in self._modes_buttons:
                    self._user_buttons.append(button)
                for control in self._param_controls:
                    control.set_identifier((control.message_identifier() - 9))
                    control._ring_mode_button.send_value(0)
            else:
                pass

            # Quick-260505-lqz: refresh LEDs LAST so single-active-LED scheme
            # overrides LEDs set by sub-component setup above. In mode 2,
            # EncoderEQComponent.set_controls_and_buttons → set_cut_buttons
            # → update() lights kill-state LEDs on SendA/B/C; this call
            # then overwrites them with the shift-mode indicator (SendB only).
            self._refresh_mode_leds()
            #self._rebuild_callback()



# local variables:
# tab-width: 4
