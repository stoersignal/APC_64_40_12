---
phase: 05-toggle-momentary-send-mode-buttons
plan: 01
subsystem: encoder-mode-selector
tags: [python, tdd, toggle-momentary, send-mode, state-machine, encoder-selector]

# Dependency graph
requires:
  - 04-03-SUMMARY.md (EncModeSelectorComponent with on_enabled_changed)
provides:
  - EncModeSelectorComponent.py — Send mode toggle/momentary state machine
  - tests/test_05_send_mode_toggle_momentary.py — 8 unit tests verifying state machine
affects:
  - Phase 05 plan 02 (if any follow-on plans)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD outside Ableton Live: sys.modules injection for _Framework and Live stubs"
    - "Toggle/momentary state machine: _send_ticks_delay countdown + _send_momentary_active flag"
    - "Shift guard in on_enabled_changed(): revert mode and clear state when disabled mid-hold (D-10)"

key-files:
  created:
    - tests/test_05_send_mode_toggle_momentary.py
  modified:
    - EncModeSelectorComponent.py

key-decisions:
  - "LONG_PRESS_DELAY = 4 defined locally in EncModeSelectorComponent.py (not imported from ToggleMomentaryChannelStripComponent) — avoids cross-file import"
  - "Revert target hardcoded to mode 0 (Pan) — D-04: no _mode_before_send_press needed"
  - "Pan button (mode 0) keeps existing pan-to-vol toggle behavior unchanged — D-06"
  - "Tests run via python3 tests/test_file.py (not pytest) matching project established pattern"

metrics:
  duration: "5 minutes"
  completed: "2026-03-31T21:44:40Z"
  tasks_completed: 2
  files_changed: 2
---

# Phase 05 Plan 01: Send Mode Toggle/Momentary State Machine Summary

**One-liner:** Toggle/momentary dual-behavior for Send A/B/C mode buttons using `_send_ticks_delay` countdown + `_send_momentary_active` flag in EncModeSelectorComponent (400ms LONG_PRESS_DELAY, reverts to Pan on release).

## What Was Built

Implemented toggle/momentary dual-behavior for Send A, Send B, and Send C mode buttons (indices 1-3) in `EncModeSelectorComponent`. Short press (<400ms) permanently switches encoder mode with no revert. Long press (>=400ms) activates mode at press-down and reverts to Pan mode (mode 0) on release. Shift press mid-hold cleanly reverts mode via `on_enabled_changed()`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED — Write failing tests for Send mode state machine | 90022b9 | tests/test_05_send_mode_toggle_momentary.py |
| 2 | GREEN — Implement Send mode state machine | 6a15755 | EncModeSelectorComponent.py |

## Implementation Details

### New state variables (`__init__`):
- `self._send_ticks_delay = -1` — countdown, -1 = inactive
- `self._send_momentary_active = False` — True after threshold fires

### Constant:
- `LONG_PRESS_DELAY = 4` — defined locally (4 ticks x 100ms = 400ms)

### `_mode_value` changes:
- Press-down on index >= 1: `set_mode(index)` fires immediately + `_send_ticks_delay = LONG_PRESS_DELAY`
- Release on index >= 1: if `_send_momentary_active`, revert to `set_mode(0)` + clear flag; always reset `_send_ticks_delay = -1`

### `_on_timer` addition:
- Countdown block after existing `_pan_to_vol_ticks_delay` block; sets `_send_momentary_active = True` when countdown reaches 0

### `disconnect()` addition:
- Resets `_send_ticks_delay = -1` and `_send_momentary_active = False`

### `on_enabled_changed()` addition (D-10 shift guard):
- In `if not self.is_enabled():` branch: reset countdown, revert mode to 0 if momentary was active

## Test Coverage

8 tests, all passing:
- TC-01: Press-down sets mode immediately and starts countdown (SEND-03)
- TC-02: Short press does not revert mode (SEND-01)
- TC-03: Long press reverts to Pan on release (SEND-02)
- TC-04: Long press on already-active Send mode reverts to Pan on release (SEND-04)
- TC-05: Pan button press does not set `_send_ticks_delay`
- TC-06: Timer idle has no side effects
- TC-07: `disconnect()` resets send state
- TC-08: `on_enabled_changed()` mid-hold reverts mode and clears state (D-10)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added Live stub injection to test file for pytest compatibility**
- **Found during:** Task 1
- **Issue:** `pytest` cannot collect tests when root `__init__.py` imports `Live` (not available outside Ableton). The `--import-mode=importlib` flag did not resolve the issue since pytest loads conftest before stubs can be injected.
- **Fix:** Added `sys.modules['Live'] = types.ModuleType('Live')` inside `_inject_stubs()` in the test file. Tests run correctly via `python3 tests/test_05.py` (established project pattern from Phase 4).
- **Files modified:** `tests/test_05_send_mode_toggle_momentary.py`
- **Commit:** 90022b9

## Known Stubs

None — all state machine paths are fully wired and tested.

## Self-Check: PASSED

- FOUND: tests/test_05_send_mode_toggle_momentary.py
- FOUND: EncModeSelectorComponent.py (with LONG_PRESS_DELAY, _send_ticks_delay, _send_momentary_active)
- FOUND commit 90022b9 (RED phase)
- FOUND commit 6a15755 (GREEN phase)
- All 8 tests pass: `python3 tests/test_05_send_mode_toggle_momentary.py` → OK
- Full suite (76 tests across 5 files) → all pass, zero regressions
