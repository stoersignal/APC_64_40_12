# tests/test_04_pan16_device.py
# TDD tests for Pan16DeviceComponent bank-fix behavior.
# Run outside Ableton Live using stub objects.

import sys
import os
import unittest

# ---------------------------------------------------------------------------
# Minimal stub replacing _Framework.DeviceComponent so tests can run outside
# Ableton Live.  Simulates the bank-reset behaviour described in the plan:
# on set_device(), _bank_index is always reset to 0 for an unseen device.
# ---------------------------------------------------------------------------

class _DeviceComponentStub:
    """Simulates DeviceComponent's set_device() bank-reset trap."""

    def __init__(self):
        self._bank_index = 0
        self._device = None
        self._parameter_controls = None
        self._update_called = 0

    def set_device(self, device):
        # Simulate the parent resetting _bank_index to 0 for every new device
        self._bank_index = 0
        self._device = device
        self._update_called += 1

    def set_parameter_controls(self, controls):
        self._parameter_controls = controls
        self._update_called += 1

    def update(self):
        self._update_called += 1


# ---------------------------------------------------------------------------
# Insert stub into sys.modules before importing Pan16DeviceComponent so that
# `from _Framework.DeviceComponent import DeviceComponent` resolves to our stub.
# ---------------------------------------------------------------------------

import types

# Only inject stubs if not already present (allow re-running tests)
if '_Framework.DeviceComponent' not in sys.modules:
    _framework_pkg = types.ModuleType('_Framework')
    _device_mod = types.ModuleType('_Framework.DeviceComponent')
    _device_mod.DeviceComponent = _DeviceComponentStub
    sys.modules.setdefault('_Framework', _framework_pkg)
    sys.modules['_Framework.DeviceComponent'] = _device_mod
else:
    # Replace DeviceComponent with our stub for these tests
    sys.modules['_Framework.DeviceComponent'].DeviceComponent = _DeviceComponentStub

# Add project root to path so Pan16DeviceComponent.py is importable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Re-import to pick up the stub (in case module was cached from previous run)
if 'Pan16DeviceComponent' in sys.modules:
    del sys.modules['Pan16DeviceComponent']

from Pan16DeviceComponent import Pan16DeviceComponent

# Add tests directory to path for stubs
_tests_dir = os.path.dirname(os.path.abspath(__file__))
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

from framework_stubs import DeviceStub, EncoderStub


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPan16DeviceComponentBankFix(unittest.TestCase):

    def test_bank0_instance_holds_bank_0_after_set_device(self):
        """bank_index=0 instance must stay at bank 0 after set_device()."""
        comp = Pan16DeviceComponent(bank_index=0)
        dev = DeviceStub()
        comp.set_device(dev)
        self.assertEqual(comp._bank_index, 0,
                         f"Expected _bank_index=0, got {comp._bank_index}")

    def test_bank1_instance_holds_bank_1_after_set_device(self):
        """bank_index=1 instance must re-assert bank 1 after parent resets it."""
        comp = Pan16DeviceComponent(bank_index=1)
        dev = DeviceStub()
        comp.set_device(dev)
        self.assertEqual(comp._bank_index, 1,
                         f"Expected _bank_index=1, got {comp._bank_index}")

    def test_bank1_holds_after_second_different_device(self):
        """bank_index=1 must survive a second set_device() call with a new device."""
        comp = Pan16DeviceComponent(bank_index=1)
        dev_a = DeviceStub(num_params=16)
        dev_b = DeviceStub(num_params=8)
        comp.set_device(dev_a)
        comp.set_device(dev_b)
        self.assertEqual(comp._bank_index, 1,
                         f"Expected _bank_index=1 after second set_device, got {comp._bank_index}")

    def test_two_instances_are_independent(self):
        """Two instances targeting the same device must have independent _bank_index."""
        instance_a = Pan16DeviceComponent(bank_index=0)
        instance_b = Pan16DeviceComponent(bank_index=1)
        dev = DeviceStub()
        instance_a.set_device(dev)
        instance_b.set_device(dev)
        self.assertEqual(instance_a._bank_index, 0,
                         f"instance_a expected _bank_index=0, got {instance_a._bank_index}")
        self.assertEqual(instance_b._bank_index, 1,
                         f"instance_b expected _bank_index=1, got {instance_b._bank_index}")

    def test_set_parameter_controls_none_does_not_crash(self):
        """set_parameter_controls(None) must not raise any exception."""
        comp = Pan16DeviceComponent(bank_index=0)
        comp.set_parameter_controls(None)
        self.assertIsNone(comp._parameter_controls)

    def test_set_device_none_does_not_crash(self):
        """set_device(None) must not raise any exception."""
        comp = Pan16DeviceComponent(bank_index=1)
        # Should complete without raising
        comp.set_device(None)

    def test_fixed_bank_index_stored_on_init(self):
        """_fixed_bank_index must be stored correctly on __init__."""
        comp0 = Pan16DeviceComponent(bank_index=0)
        comp1 = Pan16DeviceComponent(bank_index=1)
        self.assertEqual(comp0._fixed_bank_index, 0)
        self.assertEqual(comp1._fixed_bank_index, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
