---
quick_id: 260504-8yh
description: remove "MATRIX MODE 7 – USER/NOTE MODE 5" and add a new global variations mode
date: 2026-05-04
status: complete
---

# Quick Task 260504-8yh — Summary

Slot 6 of the matrix-mode selector becomes a **per-track variations cockpit**. Each grid column shows the variations of the first device on that column's visible track that has `variation_count > 0`. Bank Select Up/Down scrolls all 8 columns globally; Scene Launch buttons fire one row across every column at once. Slot 6's previous identity (User/Note Mode 5) is removed end-to-end. Slot 7 (per-device Variations Mode from 260504-5j0) is untouched.

## What changed

| File | Change |
|------|--------|
| `MatrixModesComponent.py` | Added `_set_global_variations_mode()`, `_teardown_global_variations_mode()`, `_global_var_rebind_tracks()`, `_global_var_on_song_tracks_changed()`, `_global_var_on_track_devices_changed()`, `_global_var_refresh_leds()`, `_global_var_pad_value()`, `_global_var_scene_value()`, `_global_var_bank_up_value()`, `_global_var_bank_down_value()`. Slot-6 dispatch (`_set_note_mode(PATTERN_5, ...)`) replaced with `_set_global_variations_mode()`. Teardown is invoked at every `_set_modes()` entry and from `disconnect()`. |
| `Matrix_Maps.py` | Deleted "Page 7 is User Mode 5" block (`USE_STOP_ROW_5`, `IS_NOTE_MODE_5`, `PATTERN_5`, `CHANNEL_5`, `NOTEMAP_5`). |
| `docs/manual.html` | Renamed mode-strip button `NoteMode5 → GlobalVariations`; removed `matrixMapsLiterals[5]`; replaced `'NoteMode5': makeNoteModeDef(5)` with hand-written `'GlobalVariations'` definition; updated 9-keys comment. |
| `APC40_User_Manual.md` | Inserted new "Global Variations Mode (Per-Track Rack Variations)" subsection above the existing "Variations Mode" subsection in §3 Matrix Modes. |

## Behavior contract (as implemented)

- **Pads (5×8 = 40)** — column = visible track (resolved via `clip_slot.canonical_parent`); row = variation index `bank_offset + row` on that column's first-rack-with-variations.
  - LED: green when `i = bank_offset + row < rack.variation_count`; red when `i == rack.selected_variation_index`; off otherwise (also off if column has no rack with variations).
  - Press: `rack.selected_variation_index = bank_offset + row; recall_selected_variation()`. Empty pads silently no-op.
- **Scene Launch row (5 buttons)** = global trigger. Press scene `R` → for every column with a stored variation at `bank_offset + R`, recall it. Tracks without that variation are skipped silently. LED green when ≥1 column has a stored variation at that row, else off.
- **Bank Select Up/Down** = global scroll offset. Down → `bank_offset += 1`. Up → `bank_offset = max(0, bank_offset - 1)`. Over-scrolled rows just show dark; no per-column ceiling.
- **Track Stop row** — left at default clip-stop wiring (the standard pre-mode setup in `_set_modes` handles it).
- **No rack on any column** — entire grid + scene strip dark, all presses are no-ops.
- **Refresh moments** — mode entry, bank scroll, pad press (after recall), scene press (after recall round), `track.add_devices_listener` fires (device add/remove), `device.add_variation_count_listener` fires (store/delete on a column's rack), `device.add_selected_variation_index_listener` fires (recall via Nudge or Live UI), `song.add_tracks_listener` / `add_visible_tracks_listener` fires (track structure changed → rebind columns).

## Decisions captured during /gsd-quick (2026-05-04 Q&A)

- **Rack pick**: first device with `variation_count > 0` on `track.devices` (skips racks that exist but have nothing stored).
- **Bank scroll**: single global offset applied to all columns.
- **Track Stop row**: kept at default clip-stop (matches the per-device Variations Mode contract).

## Live API mechanics worth knowing

- The Bank Select Up/Down buttons are normally owned by `_session.set_scene_bank_buttons` (`APC_64_40_9.py:90`). Entering Global Variations Mode detaches that wiring (`set_scene_bank_buttons(None, None)`); teardown restores it (`set_scene_bank_buttons(self._parent._down_button, self._parent._up_button)`).
- The Scene Launch buttons are normally bound via `scene.set_launch_button(button)` (`APC_64_40_9.py:110`). Entering this mode detaches them (`scene.set_launch_button(None)`); teardown restores them — this is the same takeover pattern Step Sequencer uses for lane-mute.
- Visible tracks are resolved via `self._session.scene(0).clip_slot(track_index).canonical_parent` per column — this works regardless of how `SessionComponent.track_offset()` is reported.
- `add_visible_tracks_listener` and `add_tracks_listener` rebind columns when the song's track structure changes (track add/remove/reorder, hide/show). `add_devices_listener` per-track rebinds when the user adds/removes a rack on one of the visible tracks.
- All listener attach/remove sites are guarded by `hasattr` + `try/except` so older Live builds without the variation listeners stay safe.

## Verification gates (all passed at end of execution)

```
python3 -c "import ast; ast.parse(open('MatrixModesComponent.py').read()); ast.parse(open('Matrix_Maps.py').read())"  # OK
grep -n 'PATTERN_5\|CHANNEL_5\|NOTEMAP_5\|USE_STOP_ROW_5\|IS_NOTE_MODE_5' Matrix_Maps.py MatrixModesComponent.py docs/manual.html  # empty
grep -n 'NoteMode5\|makeNoteModeDef(5)' docs/manual.html  # empty
grep -n '_set_global_variations_mode' MatrixModesComponent.py  # 2 hits
grep -n 'Global Variations Mode' APC40_User_Manual.md  # 2 hits
grep -n "data-mode=\"GlobalVariations\"\|'GlobalVariations'" docs/manual.html  # 2 hits
```

## Hardware UAT (still required, in Live)

- Hold Shift + Track Select 7 → enter Global Variations Mode. Each column with a rack-having-variations on its track lights green pads; the currently selected variation per column is red.
- Press a green pad → that variation recalls on that track's rack only; pad flips to red.
- Press Scene Launch 1 → every column with a stored variation at row 0 recalls it; the column's pad-LED at row 0 flips to red.
- Bank Down → window slides down by 1 row; pads repaint accordingly. Bank Up at offset 0 is a no-op.
- Add/remove a rack on a visible track via Live's UI → that column rebinds without leaving the mode.
- Scroll the session view → tracks-listener fires, columns rebind to the new visible tracks.
- Leave the mode (cycle to ClipLaunch) → Scene Launch + Bank Select buttons resume their normal session behavior; Track Stop row keeps clip-stop throughout.

## Out-of-scope follow-ups (deferred, not blocking)

- Per-column scroll offsets (single global offset only).
- Recursing into nested racks for the rack-per-column scan (top-level `track.devices` only).
- Track Stop row repurposing (default clip-stop kept).
- Shift+Bank-Select for session scroll while inside this mode (Bank Up/Down currently fully owned by variation paging).
- Handling for return tracks / master track in the column scan (only regular session tracks are addressable from the 8-column grid).
