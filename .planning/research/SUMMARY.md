# Project Research Summary

**Project:** APC40 Toggle/Momentary Button Behavior (APC_64_40_12)
**Domain:** Ableton Live _Framework MIDI control surface scripting
**Researched:** 2026-03-31
**Confidence:** HIGH

## Executive Summary

This milestone adds dual-behavior (short press = toggle, long press = momentary) to the Solo and Mute buttons in a custom APC40 Ableton Live control surface script. The research is grounded in direct source analysis of the Live 12.1 decompiled `_Framework` and the existing project codebase — there is no guesswork about API availability or timing mechanics. The correct implementation pattern is already present in this codebase: `SpecialChanStripComponent` uses `_register_timer_callback` with a tick countdown for fold-delay detection. The new feature follows the identical pattern.

The recommended approach is to create a new `ToggleMomentaryChannelStripComponent` class that extends `SpecialChanStripComponent`, add per-button tick counters and pre-press state capture in that class, and change a single factory method in `SpecialMixerComponent` to use it. The total new code is approximately 70-90 lines in one new file plus a one-line change in one existing file. No changes are required to the composition layer, the button element layer, the shift selector, or any other component.

The primary risk is correctness in the state machine logic, not architectural uncertainty. Three patterns in particular must be implemented precisely: (1) state must be applied at press-down rather than at the threshold, (2) pre-press state must be captured at press-down not at release, and (3) the `_unregister_timer_callback` call must be paired with every registration call or the timer leaks. All three are well-documented in the research with concrete examples from the existing codebase.

---

## Key Findings

### Recommended Stack

The entire implementation lives within the existing `_Framework` timer system. No external libraries, new imports, or new architectural patterns are required. The Framework's `_register_timer_callback` / `_unregister_timer_callback` API (on `ControlSurfaceComponent`) fires a registered function at approximately 100ms intervals — this is the tick system, driven by Ableton's C++ host at a fixed rate defined in `_Framework/Defaults.py`. A 400ms long-press threshold equals exactly 4 ticks.

**Core technologies:**
- `_register_timer_callback(fn)` / `_unregister_timer_callback(fn)`: timing mechanism — already proven in this codebase, correct abstraction layer, runs on Live's main thread
- `self._track.solo` / `self._track.mute` (read/write): Live track state API — direct property access, fires `_on_solo_changed` listener automatically on write (LED updates are free)
- `SpecialChanStripComponent._on_timer`: existing hook that fires every tick — new class calls `super()._on_timer()` and adds press-duration logic
- `TRACK_FOLD_DELAY = 5` constant pattern: the naming and placement precedent for `LONG_PRESS_THRESHOLD_TICKS = 4`

The alternative `self._tasks + Task.wait(seconds)` pattern (used in `pushbase` and `ModesComponent`) is viable but inconsistent with how this specific codebase is built. Staying with `_register_timer_callback` keeps the new code idiomatic to the project.

### Expected Features

This milestone has no partial delivery — either the dual-mode works correctly or it does not. The full MVP is all that ships.

**Must have (table stakes):**
- Short press toggle (preserved, unchanged from current behavior)
- Long press activates momentary with immediate state change at press-down
- State reverts to pre-press value on release (not to a fixed "off" state)
- Long press on already-active state inverts (momentarily un-solos a soloed track)
- LED reflects real track state in real time (inherited from framework, requires no extra code)
- Zero latency on short press classification
- Shift + Solo and Shift + Mute existing behaviors preserved

**Should have (quality differentiators):**
- State captured at press-down (not release) — ensures correct revert under external state changes
- Consistent behavior between Solo and Mute buttons — same code pattern for both
- `LONG_PRESS_THRESHOLD_TICKS = 4` as a named constant — 400ms, tuned for performance use

**Defer (future milestone):**
- Configurable threshold (no settings system needed now)
- Track Activator (arm) buttons — different state semantics, out of scope
- Any other button types — clip launch, transport, etc.

### Architecture Approach

The implementation uses a single new component class (`ToggleMomentaryChannelStripComponent`) that extends `SpecialChanStripComponent`. Each of the 8 per-track instances owns its own press state independently — this is the correct granularity because two tracks can be held simultaneously. The factory method `SpecialMixerComponent._create_strip()` is the only change to existing files beyond the new file and its import. Timing logic does not belong in the button element, in the mixer, or in the composition layer.

**Major components:**
1. `ToggleMomentaryChannelStripComponent` (new, ~70-90 lines) — per-track press-duration state machine, overrides `_solo_value`, `_mute_value`, and `_on_timer`; handles short/long press classification, pre-press state capture, momentary activation, and revert-on-release
2. `SpecialMixerComponent` (modified, 2-line change) — import + factory method returns new class
3. `ChannelStripComponent` (Framework base, unchanged) — provides `self._track`, `_on_solo_changed` LED update listener, `set_solo_button` / `set_mute_button` reconnect logic

