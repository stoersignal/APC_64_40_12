---
quick_id: 260505-sb9
slug: status-bar-messages
status: uat-passed
final_commit: cb161ec
uat_rounds: 4
uat_passed: 2026-05-05
date: 2026-05-05
plan: 1
phase_dir: .planning/quick/260505-sb9-status-bar-messages
files_modified:
  - StatusBarMessenger.py
  - APC_64_40_9.py
  - DrumRackModeComponent.py
  - EncoderAutoFilterComponent.py
  - EncoderEQComponent.py
  - EncModeSelectorComponent.py
  - MatrixModesComponent.py
  - ShiftableTransportComponent.py
  - SpecialChanStripComponent.py
  - APC40_User_Manual.md
files_created:
  - StatusBarMessenger.py
  - .planning/quick/260505-sb9-status-bar-messages/test_messenger.py
  - .planning/quick/260505-sb9-status-bar-messages/test_task2_wiring.py
  - .planning/quick/260505-sb9-status-bar-messages/test_task3_wiring.py
  - .planning/quick/260505-sb9-status-bar-messages/test_task4_wiring.py
commits:
  - 003b96d  feat(quick-260505-sb9): add StatusBarMessenger helper (D-01..D-06)
  - 253fc01  test(quick-260505-sb9): add StatusBarMessenger unit-test harness
  - aaf032a  feat(quick-260505-sb9): wire status messenger into mode-event sources
  - c972f15  feat(quick-260505-sb9): wire param-value listeners on APC40 hardware controls
  - 0df36dc  feat(quick-260505-sb9): wire snapshot save/recall + lock-to-device messages
  - 9104dc8  docs(quick-260505-sb9): document status-bar feedback in user manual
requirements_satisfied: [D-01, D-02, D-03, D-04, D-05, D-06]
---

# Quick Task 260505-sb9: Status Bar Messages — Summary

**One-liner:** Centralized `Application.show_message`-driven feedback across the entire APC40 surface — every mode change, encoder sub-mode flip, snapshot save / recall, lock-to-device toggle, and APC40-bound parameter move now emits a transient bottom-status message via a single throttled / cold-start-silenced / dedup'd `StatusBarMessenger` helper.

**Status:** Code landed (6 commits); **awaiting hardware UAT** (Task 5 in PLAN.md). User must reload Live with the script deployed to Ableton's Remote Scripts directory and walk through the 8 D-02 event categories per the UAT checklist.

---

## What landed in each file

### Created

* **`StatusBarMessenger.py`** (new, repo root). Centralized helper. Three public methods:
  * `show_mode(mode_name, entered)` — `"<Mode>"` / `"<Mode> exited"`.
  * `show_event(text)` — arbitrary one-liner.
  * `show_param(param_name, formatted, param_id=None)` — 50ms per-`id(param)` debounce.
  * Plus `make_hardware_value_callback(param_provider, name_provider=None)` factory used by Task 3 to build hardware-control value listeners.
  * Behavioural guarantees: 2s cold-start silence (handshake quiet window), 200ms identical-text dedup, fail-quiet `_emit` chokepoint that catches `application()`-during-teardown errors.
  * Module imports nothing from Live / `_Framework`, making it unit-testable outside Ableton.

### Modified

* **`APC_64_40_9.py`** — instantiates `StatusBarMessenger(self)` once in `__init__` (pre-handshake, so cold-start gate kicks in immediately), threads it as `messenger=self._status_messenger` into every mode-emitting and hardware-listening component (`MatrixModesComponent`, `EncModeSelectorComponent`, `EncoderAutoFilterComponent`, `EncoderEQComponent`, `DrumRackModeComponent`, `ShiftableTransportComponent`), and calls `set_messenger` on each of the 8 channel strips.

* **`DrumRackModeComponent.py`** — `messenger=None` last kwarg. `_engage` emits `Drum Rack Mode`; `_disengage` captures `was_active` pre-teardown and emits `Drum Rack Mode exited` on real transitions only. Per-slot fader (chain volume) + encoder (chain pan / send-A/B/C) emit on hardware moves via `_attach_param_message_listener`. Mute/solo LED listeners (`_refresh_mute_led` / `_refresh_solo_led`) emit `<chain>: mute on/off` / `<chain>: solo on/off`. `_param_message_listeners` list torn down at the head of `_refresh_all_chain_bindings` and in `_disengage`. Messenger nulled in `disconnect`.

