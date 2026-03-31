# tests/test_05_send_mode_toggle_momentary.py
# TDD tests for EncModeSelectorComponent Send mode toggle/momentary state machine.
# Run outside Ableton Live using stub objects.

import sys
import os
import unittest
import types

# ---------------------------------------------------------------------------
# Stubs for _Framework dependencies that EncModeSelectorComponent imports.
# Injected before the import so the module resolves cleanly outside Live.
# ---------------------------------------------------------------------------

LONG_PRESS_DELAY = 4  # mirrors constant to be defined in EncModeSelectorComponent


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
    """Minimal channel strip stub."""

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
# Inject stubs into sys.modules before importing EncModeSelectorComponent.
# ---------------------------------------------------------------------------

def _inject_stubs():
    # Stub Live module so pytest can collect without Ableton installed
    if 'Live' not in sys.modules:
        sys.modules['Live'] = types.ModuleType('Live')

    framework_pkg = sys.modules.setdefault('_Framework', types.ModuleType('_Framework'))

    # ModeSelectorComponent
    if '_Framework.ModeSelectorComponent' not in sys.modules:
        mod = types.ModuleType('_Framework.ModeSelectorComponent')
        mod.ModeSelectorComponent = _ModeSelectorComponentStub
        sys.modules['_Framework.ModeSelectorComponent'] = mod
        framework_pkg.ModeSelectorComponent = mod
    else:
        sys.modules['_Framework.ModeSelectorComponent'].ModeSelectorComponent = _ModeSelectorComponentStub

    # ButtonElement
    if '_Framework.ButtonElement' not in sys.modules:
        mod = types.ModuleType('_Framework.ButtonElement')
        mod.ButtonElement = _ButtonElementStub
        sys.modules['_Framework.ButtonElement'] = mod
        framework_pkg.ButtonElement = mod
    else:
        sys.modules['_Framework.ButtonElement'].ButtonElement = _ButtonElementStub

    # MixerComponent
    if '_Framework.MixerComponent' not in sys.modules:
        mod = types.ModuleType('_Framework.MixerComponent')
        mod.MixerComponent = _MixerComponentStub
        sys.modules['_Framework.MixerComponent'] = mod
        framework_pkg.MixerComponent = mod
    else:
        sys.modules['_Framework.MixerComponent'].MixerComponent = _MixerComponentStub


_inject_stubs()

# Add project root so EncModeSelectorComponent is importable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from EncModeSelectorComponent import EncModeSelectorComponent  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_component():
    """Create an EncModeSelectorComponent with 4 ButtonStubs wired as mode buttons."""
    mixer = _MixerComponentStub()
    comp = EncModeSelectorComponent(mixer)
    buttons = tuple(_ButtonElementStub() for _ in range(4))
    comp.set_modes_buttons(buttons)
    return comp, buttons


