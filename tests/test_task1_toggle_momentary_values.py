# Tests for Task 1: _handle_toggle_momentary helper + _solo_value / _mute_value overrides
# These tests MUST fail before implementation (RED phase).

import sys
import os
import unittest

# Inject framework stubs so imports resolve without Ableton Live
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.framework_stubs import TrackStub, SongStub, ButtonStub, SpecialChanStripStub

# Patch the framework imports before loading the module under test
import unittest.mock as mock

# Build a fake _Framework.ChannelStripComponent that the stub chain covers
import types
framework_pkg = types.ModuleType('_Framework')
chan_strip_mod = types.ModuleType('_Framework.ChannelStripComponent')

class _FakeChannelStripComponent(SpecialChanStripStub):
    pass

chan_strip_mod.ChannelStripComponent = _FakeChannelStripComponent
framework_pkg.ChannelStripComponent = chan_strip_mod
sys.modules['_Framework'] = framework_pkg
sys.modules['_Framework.ChannelStripComponent'] = chan_strip_mod

# Build fake SpecialChanStripComponent module
special_strip_mod = types.ModuleType('SpecialChanStripComponent_module')
special_strip_mod.SpecialChanStripComponent = SpecialChanStripStub

# The module uses relative import: from .SpecialChanStripComponent import SpecialChanStripComponent
# We create a package-like module entry
pkg_mod = types.ModuleType('APC_64_40_12')
pkg_mod.__path__ = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
sys.modules['APC_64_40_12'] = pkg_mod

special_in_pkg = types.ModuleType('APC_64_40_12.SpecialChanStripComponent')
special_in_pkg.SpecialChanStripComponent = SpecialChanStripStub
sys.modules['APC_64_40_12.SpecialChanStripComponent'] = special_in_pkg

# Load the module under test by executing it directly (avoids package import issues)
import importlib.util

_MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'ToggleMomentaryChannelStripComponent.py'
)


def _load_module():
    """Load ToggleMomentaryChannelStripComponent with stubs injected."""
    spec = importlib.util.spec_from_file_location(
        'ToggleMomentaryChannelStripComponent', _MODULE_PATH,
        submodule_search_locations=[]
    )
    mod = importlib.util.module_from_spec(spec)
    # Inject the stub as the relative import target
    mod.__package__ = 'APC_64_40_12'
    spec.loader.exec_module(mod)
    return mod


def _make_strip(track_solo=False, track_mute=False, enabled=True, shift_pressed=False):
    """Create a ToggleMomentaryChannelStripComponent with a live track stub."""
    mod = _load_module()
    strip = mod.ToggleMomentaryChannelStripComponent()
    strip._enabled = enabled
    strip._shift_pressed = shift_pressed
    strip._track = TrackStub(solo=track_solo, mute=track_mute)
    # Make sure master track check fails (track is not master)
    strip._song._master_track = TrackStub()  # different object
    return strip


class TestHandleToggleMomentaryHelperExists(unittest.TestCase):
    """Task 1 acceptance: helper method must exist."""

    def test_helper_method_defined(self):
        mod = _load_module()
        strip = mod.ToggleMomentaryChannelStripComponent()
        self.assertTrue(hasattr(strip, '_handle_toggle_momentary'),
                        "_handle_toggle_momentary helper not defined")

    def test_solo_value_override_defined(self):
        mod = _load_module()
        cls = mod.ToggleMomentaryChannelStripComponent
        self.assertIn('_solo_value', cls.__dict__,
                      "_solo_value not overridden in subclass")

    def test_mute_value_override_defined(self):
        mod = _load_module()
        cls = mod.ToggleMomentaryChannelStripComponent
        self.assertIn('_mute_value', cls.__dict__,
                      "_mute_value not overridden in subclass")


class TestSoloValuePressDown(unittest.TestCase):
    """_solo_value(value > 0): immediate state inversion + timer start."""

    def test_press_inactive_track_solos_it(self):
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)
        self.assertTrue(strip._track.solo,
                        "Press on inactive track must solo it")

    def test_press_active_track_unsolos_it(self):
        strip = _make_strip(track_solo=True)
        strip._solo_value(127)
        self.assertFalse(strip._track.solo,
                         "Press on already-soloed track must unsolo it")

    def test_press_starts_ticks_delay(self):
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)
        self.assertGreater(strip._solo_ticks_delay, 0,
                           "_solo_ticks_delay must be > 0 after press")

    def test_press_captures_state_before_press(self):
        strip = _make_strip(track_solo=True)
        strip._solo_value(127)
        self.assertTrue(strip._solo_state_before_press,
                        "_solo_state_before_press must capture original True state")

    def test_press_with_no_track_does_nothing(self):
        mod = _load_module()
        strip = mod.ToggleMomentaryChannelStripComponent()
        strip._track = None
        strip._enabled = True
        # Should not raise
        strip._solo_value(127)
        self.assertEqual(strip._solo_ticks_delay, -1,
                         "No track: timer must not start")

    def test_shift_pressed_blocks_press(self):
        strip = _make_strip(track_solo=False, shift_pressed=True)
        strip._solo_value(127)
        self.assertFalse(strip._track.solo,
                         "Shift held: press must not change solo state")
        self.assertEqual(strip._solo_ticks_delay, -1,
                         "Shift held: timer must not start")


