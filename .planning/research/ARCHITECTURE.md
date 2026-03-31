# Architecture Patterns

**Domain:** 16-parameter encoder control + toggle/momentary Send A/B/C in Ableton _Framework control surface script
**Milestone:** v1.1 16Macros
**Researched:** 2026-03-31
**Confidence:** HIGH — based on direct source analysis of codebase plus verified Framework source

---

## Context: What Already Exists

The v1.0 codebase ships two hardware encoder rows and an encoder mode system:

| Encoder Row | CC Numbers | Count | Current Component Owner |
|---|---|---|---|
| "Device encoders" (row below display) | CC 16–23, channel 0 | 8 | `ShiftableDeviceComponent` |
| "Top encoders" (global track control row) | CC 48–55, channel 0 | 8 | `EncModeSelectorComponent` |

The four global mode buttons (notes 87–90: Pan / Send A / Send B / Send C) currently route the top encoder row exclusively via `EncModeSelectorComponent`. In Pan mode the top encoders map to per-track pan; in Send A/B/C mode they map to per-track send levels. The device encoder row is entirely independent — always under `ShiftableDeviceComponent`, responding to shift+bank-button navigation.

The `ToggleMomentaryChannelStripComponent` (v1.0) provides the proven timer pattern: `_register_timer_callback`, tick-countdown state per button, and revert-on-release for boolean track attributes (`solo`, `mute`).

---

## Feature 1: 16-Parameter Encoder Mapping in Pan Mode

### The Core Constraint

The Framework's `DeviceComponent._assign_parameters()` connects one 8-element `_parameter_controls` tuple to one "bank" of 8 parameters at a time. Banks are fixed 8-parameter slices of `DEVICE_DICT` entries, or auto-grouped in chunks of 8 for unmapped devices. There is no native "16 controls to one bank" mechanism.

**Consequence:** To display params 1–8 on the top encoders AND params 9–16 on the device encoders simultaneously, two independent `DeviceComponent` instances must each point at the same device with different `_bank_index` values (0 and 1 respectively).

### Recommended Design

**Use two `DeviceComponent` instances targeting the same selected device, at bank 0 and bank 1.**

The `ShiftableDeviceComponent` already handles the device encoder row at `bank_index` driven by shift+bank-button. The top encoder row needs a parallel device component that:

1. Tracks the same appointed/selected device as `ShiftableDeviceComponent`
2. Is locked to `bank_index = 0` (params 1–8)
3. Is active only when Pan mode is selected

The device encoder row continues using `ShiftableDeviceComponent` but in Pan mode it should present `bank_index = 1` (params 9–16) rather than bank 0.

### Integration Point: `EncModeSelectorComponent.update()`

Currently, when `_mode_index == 0` (Pan mode), `EncModeSelectorComponent.update()` calls:

```python
self._mixer.channel_strip(index).set_pan_control(self._controls[index])
self._mixer.channel_strip(index).set_send_controls((None, None, None))
```

This must change: instead of routing top encoders to mixer pan, route them to a new `DeviceComponent` instance at bank 0. The mixer pan assignment should be cleared, and the device component at bank 0 should receive the top encoder controls.

This means `EncModeSelectorComponent` needs a reference to the new bank-0 device component (passed in constructor or via setter) so it can activate/deactivate parameter connections in `update()`.

### New Component: `Pan16DeviceComponent`

Create a new file `Pan16DeviceComponent.py`. This component:

- Extends `DeviceComponent` (not `ShiftableDeviceComponent` — no bank navigation buttons needed)
- Receives appointed device changes via `song().add_appointed_device_listener`
- Holds `bank_index = 0` permanently
- Exposes `set_parameter_controls(controls)` to receive the top 8 encoders
- Is enabled/disabled by `EncModeSelectorComponent` based on mode

The appointed device listener pattern already exists in `EncoderDeviceComponent` (line 50: `self.song().add_appointed_device_listener(self._on_device_changed)`) — copy this directly.

### `ShiftableDeviceComponent` Modification for Pan Mode

When Pan mode is active, the device encoder row (CC 16–23) should display device params 9–16. Currently `ShiftableDeviceComponent` starts at bank 0 and navigates with shift+bank-buttons. The simplest approach:

