---
quick_id: 260504-hea
description: use Stop All Clips to randomize macros in both Variations modes
date: 2026-05-04
status: complete
uat_passed: 2026-05-04
final_commit: dd3c423
commits:
  - dd3c423 feat — Stop All Clips → randomize_macros wired in both Variations modes
  - ec4df18 docs — STATE.md commit-hash backfill
---

# Quick Task 260504-hea — Summary

The **Stop All Clips** button (APC40 note 81, plain `_Framework.ButtonElement`) is repurposed inside both Variations modes to randomize rack macros via Live's `device.randomize_macros()` API. Outside these modes it keeps its default clip-stop behavior.

## What changed

| File | Change |
|------|--------|
| `MatrixModesComponent.py` | Added `_variations_stop_all_value` (slot 7) and `_global_var_stop_all_value` (slot 6) handlers + state attributes (`_variations_stop_all_button`, `_global_var_stop_all_button`). Both `_set_*_mode` methods detach the session's stop-all wiring (`set_stop_all_clips_button(None)`) and add my listener; both `_teardown_*_mode` methods remove the listener and restore (`set_stop_all_clips_button(self._parent._stop_all_button)`). |
| `docs/manual.html` | Extended the `desc` strings on `'Variations'` and `'GlobalVariations'` mode definitions with the new Stop-All-Clips → randomize_macros behavior. |
| `APC40_User_Manual.md` | Added a "Randomize Macros" bullet to both Variations subsections — "every column at once" for the global mode, "on the appointed device" for the per-device mode. |

## Behavior

- **Slot 7 (per-device Variations Mode)** — Stop All Clips → `appointed_device.randomize_macros()`. No-op when no device is appointed or the appointed device isn't a Rack (`hasattr(device, 'randomize_macros')` guard).
- **Slot 6 (Global Variations Mode)** — Stop All Clips → `rack.randomize_macros()` for every non-None entry in `_global_var_track_racks`. One button press randomizes all eight columns' racks at once.
- **Outside both modes** — `set_stop_all_clips_button(self._parent._stop_all_button)` is restored on teardown, so Stop All Clips reverts to clip-stop behavior.
- All API calls are wrapped in `try/except` so a single failing rack doesn't break the rest.

## Live API note

`Live.RackDevice.RackDevice.randomize_macros()` is the Live API method that randomizes the macro values of a Rack device. Guarded by `hasattr` so a non-Rack appointed device (or older Live build without the method) silently no-ops instead of crashing.

## Reusable lessons applied (from the previous Variations tasks)

- The Stop All Clips button is plain `ButtonElement` (`APC_64_40_9.py:99`), so we do NOT call `set_enabled` / `set_on_off_values` on it (the bug from 260504-8yh `d1bb8fa` that kept the grid dark).
- We only call `add_value_listener` / `remove_value_listener` and let the framework wire MIDI dispatch normally.
- Detach via `_session.set_stop_all_clips_button(None)` before adding our listener, restore it on teardown — same pattern used for Bank Select Up/Down in slot 6.

## Hardware UAT (passed 2026-05-04)

User confirmed working in Ableton Live: Stop All Clips randomizes macros on the appointed device in slot 7, and on every column's rack in slot 6. Default clip-stop behavior restored on mode exit. No iteration cycles needed — the lessons accumulated through 260504-5j0 and 260504-8yh (plain `ButtonElement` semantics, hasattr-guarded Live API calls, takeover-and-restore pattern) made this land first try.

## Out of scope

- Auto-saving the randomized state as a new variation.
- Per-column randomize trigger in slot 6 (single button = randomize all columns at once, matching the user's "rack/racks" wording).
- LED feedback on the Stop All Clips button while it's owned by these modes.
