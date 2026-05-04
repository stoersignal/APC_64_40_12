---
slug: eq3-led-inverted
status: resolved
trigger: LEDs for the kill switches of the EQ3 are wrong (LEDs are on, when switch is off and the other way round)
created: 2026-05-04
updated: 2026-05-04
---

# Debug Session — EQ3 kill-switch LEDs inverted

## Symptoms

- In TRACK CONTROL MODE 3 (Shift + Send B) on a track with `FilterEQ3`, the Send A / B / C kill-button LEDs are inverted: LED is ON when the band is OFF in Live, LED is OFF when the band is ON.
- Eq8 and Audio Effect Rack tracks behave correctly (LED tracks the band's enabled state).
- Independent of the toggle/momentary work shipped in 260504-i1b — that change only touched `_cut_value`, not the LED-paint paths.

## Root cause

`SpecialTrackEQComponent` had a per-device-class LED inversion in two places:

- `EncoderEQComponent.py:460-465` (`update()`)
- `EncoderEQComponent.py:491-496` (`_on_cut_changed()`)

```python
if self._device.class_name == 'FilterEQ3':
    if parameter.value == 0.0:        # band OFF
        self._cut_buttons[index].turn_on()  # LED ON  ← non-standard
else:
    if parameter.value > 0.0:         # band ON
        self._cut_buttons[index].turn_on()  # LED ON  ← standard
```

FilterEQ3's `LowOn` / `MidOn` / `HighOn` parameters use `1.0 = band ON, 0.0 = band OFF` — same as every other device's on/off parameters. The original code special-cased FilterEQ3 to invert the LED ("LED on means kill engaged") which conflicted with the Eq8 / AudioEffectGroupDevice convention ("LED on means band passing").

## Fix

Drop the FilterEQ3 branch — all devices now share the standard convention `parameter.value > 0 → LED on`. Both `update()` and `_on_cut_changed()` patched.

## Files changed

- `EncoderEQComponent.py` — drop FilterEQ3 LED inversion in `SpecialTrackEQComponent.update` and `_on_cut_changed`.

## Verification

After patching:

```bash
grep -n "FilterEQ3" EncoderEQComponent.py
```

Should only show:
- the `EQ_DEVICES` dictionary entry (line 38), and
- the comment on line 42 referencing the FilterEQ3 layout for muscle-memory consistency.

The `_set_filter_dev` / `_filter_value` device-class checks against `'FilterEQ3'` inside the LED-paint code paths are gone.
