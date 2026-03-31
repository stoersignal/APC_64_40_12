---
phase: 02-core-logic
verified: 2026-03-31T14:00:00Z
status: human_needed
score: 8/8 must-haves verified
re_verification: false
human_verification:
  - test: "Short tap Solo button on inactive track"
    expected: "Track solos; LED lights immediately; release before 400ms keeps it soloed"
    why_human: "MIDI timing, hardware LED response, and real-time feel cannot be verified outside Ableton Live"
  - test: "Hold Solo button on inactive track for >=400ms then release"
    expected: "Track solos at press-down, LED on; on release track reverts to unsoloed, LED off"
    why_human: "Timer-to-Live-API integration only verifiable with actual hardware and Live environment"
  - test: "Hold Solo button on already-soloed track for >=400ms then release"
    expected: "Track unsolos at press-down, LED off; on release track re-solos, LED on"
    why_human: "Confirms revert direction; requires hardware"
  - test: "Hold Mute button on inactive track for >=400ms then release"
    expected: "Track mutes at press-down; on release mute reverts"
    why_human: "Requires hardware"
  - test: "Press shift while holding a Solo or Mute button mid-hold"
    expected: "Track reverts to pre-press state; no stuck state after releasing shift"
    why_human: "set_solo_button/set_mute_button guard fires when shift reassigns buttons; only verifiable in Live"
  - test: "Short taps on all 8 Solo and 8 Mute buttons"
    expected: "All 16 buttons toggle correctly with no regression; identical to pre-modification behavior"
    why_human: "Requires full 8-track hardware test across all strips"
---

# Phase 2: Core Logic Verification Report

**Phase Goal:** Short press toggles and long press acts momentary for both Solo and Mute buttons across all 8 tracks, with LEDs reflecting real-time state and no regression on short presses
**Verified:** 2026-03-31T14:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Short tap (<400ms) on any Solo button toggles that track's solo state on/off | ? NEEDS HUMAN | `_solo_value` delegates to `_handle_toggle_momentary`; 6 passing unit tests confirm correct toggle logic; hardware timing unverifiable offline |
| 2 | Short tap (<400ms) on any Mute button toggles that track's mute state on/off | ? NEEDS HUMAN | `_mute_value` delegates to `_handle_toggle_momentary`; 5 passing unit tests confirm logic; hardware timing unverifiable offline |
| 3 | Holding a Solo button (>=400ms) activates solo at press-down and reverts on release | ? NEEDS HUMAN | State machine logic verified by 9 passing unit tests (`test_full_countdown_sequence_solo`, `test_release_after_threshold_reverts_state`, etc.); requires Ableton Live to confirm MIDI timing |
| 4 | Holding a Mute button (>=400ms) activates mute at press-down and reverts on release | ? NEEDS HUMAN | Symmetric with solo; 5 passing mute tests; requires hardware |
| 5 | Holding Solo on already-soloed track unsolos while held; releasing restores solo | ✓ VERIFIED | `_handle_toggle_momentary` captures `state_before_press = True`; on momentary release `setattr(self._track, track_attr, getattr(self, state_attr))` restores True; confirmed by `test_press_active_track_unsolos_it` + `test_release_after_threshold_reverts_state` |
| 6 | Holding Mute on already-muted track unmutes while held; releasing restores mute | ✓ VERIFIED | Same code path; confirmed by `test_press_active_track_unmutes_it` + `test_release_after_threshold_reverts_mute` |
| 7 | Solo and Mute LEDs reflect actual track state throughout momentary hold — no manual LED calls | ✓ VERIFIED | `grep "turn_on\|turn_off" ToggleMomentaryChannelStripComponent.py` returns zero matches; LED update delegated to `_on_solo_changed`/`_on_mute_changed` listeners which fire automatically on `track.solo`/`track.mute` write |
| 8 | Pressing shift mid-hold leaves no track stuck in wrong state | ? NEEDS HUMAN | `set_solo_button` and `set_mute_button` overrides revert track and clear `_*_momentary_active` before calling parent; 6 passing guard tests confirm code path; actual shift-button reassignment flow requires Live environment |

