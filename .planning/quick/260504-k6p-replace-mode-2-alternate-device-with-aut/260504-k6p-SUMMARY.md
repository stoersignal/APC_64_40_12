---
quick_id: 260504-k6p
description: replace MODE 2 (Alternate Device) with AutoFilter mode
date: 2026-05-04
status: complete
---

# Quick Task 260504-k6p — Summary

TRACK CONTROL MODE 2 (Shift + Send A) is now a focused **Auto Filter Mode**. When the selected track contains a Live `AutoFilter` device, the 8 Track Control encoders + 4 bank buttons re-bind to that device's most-used parameters — same shape as the EQ Smart Control mode (Shift + Send B).

## What changed

| File | Change |
|------|--------|
| `EncoderAutoFilterComponent.py` (new) | `EncoderAutoFilterComponent(ControlSurfaceComponent)`. Detects AutoFilter on the selected track via `class_name == 'AutoFilter'`. `_update_controls_and_buttons` binds 8 encoders + 4 buttons per `ENCODER_MAP` / `BUTTON_MAP`. Bank-button LEDs track parameter values via `add_value_listener`. One-shot Log.txt dump on first detection. |
| `APC_64_40_9.py` | Imports the new component; instantiates `EncoderAutoFilterComponent(self._mixer, self)` in place of `EncoderDeviceComponent`. Variable name `_encoder_device_modes` retained — referenced by `EncoderUserModesComponent` / `ShiftableEncoderSelectorComponent`. |
| `EncoderUserModesComponent.py` | Dropped the `_alt_device.*` cleanup block (lines 122-127) — old component-internal teardown that no longer applies. The new component self-cleans via `on_enabled_changed`. |
| `APC40_User_Manual.md` | Shift + Send A description rewritten as the new Auto Filter Mode bullet list. |

## Encoder + button layout

```
Top row    [0=Drive    ][1=Env Atk  ][2=Env Rel  ][3=LFO Rate ]
Bottom row [4=Frequency][5=Resonance][6=Env Amt  ][7=LFO Amt  ]
Bank btns  [Pan=Slope↻ ][SndA=LFO   ][SndB=Type↻ ][SndC=Sidech]
```

- Pan → `Filter Slope` cycle (12 → 24 → 48 dB/oct, wraps at `param.max`).
- Send A → `LFO On` toggle (on/off).
- Send B → `Filter Type` cycle (LP → HP → BP → Notch → Morph, wraps at `param.max`).
- Send C → `Sidechain Mix` toggle (on/off when the parameter is present; gracefully no-ops on Live builds where the param isn't named that way).
- LED on each bank button reflects the parameter's value (`> 0 → on`).

## Live API parameter names — diagnostic dump

The first activation of Auto Filter Mode logs the device's full parameter list to `Log.txt`:

```
[AutoFilter] params on detected device:
[AutoFilter]   'Device On'
[AutoFilter]   'Frequency'
[AutoFilter]   'Resonance'
... etc
```

If any of the guessed parameter names (`'Drive'`, `'Env. Attack'`, `'Env. Release'`, `'LFO Rate'`, `'Frequency'`, `'Resonance'`, `'Env. Amount'`, `'LFO Amount'`, `'Filter Slope'`, `'LFO On'`, `'Filter Type'`, `'Sidechain Mix'`) don't match Live's actual names on the user's build, the log block reveals the truth and `AUTOFILTER_PARAMS` can be patched in seconds.

## Verification gates (passed at end of execution)

```
python3 -c "import ast; ast.parse(open('EncoderAutoFilterComponent.py').read()); ast.parse(open('APC_64_40_9.py').read()); ast.parse(open('EncoderUserModesComponent.py').read())"   # OK
grep -n '_alt_device\.' EncoderUserModesComponent.py   # empty
grep -n 'EncoderAutoFilterComponent' APC_64_40_9.py    # 2 hits
grep -n 'Auto Filter Mode' APC40_User_Manual.md        # 1 hit
```

## Hardware UAT (still required, in Live)

- Place an Auto Filter on a track, enter Shift + Send A. Encoders 1..4 (top row) drive Drive / Env Atk / Env Rel / LFO Rate; encoders 5..8 (bottom row) drive Frequency / Resonance / Env Amt / LFO Amt. Bank buttons cycle / toggle Slope / LFO / Type / Sidechain. LEDs match.
- Open `Log.txt` after first activation and confirm the parameter names. Paste `[AutoFilter]` block if any need patching.
- Track without an AutoFilter: encoders / buttons released, LEDs off, no errors.
- Switch between AutoFilter / non-AutoFilter tracks — bindings re-evaluate on track-selection.
- Switch between Mode 1 (Pan/Send), Mode 2 (AutoFilter), Mode 3 (EQ Smart Control), Mode 4 (User mode) — encoder/button bindings swap cleanly with no stuck state.

## Out of scope

- Toggle/momentary dual behavior on bank buttons (the user asked for plain on/off / cycle).
- Real-time re-detection on device-add (track-selection retrigger covers this).
- Multi-state LED to display enum values for Slope / Filter Type — APC40 buttons are one-color on/off, so the LED just lights when the param is non-zero.
- Removing the now-unused `EncoderDeviceComponent.py` — kept in the repo for reference; not instantiated anywhere.