* **`EncoderAutoFilterComponent.py`** — `messenger=None` kwarg. Implicit-mode tracker `_last_active_device` flips `AutoFilter Mode` enter / exit on transitions in `_update_controls_and_buttons`; `on_enabled_changed` fires exit on disable. Static encoders (Drive / Env Atk / Env Rel / Env Amount / LFO Amount), dynamic LFO-rate encoder, and dynamic freq/reso encoders all carry hardware-listener callbacks. Filter-type / LFO-T-Mode rebinds use targeted `_detach_param_message_listener` so listeners don't stack mid-mode. Bank buttons `_toggle_param` / `_cycle_param` emit `<param>: on/off` and `<param>: <value_items label>` respectively.

* **`EncoderEQComponent.py`** — `messenger=None` kwarg. Implicit-mode tracker `_last_active_eq_device` keyed on `channel_eq or eq_device`; `on_enabled_changed` exits on disable. `_param_message_listeners` cleanly torn down at the head of every `_update_controls_and_buttons` (full-rebuild model). Hardware listeners on Channel EQ extras (encoders 0/4) + Eq8 extras (encoders 0..4) + Eq8 gain↔Q overrides (encoders 5/7). Highpass + FilterEQ3 Slope toggle buttons emit human-readable text (`Slope: 48 dB/oct`, `Highpass: on`).

* **`EncModeSelectorComponent.py`** — `messenger=None` kwarg + module-level `_MODE_NAMES` tuple. `_mode_value` captures `prev_mode`, fires `Encoder mode: <name>` on press-down + real transition. Send-mode auto-revert path (long-press release → snap to Pan) ALSO emits `Encoder mode: Pan` so the user sees the revert.

* **`MatrixModesComponent.py`** — `messenger=None` kwarg + module-level `MATRIX_MODE_NAMES` tuple. `set_mode` emits `Matrix: <name>` inside the `mode_index != mode` guard (skips no-op teardown re-fires). `_variations_pad_value` + `_global_var_pad_value` emit `Snapshot N recalled` (1-indexed). `_variations_on_variation_count_changed` emits `Snapshot N stored` on growth (the same text that ShiftableTransportComponent emits via Shift+Tap-Tempo — identical-text dedup in the messenger covers the duplicate). `_variations_stop_all_value` and `_global_var_stop_all_value` emit randomize-macros messages.

* **`ShiftableTransportComponent.py`** — `messenger=None` kwarg. `_nudge_down_value` (Shift+Nudge-Back) emits `Lock to device: ON/OFF` reading the post-toggle `_locked_to_device` state. `_tap_tempo_value` emits `Snapshot N stored` (after `device.store_variation()`, reading the new variation_count) and `Snapshot N recalled` (after `_recall_with_ramp()`, using `selected_variation_index + 1`).

