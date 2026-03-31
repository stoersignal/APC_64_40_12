# tests/test_05_mint03_isolation.py
# MINT-03 isolation tests: Send mode state machine (EncModeSelectorComponent) and
# Solo/Mute state machines (ToggleMomentaryChannelStripComponent) operate independently.
# No shared state, no callback cross-contamination.
# Run outside Ableton Live using stub objects.

import sys
import os
import unittest
import types
import importlib.util

# ---------------------------------------------------------------------------
# Stubs for _Framework dependencies that both components import.
# Injected before any component import.
# ---------------------------------------------------------------------------

LONG_PRESS_DELAY = 4  # mirrors constant in both EncModeSelectorComponent and ToggleMomentaryChannelStripComponent

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.framework_stubs import TrackStub, SongStub, ButtonStub, SpecialChanStripStub


class _ButtonElementStub:
    """Minimal ButtonElement stub — is_momentary returns True."""

    def __init__(self):
        self._state = 0

    def is_momentary(self):
        return True

    def turn_on(self):
        self._state = 1

    def turn_off(self):
        self._state = 0

    def add_value_listener(self, callback, identify_sender=False):
        pass

    def remove_value_listener(self, callback):
        pass


class _ChanStripStub:
    """Minimal channel strip stub for EncModeSelectorComponent's mixer."""

    def set_pan_control(self, control):
        pass

    def set_send_controls(self, controls):
        pass


class _MixerComponentStub:
    """Minimal MixerComponent stub — returns ChanStripStub for any index."""

    def channel_strip(self, index):
        return _ChanStripStub()


class _ModeSelectorComponentStub:
    """Minimal ModeSelectorComponent stub with timer registration and mode tracking."""

    def __init__(self):
        self._modes_buttons = []
        self._mode_index = 0
        self._enabled = True
        self._timer_callback = None

    def set_mode(self, index):
        self._mode_index = index

    def is_enabled(self):
        return self._enabled

    def update(self):
        pass

    def _register_timer_callback(self, cb):
        self._timer_callback = cb

    def _unregister_timer_callback(self, cb):
        self._timer_callback = None

    def set_modes_buttons(self, buttons):
        self._modes_buttons = list(buttons) if buttons else []

    def disconnect(self):
        pass

    def number_of_modes(self):
        return 4


# ---------------------------------------------------------------------------
# Inject stubs into sys.modules before importing components.
# ---------------------------------------------------------------------------

def _inject_enc_stubs():
    """Inject stubs needed by EncModeSelectorComponent."""
    if 'Live' not in sys.modules:
        sys.modules['Live'] = types.ModuleType('Live')

    framework_pkg = sys.modules.setdefault('_Framework', types.ModuleType('_Framework'))

    # ModeSelectorComponent
    mod = sys.modules.setdefault('_Framework.ModeSelectorComponent', types.ModuleType('_Framework.ModeSelectorComponent'))
    mod.ModeSelectorComponent = _ModeSelectorComponentStub
    framework_pkg.ModeSelectorComponent = mod

    # ButtonElement
    mod = sys.modules.setdefault('_Framework.ButtonElement', types.ModuleType('_Framework.ButtonElement'))
    mod.ButtonElement = _ButtonElementStub
    framework_pkg.ButtonElement = mod

    # MixerComponent
    mod = sys.modules.setdefault('_Framework.MixerComponent', types.ModuleType('_Framework.MixerComponent'))
    mod.MixerComponent = _MixerComponentStub
    framework_pkg.MixerComponent = mod


def _inject_strip_stubs():
    """Inject stubs needed by ToggleMomentaryChannelStripComponent (via SpecialChanStripComponent)."""
    framework_pkg = sys.modules.setdefault('_Framework', types.ModuleType('_Framework'))

    # ChannelStripComponent — used as base class by SpecialChanStripComponent
    chan_strip_mod = sys.modules.setdefault(
        '_Framework.ChannelStripComponent',
        types.ModuleType('_Framework.ChannelStripComponent')
    )

    class _FakeChannelStripComponent(SpecialChanStripStub):
        pass

    chan_strip_mod.ChannelStripComponent = _FakeChannelStripComponent
    framework_pkg.ChannelStripComponent = chan_strip_mod

    # EncoderElement — imported by SpecialChanStripComponent
    enc_mod = sys.modules.setdefault(
        '_Framework.EncoderElement',
        types.ModuleType('_Framework.EncoderElement')
    )

    class _FakeEncoderElement:
        pass

    enc_mod.EncoderElement = _FakeEncoderElement
    framework_pkg.EncoderElement = enc_mod


_inject_enc_stubs()
_inject_strip_stubs()

# Add project root so both components are importable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from EncModeSelectorComponent import EncModeSelectorComponent  # noqa: E402


# ToggleMomentaryChannelStripComponent uses a relative import for SpecialChanStripComponent.
# Load it via spec with __package__ set so the relative import resolves to our stub.

