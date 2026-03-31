# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from .SpecialChanStripComponent import SpecialChanStripComponent

LONG_PRESS_DELAY = 4  # 4 ticks x 100ms/tick = 400ms

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

    def _handle_toggle_momentary(self, value, track_attr, ticks_attr, state_attr, momentary_attr):
        if self.is_enabled() and self._track is not None and self._track != self.song().master_track:
            if value != 0:  # press-down
                if self._shift_pressed:
                    return
                current = getattr(self._track, track_attr)
                setattr(self, state_attr, current)
                setattr(self._track, track_attr, not current)
                setattr(self, ticks_attr, LONG_PRESS_DELAY)
            else:  # release
                if getattr(self, momentary_attr):
                    setattr(self._track, track_attr, getattr(self, state_attr))
                    setattr(self, momentary_attr, False)
                setattr(self, ticks_attr, -1)

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

    def disconnect(self):
        self._solo_ticks_delay = -1
        self._mute_ticks_delay = -1
        SpecialChanStripComponent.disconnect(self)  # handles _unregister_timer_callback

    def _on_timer(self):
        SpecialChanStripComponent._on_timer(self)  # preserve fold-delay behaviour (D-03)
        # Phase 2 will add solo/mute tick countdown logic here


# local variables:
# tab-width: 4
