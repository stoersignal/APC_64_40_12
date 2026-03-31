# Project Research Summary

**Project:** APC40 Toggle/Momentary Button Behavior — v1.1 16Macros Milestone
**Domain:** Ableton Live _Framework MIDI control surface scripting — encoder expansion + mode button behavior
**Researched:** 2026-03-31
**Confidence:** HIGH

## Executive Summary

This is a subsequent milestone on a proven codebase. The v1.0 toggle/momentary pattern for Solo and Mute buttons is fully implemented, tested, and hardened — including shift guards and `disconnect()` revert. The v1.1 16Macros milestone adds two independent feature clusters: (1) repurposing Pan mode to simultaneously map both encoder rows (16 controls total) to device parameters 1-16, and (2) extending the existing `EncModeSelectorComponent` mode buttons to behave as toggle/momentary selectors using the same ~400ms threshold from v1.0. Both features are well-scoped with clear anchor points in the existing code.

The recommended approach is to implement these as two sequential phases with a strict build order. The 16-parameter encoder mapping requires a new `Pan16DeviceComponent` and careful component ownership management — one DeviceComponent instance per 8-encoder row, each locked to a specific bank. The toggle/momentary mode buttons are a direct modification to `EncModeSelectorComponent`'s existing timer infrastructure, transposing the proven pattern from boolean track attributes to encoder mode indices. No existing components need fundamental restructuring; the changes are additive and localized to three files.

The highest risks are in the encoder feature: dual assignment of controls without proper release will silently corrupt state, and the interaction between two DeviceComponent instances targeting the same device is not officially documented (though the `_alt_device` pattern in `EncoderDeviceComponent` demonstrates it is possible). The send button feature carries one critical design ambiguity — the physical Send A/B/C buttons serve as both global encoder mode selectors and (in the new design) mode toggle/momentary triggers. The ARCHITECTURE.md research confirmed the toggle/momentary applies to the mode selection itself (not per-track send enable), but this must be stated explicitly in any plan before coding begins to prevent the mode-latch vs. momentary-revert conflict.

---

## Key Findings

### Recommended Stack

No new technologies are required for this milestone. The entire implementation uses the existing Python-in-Ableton-Live environment with `_Framework` APIs. The v1.0 timer infrastructure (`_register_timer_callback`, `LONG_PRESS_DELAY = 4`) is reused verbatim for the encoder mode toggle/momentary feature. New code is confined to three files: one new file (`Pan16DeviceComponent.py`, ~50 lines) and targeted modifications to `EncModeSelectorComponent.py` and `APC_64_40_9.py`.

One critical stack constraint: the `_Generic.Devices.parameter_banks()` function uses column-major interleaving, not sequential row ordering. Any attempt to use it for 16-param mapping produces wrong parameter ordering on devices with more than 8 parameters. Access `device.parameters[1:17]` directly to get sequential parameter access — this bypasses the bank system entirely and is verified against the decompiled `_Generic/Devices.py` source.

**Core technologies:**
- `_Framework.DeviceComponent` — base class for `Pan16DeviceComponent`; `_assign_parameters` connects controls to Live device parameters via standard `connect_to()` calls
- `device.parameters[1:17]` (Live API) — direct sequential access to first 16 device parameters; `parameters[0]` is always "Device On/Off" and is skipped
- `_register_timer_callback` / `EncModeSelectorComponent._on_timer` — existing timer hook; extended for send button toggle/momentary; no new timer registration needed
- `RingedEncoderElement.connect_to(parameter)` / `release_parameter()` — standard encoder-to-parameter wiring; ring LEDs update automatically from parameter type

### Expected Features

**Must have (table stakes — encoder cluster):**
- Pan mode: top 8 encoders (CC 48-55) connected to device params 1-8
- Pan mode: device encoders (CC 16-23) connected to device params 9-16
- Switching out of Pan mode cleanly releases all 16 parameter connections
- Ring LEDs function correctly on both encoder rows in Pan mode
- Device lock state respected (locked device followed when lock is active)
- Appointed device changes during Pan mode update both encoder rows immediately