def _load_strip_module():
    """Load ToggleMomentaryChannelStripComponent with stub base class."""
    pkg_mod = sys.modules.setdefault('APC_64_40_12', types.ModuleType('APC_64_40_12'))
    pkg_mod.__path__ = [_project_root]

    special_mod = sys.modules.setdefault(
        'APC_64_40_12.SpecialChanStripComponent',
        types.ModuleType('APC_64_40_12.SpecialChanStripComponent')
    )
    special_mod.SpecialChanStripComponent = SpecialChanStripStub

    module_path = os.path.join(_project_root, 'ToggleMomentaryChannelStripComponent.py')
    spec = importlib.util.spec_from_file_location(
        'ToggleMomentaryChannelStripComponent',
        module_path,
        submodule_search_locations=[]
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = 'APC_64_40_12'
    spec.loader.exec_module(mod)
    return mod


_strip_module = _load_strip_module()
ToggleMomentaryChannelStripComponent = _strip_module.ToggleMomentaryChannelStripComponent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_enc():
    """Create an EncModeSelectorComponent with 4 _ButtonElementStubs wired as mode buttons."""
    mixer = _MixerComponentStub()
    enc = EncModeSelectorComponent(mixer)
    buttons = tuple(_ButtonElementStub() for _ in range(4))
    enc.set_modes_buttons(buttons)
    return enc, buttons


def make_strip(track=None):
    """Create a ToggleMomentaryChannelStripComponent with an optional TrackStub."""
    strip = ToggleMomentaryChannelStripComponent()
    strip._enabled = True
    strip._track = track if track is not None else TrackStub(solo=False, mute=False)
    strip._song._master_track = TrackStub()
    return strip


def tick_enc(enc, n):
    """Call enc._on_timer() n times."""
    for _ in range(n):
        enc._on_timer()


def tick_strip(strip, n):
    """Call strip._on_timer() n times."""
    for _ in range(n):
        strip._on_timer()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestMint03Isolation(unittest.TestCase):
    """MINT-03: Send mode state machine and Solo/Mute state machines are fully independent."""

    def test_tc_mint_01_send_long_press_does_not_mutate_solo_momentary(self):
        """TC-MINT-01: Long press Send A does not mutate _solo_momentary_active on any channel strip."""
        enc, buttons = make_enc()
        track_1 = TrackStub(solo=True)   # strip_1 has an active solo state
        strip_1 = make_strip(track=track_1)
        track_2 = TrackStub(solo=False)
        strip_2 = make_strip(track=track_2)

        # Simulate long press on Send A (index 1)
        enc._mode_value(127, buttons[1])
        tick_enc(enc, LONG_PRESS_DELAY + 1)

        self.assertTrue(enc._send_momentary_active,
                        "enc._send_momentary_active must be True after long press threshold")
        self.assertFalse(strip_1._solo_momentary_active,
                         "strip_1._solo_momentary_active must be unchanged (False)")
        self.assertFalse(strip_2._solo_momentary_active,
                         "strip_2._solo_momentary_active must be unchanged (False)")
        self.assertTrue(strip_1._track.solo,
                        "strip_1._track.solo must be unchanged — Send mode press must not touch track state")

    def test_tc_mint_02_solo_long_press_does_not_mutate_send_momentary(self):
        """TC-MINT-02: Solo long-press on a strip does not mutate enc._send_momentary_active."""
        enc, buttons = make_enc()
        enc.set_mode(1)   # pre-activate Send A

        track_1 = TrackStub(solo=False)
        strip_1 = make_strip(track=track_1)

        # Simulate long solo press on strip_1
        strip_1._solo_value(127)
        tick_strip(strip_1, LONG_PRESS_DELAY + 1)

        self.assertTrue(strip_1._solo_momentary_active,
                        "strip_1._solo_momentary_active must be True after long press threshold")
        self.assertFalse(enc._send_momentary_active,
                         "enc._send_momentary_active must be False — strip solo press must not touch enc state")
        self.assertEqual(enc._mode_index, 1,
                         "enc._mode_index must remain 1 — strip solo press must not change mode")

    def test_tc_mint_03_simultaneous_long_holds_progress_independently(self):
        """TC-MINT-03: Simultaneous long holds — both state machines progress independently."""
        enc, buttons = make_enc()
        track_1 = TrackStub(solo=False)
        strip_1 = make_strip(track=track_1)

        # Start both presses simultaneously
        enc._mode_value(127, buttons[2])   # press Send B (index 2)
        strip_1._solo_value(127)           # press solo on strip_1

        # Tick both state machines past threshold
        for _ in range(LONG_PRESS_DELAY + 1):
            enc._on_timer()
            strip_1._on_timer()

        self.assertTrue(enc._send_momentary_active,
                        "enc._send_momentary_active must be True after simultaneous long hold")
        self.assertTrue(strip_1._solo_momentary_active,
                        "strip_1._solo_momentary_active must be True after simultaneous long hold")

        # Release both
        enc._mode_value(0, buttons[2])     # release Send B — should revert to mode 0
        strip_1._solo_value(0)             # release solo — should revert track.solo to False

        self.assertEqual(enc._mode_index, 0,
                         "enc._mode_index must revert to Pan (0) after long-press release")
        self.assertFalse(strip_1._track.solo,
                         "strip_1._track.solo must revert to False after long-press release")

    def test_tc_mint_04_two_channel_strips_are_independent(self):
        """TC-MINT-04: Two channel strips are independent — long press solo on strip_1 does not affect strip_2."""
        track_1 = TrackStub(solo=False)
        track_2 = TrackStub(solo=False)
        strip_1 = make_strip(track=track_1)
        strip_2 = make_strip(track=track_2)

        # Long press solo on strip_1 only
        strip_1._solo_value(127)
        tick_strip(strip_1, LONG_PRESS_DELAY + 1)

        self.assertTrue(strip_1._solo_momentary_active,
                        "strip_1._solo_momentary_active must be True after long hold")
        self.assertFalse(strip_2._solo_momentary_active,
                         "strip_2._solo_momentary_active must remain False throughout")

        # Verify state variable independence — modifying strip_1 must not affect strip_2
        self.assertEqual(strip_2._solo_ticks_delay, -1,
                         "strip_2._solo_ticks_delay must be independent of strip_1")


if __name__ == '__main__':
    unittest.main()