* **`SpecialChanStripComponent.py`** — new `set_messenger` setter + override of `update()` and `disconnect()`. `_gather_owned_controls` walks `_volume_control` / `_pan_control` / `_send_controls`. Hardware listeners are torn down at the head of `update()` (so a track switch / mode change rebuilds cleanly via the framework's `connect_to`) and re-attached after `super().update()`. Param resolution at fire-time via the framework's public `parameter()` accessor (handles `None` cleanly during teardown).

* **`APC40_User_Manual.md`** — new "Status Bar Feedback (v1.2)" section near the top covering all 8 D-02 categories with example text, throttling / dedup / cold-start behavior, the explicit "what does NOT show" boundary (Live-UI / automation moves are silent), and the Pan16 follow-up TODO marker.

### Test artifacts (live in `.planning/quick/260505-sb9-status-bar-messages/`, NOT deployed)

* `test_messenger.py` — stdlib-only unit tests for the messenger (cold-start, dedup, throttle, cross-param emit, mode bypass, post-window re-emit, `make_hardware_value_callback` factory).
* `test_task2_wiring.py` — static grep + ast.parse inspector for the mode-event wiring.
* `test_task3_wiring.py` — static inspector for the hardware-listener wiring + the gotcha-#3 gate (no `param.add_value_listener` regressions in the diff).
* `test_task4_wiring.py` — static inspector for snapshot + lock-to-device wiring.

All four scripts pass:

```
$ python3 .planning/quick/260505-sb9-status-bar-messages/test_messenger.py
Task 1 OK
$ python3 .planning/quick/260505-sb9-status-bar-messages/test_task2_wiring.py
Task 2 OK
$ python3 .planning/quick/260505-sb9-status-bar-messages/test_task3_wiring.py
Task 3 OK
$ python3 .planning/quick/260505-sb9-status-bar-messages/test_task4_wiring.py
Task 4 OK
```

---

## Architecture confirmations

* **Hardware listeners, not param listeners** (resolves gotcha #3). Every new `add_value_listener` call lands on a hardware control element (slider / encoder / button), confirmed via `git diff main -- '*.py' | grep '^+.*\.add_value_listener'`. The four matches all show `control.add_value_listener` / `ctrl.add_value_listener` receivers — no `param.` / `parameter.` regressions.
* **Listener bookkeeping**: every component that adds hardware listeners in this task maintains a `_param_message_listeners` list of `(control, callback)` tuples. Each disconnect / re-bind path iterates with `try: ctrl.remove_value_listener(cb) except Exception: pass`. No orphan-listener risk on track switches, mode flips, or script reload.
* **Param resolution at fire-time** (not at registration). The factory builds a closure that calls `param_provider()` on every fire. This is correct for components where the binding can change (filter-type rebinds in AutoFilter, gain↔Q swaps in Eq8, send-slot rebinds in mode 1/2/3) without re-registering the listener.
* **No singleton**: per D-03, the messenger is dependency-injected. Every component's `messenger=None` default keeps legacy / test instantiations working. Constructor signatures only grew at the END (additive change), preserving every existing call site.
* **Atomic commits**: 6 commits total — one per landed task (1, 1b, 2, 3, 4, 6). Task 5 is human UAT, no commit.

---

## Deviations from Plan

### Auto-fixed (Rule 1/2/3)

None substantive — the plan was followed verbatim. Two micro-adjustments:

1. **`_attach_param_message_listener` helper duplicated across components.** PLAN spec'd inline `lambda` calls at each `connect_to` site. I extracted a helper into each of `DrumRackModeComponent` / `EncoderAutoFilterComponent` / `EncoderEQComponent` for consistency with existing project idiom (mirrors the `_setup_*_extras` helper pattern in EncoderEQComponent). Net effect identical; LOC slightly higher but each component reads the same way. **(Rule 2 — code quality / consistency.)**

2. **`_detach_param_message_listener` (targeted scrub) added to `EncoderAutoFilterComponent`** for the dynamic-rebind paths. PLAN said "rebuild from scratch" but that didn't account for filter-type / LFO-T-Mode listeners firing mid-mode WITHOUT a full `_teardown_bindings`. Adding the targeted scrub keeps bookkeeping accurate and prevents listener stacking when the user switches filter types or LFO modes inside Live's UI. **(Rule 1 — would have leaked listener entries.)**

### Architectural (Rule 4)

None — no architectural decisions were ambiguous or required user input.

---

## Known stubs / deferred follow-ups

1. **Pan16DeviceComponent (16-macro Pan-mode encoders)** — the 8 device-control encoders rebound by Pan16 in mode 0 do NOT emit parameter-value status messages. `Pan16DeviceComponent` is not in the touched-files list for this task; adding parallel hardware listeners there is mechanically identical to the work in `DrumRackModeComponent._refresh_all_chain_bindings` but lives outside this task's scope. Documented as `TODO (260505-sb9)` in the user manual. Future quick task should:
   * Add `messenger=None` to `Pan16DeviceComponent.__init__`.
   * Add `_param_message_listeners` bookkeeping.
   * In whichever method is the equivalent of `_refresh_all_chain_bindings` (the path that calls `connect_to(param)` for each of the 8 encoders the instance owns), attach `_attach_param_message_listener` after each `connect_to`.
   * Tear down on every refresh + in `disconnect()`.
   * Wire from `APC_64_40_9.set_pan16_components` after both `Pan16DeviceComponent` instances are constructed.

2. **Bank-button toggle messages on EQ Smart Control's Send A/B/C kill switches.** The Eq8 / FilterEQ3 cut-button toggles in `SpecialTrackEQComponent._cut_value` are NOT yet wired to emit messages. They're toggle/momentary switches and the existing v1.0 state machine drives them. Could be added by injecting the messenger into `SpecialTrackEQComponent` (not in scope for this task). Captured here for completeness; user can decide via UAT whether the rest of the EQ Smart Control surface gives sufficient coverage.

3. **Drum Rack chain mute/solo show_event pollution risk on rapid LED repaints.** On a chain whose mute state flips rapidly via Live UI (automation), the LED listener will call `show_event` once per change. The 200ms identical-text dedup handles flutter-style toggles, but a rapid alternating on/off pattern would still emit. UAT will confirm whether this is a real nuisance — if so, the fix is to compare to a per-slot last-emitted-state cache. Captured as a UAT-decided defer.

---

## Authentication gates

None — purely local code work, no external services or credentials.

---

## Self-Check

* [x] All 6 task commits exist (003b96d, 253fc01, aaf032a, c972f15, 0df36dc, 9104dc8).
* [x] All 9 modified `.py` files parse cleanly via `ast.parse`.
* [x] All 4 test scripts (`test_messenger.py`, `test_task2_wiring.py`, `test_task3_wiring.py`, `test_task4_wiring.py`) exit 0.
* [x] Diff confirms zero NEW `param.add_value_listener` calls — every new `add_value_listener` is on a hardware control element.
* [x] Every component that grew a `_param_message_listeners` list also nulls / clears it in `disconnect`.
* [x] APC40_User_Manual.md grep gate matches the required substrings (16 hits across the 7 example-text classes).
* [x] StatusBarMessenger.py imports nothing from `Live` / `_Framework`.

## Self-Check: PASSED

---

## Awaiting UAT

User must:

1. Deploy the script to Ableton's Remote Scripts directory.
2. Restart Live.
3. Walk through the **8 D-02 event categories** documented in the PLAN.md UAT checklist (Task 5):
   * (1) Drum Rack Mode enter / exit (auto-engage on track select; Shift + Detail View exit).
   * (2) AutoFilter Mode enter / exit (Shift + Send A on a track with / without an Auto Filter).
   * (3) EQ Smart Control enter / exit (Shift + Send B on a track with / without an EQ device).
   * (4) Matrix-mode swaps — all 8 modes (Clip Launch through Variations).
   * (5) Snapshot save (Shift + Tap Tempo release without encoder touch) + recall (Tap Tempo, plus Variations Mode pad press).
   * (6) Encoder sub-mode flips — Pan / Send A / Send B / Send C.
   * (7) Lock to device toggle (Shift + Nudge Back).
   * (8) Parameter-value display on every fader / encoder turn — verify smooth ~20 Hz update under rapid encoder twirl, identical-text dedup on repeated mode-button press, and cold-start silence in the first ~2 seconds after script load.

Resume signal: "approved" or per-category issue list (e.g. "category 4 ok; category 8 missing on send encoders").

## Post-UAT iterations (4 rounds, final commit cb161ec)

UAT round 0 (`9104dc8`): user reported "no messages at all" — every
silent except in `_emit` was swallowing the actual cause.

| Round | Commit | Hypothesis | Result |
|-------|--------|------------|--------|
| 1 | `dcef1a9` | Add log_message diagnostics to surface the silent failure | Diagnostic confirmed: `Application.show_message(text)` raised `ArgumentError` — C++ signature mismatch |
| 2 | `48963d0` | C++ signature suggested it's a modal dialog; switch to `Song.show_message` | Still no messages — `Song` doesn't have `show_message` (`AttributeError`) |
| 3 | `29aec07` + `3dcf454` | Multi-strategy probe: `app.view.show_message`, `app.view.set_status_text`, `app.get_document().show_message`, `parent._c_instance.show_message` | All four FAIL'd with the same C++ self-type mismatch |
| 4 | `cb161ec` | User pointed at the existing `_show_msg_callback` pattern in `ShiftableTransportComponent` ("look at how it's done for the variations ramp time"). Switch `_emit` to `self._parent.show_message(text)` — the canonical `_Framework.ControlSurface.show_message` callback that wraps Live's correct internal status-bar API | **APPROVED** |

### The actual answer

`ControlSurface.show_message(text)` is the `_Framework` method that
ALL existing components use via the inherited `_show_msg_callback`:

```python
# ShiftableTransportComponent.py line 384, 386, 455 — Variations Ramp Time
self._show_msg_callback('Ramp: ' + label)
self._show_msg_callback('Ramp: ' + str(self._ramp_ms) + 'ms')
self._show_msg_callback('Ramping ' + str(int(ramp_ms)) + 'ms')
```

`_show_msg_callback` is bound by `_Framework.ControlSurface` to
`self.show_message` when each component registers. Our messenger holds
the surface as `self._parent` (constructed in APC_64_40_9 via
`StatusBarMessenger(self)`), so the direct call is:

```python
self._parent.show_message(text)
```

The `Application.show_message` C++ binding mismatch (rounds 1-3) was a
red herring — that's an internal modal-dialog stub not meant for remote
scripts. `ControlSurface.show_message` routes through Live's correct
internal path.

### Lessons reinforced

- **Look in-project FIRST.** Three working call sites
  (`ShiftableTransportComponent`, `EncModeSelectorComponent`,
  `ShiftableDeviceComponent`) used the canonical
  `_show_msg_callback` pattern. A `grep show_msg *.py` before writing
  the helper would have made this a one-round task.
- **Silent except is the root of all wasted UAT cycles.** Round 0's
  six commits + Round 1's diagnostic re-instrumentation could have
  been avoided if `_emit` had logged the exception from the first
  attempt. Pattern: ALWAYS log the actual exception in fail-quiet
  wrappers, even temporarily, when the symptom is "nothing happens".
- **C++ signature errors are not always actionable from Python.**
  The `ArgumentError ... did not match C++ signature` message looked
  like it was telling us "pass these args"; in fact it was telling us
  "this method is bound to a different self-type and is unreachable
  from the Application instance you have". Could have caught this at
  Round 1 by reading the FULL signature including the `TPyHandle<...>`
  self-type, not just the `text/buttons/...` user-facing args.

### Final UAT (passed 2026-05-05)

All 8 D-02 categories tested in Live, status bar text appears at the
bottom-left for ~3 seconds:

1. ✅ Drum Rack Mode enter/exit
2. ✅ AutoFilter Mode (Shift+Send A) enter/exit
3. ✅ EQ Smart Control (Shift+Send B) enter/exit
4. ✅ Matrix-mode swaps (Variations / Sequencer / Note / etc.)
5. ✅ Snapshot save/recall
6. ✅ Encoder sub-mode flips (Pan / Send A/B/C)
7. ✅ Lock to device toggle
8. ✅ Parameter values (Live-formatted via `str_for_value`)

Throttling, dedup, and cold-start silence verified working.

### Files changed across all rounds

| File | Net change |
|------|------------|
| `StatusBarMessenger.py` | new, 100 lines after R4 (was 215 at peak with multi-strategy scaffolding; collapsed to single canonical path) |
| `APC_64_40_9.py` | wired StatusBarMessenger; passed to 6 components |
| `DrumRackModeComponent.py` | mode message + chain mute/solo/param listeners |
| `EncoderAutoFilterComponent.py` | mode message + 8-encoder param listeners |
| `EncoderEQComponent.py` | mode message + EQ-encoder param listeners |
| `EncModeSelectorComponent.py` | encoder sub-mode flip messages |
| `MatrixModesComponent.py` | matrix-mode swap messages + snapshot save/recall |
| `ShiftableTransportComponent.py` | lock-to-device toggle messages |
| `SpecialChanStripComponent.py` | track-mixer mode hardware-side param listeners |
| `APC40_User_Manual.md` | "Status Bar Feedback (v1.2)" section + Pan16 follow-up TODO |
