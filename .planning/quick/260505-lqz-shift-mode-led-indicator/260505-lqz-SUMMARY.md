---
quick_id: 260505-lqz
slug: shift-mode-led-indicator
date: 2026-05-05
status: complete
files_modified:
  - EncoderUserModesComponent.py
files_versioned:
  - EncoderUserModesComponent.py
  - .planning/quick/260505-lqz-shift-mode-led-indicator/260505-lqz-CONTEXT.md
  - .planning/quick/260505-lqz-shift-mode-led-indicator/260505-lqz-PLAN.md
  - .planning/quick/260505-lqz-shift-mode-led-indicator/260505-lqz-SUMMARY.md
  - .planning/STATE.md
acceptance_criteria_passed: 4/4 automated (manual UAT in Live deferred)
---

# Quick Task 260505-lqz: Shift Mode LED Indicator — Summary

## What Changed

While Shift is held, the LEDs of the Pan / Send A / Send B / Send C
buttons now use a **single-active-LED indicator** instead of the
prior cumulative "level meter":

| `_mode_index` | Mode | LEDs (was) | LEDs (now) |
|---|---|---|---|
| 0 | Default (no Shift-mode active) | Pan only | **all OFF** |
| 1 | AutoFilter (Shift+SendA) | Pan + SendA | **SendA only** |
| 2 | EQ Smart Control (Shift+SendB) | Pan + SendA + SendB | **SendB only** |
| 3 | User mode (Shift+SendC) | Pan + SendA + SendB + SendC | **SendC only** |

LEDs now also refresh immediately on Shift-press (via a `_set_modes()`
call appended to `set_mode_buttons` after the bind loop). Previously
the LEDs were stale from the prior shift session until the user
pressed one of the 4 buttons.

When Shift is released, control returns to `EncModeSelectorComponent`
which lights the active sub-mode (Pan/SendA/SendB/SendC) — unchanged.

## Why

User wants the 4 mode-selector buttons to function as a status display
when held under Shift: "what Shift-mode am I currently in?". The old
cumulative scheme was confusing because all 4 buttons being lit didn't
clearly communicate "User mode is active" — it looked like all modes
were active. Single-LED is the standard pattern for radio-button-style
mode indicators on the APC40.

## How

Two small edits to `EncoderUserModesComponent.py`:

1. **`_set_modes` (lines 113-171)** — replaced the LED loop. Old:
   `if (index <= self._mode_index): turn_on else turn_off`. New:
   `if self._mode_index != 0 and index == self._mode_index: turn_on else turn_off`.

2. **`set_mode_buttons` (lines 72-90)** — appended a `self._set_modes()`
   call inside the `if (buttons != None):` block, after the bind loop.
   This refreshes LEDs immediately on Shift-press to reflect the
   sticky `_mode_index` from the prior shift session. Skipped on
   Shift-release (`buttons == None` path) so EncoderUserModesComponent's
   LED scheme doesn't fight EncModeSelectorComponent for ownership.

## Verification

Acceptance criteria from PLAN.md:

- [x] `grep -c "self._mode_index != 0 and index == self._mode_index" EncoderUserModesComponent.py` → 1
- [x] `grep -c "if (index <= self._mode_index):" EncoderUserModesComponent.py` → 0
- [x] `_set_modes()` call appears inside `if (buttons != None):` block in `set_mode_buttons`
- [x] `python3 -c "import py_compile; py_compile.compile('EncoderUserModesComponent.py', doraise=True)"` → exit 0
- [ ] **Manual UAT in Ableton Live** — deferred to user. Test plan:
  1. Reload script in Live (or restart Live)
  2. Hold Shift in default state → all 4 LEDs (Pan/SendA/SendB/SendC) should be **OFF**
  3. While holding Shift, press SendA → SendA LED on; release Shift → EncMode regular highlight returns
  4. Press Shift again → SendA still lit (sticky AutoFilter mode)
  5. While holding Shift, press SendA again → exit AutoFilter (toggle from quick-260505-tg2); LED goes off
  6. Repeat steps 3-5 for SendB (EQ) and SendC (User mode)

## Sticky-mode note

The new behavior makes a previously invisible state visible: AutoFilter
/ EQ / User-mode persist across Shift release/press cycles. The LED
will now correctly show this on the next Shift-press without the user
having to touch a button. If this surfaces a UX preference for "reset
on Shift release", that's a separate quick task — not in scope here.

## Notes

- `EncoderUserModesComponent.py` is tracked in git (corrected from an
  earlier draft that incorrectly cited `.continue-here.md`'s partial-
  tracking note — that note applies to other files like `APC.py` /
  `EncoderEQComponent.py`, not this one).
- No tests written: this is LED feedback in the Live runtime; no test
  harness can simulate the framework's button-LED I/O.
- Toggle-out-of-mode behavior from quick-260505-tg2 is preserved
  (`_mode_value` lines 96-110 untouched).
- Commit pattern mirrors quick-260505-tg2: feat commit with code only
  first; UAT-passed commit with planning artifacts + STATE.md row
  follows after user verifies in Live.

## Iteration (2026-05-07) — fix(quick-260505-lqz)

### What failed

UAT round 1 cleared tests 1–6 in a clean default state. UAT round 2 in
EQ Smart Control mode (mode 2, FilterEQ3 / Eq8 / ChannelEq tracks)
revealed that the kill-switch LEDs (SendA/B/C reflecting band-on state)
were NOT overridden by the single-active-LED scheme on Shift-press.

### Root cause

