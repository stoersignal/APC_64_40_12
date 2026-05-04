---
quick_id: 260504-jt9
description: Eq8 gain encoders swap to Q on filter types without gain (LP/HP/Notch)
date: 2026-05-04
status: complete
uat_passed: 2026-05-04
final_commit: <pending>
commits:
  - 1eff437 feat — gain↔Q swap based on parameter.is_enabled (didn't fire — Live keeps gain enabled even on no-gain types)
  - 67fa36d fix — switch to filter-type VALUE (0/1/4/6/7 = no-gain types); per-call diagnostic line for one-shot verification
  - <pending> docs/cleanup — remove diagnostics (filter-type values verified), mark UAT-passed
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

## Hardware UAT (passed 2026-05-04)

User confirmed working in Live: encoder 5 drives Low Q on no-gain filter types and Low Gain on gain types; encoder 7 same for High; the swap re-evaluates instantly when the user changes filter type from Live's UI. Band 2 (Mid) stays on Mid Gain throughout.

## Iteration history (notes for future similar tasks)

The first attempt (`1eff437`) used `parameter.is_enabled` on the gain parameter as the gain-vs-Q signal, expecting Live to flip it to `False` on no-gain filter types. **`is_enabled` does not track UI greying for EQ8** — Live keeps the gain parameter `is_enabled = True` even when its UI knob is greyed out, so the conditional always landed on the gain branch and the Q swap never engaged.

The fix (`67fa36d`) reads the filter-type **value** directly:

| filter_type value | Live's UI label | gain? |
|-------------------|-----------------|-------|
| 0 | 48 dB Low Cut  | no  |
| 1 | 12 dB Low Cut  | no  |
| 2 | Low Shelf      | yes |
| 3 | Bell           | yes |
| 4 | Notch          | no  |
| 5 | High Shelf     | yes |
| 6 | 12 dB High Cut | no  |
| 7 | 48 dB High Cut | no  |

`EQ8_NO_GAIN_TYPES = (0, 1, 4, 6, 7)` is the canonical lookup. Verified one-shot via the per-call diagnostic line in `67fa36d`; that diagnostic is removed in the final cleanup commit now that the values are confirmed.

**Reusable lesson:** *don't use `parameter.is_enabled` to detect "this control is currently meaningful in Live's UI".* Live treats `is_enabled` as "API-controllable," which can stay `True` even for parameters Live's UI greys out. For UI-greyed-out detection, find the upstream value (filter type, mode index, etc.) and read it directly.

## Out of scope

- Q swap for band 2 (user asked for first/last only).
- LED feedback distinguishing "encoder in Q mode" vs "gain mode".
- Same swap for other EQ devices (FilterEQ3 / ChannelEq / AEG).
