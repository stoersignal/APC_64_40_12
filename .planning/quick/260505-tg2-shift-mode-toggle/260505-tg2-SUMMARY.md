---
quick_id: 260505-tg2
slug: shift-mode-toggle
status: uat-passed
final_commit: e67b0a0
uat_rounds: 0
uat_passed: 2026-05-05
date: 2026-05-05
files_modified:
  - EncoderUserModesComponent.py
commits:
  - e67b0a0  feat(quick-260505-tg2): Shift+X mode toggle exit
requirements_satisfied: [D-01, D-02, D-03, D-04]
---

# Quick Task 260505-tg2: Shift+X Mode Toggle Exit — Summary

**One-liner:** Re-pressing a Shift+X mode-button while already in that mode now exits to mode 0 (no-shift Pan/Send-A/B/C selector) instead of being a silent no-op — restoring the only path back to standard encoder modes after entering AutoFilter / EQ Smart Control / User Mode.

**Status:** UAT-passed first round, no debug iterations.

## What changed

One conditional in `EncoderUserModesComponent._mode_value`:

```python
if ((value != 0) or (not sender.is_momentary())):
    idx = self._modes_buttons.index(sender)
    if idx == self._mode_index and idx != 0:
        self.set_mode(0)
    else:
        self.set_mode(idx)
```

8 net lines added (1 condition + 5 lines of comment + idx local).

## Behavior

| Combo | Current mode | Pre-fix | Post-fix |
|---|---|---|---|
| Shift+Send-A | mode 1 (AutoFilter) | no-op | exit → mode 0 |
| Shift+Send-B | mode 2 (EQ Smart Control) | no-op | exit → mode 0 |
| Shift+Send-C | mode 3 (User Mode) | no-op | exit → mode 0 |
| Shift+Pan | mode 0 (Pan) | no-op | no-op (still) |

## Why this matters

Pre-fix, once a user pressed Shift+Send-A/B/C they were stranded in the custom mode. The Pan/Send-A/B/C buttons (with or without shift) would re-assert the current custom mode rather than returning to the standard `EncModeSelectorComponent` sub-mode selector. There was no exit affordance.

Post-fix, the same Shift+X combo is its own escape hatch. `EncModeSelectorComponent`'s `_mode_index` is preserved across the round-trip, so the user lands back on whichever standard sub-mode (Pan / Send A / Send B / Send C) they had before entering the custom mode — context preserved.

## Status-bar feedback rides for free

When `set_mode(0)` runs, `_set_modes` cascades through:

- `EncoderAutoFilterComponent.on_enabled_changed(False)` → `messenger.show_mode('AutoFilter Mode', False)` → "AutoFilter Mode exited"
- `EncoderEQComponent.on_enabled_changed(False)` → "EQ Smart Control exited"

No new status-bar wiring needed — the existing transition hooks fire automatically on the disable side.

## Out of scope (verified unchanged)

- `EncModeSelectorComponent` (no-shift Pan/Send-A/B/C selector) — toggle behavior here would conflict with the existing 400ms long-press momentary auto-revert; left alone.
- Other Shift+X combos that already toggle:
  - Shift+Detail-View — Drum Rack Mode exit (per-track)
  - Shift+Nudge-Back — Lock-to-device toggle
- Shift+Tap-Tempo (snapshot save) and Shift+Stop-All-Clips (randomize macros) — not mode entries; one-shot actions.

## Verification

- `python3 -c "import ast; ast.parse(open('EncoderUserModesComponent.py').read())"` — clean
- Hardware UAT (single round, 2026-05-05): all 7 verification steps approved
  1. ✅ Shift+Send-A enters AutoFilter Mode
  2. ✅ Shift+Send-A again exits to Pan + "AutoFilter Mode exited"
  3. ✅ Shift+Send-B / Send-B again — EQ Smart Control round-trip
  4. ✅ Shift+Send-C / Send-C again — User Mode round-trip
  5. ✅ Shift+Pan in Pan mode — no-op confirmed
  6. ✅ Cross-mode switching: Shift+Send-A → Shift+Send-B transitions cleanly through `set_mode(2)` (no exit-then-enter intermediate)
  7. ✅ EncModeSelectorComponent's standard-mode context preserved across the round-trip — user lands back on whichever Pan/Send-A/B/C they had selected before entering the custom mode

## Lessons reinforced

- **`set_mode(same_index)` is idempotent** — returns without firing `_set_modes`. To make a mode button perform an exit-on-re-press, the conditional has to live BEFORE the call, not inside it.
- **Status-bar feedback can ride free on existing enable/disable transitions** — when `_set_modes` flips component enable state, each component's `on_enabled_changed` hook already messages "X exited". Confirmed no double-hook needed for this fix.