The feat commit's Edit 2 called the full `self._set_modes()` from
`set_mode_buttons`. `_set_modes()` re-runs sub-component setup,
including `_encoder_eq_modes.set_controls_and_buttons(...)` →
`SpecialTrackEQComponent.set_cut_buttons(...)` → `update()`, which
lights LEDs based on kill-parameter state. Kill-state LEDs therefore
ran AFTER our LED loop and reclaimed the buttons.

The same defect pre-existed in `_set_modes()` itself — the original
LED loop ran BEFORE the sub-component branch, so user-pressed mode
entries (Shift+SendB on an EQ track) also had their single-active-LEDs
overwritten. Test 5 passed in round 1 by coincidence (kill-state
alignment with desired LED state).

### Fix (3 structural edits)

1. Extracted the LED loop into `_refresh_mode_leds()` (new helper).
2. In `_set_modes()`: removed the inline LED loop; appended
   `self._refresh_mode_leds()` AFTER the mode-branch block, so the
   single-active-LED scheme runs LAST and overrides any LEDs set by
   sub-component setup (kill-switches in mode 2, AutoFilter in mode 1,
   user mode in mode 3).
3. In `set_mode_buttons()`: replaced `self._set_modes()` with
   `self._refresh_mode_leds()`. On Shift-press we only want LEDs to
   refresh — not to re-attach sub-components.

### Verification (automated)

- [x] `grep -c "def _refresh_mode_leds" EncoderUserModesComponent.py` → 1
- [x] `grep -c "self._refresh_mode_leds()" EncoderUserModesComponent.py` → 2
- [x] No `self._set_modes()` call inside `set_mode_buttons` body
- [x] `python3 -c "import py_compile; py_compile.compile('EncoderUserModesComponent.py', doraise=True)"` → exit 0

### UAT round 2 plan

1. Reload script in Live.
2. Select a track with an EQ device (FilterEQ3 / Eq8 / ChannelEq).
3. Enter EQ Smart Control: Shift+SendB. Confirm encoders/kill-switches behave as before (no regression).
4. Release Shift. Observe SendA/B/C LEDs reflecting kill (band-on) state.
5. Press Shift again — **expect: Pan / SendA / SendC dark, SendB lit only**, regardless of kill-switch state.
6. Release Shift — kill-state LEDs return on next kill toggle (no immediate refresh by design; matches pre-existing pattern).
7. Repeat for AutoFilter (Shift+SendA) and User mode (Shift+SendC) on relevant tracks.
8. Confirm tests 1–6 from round 1 still pass (default-state behaviour unchanged).

### Edge case (acknowledged, not fixed)

`_on_cut_changed` in `SpecialTrackEQComponent` re-renders kill-state
LEDs whenever a kill parameter value changes. While Shift is held,
button presses can't trigger this (`_ignore_cut_buttons=True` blocks
`_cut_value`), but external automation or another control surface
changing the kill state WOULD overwrite the single-active-LED. Not
fixed because: (a) edge case in practice, (b) suppressing
`_on_cut_changed` during Shift hold is invasive cross-component state
and would need a separate quick task if it ever surfaces.

## Iteration 2 (2026-05-07) — Shift-release LED restore

### What user reported

After iteration 1 fixed the Shift-press override, on Shift-release the
LEDs stayed in the single-active-LED state until the next kill-toggle
event. Desired behavior: kill-switch LEDs should repaint immediately
on Shift-release, even with no other button press.

### Fix (2 files)

1. **`EncoderEQComponent.refresh_button_leds()`** (new public method):
   Lightweight repaint of kill-state LEDs (`_track_eq.update()`) plus
   Pan-button LED (highpass / slope / lock — whichever is active for
   the current EQ device class). Does NOT re-run the full
   `_update_controls_and_buttons` (avoids encoder release/reconnect
   churn). Each Pan-button restorer is a no-op when its respective
   binding isn't active, so the call is safe regardless of EQ device
   class.

2. **`EncoderUserModesComponent.set_mode_buttons` (Shift-release path):**
   When `buttons is None` and `_mode_index == 2`, call
   `self._encoder_eq_modes.refresh_button_leds()`. Other modes (0/1/3)
   are left alone — EncMode is the natural owner of these buttons in
   mode 0 but its `update()` asserts `_modes_buttons != None`, which
   is briefly false at this point in the Shift-release sequence (it's
   re-bound by `ShiftableEncoderSelectorComponent.update` line 67
   AFTER our `set_mode_buttons(None)` returns). Mode 0 LED state
   matches pre-fix behavior verified in tests 1–6.

### Verification (automated)

- [x] `grep -c "def refresh_button_leds" EncoderEQComponent.py` → 1
- [x] `grep -c "self._encoder_eq_modes.refresh_button_leds()" EncoderUserModesComponent.py` → 1
- [x] `python3 -c "import py_compile; py_compile.compile('EncoderEQComponent.py', doraise=True); py_compile.compile('EncoderUserModesComponent.py', doraise=True)"` → exit 0

### UAT round 3 plan

1. Reload script in Live.
2. Track with EQ device → Shift+SendB to enter EQ Smart Control.
3. Release Shift → kill-state LEDs (SendA/B/C) reflect band-on. Pan-button LED reflects highpass/slope/lock per device.
4. Press Shift → SendB lit only, others dark (iteration 1 verified).
5. **Release Shift WITHOUT pressing any other button** → expect kill-state LEDs and Pan-button LED to repaint immediately.
6. Confirm tests 1–6 + iteration-1 EQ-mode case still pass.
