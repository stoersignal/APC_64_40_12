---
slug: eq8-track-control-mode-3
status: resolved
trigger: fix broken EQ8 support in "TRACK CONTROL MODE 3"
created: 2026-05-04
updated: 2026-05-04
---

# Debug Session — Eq8 mapping in TRACK CONTROL MODE 3

## Symptoms

User-reported intent (clarified during the debug session — the original "broken" framing was the user catching that the EQ8 mapping wasn't usable, not a regression):

- Use the **last EQ band (band 8)** for Highs instead of band 3.
- The Track Control section's **top row** of encoders (encoders 0 / 1 / 2 / 3 in the 2 × 4 grid) should drive band frequency.
- Encoder 0 (top-left) → **Scale**.
- Encoder 4 (bottom-left, directly below encoder 0) → **Output**.

Key insight surfaced during clarification: the APC40's Track Control section is a **2 × 4 encoder grid**, not a single row of 8. That re-anchored every "above" / "below" / "first encoder" reference in the prior tasks (Channel EQ Mid Freq on encoder 0 = top-left; Output on encoder 4 = directly below it).

## Root cause / design

`EQ_DEVICES['Eq8']` previously listed all 8 bands in `Gains` / `Cuts`, but the wiring in `_update_controls_and_buttons` only used the FIRST 3 entries (passed encoders 5/6/7 to `set_gain_controls`). That meant Highs landed on band 3 — not the user's expected band 8 — and there was no Eq8-specific encoder takeover for Scale / band freqs / Output.

## Fix

`EncoderEQComponent.py`:

- `EQ_DEVICES['Eq8']` reduced to the three bands actually wired: `Gains: ['1 Gain A', '2 Gain A', '8 Gain A']`, `Cuts: ['1 Filter On A', '2 Filter On A', '8 Filter On A']`. Highs now correctly land on band 8.
- New `EQ8_EXTRAS` dict for the top-row + Output extras: `Scale`, `Output Gain`, `1 Frequency A`, `2 Frequency A`, `8 Frequency A`.
- New state on `EncoderEQComponent`: `_eq8_device`, `_eq8_logged`.
- New helpers: `_setup_eq8_extras(eq8_device)` / `_teardown_eq8_extras()`. Setup releases encoders 0..4 first (so any prior AutoFilter or appointed-device binding is dropped), then connects:
  - 0 → Scale, 1 → LowFreq, 2 → MidFreq, 3 → HighFreq, 4 → Output.
  - One-shot Log.txt dump under `[Eq8]` on first activation — same self-verifying pattern that caught `'Output Gain'` vs `'Output'` for Channel EQ.
- New branch in `_update_controls_and_buttons`: when the active EQ device is `Eq8`, disable `_track_filter` (so AutoFilter doesn't fight for encoders 0/4), set up Eq8 extras, keep Pan = lock.
- Disconnect cleanup extended.

The Pan-button hierarchy is now:

| Active EQ device | Pan button |
|------------------|------------|
| `ChannelEq`      | Highpass on/off |
| `FilterEQ3`      | Slope toggle (24 ↔ 48) |
| `Eq8`            | Lock to track |
| Anything / none  | Lock to track |

`APC40_User_Manual.md` extended with an EQ Eight bullet describing the 2 × 4 encoder layout under Shift + Send B.

## Verification

```bash
python3 -c "import ast; ast.parse(open('EncoderEQComponent.py').read())"
grep -n "EQ8_EXTRAS\|_setup_eq8_extras\|'8 Gain A'\|'8 Filter On A'" EncoderEQComponent.py   # multi-hit
grep -n "EQ Eight" APC40_User_Manual.md   # 1 hit
```

Hardware UAT (still required, in Live):

- On a track with EQ Eight (and bands 1, 2, 8 active): enter Shift + Send B. Encoders 5/6/7 should drive bands 1, 2, 8 gains; encoders 1/2/3 drive their frequencies; encoder 0 = Scale; encoder 4 = Output Gain. Send A / B / C toggle bands 1 / 2 / 8 on/off (with toggle-momentary).
- Open `Log.txt` after first EQ8 activation and confirm `'Output Gain'` is the right parameter name. If different (e.g. `'Gain'`), paste the `[Eq8]` lines.
- Switch between Eq8 / FilterEQ3 / ChannelEq / no-EQ tracks — encoder bindings should swap cleanly each time, with no stale connections.
