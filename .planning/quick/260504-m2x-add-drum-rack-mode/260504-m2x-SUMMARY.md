---
quick_id: 260504-m2x
slug: add-drum-rack-mode
status: uat-passed
final_commit: fad89f9
uat_rounds: 4
created: 2026-05-04
uat_passed: 2026-05-05
date: 2026-05-04
phase: quick-260504-m2x
plan: 01
requirements: [DRUMRACK-01, DRUMRACK-02, DRUMRACK-03, DRUMRACK-04, DRUMRACK-05, DRUMRACK-06]
files_modified:
  - DrumRackModeComponent.py            # new (860 lines)
  - ToggleMomentaryChannelStripComponent.py  # press-timing helpers extracted; v1.0 unchanged
  - APC_64_40_9.py                       # wires DrumRackModeComponent into _setup_global_control
  - APC40_User_Manual.md                 # Phase 6 TODO marker
commits:
  - 9712d35 refactor(quick-260504-m2x): extract reusable press-timing helpers
  - e21de82 feat(quick-260504-m2x): add DrumRackModeComponent (auto-engaging drum-chain overlay)
  - 4cd4dde feat(quick-260504-m2x): wire DrumRackModeComponent into APC_64_40_9
  - 821b952 docs(quick-260504-m2x): add Phase 6 TODO marker for Drum Rack Mode
  - 60391fc fix(quick-260504-m2x): post-UAT — LED feedback + bank-scroll ownership
  - 7235fbd fix(quick-260504-m2x): force=True on Stop All Clips LED + bank-scroll diagnostics
  - 0bd8a02 fix(quick-260504-m2x): try velocity=1 + tick re-assertion + diagnostic log for Stop All Clips LED
  - fad89f9 fix(quick-260504-m2x): migrate indicator + manual exit to Shift+DetailView
---

# Quick Task 260504-m2x — Drum Rack Mode Summary

## What changed

A new **Drum Rack Mode** auto-engages on the APC40 whenever the selected
track's first top-level device is a Live Drum Rack
(`class_name == 'DrumGroupDevice'`). While the mode is active, the listed
controls retarget from track-mixing to drum-chain semantics; all other
APC40 controls (clip matrix, scenes, transport, crossfader, master,
prehear, Shift+Send-A AutoFilter, Shift+Send-B EQ Smart Control,
Variations modes) preserve their default behaviour.

## Encoder / button layout while in Drum Rack Mode

| Surface section | Drum Rack Mode binding |
|---|---|
| 8 Track faders | `chain[i].mixer_device.volume` |
| 8 Track Mute buttons | `chain[i].mute` (v1.0 toggle/momentary, LONG_PRESS_DELAY=4) |
| 8 Track Solo buttons | `chain[i].solo` (v1.0 toggle/momentary, LONG_PRESS_DELAY=4) |
| 8 Track Control encoders, Pan sub-mode | `chain[i].mixer_device.panning` |
| 8 Track Control encoders, Send A | `chain[i].mixer_device.sends[0]` |
| 8 Track Control encoders, Send B | `chain[i].mixer_device.sends[1]` (release if missing) |
| 8 Track Control encoders, Send C | `chain[i].mixer_device.sends[2]` (release if missing) |
| Pan / Send-A / Send-B / Send-C mode buttons | OBSERVED — selects encoder sub-mode |
| Bank Select up/down | Scroll `_chain_offset` by ±8 (when chain count > 8) |
| Detail View button (note 62) | LED = mode-active indicator (migrated from Stop All Clips after UAT R4 — see Post-UAT iterations below) |
| Shift + Detail View | Exit mode for current track only (per-track scope) |

## Files touched

| File | Status | Notes |
|---|---|---|
| `DrumRackModeComponent.py` | **new** | Auto-engaging overlay; 132 try/except blocks; 8 `[DrumRack]` log markers; one-shot diagnostic dump on first activation |
| `ToggleMomentaryChannelStripComponent.py` | refactored | Module-level `handle_toggle_momentary_event(value, target_obj, target_attr, state, long_press_delay, shift_pressed)` and `tick_state(state)` extracted; v1.0 wrapper rewritten as a state-dict view delegator. **61 existing v1.0 tests still green.** |
| `APC_64_40_9.py` | wired | Import; `_drum_rack_mode = None` in `__init__` and `disconnect`; `_sliders` / `_mute_buttons` / `_solo_buttons` promoted to instance attrs; instantiation + `trigger_initial_evaluation()` at end of `_setup_global_control` |
| `APC40_User_Manual.md` | append | Phase 6 TODO marker so doc integration is not dropped |

