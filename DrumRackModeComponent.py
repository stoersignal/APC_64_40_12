# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

"""
DrumRackModeComponent — auto-engaging Drum Rack overlay (quick-260504-m2x).

When the user selects a track whose first top-level device is a Live Drum
Rack (class_name 'DrumGroupDevice'), this component automatically captures
the 8 Track faders, 8 Mute / Solo buttons, the 8 Track Control encoders,
the Bank Select up/down buttons and the Stop All Clips LED, and retargets
them to drum-chain semantics:

  Surface section          Drum Rack Mode binding
  --------------------     -----------------------------------------
  8 Track faders           chain[i].mixer_device.volume
  8 Track Mute buttons     chain[i].mute  (v1.0 toggle/momentary)
  8 Track Solo buttons     chain[i].solo  (v1.0 toggle/momentary)
  8 Track Control encoders chain[i].mixer_device.{panning|sends[0..2]}
  Track Control mode btns  OBSERVED — selects encoder sub-mode
  Bank Select up/down      Scroll _chain_offset by 8 (when chains > 8)
  Stop All Clips           LED = mode-active; Shift+press = exit-this-track

Detection runs on every track-selection change; on a non-drum-rack track
the component is a fail-quiet passthrough — every captured-button value
listener returns immediately so the underlying components see normal
events. Per-track manual exit (Shift + Stop All Clips) is tracked in
_exited_tracks (set of track-id ints), pruned on track-list change.

Architectural twin: EncoderAutoFilterComponent (quick-260504-k6p). Same
shape — selection-driven, fail-quiet, one-shot diagnostic dump on first
activation, listener-add wraps every framework call in try/except.
"""

import Live
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.MixerComponent import MixerComponent

from .ToggleMomentaryChannelStripComponent import (
    handle_toggle_momentary_event,
    tick_state,
    LONG_PRESS_DELAY,
)


# Live 11+ ships drum racks as class_name 'DrumGroupDevice'. Tuple kept so
# a future Live build that bumps the suffix (DrumGroupDevice2, etc.) can be
# accommodated without rewriting the detection path.
DRUM_RACK_CLASS_NAMES = ('DrumGroupDevice',)

# Strip count is the APC40's fixed 8 mixer slots — also used as the
# chain-page step for Bank Select up/down scrolling.
NUM_STRIPS = 8


class _ChainSlotHandler(object):
    """Per-strip-slot wrapper around the v1.0 toggle/momentary press-timing
    helpers. Each instance owns two state dicts (mute + solo) and a chain
    reference; on each press/release/timer-tick it forwards to the module-
    level handle_toggle_momentary_event / tick_state pure functions in
    ToggleMomentaryChannelStripComponent.

    The chain reference is rebound by the parent on every chain-binding
    refresh — when a new chain becomes the slot's target, any in-flight
    momentary hold is dropped (we cannot meaningfully revert a chain that's
    no longer in the slot).
    """

    def __init__(self, parent):
        self._parent = parent
        self._chain = None
        self._mute_state = {'ticks': -1, 'before': False, 'momentary': False}
        self._solo_state = {'ticks': -1, 'before': False, 'momentary': False}

    def set_chain(self, chain):
        # If a momentary hold was active when the slot is rebound to a new
        # chain (e.g. user scrolls Bank Down mid-press), drop the hold —
        # the old chain has already been flipped at press-down so leaving
        # state['momentary'] True would never revert anything we can address.
        self._mute_state = {'ticks': -1, 'before': False, 'momentary': False}
        self._solo_state = {'ticks': -1, 'before': False, 'momentary': False}
        self._chain = chain

    def handle_mute(self, value, shift_pressed):
        if self._chain is None:
            return
        try:
            handle_toggle_momentary_event(
                value, self._chain, 'mute', self._mute_state,
                LONG_PRESS_DELAY, shift_pressed,
            )
        except Exception:
            # Live's chain.mute setter throws on dead refs (chain removed
            # mid-press). Fail quiet — the next press evaluates fresh.
            pass

    def handle_solo(self, value, shift_pressed):
        if self._chain is None:
            return
        try:
            handle_toggle_momentary_event(
                value, self._chain, 'solo', self._solo_state,
                LONG_PRESS_DELAY, shift_pressed,
            )
        except Exception:
            pass

    def tick(self):
        try:
            tick_state(self._mute_state)
            tick_state(self._solo_state)
        except Exception:
            pass

    def revert_holds(self):
        """Force any active momentary hold to revert. Called on disengage
        so the user doesn't leave the rack with a chain stuck muted/soloed
        because they were holding a button when they exited the mode."""
        try:
            if self._chain is not None and self._mute_state.get('momentary'):
                self._chain.mute = self._mute_state['before']
            if self._chain is not None and self._solo_state.get('momentary'):
                self._chain.solo = self._solo_state['before']
        except Exception:
            pass
        self._mute_state = {'ticks': -1, 'before': False, 'momentary': False}
        self._solo_state = {'ticks': -1, 'before': False, 'momentary': False}


