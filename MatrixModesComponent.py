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
# -*- coding: utf-8 -*-

from _Framework.ModeSelectorComponent import ModeSelectorComponent 
from _Framework.ButtonElement import ButtonElement 
from _Framework.MixerComponent import MixerComponent 
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ControlSurface import ControlSurface
from .Matrix_Maps import *

class MatrixModesComponent(ModeSelectorComponent):
    ' SelectorComponent that assigns matrix to different functions '
    __module__ = __name__

    def __init__(self, matrix, session, zooming, stop_buttons, parent):
        assert isinstance(matrix, ButtonMatrixElement)
        ModeSelectorComponent.__init__(self)
        self._controls = None
        self._session = session
        self._session_zoom = zooming
        self._matrix = matrix
        self._track_stop_buttons = stop_buttons
        self._stop_button_matrix = ButtonMatrixElement() #new dummy matrix for stop buttons, to allow note mode/user mode switching
        button_row = []
        for track_index in range(8):
            button = self._track_stop_buttons[track_index]
            button_row.append(button)
        self._stop_button_matrix.add_row(tuple(button_row))
        self._mode_index = 0
        self._last_mode = 0
        self._parent = parent
        self._parent.set_pad_translations(PAD_TRANSLATIONS) #comment out to remove Drum Rack mapping
        # Variations Mode state (matrix mode 7) — Rack macro variation pads.
        self._variations_pad_buttons = None
        self._variations_appointed_listener_attached = False
        self._variations_listened_device = None  # device we currently have variation_count/selected_variation_index listeners on

        
    def disconnect(self):
        self._teardown_variations_mode()
        for button in self._modes_buttons:
            button.remove_value_listener(self._mode_value)
        self._controls = None
        self._session = None
        self._session_zoom = None
        self._matrix = None
        self._track_stop_buttons = None
        self._stop_button_matrix = None
        ModeSelectorComponent.disconnect(self)

        
    def set_mode(self, mode): #override ModeSelectorComponent set_mode, to avoid flickers
        assert isinstance(mode, int)
        assert (mode in range(self.number_of_modes()))
        if (self._mode_index != mode):
            self._last_mode = 0 # self._mode_index # keep track of previous mode, to allow refresh after Note Mode only
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
            for index in range(len(self._modes_buttons)):
                if (index == self._mode_index):
                    self._modes_buttons[index].turn_on()
                else:
                    self._modes_buttons[index].turn_off()


    def _mode_value(self, value, sender):
        assert (len(self._modes_buttons) > 0)
        assert isinstance(value, int)
        assert isinstance(sender, ButtonElement)
        assert (self._modes_buttons.count(sender) == 1)
        if self.is_enabled():
            if ((value != 0) or (not sender.is_momentary())):
                self.set_mode(self._modes_buttons.index(sender))                    

    def number_of_modes(self):
        return 8
    
    def update(self):
        pass

    def get_mode_index_value(self):
        return self._mode_index
    
    def _set_modes(self):
        if self.is_enabled():
            # Tear down Variations Mode listeners before switching to any other mode,
            # so the pad/store callbacks don't outlive their slot.
            self._teardown_variations_mode()
            self._session.set_allow_update(False)
            self._session_zoom.set_allow_update(False)
            assert (self._mode_index in range(self.number_of_modes()))
            for index in range(len(self._modes_buttons)):
                if (index == self._mode_index):
                    self._modes_buttons[index].turn_on()
                else:
                    self._modes_buttons[index].turn_off()
            self._session.set_stop_track_clip_buttons(tuple(self._track_stop_buttons))            
            for track_index in range(8):
                button = self._track_stop_buttons[track_index]
                button.use_default_message()
                button.set_enabled(True)
                button.set_force_next_value()
                button.send_value(0)
            self._session_zoom.set_enabled(True)
            self._session.set_enabled(True)
            self._session.set_show_highlight(True)
            self._session_zoom.set_zoom_button(self._parent._shift_button)
            for scene_index in range(5):
                scene = self._session.scene(scene_index) 
                for track_index in range(8):                
                    button = self._matrix.get_button(track_index, scene_index)
                    button.use_default_message()
                    clip_slot = scene.clip_slot(track_index)
                    clip_slot.set_launch_button(button)
                    button.set_enabled(True)
                
            if (self._mode_index == 0): #Clip Launch
                self._session_zoom._on_zoom_value(1) #zoom out

                        
            elif (self._mode_index == 1): #Session Overview
                self._session_zoom.set_zoom_button(None)
                self._session_zoom.set_enabled(True)
                self._session_zoom._is_zoomed_out = True
                self._session_zoom._scene_bank_index = int(((self._session_zoom._session.scene_offset() / self._session_zoom._session.height()) / self._session_zoom._buttons.height()))               
                self._session.set_enabled(False)
                self._session_zoom.update()

    
            elif (self._mode_index == 2):
                self._set_note_mode(PATTERN_1, CHANNEL_1, NOTEMAP_1, USE_STOP_ROW_1, IS_NOTE_MODE_1)
            elif (self._mode_index == 3):
                self._set_note_mode(PATTERN_2, CHANNEL_2, NOTEMAP_2, USE_STOP_ROW_2, IS_NOTE_MODE_2)
            elif (self._mode_index == 4):
                self._set_note_mode(PATTERN_3, CHANNEL_3, NOTEMAP_3, USE_STOP_ROW_3, IS_NOTE_MODE_3)
            elif (self._mode_index == 5):
                self._set_note_mode(PATTERN_4, CHANNEL_4, NOTEMAP_4, USE_STOP_ROW_4, IS_NOTE_MODE_4)
            elif (self._mode_index == 6):
                self._set_note_mode(PATTERN_5, CHANNEL_5, NOTEMAP_5, USE_STOP_ROW_5, IS_NOTE_MODE_5)
            elif (self._mode_index == 7):
                self._set_variations_mode()
            else:
                pass
            self._session.set_allow_update(True)
            self._session_zoom.set_allow_update(True)
            #self._rebuild_callback()


    def _set_note_mode(self, pattern, channel, notemap, use_stop_row = False, is_note_mode = True):
        self._session_zoom.set_zoom_button(None)
        self._session_zoom.set_enabled(False)
        for scene_index in range(5):
            scene = self._session.scene(scene_index) 
            for track_index in range(8):
                clip_slot = scene.clip_slot(track_index)
                button = self._matrix.get_button(track_index, scene_index)
                clip_slot.set_launch_button(None)
                button.set_channel(channel) #remap all Note Mode notes to new channel
                button.set_identifier(notemap[scene_index][track_index])
                button.set_on_off_values(pattern[scene_index][track_index], 0)
                button.set_force_next_value()
                button.turn_on()
                if is_note_mode == True:
                    button.set_enabled(False)
        if use_stop_row == True:
            self._session.set_stop_track_clip_buttons(None)
            for track_index in range(8):
                button = self._stop_button_matrix.get_button(track_index, 0)
                button.set_channel(channel) #remap all Note Mode notes to new channel
                button.set_identifier(notemap[5][track_index])
                button.set_force_next_value()
                button.send_value(pattern[5][track_index])
                if is_note_mode == True:
                    button.set_enabled(False)
        else:
            for track_index in range(8):
                button = self._stop_button_matrix.get_button(track_index, 0)
                button.send_value(0, True)
        self._session.set_enabled(True)
        self._session.set_show_highlight(True)


    # --- Variations Mode (matrix slot 7) -------------------------------------
    # Rack macro variation pads on the appointed device. 5x8 main grid maps
    # row-major to variation indices 0..39 — green = stored, red = currently
    # selected, off = empty slot. Press a stored pad to set
    # selected_variation_index and recall instantly. The Track Stop row keeps
    # its default clip-stop function (no store button — store is on
    # Shift+Tap Tempo, see ShiftableTransportComponent.py:158-176).
    # Live API: variation_count / selected_variation_index / recall_selected_variation()
    # mirror the existing Tap-Tempo/Nudge handlers.

    def _set_variations_mode(self):
        self._session_zoom.set_zoom_button(None)
        self._session_zoom.set_enabled(False)
        # Detach clip-launch wiring so pads only fire OUR listener. Buttons
        # stay set_enabled(True) so the framework still routes incoming MIDI
        # to listeners — see ConfigurableButtonElement.install_connections.
        # Track Stop row is left at its default clip-stop wiring (set up
        # earlier in _set_modes); the Variations Mode does not own it.
        pad_buttons = []
        for scene_index in range(5):
            scene = self._session.scene(scene_index)
            for track_index in range(8):
                clip_slot = scene.clip_slot(track_index)
                clip_slot.set_launch_button(None)
                button = self._matrix.get_button(track_index, scene_index)
                button.use_default_message()
                button.set_enabled(True)
                pad_buttons.append(button)
        for button in pad_buttons:
            button.add_value_listener(self._variations_pad_value, identify_sender=True)
        self._variations_pad_buttons = pad_buttons

        # Live API listeners — keep LEDs in sync with real-time Live state.
        song = self.song()
        if hasattr(song, 'add_appointed_device_changed_listener') and not self._variations_appointed_listener_attached:
            try:
                song.add_appointed_device_changed_listener(self._variations_on_appointed_device_changed)
                self._variations_appointed_listener_attached = True
            except Exception:
                self._variations_appointed_listener_attached = False
        self._variations_attach_device_listeners(song.appointed_device)

        self._session.set_enabled(True)
        self._session.set_show_highlight(True)
        self._refresh_variations_leds()


    def _teardown_variations_mode(self):
        if self._variations_pad_buttons is not None:
            for button in self._variations_pad_buttons:
                try:
                    button.remove_value_listener(self._variations_pad_value)
                except Exception:
                    pass
                try:
                    button.send_value(0, True)
                except Exception:
                    pass
            self._variations_pad_buttons = None
        self._variations_detach_device_listeners()
        if self._variations_appointed_listener_attached:
            song = self.song()
            if hasattr(song, 'remove_appointed_device_changed_listener'):
                try:
                    song.remove_appointed_device_changed_listener(self._variations_on_appointed_device_changed)
                except Exception:
                    pass
            self._variations_appointed_listener_attached = False


    def _variations_on_appointed_device_changed(self):
        if self._mode_index != 7:
            return
        # Re-bind variation listeners onto the new device, then repaint.
        self._variations_detach_device_listeners()
        self._variations_attach_device_listeners(self.song().appointed_device)
        self._refresh_variations_leds()


    def _variations_attach_device_listeners(self, device):
        # Hook variation_count + selected_variation_index so LEDs follow
        # Live-side changes (e.g. Shift+Tap Tempo store, Nudge step,
        # variations added in Live's UI). Guarded by hasattr — older Live
        # builds may not expose the listeners.
        if device is None:
            self._variations_listened_device = None
            return
        if hasattr(device, 'add_variation_count_listener'):
            try:
                device.add_variation_count_listener(self._variations_on_variation_count_changed)
            except Exception:
                pass
        if hasattr(device, 'add_selected_variation_index_listener'):
            try:
                device.add_selected_variation_index_listener(self._variations_on_selected_index_changed)
            except Exception:
                pass
        self._variations_listened_device = device


    def _variations_detach_device_listeners(self):
        device = self._variations_listened_device
        if device is None:
            return
        if hasattr(device, 'remove_variation_count_listener'):
            try:
                device.remove_variation_count_listener(self._variations_on_variation_count_changed)
            except Exception:
                pass
        if hasattr(device, 'remove_selected_variation_index_listener'):
            try:
                device.remove_selected_variation_index_listener(self._variations_on_selected_index_changed)
            except Exception:
                pass
        self._variations_listened_device = None


    def _variations_on_variation_count_changed(self):
        if self._mode_index == 7:
            self._refresh_variations_leds()


    def _variations_on_selected_index_changed(self):
        if self._mode_index == 7:
            self._refresh_variations_leds()


    def _refresh_variations_leds(self):
        if self._variations_pad_buttons is None:
            return
        device = self.song().appointed_device
        count = 0
        selected = -1
        if device is not None:
            if hasattr(device, 'variation_count'):
                try:
                    count = int(device.variation_count)
                except Exception:
                    count = 0
            if hasattr(device, 'selected_variation_index'):
                try:
                    selected = int(device.selected_variation_index)
                except Exception:
                    selected = -1
        for index, button in enumerate(self._variations_pad_buttons):
            if index == selected and 0 <= selected < count:
                color = 3  # red — currently selected
            elif index < count:
                color = 1  # green — stored slot
            else:
                color = 0  # off — empty slot
            try:
                button.set_on_off_values(color if color != 0 else 127, 0)
                button.send_value(color, True)
            except Exception:
                pass


    def _variations_pad_value(self, value, sender):
        if not self.is_enabled() or value == 0:
            return
        if self._variations_pad_buttons is None:
            return
        try:
            pad_index = self._variations_pad_buttons.index(sender)
        except ValueError:
            return
        device = self.song().appointed_device
        if device is None or not hasattr(device, 'variation_count'):
            return
        try:
            count = int(device.variation_count)
        except Exception:
            return
        if pad_index >= count:
            return  # empty slot — nothing to recall
        try:
            device.selected_variation_index = pad_index
            if hasattr(device, 'recall_selected_variation'):
                device.recall_selected_variation()
        except Exception:
            return
        # Explicit repaint — the selected_variation_index listener also fires,
        # but Live does not guarantee it has propagated by the time we return,
        # and a stuck-green pad (UAT 2026-05-04) showed the listener alone is
        # not enough. Belt + listener: the second paint inside the listener is
        # cheap (~48 LED writes).
        self._refresh_variations_leds()


# local variables:
# tab-width: 4
