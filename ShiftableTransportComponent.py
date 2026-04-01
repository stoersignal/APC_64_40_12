# http://remotescripts.blogspot.com

# partial --== Decompile ==-- with fixes
import Live
from .CustomTransportComponent import CustomTransportComponent
from _Framework.ButtonElement import ButtonElement
from _Framework.EncoderElement import EncoderElement

# Beat sync values in beats (quarter notes). 1 bar = 4 beats.
BEAT_SYNC_VALUES = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
BEAT_SYNC_LABELS = ('1/16', '1/8', '1/4', '1/2', '1 bar', '2 bars', '4 bars', '8 bars')
RAMP_TIMER_INTERVAL = 0.1  # 100ms per tick, same as framework timer

class ShiftableTransportComponent(CustomTransportComponent):
    __doc__ = ' CustomTransportComponent that only uses certain buttons if a shift button is pressed '
    def __init__(self):
        CustomTransportComponent.__init__(self)
        self._shift_button = None
        self._quant_toggle_button = None
        self._shift_pressed = False
        self._last_quant_value = Live.Song.RecordingQuantization.rec_q_eight
        self.song().add_midi_recording_quantization_listener(self._on_quantisation_changed)
        self._on_quantisation_changed()
        self._undo_button = None
        self._redo_button = None
        self._bts_button = None
        self._tempo_encoder_control = None
        # Ramp state for variation recall
        self._ramp_ms = 0  # ramp time in milliseconds (0 = instant)
        self._ramp_beat_index = -1  # index into BEAT_SYNC_VALUES (-1 = not synced)
        self._ramp_mode = 'ms'  # 'ms' or 'beats' — last touched wins
        self._ramp_edit_active = False  # True while Shift+Tap Tempo is held
        self._ramp_edit_touched = False  # True if encoders were turned during ramp edit
        self._ramp_encoders = None  # tuple of top 8 encoders, set via setter
        self._device_component = None  # ShiftableDeviceComponent for lock-to-device
        self._ramp_encoder_listeners = []  # active listeners during ramp edit
        # Ramp interpolation state
        self._ramp_active = False  # True during active ramp interpolation
        self._ramp_start_values = []  # macro values at ramp start
        self._ramp_target_values = []  # macro values to ramp toward
        self._ramp_ticks_total = 0  # total ticks for ramp duration
        self._ramp_ticks_remaining = 0  # countdown
        self._ramp_device = None  # device being ramped
        self._ramp_macros = None  # cached macro parameter list during ramp
        self._register_timer_callback(self._on_ramp_timer)
        return None

    def disconnect(self):
        self._exit_ramp_edit()
        self._ramp_active = False
        self._unregister_timer_callback(self._on_ramp_timer)
        self._ramp_encoders = None
        CustomTransportComponent.disconnect(self)
        if self._shift_button != None:
            self._shift_button.remove_value_listener(self._shift_value)
            self._shift_button = None
        if self._quant_toggle_button != None:
            self._quant_toggle_button.remove_value_listener(self._quant_toggle_value)
            self._quant_toggle_button = None
        self.song().remove_midi_recording_quantization_listener(self._on_quantisation_changed)
        if (self._undo_button != None):
            self._undo_button.remove_value_listener(self._undo_value)
            self._undo_button = None
        if (self._redo_button != None):
            self._redo_button.remove_value_listener(self._redo_value)
            self._redo_button = None
        if (self._bts_button != None):
            self._bts_button.remove_value_listener(self._bts_value)
            self._bts_button = None
        if (self._tempo_encoder_control != None):
            self._tempo_encoder_control.remove_value_listener(self._tempo_encoder_value)
            self._tempo_encoder_control = None
        return None

    def set_ramp_encoders(self, encoders):
        self._ramp_encoders = encoders

    def set_device_component(self, device_component):
        self._device_component = device_component

    def set_shift_button(self, button):
        if not(button == None or isinstance(button, ButtonElement) and button.is_momentary()):
            isinstance(button, ButtonElement)
            raise AssertionError
        if self._shift_button != button:
            if self._shift_button != None:
                self._shift_button.remove_value_listener(self._shift_value)
            self._shift_button = button
            if self._shift_button != None:
                self._shift_button.add_value_listener(self._shift_value)
            self.update()
        return None

    def set_quant_toggle_button(self, button):
        if not(button == None or isinstance(button, ButtonElement) and button.is_momentary()):
            isinstance(button, ButtonElement)
            raise AssertionError
        if self._quant_toggle_button != button:
            if self._quant_toggle_button != None:
                self._quant_toggle_button.remove_value_listener(self._quant_toggle_value)
            self._quant_toggle_button = button
            if self._quant_toggle_button != None:
                self._quant_toggle_button.add_value_listener(self._quant_toggle_value)
            self.update()
        return None

    def update(self):
        self._on_metronome_changed()
        self._on_overdub_changed()
        self._on_quantisation_changed()
        self._on_nudge_up_changed() 
        self._on_nudge_down_changed 

    def _shift_value(self, value):
        if not self._shift_button != None:
            raise AssertionError
        if not value in range(128):
            raise AssertionError
        self._shift_pressed = value != 0
        if self.is_enabled():
            self.is_enabled()
            self.update()
        else:
            self.is_enabled()
        return None

    def _metronome_value(self, value):
        if not self._shift_pressed:
            CustomTransportComponent._metronome_value(self, value)


    def _overdub_value(self, value):
        if not self._shift_pressed:
            CustomTransportComponent._overdub_value(self, value)


    def _nudge_up_value(self, value):
        if self.is_enabled() and (value != 0):
            device = self.song().appointed_device
            if device is not None and hasattr(device, 'variation_count') and device.variation_count > 0:
                new_index = min(device.selected_variation_index + 1, device.variation_count - 1)
                device.selected_variation_index = new_index

    def _nudge_down_value(self, value):
        if not self.is_enabled() or value == 0:
            return
        if self._shift_pressed:
            # Shift+Nudge Back: toggle lock-to-device
            device = self.song().appointed_device
            if device is not None:
                self._device_component.set_lock_to_device(not self._device_component._locked_to_device, device)
        else:
            device = self.song().appointed_device
            if device is not None and hasattr(device, 'variation_count') and device.variation_count > 0:
                new_index = max(device.selected_variation_index - 1, 0)
                device.selected_variation_index = new_index

    def _tap_tempo_value(self, value):
        if not self.is_enabled():
            return
        if self._shift_pressed:
            if value != 0:
                # Shift+Tap Tempo press: enter ramp edit mode
                self._ramp_edit_touched = False
                self._enter_ramp_edit()
            else:
                # Shift+Tap Tempo release: save variation only if encoders weren't touched
                if not self._ramp_edit_touched:
                    device = self.song().appointed_device
                    if device is not None and hasattr(device, 'store_variation'):
                        device.store_variation()
                self._exit_ramp_edit()
        else:
            if value != 0:
                # Tap Tempo press: recall with ramp
                self._recall_with_ramp()


    def _quant_toggle_value(self, value):
        assert (self._quant_toggle_button != None)
        assert (value in range(128))
        assert (self._last_quant_value != Live.Song.RecordingQuantization.rec_q_no_q)
        if (self.is_enabled() and (not self._shift_pressed)):
            if ((value != 0) or (not self._quant_toggle_button.is_momentary())):
                quant_value = self.song().midi_recording_quantization
                if (quant_value != Live.Song.RecordingQuantization.rec_q_no_q):
                    self._last_quant_value = quant_value
                    self.song().midi_recording_quantization = Live.Song.RecordingQuantization.rec_q_no_q
                else:
                    self.song().midi_recording_quantization = self._last_quant_value


    def _on_metronome_changed(self):
        if not self._shift_pressed:
            CustomTransportComponent._on_metronome_changed(self)


    def _on_overdub_changed(self):
        if not self._shift_pressed:
            CustomTransportComponent._on_overdub_changed(self)


    def _on_nudge_up_changed(self): 
        if not self._shift_pressed:
            CustomTransportComponent._on_nudge_up_changed(self)


    def _on_nudge_down_changed(self): 
        if not self._shift_pressed:
            CustomTransportComponent._on_nudge_down_changed(self)


    def _on_quantisation_changed(self):
        if self.is_enabled():
            quant_value = self.song().midi_recording_quantization
            quant_on = (quant_value != Live.Song.RecordingQuantization.rec_q_no_q)
            if quant_on:
                self._last_quant_value = quant_value
            if ((not self._shift_pressed) and (self._quant_toggle_button != None)):
                if quant_on:
                    self._quant_toggle_button.turn_on()
                else:
                    self._quant_toggle_button.turn_off()

    """ from OpenLabs module SpecialCustomTransportComponent """
    
    def set_undo_button(self, undo_button):
        assert isinstance(undo_button, (ButtonElement,
                                        type(None)))
        if (undo_button != self._undo_button):
            if (self._undo_button != None):
                self._undo_button.remove_value_listener(self._undo_value)
            self._undo_button = undo_button
            if (self._undo_button != None):
                self._undo_button.add_value_listener(self._undo_value)
            self.update()



    def set_redo_button(self, redo_button):
        assert isinstance(redo_button, (ButtonElement,
                                        type(None)))
        if (redo_button != self._redo_button):
            if (self._redo_button != None):
                self._redo_button.remove_value_listener(self._redo_value)
            self._redo_button = redo_button
            if (self._redo_button != None):
                self._redo_button.add_value_listener(self._redo_value)
            self.update()


    def set_bts_button(self, bts_button): 
        assert isinstance(bts_button, (ButtonElement,
                                       type(None)))
        if (bts_button != self._bts_button):
            if (self._bts_button != None):
                self._bts_button.remove_value_listener(self._bts_value)
            self._bts_button = bts_button
            if (self._bts_button != None):
                self._bts_button.add_value_listener(self._bts_value)
            self.update()


    def _undo_value(self, value):
        if self._shift_pressed: 
            assert (self._undo_button != None)
            assert (value in range(128))
            if self.is_enabled():
                if ((value != 0) or (not self._undo_button.is_momentary())):
                    if self.song().can_undo:
                        self.song().undo()


    def _redo_value(self, value):
        if self._shift_pressed: 
            assert (self._redo_button != None)
            assert (value in range(128))
            if self.is_enabled():
                if ((value != 0) or (not self._redo_button.is_momentary())):
                    if self.song().can_redo:
                        self.song().redo()


    def _bts_value(self, value):
        assert (self._bts_button != None)
        assert (value in range(128))
        if self.is_enabled():
            if ((value != 0) or (not self._bts_button.is_momentary())):
                self.song().current_song_time = 0.0
     
        
    # --- Ramp edit mode (Shift+Tap Tempo held) ---

    def _enter_ramp_edit(self):
        if self._ramp_edit_active:
            return
        self._ramp_edit_active = True
        if self._ramp_encoders is not None and len(self._ramp_encoders) >= 2:
            # Temporarily listen to encoder 1 (ms) and encoder 2 (beats)
            enc_ms = self._ramp_encoders[0]
            enc_beats = self._ramp_encoders[1]
            enc_ms.add_value_listener(self._ramp_ms_encoder_value)
            enc_beats.add_value_listener(self._ramp_beats_encoder_value)
            self._ramp_encoder_listeners = [enc_ms, enc_beats]
        self._show_ramp_status()

    def _exit_ramp_edit(self):
        if not self._ramp_edit_active:
            return
        self._ramp_edit_active = False
        for enc in self._ramp_encoder_listeners:
            if enc is not None:
                try:
                    enc.remove_value_listener(self._ramp_ms_encoder_value)
                except:
                    pass
                try:
                    enc.remove_value_listener(self._ramp_beats_encoder_value)
                except:
                    pass
        self._ramp_encoder_listeners = []

    def _ramp_ms_encoder_value(self, value):
        self._ramp_edit_touched = True
        # Absolute encoder: 0-127 maps to 0-10000ms
        self._ramp_ms = int((value / 127.0) * 10000)
        self._ramp_mode = 'ms'
        self._show_ramp_status()

    def _ramp_beats_encoder_value(self, value):
        self._ramp_edit_touched = True
        # Absolute encoder: 0-127 maps to beat sync index (-1 to 7)
        # -1 = off, 0-7 = BEAT_SYNC_VALUES entries
        num_steps = len(BEAT_SYNC_VALUES)  # 8
        new_index = int((value / 127.0) * num_steps) - 1
        new_index = max(-1, min(num_steps - 1, new_index))
        self._ramp_beat_index = new_index
        self._ramp_mode = 'beats'
        self._show_ramp_status()

    def _show_ramp_status(self):
        if self._ramp_mode == 'beats' and self._ramp_beat_index >= 0:
            label = BEAT_SYNC_LABELS[self._ramp_beat_index]
            self._show_msg_callback('Ramp: ' + label)
        else:
            self._show_msg_callback('Ramp: ' + str(self._ramp_ms) + 'ms')

    # --- Ramped variation recall ---

    def _get_ramp_duration_ms(self):
        if self._ramp_mode == 'beats' and self._ramp_beat_index >= 0:
            # Convert beats to ms using current tempo
            beats = BEAT_SYNC_VALUES[self._ramp_beat_index]
            bpm = self.song().tempo
            ms_per_beat = 60000.0 / bpm
            return beats * ms_per_beat
        return float(self._ramp_ms)

    def _get_macro_parameters(self, device):
        # Rack device parameters: index 0 = Device On, indices 1+ = macros
        # Use all parameters except Device On — works regardless of user-renamed macros
        if device is not None and hasattr(device, 'visible_macro_count'):
            count = device.visible_macro_count
            if count > 0:
                return list(device.parameters[1:count + 1])
        return []

    def _recall_with_ramp(self):
        device = self.song().appointed_device
        if device is None or not hasattr(device, 'recall_selected_variation'):
            return
        if not hasattr(device, 'variation_count') or device.variation_count == 0:
            return

        ramp_ms = self._get_ramp_duration_ms()
        if ramp_ms <= 0:
            # Instant recall
            device.recall_selected_variation()
            return

        macros = self._get_macro_parameters(device)
        if not macros:
            device.recall_selected_variation()
            return

        # Capture current values before recall
        start_values = [p.value for p in macros]

        # Recall to get target values
        device.recall_selected_variation()
        target_values = [p.value for p in macros]

        # Check if anything actually changed
        needs_ramp = False
        for i in range(len(start_values)):
            if abs(start_values[i] - target_values[i]) > 0.001:
                needs_ramp = True
                break
        if not needs_ramp:
            return

        # Restore start values — we'll interpolate from here
        for i, p in enumerate(macros):
            p.value = start_values[i]

        # Set up ramp interpolation
        self._ramp_device = device
        self._ramp_macros = macros
        self._ramp_start_values = start_values
        self._ramp_target_values = target_values
        ticks = max(1, int(ramp_ms / (RAMP_TIMER_INTERVAL * 1000)))
        self._ramp_ticks_total = ticks
        self._ramp_ticks_remaining = ticks
        self._ramp_active = True
        self._show_msg_callback('Ramping ' + str(int(ramp_ms)) + 'ms')

    def _on_ramp_timer(self):
        if not self._ramp_active:
            return
        if self._ramp_device is None or self._ramp_macros is None:
            self._ramp_active = False
            return

        self._ramp_ticks_remaining -= 1

        if self._ramp_ticks_remaining <= 0:
            # Final tick: set exact target values
            for i, p in enumerate(self._ramp_macros):
                if i < len(self._ramp_target_values):
                    p.value = self._ramp_target_values[i]
            self._ramp_active = False
            self._ramp_device = None
            self._ramp_macros = None
            return

        # Interpolate: linear ramp
        progress = 1.0 - (float(self._ramp_ticks_remaining) / float(self._ramp_ticks_total))
        for i, p in enumerate(self._ramp_macros):
            if i < len(self._ramp_start_values) and i < len(self._ramp_target_values):
                start = self._ramp_start_values[i]
                target = self._ramp_target_values[i]
                p.value = start + (target - start) * progress

    def _tempo_encoder_value(self, value):
        if self._shift_pressed:
            assert (self._tempo_encoder_control != None)
            assert (value in range(128))
            backwards = (value >= 64)
            step = 0.1 
            if backwards:
                amount = (value - 128)
            else:
                amount = value
            tempo = max(20, min(999, (self.song().tempo + (amount * step))))
            self.song().tempo = tempo

            
        
    def set_tempo_encoder(self, control):
        assert ((control == None) or (isinstance(control, EncoderElement) and (control.message_map_mode() == Live.MidiMap.MapMode.relative_two_compliment)))
        if (self._tempo_encoder_control != None):
            self._tempo_encoder_control.remove_value_listener(self._tempo_encoder_value)
        self._tempo_encoder_control = control
        if (self._tempo_encoder_control != None):
            self._tempo_encoder_control.add_value_listener(self._tempo_encoder_value)
        self.update()