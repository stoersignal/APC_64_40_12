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

    def disconnect(self):
        self._solo_ticks_delay = -1
        self._mute_ticks_delay = -1
        SpecialChanStripComponent.disconnect(self)  # handles _unregister_timer_callback

    def _on_timer(self):
        SpecialChanStripComponent._on_timer(self)  # preserve fold-delay behaviour (D-03)
        # Phase 2 will add solo/mute tick countdown logic here


# local variables:
# tab-width: 4