**Must have (table stakes — send button cluster):**
- Short press on any mode button (Pan/Send A/B/C) permanently selects that mode (existing behavior, preserved)
- Long press on Send A/B/C mode button activates that mode while held, reverts to prior mode on release
- Same 400ms threshold (LONG_PRESS_DELAY = 4 ticks) as Solo/Mute
- Shift guard: shift + Send A/B/C does not trigger momentary behavior
- `disconnect()` reverts any active momentary mode hold on teardown

**Defer to v2+:**
- Configurable press threshold
- Bank navigation behavior in 16-param mode (leave existing bank nav as-is and document the limitation)
- Any new button types beyond the four mode buttons

### Architecture Approach

The 16-param feature uses two new `Pan16DeviceComponent` instances — one locked to bank 0 (params 1-8) for the top encoders, one locked to bank 1 (params 9-16) for the device encoders. `EncModeSelectorComponent` activates both in its mode 0 (Pan) branch and deactivates them in all other branches. The existing `ShiftableDeviceComponent` is disconnected from the device encoder row during Pan mode by passing `None` to `set_parameter_controls()` from the composition layer — no changes to `ShiftableDeviceComponent` itself. The toggle/momentary mode buttons are implemented entirely within `EncModeSelectorComponent` by extending its existing `_on_timer` and `_mode_value` methods with per-button tick countdown state.

**Major components:**
1. `Pan16DeviceComponent` (new, ~50 lines) — extends `DeviceComponent`; fixed bank index (0 or 1); tracks appointed device via `song().add_appointed_device_listener`; exposes `set_parameter_controls()`
2. `EncModeSelectorComponent` (modified) — Pan mode routing to two `Pan16DeviceComponent` instances; toggle/momentary timer state for all four mode buttons using existing `_on_timer`
3. `APC_64_40_9._setup_global_control()` (modified) — promotes `device_param_controls` to instance variable; instantiates and wires two `Pan16DeviceComponent` instances; passes references to `EncModeSelectorComponent` via setters or constructor
4. `ToggleMomentaryChannelStripComponent` (no change) — v1.0 component unaffected by both features
5. `ShiftableDeviceComponent` (no change) — disconnected from encoders during Pan mode by composition layer, not by internal modification

### Critical Pitfalls

1. **Dual-assignment of encoders without release (Pitfall E1)** — call `release_parameter()` on every control before `connect_to()` in a new mode; follow the `EncoderUserModesComponent._set_modes()` canonical teardown pattern which explicitly iterates and releases before reassigning.

2. **16-element tuple passed to `EncModeSelectorComponent.set_controls()` (Pitfall E2)** — the component asserts `len(controls) == 8` and maps controls 1:1 to mixer channel strips; passing 16 controls crashes on load or silently only assigns the first 8. Use two separate `Pan16DeviceComponent` instances, each receiving 8 controls.

3. **Device encoder parameters not released on mode exit (Pitfall E3)** — every `connect_to()` call in the Pan mode activation path must have a matching `release_parameter()` call in every non-Pan mode branch of `EncModeSelectorComponent.update()`; orphaned connections cause stuck encoders and stale ring LEDs.

4. **Mode-latch vs. momentary-revert semantic conflict (Pitfall S6/S1)** — encoder mode selection is a persistent latch; momentary behavior is transient. These are two asymmetric release semantics on the same physical button. The v1.1 design resolves this by applying momentary behavior to the mode selection itself (the mode reverts on release), not to any per-track send enable. This must be explicit in the plan before code is written.

5. **Bank state not preserved on mode re-entry (Pitfall E5)** — `ShiftableDeviceComponent` freely changes `_bank_index` via shift+bank buttons; when returning to Pan mode after bank navigation, the device encoder row must explicitly re-lock to bank 1, not rely on the last bank index. `Pan16DeviceComponent` with a fixed `bank_index` constructor argument solves this by design.

---

## Implications for Roadmap

Two phases are recommended. The build order is driven by the dependency that Phase 2's timer changes interact with `EncModeSelectorComponent.update()`, which is also Phase 1's integration point — doing Phase 1 first means Phase 2 tests verify against a fully wired update method.

### Phase 1: 16-Parameter Encoder Mapping (Pan Mode)

**Rationale:** Encoder ownership and component wiring must be established before the toggle/momentary mode button behavior is layered on top. A clean, loadable script at the end of Phase 1 provides a verified baseline for Phase 2's changes.

