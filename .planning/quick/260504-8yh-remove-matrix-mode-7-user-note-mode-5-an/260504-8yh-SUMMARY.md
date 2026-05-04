---
quick_id: 260504-8yh
description: remove "MATRIX MODE 7 – USER/NOTE MODE 5" and add a new global variations mode
date: 2026-05-04
status: complete
uat_passed: 2026-05-04
final_commit: d1bb8fa
commits:
  - 2db6430 feat — initial Global Variations Mode + USER MODE 5 removal
  - c6235c1 docs — STATE.md commit-hash backfill
  - 0de8cd8 fix — visible_tracks instead of clip_slot.canonical_parent (returned Scene on Live 12)
  - 3ef0475 debug — log_message diagnostics (removed in d1bb8fa)
  - d1bb8fa fix — drop set_enabled/set_on_off_values on plain ButtonElement (scene-launch + bank-up/down crashed AttributeError on entry)
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

## Hardware UAT (passed 2026-05-04)

User confirmed working in Ableton Live with racks-on-visible-tracks: pad recall (per-track), scene launch (global trigger), Bank Up/Down scroll, and clean transition out of the mode (scene-launch + bank-select restored to their normal session behavior).

## Iteration history (notes for future similar tasks)

Two non-obvious gotchas surfaced through UAT:

- **`clip_slot.canonical_parent` returns the Scene on Live 12, not the Track.** First fix attempt (0de8cd8) switched to `self.song().visible_tracks[session.track_offset() + i]` — the proven pattern from `SpecialMixerComponent.py:46-47` in this codebase. Should be the first reach for "8 visible tracks" lookups in any future component.
- **Scene-Launch and Bank-Select buttons are plain `_Framework.ButtonElement`, not `ConfigurableButtonElement`.** Calling `set_enabled(True)` / `set_on_off_values(...)` on them throws `AttributeError` and aborts whatever method is in flight before any value-listener side effects run. (Construction sites: `APC_64_40_9.py:81-82` and `:93`.) Plain `ButtonElement` is always enabled and routes value listeners directly; LED paint goes through `send_value(color)` without the on/off cache. Matrix pads (`self._matrix.get_button(...)`) remain `ConfigurableButtonElement` and continue to use the cached `set_on_off_values + send_value(force=True)` path.

The diagnostic `log_message('[GlobalVar] ...')` instrumentation in 3ef0475 made the second issue visible immediately — the entry log printed but the rebind log never did, with the traceback in `Log.txt` pointing straight at `scene_button.set_enabled(True)`. Worth keeping in mind for future Live UAT loops: a few `log_message` calls beat any number of guesses.

## Out-of-scope follow-ups (deferred, not blocking)

- Per-column scroll offsets (single global offset only).
- Recursing into nested racks for the rack-per-column scan (top-level `track.devices` only).
- Track Stop row repurposing (default clip-stop kept).
- Shift+Bank-Select for session scroll while inside this mode (Bank Up/Down currently fully owned by variation paging).
- Handling for return tracks / master track in the column scan (only regular session tracks are addressable from the 8-column grid).