**Score:** 8/8 truths have implementation evidence — 3 truths fully verifiable offline; 5 truths require human hardware test to confirm end-to-end behavior

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ToggleMomentaryChannelStripComponent.py` | Full toggle/momentary state machine | ✓ VERIFIED | 89 lines, substantive — 8 methods: `__init__`, `_handle_toggle_momentary`, `_solo_value`, `_mute_value`, `set_solo_button`, `set_mute_button`, `disconnect`, `_on_timer` |
| `ToggleMomentaryChannelStripComponent.py` | Contains `_handle_toggle_momentary` | ✓ VERIFIED | Present at line 26; called from `_solo_value` (line 42) and `_mute_value` (line 48) |
| `ToggleMomentaryChannelStripComponent.py` | `_solo_value` and `_mute_value` overrides | ✓ VERIFIED | Both defined in class `__dict__` (confirmed by unit test `test_solo_value_override_defined`); no super() call |
| `ToggleMomentaryChannelStripComponent.py` | `set_solo_button` and `set_mute_button` overrides | ✓ VERIFIED | Lines 53 and 61; include guard and call `SpecialChanStripComponent.set_solo_button/set_mute_button` |
| `ToggleMomentaryChannelStripComponent.py` | Timer countdown (`_solo_ticks_delay`) | ✓ VERIFIED | `_on_timer` at line 74; parent call first; independent solo and mute countdown blocks; `_*_momentary_active = True` set at counter==0 |
| `tests/framework_stubs.py` | Minimal Ableton stubs for unit tests | ✓ VERIFIED | `TrackStub`, `SongStub`, `ButtonStub`, `SpecialChanStripStub` all present |
| `tests/test_task1_toggle_momentary_values.py` | 20 unit tests for value handlers | ✓ VERIFIED | All 20 tests pass |
| `tests/test_task2_timer_and_shift_guards.py` | 23 unit tests for timer and guards | ✓ VERIFIED | All 23 tests pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_solo_value` / `_mute_value` | `_handle_toggle_momentary` | delegation — no super() call | ✓ WIRED | Lines 42-50; grep confirms 3 occurrences (definition + 2 call sites); no `SpecialChanStripComponent._solo_value` call present |
| `_handle_toggle_momentary` press-down branch | `self._track.solo / .mute` | `setattr(self._track, track_attr, not current)` | ✓ WIRED | Line 33: `setattr(self._track, track_attr, not current)` confirmed present |
| `_on_timer` | `_solo_ticks_delay` / `_mute_ticks_delay` | decrement after parent call | ✓ WIRED | Lines 75-84; parent call is first statement; both counters processed as independent `if` blocks |
| `set_solo_button` / `set_mute_button` guard | `self._track.solo / .mute` | revert to `_state_before_press` when `_momentary_active` is True | ✓ WIRED | Lines 56 and 64: `self._track.solo = self._solo_state_before_press` and `self._track.mute = self._mute_state_before_press`; guard confirms `_solo_momentary_active` before writing |
| `ToggleMomentaryChannelStripComponent` | `SpecialMixerComponent._create_strip` | factory instantiation | ✓ WIRED | `SpecialMixerComponent.py` line 50: `return ToggleMomentaryChannelStripComponent()`; imported at line 26 |
| `SpecialMixerComponent` | `APC_64_40_9` | mixer setup | ✓ WIRED | `APC_64_40_9.py` line 136: `self._mixer = SpecialMixerComponent(self, 8)`; imported at line 42 |
| `strip.set_shift_button` | `_shift_pressed` on each channel strip | called per-strip in `APC_64_40_9._setup_mixer_control` | ✓ WIRED | `APC_64_40_9.py` line 159: `strip.set_shift_button(self._shift_button)` in the strip setup loop; `_shift_pressed` is an attribute from `ChannelStripComponent` (Ableton framework base) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| CORE-01 | 02-01-PLAN.md | Short press (<400ms) on Solo button toggles solo on/off | ✓ SATISFIED | `_solo_value` → `_handle_toggle_momentary`; release before threshold keeps toggle; unit tests pass |
| CORE-02 | 02-01-PLAN.md | Long press (>=400ms) on Solo button acts momentary | ✓ SATISFIED | `_on_timer` countdown sets `_solo_momentary_active = True` at tick 0; release branch reverts state |
| CORE-03 | 02-01-PLAN.md | Short press (<400ms) on Mute button toggles mute on/off | ✓ SATISFIED | Symmetric to CORE-01; mute unit tests pass |
| CORE-04 | 02-01-PLAN.md | Long press (>=400ms) on Mute button acts momentary | ✓ SATISFIED | Symmetric to CORE-02; independent mute countdown block |
| CORE-05 | 02-01-PLAN.md | State change fires immediately at press-down | ✓ SATISFIED | `setattr(self._track, track_attr, not current)` executes on `value != 0` branch — no wait for timer |
| CORE-06 | 02-01-PLAN.md | Long press on already-soloed track temporarily unsolos while held | ✓ SATISFIED | `_state_before_press = True` captured; revert writes `True` back on momentary release |
| CORE-07 | 02-01-PLAN.md | Long press on already-muted track temporarily unmutes while held | ✓ SATISFIED | Same logic via shared helper for mute |
| LED-01 | 02-01-PLAN.md | Solo LED reflects real-time state during momentary holds | ✓ SATISFIED | No `turn_on`/`turn_off` calls in implementation; LED driven by `_on_solo_changed` listener on `track.solo` write |
| LED-02 | 02-01-PLAN.md | Mute LED reflects real-time state during momentary holds | ✓ SATISFIED | Same; `_on_mute_changed` listener fires on `track.mute` write |
| INTG-01 | 02-01-PLAN.md | Existing toggle behavior preserved; no stuck states on shift | ✓ SATISFIED | `set_solo_button`/`set_mute_button` guards revert track before parent call; `_shift_pressed` blocks press on `value != 0` |

