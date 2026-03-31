# Phase 4: 16-Parameter Encoder Mapping - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Repurpose Pan mode (mode_index 0 in `EncModeSelectorComponent`) to map both encoder rows to device parameters instead of per-track pan. Top 8 encoders → device params 1-8 (fixed, no bank navigation). Device encoders → params 9-16 (with bank navigation via existing prev/next buttons). Clean teardown when leaving Pan mode.

</domain>

<decisions>
## Implementation Decisions

### Component Design
- **D-01:** Create new `Pan16DeviceComponent.py` (~50 lines) — two instances (bank 0 for top row, bank 1 for device row) targeting same appointed device. Mirrors `EncoderDeviceComponent._alt_device = DeviceComponent()` pattern.
- **D-02:** Both instances track appointed device changes (listen for `appointed_device` updates).
- **D-03:** Top-row instance is fixed at bank 0 (params 1-8, no bank navigation). Device-row instance starts at bank 1 (params 9-16) with bank navigation via existing prev/next buttons.

### Mode Switching
- **D-04:** Pan mode (mode_index 0) replaces per-track pan with device parameter mapping. Pan function effectively disabled in this mode.
- **D-05:** Leaving Pan mode (pressing Send A/B/C) fully disconnects: `release_parameter()` on all 16 encoders, disable both `Pan16DeviceComponent` instances. Send mode takes over top encoders normally.
- **D-06:** Entering Pan mode auto-sets device encoder bank to 1 (params 9-16).

### Hardware Layout Clarification
- **D-07:** Top encoders have mode buttons: Pan/Send A/Send B/Send C (via `EncModeSelectorComponent`)
- **D-08:** Device encoders have their own buttons: Device (lock)/Device On-Off/Prev Bank/Next Bank (via `EncoderDeviceComponent`)
- **D-09:** In Pan mode, device encoder bank buttons continue to function for navigating deeper banks (17-24, 25-32, etc.)

### Integration
- **D-10:** `device_param_controls` (currently local in `APC_64_40_9._setup_global_control`) needs to be promoted to instance variable `self._device_param_controls` so `EncModeSelectorComponent` can access them for Pan mode wiring.

### Claude's Discretion
- Whether `Pan16DeviceComponent` extends `DeviceComponent` directly or wraps it like `EncoderDeviceComponent` does
- Internal naming conventions for the two instances
- How to handle devices with fewer than 16 parameters (graceful degradation)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Integration Points
- `EncModeSelectorComponent.py` — Mode switching hub. `update()` method at line 74 is where Pan mode routing happens. `_mode_value()` at line 61 handles button presses.
- `APC_64_40_9.py` — Main composition. Lines 203-219 create `device_param_controls` (local). Lines 263-279 create `_global_param_controls` and `_encoder_modes`.

### Existing Pattern
- `EncoderDeviceComponent.py` — Uses `_alt_device = DeviceComponent()` for device parameter mapping. Shows appointed device listener pattern, lock button, bank navigation wiring.
- `ShiftableDeviceComponent.py` — The main device component. Gets `set_parameter_controls(None)` when its encoders are borrowed.

### Research
- `.planning/research/ARCHITECTURE.md` — Dual DeviceComponent pattern, integration points, build order
- `.planning/research/STACK.md` — `parameter_banks()` column-major trap, direct `device.parameters[1:17]` approach
- `.planning/research/PITFALLS.md` — Encoder ownership, `release_parameter()` on every mode switch

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EncoderDeviceComponent._alt_device = DeviceComponent()` — Proven pattern for secondary device parameter mapping
- `EncModeSelectorComponent._on_timer` / `_register_timer_callback` — Already wired, Phase 5 will extend
- `_global_param_controls` — Top 8 encoders, already instance variable
- Bank navigation buttons — Already wired in `EncoderDeviceComponent.set_controls_and_buttons()`

### Established Patterns
- Mode switching: `EncModeSelectorComponent.update()` routes `_controls` to pan/send based on `_mode_index`
- Device tracking: `song().add_appointed_device_listener(callback)` for device change notifications
- Parameter connection: `DeviceComponent.set_parameter_controls(tuple)` + `set_bank_nav_buttons(up, down)`
- Cleanup: `release_parameter()` before reassigning encoders

### Integration Points
- `EncModeSelectorComponent.update()` mode_index 0 branch — currently sets pan, needs to set device params instead
- `APC_64_40_9._setup_global_control()` — needs to pass device encoder reference to `EncModeSelectorComponent`
- `ShiftableDeviceComponent` — gets `set_parameter_controls(None)` when Pan mode borrows device encoders

</code_context>

<specifics>
## Specific Ideas

- The `Pan16DeviceComponent` could use `DeviceComponent` directly (not a subclass) — just two instances with different bank indices, similar to how `EncoderDeviceComponent` wraps `_alt_device`.
- The top-row instance can use `set_bank_nav_buttons(None, None)` to prevent bank changes.
- Device encoders already have bank buttons wired via `EncoderDeviceComponent` — in Pan mode, these buttons should control the `Pan16DeviceComponent` bank 1 instance's navigation instead.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-16-parameter-encoder-mapping*
*Context gathered: 2026-03-31*