**Delivers:** Pan mode simultaneously maps device params 1-8 via top encoders and params 9-16 via device encoders. Clean teardown on mode exit to Send A/B/C. Ring LEDs functional on both rows. Appointed device changes update both rows.

**Build order within phase:**
1. Promote `device_param_controls` to `self._device_param_controls` in `_setup_device_and_transport_control()` — no behavior change; verify script loads
2. Create `Pan16DeviceComponent.py` with two instances (bank 0, bank 1) wired but not yet active — verify script loads without error
3. Modify `EncModeSelectorComponent.update()` mode 0 branch to release mixer pan, activate both `Pan16DeviceComponent` instances, disconnect `ShiftableDeviceComponent`; all other modes do the reverse
4. Edge cases: rapid mode switching leaves no stuck assignments; appointed device change during Pan mode; devices with fewer than 16 parameters

**Addresses:** Encoder cluster table-stakes features (FEATURES.md)
**Avoids:** Pitfalls E1, E2, E3, E5

### Phase 2: Toggle/Momentary Send A/B/C Mode Buttons

**Rationale:** Depends on Phase 1 because the timer state additions in `EncModeSelectorComponent` interact with the same `_on_timer` and `_mode_value` methods modified in Phase 1. Isolating this to Phase 2 keeps each diff readable and allows independent verification in Live.

**Delivers:** Short press on Send A/B/C mode buttons permanently selects that mode (preserved). Long press activates the mode while held and reverts to the previous mode on release (~400ms threshold). Shift guard prevents momentary activation when shift is held. `disconnect()` reverts active momentary mode hold.

**Build order within phase:**
1. Add `_send_ticks_delay` (array of 4), `_send_mode_before_press`, `_send_momentary_active`, `_send_pressed_mode` state variables to `EncModeSelectorComponent.__init__()`
2. Extend `_mode_value()` to record prior mode and arm timer countdown on press-down (immediate mode activation at press-down, zero latency)
3. Extend `_on_timer()` to decrement counters, mark threshold crossing, handle revert on release
4. Add shift guard via `set_shift_button()` setter on `EncModeSelectorComponent` — same pattern as `ShiftableDeviceComponent`
5. Harden `disconnect()` to revert any active momentary mode before teardown
6. Decision point: unify existing `_pan_to_vol_ticks_delay` into the new per-button tick array or leave alongside — unified approach preferred (cleaner `_on_timer`), document the decision

**Addresses:** Send button cluster table-stakes features (FEATURES.md)
**Avoids:** Pitfalls S1, S5, S6, E4

### Phase Ordering Rationale

- Phase 1 before Phase 2 because both phases touch `EncModeSelectorComponent.update()` and `_on_timer`; sequential changes prevent interaction bugs and make code review tractable
- Both phases are additive — no existing tested components are modified internally, only composition wiring and `EncModeSelectorComponent` (which is explicitly in scope)
- The "promote instance variable" micro-step in Phase 1 is the only change that touches `APC_64_40_9.py` in a way that could break existing features; doing it first and verifying script load provides an early regression signal
- There are no workstreams that benefit from parallel execution; each step within each phase depends on the prior

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1, Step 2:** Verify that two `DeviceComponent` instances targeting the same appointed device simultaneously do not conflict via `_device_bank_registry`. The `EncoderDeviceComponent._alt_device` pattern suggests it works, but confidence is MEDIUM. The verification is empirical — create the instances in Step 2, load the script, change the selected device, confirm both instances receive the update without errors before wiring controls in Step 3.

Phases with standard patterns (skip research-phase):
- **Phase 2:** The toggle/momentary timer pattern is fully proven in v1.0 (`ToggleMomentaryChannelStripComponent`). The transposition to mode indices in `EncModeSelectorComponent` is mechanical — STACK.md and ARCHITECTURE.md both provide concrete code sketches. No additional research phase needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All APIs verified against decompiled `_Framework` source at `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/` (source timestamp 2025-03-17). Direct sequential parameter access via `device.parameters[1:17]` verified against `_Generic/Devices.py`. |
| Features | HIGH | Grounded entirely in existing codebase analysis. No external domain inference required. v1.0 implementation provides verified behavioral template. |
| Architecture | HIGH | Component boundaries and data flow verified by reading every file in the change path. One MEDIUM item: dual DeviceComponent on same device needs empirical verification in Step 2 of Phase 1. |
| Pitfalls | HIGH | Derived from direct reading of the exact code paths that will be modified. v1.0 pitfalls confirmed by the shipped implementation. No pitfall is speculation. |

