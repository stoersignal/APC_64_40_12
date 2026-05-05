# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from _Framework.ModeSelectorComponent import ModeSelectorComponent 
from _Framework.ButtonElement import ButtonElement 
from _Framework.MixerComponent import MixerComponent 
PAN_TO_VOL_DELAY = 5 #added delay value for _on_timer Pan/Vol Mode selection
LONG_PRESS_DELAY = 4 # 4 ticks x 100ms = 400ms — same threshold as v1.0 Solo/Mute

class EncModeSelectorComponent(ModeSelectorComponent):
    ' Class that reassigns encoders on the AxiomPro to different mixer functions '
    __module__ = __name__

    # Encoder sub-mode index → human-readable label for status-bar feedback
    # (quick-260505-sb9 D-06). Module-level tuple so both _mode_value and
    # _on_timer (Send mode revert path) can read the same labels.
    _MODE_NAMES = ('Pan', 'Send A', 'Send B', 'Send C')

    def __init__(self, mixer, messenger=None):
        assert isinstance(mixer, MixerComponent)
        ModeSelectorComponent.__init__(self)
        self._controls = None
        self._mixer = mixer
        self.set_mode(0) #moved here
        self._pan_to_vol_ticks_delay = -1 #added
        self._mode_is_pan = True #new
        self._send_ticks_delay = -1        # countdown for Send mode long-press, -1 = inactive
        self._send_momentary_active = False # True after long-press threshold fires
        self._register_timer_callback(self._on_timer) #added
        self._pan16_top = None
        self._pan16_enc = None
        self._device_component = None
        self._device_controls = None
        self._bank_nav_buttons = None
        # Status-bar messenger (quick-260505-sb9). Emit on every real
        # mode transition (Pan / Send A / Send B / Send C press).
        self._messenger = messenger


    def disconnect(self):
        for button in self._modes_buttons:
            button.remove_value_listener(self._mode_value)

        self._controls = None
        self._mixer = None
        self._pan16_top = None
        self._pan16_enc = None
        self._device_component = None
        self._device_controls = None
        self._bank_nav_buttons = None
        self._send_ticks_delay = -1
        self._send_momentary_active = False
        self._messenger = None
        self._unregister_timer_callback(self._on_timer) #added
        ModeSelectorComponent.disconnect(self)


    def set_modes_buttons(self, buttons):
        assert ((buttons == None) or (isinstance(buttons, tuple) or (len(buttons) == self.number_of_modes())))
        identify_sender = True
        for button in self._modes_buttons:
            button.remove_value_listener(self._mode_value)

        self._modes_buttons = []
        if (buttons != None):
            for button in buttons:
                assert isinstance(button, ButtonElement)
                self._modes_buttons.append(button)
                button.add_value_listener(self._mode_value, identify_sender)
        # self.update()


    def set_controls(self, controls):
        assert ((controls == None) or (isinstance(controls, tuple) and (len(controls) == 8)))
        self._controls = controls
        self.update()


    def set_pan16_components(self, pan16_top, pan16_enc, device_component, device_controls, bank_nav_buttons):
        self._pan16_top = pan16_top
        self._pan16_enc = pan16_enc
        self._device_component = device_component
        self._device_controls = device_controls
        self._bank_nav_buttons = bank_nav_buttons


    def number_of_modes(self):
        return 4


    def _mode_value(self, value, sender):
        if self.is_enabled(): #added to ignore mode buttons when not enabled
            assert (len(self._modes_buttons) > 0)
            assert isinstance(value, int)
            assert isinstance(sender, ButtonElement)
            assert (self._modes_buttons.count(sender) == 1)
            index = self._modes_buttons.index(sender)
            # Capture pre-set_mode index so the status-bar transition gate
            # can compare. set_mode is idempotent on identical index, so a
            # repeat-press of the same mode button does NOT update _mode_index;
            # the dedup window in the messenger covers any user-intended
            # re-confirmation press.
            prev_mode = self._mode_index
            if ((value != 0) or (not sender.is_momentary())):
                self.set_mode(index)
            # Status-bar feedback (quick-260505-sb9). Fire on real
            # transitions only -- only on press-down (value != 0) so we
            # don't double-message on press + release.
            if (value != 0
                    and prev_mode != self._mode_index
                    and self._messenger is not None):
                try:
                    if 0 <= self._mode_index < len(self._MODE_NAMES):
                        self._messenger.show_event(
                            'Encoder mode: ' + self._MODE_NAMES[self._mode_index])
                except Exception:
                    pass
            if index == 0 and sender.is_momentary() and (value != 0): #added check for Pan button
                self._pan_to_vol_ticks_delay = PAN_TO_VOL_DELAY
            else:
                self._pan_to_vol_ticks_delay = -1
            if index >= 1 and sender.is_momentary():
                if value != 0:  # press-down on Send A/B/C — start countdown
                    self._send_ticks_delay = LONG_PRESS_DELAY
                else:           # release on Send A/B/C — revert if momentary was active
                    if self._send_momentary_active:
                        self.set_mode(0)
                        self.update()
                        self._send_momentary_active = False
                        # Send-mode momentary auto-revert: the user just
                        # experienced a mode change back to Pan, so emit
                        # the corresponding status message (quick-260505-sb9).
                        if self._messenger is not None:
                            try:
                                self._messenger.show_event(
                                    'Encoder mode: ' + self._MODE_NAMES[0])
                            except Exception:
                                pass
                    self._send_ticks_delay = -1

    def update(self):
        assert (self._modes_buttons != None)
        if self.is_enabled() and self._modes_buttons != None:
            for button in self._modes_buttons:
                if self._modes_buttons.index(button) == self._mode_index:
                    button.turn_on()
                else:
                    button.turn_off()

        if (self._controls != None) and (self.is_enabled()):
            if self._mode_index == 0:
                # Pan mode: assign both encoder rows to device parameters 1-16.
                # Per D-04: per-track pan is disabled in this mode.
                # Per D-05: ShiftableDeviceComponent releases device encoders.
                # Step 1: Clear mixer pan/send assignments from top encoders.
                for index in range(len(self._controls)):
                    self._mixer.channel_strip(index).set_pan_control(None)
                    self._mixer.channel_strip(index).set_send_controls((None, None, None))
                # Step 2: Release ShiftableDeviceComponent from device encoders (per ENC-07).
                if self._device_component is not None and self._device_controls is not None:
                    self._device_component.set_parameter_controls(tuple())
                # Step 3: Assign top 8 encoders to params 1-8 (per ENC-01, ENC-03).
                if self._pan16_top is not None:
                    self._pan16_top.set_parameter_controls(self._controls)
                # Step 4: Assign device 8 encoders to params 9-16 with bank nav (per ENC-02, ENC-04, D-06).
                if self._pan16_enc is not None:
                    self._pan16_enc.set_parameter_controls(self._device_controls)
                    if self._bank_nav_buttons is not None:
                        self._pan16_enc.set_bank_nav_buttons(
                            self._bank_nav_buttons[0], self._bank_nav_buttons[1]
                        )
            else:
                # Non-Pan modes: release Pan16DeviceComponent instances (per ENC-06)
                # and restore ShiftableDeviceComponent to device encoders (per ENC-07).
                if self._pan16_top is not None:
                    self._pan16_top.set_parameter_controls(None)
                if self._pan16_enc is not None:
                    self._pan16_enc.set_parameter_controls(None)
                    self._pan16_enc.set_bank_nav_buttons(None, None)
                if self._device_component is not None:
                    self._device_component.set_parameter_controls(self._device_controls)
                # Assign top encoders to mixer sends per mode (per MINT-01).
                for index in range(len(self._controls)):
                    self._mixer.channel_strip(index).set_pan_control(None)
                    if self._mode_index == 1:
                        self._mixer.channel_strip(index).set_send_controls((self._controls[index], None, None))
                    elif self._mode_index == 2:
                        self._mixer.channel_strip(index).set_send_controls((None, self._controls[index], None))
                    elif self._mode_index == 3:
                        self._mixer.channel_strip(index).set_send_controls((None, None, self._controls[index]))
                    else:
                        print('Invalid mode index')
                        raise AssertionError
        
    def on_enabled_changed(self):
        # When EncoderUserModesComponent disables this component (shift mode switch),
        # release Pan16DeviceComponent instances to prevent stale encoder bindings.
        # Pitfall 6 guard: without this, device encoders keep controlling device params
        # after shift is pressed and encoder user mode changes away from mode 0.
        if not self.is_enabled():
            if self._pan16_top is not None:
                self._pan16_top.set_enabled(False)
            if self._pan16_enc is not None:
                self._pan16_enc.set_enabled(False)
            self._send_ticks_delay = -1
            if self._send_momentary_active:
                self.set_mode(0)
                self._send_momentary_active = False
        else:
            # Re-enable on component re-enable; update() will route correctly.
            if self._pan16_top is not None:
                self._pan16_top.set_enabled(True)
            if self._pan16_enc is not None:
                self._pan16_enc.set_enabled(True)
            self.update()

    def _on_timer(self): #added to allow press & hold for Pan/Vol Mode selection
        if (self.is_enabled()):
            if (self._pan_to_vol_ticks_delay > -1):
                if (self._pan_to_vol_ticks_delay == 0):
                    self._mode_is_pan = not self._mode_is_pan
                    if self._mode_is_pan == True:
                        self._show_msg_callback("Set to Pan Mode")
                    else:
                        self._show_msg_callback("Set to Volume Mode")
                    self.update()
                self._pan_to_vol_ticks_delay -= 1
            if self._send_ticks_delay > -1:
                if self._send_ticks_delay == 0:
                    self._send_momentary_active = True
                self._send_ticks_delay -= 1

# local variables:
# tab-width: 4
