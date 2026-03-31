# Tests for Phase 3: Multi-track simultaneous holds and disconnect hardening
# These tests verify MULTI-01, MULTI-02, MULTI-03 and the disconnect() mid-hold gap.
# All tests exercise two ToggleMomentaryChannelStripComponent instances to prove
# per-instance isolation — single-instance tests already exist in test_task1/task2.

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


class TestMulti01SoloSimultaneous(unittest.TestCase):
    """MULTI-01: Two strips can hold Solo simultaneously with full independence.

    Note on "set momentary active" pattern: Tests manually set _solo_momentary_active = True
    to simulate the timer having reached threshold, because driving a full timer countdown
    via _on_timer() calls is unnecessary — the momentary flag is what the release handler
    checks (verified in test_task2_timer_and_shift_guards.py). This is not a shortcut; it
    directly exercises the production code path.
    """

    def test_two_strips_solo_simultaneously_both_activate(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_solo=False)
        strip_a._solo_value(127)
        strip_b._solo_value(127)
        self.assertTrue(strip_a._track.solo,
                        "strip_a track.solo must be True after press-down")
        self.assertTrue(strip_b._track.solo,
                        "strip_b track.solo must be True after press-down")

    def test_two_strips_solo_simultaneously_release_a_only(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_solo=False)
        strip_a._solo_value(127)
        strip_b._solo_value(127)
        strip_a._solo_momentary_active = True
        strip_b._solo_momentary_active = True
        strip_a._solo_value(0)
        self.assertFalse(strip_a._track.solo,
                         "strip_a track.solo must be reverted after release")
        self.assertTrue(strip_b._track.solo,
                        "strip_b track.solo must remain True (still held)")

    def test_two_strips_solo_simultaneously_release_b_only(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_solo=False)
        strip_a._solo_value(127)
        strip_b._solo_value(127)
        strip_a._solo_momentary_active = True
        strip_b._solo_momentary_active = True
        strip_b._solo_value(0)
        self.assertTrue(strip_a._track.solo,
                        "strip_a track.solo must remain True (still held)")
        self.assertFalse(strip_b._track.solo,
                         "strip_b track.solo must be reverted after release")

    def test_two_strips_solo_simultaneously_independent_revert(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_solo=False)
        strip_a._solo_value(127)
        strip_b._solo_value(127)
        strip_a._solo_momentary_active = True
        strip_b._solo_momentary_active = True
        strip_a._solo_value(0)
        strip_b._solo_value(0)
        self.assertFalse(strip_a._track.solo,
                         "strip_a must revert to False after release")
        self.assertFalse(strip_b._track.solo,
                         "strip_b must revert to False after release")

    def test_two_strips_solo_state_machines_never_share_state(self):
        """Proves no class-level variable is shared — modifying strip_a state
        must not affect strip_b state at all."""
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_solo=False)
        strip_a._solo_ticks_delay = 3
        self.assertEqual(strip_b._solo_ticks_delay, -1,
                         "strip_b._solo_ticks_delay must be independent of strip_a")


