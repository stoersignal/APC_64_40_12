---
quick_id: 260504-i1b
description: toggle/momentary kill switches in EQ Smart Control mode (Shift + Send B)
date: 2026-05-04
status: complete
---

# Quick Task 260504-i1b — Summary

The three EQ kill buttons in TRACK CONTROL MODE 3 (Shift + Send B = EQ / Filter Smart Control) gain the same toggle / momentary dual-behavior the v1.0 Solo / Mute buttons already have:

- **Short tap (< 400 ms)** — toggle the kill on / off (existing behavior, preserved).
- **Long hold (≥ 400 ms)** — momentary: kill engages on press, reverts to the previous state on release.

Outside this mode the buttons stay normal Pan / Send A / Send B / Send C bank selectors — only the in-mode press/release handler is patched.

## What changed

| File | Change |
|------|--------|
| `EncoderEQComponent.py` | Added module-level `LONG_PRESS_DELAY = 4` (matching `ToggleMomentaryChannelStripComponent.py:8`). Extended `SpecialTrackEQComponent` with three per-cut state arrays (`_cut_ticks_delay`, `_cut_state_before_press`, `_cut_momentary_active`), a `_register_timer_callback(self._on_timer)` registration in `__init__`, and a matching `_unregister_timer_callback` in a new `disconnect`. Rewrote `_cut_value` to branch press / release: press captures pre-press state + toggles parameter + starts countdown; release reverts to captured state if the hold crossed the 400 ms threshold. Added `_on_timer` for the per-button countdown, and `set_cut_buttons` resizes the state arrays to the new button count and reverts any in-flight momentary on the outgoing buttons. |
| `APC40_User_Manual.md` | Appended a Toggle / Momentary kill-switches sub-bullet to the existing **Shift + Send B** description (§2 Track Control Modes), naming the bands (bass / mids / highs) and the 400 ms threshold. |

## State machine (for cut index `i`)

```
press (value != 0):
    pre_press[i] = parameter.value
    parameter.value = (1 if was 0 else 0)  [scaled ×127 for AudioEffectGroupDevice]
    ticks_delay[i] = LONG_PRESS_DELAY  (4 ticks = 400ms)

timer tick (every 100ms):
    if ticks_delay[i] > -1:
        if ticks_delay[i] == 0:
            momentary_active[i] = True
        ticks_delay[i] -= 1

release (value == 0):
    if momentary_active[i]:
        parameter.value = pre_press[i]
        momentary_active[i] = False
    ticks_delay[i] = -1
```

Mirrors `ToggleMomentaryChannelStripComponent._handle_toggle_momentary` exactly, with the key difference that EQ's kill state is on a *parameter*, not a track property — so the read/write is `parameter.value` instead of `setattr(track, ...)`.

## Edge cases handled

- **`_ignore_cut_buttons`** flag (set during mode transitions in `ShiftableEncoderSelectorComponent.py:84`) is honored — both press and release fast-return when set, so a mode transition mid-press cannot corrupt state.
- **`set_cut_buttons(buttons)`** reverts any active momentary on the OUTGOING buttons before swapping. Without this, a held band would stay killed after the user leaves EQ Smart Control mode.
- **`disconnect`** reverts any in-flight momentary AND unregisters the timer.
- **`AudioEffectGroupDevice`** parameter scaling (×127) preserved — the press path keeps the existing scale step exactly.
- **`Eq8`** has 8 cut names but only 3 buttons are wired (`EncoderEQComponent.py:506`); only cut indices 0..2 participate, which is what the user wants for the bass/mids/highs metaphor.

## Verification gates (all passed at end of execution)

```
python3 -c "import ast; ast.parse(open('EncoderEQComponent.py').read())"  # OK
grep -n '_cut_ticks_delay\|_cut_momentary_active\|_cut_state_before_press' EncoderEQComponent.py  # 10+ hits across init / disconnect / set_cut_buttons / _on_timer / _cut_value
grep -n 'LONG_PRESS_DELAY' EncoderEQComponent.py  # 2 hits (constant + use)
grep -n '_register_timer_callback\|_unregister_timer_callback' EncoderEQComponent.py  # 2 hits
grep -n 'Toggle / Momentary kill switches' APC40_User_Manual.md  # 1 hit
```

## Hardware UAT (still required, in Live)

- Engage TRACK CONTROL MODE 3 (Shift + Send B). On a track with FilterEQ3 (or Audio Effect Rack with Macro 6/7/8 wired), the Send A / B / C buttons should light per the kill state.
- Tap any kill button briefly (< 400 ms): kill toggles on / off, persists after release.
- Hold any kill button longer than 400 ms: kill engages on press, reverts on release (band returns to previous state).
- Switch tracks while holding a kill long: held state should NOT persist on the new track (timer ticks but the held button gets re-bound through `set_cut_buttons`, which reverts).
- Leave the mode (any other Shift+bank combination) while holding a kill long: kill should revert immediately (`_ignore_cut_buttons` + `set_cut_buttons(None)` cleanup paths cover this).

## Out of scope

- LED feedback during the held momentary phase — the existing `_on_cut_changed` listener paints LEDs from the parameter value via the value-changed listener, so the LED naturally tracks the held state.
- Eq8's 4..7 cut indices — only the first three are wired through `set_cut_buttons` in this mode.
- Other buttons in EQ Smart Control mode (Pan / lock / encoder Track Control knobs) — only the kill buttons (cut indices 0..2) get the new behavior.
- Tests under `tests/` — not extended; the dual behavior is small and the hardware UAT covers it.