## Architectural shape

Modeled on `EncoderAutoFilterComponent` (the recently-shipped quick-260504-k6p):

* `__init__` stores refs, builds 8 `_ChainSlotHandler` instances (one per
  APC40 strip slot), registers a timer callback (drives mute/solo press-state
  ticks at v1.0 cadence), and attaches the always-alive observer listeners
  (Stop All Clips, Bank Up/Down, Shift, the four encoder mode buttons,
  selected-track listener, track-list listener).
* `on_selected_track_changed` → `_evaluate_selection` decides engage /
  disengage based on (a) is the new track's first top-level device a
  `DrumGroupDevice` AND (b) is `id(track) not in _exited_tracks`.
* `_engage(rack)` releases each mixer-strip's volume/mute/solo binding
  (`set_volume_control(None)` / `set_mute_button(None)` /
  `set_solo_button(None)`), then adds value listeners on the captured
  faders + mute/solo buttons routed through `_ChainSlotHandler`. Encoders
  bind via `_bind_chain_encoder` per current `EncModeSelectorComponent._mode_index`.
* `_disengage()` removes every listener we added, releases the encoders,
  detaches the chain-count listener, then calls `mixer.update()` AND
  `encoder_modes.update()` so `SpecialMixerComponent`/`EncModeSelectorComponent`
  re-assert their normal wiring.
* Per-chain mute/solo timing is byte-identical to v1.0 — the
  `_ChainSlotHandler` forwards each press/release/tick to the same
  module-level helpers used by `ToggleMomentaryChannelStripComponent`.
* Stop All Clips is shared by **add_value_listener** (never
  `set_stop_all_clips_button(None)`), matching how `MatrixModesComponent`
  Variations modes coexist with `PedaledSessionComponent`'s ownership.
* Bank Select up/down is also additive — the listener is a passthrough
  unless `_active AND chains > 8`, so scene-bank navigation is preserved
  on small drum racks (≤ 8 chains) and on non-drum-rack tracks.

## Anti-pattern guards applied

| Pattern | Status |
|---|---|
| `parameter.is_enabled` gating | Not used — read upstream values only |
| `connect_to(param)` always wrapped in try/except + None guard | ✅ |
| Plain `ButtonElement` LED ops (no `set_on_off_values`) | ✅ — `turn_on()`/`turn_off()` only, in try/except |
| `clip_slot.canonical_parent` | Not used — Drum Rack Mode never resolves track-from-slot |
| First-activation Log.txt dump | ✅ Mandatory — class_name + chain count + chain names + chain[0] mixer attrs |
| Listener-add wrapped in try/except | ✅ — every framework call is wrapped (132 try/except blocks) |
| In-flight momentary holds reverted on disengage | ✅ — `revert_holds()` per slot in `disconnect` |

## Verification

* `python3 -c "import ast; ast.parse(...)"` — clean across all 3 modified .py files.
* `python3 -m unittest tests.test_task1_toggle_momentary_values tests.test_task2_timer_and_shift_guards tests.test_task3_multi_track` — **61 tests passing**, byte-identical v1.0 behaviour preserved by the helper extraction.
* `grep -nc "DrumRackModeComponent" APC_64_40_9.py` — 3 (1 import + 1 instantiation + 1 doc-comment reference).
* `grep -c "self\._drum_rack_mode" APC_64_40_9.py` — 5 (init + disconnect + instantiation + name set + trigger_initial_evaluation).
* `grep -nc "_dump_diagnostics_once|\[DrumRack\]" DrumRackModeComponent.py` — 10 hits.
* `grep -c "try:\|except" DrumRackModeComponent.py` — 132 (extensive fail-quiet coverage).

## Out of scope (per PLAN.md)

* Return chains (`drum_rack.return_chains`) — only main `chains` are addressed in v1.
* Recursion into nested instrument/effect racks (per D-04 — top-level only).
* Page-by-1 scroll on Bank Select — `±8` full-page step is the chosen behaviour.
* Persistence of `_exited_tracks` across project reloads — set is in-memory only.
* Removal/simplification of `EncModeSelectorComponent`'s pan/send wiring while Drum Rack Mode is active — the strips' writes target released (no-op) channel slots; if empirical UAT shows audible side-effects, add a guarded passthrough in `EncModeSelectorComponent.update()`.

## Deviations from plan