def tick(component, n):
    """Call component._on_timer() n times."""
    for _ in range(n):
        component._on_timer()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestSendModeToggleMomentary(unittest.TestCase):

    def test_tc01_press_down_sets_mode_and_starts_countdown(self):
        """TC-01 (SEND-03): Press-down on Send A immediately sets mode AND starts countdown."""
        comp, buttons = make_component()
        # Press Send A (index 1) — value=127
        comp._mode_value(127, buttons[1])
        self.assertEqual(comp._mode_index, 1, "mode should switch to 1 on press-down")
        self.assertEqual(comp._send_ticks_delay, LONG_PRESS_DELAY,
                         "_send_ticks_delay should start at LONG_PRESS_DELAY on press-down")

    def test_tc02_short_press_does_not_revert_mode(self):
        """TC-02 (SEND-01): Short press — release before timer fires does NOT revert mode."""
        comp, buttons = make_component()
        comp._mode_value(127, buttons[1])  # press Send A
        tick(comp, 3)                       # 3 ticks < LONG_PRESS_DELAY (4)
        comp._mode_value(0, buttons[1])    # release
        self.assertEqual(comp._mode_index, 1, "mode should stay at 1 after short press")
        self.assertFalse(comp._send_momentary_active,
                         "_send_momentary_active must be False after short-press release")

    def test_tc03_long_press_reverts_to_pan_on_release(self):
        """TC-03 (SEND-02): Long press — timer fires, release reverts to Pan (mode 0)."""
        comp, buttons = make_component()
        comp._mode_value(127, buttons[2])          # press Send B (index 2)
        tick(comp, LONG_PRESS_DELAY + 1)           # tick past threshold
        self.assertTrue(comp._send_momentary_active,
                        "_send_momentary_active should be True after timer fires")
        comp._mode_value(0, buttons[2])            # release
        self.assertEqual(comp._mode_index, 0,
                         "mode should revert to Pan (0) after long-press release")
        self.assertFalse(comp._send_momentary_active,
                         "_send_momentary_active must be False after revert")

    def test_tc04_long_press_on_active_send_mode_reverts_to_pan(self):
        """TC-04 (SEND-04): Long press on already-active Send mode — reverts to Pan on release."""
        comp, buttons = make_component()
        comp.set_mode(1)                           # pre-activate Send A
        comp._mode_value(127, buttons[1])          # press Send A again
        # set_mode(1) still fires (same mode index, value != 0)
        self.assertEqual(comp._mode_index, 1, "mode should remain 1 after press-down")
        tick(comp, LONG_PRESS_DELAY + 1)
        self.assertTrue(comp._send_momentary_active)
        comp._mode_value(0, buttons[1])            # release
        self.assertEqual(comp._mode_index, 0,
                         "long-press release should revert to Pan (0) regardless of prior mode")
        self.assertFalse(comp._send_momentary_active)

    def test_tc05_pan_button_does_not_set_send_ticks_delay(self):
        """TC-05: Pan button press (mode 0) does NOT set _send_ticks_delay."""
        comp, buttons = make_component()
        comp._mode_value(127, buttons[0])          # press Pan
        self.assertEqual(comp._send_ticks_delay, -1,
                         "_send_ticks_delay must stay -1 when Pan button pressed")

    def test_tc06_timer_idle_no_side_effects(self):
        """TC-06: _on_timer with _send_ticks_delay == -1 has no side effects."""
        comp, buttons = make_component()
        tick(comp, 5)
        self.assertFalse(comp._send_momentary_active)
        self.assertEqual(comp._mode_index, 0)

    def test_tc07_disconnect_resets_send_state(self):
        """TC-07: disconnect() resets _send_ticks_delay and _send_momentary_active."""
        comp, buttons = make_component()
        comp._mode_value(127, buttons[1])
        tick(comp, LONG_PRESS_DELAY + 1)
        self.assertTrue(comp._send_momentary_active)
        comp.disconnect()
        self.assertEqual(comp._send_ticks_delay, -1,
                         "_send_ticks_delay must be -1 after disconnect")
        self.assertFalse(comp._send_momentary_active,
                         "_send_momentary_active must be False after disconnect")

    def test_tc08_on_enabled_changed_mid_hold_reverts_mode(self):
        """TC-08 (D-10): on_enabled_changed() mid-hold reverts mode and clears send state."""
        comp, buttons = make_component()
        comp._mode_value(127, buttons[1])          # press Send A
        tick(comp, LONG_PRESS_DELAY + 1)           # fire momentary
        self.assertTrue(comp._send_momentary_active)
        comp._enabled = False                      # simulate shift press disabling component
        comp.on_enabled_changed()
        self.assertEqual(comp._send_ticks_delay, -1,
                         "_send_ticks_delay must be -1 after on_enabled_changed")
        self.assertFalse(comp._send_momentary_active,
                         "_send_momentary_active must be False after on_enabled_changed")
        self.assertEqual(comp._mode_index, 0,
                         "mode must revert to Pan (0) after on_enabled_changed mid-hold")


if __name__ == '__main__':
    unittest.main()
