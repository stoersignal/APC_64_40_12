# Quick Task 260504-m2x: Add Drum Rack Mode — Context

**Gathered:** 2026-05-04
**Status:** Ready for planning

<domain>
## Task Boundary

Add a new "Drum Rack Mode" to the APC40 control surface. When the selected
track contains a top-level Live Drum Rack device, the script automatically
enters Drum Rack Mode. While the mode is active, the listed APC40 controls
are retargeted from track-mixing to drum-chain-mixing semantics. The mode
captures only the listed controls; clip launch matrix, scene buttons,
transport, and other APC40 sections continue to behave as in the active
host mode.

### Controls captured by Drum Rack Mode

| Surface section | Drum Rack Mode behavior |
|---|---|
| 8 Track faders | Volume of the 8 in-focus drum chains |
| Track Mute buttons (8) | Mute on the corresponding drum chain |
| Track Solo buttons (8) | Solo on the corresponding drum chain |
| Track Control encoders (8, 2 rows × 4) | Pan / Send A / Send B / Send C of in-focus chains, depending on encoder mode |
| Track Control mode buttons (Pan / Send A / Send B / Send C) | Same role as in normal mode — selects encoder sub-mode |
| Bank Select up/down | Scroll the chain offset (when more than 8 chains exist) |
| Stop All Clips button LED | Visual indicator: lit when Drum Rack Mode is active |

### Controls NOT captured (preserve default behavior)

- 5×8 clip-launch matrix
- Scene Launch buttons
- Transport (Play / Stop / Rec / Tap / Nudge)
- Crossfader, Master volume, Cue Level
- Shift, Bank Select left/right (track navigation)
- Note / Clip Stop / Activator (matrix-mode-modifier buttons)

</domain>

<decisions>
## Implementation Decisions (locked)

### D-01 — Mode entry: automatic, track-selection-driven

- The mode auto-engages whenever the selected track has a top-level drum
  rack and the user has NOT manually exited it on this track.
- No dedicated entry combo. The user does not have to "switch" into the
  mode — selecting a track with a drum rack puts the script in the mode
  immediately.
- Detection runs on `on_selected_track_changed`.

### D-02 — Manual exit: Shift + Detail View, per-track scope (UPDATED post-UAT)

- Pressing **Shift + Detail View** (note 62, channel 0 — the 5th
  device-bank button) while in Drum Rack Mode exits the mode for the
  current track only. The captured controls revert to their normal
  (track-mixer) behavior on this track.
- Switching to a different track re-evaluates from scratch: if the new
  track has a drum rack, the mode auto-engages again.
- The "manually exited" override is **per-track** state — it does NOT
  persist across track changes.
- **Originally specified as Shift + Stop All Clips**; migrated during UAT
  round 4 because the Stop All Clips LED on APC40 mk1 turned out to be
  hardware-only and the indicator (D-06) needed to live on the same
  button as the exit combo. DetailViewCntrlComponent's existing handler
  gates on `not self._shift_pressed`, so unshifted Detail View still
  toggles Live's Detail panel — no conflict.

### D-03 — Mute/Solo: v1.0 toggle/momentary state machine

- Reuse `ToggleMomentaryChannelStripComponent` (or its existing pattern)
  to provide short-tap-toggles / long-hold-momentary on each chain's mute
  and solo. `LONG_PRESS_DELAY = 4` (400ms) — same as v1.0.
- Press-down fires immediately (zero latency); release after threshold
  reverts the chain to the pre-press state.
- Long-press momentary affects only the held chain — independent
  per-chain timer state.

### D-04 — Drum rack detection: first top-level drum rack on selected track

- Walk `track.devices` looking for the first device with
  `class_name == 'DrumGroupDevice'`. Top-level only — do NOT recurse into
  nested instrument/effect racks.
- If no top-level drum rack found, the mode does not engage and the script
  stays in the normal track-mixer behavior.

### D-05 — Empty state (no drum rack on selected track)

- Mode does not engage. APC40 stays in whatever mode was previously active
  (normal track mixer / Pan / Send modes / EQ Smart Control / AutoFilter
  Mode if Shift+Send A is held, etc.).
- Same pattern as AutoFilter Mode and EQ Smart Control: fail-quiet on
  detection miss.

### D-06 — Visual indicator: Detail View button LED (UPDATED post-UAT)

- The **Detail View button's LED** (5th device-bank button, note 62
  channel 0) is lit when Drum Rack Mode is active and off when not.
- The same button handles manual exit (Shift + Detail View) — one button
  serves both roles. LED tells you mode state, Shift+press flips it.
- LED updates on mode entry, mode exit, and track change. Periodic
  re-assertion via `_on_timer` defeats races with
  DetailViewCntrlComponent's own LED writes (which fire on Live's
  Detail-view visibility-change events).
- **Originally specified as Stop All Clips LED**; migrated during UAT
  round 4 after confirming that LED is hardware-only on APC40 mk1 (it
  never lights even from Live's own session writes when clips are
  playing — verified via diagnostic Log.txt instrumentation). Detail
  View was the user-chosen replacement.

</decisions>

<specifics>
## Specific Implementation Notes

### Drum-rack chain API (Live)

- `drum_rack.chains` — list of `DrumChain` objects (each pad on the rack).
- `drum_rack.return_chains` — separate list for the rack's return chains
  (out of scope for v1; only main chains are addressed).
