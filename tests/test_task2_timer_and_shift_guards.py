# Tests for Task 2: _on_timer countdown + set_solo_button / set_mute_button shift guards
# These tests MUST fail before implementation (RED phase).

import sys
import os
import unittest
import types
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.framework_stubs import TrackStub, SongStub, ButtonStub, SpecialChanStripStub

# Inject framework stubs
framework_pkg = types.ModuleType('_Framework')
chan_strip_mod = types.ModuleType('_Framework.ChannelStripComponent')


class _FakeChannelStripComponent(SpecialChanStripStub):
    pass


chan_strip_mod.ChannelStripComponent = _FakeChannelStripComponent
framework_pkg.ChannelStripComponent = chan_strip_mod
sys.modules.setdefault('_Framework', framework_pkg)
sys.modules.setdefault('_Framework.ChannelStripComponent', chan_strip_mod)

pkg_mod = types.ModuleType('APC_64_40_12')
pkg_mod.__path__ = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
sys.modules.setdefault('APC_64_40_12', pkg_mod)

special_in_pkg = types.ModuleType('APC_64_40_12.SpecialChanStripComponent')
special_in_pkg.SpecialChanStripComponent = SpecialChanStripStub
sys.modules.setdefault('APC_64_40_12.SpecialChanStripComponent', special_in_pkg)

_MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'ToggleMomentaryChannelStripComponent.py'
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        'ToggleMomentaryChannelStripComponent', _MODULE_PATH,
        submodule_search_locations=[]
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = 'APC_64_40_12'
    spec.loader.exec_module(mod)
    return mod


def _make_strip(track_solo=False, track_mute=False, enabled=True):
    mod = _load_module()
    strip = mod.ToggleMomentaryChannelStripComponent()
    strip._enabled = enabled
    strip._track = TrackStub(solo=track_solo, mute=track_mute)
    strip._song._master_track = TrackStub()
    return strip


class TestOnTimerMethodExists(unittest.TestCase):
    """Task 2: _on_timer must have countdown logic, not just stub comment."""

    def test_stub_comment_removed(self):
        with open(_MODULE_PATH) as f:
            source = f.read()
        self.assertNotIn('Phase 2 will add', source,
                         "Stub comment 'Phase 2 will add' must be removed")


class TestOnTimerSoloCountdown(unittest.TestCase):
    """_on_timer decrements _solo_ticks_delay and sets _solo_momentary_active at 0."""

    def test_timer_decrements_solo_ticks(self):
        strip = _make_strip(track_solo=False)
        strip._solo_ticks_delay = 3
        strip._on_timer()
        self.assertEqual(strip._solo_ticks_delay, 2,
                         "_on_timer must decrement _solo_ticks_delay from 3 to 2")

    def test_timer_inactive_solo_not_decremented(self):
        strip = _make_strip()
        strip._solo_ticks_delay = -1
        strip._on_timer()
        self.assertEqual(strip._solo_ticks_delay, -1,
                         "-1 (inactive) must not be decremented further")

    def test_timer_sets_momentary_active_at_zero(self):
        strip = _make_strip(track_solo=False)
        strip._solo_ticks_delay = 0
        strip._on_timer()
        self.assertTrue(strip._solo_momentary_active,
                        "_solo_momentary_active must be True when tick countdown hits 0")

    def test_timer_does_not_set_momentary_above_zero(self):
        strip = _make_strip(track_solo=False)
        strip._solo_ticks_delay = 1
        strip._on_timer()
        self.assertFalse(strip._solo_momentary_active,
                         "_solo_momentary_active must NOT be set before countdown hits 0")

    def test_timer_does_not_change_track_state_at_threshold(self):
        """State was already inverted at press-down — no re-write at threshold."""
        strip = _make_strip(track_solo=True)  # already inverted at press-down
        strip._solo_ticks_delay = 0
        strip._on_timer()
        # Track state must not flip again
        self.assertTrue(strip._track.solo,
                        "_on_timer must not re-write track.solo at threshold (already inverted)")


class TestOnTimerMuteCountdown(unittest.TestCase):
    """_on_timer decrements _mute_ticks_delay symmetrically."""

    def test_timer_decrements_mute_ticks(self):
        strip = _make_strip(track_mute=False)
        strip._mute_ticks_delay = 2
        strip._on_timer()
        self.assertEqual(strip._mute_ticks_delay, 1)

    def test_timer_sets_mute_momentary_active_at_zero(self):
        strip = _make_strip(track_mute=False)
        strip._mute_ticks_delay = 0
        strip._on_timer()
        self.assertTrue(strip._mute_momentary_active)

    def test_timer_inactive_mute_not_decremented(self):
        strip = _make_strip()
        strip._mute_ticks_delay = -1
        strip._on_timer()
        self.assertEqual(strip._mute_ticks_delay, -1)