class DrumRackModeComponent(ControlSurfaceComponent):
    """ Auto-engaging Drum Rack overlay over the APC40 mixer + encoder strip. """

    def __init__(self, parent, mixer, encoder_modes, session,
                 sliders, mute_buttons, solo_buttons,
                 encoders, encoder_mode_buttons,
                 bank_up_button, bank_down_button,
                 detail_view_button, shift_button):
        ControlSurfaceComponent.__init__(self)
        assert isinstance(mixer, MixerComponent)
        assert len(sliders) == NUM_STRIPS
        assert len(mute_buttons) == NUM_STRIPS
        assert len(solo_buttons) == NUM_STRIPS
        assert len(encoders) == NUM_STRIPS
        assert len(encoder_mode_buttons) == 4

        self._parent = parent
        self._mixer = mixer
        self._encoder_modes = encoder_modes
        # Session ref still needed for scene-bank ownership transfer when
        # chains > NUM_STRIPS (otherwise session's set_scene_bank_buttons
        # listener fights ours). Stop-All-Clips LED ownership is no longer
        # touched — that LED is hardware-only on APC40 mk1 firmware (UAT
        # confirmed it never lights even when clips play normally), so the
        # indicator was moved to the Detail View button (which has a
        # MIDI-addressable LED).
        self._session = session
        self._sliders = tuple(sliders)
        self._mute_buttons = tuple(mute_buttons)
        self._solo_buttons = tuple(solo_buttons)
        self._encoders = tuple(encoders)
        self._encoder_mode_buttons = tuple(encoder_mode_buttons)
        self._bank_up_button = bank_up_button
        self._bank_down_button = bank_down_button
        # Indicator + manual-exit combo migrated from Stop All Clips to
        # Shift + Detail View (note 62, channel 0 — self._device_bank_buttons[4]).
        # DetailViewCntrlComponent normally drives this LED based on Live's
        # Detail-view-visible state, but only on visibility change events —
        # our _on_timer tick re-asserts every Live MIDI loop, so we always
        # win the race while the mode is active.
        self._detail_view_button = detail_view_button
        self._shift_button = shift_button

        # Mode state.
        self._active = False
        self._drum_rack = None
        self._chain_offset = 0
        self._exited_tracks = set()    # set of id(track) ints
        self._shift_pressed = False
        self._diag_logged = False

        # Per-slot mute/solo state machines.
        self._slot_handlers = [_ChainSlotHandler(self) for _ in range(NUM_STRIPS)]

        # Listener bookkeeping. Each entry on a list is removed in disconnect.
        self._slider_listeners = []         # (slider, callback)
        self._mute_listeners = []           # (button, callback)
        self._solo_listeners = []           # (button, callback)
        # LED-feedback listeners on chain.mute / chain.solo so the per-slot
        # Mute/Solo button LEDs follow chain state. The buttons' default
        # SpecialChanStripComponent LED feeding is suppressed when we call
        # strip.set_mute_button(None) on _engage — without our own listeners
        # the LEDs stay dark even though the toggle/momentary handler works.
        self._chain_mute_listeners = []     # (chain, callback)
        self._chain_solo_listeners = []     # (chain, callback)
        self._encoder_mode_listeners = []   # (button, callback)
        self._chains_listener_rack = None   # drum_rack (we attached a chains listener to)
        self._track_selection_listener_song = None  # song().view (we attached to)
        self._track_list_listener_song = None       # song() (we attached to)
        # True while we're holding scene-nav ownership away from session.
        self._scene_nav_taken = False

        # Add cross-cutting listeners that are active in all states. These
        # are passthroughs unless _active and _shift_pressed.
        self._attach_static_listeners()

        # Register timer callback to drive ChainSlotHandler ticks at v1.0 cadence.
        try:
            self._register_timer_callback(self._on_timer)
        except Exception:
            pass

    # ---------- ControlSurfaceComponent overrides --------------------------

    def disconnect(self):
        # Disengage any active capture; revert in-flight momentary holds.
        if self._active:
            for h in self._slot_handlers:
                h.revert_holds()
            try:
                self._disengage()
            except Exception:
                pass

        # Static listeners.
        self._detach_static_listeners()

        # Selection / track-list listeners.
        try:
            if self._track_selection_listener_song is not None:
                self._track_selection_listener_song.remove_selected_track_listener(
                    self._on_selected_track_changed_listener)
        except Exception:
            pass
        self._track_selection_listener_song = None
        try:
            if self._track_list_listener_song is not None:
                self._track_list_listener_song.remove_tracks_listener(
                    self._on_tracks_changed_listener)
        except Exception:
            pass
        self._track_list_listener_song = None

        # Timer callback.
        try:
            self._unregister_timer_callback(self._on_timer)
        except Exception:
            pass

        # Drop refs.
        self._slot_handlers = []
        self._parent = None
        self._mixer = None
        self._encoder_modes = None
        self._sliders = ()
        self._mute_buttons = ()
        self._solo_buttons = ()
        self._encoders = ()
        self._encoder_mode_buttons = ()
        self._bank_up_button = None
        self._bank_down_button = None
        self._detail_view_button = None
        self._shift_button = None
        self._drum_rack = None

    def update(self):
        pass

    def on_enabled_changed(self):
        # Re-evaluate engagement whenever framework toggles enabled state.
        if self.is_enabled():
            self._evaluate_selection()
        else:
            if self._active:
                try:
                    self._disengage()
                except Exception:
                    pass

    def on_track_list_changed(self):
        # Prune dead track ids from _exited_tracks. Ableton recycles ids
        # within a session, so a stale id could spuriously block re-engage
        # on a brand-new track. Defence: keep the set tight.
        try:
            live_ids = set()
            for tr in self.song().tracks:
                live_ids.add(id(tr))
            for tr in self.song().return_tracks:
                live_ids.add(id(tr))
            self._exited_tracks = self._exited_tracks & live_ids
        except Exception:
            pass
        # Selected track may have been replaced.
        self._evaluate_selection()

    def on_selected_track_changed(self):
        self._evaluate_selection()

    # ---------- Public for parent script's initial bootstrap --------------

    def trigger_initial_evaluation(self):
        """Called from APC_64_40_9._setup_global_control end so the script
        enters Drum Rack Mode immediately on script-load if Live boots with
        a drum-rack track already selected. Idempotent."""
        self._evaluate_selection()

    # ---------- Static listeners (always attached) ------------------------

    def _attach_static_listeners(self):
        # Detail View button: passthrough listener — co-exists with the
        # existing DetailViewCntrlComponent.set_detail_toggle_button binding
        # (DetailViewCntrlComponent gates on `not self._shift_pressed`, so
        # Shift+DetailView is free for our exit combo). Only fires its
        # exit-this-track action when (_active AND _shift_pressed).
        try:
            if self._detail_view_button is not None:
                self._detail_view_button.add_value_listener(self._detail_view_value)
        except Exception:
            pass

        # Bank Select up/down: passthrough unless _active AND chains > 8.
        try:
            if self._bank_up_button is not None:
                self._bank_up_button.add_value_listener(self._bank_up_value)
        except Exception:
            pass
        try:
            if self._bank_down_button is not None:
                self._bank_down_button.add_value_listener(self._bank_down_value)
        except Exception:
            pass

        # Shift tracker (do NOT own the button — we add an observer listener).
        try:
            if self._shift_button is not None:
                self._shift_button.add_value_listener(self._shift_value)
        except Exception:
            pass

        # Encoder sub-mode observer: when the user presses Pan/SendA/B/C,
        # rebind chain encoders to the new sub-mode. Add to ALL 4 buttons
        # (Pan/SendA/SendB/SendC) so any of them triggers a re-evaluation.
        for btn in self._encoder_mode_buttons:
            try:
                cb = (lambda value, b=btn: self._on_encoder_sub_mode_change(value))
                btn.add_value_listener(cb)
                self._encoder_mode_listeners.append((btn, cb))
            except Exception:
                pass

        # Selected-track listener — same hook the AutoFilter component uses.
        try:
            song = self.song()
            song.view.add_selected_track_listener(self._on_selected_track_changed_listener)
            self._track_selection_listener_song = song.view
        except Exception:
            self._track_selection_listener_song = None

        try:
            song = self.song()
            song.add_tracks_listener(self._on_tracks_changed_listener)
            self._track_list_listener_song = song
        except Exception:
            self._track_list_listener_song = None

    def _detach_static_listeners(self):
        try:
            if self._detail_view_button is not None:
                self._detail_view_button.remove_value_listener(self._detail_view_value)
        except Exception:
            pass
        try:
            if self._bank_up_button is not None:
                self._bank_up_button.remove_value_listener(self._bank_up_value)
        except Exception:
            pass
        try:
            if self._bank_down_button is not None:
                self._bank_down_button.remove_value_listener(self._bank_down_value)
        except Exception:
            pass
        try:
            if self._shift_button is not None:
                self._shift_button.remove_value_listener(self._shift_value)
        except Exception:
            pass
        for btn, cb in self._encoder_mode_listeners:
            try:
                btn.remove_value_listener(cb)
            except Exception:
                pass
        self._encoder_mode_listeners = []

    def _on_selected_track_changed_listener(self):
        self._evaluate_selection()

    def _on_tracks_changed_listener(self):
        self.on_track_list_changed()

    # ---------- Detection + engagement decision --------------------------

    def _detect_drum_rack(self, track):
        """Walk track.devices top-level only. Return first device whose
        class_name matches DRUM_RACK_CLASS_NAMES, else None. Fail-quiet."""
        if track is None:
            return None
        try:
            devices = list(track.devices)
        except Exception:
            return None
        for device in devices:
            try:
                cls = getattr(device, 'class_name', None)
            except Exception:
                cls = None
            if cls in DRUM_RACK_CLASS_NAMES:
                return device
        return None

    def _evaluate_selection(self):
        """Decide whether the mode should be engaged for the currently
        selected track, and bring the actual state into line."""
        try:
            track = self.song().view.selected_track
        except Exception:
            track = None

        rack = self._detect_drum_rack(track) if track is not None else None
        should_engage = (
            rack is not None
            and (track is not None and id(track) not in self._exited_tracks)
        )

        if should_engage:
            if self._active:
                # Already engaged. If the rack changed (different track,
                # different rack instance), re-engage from scratch so we
                # capture fresh.
                if rack is not self._drum_rack:
                    self._disengage()
                    self._engage(rack)
                # Else: same rack still active — nothing to do.
            else:
                self._engage(rack)
        else:
            if self._active:
                self._disengage()

        self._refresh_indicator_led()

    # ---------- Engagement / disengagement -------------------------------

    def _engage(self, drum_rack):
        self._active = True
        self._drum_rack = drum_rack
        self._chain_offset = 0

        # First-activation diagnostic dump — mirrors EncoderAutoFilterComponent
        # _params_logged. Surfaces the actual class_name + chain count + the
        # parameter list of chain[0].mixer_device, so any name mismatch
        # (panning vs pan, sends[] indexing) is obvious in Log.txt rather
        # than producing a silent miss.
        if not self._diag_logged:
            self._dump_diagnostics_once(drum_rack)

        # Chain-count change listener so faders/encoders/mute/solo for newly
        # added chains become live without re-selecting the track. Pruned
        # in _disengage.
        try:
            if hasattr(drum_rack, 'add_chains_listener'):
                drum_rack.add_chains_listener(self._on_chains_changed)
                self._chains_listener_rack = drum_rack
        except Exception:
            self._chains_listener_rack = None

        # Capture the mixer strips' fader/mute/solo bindings — release them
        # so SpecialMixerComponent's writes go to released slots (no-op) and
        # our chain bindings own the surface controls.
        for i in range(NUM_STRIPS):
            try:
                strip = self._mixer.channel_strip(i)
                strip.set_volume_control(None)
                strip.set_mute_button(None)
                strip.set_solo_button(None)
            except Exception:
                pass

        # Bind the captured controls to chain semantics. This also computes
        # whether to take scene-bank ownership (depends on chain count > 8).
        self._refresh_all_chain_bindings()
        self._refresh_scene_bank_ownership()

    def _disengage(self):
        # Release encoders, faders. Slots will revert to mixer-strip ownership
        # after we call mixer.update() below.
        try:
            for slider, cb in self._slider_listeners:
                try:
                    slider.remove_value_listener(cb)
                except Exception:
                    pass
                try:
                    slider.release_parameter()
                except Exception:
                    pass
        except Exception:
            pass
        self._slider_listeners = []

        try:
            for button, cb in self._mute_listeners:
                try:
                    button.remove_value_listener(cb)
                except Exception:
                    pass
        except Exception:
            pass
        self._mute_listeners = []

        try:
            for button, cb in self._solo_listeners:
                try:
                    button.remove_value_listener(cb)
                except Exception:
                    pass
        except Exception:
            pass
        self._solo_listeners = []

        # Detach chain LED-feedback listeners (chain.mute / chain.solo).
        for chain, cb in self._chain_mute_listeners:
            try:
                chain.remove_mute_listener(cb)
            except Exception:
                pass
        self._chain_mute_listeners = []
        for chain, cb in self._chain_solo_listeners:
            try:
                chain.remove_solo_listener(cb)
            except Exception:
                pass
        self._chain_solo_listeners = []

        # Encoders: release any chain-bound parameter so the encoder is
        # available again for EncModeSelectorComponent's per-strip pan/send
        # routing once mixer.update() runs.
        for enc in self._encoders:
            try:
                enc.release_parameter()
            except Exception:
                pass

        # Detach chain-count listener.
        try:
            if self._chains_listener_rack is not None and hasattr(self._chains_listener_rack, 'remove_chains_listener'):
                self._chains_listener_rack.remove_chains_listener(self._on_chains_changed)
        except Exception:
            pass
        self._chains_listener_rack = None

        # Drop in-flight momentary holds and clear chain refs on slot handlers.
        for h in self._slot_handlers:
            h.set_chain(None)

        # Restore session ownership of scene-bank buttons (Stop All Clips
        # ownership is no longer touched — that LED is hardware-only on
        # APC40 mk1; the indicator moved to the Detail View button).
        try:
            if self._session is not None and self._scene_nav_taken:
                # Restore scene-nav. Note the SessionComponent API is
                # set_scene_bank_buttons(down, up) — order matters.
                self._session.set_scene_bank_buttons(self._bank_down_button, self._bank_up_button)
                self._scene_nav_taken = False
        except Exception:
            pass

        # Turn off the Detail View LED. DetailViewCntrlComponent's own
        # _detail_view_visibility_changed will repaint it on next view-change
        # event, but we don't want a stale "active" indicator hanging around
        # after disengage.
        try:
            if self._detail_view_button is not None:
                self._detail_view_button.send_value(0, True)
        except Exception:
            pass

        # Restore SpecialMixerComponent's normal wiring. mixer.update() walks
        # every channel strip and re-asserts volume / mute / solo / pan / send
        # bindings per the current encoder mode.
        try:
            self._mixer.update()
        except Exception:
            pass
        # ALSO ask EncModeSelectorComponent to refresh, so its current sub-mode
        # re-asserts pan/send encoder routing on the released encoders.
        try:
            if self._encoder_modes is not None:
                self._encoder_modes.update()
        except Exception:
            pass

        self._active = False
        self._drum_rack = None

    # ---------- Chain bindings -------------------------------------------

    def _get_chains(self):
        if self._drum_rack is None:
            return []
        try:
            return list(self._drum_rack.chains)
        except Exception:
            return []

    def _chain_at_slot(self, slot):
        """Return the chain occupying APC40 strip slot 0..7, or None."""
        chains = self._get_chains()
        idx = self._chain_offset + slot
        if 0 <= idx < len(chains):
            return chains[idx]
        return None

    def _refresh_all_chain_bindings(self):
        if not self._active:
            return

        # Tear down whatever we previously bound — we re-build from scratch
        # on every refresh (chain-count change, bank scroll, sub-mode flip).
        for slider, cb in self._slider_listeners:
            try:
                slider.remove_value_listener(cb)
            except Exception:
                pass
            try:
                slider.release_parameter()
            except Exception:
                pass
        self._slider_listeners = []

        for button, cb in self._mute_listeners:
            try:
                button.remove_value_listener(cb)
            except Exception:
                pass
        self._mute_listeners = []

        for button, cb in self._solo_listeners:
            try:
                button.remove_value_listener(cb)
            except Exception:
                pass
        self._solo_listeners = []

        # Tear down chain LED-feedback listeners — we'll re-add them per slot.
        for chain, cb in self._chain_mute_listeners:
            try:
                chain.remove_mute_listener(cb)
            except Exception:
                pass
        self._chain_mute_listeners = []
        for chain, cb in self._chain_solo_listeners:
            try:
                chain.remove_solo_listener(cb)
            except Exception:
                pass
        self._chain_solo_listeners = []

        for enc in self._encoders:
            try:
                enc.release_parameter()
            except Exception:
                pass

        # Determine encoder sub-mode from the encoder_modes' current state.
        sub_mode = self._current_encoder_sub_mode()

        # Bind one slot at a time. Slots beyond chain count are released.
        for slot in range(NUM_STRIPS):
            chain = self._chain_at_slot(slot)
            self._slot_handlers[slot].set_chain(chain)

            if chain is None:
                # Slot is past the end. Leave fader / encoder / mute / solo
                # released and dark-paint the buttons explicitly so any
                # leftover state from the prior page or strip wiring goes off.
                try:
                    self._mute_buttons[slot].send_value(0)
                except Exception:
                    pass
                try:
                    self._solo_buttons[slot].send_value(0)
                except Exception:
                    pass
                continue

            # Fader → chain.mixer_device.volume.
            try:
                vol = chain.mixer_device.volume
                if vol is not None:
                    self._sliders[slot].connect_to(vol)
            except Exception:
                pass

            # Mute / Solo: add value listeners that route through the per-slot
            # ChainSlotHandler. Captured-by-default-arg lambda for the slot id.
            def _mk_mute_cb(s=slot):
                return (lambda value: self._mute_value(s, value))
            def _mk_solo_cb(s=slot):
                return (lambda value: self._solo_value(s, value))
            mute_cb = _mk_mute_cb()
            solo_cb = _mk_solo_cb()
            try:
                self._mute_buttons[slot].add_value_listener(mute_cb)
                self._mute_listeners.append((self._mute_buttons[slot], mute_cb))
            except Exception:
                pass
            try:
                self._solo_buttons[slot].add_value_listener(solo_cb)
                self._solo_listeners.append((self._solo_buttons[slot], solo_cb))
            except Exception:
                pass

            # Chain → button LED feedback. add_mute_listener / add_solo_listener
            # fire whenever chain.mute / chain.solo changes (toggled from the
            # APC40 OR from Live's own mixer panel). We then repaint the LED
            # via send_value(127|0) — bypasses set_on_off_values, which plain
            # ButtonElement doesn't have.
            def _mk_mute_led(s=slot):
                return (lambda: self._refresh_mute_led(s))
            def _mk_solo_led(s=slot):
                return (lambda: self._refresh_solo_led(s))
            mute_led_cb = _mk_mute_led()
            solo_led_cb = _mk_solo_led()
            try:
                chain.add_mute_listener(mute_led_cb)
                self._chain_mute_listeners.append((chain, mute_led_cb))
            except Exception:
                pass
            try:
                chain.add_solo_listener(solo_led_cb)
                self._chain_solo_listeners.append((chain, solo_led_cb))
            except Exception:
                pass
            # Initial paint for this slot.
            self._refresh_mute_led(slot)
            self._refresh_solo_led(slot)

            # Encoder → chain.mixer_device.{panning|sends[0..2]} per sub-mode.
            self._bind_chain_encoder(slot, chain, sub_mode)

    def _current_encoder_sub_mode(self):
        """Read the current encoder sub-mode from EncModeSelectorComponent.
        Returns 0 (Pan), 1 (Send A), 2 (Send B), 3 (Send C). Defaults to 0
        on any failure — Pan is the safe default."""
        try:
            idx = int(self._encoder_modes._mode_index)
            if 0 <= idx <= 3:
                return idx
        except Exception:
            pass
        return 0

    def _bind_chain_encoder(self, slot, chain, sub_mode):
        if chain is None:
            return
        try:
            mixer = chain.mixer_device
        except Exception:
            return
        param = None
        try:
            if sub_mode == 0:
                param = getattr(mixer, 'panning', None)
            else:
                # sub_mode 1..3 → sends[0..2]. Project may have fewer
                # return tracks; index out of range → release (no-op).
                send_idx = sub_mode - 1
                sends = list(getattr(mixer, 'sends', []))
                if 0 <= send_idx < len(sends):
                    param = sends[send_idx]
        except Exception:
            param = None
        if param is None:
            return
        try:
            self._encoders[slot].connect_to(param)
        except Exception:
            pass

    def _on_chains_changed(self):
        # drum_rack.chains changed (chain added or removed). Clamp offset,
        # re-bind, and re-evaluate scene-bank ownership (chain count crossing
        # the 8 threshold flips ownership).
        try:
            chains = self._get_chains()
            max_offset = max(0, len(chains) - NUM_STRIPS)
            if self._chain_offset > max_offset:
                self._chain_offset = max_offset
            self._refresh_all_chain_bindings()
            self._refresh_scene_bank_ownership()
        except Exception:
            pass

    def _refresh_scene_bank_ownership(self):
        """Take or release scene-bank ownership based on chain count.

        With chains > NUM_STRIPS the user expects bank up/down to scroll
        through chain pages — so we suppress the SessionComponent's
        scene-nav listener for the duration. With chains <= NUM_STRIPS we
        passthrough scene nav (UAT step 6 requirement).

        Toggling here rather than always-take-on-_engage means switching
        from a 16-pad rack to a 4-pad rack restores scene nav cleanly.
        """
        if self._session is None:
            return
        try:
            chain_count = len(self._get_chains())
            should_take = self._active and chain_count > NUM_STRIPS
            if should_take and not self._scene_nav_taken:
                self._session.set_scene_bank_buttons(None, None)
                self._scene_nav_taken = True
                try:
                    self._parent.log_message(
                        '[DrumRack] scene-bank ownership TAKEN (chains=' + repr(chain_count) + ')')
                except Exception:
                    pass
            elif (not should_take) and self._scene_nav_taken:
                # Restore. SessionComponent.set_scene_bank_buttons signature
                # is (down, up) — match the binding established in __init__
                # of APC_64_40_9 (line 94).
                self._session.set_scene_bank_buttons(self._bank_down_button, self._bank_up_button)
                self._scene_nav_taken = False
                try:
                    self._parent.log_message(
                        '[DrumRack] scene-bank ownership RESTORED (chains=' + repr(chain_count) + ')')
                except Exception:
                    pass
        except Exception:
            pass

    def _refresh_mute_led(self, slot):
        """Paint mute LED for a slot. Inverted convention (matches v1.0
        set_invert_mute_feedback): lit when chain is alive, dark when muted."""
        if not (0 <= slot < NUM_STRIPS):
            return
        button = self._mute_buttons[slot]
        chain = self._chain_at_slot(slot)
        if chain is None:
            try:
                button.send_value(0)
            except Exception:
                pass
            return
        try:
            muted = bool(chain.mute)
        except Exception:
            muted = False
        try:
            button.send_value(0 if muted else 127)
        except Exception:
            pass

    def _refresh_solo_led(self, slot):
        """Paint solo LED for a slot. Direct convention: lit when soloing."""
        if not (0 <= slot < NUM_STRIPS):
            return
        button = self._solo_buttons[slot]
        chain = self._chain_at_slot(slot)
        if chain is None:
            try:
                button.send_value(0)
            except Exception:
                pass
            return
        try:
            soloed = bool(chain.solo)
        except Exception:
            soloed = False
        try:
            button.send_value(127 if soloed else 0)
        except Exception:
            pass

    def _on_encoder_sub_mode_change(self, value):
        # Triggered on every press/release of the four encoder mode buttons.
        # We rebind on press-down only (value != 0) — release events would
        # cause two rebinds per press otherwise. Read _mode_index directly;
        # the existing EncModeSelectorComponent handler has already updated
        # it by the time our observer listener fires (synchronous chain).
        if not self._active:
            return
        if value == 0:
            return
        self._refresh_all_chain_bindings()

    # ---------- Cross-cutting passthroughs --------------------------------

    def _detail_view_value(self, value):
        # Passthrough unless mode is active AND user is holding shift AND
        # this is a press-down event. On match, mark current track as exited
        # and disengage. DetailViewCntrlComponent gates ITS handler on
        # `not self._shift_pressed`, so a shift-held press is exclusively
        # ours; an unshifted press is exclusively theirs (toggles Live's
        # Detail view as before).
        if not self._active:
            return
        if not self._shift_pressed:
            return
        if value == 0:
            return
        try:
            track = self.song().view.selected_track
        except Exception:
            track = None
        if track is not None:
            self._exited_tracks.add(id(track))
        try:
            self._disengage()
        except Exception:
            pass
        self._refresh_indicator_led()

    def _bank_up_value(self, value):
        # Passthrough unless mode active AND chains > 8 AND press-down.
        if value == 0:
            return
        chains = self._get_chains()
        # Diagnostic so the next UAT can paste Log.txt and tell us whether
        # the listener is firing AND what the actual chain count is. The
        # round-1+2 "still not working" reports were ambiguous between
        # "listener never fired" and "listener fired but chain count <= 8".
        try:
            self._parent.log_message(
                '[DrumRack] bank_up press: active=' + repr(self._active) +
                ' chains=' + repr(len(chains)) +
                ' offset=' + repr(self._chain_offset) +
                ' scene_nav_taken=' + repr(self._scene_nav_taken))
        except Exception:
            pass
        if not self._active:
            return
        if len(chains) <= NUM_STRIPS:
            return
        new_offset = max(self._chain_offset - NUM_STRIPS, 0)
        if new_offset != self._chain_offset:
            self._chain_offset = new_offset
            self._refresh_all_chain_bindings()
            try:
                self._parent.log_message(
                    '[DrumRack] bank_up scrolled: new offset=' + repr(new_offset))
            except Exception:
                pass

    def _bank_down_value(self, value):
        # Passthrough unless mode active AND chains > 8 AND press-down.
        if value == 0:
            return
        chains = self._get_chains()
        try:
            self._parent.log_message(
                '[DrumRack] bank_down press: active=' + repr(self._active) +
                ' chains=' + repr(len(chains)) +
                ' offset=' + repr(self._chain_offset) +
                ' scene_nav_taken=' + repr(self._scene_nav_taken))
        except Exception:
            pass
        if not self._active:
            return
        if len(chains) <= NUM_STRIPS:
            return
        max_offset = max(0, len(chains) - NUM_STRIPS)
        new_offset = min(self._chain_offset + NUM_STRIPS, max_offset)
        if new_offset != self._chain_offset:
            self._chain_offset = new_offset
            self._refresh_all_chain_bindings()
            try:
                self._parent.log_message(
                    '[DrumRack] bank_down scrolled: new offset=' + repr(new_offset))
            except Exception:
                pass

    def _shift_value(self, value):
        # Observer-only: track the modifier state so _detail_view_value can
        # gate its exit action. NEVER own the shift button.
        self._shift_pressed = (value != 0)

    # ---------- Per-slot mute / solo callbacks ----------------------------

    def _mute_value(self, slot, value):
        if not self._active:
            return
        if 0 <= slot < len(self._slot_handlers):
            self._slot_handlers[slot].handle_mute(value, self._shift_pressed)

    def _solo_value(self, slot, value):
        if not self._active:
            return
        if 0 <= slot < len(self._slot_handlers):
            self._slot_handlers[slot].handle_solo(value, self._shift_pressed)

    # ---------- Detail View indicator LED -------------------------------

    def _refresh_indicator_led(self):
        # Detail View button (note 62, channel 0). Has a MIDI-addressable
        # LED — confirmed working via send_value(127, True). Indicator
        # migrated from Stop All Clips after UAT confirmed Stop All Clips
        # is hardware-only on APC40 mk1 (LED never lights even from Live's
        # own writes when clips are playing).
        # DetailViewCntrlComponent normally drives this LED to follow Live's
        # Detail-view-visible state, but only fires on visibility change.
        # Our _on_timer tick re-asserts every Live MIDI loop iteration so
        # we always win the race while the mode is active.
        if self._detail_view_button is None:
            return
        try:
            self._detail_view_button.send_value(127 if self._active else 0, True)
        except Exception:
            pass

    # ---------- One-shot diagnostic dump ---------------------------------

    def _dump_diagnostics_once(self, drum_rack):
        """Mirrors EncoderAutoFilterComponent._params_logged. Logs the
        actual class_name + chain count + chain names + the parameter list
        of chain[0].mixer_device on first activation. Surfaces any
        Live-version drift (DrumGroupDevice2, panning vs pan, etc.) in
        Log.txt rather than producing silent wrong bindings."""
        self._diag_logged = True
        try:
            cls = getattr(drum_rack, 'class_name', '?')
            self._log("[DrumRack] detected device class: " + repr(cls))
        except Exception:
            pass
        try:
            chains = self._get_chains()
            self._log("[DrumRack] chain count: " + str(len(chains)))
            for i, ch in enumerate(chains):
                try:
                    nm = getattr(ch, 'name', '?')
                except Exception:
                    nm = '?'
                self._log("[DrumRack] chain " + str(i) + ": " + repr(nm))
            if chains:
                try:
                    md = chains[0].mixer_device
                    self._log("[DrumRack] chain[0] mixer attrs: panning=" +
                              repr(getattr(md, 'panning', None) is not None) +
                              " volume=" +
                              repr(getattr(md, 'volume', None) is not None))
                    sends = list(getattr(md, 'sends', []))
                    self._log("[DrumRack] chain[0] mixer sends count: " + str(len(sends)))
                    for j, snd in enumerate(sends):
                        try:
                            sn = getattr(snd, 'name', '?')
                        except Exception:
                            sn = '?'
                        self._log("[DrumRack] chain[0] send " + str(j) + ": " + repr(sn))
                except Exception as e:
                    try:
                        self._log("[DrumRack] chain[0] mixer dump failed: " + str(e))
                    except Exception:
                        pass
        except Exception as e:
            try:
                self._log("[DrumRack] diagnostics failed: " + str(e))
            except Exception:
                pass

    def _log(self, msg):
        try:
            if self._parent is not None and hasattr(self._parent, 'log_message'):
                self._parent.log_message(msg)
        except Exception:
            pass

    # ---------- Timer-driven press-state countdown -----------------------

    def _on_timer(self):
        if not self.is_enabled():
            return
        if not self._active:
            return
        try:
            for h in self._slot_handlers:
                h.tick()
        except Exception:
            pass
        # Periodic LED re-assertion — DetailViewCntrlComponent only writes
        # the LED on Live-side Detail-view visibility-change events; our
        # tick repaint covers any race where the user toggles Detail view
        # while in Drum Rack Mode. Cost: one MIDI byte per tick = negligible.
        try:
            if self._detail_view_button is not None:
                self._detail_view_button.send_value(127, True)
        except Exception:
            pass


# local variables:
# tab-width: 4
