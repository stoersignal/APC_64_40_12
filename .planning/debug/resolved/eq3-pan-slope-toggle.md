---
slug: eq3-pan-slope-toggle
status: resolved
trigger: when EQ3 is used in "TRACK CONTROL MODE 3" the first button (PAN) should be used to switch between 24/48 slope
created: 2026-05-04
updated: 2026-05-04
---

# Debug Session — Pan button = FilterEQ3 Slope toggle

## Symptoms

- In TRACK CONTROL MODE 3 (Shift + Send B), the Pan button currently controls "lock-to-track" (`set_lock_button(self._buttons[0])`).
- The user wants the Pan button to toggle FilterEQ3's **Slope** parameter (24 ↔ 48 dB/oct) when the active EQ device is FilterEQ3.
- Channel EQ already gets a special Pan-button role (Highpass on/off) — this session adds a third role: Slope toggle for FilterEQ3.

## Root cause / design

Pan-button behavior in EQ Smart Control mode is now resolved per device class:

| EQ device on track     | Pan button role                                  |
|------------------------|--------------------------------------------------|
| `ChannelEq`            | Highpass on/off  (shipped 5660914)               |
| `FilterEQ3`            | Slope toggle (24 ↔ 48 dB/oct)  ← NEW             |
| `Eq8`, `AudioEffectGroupDevice`, none | Lock to track  (default, original behavior) |

Implementation mirrors the Channel EQ pattern in 5248cce / 5660914:
- New state on `EncoderEQComponent`: `_slope_button`, `_slope_parameter`, `_slope_listener_attached`, `_filter_eq3_logged`.
- New helpers: `_setup_slope_button`, `_teardown_slope_button`, `_slope_value`, `_on_slope_changed`, `_update_slope_led` — same shape as the highpass helpers.
- Branch in `_update_controls_and_buttons`: ChannelEq first, then FilterEQ3, else lock fallback.
- One-shot Log.txt dump of FilterEQ3's parameter names on first detection (gated by `_filter_eq3_logged`) — verifies the `'Slope'` parameter-name guess in one UAT round if needed, same lesson as the Channel EQ dump.
- LED convention: ON when value > 0 (48 dB/oct), OFF otherwise (24 dB/oct).
- `disconnect` extended to call `_teardown_slope_button` alongside `_teardown_channel_eq_extras`.

## Files changed

- `EncoderEQComponent.py` — slope-button state + helpers + Pan-button branch + disconnect cleanup.
- `APC40_User_Manual.md` — Slope-toggle bullet under Shift + Send B.

## Verification

```bash
python3 -c "import ast; ast.parse(open('EncoderEQComponent.py').read())"
grep -n "_slope_button\|_setup_slope_button\|'Slope'" EncoderEQComponent.py   # multi-hit
grep -n "FilterEQ3 Slope toggle" APC40_User_Manual.md   # 1 hit
```

Hardware UAT (still required, in Live):

- On a track with FilterEQ3: enter Shift + Send B. Pan button LED reflects current Slope state. Tap Pan → Slope toggles between 24 and 48 dB/oct in Live's UI; LED matches.
- On a track with Eq8 / Audio Effect Rack: Pan button stays on its lock function.
- On a track with Channel EQ: Pan button stays on its Highpass on/off role (untouched by this change).
- Switching between FilterEQ3 / Eq8 / ChannelEq tracks should re-bind Pan correctly with no stale listeners.
- Open `Log.txt` after first FilterEQ3 activation and confirm the parameter is named `'Slope'`. If different, paste the `[FilterEQ3]` lines and I'll patch the dictionary.
