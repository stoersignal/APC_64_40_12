---
quick_id: 260504-jt9
description: Eq8 gain encoders swap to Q on filter types without gain (LP/HP/Notch)
date: 2026-05-04
status: complete
---

# Quick Task 260504-jt9 — Eq8 gain ↔ Q swap

In TRACK CONTROL MODE 3 with EQ Eight, when band 1 or band 8 has its filter type set to a shape that has no gain (LP / HP / Notch), the matching gain encoder (Low Gain on encoder 5, High Gain on encoder 7) is automatically re-bound to that band's Q parameter. Switching the filter type back to a shape with gain (Shelf / Bell) restores the gain binding immediately — no track-toggle required.

## What changed

| File | Change |
|------|--------|
| `EncoderEQComponent.py` | Re-introduced `_eq8_logged` (one-shot diagnostic) and added `_eq8_filter_type_listeners`. New helpers: `_eq8_apply_q_overrides`, `_eq8_attach_filter_type_listeners`, `_eq8_detach_filter_type_listeners`, `_on_eq8_filter_type_changed`. `_setup_eq8_extras` now calls `_eq8_apply_q_overrides` after the freq/Output/Scale connections, then attaches listeners on `'1 Filter Type A'` / `'8 Filter Type A'` so a UI filter-type change triggers a re-evaluation. `_teardown_eq8_extras` detaches the listeners and now releases encoders 5 and 7 too (in addition to 0..4) so the next mode/track binds them cleanly. |
| `APC40_User_Manual.md` | Auto Q swap bullet under the EQ Eight section. |

## Logic (per band ∈ {1, 8})

```
gain_param = get_parameter_by_name(eq8, '<n> Gain A')
if gain_param.is_enabled:
    encoder.connect_to(gain_param)            # filter type has gain
else:
    q_param = get_parameter_by_name(eq8, '<n> Q A')
    encoder.connect_to(q_param)               # filter type has no gain → use Q
```

Triggered:
- on entry to EQ Smart Control mode with an Eq8 track,
- on track-selection change to another Eq8 track,
- on real-time filter-type change via the value listener attached to `'<n> Filter Type A'`.

## Live API parameter names (best-effort)

`'<n> Q A'` and `'<n> Filter Type A'` are the parameter-name guesses. The one-shot Log.txt dump (gated by `_eq8_logged`) re-fires on the first activation under this commit so we can verify or correct in one UAT round — same self-verifying pattern that caught `'Output Gain'` → `'Output'` previously.

## Edge cases handled

- Band 2 (Mid) is intentionally left alone — `_eq8_apply_q_overrides` only iterates bands 1 and 8.
- Filter-type listeners are detached cleanly on every teardown (entering a different track / mode), so no stale callbacks fire after Eq8 is no longer the active EQ device.
- `_teardown_eq8_extras` releases encoders 5 and 7 too — without this, a previous Q binding could persist after switching to a non-Eq8 track until something else re-bound the encoder.
- `is_enabled` read is wrapped in `try/except` so a Live API quirk (e.g. on transient device states) defaults to "gain enabled" — safer than guessing Q on a transient.

## Verification gates (passed at end of execution)

```
python3 -c "import ast; ast.parse(open('EncoderEQComponent.py').read())"
grep -n '_eq8_apply_q_overrides\|_eq8_filter_type_listeners\|_on_eq8_filter_type_changed' EncoderEQComponent.py
grep -n 'Auto Q swap' APC40_User_Manual.md
```

## Hardware UAT (still required, in Live)

- Place EQ Eight on a track. Set band 1 to Low Shelf (has gain) — encoder 5 should drive band 1 gain. Switch band 1 to 12 dB Low Cut — encoder 5 should now drive band 1 Q. Open Live's UI mid-knob-twist; values match.
- Same for band 8: Bell → encoder 7 drives gain; Notch → encoder 7 drives Q.
- Band 2 (Mid): always Mid Gain on encoder 6, regardless of filter type.
- Open `Log.txt` after first activation and confirm the params named `'1 Q A'`, `'8 Q A'`, `'1 Filter Type A'`, `'8 Filter Type A'` exist. Paste the `[Eq8]` block if any names need patching.
- Switch between Eq8 tracks and other-EQ tracks — listeners detach cleanly, no stuck Q binding.

## Out of scope

- Q swap for band 2 (user asked for first/last only).
- LED feedback distinguishing "encoder in Q mode" vs "gain mode".
- Same swap for other EQ devices (FilterEQ3 / ChannelEq / AEG).
