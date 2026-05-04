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
        self._variations_prev_count = 0  # last seen variation_count — used to detect "newly stored" so the new slot becomes selected
        # Global Variations Mode state (matrix mode 6) — per-track first-rack-with-variations cockpit.
        self._global_var_pad_buttons = None  # flat 5x8 list while active
        self._global_var_scene_buttons = None  # 5 scene-launch buttons while active
        self._global_var_bank_up_button = None
        self._global_var_bank_down_button = None
        self._global_var_bank_offset = 0
        self._global_var_track_racks = []  # 8 entries: (track, rack_or_None) per column
        self._global_var_listened_tracks = []
        self._global_var_listened_devices = []
        self._global_var_song_tracks_listener_attached = False
        self._global_var_song_visible_tracks_listener_attached = False

        
    def disconnect(self):
        self._teardown_global_variations_mode()
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
            # Tear down Variations / Global Variations Mode listeners before switching to any other mode,
            # so the pad/store callbacks don't outlive their slot.
            self._teardown_global_variations_mode()
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
                self._set_global_variations_mode()
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
        # NB: the Live API method is `add_appointed_device_listener` (no
        # `_changed_`), proven by EncoderDeviceComponent.py:50. The earlier
        # `_changed_` spelling silently failed the hasattr guard, leaving us
        # blind to device appointment changes (UAT 2026-05-04).
        song = self.song()
        if hasattr(song, 'add_appointed_device_listener') and not self._variations_appointed_listener_attached:
            try:
                song.add_appointed_device_listener(self._variations_on_appointed_device_changed)
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
            if hasattr(song, 'remove_appointed_device_listener'):
                try:
                    song.remove_appointed_device_listener(self._variations_on_appointed_device_changed)
                except Exception:
                    pass
            self._variations_appointed_listener_attached = False
        self._variations_prev_count = 0


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
            self._variations_prev_count = 0
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
        # Seed prev-count baseline so the first store after binding (or after
        # appointing a different rack) is correctly recognised as a growth.
        if hasattr(device, 'variation_count'):
            try:
                self._variations_prev_count = int(device.variation_count)
            except Exception:
                self._variations_prev_count = 0
        else:
            self._variations_prev_count = 0


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
        if self._mode_index != 7:
            return
        # Treat a growth in variation_count as "a new variation was just
        # stored" and force-select the newest slot. Live's store_variation()
        # does NOT auto-update selected_variation_index, so without this the
        # new pad would light green instead of red (UAT 2026-05-04).
        device = self.song().appointed_device
        if device is not None and hasattr(device, 'variation_count'):
            try:
                new_count = int(device.variation_count)
            except Exception:
                new_count = self._variations_prev_count
            if new_count > self._variations_prev_count and hasattr(device, 'selected_variation_index'):
                try:
                    device.selected_variation_index = new_count - 1
                except Exception:
                    pass
            self._variations_prev_count = new_count
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


    # --- Global Variations Mode (matrix slot 6) ------------------------------
    # Per-track variations cockpit: each grid column shows the variations of
    # the first device with variation_count > 0 on the visible track at that
    # column. Bank Select Up/Down scrolls all columns globally; Scene Launch
    # buttons fire one row across every column at once. Track Stop row keeps
    # its default clip-stop wiring. Storing a variation is still on
    # Shift+Tap Tempo (which acts on the appointed device — the user must
    # appoint the column's rack first via the blue-hand icon or
    # Shift+Nudge Back).

    def _set_global_variations_mode(self):
        self._parent.log_message('[GlobalVar] _set_global_variations_mode ENTRY')
        self._session_zoom.set_zoom_button(None)
        self._session_zoom.set_enabled(False)

        # Detach clip-launch wiring on the 5x8 grid; pads stay set_enabled(True)
        # so install_connections routes MIDI to my listener (lesson from 5j0:
        # set_enabled(False) silently breaks pad presses).
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
            button.add_value_listener(self._global_var_pad_value, identify_sender=True)
        self._global_var_pad_buttons = pad_buttons

        # Take over Scene Launch buttons. scene.set_launch_button(None) detaches
        # Live's clip-launch binding; we re-attach in teardown.
        scene_buttons = []
        for scene_index in range(5):
            scene = self._session.scene(scene_index)
            scene.set_launch_button(None)
            scene_button = self._parent._scene_launch_buttons[scene_index]
            scene_button.use_default_message()
            scene_button.set_enabled(True)
            scene_buttons.append(scene_button)
        for button in scene_buttons:
            button.add_value_listener(self._global_var_scene_value, identify_sender=True)
        self._global_var_scene_buttons = scene_buttons

        # Take over Bank Select Up/Down. Detach the session's scene-bank wiring
        # so the buttons no longer page scenes while in this mode.
        try:
            self._session.set_scene_bank_buttons(None, None)
        except Exception:
            pass
        up_button = self._parent._up_button
        down_button = self._parent._down_button
        up_button.use_default_message()
        up_button.set_enabled(True)
        down_button.use_default_message()
        down_button.set_enabled(True)
        up_button.add_value_listener(self._global_var_bank_up_value)
        down_button.add_value_listener(self._global_var_bank_down_value)
        self._global_var_bank_up_button = up_button
        self._global_var_bank_down_button = down_button

        self._global_var_bank_offset = 0

        # Song-level structural listeners — rescan when tracks are added/removed/reordered.
        song = self.song()
        if hasattr(song, 'add_tracks_listener') and not self._global_var_song_tracks_listener_attached:
            try:
                song.add_tracks_listener(self._global_var_on_song_tracks_changed)
                self._global_var_song_tracks_listener_attached = True
            except Exception:
                self._global_var_song_tracks_listener_attached = False
        if hasattr(song, 'add_visible_tracks_listener') and not self._global_var_song_visible_tracks_listener_attached:
            try:
                song.add_visible_tracks_listener(self._global_var_on_song_tracks_changed)
                self._global_var_song_visible_tracks_listener_attached = True
            except Exception:
                self._global_var_song_visible_tracks_listener_attached = False

        self._global_var_rebind_tracks()

        self._session.set_enabled(True)
        self._session.set_show_highlight(True)
        self._global_var_refresh_leds()


    def _teardown_global_variations_mode(self):
        if self._global_var_pad_buttons is not None:
            for button in self._global_var_pad_buttons:
                try:
                    button.remove_value_listener(self._global_var_pad_value)
                except Exception:
                    pass
                try:
                    button.send_value(0, True)
                except Exception:
                    pass
            self._global_var_pad_buttons = None
        if self._global_var_scene_buttons is not None:
            for button in self._global_var_scene_buttons:
                try:
                    button.remove_value_listener(self._global_var_scene_value)
                except Exception:
                    pass
                try:
                    button.send_value(0, True)
                except Exception:
                    pass
            # Restore Live's scene clip-launch binding so scenes fire normally
            # outside this mode (set_launch_button(None) is sticky until re-set).
            for scene_index in range(5):
                try:
                    scene = self._session.scene(scene_index)
                    scene.set_launch_button(self._parent._scene_launch_buttons[scene_index])
                except Exception:
                    pass
            self._global_var_scene_buttons = None
        if self._global_var_bank_up_button is not None:
            try:
                self._global_var_bank_up_button.remove_value_listener(self._global_var_bank_up_value)
            except Exception:
                pass
            self._global_var_bank_up_button = None
        if self._global_var_bank_down_button is not None:
            try:
                self._global_var_bank_down_button.remove_value_listener(self._global_var_bank_down_value)
            except Exception:
                pass
            self._global_var_bank_down_button = None
        # Restore the session's scene-bank wiring (down=down_button, up=up_button)
        # so subsequent modes get back their scene-paging behavior.
        try:
            self._session.set_scene_bank_buttons(self._parent._down_button, self._parent._up_button)
        except Exception:
            pass

        # Detach per-track + per-device listeners.
        for track in self._global_var_listened_tracks:
            if hasattr(track, 'remove_devices_listener'):
                try:
                    track.remove_devices_listener(self._global_var_on_track_devices_changed)
                except Exception:
                    pass
        self._global_var_listened_tracks = []
        for device in self._global_var_listened_devices:
            if hasattr(device, 'remove_variation_count_listener'):
                try:
                    device.remove_variation_count_listener(self._global_var_refresh_leds)
                except Exception:
                    pass
            if hasattr(device, 'remove_selected_variation_index_listener'):
                try:
                    device.remove_selected_variation_index_listener(self._global_var_refresh_leds)
                except Exception:
                    pass
        self._global_var_listened_devices = []

        # Detach song-level listeners.
        song = self.song()
        if self._global_var_song_tracks_listener_attached and hasattr(song, 'remove_tracks_listener'):
            try:
                song.remove_tracks_listener(self._global_var_on_song_tracks_changed)
            except Exception:
                pass
            self._global_var_song_tracks_listener_attached = False
        if self._global_var_song_visible_tracks_listener_attached and hasattr(song, 'remove_visible_tracks_listener'):
            try:
                song.remove_visible_tracks_listener(self._global_var_on_song_tracks_changed)
            except Exception:
                pass
            self._global_var_song_visible_tracks_listener_attached = False

        self._global_var_track_racks = []
        self._global_var_bank_offset = 0


    def _global_var_rebind_tracks(self):
        # Detach existing per-track + per-device listeners before reseating.
        for track in self._global_var_listened_tracks:
            if hasattr(track, 'remove_devices_listener'):
                try:
                    track.remove_devices_listener(self._global_var_on_track_devices_changed)
                except Exception:
                    pass
        self._global_var_listened_tracks = []
        for device in self._global_var_listened_devices:
            if hasattr(device, 'remove_variation_count_listener'):
                try:
                    device.remove_variation_count_listener(self._global_var_refresh_leds)
                except Exception:
                    pass
            if hasattr(device, 'remove_selected_variation_index_listener'):
                try:
                    device.remove_selected_variation_index_listener(self._global_var_refresh_leds)
                except Exception:
                    pass
        self._global_var_listened_devices = []

        # Resolve the 8 visible tracks via song.visible_tracks + session.track_offset()
        # — the proven pattern from SpecialMixerComponent.py:46-47. The earlier
        # clip_slot.canonical_parent route returned the SCENE on this Live build
        # (Scenes have no `devices` attribute), so every column resolved to a
        # rack-less track and the grid stayed dark (UAT 2026-05-04).
        song = self.song()
        visible = []
        offset = 0
        try:
            visible = list(song.visible_tracks)
        except Exception as e:
            self._parent.log_message('[GlobalVar] visible_tracks failed: ' + str(e))
        try:
            offset = int(self._session.track_offset())
        except Exception as e:
            self._parent.log_message('[GlobalVar] track_offset() failed: ' + str(e))
        self._parent.log_message('[GlobalVar] rebind: visible=' + str(len(visible)) + ' offset=' + str(offset))
        tracks = []
        for track_index in range(8):
            idx = offset + track_index
            if 0 <= idx < len(visible):
                track = visible[idx]
                # Defensive: only accept objects exposing a devices list.
                if not hasattr(track, 'devices'):
                    self._parent.log_message('[GlobalVar] col=' + str(track_index) + ' track has no devices attr; type=' + str(type(track).__name__))
                    track = None
            else:
                track = None
            tracks.append(track)

        # For each visible track: hook devices_listener; pick first rack with variation_count > 0.
        racks = []
        for col_idx, track in enumerate(tracks):
            rack = None
            if track is not None:
                if hasattr(track, 'add_devices_listener'):
                    try:
                        track.add_devices_listener(self._global_var_on_track_devices_changed)
                        self._global_var_listened_tracks.append(track)
                    except Exception:
                        pass
                try:
                    devices = list(track.devices)
                except Exception as e:
                    self._parent.log_message('[GlobalVar] col=' + str(col_idx) + ' track.devices failed: ' + str(e))
                    devices = []
                self._parent.log_message('[GlobalVar] col=' + str(col_idx) + ' devices=' + str(len(devices)))
                for device in devices:
                    has_attr = hasattr(device, 'variation_count')
                    vc = -1
                    if has_attr:
                        try:
                            vc = int(device.variation_count)
                        except Exception as e:
                            self._parent.log_message('[GlobalVar] col=' + str(col_idx) + ' variation_count read failed: ' + str(e))
                    self._parent.log_message('[GlobalVar] col=' + str(col_idx) + ' device=' + str(getattr(device, 'name', '?')) + ' has_var_count=' + str(has_attr) + ' count=' + str(vc))
                    if has_attr and vc > 0:
                        rack = device
                        break
            self._parent.log_message('[GlobalVar] col=' + str(col_idx) + ' rack=' + ('NONE' if rack is None else getattr(rack, 'name', '?')))
            racks.append((track, rack))
            if rack is not None:
                if hasattr(rack, 'add_variation_count_listener'):
                    try:
                        rack.add_variation_count_listener(self._global_var_refresh_leds)
                    except Exception:
                        pass
                if hasattr(rack, 'add_selected_variation_index_listener'):
                    try:
                        rack.add_selected_variation_index_listener(self._global_var_refresh_leds)
                    except Exception:
                        pass
                self._global_var_listened_devices.append(rack)
        self._global_var_track_racks = racks


    def _global_var_on_song_tracks_changed(self):
        if self._mode_index != 6:
            return
        self._global_var_rebind_tracks()
        self._global_var_refresh_leds()


    def _global_var_on_track_devices_changed(self):
        if self._mode_index != 6:
            return
        self._global_var_rebind_tracks()
        self._global_var_refresh_leds()


    def _global_var_refresh_leds(self):
        if self._global_var_pad_buttons is None:
            self._parent.log_message('[GlobalVar] refresh_leds: pad_buttons is None — abort')
            return
        self._parent.log_message('[GlobalVar] refresh_leds: racks=' + str([('NONE' if r is None else getattr(r, 'name', '?')) for (_t, r) in self._global_var_track_racks]))
        # Pads
        for col in range(8):
            track, rack = self._global_var_track_racks[col] if col < len(self._global_var_track_racks) else (None, None)
            count = 0
            selected = -1
            if rack is not None:
                if hasattr(rack, 'variation_count'):
                    try:
                        count = int(rack.variation_count)
                    except Exception:
                        count = 0
                if hasattr(rack, 'selected_variation_index'):
                    try:
                        selected = int(rack.selected_variation_index)
                    except Exception:
                        selected = -1
            for row in range(5):
                pad_index = row * 8 + col
                variation_index = self._global_var_bank_offset + row
                if rack is None:
                    color = 0
                elif variation_index == selected and 0 <= selected < count:
                    color = 3  # red
                elif variation_index < count:
                    color = 1  # green
                else:
                    color = 0
                button = self._global_var_pad_buttons[pad_index]
                try:
                    button.set_on_off_values(color if color != 0 else 127, 0)
                    button.send_value(color, True)
                except Exception:
                    pass
        # Scene Launch row — green if at least one column has a stored variation at that row.
        if self._global_var_scene_buttons is not None:
            for row in range(5):
                variation_index = self._global_var_bank_offset + row
                any_stored = False
                for (_track, rack) in self._global_var_track_racks:
                    if rack is None or not hasattr(rack, 'variation_count'):
                        continue
                    try:
                        if int(rack.variation_count) > variation_index:
                            any_stored = True
                            break
                    except Exception:
                        continue
                color = 1 if any_stored else 0
                button = self._global_var_scene_buttons[row]
                try:
                    button.set_on_off_values(color if color != 0 else 127, 0)
                    button.send_value(color, True)
                except Exception:
                    pass


    def _global_var_pad_value(self, value, sender):
        if not self.is_enabled() or value == 0:
            return
        if self._global_var_pad_buttons is None:
            return
        try:
            pad_index = self._global_var_pad_buttons.index(sender)
        except ValueError:
            return
        col = pad_index % 8
        row = pad_index // 8
        if col >= len(self._global_var_track_racks):
            return
        track, rack = self._global_var_track_racks[col]
        if rack is None or not hasattr(rack, 'variation_count'):
            return
        try:
            count = int(rack.variation_count)
        except Exception:
            return
        variation_index = self._global_var_bank_offset + row
        if variation_index >= count:
            return  # empty slot
        try:
            rack.selected_variation_index = variation_index
            if hasattr(rack, 'recall_selected_variation'):
                rack.recall_selected_variation()
        except Exception:
            return
        # Synchronous repaint — same belt+listener strategy as 260504-5j0.
        self._global_var_refresh_leds()


    def _global_var_scene_value(self, value, sender):
        if not self.is_enabled() or value == 0:
            return
        if self._global_var_scene_buttons is None:
            return
        try:
            scene_index = self._global_var_scene_buttons.index(sender)
        except ValueError:
            return
        variation_index = self._global_var_bank_offset + scene_index
        for (_track, rack) in self._global_var_track_racks:
            if rack is None or not hasattr(rack, 'variation_count'):
                continue
            try:
                if int(rack.variation_count) <= variation_index:
                    continue
            except Exception:
                continue
            try:
                rack.selected_variation_index = variation_index
                if hasattr(rack, 'recall_selected_variation'):
                    rack.recall_selected_variation()
            except Exception:
                continue
        self._global_var_refresh_leds()


    def _global_var_bank_up_value(self, value):
        if not self.is_enabled() or value == 0:
            return
        if self._global_var_bank_offset > 0:
            self._global_var_bank_offset -= 1
            self._global_var_refresh_leds()


    def _global_var_bank_down_value(self, value):
        if not self.is_enabled() or value == 0:
            return
        self._global_var_bank_offset += 1
        self._global_var_refresh_leds()


# local variables:
# tab-width: 4
