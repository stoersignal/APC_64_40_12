---
quick_id: 260505-lqz
slug: shift-mode-led-indicator
date: 2026-05-05
files_modified:
  - EncoderUserModesComponent.py  # untracked at repo root, on-disk only
files_versioned:
  - .planning/quick/260505-lqz-shift-mode-led-indicator/260505-lqz-CONTEXT.md
  - .planning/quick/260505-lqz-shift-mode-led-indicator/260505-lqz-PLAN.md
  - .planning/quick/260505-lqz-shift-mode-led-indicator/260505-lqz-SUMMARY.md
  - .planning/STATE.md
autonomous: true
---

# Quick Task 260505-lqz: Shift Mode LED Indicator

**Goal:** While Shift is held, the LEDs of the Pan/Send A/B/C buttons display only the currently active Shift-mode (single LED on; mode 0 = all off). Replace the existing cumulative "level meter" LED scheme.

See `260505-lqz-CONTEXT.md` for the locked decisions.

## Tasks

<task id="01" type="execute">
<objective>
Replace cumulative LED loop in `EncoderUserModesComponent._set_modes` with a single-active-LED scheme, and refresh LEDs on Shift-press by calling `_set_modes()` at the end of `set_mode_buttons`.
</objective>

<read_first>
- EncoderUserModesComponent.py (full file — small, 178 lines)
- ShiftableEncoderSelectorComponent.py:63-71 (the caller of set_mode_buttons)
</read_first>

<action>
**Edit 1.** In `EncoderUserModesComponent.py`, inside `_set_modes` (around lines 116-120), replace:

```python
            for index in range(len(self._modes_buttons)):
                if (index <= self._mode_index):
                    self._modes_buttons[index].turn_on()
                else:
                    self._modes_buttons[index].turn_off()
```

with:

```python
            # Quick-260505-lqz: single-active-LED indicator. In default
            # mode 0 (no Shift-mode active), all 4 LEDs go dark; in modes
            # 1-3, only the matching Shift+X button lights up.
            for index in range(len(self._modes_buttons)):
                if self._mode_index != 0 and index == self._mode_index:
                    self._modes_buttons[index].turn_on()
                else:
                    self._modes_buttons[index].turn_off()
```

**Edit 2.** In `EncoderUserModesComponent.py`, inside `set_mode_buttons` (around lines 72-85), after the `for button in buttons:` loop populates `self._modes_buttons` and before the `assert (self._mode_index in range(self.number_of_modes()))` line, append:

```python
            # Quick-260505-lqz: refresh LEDs to reflect current _mode_index
            # immediately on Shift-press. Without this, the LEDs stay stale
            # (cumulative from prior _set_modes call) until the user presses
            # one of the 4 buttons.
            self._set_modes()
```

This call goes inside the `if (buttons != None):` block. Do NOT call `_set_modes()` when `buttons is None` (Shift-release path), since on Shift-release the buttons are about to be bound to `EncModeSelectorComponent` and we don't want EncoderUserModesComponent's LED scheme to run.
</action>

<acceptance_criteria>
- [ ] `grep -c "self._mode_index != 0 and index == self._mode_index" EncoderUserModesComponent.py` returns `1`
- [ ] `grep -c "if (index <= self._mode_index):" EncoderUserModesComponent.py` returns `0` (old pattern removed)
- [ ] `grep -nA1 "if (buttons != None):" EncoderUserModesComponent.py` shows the bind loop, and somewhere within that block (before the closing of the function) a `self._set_modes()` call appears
- [ ] `python3 -c "import py_compile; py_compile.compile('EncoderUserModesComponent.py', doraise=True)"` returns 0 (compiles)
- [ ] Manual UAT in Ableton Live (deferred to user): hold Shift, observe Pan/SendA/SendB/SendC LEDs. Default state = all OFF. Press Shift+SendA = SendA lit only. Press Shift+SendA again = exit, all OFF. Repeat for SendB / SendC.
</acceptance_criteria>
</task>

## must_haves

1. Single-active-LED behavior matches the table in `260505-lqz-CONTEXT.md` D-01.
2. Sticky shift-mode preserved: AutoFilter remains mode 1 across Shift release/press; LED reflects this on the next Shift-press without requiring a button touch.
3. `EncModeSelectorComponent` LED behavior (when Shift is NOT held) is unchanged — verified by NOT modifying that file.
4. No regression in toggle-out-of-mode behavior from quick-260505-tg2 — `_mode_value` toggle path is untouched.

