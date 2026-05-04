# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from .SpecialChanStripComponent import SpecialChanStripComponent

LONG_PRESS_DELAY = 4  # 4 ticks x 100ms/tick = 400ms


# --- Module-level reusable press-timing helpers ----------------------------
#
# Extracted from ToggleMomentaryChannelStripComponent for reuse by other
# components that need v1.0 toggle/momentary press semantics on attributes
# of arbitrary target objects (e.g. drum-rack chains, not just tracks).
# Behaviour is byte-identical to the v1.0 in-class state machine: press-down
# captures pre-press state, flips the attribute, starts a tick countdown;
# release reverts the attribute iff the countdown crossed the threshold
# (state['momentary'] == True). Caller drives the tick countdown.
#
# `state` is a caller-owned dict with keys:
#   'ticks'     int   — countdown remaining; -1 means "inactive"
#   'before'    bool  — value of target_attr captured at press-down
#   'momentary' bool  — set True when ticks reaches 0; cleared on release
#
# `long_press_delay` is the initial value loaded into 'ticks' on press-down.
# Module constant LONG_PRESS_DELAY = 4 (400ms) preserves v1.0 timing.


def handle_toggle_momentary_event(value, target_obj, target_attr, state,
                                  long_press_delay, shift_pressed):
    """Process a press/release event for a toggle/momentary control.

    Press-down (value != 0): if not shift_pressed, capture target_attr's
    current value into state['before'], flip the attribute on target_obj,
    set state['ticks'] = long_press_delay.

    Release (value == 0): if state['momentary'] is True, restore target_attr
    to state['before'] and clear state['momentary']. Always reset
    state['ticks'] = -1.

    Caller is responsible for any enabled / null-target guards.
    """
    if value != 0:  # press-down
        if shift_pressed:
            return
        current = getattr(target_obj, target_attr)
        state['before'] = current
        setattr(target_obj, target_attr, not current)
        state['ticks'] = long_press_delay
    else:  # release
        if state.get('momentary'):
            setattr(target_obj, target_attr, state['before'])
            state['momentary'] = False
        state['ticks'] = -1


def tick_state(state):
    """Advance one timer tick on a press-state dict.

    If state['ticks'] is -1 (inactive), do nothing.
    If state['ticks'] is 0, set state['momentary'] = True (threshold crossed).
    Always decrement state['ticks'] by 1 (so 0 → -1 next tick).

    Caller drives this from its own _on_timer at the same cadence as v1.0.
    """
    if state['ticks'] > -1:
        if state['ticks'] == 0:
            state['momentary'] = True
        state['ticks'] -= 1


class ToggleMomentaryChannelStripComponent(SpecialChanStripComponent):
    ' Channel strip subclass with toggle/momentary dual-behavior for solo and mute buttons '
    __module__ = __name__

    def __init__(self):
        SpecialChanStripComponent.__init__(self)
        # Solo press state (Phase 2 will use these)
        self._solo_ticks_delay = -1
        self._solo_state_before_press = False
        self._solo_momentary_active = False
        # Mute press state (Phase 2 will use these)
        self._mute_ticks_delay = -1
        self._mute_state_before_press = False
        self._mute_momentary_active = False
        # Note: timer registration is inherited from SpecialChanStripComponent.__init__ (D-04)

    def _build_state_view(self, ticks_attr, state_attr, momentary_attr):
        """Build a dict view over the per-press instance attributes so the
        module-level helpers can read/write the v1.0 state in place. The
        dict shares no storage with the instance — we copy on entry, write
        back on exit. This keeps the on-the-wire state machine byte-identical
        to the original implementation while letting the helpers operate on
        the standardised 'ticks' / 'before' / 'momentary' key set."""
        return {
            'ticks':     getattr(self, ticks_attr),
            'before':    getattr(self, state_attr),
            'momentary': getattr(self, momentary_attr),
        }

    def _writeback_state_view(self, state, ticks_attr, state_attr, momentary_attr):
        setattr(self, ticks_attr, state['ticks'])
        setattr(self, state_attr, state['before'])
        setattr(self, momentary_attr, state['momentary'])

    def _handle_toggle_momentary(self, value, track_attr, ticks_attr, state_attr, momentary_attr):
        if self.is_enabled() and self._track is not None and self._track != self.song().master_track:
            state = self._build_state_view(ticks_attr, state_attr, momentary_attr)
            handle_toggle_momentary_event(
                value, self._track, track_attr, state,
                LONG_PRESS_DELAY, self._shift_pressed,
            )
            self._writeback_state_view(state, ticks_attr, state_attr, momentary_attr)

    def _solo_value(self, value):
        self._handle_toggle_momentary(
            value, 'solo',
            '_solo_ticks_delay', '_solo_state_before_press', '_solo_momentary_active'
        )

    def _mute_value(self, value):
        self._handle_toggle_momentary(
            value, 'mute',
            '_mute_ticks_delay', '_mute_state_before_press', '_mute_momentary_active'
        )

    def set_solo_button(self, button):
        if self._solo_momentary_active:
            if self._track is not None:
                self._track.solo = self._solo_state_before_press
            self._solo_momentary_active = False
        self._solo_ticks_delay = -1
        SpecialChanStripComponent.set_solo_button(self, button)

    def set_mute_button(self, button):
        if self._mute_momentary_active:
            if self._track is not None:
                self._track.mute = self._mute_state_before_press
            self._mute_momentary_active = False
        self._mute_ticks_delay = -1
        SpecialChanStripComponent.set_mute_button(self, button)

    def disconnect(self):
        # Revert any active momentary hold before disconnecting (prevents stuck track state)
        if self._solo_momentary_active and self._track is not None:
            self._track.solo = self._solo_state_before_press
            self._solo_momentary_active = False
        if self._mute_momentary_active and self._track is not None:
            self._track.mute = self._mute_state_before_press
            self._mute_momentary_active = False
        self._solo_ticks_delay = -1
        self._mute_ticks_delay = -1
        SpecialChanStripComponent.disconnect(self)  # handles _unregister_timer_callback

    def _tick_attr(self, ticks_attr, momentary_attr):
        """Advance the v1.0 tick countdown for one solo/mute slot, in place
        on the instance attributes. Behaviour matches the original inline
        if-block byte-for-byte: at ticks==0 set momentary True, then
        decrement ticks (so 0 → -1 next tick)."""
        state = {
            'ticks':     getattr(self, ticks_attr),
            'momentary': getattr(self, momentary_attr),
        }
        tick_state(state)
        setattr(self, ticks_attr, state['ticks'])
        setattr(self, momentary_attr, state['momentary'])

    def _on_timer(self):
        SpecialChanStripComponent._on_timer(self)  # preserve fold-delay behaviour (D-03)
        if self.is_enabled() and self._track is not None:
            self._tick_attr('_solo_ticks_delay', '_solo_momentary_active')
            self._tick_attr('_mute_ticks_delay', '_mute_momentary_active')


# local variables:
# tab-width: 4
