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
        self._variations_store_button = None
        self._variations_appointed_listener_attached = False

        
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
    # row-major to variation indices 0..39; Track Stop col 0 stores a new
    # variation. Mirrors the variation API already used by Tap Tempo / Nudge
    # (see ShiftableTransportComponent.py:137-176, :359-415).

    def _set_variations_mode(self):
        self._session_zoom.set_zoom_button(None)
        self._session_zoom.set_enabled(False)
        # Detach clip-launch + clip-stop wiring so pads/stop-row are ours alone.
        for scene_index in range(5):
            scene = self._session.scene(scene_index)
            for track_index in range(8):
                clip_slot = scene.clip_slot(track_index)
                clip_slot.set_launch_button(None)
                button = self._matrix.get_button(track_index, scene_index)
                button.use_default_message()
                button.set_enabled(False)
                button.set_on_off_values(127, 0)
        self._session.set_stop_track_clip_buttons(None)
        for track_index in range(8):
            button = self._stop_button_matrix.get_button(track_index, 0)
            button.use_default_message()
            button.set_enabled(False)
            button.set_on_off_values(127, 0)

        # Cache flat pad list (row-major) and the store button, then attach
        # value listeners. Stop-row col 0 is "store"; cols 1..7 are inactive.
        pad_buttons = []
        for scene_index in range(5):
            for track_index in range(8):
                button = self._matrix.get_button(track_index, scene_index)
                pad_buttons.append(button)
        for button in pad_buttons:
            button.add_value_listener(self._variations_pad_value, identify_sender=True)
        self._variations_pad_buttons = pad_buttons

        store_button = self._stop_button_matrix.get_button(0, 0)
        store_button.add_value_listener(self._variations_store_value, identify_sender=True)
        self._variations_store_button = store_button

        # Listen for appointed-device changes so LEDs reflect the current Rack.
        # Guarded by hasattr — the API is present on Live 9+, but we stay safe.
        song = self.song()
        if hasattr(song, 'add_appointed_device_changed_listener') and not self._variations_appointed_listener_attached:
            try:
                song.add_appointed_device_changed_listener(self._variations_on_appointed_device_changed)
                self._variations_appointed_listener_attached = True
            except Exception:
                self._variations_appointed_listener_attached = False

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
        if self._variations_store_button is not None:
            try:
                self._variations_store_button.remove_value_listener(self._variations_store_value)
            except Exception:
                pass
            try:
                self._variations_store_button.send_value(0, True)
            except Exception:
                pass
            self._variations_store_button = None
        if self._variations_appointed_listener_attached:
            song = self.song()
            if hasattr(song, 'remove_appointed_device_changed_listener'):
                try:
                    song.remove_appointed_device_changed_listener(self._variations_on_appointed_device_changed)
                except Exception:
                    pass
            self._variations_appointed_listener_attached = False


    def _variations_on_appointed_device_changed(self):
        if self._mode_index == 7:
            self._refresh_variations_leds()


    def _refresh_variations_leds(self):
        if self._variations_pad_buttons is None:
            return
        device = self.song().appointed_device
        count = 0
        selected = -1
        rack_capable = False
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
            rack_capable = hasattr(device, 'store_variation')
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
        if self._variations_store_button is not None:
            store_color = 5 if rack_capable else 0  # yellow when Rack can store
            try:
                self._variations_store_button.set_on_off_values(store_color if store_color != 0 else 127, 0)
                self._variations_store_button.send_value(store_color, True)
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
        self._refresh_variations_leds()


    def _variations_store_value(self, value, sender):
        if not self.is_enabled() or value == 0:
            return
        device = self.song().appointed_device
        if device is None or not hasattr(device, 'store_variation'):
            return
        try:
            device.store_variation()
        except Exception:
            return
        self._refresh_variations_leds()


# local variables:
# tab-width: 4