### Critical Pitfalls

1. **Activating state at the threshold instead of at press-down** — Apply state change in the `value != 0` branch of the value handler; the timer only marks the threshold as crossed, it does not trigger the action. Violating this causes 400ms latency on every press.

2. **Not pairing `_unregister_timer_callback` with every registration** — Write the `disconnect()` call immediately when adding the `__init__` registration. `StepSequencerComponent` in this codebase has this exact bug already; it must not be repeated.

3. **Placing logic in `_on_solo_changed` instead of `_solo_value`** — `_on_solo_changed` fires on any external track state change, not just button presses. Press-duration logic belongs only in `_solo_value` / `_mute_value`. The two method names sound similar; consult `ChannelStripComponent.py` source before writing the override.

4. **Capturing pre-press state at release instead of press-down** — `self._solo_state_before_press = self._track.solo` must be inside `if value != 0:`, not `else:`. Automation, scene launches, or exclusive-solo propagation can change the track state during a hold, making a release-time capture unreliable.

5. **Failing to preserve the shift guard** — The `_solo_value` override must check `_shift_pressed` (or the equivalent guard used in this component) and return early before entering the toggle/momentary logic. Shift + Solo is wired to the step sequencer's loop-length paging — silently breaking this is a regression invisible in simple testing.

---

## Implications for Roadmap

Based on research, the work is small and well-defined. A single linear sequence of steps is appropriate; there are no parallel workstreams.

### Phase 1: Component Scaffolding

**Rationale:** Creating the new class with no behavior change first gives a clean verification checkpoint. If the script loads and all existing behavior is intact, the scaffolding is correct. This separates "did I break the wiring?" from "does the new logic work?" — which makes debugging faster.

**Delivers:** `ToggleMomentaryChannelStripComponent.py` with passthrough `__init__`, import added to `SpecialMixerComponent.py`, factory method returns new class. Script loads cleanly in Live. All existing behavior identical.

**Addresses:** Architecture integration points 1 and 2 from ARCHITECTURE.md (factory method + class definition).

**Avoids:** Discovering wiring errors while simultaneously debugging state machine logic.

### Phase 2: Timer Scaffolding and State Variables

**Rationale:** Adding the timer registration and state variables before the logic confirms that the timer fires correctly and the state variables initialize cleanly. A log statement in `_on_timer` that is then removed verifies the tick rate empirically.

**Delivers:** `_solo_ticks_delay`, `_mute_ticks_delay`, `_solo_momentary_active`, `_mute_momentary_active`, `_solo_state_before_press`, `_mute_state_before_press` instance variables. `_on_timer` fires every 100ms. `_unregister_timer_callback` called in `disconnect()`. Script behavior still unchanged.

**Avoids:** Pitfall 2 (missing unregister) — the unregister is written in this phase alongside the register.

### Phase 3: Solo Toggle/Momentary Logic

**Rationale:** Implementing solo first (before mute) halves the testing surface. Mute uses identical logic; once solo is verified correct, mute is a near-copy with high confidence.

**Delivers:** `_solo_value` override implementing the full state machine. Short press toggles solo. Long press activates momentary immediately on press-down, reverts on release. Long press on already-soloed track temporarily unsolos. LED tracks state automatically. Shift guard in place.

**Addresses:** All table stakes features for solo buttons. Features from FEATURES.md: short press toggle, long press momentary, state revert, inversion on active state, LED accuracy, zero latency, shift compatibility.

**Avoids:** Pitfalls 1 (act at press-down), 3 (correct override point), 4 (pre-press state at press-down), 5 (shift guard).

### Phase 4: Mute Toggle/Momentary Logic

**Rationale:** Mirror of Phase 3 for mute buttons. Done separately to keep each phase's test scope clear.

**Delivers:** `_mute_value` override with identical logic to solo. Both solo and mute dual-mode fully operational. Both can be held simultaneously on different tracks.

**Avoids:** Same pitfalls as Phase 3 (re-verified for mute path).

### Phase 5: Edge Case Hardening and Testing

**Rationale:** The state machine has edge cases that are hard to hit accidentally but critical for live performance reliability. These require explicit testing after the happy path works.

**Delivers:** Verified behavior for: long-press on already-active track; rapid consecutive short presses (tick counter reset — Pitfall 7); shift pressed mid-hold (component disable mid-press — Pitfall 10); sequencer mode transition mid-hold; two buttons held simultaneously on different tracks. `set_solo_button(None)` and `set_mute_button(None)` reset state correctly (Pitfall 10 / integration point 4 in ARCHITECTURE.md).