- In Pan mode, `ShiftableDeviceComponent` is set to `bank_index = 1` via a new `set_pan_mode(active)` method, which calls `set_mode(1)` on the internal `_control_translation_selector` and updates the display.
- When Pan mode exits, the `_bank_index` reverts to its last user-selected value.

**Alternative (simpler):** Do not modify `ShiftableDeviceComponent`. Instead, disconnect its parameter controls in Pan mode and route the device encoder row through a second `Pan16DeviceComponent` instance (bank 1). Reconnect `ShiftableDeviceComponent` when Pan mode exits.

The "disconnect/reconnect" alternative is lower risk because it avoids modifying the tested `ShiftableDeviceComponent` and reuses the same appointed-device tracking code in a second component instance.

### Wiring Change in `APC_64_40_9._setup_global_control()`

```python
# New additions (alongside existing components):
self._pan16_device_top = Pan16DeviceComponent(bank_index=0)    # top encoders → params 1-8
self._pan16_device_enc = Pan16DeviceComponent(bank_index=1)    # device encoders → params 9-16
```

`EncModeSelectorComponent` needs the references so `update()` can wire/unwire them:

```python
self._encoder_modes = EncModeSelectorComponent(
    self._mixer,
    pan16_top=self._pan16_device_top,
    pan16_enc=self._pan16_device_enc,
    device_component=self._device,
    global_param_controls=tuple(self._global_param_controls),
    device_param_controls=tuple(device_param_controls)   # need to pass down
)
```

Or expose them via setters to keep the constructor unchanged.

---

## Feature 2: Toggle/Momentary for Send A/B/C Buttons

### Hardware Clarification

The APC40 has **no per-track Send A/B/C hardware buttons**. The physical buttons at notes 88, 89, 90 are the global encoder mode selectors. "Send A/B/C per-track buttons get toggle/momentary" in the milestone context means: the **mode selector buttons** (Send A, Send B, Send C) get toggle/momentary behavior — short press selects that send mode permanently; long press activates that send mode only while held, reverting to the previous mode on release.

This is directly analogous to the `EncModeSelectorComponent._on_timer` press-hold mechanism already in the codebase (the Pan/Vol mode toggle uses 5 ticks). The v1.1 version extends this to Send A/B/C with the same 4-tick (~400ms) threshold from v1.0.

### Integration Point: `EncModeSelectorComponent`

The existing `_pan_to_vol_ticks_delay` field and `_on_timer` in `EncModeSelectorComponent` already handle press-hold for the Pan button (to switch between Pan mode and Volume mode). The Send A/B/C buttons need the same treatment.

**Modify `EncModeSelectorComponent._mode_value()`** to arm the ticks countdown for buttons at index 1, 2, 3 (Send A/B/C), not just index 0 (Pan). On threshold expiry, the mode activates momentarily. On release before threshold, it toggles (stays in the new mode).

The exact inversion logic to implement:
- **Short press:** Set mode index to the pressed button's index. Mode persists after release. (Current behavior — no change needed.)
- **Long press:** Set mode index to the pressed button's index at press-down (immediate activation, zero latency). After threshold, mark as momentary. On release, revert `_mode_index` to the mode that was active before the press.

This mirrors the v1.0 `_handle_toggle_momentary` pattern precisely, transposed to mode indices instead of boolean track attributes.

### State Variables Needed in `EncModeSelectorComponent`

```python
self._send_ticks_delay = [-1, -1, -1, -1]    # one per mode button (index 0-3)
self._send_mode_before_press = 0              # mode index active before press
self._send_momentary_active = False           # True if long-press threshold crossed
self._send_pressed_mode = -1                  # which mode is currently held
```

The per-button tick array avoids allocating separate fields per button, consistent with the existing code style in the sequencer (`_on_timer` approach).

### No New File Needed

This is a modification to the existing `EncModeSelectorComponent.py`, not a new component. The timer callback is already registered in `__init__` and unregistered in `disconnect`. The `_on_timer` method already exists.

---

## Component Boundary Map (Post-v1.1)