class TestSoloValueRelease(unittest.TestCase):
    """_solo_value(0): short press keeps toggle; long press reverts."""

    def test_release_before_threshold_keeps_toggle(self):
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)  # press-down; track.solo = True, ticks = 4
        # Simulate short hold: do NOT let timer reach 0
        # _solo_momentary_active is still False
        self.assertFalse(strip._solo_momentary_active)
        strip._solo_value(0)   # release
        # State must remain toggled (True)
        self.assertTrue(strip._track.solo,
                        "Short press: toggle must be kept on release")
        self.assertEqual(strip._solo_ticks_delay, -1,
                         "Release: _solo_ticks_delay must reset to -1")

    def test_release_after_threshold_reverts_state(self):
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)  # press-down; track.solo = True
        # Simulate threshold reached
        strip._solo_momentary_active = True
        strip._solo_value(0)   # release
        # State must revert to original (False)
        self.assertFalse(strip._track.solo,
                         "Long press release: track.solo must revert to pre-press state")
        self.assertFalse(strip._solo_momentary_active,
                         "Long press release: _solo_momentary_active must clear")
        self.assertEqual(strip._solo_ticks_delay, -1,
                         "Long press release: _solo_ticks_delay must reset")

    def test_release_always_resets_ticks_delay(self):
        strip = _make_strip(track_solo=False)
        strip._solo_value(127)
        strip._solo_value(0)
        self.assertEqual(strip._solo_ticks_delay, -1)


class TestMuteValueBehavior(unittest.TestCase):
    """Symmetric tests for _mute_value — mirrors solo behavior."""

    def test_press_inactive_track_mutes_it(self):
        strip = _make_strip(track_mute=False)
        strip._mute_value(127)
        self.assertTrue(strip._track.mute,
                        "Press on inactive track must mute it")

    def test_press_active_track_unmutes_it(self):
        strip = _make_strip(track_mute=True)
        strip._mute_value(127)
        self.assertFalse(strip._track.mute,
                         "Press on already-muted track must unmute it")

    def test_press_starts_mute_ticks_delay(self):
        strip = _make_strip(track_mute=False)
        strip._mute_value(127)
        self.assertGreater(strip._mute_ticks_delay, 0)

    def test_release_before_threshold_keeps_mute(self):
        strip = _make_strip(track_mute=False)
        strip._mute_value(127)
        self.assertFalse(strip._mute_momentary_active)
        strip._mute_value(0)
        self.assertTrue(strip._track.mute,
                        "Short press: mute toggle must be kept on release")
        self.assertEqual(strip._mute_ticks_delay, -1)

    def test_release_after_threshold_reverts_mute(self):
        strip = _make_strip(track_mute=False)
        strip._mute_value(127)
        strip._mute_momentary_active = True
        strip._mute_value(0)
        self.assertFalse(strip._track.mute,
                         "Long press: mute must revert on release")
        self.assertFalse(strip._mute_momentary_active)

    def test_shift_pressed_blocks_mute_press(self):
        strip = _make_strip(track_mute=False, shift_pressed=True)
        strip._mute_value(127)
        self.assertFalse(strip._track.mute,
                         "Shift held: press must not change mute state")


class TestNoForbiddenPatterns(unittest.TestCase):
    """Verify anti-patterns from RESEARCH.md are not present in the source."""

    def test_no_manual_led_calls(self):
        with open(_MODULE_PATH) as f:
            source = f.read()
        self.assertNotIn('turn_on', source,
                         "Manual LED call turn_on found in source")
        self.assertNotIn('turn_off', source,
                         "Manual LED call turn_off found in source")

    def test_no_super_call_in_value_handlers(self):
        with open(_MODULE_PATH) as f:
            source = f.read()
        self.assertNotIn('ChannelStripComponent._solo_value', source)
        self.assertNotIn('ChannelStripComponent._mute_value', source)
        self.assertNotIn('SpecialChanStripComponent._solo_value', source)
        self.assertNotIn('SpecialChanStripComponent._mute_value', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