**None.** Plan executed exactly as written. The four landed commits map
1:1 to Tasks 1, 2, 3, 5; Task 4 (hardware UAT) is the human-verify
checkpoint and remains pending.

## Pending: Task 4 — Hardware UAT in Ableton Live

The user must reload Ableton Live with the updated script and walk the
10-step UAT checklist in `260504-m2x-PLAN.md` (Task 4):

1. **Cold-start dump** — open a project with a drum-rack track, confirm
   `[DrumRack] detected device class: 'DrumGroupDevice'` + chain count +
   chain[0] mixer attrs in `Log.txt`. **If `class_name` differs** (e.g.
   `'DrumRack'` or `'DrumGroupDevice2'` on a future Live build) note the
   exact string — patch `DRUM_RACK_CLASS_NAMES`.
2. **Stop All Clips LED** — lit on drum-rack track, off on non-drum-rack track.
3. **Faders** — fader 1..8 drives chain 1..8 volume (not project track volume).
4. **Mute/Solo timing (D-03)** — short-tap toggles, long-press momentary; two simultaneous holds independent.
5. **Encoder sub-modes** — Pan / Send A / B / C bind correctly; missing sends fail-quiet.
6. **Bank Select scroll** — `±8` page step on rack with > 8 chains; preserves scene navigation on rack with ≤ 8 chains.
7. **Manual exit (D-02)** — Shift + Stop All Clips exits this track only; per-track scope verified by switching tracks.
8. **Non-drum-rack tracks (D-05)** — script stays in normal track-mixer / EQ / AutoFilter / Variations behaviour; Stop All Clips LED off.
9. **Chain count change** — drag a new sample onto rack mid-mode; new chain becomes live without re-selecting track.
10. **Variations modes coexistence** — switch matrix to Variations mode 7, Stop All Clips becomes randomize-macros; switch back, Drum Rack Mode resumes.

After UAT passes, this SUMMARY should be updated with `status=uat-passed`
and `final_commit: <sha>`. Failure → return planning context with
Log.txt lines + reproduction steps; same 4-round debug pattern as
quick-260504-k6p applies.

## Self-Check: PASSED

* `DrumRackModeComponent.py` — FOUND.
* `APC40_User_Manual.md` Phase 6 TODO marker — FOUND.
* Commit `9712d35` (Task 1 refactor) — FOUND.
* Commit `e21de82` (Task 2 new component) — FOUND.
* Commit `4cd4dde` (Task 3 wiring) — FOUND.
* Commit `821b952` (Task 5 manual TODO) — FOUND.

## Post-UAT iterations (4 rounds, final commit fad89f9)

UAT round 0 (`821b952` final commit) shipped 4 of 10 steps green; the
remaining 6 needed 4 fix rounds. All bugs were in the LED/button-feedback
ownership wiring — the toggle/momentary timing extracted in Task 1 was
byte-identical to v1.0 and never wavered.

| UAT step | Round 0 | R1 | R2 | R3 | R4 |
|----------|---------|----|----|----|----|
| 1 cold-start dump | ✓ | | | | |
| 2 Stop All Clips LED | ✗ | ✗ | ✗ | ✗ | ✓ (migrated to Detail View) |
| 3 faders | ✓ | | | | |
| 4 Mute/Solo timing | partial (no LEDs) | ✓ (chain.add_*_listener) | | | |
| 5 encoder sub-modes | ✓ | | | | |
| 6 Bank scroll | ✗ | ✗ (race) | ✓ (set_scene_bank_buttons(None,None)) | | |
| 7 manual exit | ✓ → moved | ✓ | ✓ | ✓ | ✓ (now Shift+Detail View) |
| 8 non-drum-rack tracks | ✓ | | | | |
| 9 chain count change | ✓ | | | | |
| 10 Variations coexistence | ✓ | | | | |

### Round 1 — `60391fc` LED feedback + bank-scroll ownership

Three bugs, one commit. All in the same family: ownership transfer of
shared resources between SpecialChanStripComponent / SessionComponent and
us.

* Stop All Clips LED stayed dark — session retains LED ownership via
  `_update_stop_all_clips_button` on every clip-state change. Detached
  via `session.set_stop_all_clips_button(None)` (mirrors
  MatrixModesComponent variations-mode pattern).