## Verification

- Compilation: `python3 -c "import py_compile; py_compile.compile('EncoderUserModesComponent.py', doraise=True)"`
- Pattern check: `grep -c "self._mode_index != 0 and index == self._mode_index" EncoderUserModesComponent.py` → 1
- Pattern removed: `grep -c "if (index <= self._mode_index):" EncoderUserModesComponent.py` → 0
- Manual UAT in Ableton Live (user-confirmed): all 4 mode states behave per the table.

## Iteration — UAT round 2 (2026-05-07)

### Failure mode discovered

Tests 1–6 from the original test plan passed in a clean default state. UAT in EQ Smart Control mode (mode 2, FilterEQ3 / Eq8 / ChannelEq tracks) revealed that the kill-switch LEDs (SendA/B/C reflecting band-on state) were NOT overridden by the single-active-LED scheme on Shift-press.

Root cause: feat-commit Edit 2 called the full `self._set_modes()` from `set_mode_buttons`. `_set_modes()` re-runs sub-component setup, including `_encoder_eq_modes.set_controls_and_buttons(...)` → `SpecialTrackEQComponent.set_cut_buttons(...)` → `update()`, which lights LEDs based on kill-state. Kill-state LEDs therefore ran AFTER our LED loop and reclaimed the buttons.

Same defect pre-existed in `_set_modes()` itself — original LED loop ran BEFORE sub-component setup, so user-pressed mode entries (Shift+SendB) also got their single-active-LEDs overwritten by kill-state LEDs. Test 5 in round 1 happened to pass by coincidence (kill-state alignment).

### Fix (replaces feat-commit Edit 1 + Edit 2)

<task id="02" type="execute">
<objective>
Restructure LED logic so the single-active-LED scheme always runs LAST and is independent of sub-component re-binding.
</objective>

<action>
Three structural changes to `EncoderUserModesComponent.py`:

1. **New helper** `_refresh_mode_leds()` (after `_mode_value`, before `_set_modes`):

```python
def _refresh_mode_leds(self):
    if not self.is_enabled():
        return
    for index in range(len(self._modes_buttons)):
        if self._mode_index != 0 and index == self._mode_index:
            self._modes_buttons[index].turn_on()
        else:
            self._modes_buttons[index].turn_off()
```

2. **In `_set_modes`:** remove the inline LED loop from the start of the function; append `self._refresh_mode_leds()` AFTER the `if/elif/elif/elif/else` mode-branch block (immediately before the `#self._rebuild_callback()` comment). This makes the LED scheme override any LEDs set by sub-component setup (kill-switches in mode 2, AutoFilter in mode 1, user mode 3).

3. **In `set_mode_buttons`:** replace `self._set_modes()` (added in feat commit) with `self._refresh_mode_leds()`. On Shift-press we only want LEDs to refresh — not to re-attach sub-components, which would cause kill-state LEDs to reclaim the buttons.
</action>

<acceptance_criteria>
- [x] `grep -c "def _refresh_mode_leds" EncoderUserModesComponent.py` → 1
- [x] `grep -c "self._refresh_mode_leds()" EncoderUserModesComponent.py` → 2 (set_mode_buttons + tail of _set_modes)
- [x] LED loop body (`if self._mode_index != 0 and index == self._mode_index:`) appears exactly once (inside the helper)
- [x] No `self._set_modes()` call inside `set_mode_buttons` body
- [x] `python3 -c "import py_compile; py_compile.compile('EncoderUserModesComponent.py', doraise=True)"` returns 0
- [ ] Manual UAT in Live: enter EQ Smart Control mode (Shift+SendB on a track with FilterEQ3/Eq8/ChannelEq); release Shift; verify kill-state LEDs on SendA/B/C reflect band-on state. Re-press Shift → expect SendB lit only, SendA/SendC/Pan dark; release → kill-state LEDs return on next kill toggle. Repeat for AutoFilter (mode 1, Shift+SendA) and User mode (mode 3, Shift+SendC).
</acceptance_criteria>
</task>