- Each `chain.mixer_device` exposes:
  - `volume` (Parameter)
  - `panning` (Parameter)
  - `sends[]` (list of send Parameters — one per project return track)
  - `mute` (boolean attribute on chain, NOT mixer_device)
  - `solo` (boolean attribute on chain)
- `chain.name` — display name (typically the assigned drum sample / device).

### Chain offset / scrolling

- Maintain `_chain_offset: int` in the Drum Rack Mode component.
- "8 in-focus chains" = `chains[chain_offset : chain_offset + 8]`.
- Bank Select Down: `chain_offset = min(chain_offset + 8, len(chains) - 1)`
  (or page-by-1 — to be decided in plan; `+8` is full-page step).
- Bank Select Up: `chain_offset = max(chain_offset - 8, 0)`.
- When fewer than 8 chains visible at offset, the trailing fader/encoder
  positions release their parameter (LED off, fader move = no-op).
- Re-scroll when chain count changes (chain added/removed in Live).

### Encoder sub-mode (Pan / Send A / B / C)

- The four Track Control mode buttons remain the source of truth for
  which sub-mode is active — same wiring as the existing
  `EncModeSelectorComponent`.
- In Drum Rack Mode, the encoder bindings translate as:
  - Pan sub-mode → bind 8 encoders to chain[i].mixer_device.panning
  - Send A sub-mode → bind 8 encoders to chain[i].mixer_device.sends[0]
  - Send B sub-mode → bind 8 encoders to chain[i].mixer_device.sends[1]
  - Send C sub-mode → bind 8 encoders to chain[i].mixer_device.sends[2]
- If the project has fewer than 3 return tracks, sends[1] / sends[2] may
  be missing — release the corresponding encoders cleanly.

### Per-track manual-exit state

- Maintain a set of track refs (or track ids) that the user has manually
  exited. Lookup is `track in _exited_tracks`.
- On track change: re-evaluate based on (a) whether new track has a drum
  rack AND (b) whether new track is in `_exited_tracks`.
- On Shift + Stop All Clips while in the mode: add current track to
  `_exited_tracks`.
- Behavior on Shift + Stop while NOT in the mode: must NOT trigger the
  existing Stop All Clips action (but Shift + Stop should be a distinct
  combo — investigate existing assignment in `APC_64_40_9.py`).

### Integration with existing modes

- Drum Rack Mode and the existing TRACK CONTROL MODES (1=Pan/Send,
  2=AutoFilter, 3=EQ Smart Control, 4=User mode) need a clear ordering.
  Suggested: Drum Rack Mode is an OVERLAY that overrides the normal
  per-track control routing while active. Shift+Send A (AutoFilter) and
  Shift+Send B (EQ Smart Control) should still work — they target the
  selected track's AutoFilter / EQ device, NOT a chain's. (The
  AutoFilter / EQ are on the track, not on a chain.)
- The 8 faders normally drive `mixer_strip.set_volume_control(...)`.
  In Drum Rack Mode they bind to chain volume directly. Need to release
  the regular fader binding cleanly on entry, restore on exit.

### Anti-patterns (apply to all bindings)

- `parameter.is_enabled` lies — read upstream values directly.
- `connect_to(None)` / `get_parameter_by_name() == None` are silent —
  always log a `[DrumRack]` diagnostic on first activation listing the
  chains found and the params bound (mirror the
  `EncoderAutoFilterComponent._params_logged` / `_lfo_modes_logged`
  pattern).
- Plain `ButtonElement` has no `set_enabled` / `set_on_off_values`. Check
  the actual class at construction site before assuming.
- `clip_slot.canonical_parent` returns Scene on Live 12 (not Track).

</specifics>

<canonical_refs>
## Canonical References

- `EncoderAutoFilterComponent.py` — recently shipped pattern for a
  device-detection-driven mode (auto-bind on selected track having a
  specific device). Same skeleton applies: `_detect_drum_rack`, listener-
  driven re-bind on track change, fail-quiet on missing device.
- `EncoderEQComponent.py` — sister-component example of param-name
  diagnostic dumping pattern.
- `ToggleMomentaryChannelStripComponent.py` — v1.0 toggle/momentary state
  machine. Reuse its press-timing logic (fire on press-down, revert on
  release after threshold) for chain mute/solo.
- `EncModeSelectorComponent.py` — Track Control encoder mode selector
  (Pan / Send A / B / C). Drum Rack Mode hooks into this for sub-mode
  routing of encoders 1..8.
- `SpecialMixerComponent.py` / `SpecialChanStripComponent.py` — current
  fader → volume, mute/solo binding owners. Drum Rack Mode must release
  these cleanly on entry and re-bind on exit.
- `APCSessionComponent.py` — Bank Select up/down handlers. The new
  chain-scroll behavior must not break the existing track/scene bank
  navigation when Drum Rack Mode is inactive.
- `APC40_User_Manual.md` — must be updated to document the new mode
  (Phase 6 picks this up; the planner doesn't need to write the manual
  but should add a TODO marker for Phase 6 to incorporate).
- Project anti-patterns — see `.continue-here.md` (now removed) /
  `.planning/debug/resolved/lfo-rate-encoder-dead.md` for the running
  list of project-wide gotchas.

</canonical_refs>
