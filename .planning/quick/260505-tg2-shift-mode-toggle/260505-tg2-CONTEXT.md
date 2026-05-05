# Quick Task 260505-tg2: Shift+X Mode Toggle Exit — Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Task Boundary

When the user enters a mode via a Shift+X combo (Shift+Send-A,
Shift+Send-B, Shift+Send-C), pressing the SAME combo a second time
should EXIT that mode (revert to the default Pan mode). Currently the
second press is a no-op because `set_mode(idx)` early-returns on
`self._mode_index == idx`.

**Scope (only the 3 Shift-modified encoder sub-modes via
`EncoderUserModesComponent._mode_value`):**

| Combo | Current mode | Press again | Currently | Should be |
|---|---|---|---|---|
| Shift+Pan | mode 0 (Pan) | Shift+Pan | no-op | no-op (no change) |
| Shift+Send-A | mode 1 (AutoFilter) | Shift+Send-A | no-op | exit → mode 0 |
| Shift+Send-B | mode 2 (EQ Smart Control) | Shift+Send-B | no-op | exit → mode 0 |
| Shift+Send-C | mode 3 (User Mode) | Shift+Send-C | no-op | exit → mode 0 |

**Out of scope:**

- The non-shifted Pan/Send-A/B/C buttons (handled by
  `EncModeSelectorComponent`, not `EncoderUserModesComponent`). Their
  long-press momentary auto-revert is unrelated and unchanged.
- Other Shift+X combos that already toggle correctly:
  - Shift+Detail-View — Drum Rack Mode exit (auto-engage on track-select
    means re-press is rarely meaningful; mode is already a per-track toggle)
  - Shift+Nudge-Back — Lock-to-device toggle
  - Shift+Tap-Tempo — Snapshot save (not a mode entry)
  - Shift+Stop All Clips — randomize_macros (not a mode entry)

</domain>

<decisions>
## Implementation Decisions (locked)

### D-01 — Toggle target: mode 0 (Pan)

When user re-presses a Shift+X mode-button while already in that mode,
revert to mode 0 (Pan / default). Not "previous mode" — always Pan.

**Why:** Keeps the mental model simple. Users don't have to remember
which mode they were in before; pressing the SAME Shift+X combo again
always returns them to the default Pan mode.

### D-02 — Mode 0 (Pan) is exempt

Pressing Shift+Pan while in Pan mode stays a no-op. No state change,
no message. Toggle logic only applies to non-zero modes.

### D-03 — Status-bar feedback rides for free

When `set_mode(0)` runs, the existing component-level transition hooks
fire automatically:

- `EncoderAutoFilterComponent.on_enabled_changed(False)` →
  `messenger.show_mode('AutoFilter Mode', False)` → "AutoFilter Mode exited"
- `EncoderEQComponent.on_enabled_changed(False)` →
  "EQ Smart Control exited"

No additional wiring needed.

### D-04 — Preserve existing momentary-revert semantics

`EncModeSelectorComponent` (the no-shift selector for Pan/Send) has a
~400 ms long-press auto-revert path that snaps back to Pan on release.
This is unrelated to the Shift+X toggle behaviour and unchanged here —
it lives in a different component, only fires when shift is NOT held.

</decisions>

<specifics>
## Specific Implementation

### Change site

`EncoderUserModesComponent._mode_value` (lines 96-102 of
`EncoderUserModesComponent.py`).

### Current

```python
def _mode_value(self, value, sender):
    assert (len(self._modes_buttons) > 0)
    assert isinstance(value, int)
    assert isinstance(sender, ButtonElement)
    assert (self._modes_buttons.count(sender) == 1)
    if ((value != 0) or (not sender.is_momentary())):
        self.set_mode(self._modes_buttons.index(sender))
```

### Target

```python
def _mode_value(self, value, sender):
    assert (len(self._modes_buttons) > 0)
    assert isinstance(value, int)
    assert isinstance(sender, ButtonElement)
    assert (self._modes_buttons.count(sender) == 1)
    if ((value != 0) or (not sender.is_momentary())):
        idx = self._modes_buttons.index(sender)
        # Toggle: re-pressing the same Shift+<mode-button> combo while
        # already in that non-default mode exits back to mode 0 (Pan).
        # Mode 0 itself is exempt — pressing Shift+Pan in Pan mode is
        # already a no-op (set_mode is idempotent).
        if idx == self._mode_index and idx != 0:
            self.set_mode(0)
        else:
            self.set_mode(idx)
```

### Why this is safe

- `set_mode` is the existing public API — no internal-state surgery
  required.
- The `idx != 0` guard preserves the existing Shift+Pan no-op (avoids
  the toggle path firing on Pan re-presses).
- All downstream side-effects (status-bar messages, encoder rebinding,
  LED updates) ride on the existing `_set_modes` cascade.

### Verification

- AST parse: `python3 -c "import ast; ast.parse(open('EncoderUserModesComponent.py').read())"` → OK
- Hardware UAT (single round expected — change is mechanical):
  1. Press Shift+Send-A → AutoFilter Mode entered + status-bar message
  2. Press Shift+Send-A AGAIN → returns to Pan + "AutoFilter Mode exited"
  3. Repeat for Send-B (EQ Smart Control) and Send-C (User Mode)
  4. Shift+Pan twice in Pan mode → no-op (no status messages, no
     mode-state churn)
  5. Cross-mode switching still works: Shift+Send-A → Shift+Send-B
     transitions cleanly through `set_mode(2)`

</specifics>

<canonical_refs>
## Canonical References

- `EncoderUserModesComponent.py` — the change site.
- `EncModeSelectorComponent.py` — sister component (no-shift sub-mode);
  unchanged.
- `ShiftableEncoderSelectorComponent.py` — the shift-mux that routes
  button presses to `_encoder_user_modes` when shift is held; unchanged.
- Project anti-pattern reinforced: `set_mode(same_index)` is idempotent
  (returns without firing `_set_modes`). The toggle exit needs an
  explicit conditional BEFORE the call.

</canonical_refs>
