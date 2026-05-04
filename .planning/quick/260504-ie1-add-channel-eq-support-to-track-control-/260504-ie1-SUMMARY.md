---
quick_id: 260504-ie1
description: add Channel EQ support to TRACK CONTROL MODE 3 (Shift + Send B)
date: 2026-05-04
status: complete
uat_passed: 2026-05-04
final_commit: 5660914
commits:
  - 5248cce feat — Channel EQ detection + extras wiring + Log.txt diagnostic dump
  - 847a44f docs — STATE.md commit-hash backfill
  - 5660914 fix — output param is 'Output' (not 'Output Gain'); diagnostic dump removed after serving its purpose
---

# Quick Task 260504-ie1 — Summary

EQ Smart Control mode (Shift + Send B) now recognises Live's **Channel EQ** device (`class_name = 'ChannelEq'`, Live 11+) — which the original `EncoderEQComponent.py` was written before and so previously ignored.

## What changed

| File | Change |
|------|--------|
| `EncoderEQComponent.py` | Added `'ChannelEq'` to `EQ_DEVICES` (with `Gains: ['Low Gain', 'Mid Gain', 'High Gain']` and empty `Cuts`). Added a `CHANNEL_EQ_EXTRAS` dict (`'Output Gain'`, `'Mid Freq'`, `'Highpass On'`). Added `EncoderEQComponent` state for the active Channel EQ device + Highpass button, plus `_detect_channel_eq` / `_setup_channel_eq_extras` / `_teardown_channel_eq_extras` / `_setup_highpass_button` / `_teardown_highpass_button` / `_highpass_value` / `_on_highpass_changed` / `_update_highpass_led`. Removed the eager `self.set_lock_button(self._buttons[0])` from `set_controls_and_buttons` so the Pan-button role is decided per track in `_update_controls_and_buttons` — Channel EQ tracks get Pan = Highpass; everything else gets the original Pan = lock. |
| `APC40_User_Manual.md` | Extended the Shift + Send B description with a Channel EQ subsection. |

## Behavior

- **When the selected track has a `ChannelEq` device**, EQ Smart Control mode wires it up:
  - **Encoder 0** (first knob) → `Mid Freq` (the user's "split frequency").
  - **Encoder 4** (knob to the left of the gain bands) → `Output Gain`.
  - **Encoders 5 / 6 / 7** → `Low Gain` / `Mid Gain` / `High Gain` — same encoders used for FilterEQ3 / Audio Effect Rack.
  - **Pan button** → `Highpass On` toggle (replaces the lock button while Channel EQ is active). LED tracks the parameter via `add_value_listener`.
  - **Send A / B / C** stay dark (Channel EQ has no per-band on/off; the kill code's `'Cuts': []` causes the toggle/momentary handler from 260504-i1b to fast-return).
- **When the selected track has no `ChannelEq`**, the existing wiring is preserved exactly: AutoFilter on encoders 0/4 (via `SpecialTrackFilterComponent`), lock on Pan button, kill switches with toggle/momentary behaviour on Send A/B/C.
- **Track-selection switching** between Channel EQ and non-Channel EQ tracks correctly tears down whichever path was active and brings up the other one — the Pan button reattaches to lock or highpass as needed; encoders 0/4 release / re-bind cleanly.

## Live API parameter names — diagnostic dump

On the FIRST activation of a Channel EQ device the script writes one block to `Log.txt`:

```
[ChannelEq] params on detected device:
[ChannelEq]   'Device On'
[ChannelEq]   'Highpass On'
[ChannelEq]   'Low Gain'
... etc
```

This is a one-shot dump (gated by `_channel_eq_logged`). If the parameter names I guessed (`'Mid Freq'`, `'Output Gain'`, `'Highpass On'`, `'Low Gain'`, `'Mid Gain'`, `'High Gain'`) don't match Live's actual names on the user's build, the log will reveal the truth in one UAT round and the dictionary entries can be patched in seconds.

## Verification gates (all passed at end of execution)

```
python3 -c "import ast; ast.parse(open('EncoderEQComponent.py').read())"  # OK
grep -n "'ChannelEq'\|CHANNEL_EQ_EXTRAS" EncoderEQComponent.py  # 5+ hits
grep -n "_channel_eq_device\|_highpass_button" EncoderEQComponent.py  # 6+ hits
grep -n "Channel EQ" APC40_User_Manual.md  # multiple hits in the Shift+Send B section
```

## Hardware UAT (passed 2026-05-04)

User confirmed all five encoder + button mappings working in Live with a Channel EQ on the track: encoders 0/4 (Mid Freq + Output) and 5/6/7 (Low/Mid/High Gain) drive their parameters; the Pan button toggles Highpass on/off with correct LED tracking. Non-Channel-EQ tracks fall back to AutoFilter + lock unchanged.

## Iteration history

The diagnostic `log_message` dump shipped in the initial commit (5248cce) caught the one parameter-name miss in a single UAT round: Live names the output trim simply `'Output'`, not `'Output Gain'` as the initial guess assumed. Fix landed in 5660914 alongside removal of the one-shot dump. The other guessed names (`Mid Freq`, `Highpass On`, `Low Gain`, `Mid Gain`, `High Gain`) were correct first try.

Reusable lesson: **for Live API parameter-name guesses, ship the one-shot `device.parameters` dump in the initial commit.** The dump is ~5 lines, costs nothing on the happy path (only fires once per session), and turns "is this the right name?" from a multi-round UAT loop into a single Log.txt paste.

## Out of scope

- Toggle/momentary on the Highpass button (the user asked for plain on/off; Solo/Mute-style dual behavior is a separate ask).
- Real-time re-detection if Channel EQ is ADDED to a track without a subsequent track-selection change. Track-selection updates trigger `on_selected_track_changed` → `_update_controls_and_buttons`. Adding/removing a device on the currently-selected track without re-selecting it relies on the lower `_track_eq` device-listener path; the `EncoderEQComponent`-level extras don't have their own `add_devices_listener`.
- LED state of the Send A / B / C buttons during Channel EQ — they're dark via the existing empty-`Cuts` paint loop.
- Changes to other matrix / fader / snapshot modes — only the EQ Smart Control encoder + Pan-button wiring is affected.
