---
quick_id: 260504-hea
description: use Stop All Clips to randomize macros in both Variations modes
created: 2026-05-04
mode: quick
must_haves:
  truths:
    - The Stop All Clips button (`_stop_all_button`) is a plain `_Framework.ButtonElement` (`APC_64_40_9.py:99-101`, MIDI note 81). It is wired into the session via `self._session.set_stop_all_clips_button(self._stop_all_button)`. To take it over inside a mode we must detach that session hook (`set_stop_all_clips_button(None)`) and restore it on teardown.
    - Plain `ButtonElement` does NOT expose `set_enabled` / `set_on_off_values` (lesson from 260504-8yh `d1bb8fa`). Only `add_value_listener` / `remove_value_listener` / `send_value(color)` are safe to call.
    - Live API: `Live.RackDevice.RackDevice.randomize_macros()` randomizes the macro values of a Rack device. It is the canonical "randomize the macros" call referenced by the user. Guard with `hasattr` so older Live builds without the method don't crash.
    - Slot 7 (per-device Variations Mode, 260504-5j0) operates on `song().appointed_device`; slot 6 (Global Variations Mode, 260504-8yh) operates on the cached `_global_var_track_racks` list (one rack per visible track).
  artifacts:
    - MatrixModesComponent.py — extends both `_set_variations_mode` / `_teardown_variations_mode` (slot 7) and `_set_global_variations_mode` / `_teardown_global_variations_mode` (slot 6) to take over Stop All Clips. Adds `_variations_stop_all_value` and `_global_var_stop_all_value` handlers.
    - docs/manual.html — `'Variations'` and `'GlobalVariations'` mode definitions get a Stop-All-Clips note (it's an APC40 button to the LEFT of the matrix; not part of the matrix-mode-strip's per-cell tooltips, but the `desc` should mention it).
    - APC40_User_Manual.md — both Variations subsections gain a "Randomize Macros" line.

  scope_out:
    - Storing the randomized values as a new variation (Shift+Tap Tempo still does that).
    - Per-track randomize in Global mode (single button = randomize ALL columns at once, matching the user's wording "the rack/racks").
    - Visual LED feedback on the Stop All Clips button — left at default (we just take over the press handler; the button's LED is hardware-driven).
    - Touching the Track Stop row, Scene Launch, Bank Select, etc.
---

# Quick Task 260504-hea — Stop All Clips → randomize macros (both Variations modes)

## Goal

Inside Variations Mode (slot 7) and Global Variations Mode (slot 6), pressing the **Stop All Clips** button randomizes the macros of the relevant rack(s) instead of stopping clips:

- Slot 7 (per-device): randomize the appointed device's macros (`device.randomize_macros()`).
- Slot 6 (global): randomize the macros of every column's rack — one button, all eight tracks at once.

Outside these two modes the Stop All Clips button keeps its default behavior (the session's stop-all hook).

## Tasks

### Task 1 — Slot 7 (per-device Variations Mode): take over Stop All Clips

**Files:** `MatrixModesComponent.py`

**Action:**
1. Add `self._variations_stop_all_button = None` to `__init__` alongside the existing `_variations_*` state.
2. In `_set_variations_mode`, after the appointed-device listener block:
   ```python
   try:
       self._session.set_stop_all_clips_button(None)
   except Exception:
       pass
   stop_all = self._parent._stop_all_button
   stop_all.add_value_listener(self._variations_stop_all_value)
   self._variations_stop_all_button = stop_all
   ```
3. In `_teardown_variations_mode`, before the song-listener detach:
   ```python
   if self._variations_stop_all_button is not None:
       try:
           self._variations_stop_all_button.remove_value_listener(self._variations_stop_all_value)
       except Exception:
           pass
       self._variations_stop_all_button = None
   try:
       self._session.set_stop_all_clips_button(self._parent._stop_all_button)
   except Exception:
       pass
   ```
4. Add the handler:
   ```python
   def _variations_stop_all_value(self, value):
       if not self.is_enabled() or value == 0:
           return
       device = self.song().appointed_device
       if device is None or not hasattr(device, 'randomize_macros'):
           return
       try:
           device.randomize_macros()
       except Exception:
           return
   ```

**Verify:** `python3 -c "import ast; ast.parse(open('MatrixModesComponent.py').read())"` succeeds; `grep -n '_variations_stop_all_value\|set_stop_all_clips_button(None)' MatrixModesComponent.py` shows the new code.

---

### Task 2 — Slot 6 (Global Variations Mode): take over Stop All Clips

**Files:** `MatrixModesComponent.py`

**Action:**
1. Add `self._global_var_stop_all_button = None` to `__init__` alongside the existing `_global_var_*` state.
2. In `_set_global_variations_mode`, after the bank-up/down listener block:
   ```python
   try:
       self._session.set_stop_all_clips_button(None)
   except Exception:
       pass
   stop_all = self._parent._stop_all_button
   stop_all.add_value_listener(self._global_var_stop_all_value)
   self._global_var_stop_all_button = stop_all
   ```
3. In `_teardown_global_variations_mode`, alongside the bank-button detach:
   ```python
   if self._global_var_stop_all_button is not None:
       try:
           self._global_var_stop_all_button.remove_value_listener(self._global_var_stop_all_value)
       except Exception:
           pass
       self._global_var_stop_all_button = None
   try:
       self._session.set_stop_all_clips_button(self._parent._stop_all_button)
   except Exception:
       pass
   ```
4. Add the handler:
   ```python
   def _global_var_stop_all_value(self, value):
       if not self.is_enabled() or value == 0:
           return
       for (_track, rack) in self._global_var_track_racks:
           if rack is None or not hasattr(rack, 'randomize_macros'):
               continue
           try:
               rack.randomize_macros()
           except Exception:
               continue
   ```

**Verify:** `grep -n '_global_var_stop_all_value\|self._global_var_stop_all_button' MatrixModesComponent.py` shows the new code in both setup and teardown.

---

### Task 3 — Documentation

**Files:** `docs/manual.html`, `APC40_User_Manual.md`

**Action:**
- `docs/manual.html` — extend the `desc` strings of both `'Variations'` and `'GlobalVariations'` mode definitions to mention "Stop All Clips → randomize macros".
- `APC40_User_Manual.md` — append a "Randomize Macros" bullet to both Variations subsections.

**Verify:** `grep -n 'randomize_macros\|Randomize Macros\|Stop All Clips.*randomize' MatrixModesComponent.py docs/manual.html APC40_User_Manual.md` shows hits in all three files.

---

## Out of scope

- Capturing the randomized state into a new variation (Shift+Tap Tempo path is unaffected).
- Per-track randomize trigger in Global mode (one button randomizes all eight columns simultaneously).
- LED feedback on the Stop All Clips button.
- Slot teardown does not need to re-paint the Stop All button — Live's session handles that on next paint.