**Overall confidence:** HIGH

### Gaps to Address

- **Dual DeviceComponent on same device (architecture risk):** Two `Pan16DeviceComponent` instances both subscribing to the appointed device listener is the core assumption of the 16-param design. The `_device_bank_registry.set_device_bank` interaction is not fully characterized. Mitigation: verify empirically in Phase 1 Step 2 by creating both instances, loading the script in Live, and changing the selected device before any encoder controls are wired. Fail fast before control wiring is added.

- **`_pan_to_vol_ticks_delay` unification:** `EncModeSelectorComponent` has an existing `_pan_to_vol_ticks_delay` mechanism (5-tick countdown, Pan/Vol sub-mode toggle). Phase 2 can either unify this into the new per-button tick array or leave it alongside. Unified is cleaner and avoids two concurrent timer counters in `_on_timer` (Pitfall E4). The decision must be made before writing `_on_timer` changes to avoid rewriting that method twice.

- **Send button dual-role clarification:** The FEATURES.md research flag notes that per-track Send A/B/C MIDI note assignments are not explicitly wired in the current script. The ARCHITECTURE.md research confirmed the Send A/B/C buttons (notes 88-90) are global mode selectors only — there are no separate per-track send buttons on the APC40. This interpretation is the basis for the Phase 2 design. Confirm this reading is correct before Phase 2 coding begins by cross-referencing APC40 hardware documentation.

---

## Sources

### Primary (HIGH confidence)

- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/DeviceComponent.py` — `_assign_parameters`, `set_parameter_controls`, bank structure (source timestamp 2025-03-17)
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Generic/Devices.py` — `parameter_banks`, column-major `group()` interleaving confirmed
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/Util.py` — `group(lst, n)` column-major implementation
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ChannelStripComponent.py` — `set_send_controls()` maps encoders to send level only; no built-in send enable button
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ControlSurfaceComponent.py` — `_register_timer_callback`, `_unregister_timer_callback`
- `/Users/stoersignal/Dev/APC_64_40_12/EncModeSelectorComponent.py` — existing `_pan_to_vol_ticks_delay` / `_on_timer` pattern; mode routing; timer already registered
- `/Users/stoersignal/Dev/APC_64_40_12/ToggleMomentaryChannelStripComponent.py` — v1.0 reference implementation for toggle/momentary timer pattern
- `/Users/stoersignal/Dev/APC_64_40_12/EncoderDeviceComponent.py` — appointed device listener pattern; `_alt_device` dual-DeviceComponent precedent
- `/Users/stoersignal/Dev/APC_64_40_12/ShiftableDeviceComponent.py` — shift guard pattern, `ChannelTranslationSelector` usage, bank index management
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` — full encoder and mode button wiring, CC assignments, composition layer
- `/Users/stoersignal/Dev/APC_64_40_12/EncoderUserModesComponent.py` — canonical `release_parameter()` before mode switch pattern
- `/Users/stoersignal/Dev/APC_64_40_12/ConfigurableButtonElement.py` — deferred listener queue pattern (`_pending_listeners`)
- `/Users/stoersignal/Dev/APC_64_40_12/ShiftableEncoderSelectorComponent.py` — shift toggle re-routing of encoder bank buttons
- `.planning/codebase/CONCERNS.md` — existing timer cleanup gap in `StepSequencerComponent`; confirms Pitfall 2 is a real risk in this codebase

### Secondary (MEDIUM confidence)

- [Ableton Live 11 MIDIRemoteScripts — DeviceComponent.py](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts/blob/master/_Framework/DeviceComponent.py) — bank structure confirmed in Live 11 source; API confirmed stable through Live 12
- [Ableton Live 11 MIDIRemoteScripts — _Generic/Devices.py](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts/blob/master/_Generic/Devices.py) — `number_of_parameter_banks`, 8-parameter bank structure confirmed

---

*Research completed: 2026-03-31*
*Ready for roadmap: yes*
