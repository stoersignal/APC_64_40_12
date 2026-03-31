# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from _Framework.ModeSelectorComponent import ModeSelectorComponent 
from _Framework.ButtonElement import ButtonElement 
from _Framework.MixerComponent import MixerComponent 
PAN_TO_VOL_DELAY = 5 #added delay value for _on_timer Pan/Vol Mode selection

class EncModeSelectorComponent(ModeSelectorComponent):
    ' Class that reassigns encoders on the AxiomPro to different mixer functions '
    __module__ = __name__

    def __init__(self, mixer):
        assert isinstance(mixer, MixerComponent)
        ModeSelectorComponent.__init__(self)
        self._controls = None
        self._mixer = mixer
        self.set_mode(0) #moved here
        self._pan_to_vol_ticks_delay = -1 #added
        self._mode_is_pan = True #new
        self._register_timer_callback(self._on_timer) #added
        self._pan16_top = None
        self._pan16_enc = None
        self._device_component = None
        self._device_controls = None
        self._bank_nav_buttons = None


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
            if ((value != 0) or (not sender.is_momentary())):
                self.set_mode(self._modes_buttons.index(sender))
            if self._modes_buttons.index(sender) == 0 and sender.is_momentary() and (value != 0): #added check for Pan button
                self._pan_to_vol_ticks_delay = PAN_TO_VOL_DELAY
            else:
                self._pan_to_vol_ticks_delay = -1

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
                if self._device_component is not None:
                    self._device_component.set_parameter_controls(None)
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

# local variables:
# tab-width: 4