| Component | Responsibility | New/Modified |
|---|---|---|
| `Pan16DeviceComponent` | Track appointed device; map 8 encoders to one bank (index 0 or 1) of device params | **NEW FILE** |
| `EncModeSelectorComponent` | Mode switching for top encoder row. Pan mode: activate `Pan16DeviceComponent`. Send A/B/C: activate send routing. Long-press momentary for all mode buttons | **MODIFIED** |
| `ShiftableDeviceComponent` | Device encoder row navigation with shift+bank-buttons. In Pan mode: disconnected from encoders (or held at bank 1) | **MODIFIED (minimally)** or disconnect/reconnect from composition |
| `ToggleMomentaryChannelStripComponent` | Solo/Mute toggle/momentary per track (v1.0, unchanged) | No change |
| `SpecialMixerComponent` | Factory for channel strips (v1.0, unchanged) | No change |
| `APC_64_40_9._setup_global_control()` | Wire new `Pan16DeviceComponent` instances, pass references to `EncModeSelectorComponent` | **MODIFIED** |
| `APC_64_40_9._setup_device_and_transport_control()` | Device encoder row setup; may need to expose `device_param_controls` tuple for `EncModeSelectorComponent` | **MODIFIED (minimally)** |

---

## Data Flow: Pan Mode (16 Parameters)

```
Pan button pressed (note 87)
  → EncModeSelectorComponent._mode_value(value=127)
  → EncModeSelectorComponent.update() [mode_index == 0]
    → mixer.channel_strip(i).set_pan_control(None)          # release mixer pan
    → mixer.channel_strip(i).set_send_controls((None,None,None))
    → pan16_device_top.set_parameter_controls(top_encoders)  # NEW: bank 0, params 1-8
    → pan16_device_enc.set_parameter_controls(device_encoders) # NEW: bank 1, params 9-16
    → device_component.set_parameter_controls(None)          # disconnect ShiftableDevice

Pan mode active:
  top encoders (CC 48-55) → Pan16DeviceComponent(bank=0) → device.params[0:8]
  device encoders (CC 16-23) → Pan16DeviceComponent(bank=1) → device.params[8:16]

Send A button pressed (note 88):
  → EncModeSelectorComponent.update() [mode_index == 1]
    → pan16_device_top.set_parameter_controls(None)          # release device params
    → pan16_device_enc.set_parameter_controls(None)          # release device params
    → device_component.set_parameter_controls(device_encoders) # reconnect ShiftableDevice
    → mixer.channel_strip(i).set_send_controls((top_encoders[i], None, None))  # send A
```

---

## Data Flow: Toggle/Momentary Send A/B/C Buttons

```
Send A button press-down (value=127):
  → EncModeSelectorComponent._mode_value(127, sender=send_a_button)
  → _send_mode_before_press = self._mode_index   # record current mode
  → set_mode(1)                                  # activate Send A immediately
  → _send_ticks_delay[1] = LONG_PRESS_DELAY      # arm countdown

EncModeSelectorComponent._on_timer (ticks 1..3):
  → _send_ticks_delay[1] > 0, decrement

EncModeSelectorComponent._on_timer (tick 4, threshold crossed):
  → _send_momentary_active = True
  → _send_pressed_mode = 1

Send A button release (value=0):
  → EncModeSelectorComponent._mode_value(0, sender=send_a_button)
  → IF _send_momentary_active and _send_pressed_mode == 1:
      set_mode(_send_mode_before_press)          # revert to previous mode
      _send_momentary_active = False
  → _send_ticks_delay[1] = -1

Short press (release before tick 4):
  → _send_ticks_delay[1] = -1, _send_momentary_active stays False
  → Send A mode stays active (already set at press-down)
```

---

## Integration Points Summary

### 1. New file: `Pan16DeviceComponent.py`

Extends `DeviceComponent`. Constructor takes `bank_index` (0 or 1). Adds appointed device listener (same pattern as `EncoderDeviceComponent` lines 50, 84–89). Exposes `set_parameter_controls()`. No bank navigation buttons. Approximately 40–60 lines.

### 2. `EncModeSelectorComponent.py` — two changes