class TestOnTimerSoloAndMuteIndependent(unittest.TestCase):
    """Both counters progress simultaneously (independent if-statements, not if/elif)."""

    def test_both_counters_decrement_independently(self):
        strip = _make_strip()
        strip._solo_ticks_delay = 3
        strip._mute_ticks_delay = 2
        strip._on_timer()
        self.assertEqual(strip._solo_ticks_delay, 2)
        self.assertEqual(strip._mute_ticks_delay, 1)

    def test_full_countdown_sequence_solo(self):
        """Simulate full countdown; momentary flag set when ticks_delay reaches 0.

        Sequence: start=4, tick→3, tick→2, tick→1, tick→0 (next tick fires flag).
        The flag fires on tick 5 (LONG_PRESS_DELAY+1 ticks total from start=LONG_PRESS_DELAY).
        """
        mod = _load_module()
        LONG_PRESS_DELAY = mod.LONG_PRESS_DELAY  # should be 4
        strip = _make_strip(track_solo=False)
        strip._solo_ticks_delay = LONG_PRESS_DELAY  # 4

        # LONG_PRESS_DELAY+1 ticks: reaches 0, then 0 triggers flag, decrements to -1
        for tick in range(LONG_PRESS_DELAY + 1):
            strip._on_timer()

        self.assertTrue(strip._solo_momentary_active,
                        "After LONG_PRESS_DELAY+1 ticks, _solo_momentary_active must be True")


class TestSetSoloButtonGuard(unittest.TestCase):
    """set_solo_button override reverts track state when called mid-hold."""

    def test_set_solo_button_defined_in_subclass(self):
        mod = _load_module()
        cls = mod.ToggleMomentaryChannelStripComponent
        self.assertIn('set_solo_button', cls.__dict__,
                      "set_solo_button must be overridden in subclass")

    def test_set_solo_button_reverts_track_when_momentary_active(self):
        strip = _make_strip(track_solo=True)  # currently inverted
        strip._solo_state_before_press = False  # was False before press
        strip._solo_momentary_active = True
        strip._solo_ticks_delay = 0
        strip.set_solo_button(None)
        self.assertFalse(strip._track.solo,
                         "set_solo_button must revert track.solo to _solo_state_before_press")

    def test_set_solo_button_clears_momentary_active(self):
        strip = _make_strip(track_solo=True)
        strip._solo_state_before_press = False
        strip._solo_momentary_active = True
        strip.set_solo_button(None)
        self.assertFalse(strip._solo_momentary_active,
                         "set_solo_button must clear _solo_momentary_active")

    def test_set_solo_button_resets_ticks_delay(self):
        strip = _make_strip()
        strip._solo_ticks_delay = 2
        strip._solo_momentary_active = False
        strip.set_solo_button(None)
        self.assertEqual(strip._solo_ticks_delay, -1,
                         "set_solo_button must reset _solo_ticks_delay to -1")

    def test_set_solo_button_no_track_no_crash(self):
        mod = _load_module()
        strip = mod.ToggleMomentaryChannelStripComponent()
        strip._track = None
        strip._solo_momentary_active = True
        # Must not raise AttributeError
        strip.set_solo_button(None)
        self.assertFalse(strip._solo_momentary_active)

    def test_set_solo_button_skips_revert_when_not_momentary(self):
        """Short press path: momentary not active, so revert must not fire."""
        strip = _make_strip(track_solo=True)
        strip._solo_state_before_press = False
        strip._solo_momentary_active = False  # short press — not in momentary mode
        strip.set_solo_button(None)
        # track.solo must be unchanged (still True from short press toggle)
        self.assertTrue(strip._track.solo,
                        "Short press (not momentary): set_solo_button must not revert solo state")


class TestSetMuteButtonGuard(unittest.TestCase):
    """set_mute_button override mirrors set_solo_button behavior."""

    def test_set_mute_button_defined_in_subclass(self):
        mod = _load_module()
        cls = mod.ToggleMomentaryChannelStripComponent
        self.assertIn('set_mute_button', cls.__dict__,
                      "set_mute_button must be overridden in subclass")

    def test_set_mute_button_reverts_track_when_momentary_active(self):
        strip = _make_strip(track_mute=True)
        strip._mute_state_before_press = False
        strip._mute_momentary_active = True
        strip.set_mute_button(None)
        self.assertFalse(strip._track.mute,
                         "set_mute_button must revert track.mute to _mute_state_before_press")

    def test_set_mute_button_clears_momentary_active(self):
        strip = _make_strip(track_mute=True)
        strip._mute_state_before_press = False
        strip._mute_momentary_active = True
        strip.set_mute_button(None)
        self.assertFalse(strip._mute_momentary_active)

    def test_set_mute_button_resets_ticks_delay(self):
        strip = _make_strip()
        strip._mute_ticks_delay = 3
        strip._mute_momentary_active = False
        strip.set_mute_button(None)
        self.assertEqual(strip._mute_ticks_delay, -1)

    def test_set_mute_button_no_track_no_crash(self):
        mod = _load_module()
        strip = mod.ToggleMomentaryChannelStripComponent()
        strip._track = None
        strip._mute_momentary_active = True
        strip.set_mute_button(None)
        self.assertFalse(strip._mute_momentary_active)


class TestParentOnTimerCallOrder(unittest.TestCase):
    """SpecialChanStripComponent._on_timer must be called first (fold-delay preservation)."""

    def test_parent_on_timer_call_is_first(self):
        """Verify by checking that fold-delay (_ticks_delay) still decrements."""
        strip = _make_strip()
        strip._ticks_delay = 2  # simulate in-progress fold-delay (parent's counter)
        strip._on_timer()
        self.assertEqual(strip._ticks_delay, 1,
                         "Parent _on_timer must still execute (fold-delay must decrement)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
