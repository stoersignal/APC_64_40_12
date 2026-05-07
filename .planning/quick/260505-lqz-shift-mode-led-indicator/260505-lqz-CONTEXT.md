# Quick Task 260505-lqz: Shift Mode LED Indicator — Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Task Boundary

While **Shift is held**, the LEDs of the Pan / Send A / Send B / Send C
buttons (the same 4 physical buttons that act as encoder-mode selectors
when Shift is NOT held) currently display a cumulative "level meter":
all buttons up to and including `EncoderUserModesComponent._mode_index`
light up.

We want this changed to a **single-active-LED** scheme that shows
which Shift-mode is currently active (or no LED at all if no
Shift-mode is active).

| `_mode_index` | What it represents | Current LEDs (level meter) | Target LEDs (option B) |
|---|---|---|---|
| 0 | Default — no Shift-mode active (Pan / Send A/B/C unshifted are owned by EncModeSelectorComponent when Shift is released) | Pan only | **all OFF** |
| 1 | AutoFilter mode (entered via Shift+Send A) | Pan + Send A | **Send A only** |
| 2 | EQ Smart Control mode (entered via Shift+Send B) | Pan + Send A + Send B | **Send B only** |
| 3 | User mode (entered via Shift+Send C) | Pan + Send A + Send B + Send C | **Send C only** |

This is purely an LED-feedback change. Functional behavior of the
buttons (mode entry, exit-via-toggle from quick-260505-tg2, momentary
behavior) is unchanged.

**Out of scope:**
- LED behavior when Shift is NOT held (owned by `EncModeSelectorComponent`
  — already correct: highlights the currently selected sub-mode Pan/SendA/SendB/SendC).
- LED color / blink — current behavior is plain on/off; no color change requested.
- The bottom encoder mode strip (User1/User2/User3 buttons) — unchanged.
- `EncoderUserModesComponent._set_modes` parameter-release / sub-component
  enable logic — only the LED loop (lines 116-120) is touched.

</domain>

<decisions>
## Implementation Decisions (locked)

### D-01 — Option B: mode 0 → all OFF

Confirmed by user 2026-05-05 in the planning thread. When Shift is held
and `_mode_index == 0`, **all 4 LEDs go dark**. Rationale: the user's
phrasing "(if one is active)" treats mode 0 as "no Shift-mode is
currently active", so there is nothing to indicate.

### D-02 — Refresh LEDs on Shift-press, not only on button-press

Currently `_set_modes()` is the only LED-redraw path, and it runs only
when the user presses one of the 4 buttons (via `set_mode` →
`_set_modes`). That means when the user first holds Shift while in a
sticky non-zero mode (e.g., AutoFilter persists across Shift release/press),
the LEDs would be stale until they touch a button.

We must refresh LEDs at the moment EncoderUserModesComponent acquires
the buttons. The hook is `set_mode_buttons` (called by
`ShiftableEncoderSelectorComponent.update()` line 70 when Shift is pressed).

### D-03 — Sticky shift-mode preserved

`_mode_index` is NOT reset across Shift release/press cycles. If the
user enters AutoFilter (mode 1), releases Shift, then re-presses Shift,
the new LED scheme correctly shows Send A lit — communicating that
AutoFilter is still the active Shift-mode. No state change needed for
this; sticky behavior is already in place via Shiftable wrapper.

### D-04 — Two-commit pattern (feat then UAT-passed)

Mirror quick-260505-tg2's commit shape:
1. **Feat commit (code only):** stage `EncoderUserModesComponent.py`,
   commit message `feat(quick-260505-lqz): ...`. This file IS tracked
   (the `.continue-here.md` partial-tracking note applies to other
   files like `APC.py` / `EncoderEQComponent.py`, not this one).
2. **UAT-passed commit (planning + STATE):** after user verifies in
   Live, stage CONTEXT/PLAN/SUMMARY + STATE.md row, commit message
   `chore(quick-260505-lqz): mark UAT-passed (final commit <hash>)`.

</decisions>

<canonical_refs>
## Canonical References

### Files modified (on disk only — repo root sources are untracked)
- `EncoderUserModesComponent.py` lines 113-171 (`_set_modes`) and 72-85 (`set_mode_buttons`)

### Files read for context (not modified)
- `ShiftableEncoderSelectorComponent.py:63-71` — Shift-state wrapper that binds/unbinds buttons via `set_mode_buttons`
- `EncModeSelectorComponent.py:143-150` — Owns LEDs when Shift is NOT held; unchanged
- `APC_64_40_9.py:347-350` — Wiring: `_global_bank_buttons` are the 4 physical buttons

### Related quick tasks
- `260505-tg2-shift-mode-toggle` — Toggle-out-of-mode behavior. Same component, complementary feature.
- `260504-k6p-replace-mode-2-alternate-device-with-aut` — Introduced AutoFilter at mode 1.

</canonical_refs>

<specifics>
## Specific Ideas

The minimal code change is two edits in `EncoderUserModesComponent.py`:

**Edit 1 — Replace cumulative LED loop** (in `_set_modes`, around lines 116-120):

```python
# Before:
for index in range(len(self._modes_buttons)):
    if (index <= self._mode_index):
        self._modes_buttons[index].turn_on()
    else:
        self._modes_buttons[index].turn_off()

# After (quick-260505-lqz):
for index in range(len(self._modes_buttons)):
    if self._mode_index != 0 and index == self._mode_index:
        self._modes_buttons[index].turn_on()
    else:
        self._modes_buttons[index].turn_off()
```

**Edit 2 — Refresh LEDs when Shift-press binds buttons** (at the end of
`set_mode_buttons`, after the `if buttons != None:` block populates
`self._modes_buttons`):

```python
# Refresh LEDs to reflect current _mode_index immediately on Shift-press
# (quick-260505-lqz). Without this, the LEDs stay stale (showing the
# pre-Shift state) until the user presses one of the 4 buttons.
if self._modes_buttons:
    self._set_modes()
```

This calls `_set_modes()`, which redoes the LED loop AND the parameter-
release / sub-component enable side-effects. The side-effects are
idempotent on the current `_mode_index` (they re-enable whichever
sub-component is current), so calling `_set_modes()` on shift-press is
safe and matches the original "set everything to current mode" semantics.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

---

*Quick task: 260505-lqz-shift-mode-led-indicator*
*Context gathered: 2026-05-05*