**Avoids:** Pitfalls 7 (counter reset), 10 (state machine on disable), and the moderate/minor pitfalls documented in PITFALLS.md.

### Phase Ordering Rationale

- Scaffolding before logic separates infrastructure problems from logic problems — saves debugging time.
- Timer scaffolding before state machine logic ensures the tick rate is verified before it is depended upon.
- Solo before mute halves the complexity at each step; the second is a near-copy of a verified implementation.
- Edge case testing as a dedicated final phase ensures it is not skipped when the happy path works.
- There is no phase that benefits from parallel execution — each depends on the prior.

### Research Flags

Phases with standard patterns (skip research-phase during planning):

- **All phases:** The implementation pattern, API, tick rate, and integration points are fully researched against verified source. No additional research phase is needed. Every implementation decision has a verified source and a working example in the existing codebase.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All APIs verified against decompiled Live 12.1 `_Framework` source. Tick rate confirmed in `Defaults.py`. `_register_timer_callback` confirmed in `ControlSurfaceComponent.py`. Pattern confirmed working in this exact codebase. |
| Features | MEDIUM | Core behavior semantics verified against multiple sources. 400ms threshold informed by community consensus (300-500ms range), not official documentation. Inversion requirement validated against PROJECT.md. |
| Architecture | HIGH | Based entirely on direct source analysis of this codebase and Live 12.1 `_Framework`. Component boundary decisions are grounded in observed patterns across 5+ existing components. |
| Pitfalls | HIGH | Critical pitfalls are derived from Framework source analysis and existing codebase evidence (including a documented pre-existing bug in `StepSequencerComponent`). No pitfall is speculation. |

**Overall confidence:** HIGH

### Gaps to Address

- **400ms threshold feel:** Research confirms 400ms is in the correct range for performance controllers, but "correct" here is subjective. The constant is named and isolated; it can be tuned during manual testing without code structure changes. Plan one tuning pass after the feature is wired.

- **Exclusive-solo propagation under hold:** Live's exclusive-solo mode fires `_on_solo_changed` on all tracks when one changes. The pre-press state capture strategy (capture at press-down) handles this correctly in theory. Verify empirically during Phase 5 testing — hold a long-press on track 1 while manually soloing track 2 via the GUI.

- **`_shift_pressed` access in the new class:** The research identifies that shift handling is wired via `APC_64_40_9.py` using `strip.set_shift_button()`. Confirm that `self._shift_button` (or whatever attribute the parent class uses) is accessible in `ToggleMomentaryChannelStripComponent` before writing the guard in Phase 3.

---

## Sources

### Primary (HIGH confidence)

- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/Defaults.py` — `TIMER_DELAY = 0.1`, `MOMENTARY_DELAY = 0.3` (source timestamp 2025-03-17)
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ControlSurfaceComponent.py` — `_register_timer_callback`, `_unregister_timer_callback`, `_tasks` lazy attribute
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ChannelStripComponent.py` — `_solo_value`, `_mute_value`, `_on_solo_changed`, `_on_mute_changed`
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/MomentaryModeObserver.py` — tick-counting pattern (canonical Framework example)
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ModesComponent.py` — `Task.sequence(Task.wait(...))` alternative pattern
- `/Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py` — existing correct `_register_timer_callback` / `_unregister_timer_callback` pair
- `/Users/stoersignal/Dev/APC_64_40_12/EncModeSelectorComponent.py` — press-hold mode selection pattern
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` lines 134-195 — solo/mute wiring and sequencer button assignment
- `/Users/stoersignal/Dev/APC_64_40_12/StepSequencerComponent.py` line 84 — pre-existing missing-unregister bug (the negative example)

### Secondary (MEDIUM confidence)

- Ableton official: Toggle vs Momentary MIDI functions — https://help.ableton.com/hc/en-us/articles/209774945-Toggle-and-Momentary-MIDI-functions
- DJ TechTools: Momentary FX in Ableton Live — inversion pattern — https://djtechtools.com/2012/08/19/momentary-fx-in-ableton-live-advanced-midi-mappings/
- Ableton Forum: Python API timer callbacks at ~100ms resolution — https://forum.ableton.com/viewtopic.php?t=179893
- Mixxx community: Long/short/double press code snippet patterns — https://mixxx.org/forums/viewtopic.php?f=7&t=7681
- BeepStreet forums: Long press vs double-tap latency tradeoff — https://forum.beepstreet.com/discussion/1574/double-tap-and-long-press-midi-map-learn-actions

### Tertiary (LOW confidence)

- Avid VENUE Manual (momentary solo threshold = 1 second) — https://www.manualslib.com/manual/678243/Avid-Technology-Venue.html?page=130 (page partially inaccessible; used only for context on industry norms, not for implementation decisions)

---

*Research completed: 2026-03-31*
*Ready for roadmap: yes*