**Change A (Pan mode routing):** `update()` must route to `Pan16DeviceComponent` instances when `_mode_index == 0`, and disconnect them in all other modes. Requires constructor or setter to receive `pan16_top`, `pan16_enc`, `device_component` references.

**Change B (toggle/momentary mode buttons):** `_mode_value()` and `_on_timer()` extended with the tick-countdown pattern for all 4 mode buttons. The existing `_pan_to_vol_ticks_delay` field may be unified into a single mechanism or left as-is with the new fields added alongside it.

### 3. `APC_64_40_9._setup_global_control()` — constructor/setter calls

Instantiate `Pan16DeviceComponent` for bank 0 and bank 1. Pass them to `EncModeSelectorComponent`. The device encoder controls (`device_param_controls` list) are created in `_setup_device_and_transport_control()` — they need to be accessible in `_setup_global_control()`. Store them as `self._device_param_controls` on the instance (currently they are local to the method).

### 4. `APC_64_40_9._setup_device_and_transport_control()` — promote local variable

Change `device_param_controls` from a local list to `self._device_param_controls` so `_setup_global_control()` can reference it.

### 5. No change to `ToggleMomentaryChannelStripComponent.py`

The v1.0 component is unaffected by both v1.1 features.

### 6. No change to `SpecialMixerComponent.py`, `ShiftableSelectorComponent.py`, `APC.py`

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Trying to pass 16 controls to one DeviceComponent

**What:** Create a 16-element tuple and call `ShiftableDeviceComponent.set_parameter_controls(16_controls)`.

**Why bad:** `EncModeSelectorComponent.set_controls()` asserts `len(controls) == 8`. `ShiftableDeviceComponent._assign_parameters()` zips controls against an 8-parameter bank — it only assigns the first 8 even if 16 are passed. The second 8 controls never get assigned.

**Instead:** Two DeviceComponent instances, one per 8-encoder row.

### Anti-Pattern 2: Using bank navigation buttons to cycle to bank 1

**What:** Have the user press shift+bank-button to get to params 9–16 on the device encoder row while Pan mode is active.

**Why bad:** This requires the user to manually navigate to bank 1 every time they enter Pan mode. The milestone requirement says "Pan mode maps device encoders to device parameters 9-16" — this implies automatic, not user-driven bank selection.

**Instead:** `Pan16DeviceComponent` locks `bank_index` in `__init__`. No user interaction required.

### Anti-Pattern 3: Toggling send encoder mapping to implement "toggle/momentary sends"

**What:** On Send A button long-press, activate send encoder control; on release, remove it. Treating send level encoders as togglable.

**Why bad:** The APC40 hardware has no per-track send button. Sends are continuous parameters (volume levels) — there is no boolean send state to toggle. This interpretation is not actionable.

**Instead:** The toggle/momentary behavior applies to the **mode selector button itself** (Send A button = note 88 = global encoder mode): short press permanently enters Send A encoder mode; long press enters it momentarily and reverts on release.

### Anti-Pattern 4: Modifying `ShiftableDeviceComponent` bank navigation for Pan mode

**What:** Add a `set_pan_mode()` method to `ShiftableDeviceComponent` that forces `_bank_index = 1` when Pan mode is active.

**Why bad:** `ShiftableDeviceComponent` is shift-button-controlled. Adding Pan mode awareness to it creates cross-concern coupling — the device component would need to know about encoder mode state, violating the single-responsibility boundary.

**Instead:** Disconnect `ShiftableDeviceComponent` from the device encoder controls during Pan mode (call `set_parameter_controls(None)`) and let `Pan16DeviceComponent(bank=1)` own those controls instead.

---

## Suggested Build Order

This sequence keeps each step independently loadable and verifiable in Ableton Live.

**Step 1 — Promote device encoder controls to instance variable**

In `_setup_device_and_transport_control()`, change `device_param_controls = []` to `self._device_param_controls = []` and update all references. No behavior change. Verify: script loads, all device controls work.

**Step 2 — Create `Pan16DeviceComponent.py` (no wiring yet)**

New file, two instances (bank 0, bank 1). No wiring to encoders yet — just verify script loads without error.

**Step 3 — Wire Pan mode to `Pan16DeviceComponent`**

