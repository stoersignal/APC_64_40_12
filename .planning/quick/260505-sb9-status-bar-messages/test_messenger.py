#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit-test harness for StatusBarMessenger. Quick task 260505-sb9 Task 1b.

Runs OUTSIDE Ableton -- StatusBarMessenger.py imports nothing from Live
or _Framework. Verifies all seven behaviours specified in PLAN Task 1b:

  1. Cold-start silence (calls within COLD_START_QUIET_MS drop)
  2. Identical-text dedup (back-to-back same text -> single emit)
  3. show_param throttle (rapid same-param -> single emit)
  4. show_param different param_id within window -> emits
  5. Mode events bypass throttle
  6. show_event honors dedup + cold-start
  7. make_hardware_value_callback factory builds working callbacks

Stdlib only -- project pattern is "tests run directly via python3"
(see STATE.md Phase 5 decisions). Place all asserts at module top
level so a failure raises AssertionError with the offending state.

Exits 0 + prints "Task 1 OK" if all asserts pass.
"""

import os
import sys
import time

# Inject repo root into sys.path so `from StatusBarMessenger import ...`
# works regardless of where the test runner is invoked from. Repo root
# is two directories above this file (.planning/quick/<id>/).
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from StatusBarMessenger import StatusBarMessenger


# --- Test doubles -------------------------------------------------------

class FakeApp(object):
    """Records every show_message call. Stand-in for Live.Application.Application."""
    def __init__(self):
        self.messages = []  # list of strings, in emission order

    def show_message(self, text):
        self.messages.append(text)


class FakeParent(object):
    """Stand-in for the ControlSurface; provides .application()."""
    def __init__(self):
        self.app = FakeApp()

    def application(self):
        return self.app


class FakeParam(object):
    """Stand-in for a Live DeviceParameter -- enough surface for
    make_hardware_value_callback to format via str_for_value."""
    def __init__(self, name, value, formatter=None):
        self.name = name
        self.original_name = name
        self.value = value
        self._formatter = formatter or (lambda v: str(v))

    def str_for_value(self, value):
        return self._formatter(value)


# --- Helpers ------------------------------------------------------------

def make_warm_messenger(parent):
    """Build a messenger and rewind its construction time so cold-start
    silence is no longer in effect. Saves us 2.1s of real-time sleep
    per assertion block."""
    m = StatusBarMessenger(parent)
    m._construct_ms = m._now_ms() - (StatusBarMessenger.COLD_START_QUIET_MS + 100)
    return m


# === Test 1: cold-start silence ========================================
parent = FakeParent()
m = StatusBarMessenger(parent)
m.show_mode('Test Mode', True)
m.show_event('cold event')
m.show_param('Cutoff', '1.20 kHz', param_id=1)
assert parent.app.messages == [], (
    'cold-start should drop all messages, got: ' + repr(parent.app.messages))


# === Test 2: identical-text dedup =====================================
parent = FakeParent()
m = make_warm_messenger(parent)
m.show_mode('Drum Rack Mode', True)
m.show_mode('Drum Rack Mode', True)  # identical -> dropped
m.show_mode('Drum Rack Mode', True)  # identical -> dropped
assert parent.app.messages == ['Drum Rack Mode'], (
    'identical-text dedup failed, got: ' + repr(parent.app.messages))


# === Test 3: show_param throttle (same param within window) ===========
parent = FakeParent()
m = make_warm_messenger(parent)
# Five rapid same-param emissions. THROTTLE_MS=50; we fire them within
# microseconds of each other so all but the first are throttled.
m.show_param('Cutoff', '1.20 kHz', param_id=42)
m.show_param('Cutoff', '1.21 kHz', param_id=42)
m.show_param('Cutoff', '1.22 kHz', param_id=42)
m.show_param('Cutoff', '1.23 kHz', param_id=42)
m.show_param('Cutoff', '1.24 kHz', param_id=42)
assert len(parent.app.messages) == 1, (
    'throttle should drop 4 of 5 same-param rapid calls, got: '
    + repr(parent.app.messages))
assert parent.app.messages[0] == 'Cutoff: 1.20 kHz'


# === Test 4: different param_id within throttle window emits ==========
parent = FakeParent()
m = make_warm_messenger(parent)
m.show_param('Cutoff', '1.20 kHz', param_id=42)
m.show_param('Resonance', '0.50', param_id=43)  # different id -> emit
assert len(parent.app.messages) == 2, (
    'different param_id should emit immediately even within throttle '
    'window, got: ' + repr(parent.app.messages))
assert parent.app.messages == ['Cutoff: 1.20 kHz', 'Resonance: 0.50']


# === Test 5: mode events bypass throttle ==============================
# Mode events are infrequent and should never be silenced by the
# show_param throttle state -- show_param doesn't share its throttle
# clock with show_mode.
parent = FakeParent()
m = make_warm_messenger(parent)
m.show_param('Cutoff', '1.20 kHz', param_id=42)
m.show_mode('AutoFilter Mode', True)
m.show_mode('AutoFilter Mode', False)
assert parent.app.messages == [
    'Cutoff: 1.20 kHz', 'AutoFilter Mode', 'AutoFilter Mode exited',
], 'mode events should not be throttled, got: ' + repr(parent.app.messages)


# === Test 6: show_event dedup + post-dedup-window re-emit =============
parent = FakeParent()
m = make_warm_messenger(parent)
m.show_event('Snapshot 5 stored')
m.show_event('Snapshot 5 stored')  # dedup
assert parent.app.messages == ['Snapshot 5 stored'], (
    'show_event dedup failed, got: ' + repr(parent.app.messages))
# Slide the dedup clock back to simulate the window expiring (avoids a
# real-time sleep). Use a value safely past DEDUP_WINDOW_MS so the
# expiry branch in _check_dedup fires.
m._last_text_ms = m._now_ms() - (StatusBarMessenger.DEDUP_WINDOW_MS + 50)
m.show_event('Snapshot 5 stored')  # window expired -> re-emit
assert parent.app.messages == ['Snapshot 5 stored', 'Snapshot 5 stored'], (
    'after dedup window expiry, identical text should re-emit, got: '
    + repr(parent.app.messages))


# === Test 7: make_hardware_value_callback ==============================
# The callback should: read the param via param_provider() at fire-time,
# format via str_for_value, dispatch to show_param.
parent = FakeParent()
m = make_warm_messenger(parent)
param = FakeParam('Volume', -6.3, formatter=lambda v: '%.1f dB' % v)
cb = m.make_hardware_value_callback(lambda: param)
cb(64)  # MIDI value -- callback ignores it; reads param.value at fire-time.
assert parent.app.messages == ['Volume: -6.3 dB'], (
    'hardware callback emit failed, got: ' + repr(parent.app.messages))

# Provider returning None -> no emit, no crash.
parent = FakeParent()
m = make_warm_messenger(parent)
cb_none = m.make_hardware_value_callback(lambda: None)
cb_none(64)
assert parent.app.messages == [], (
    'hardware callback with None provider should be a no-op, got: '
    + repr(parent.app.messages))

# Param whose str_for_value raises -> repr fallback.
class _RaisingFormatter(FakeParam):
    def str_for_value(self, value):
        raise RuntimeError('boom')
parent = FakeParent()
m = make_warm_messenger(parent)
raising = _RaisingFormatter('Q', 0.707)
cb = m.make_hardware_value_callback(lambda: raising)
cb(64)
# repr(0.707) is '0.707' on Python 3, so we expect 'Q: 0.707'.
assert parent.app.messages == ['Q: 0.707'], (
    'hardware callback should fall back to repr on str_for_value '
    'failure, got: ' + repr(parent.app.messages))


# Multiple different params via the same factory -- exercises the
# id(param)-based throttle: two callbacks, two distinct ids, both emit.
parent = FakeParent()
m = make_warm_messenger(parent)
p1 = FakeParam('Vol', -6.3, formatter=lambda v: '%.1f dB' % v)
p2 = FakeParam('Pan', 0.5,  formatter=lambda v: '%dR' % int(v * 100))
cb1 = m.make_hardware_value_callback(lambda: p1)
cb2 = m.make_hardware_value_callback(lambda: p2)
cb1(64)
cb2(64)
assert parent.app.messages == ['Vol: -6.3 dB', 'Pan: 50R'], (
    'two different-param callbacks within throttle window should both '
    'emit, got: ' + repr(parent.app.messages))


print('Task 1 OK')
