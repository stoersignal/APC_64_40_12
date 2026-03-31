---
phase: 05-toggle-momentary-send-mode-buttons
plan: 02
subsystem: isolation-verification
tags: [python, tdd, toggle-momentary, send-mode, isolation, mint-03]

# Dependency graph
requires:
  - 05-01-SUMMARY.md (EncModeSelectorComponent Send mode state machine)
  - tests/test_05_send_mode_toggle_momentary.py (enc stub injection pattern)
  - tests/framework_stubs.py (SpecialChanStripStub and TrackStub)
provides:
  - tests/test_05_mint03_isolation.py — 4 MINT-03 isolation tests proving state independence
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Isolation testing via two independently instantiated components with no shared state"
    - "Simultaneous tick-stepping of two independent state machines in a single test loop"
    - "Strip module loaded via importlib.util.spec_from_file_location with __package__ override for relative import resolution"
    - "Tests run via python3 tests/test_file.py (established project pattern — pytest blocked by root __init__.py importing Live)"

key-files:
  created:
    - tests/test_05_mint03_isolation.py
  modified: []

key-decisions:
  - "Tests run directly via python3 (not pytest) — root __init__.py imports Live which fails outside Ableton; this is the established project pattern from Phase 4 and 05-01"
  - "ToggleMomentaryChannelStripComponent loaded via importlib.util with __package__='APC_64_40_12' to resolve relative import from .SpecialChanStripComponent"
  - "No shared class-level state confirmed — EncModeSelectorComponent._send_momentary_active and ToggleMomentaryChannelStripComponent._solo/_mute_momentary_active are all per-instance variables"

metrics:
  duration: "6 minutes"
  completed: "2026-03-31T22:37:00Z"
  tasks_completed: 1
  files_changed: 1
---

# Phase 05 Plan 02: MINT-03 Isolation Verification Summary

**One-liner:** Four isolation tests prove EncModeSelectorComponent._send_momentary_active and ToggleMomentaryChannelStripComponent._solo/_mute_momentary_active are fully independent per-instance state machines with zero cross-contamination.

## What Was Built

Created `tests/test_05_mint03_isolation.py` with 4 tests that verify MINT-03: Send mode toggle/momentary state machine in `EncModeSelectorComponent` and Solo/Mute toggle/momentary state machines in `ToggleMomentaryChannelStripComponent` operate with full isolation. No shared state, no callback cross-contamination. Tests cover: long press Send does not mutate strip solo state, long press solo does not mutate enc send state, simultaneous holds on both components progress independently, and two channel strip instances maintain independent state machines.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | MINT-03 isolation test — Send mode changes don't bleed into strip state | 895f89e | tests/test_05_mint03_isolation.py |

## Implementation Details

### Test infrastructure:

Both stub injection patterns merged:
- `_inject_enc_stubs()` — ModeSelectorComponent, ButtonElement, MixerComponent stubs for EncModeSelectorComponent
- `_inject_strip_stubs()` — ChannelStripComponent and EncoderElement stubs for SpecialChanStripComponent

`ToggleMomentaryChannelStripComponent` loaded via `importlib.util.spec_from_file_location` with `__package__ = 'APC_64_40_12'` so the relative import `from .SpecialChanStripComponent import SpecialChanStripComponent` resolves to the stub.

### Test cases:

- **TC-MINT-01:** Long press Send A (enc._mode_value(127, buttons[1]) + tick 5) → enc._send_momentary_active=True, strip_1._solo_momentary_active unchanged (False), strip_1._track.solo unchanged (True)
- **TC-MINT-02:** Pre-activate enc to mode 1, long press solo on strip_1 → strip_1._solo_momentary_active=True, enc._send_momentary_active=False, enc._mode_index=1 (unchanged)
- **TC-MINT-03:** Simultaneous press + tick-step both state machines → both momentary flags True independently; release both → enc reverts to mode 0, strip solo reverts to False
- **TC-MINT-04:** Long press solo on strip_1 → only strip_1._solo_momentary_active=True; strip_2._solo_momentary_active and strip_2._solo_ticks_delay remain at initial values

### Full suite results:

All 80 tests pass across 6 test files:
- test_task1_toggle_momentary_values.py: 20 tests
- test_task2_timer_and_shift_guards.py: 23 tests
- test_task3_multi_track.py: 18 tests
- test_04_pan16_device.py: 7 tests
- test_05_send_mode_toggle_momentary.py: 8 tests
- test_05_mint03_isolation.py: 4 tests

## Deviations from Plan

None — plan executed exactly as written. The `python3 tests/test_file.py` pattern was already the established project convention per the 05-01 SUMMARY key decision; the plan's pytest invocation line was treated as pseudocode for the verification step.

## Known Stubs

None — all isolation assertions exercise fully implemented production state machines in both components.

## Self-Check: PASSED

- FOUND: tests/test_05_mint03_isolation.py (326 lines)
- FOUND commit 895f89e
- All 4 MINT-03 isolation tests pass: python3.11 tests/test_05_mint03_isolation.py → OK
- Full suite (80 tests across 6 files) → all pass, zero regressions
- grep "TC-MINT-0" tests/test_05_mint03_isolation.py → 4 matches
- grep "_send_ticks_delay" EncModeSelectorComponent.py → 8 matches (>= 4)
- grep "LONG_PRESS_DELAY" EncModeSelectorComponent.py → 2 matches (>= 1)
- grep "_send_momentary_active" EncModeSelectorComponent.py → 7 matches (>= 4)