Modify `EncModeSelectorComponent.update()` mode 0 branch: release mixer pan, activate `Pan16DeviceComponent` for top and device encoder rows, disable `ShiftableDeviceComponent` parameter controls. All other modes: do the reverse. Verify: Pan button routes both encoder rows to device params 1–16; Send A/B/C routes top encoders to sends as before; device encoder row under ShiftableDevice in Send modes.

**Step 4 — Add toggle/momentary to Send A/B/C mode buttons**

Add tick-countdown state to `EncModeSelectorComponent`. Extend `_mode_value()` and `_on_timer()`. Verify: short press on Send A/B/C permanently selects mode; long press activates mode then reverts on release; Pan mode unchanged.

**Step 5 — Edge cases**

Test: rapid mode switching does not leave stuck encoder assignments; mid-hold mode transition reverts correctly; appointed device changes during Pan mode update both `Pan16DeviceComponent` instances; shift held during mode press does not cause stuck mode state.

---

## Files to Create or Modify

| Action | File | Change |
|---|---|---|
| Create | `Pan16DeviceComponent.py` | New component, ~50 lines |
| Modify | `EncModeSelectorComponent.py` | Pan mode routing + toggle/momentary for all mode buttons |
| Modify | `APC_64_40_9.py` | Promote `device_param_controls` to instance var; instantiate and wire `Pan16DeviceComponent`; extend `EncModeSelectorComponent` constructor/setter calls |
| No change | `ToggleMomentaryChannelStripComponent.py` | v1.0 component unaffected |
| No change | `SpecialMixerComponent.py` | Unchanged |
| No change | `ShiftableDeviceComponent.py` | Unchanged (disconnected from encoders during Pan mode by EncModeSelectorComponent) |
| No change | `ShiftableSelectorComponent.py` | Unchanged |

---

## Open Questions / Risks

| Question | Impact | Confidence |
|---|---|---|
| Does Framework allow two DeviceComponent instances on the same device simultaneously without conflict? | HIGH — core assumption of the 16-param design | MEDIUM — no official doc; `EncoderDeviceComponent` uses `_alt_device = DeviceComponent()` which suggests it is possible; verify in Step 2 |
| Is `EncModeSelectorComponent._on_timer` already unregistered when mode selector is disabled (non-normal mode)? | MEDIUM — timer must not fire in shift mode | HIGH — `_on_timer` already guards with `if self.is_enabled()` |
| Do `Pan16DeviceComponent` instances need to handle the `device_selection_follows_track_selection` flag from `APC_64_40_9`? | MEDIUM — if not tracked, params won't update on track change | MEDIUM — use `appointed_device_listener` which fires on track-follows-device changes; verify behavior |
| What happens with devices that have fewer than 16 parameters? | LOW — extra controls silently release; `_assign_parameters` already handles `_parameter_controls[len(bank):]` with release | HIGH — confirmed in Framework source analysis |

---

## Sources

- Direct source analysis: `EncModeSelectorComponent.py` — mode switching, timer pattern (HIGH confidence)
- Direct source analysis: `ShiftableDeviceComponent.py` — bank_index, parameter_controls wiring (HIGH confidence)
- Direct source analysis: `EncoderDeviceComponent.py` — appointed device listener pattern, dual DeviceComponent usage (HIGH confidence)
- Direct source analysis: `APC_64_40_9.py` — composition layer, encoder row MIDI assignments (HIGH confidence)
- Direct source analysis: `ToggleMomentaryChannelStripComponent.py` — v1.0 timer pattern to replicate (HIGH confidence)
- [Ableton Live 11 MIDIRemoteScripts — DeviceComponent.py](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts/blob/master/_Framework/DeviceComponent.py) — `_assign_parameters`, bank structure, 8-param-per-bank constraint (MEDIUM confidence — Live 11 source; API stable across Live 12)
- [Ableton Live 11 MIDIRemoteScripts — _Generic/Devices.py](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts/blob/master/_Generic/Devices.py) — `number_of_parameter_banks`, 8-parameter bank structure confirmed (MEDIUM confidence)

---

*Architecture analysis: 2026-03-31*