**Orphaned requirements check:** REQUIREMENTS.md maps CORE-01 through CORE-07, LED-01, LED-02, and INTG-01 to Phase 2 — all 10 are claimed in 02-01-PLAN.md frontmatter. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/framework_stubs.py` | 61-66 | `SpecialChanStripStub._on_timer` uses `_ticks_delay` but real `SpecialChanStripComponent._on_timer` uses `_toggle_fold_ticks_delay` | Info | Test for fold-delay preservation (`test_parent_on_timer_call_is_first`) tests the stub's own counter, not the real parent variable name. No production impact — the real parent call `SpecialChanStripComponent._on_timer(self)` correctly operates on `_toggle_fold_ticks_delay` in production. |

No blockers or warnings found in the production implementation file.

### Human Verification Required

#### 1. Short-press toggle (all 16 buttons)

**Test:** Quick-tap each of the 8 Solo and 8 Mute buttons in turn.
**Expected:** Each tap toggles the track state on then off; LED matches immediately; behavior is identical to the unmodified script.
**Why human:** MIDI event timing in Ableton Live's processing loop cannot be replicated offline. The 400ms threshold is implemented as a tick counter (4 ticks at ~100ms/tick); actual tick cadence depends on Live's scheduler.

#### 2. Long-press momentary Solo — inactive track

**Test:** Press and hold a Solo button on an unsoloed track for at least 500ms, then release.
**Expected:** Track solos at the moment of press (LED on immediately); on release the track returns to unsoloed state (LED off).
**Why human:** Timer-to-API integration requires the Live environment. Confirms `_solo_momentary_active` flag is set by Live's timer callback before release arrives.

#### 3. Long-press momentary Solo — active track

**Test:** Press and hold a Solo button on an already-soloed track for at least 500ms, then release.
**Expected:** Track unsolos at press-down (LED off); on release track re-solos (LED on).
**Why human:** Confirms revert direction for the "already active" case; requires hardware.

#### 4. Long-press momentary Mute

**Test:** Repeat tests 2 and 3 for Mute buttons.
**Expected:** Symmetric behavior — mutes at press-down, reverts on release.
**Why human:** Requires hardware.

#### 5. Shift pressed mid-hold

**Test:** Hold a Solo button, wait ~200ms (not yet momentary), then press Shift and release it, then release the Solo button.
**Expected:** Track reverts to pre-press state when Shift causes button reassignment. No track is left stuck in the wrong state after the sequence completes.
**Why human:** The `set_solo_button(None)` call that triggers the guard fires when Shift reassigns the button matrix — this wiring exists in `APC_64_40_9.py` line 159 but the full button-reassignment timing flow can only be tested with Live running.

#### 6. Exclusive-solo behavior (known tradeoff)

**Test:** With Ableton's exclusive-solo mode enabled, long-press Solo on one track while another track is already soloed.
**Expected:** The implementation writes `self._track.solo` directly without iterating other tracks. In exclusive-solo mode, other tracks may not auto-unsolo as they would with the base `ChannelStripComponent._solo_value`. Document observed behavior.
**Why human:** Exclusive-solo propagation is a known intentional tradeoff documented in the SUMMARY (Decision 1). Hardware test is needed to determine if this is acceptable or requires Phase 3 handling.

### Gaps Summary

No gaps in the implementation. All 10 requirements have code evidence. All 8 observable truths are supported by:
- A substantive, non-stub implementation in `ToggleMomentaryChannelStripComponent.py` (89 lines, 8 methods)
- 43 unit tests (43/43 passing) covering all behavior branches
- Full wiring chain: `APC_64_40_9` -> `SpecialMixerComponent._create_strip` -> `ToggleMomentaryChannelStripComponent`

The `human_needed` status is because 5 of the 8 truths involve real-time MIDI timing, hardware LED response, or Ableton Live API integration that cannot be verified programmatically. The offline unit tests provide high confidence in the state machine logic; hardware testing confirms the Live integration.

---

_Verified: 2026-03-31T14:00:00Z_
_Verifier: Claude (gsd-verifier)_