class TestMulti02MuteSimultaneous(unittest.TestCase):
    """MULTI-02: Two strips can hold Mute simultaneously with full independence.

    Note on "set momentary active" pattern: see TestMulti01SoloSimultaneous docstring.
    """

    def test_two_strips_mute_simultaneously_both_activate(self):
        strip_a = _make_strip(track_mute=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._mute_value(127)
        strip_b._mute_value(127)
        self.assertTrue(strip_a._track.mute,
                        "strip_a track.mute must be True after press-down")
        self.assertTrue(strip_b._track.mute,
                        "strip_b track.mute must be True after press-down")

    def test_two_strips_mute_simultaneously_release_a_only(self):
        strip_a = _make_strip(track_mute=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._mute_value(127)
        strip_b._mute_value(127)
        strip_a._mute_momentary_active = True
        strip_b._mute_momentary_active = True
        strip_a._mute_value(0)
        self.assertFalse(strip_a._track.mute,
                         "strip_a track.mute must be reverted after release")
        self.assertTrue(strip_b._track.mute,
                        "strip_b track.mute must remain True (still held)")

    def test_two_strips_mute_simultaneously_release_b_only(self):
        strip_a = _make_strip(track_mute=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._mute_value(127)
        strip_b._mute_value(127)
        strip_a._mute_momentary_active = True
        strip_b._mute_momentary_active = True
        strip_b._mute_value(0)
        self.assertTrue(strip_a._track.mute,
                        "strip_a track.mute must remain True (still held)")
        self.assertFalse(strip_b._track.mute,
                         "strip_b track.mute must be reverted after release")

    def test_two_strips_mute_simultaneously_independent_revert(self):
        strip_a = _make_strip(track_mute=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._mute_value(127)
        strip_b._mute_value(127)
        strip_a._mute_momentary_active = True
        strip_b._mute_momentary_active = True
        strip_a._mute_value(0)
        strip_b._mute_value(0)
        self.assertFalse(strip_a._track.mute,
                         "strip_a must revert to False after release")
        self.assertFalse(strip_b._track.mute,
                         "strip_b must revert to False after release")


class TestMulti03SoloOnOneTrackMuteOnAnother(unittest.TestCase):
    """MULTI-03: Solo held on one track and Mute held on another are fully independent.

    Note on "set momentary active" pattern: see TestMulti01SoloSimultaneous docstring.
    """

    def test_solo_a_mute_b_both_activate(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._solo_value(127)
        strip_b._mute_value(127)
        self.assertTrue(strip_a._track.solo,
                        "strip_a track.solo must be True after press-down")
        self.assertTrue(strip_b._track.mute,
                        "strip_b track.mute must be True after press-down")

    def test_solo_a_mute_b_release_solo_first(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._solo_value(127)
        strip_b._mute_value(127)
        strip_a._solo_momentary_active = True
        strip_b._mute_momentary_active = True
        strip_a._solo_value(0)
        self.assertFalse(strip_a._track.solo,
                         "strip_a track.solo must be reverted after solo release")
        self.assertTrue(strip_b._track.mute,
                        "strip_b track.mute must remain True (mute still held)")

    def test_solo_a_mute_b_release_mute_first(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._solo_value(127)
        strip_b._mute_value(127)
        strip_a._solo_momentary_active = True
        strip_b._mute_momentary_active = True
        strip_b._mute_value(0)
        self.assertTrue(strip_a._track.solo,
                        "strip_a track.solo must remain True (solo still held)")
        self.assertFalse(strip_b._track.mute,
                         "strip_b track.mute must be reverted after mute release")

    def test_solo_a_mute_b_full_independent_revert(self):
        strip_a = _make_strip(track_solo=False)
        strip_b = _make_strip(track_mute=False)
        strip_a._solo_value(127)
        strip_b._mute_value(127)
        strip_a._solo_momentary_active = True
        strip_b._mute_momentary_active = True
        strip_a._solo_value(0)
        strip_b._mute_value(0)
        self.assertFalse(strip_a._track.solo,
                         "strip_a solo must revert to False after release")
        self.assertFalse(strip_b._track.mute,
                         "strip_b mute must revert to False after release")


class TestDisconnectMidHold(unittest.TestCase):
    """Hardening: disconnect() must revert active momentary state before tearing down.

    Without this guard, a controller disconnect during a momentary hold leaves the
    track permanently in the inverted state. The hardened disconnect() mirrors the
    guard already present in set_solo_button() / set_mute_button().
    """

    def test_disconnect_reverts_solo_momentary_state(self):
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)          # track.solo = True (inverted on press-down)
        strip._solo_momentary_active = True
        strip._solo_state_before_press = False
        strip.disconnect()
        self.assertFalse(strip._track.solo,
                         "disconnect() must revert track.solo to pre-press state")

    def test_disconnect_reverts_mute_momentary_state(self):
        strip = _make_strip(track_mute=False)
        strip._mute_value(127)          # track.mute = True (inverted on press-down)
        strip._mute_momentary_active = True
        strip._mute_state_before_press = False
        strip.disconnect()
        self.assertFalse(strip._track.mute,
                         "disconnect() must revert track.mute to pre-press state")

    def test_disconnect_no_track_no_crash(self):
        strip = _make_strip()
        strip._track = None
        strip._solo_momentary_active = True
        # Must not raise AttributeError when _track is None
        strip.disconnect()

    def test_disconnect_short_press_does_not_revert(self):
        """Short press path: _solo_momentary_active is False (timer threshold not reached).
        disconnect() guard checks this flag — so the toggle (solo=True) must be preserved.
        This documents the expected behavior: disconnect() reverts momentary holds only,
        not short-press toggles."""
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)   # track.solo = True (toggle on press-down)
        # _solo_momentary_active is False — timer has not counted down yet
        self.assertFalse(strip._solo_momentary_active,
                         "Precondition: momentary not yet active before disconnect")
        strip.disconnect()
        self.assertTrue(strip._track.solo,
                        "Short-press toggle (solo=True) must be preserved after disconnect; "
                        "only momentary holds are reverted")


class TestRapidConsecutivePresses(unittest.TestCase):
    """Regression documentation: rapid press-release-press on the same button.

    Note: MIDI protocol guarantees note-off before note-on on retrigger, so
    _solo_value(0) is always called before a subsequent _solo_value(127).
    The second press therefore always starts with a clean state machine.
    """

    def test_rapid_press_release_press_second_press_is_clean(self):
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)   # first press: solo=True, ticks=LONG_PRESS_DELAY
        strip._solo_value(0)     # first release (short press): solo stays True, ticks=-1
        strip._solo_value(127)   # second press: solo=False (re-toggle), ticks=LONG_PRESS_DELAY
        self.assertFalse(strip._track.solo,
                         "Second press must re-toggle solo back to False")
        self.assertGreater(strip._solo_ticks_delay, 0,
                           "Second press must restart tick countdown")
        self.assertFalse(strip._solo_momentary_active,
                         "Second press must start with momentary_active=False (clean state)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