* Mute/Solo LEDs stayed dark — we wired input listeners on the buttons
  but never the OUTPUT direction (chain.mute / chain.solo →
  button.send_value). After `strip.set_mute_button(None)` the strip's
  LED feeding stops. Added `chain.add_mute_listener` /
  `chain.add_solo_listener` per slot, repaint via `send_value(127|0)`.
  Inverted convention on Mute (lit = alive) matches v1.0
  set_invert_mute_feedback. Direct on Solo. **WORKED first try.**
* Bank Select scroll didn't engage — session's scene-nav listener races
  ours. With chains > 8 we need to suppress session's listener; with ≤ 8
  we passthrough. `session.set_scene_bank_buttons(None, None)` while
  active AND chains > NUM_STRIPS, restore otherwise.

### Round 2 — `7235fbd` force=True on Stop All Clips LED + bank diagnostics

* Stop All Clips LED still dark. Hypothesis: `turn_on()`/`turn_off()`
  hits the `_last_sent_value` short-circuit inside ButtonElement;
  `_refresh_variations_leds` line 440 uses `send_value(value, True)`
  with force=True for this exact reason. Switched to that.
* Bank Select still "not working" — added log_message diagnostics on
  every press: active, chain count, current offset, scene_nav_taken.

### Round 3 — `0bd8a02` velocity=1 + tick re-assertion

Bank scroll **WORKED** (R2 fix landed correctly; user just hadn't tested
on a >8-chain rack initially).

Stop All Clips LED still dark. Two more theories:
* (T1) APC40 single-color LEDs may use velocity=1, not 127. Tried 1.
* (T2) Periodic repaint races us. Added `_on_timer`-driven re-assertion
  every Live MIDI loop iteration so we can't be silenced by a one-shot
  overwrite.

### Round 4 — `fad89f9` migrate to Shift+Detail View

Diagnostic Log.txt confirmed `[DrumRack] _refresh_stop_all_led
active=True sending velocity=1` was firing correctly — code path is
sound. User confirmed the Stop All Clips LED on their APC40 firmware
**never lights even from Live's own session writes when clips are
playing** — it's hardware-only.

Per user direction: **D-02 + D-06 migrated to Detail View** (note 62,
channel 0 — `self._device_bank_buttons[4]`). Detail View has a
MIDI-addressable LED. DetailViewCntrlComponent already gates its
handler on `not self._shift_pressed` (line 131), so Shift+Detail View
was already free for our exit combo and unshifted Detail View still
toggles Live's Detail panel. Stop All Clips listener removed entirely;
session.set_stop_all_clips_button(None)/restore removed; replaced with
single periodic `send_value(127, True)` to the Detail View button on
every tick. **Approved on first reload.**

### Lessons reinforced

* `connect_to(None)` and `get_parameter_by_name() == None` are silent;
  `turn_on()` is silent when `_last_sent_value` cache matches; **assume
  every button-feedback path is silent unless your diagnostic
  log_message proves otherwise**.
* Adding `log_message` instrumentation to every state-changing branch is
  cheap (one MIDI byte per call) and **resolves "still not working"
  reports in one round** when the symptom is ambiguous.
* Hardware addressability is firmware-version-dependent; some APC40
  buttons accept MIDI feedback, others (transport-style: Stop All
  Clips, Play, etc.) are firmware-managed and ignore feedback. **The
  test is whether the LED responds to Live's own writes during normal
  use** — if not, no script-side change can fix it.
* DetailViewCntrlComponent's existing `not self._shift_pressed` gate
  made Shift+Detail View "free" for our exit combo without needing to
  steal ownership. **Composable shift-gated listeners are the cleanest
  multiplexing pattern** (also used by MatrixModesComponent for
  Stop All Clips during Variations mode).

### Final UAT (passed 2026-05-05)

All 10 UAT steps from the original plan passed. Encoder/button layout,
toggle/momentary timing, encoder sub-mode swap, chain count changes
during the mode, fail-quiet on non-drum-rack tracks, and Variations-
mode coexistence — all green. Working tree clean at `fad89f9`.

### Files added / modified across all rounds

| File | Net change |
|------|------------|
| `DrumRackModeComponent.py` | new, ~990 lines after R4 (was 860 at R0) |
| `ToggleMomentaryChannelStripComponent.py` | refactor (helpers extracted; 61 v1.0 tests still green) |
| `APC_64_40_9.py` | wired DrumRackModeComponent; `detail_view_button=self._device_bank_buttons[4]` |
| `APC40_User_Manual.md` | Phase 6 TODO marker (updated with Shift+Detail View) |
| `.planning/quick/260504-m2x-add-drum-rack-mode/` | CONTEXT, PLAN, SUMMARY (this file) |
