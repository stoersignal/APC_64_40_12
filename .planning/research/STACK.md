# Technology Stack: 16Macros Milestone

**Project:** APC40 Toggle/Momentary Button Behavior
**Milestone:** v1.1 16Macros — 16-parameter encoder mapping in Pan mode + Send A/B/C toggle/momentary
**Researched:** 2026-03-31
**Overall confidence:** HIGH — all claims verified against decompiled _Framework source at
`/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/` (source timestamp 2025-03-17)

---

## What Is Already Settled (Do Not Re-Research)

The v1.0 timer infrastructure, shift guards, `_register_timer_callback`, tick rate, and
`LONG_PRESS_DELAY = 4` are proven and unchanged. The new milestone reuses them verbatim.

---

## Feature 1: 16-Parameter Encoder Mapping in Pan Mode

### What the hardware provides

Two independent encoder rows are wired in `_setup_device_and_transport_control` and
`_setup_global_control`:

| Row | CC range | Python list | Current Pan-mode role |
|-----|----------|-------------|----------------------|
| Device encoders (bottom) | CC 16-23, ch 0 | `device_param_controls` (8x `RingedEncoderElement`) | Connected to `ShiftableDeviceComponent` — parameters 1-8 of selected device |
| Top encoders (global) | CC 48-55, ch 0 | `_global_param_controls` (8x `RingedEncoderElement`) | Connected to per-track panning via `EncModeSelectorComponent` when mode_index == 0 |

The goal is: when Pan mode is active, top encoders map to device params 1-8 AND device
encoders map to device params 9-16 simultaneously, giving 16 parameters total.

### Why the existing `DeviceComponent.set_parameter_controls` works for this

`DeviceComponent._assign_parameters` iterates `zip(self._parameter_controls, bank)` and
calls `control.connect_to(parameter)` on each pair. If you pass a tuple of 16 controls and
provide a 16-element bank, it connects all 16. The method is already correct — only the
inputs need to change.

**Confidence: HIGH** — verified in `_Framework/DeviceComponent.py` line 321-331.

### The bank-size problem and correct solution

`_Generic.Devices.parameter_banks(device)` always partitions parameters into groups of 8.
For generic (non-DEVICE_DICT) devices it calls `group(device_parameters_to_map(device), 8)`,
where `group` uses `zip_longest(*[lst[i::n] for i in range(n)])` — column-major interleaving,
not sequential rows. `bank[0]` does NOT contain parameters 1-8; it contains parameters at
indices 0, 8, 16, 24... This makes `_current_bank_details` wrong for the 16-param use case.

**Correct approach:** bypass the bank system entirely for the 16-param case. Access
`device.parameters[1:17]` directly. `parameters[0]` is always "Device On/Off"; parameters
1-16 are the first 16 controllable parameters (macro parameters for instruments and effects
with macros, or sequential device parameters otherwise).

**Confidence: HIGH** — verified by reading `_Generic/Devices.py` lines 355-381 and
`_Framework/Util.py` lines 176-178.

### Recommended implementation: new `SixteenParamDeviceComponent`

Create a new file `SixteenParamDeviceComponent.py` that subclasses `DeviceComponent` and
overrides `_assign_parameters`:

```python
from _Framework.DeviceComponent import DeviceComponent
from ableton.v2.base import liveobj_valid

class SixteenParamDeviceComponent(DeviceComponent):
    """DeviceComponent that maps up to 16 device parameters directly to controls."""

    def _assign_parameters(self):
        if self._parameter_controls is None or not liveobj_valid(self._device):
            return
        # parameters[0] is Device On/Off; skip it.
        mappable = [p for p in self._device.parameters[1:] if liveobj_valid(p)]
        for index, control in enumerate(self._parameter_controls):
            if control is None:
                continue
            if index < len(mappable):
                control.connect_to(mappable[index])
            else:
                control.release_parameter()
        self._bank_name = 'Params 1-16'
```

Pass it a 16-element tuple: `tuple(device_param_controls) + tuple(global_param_controls)`.
When Pan mode activates in `EncModeSelectorComponent`, call
`sixteen_param_device.set_enabled(True)` and clear pan assignments from the mixer strips;
when leaving Pan mode, disable it and restore assignments.

**Why not subclass `ShiftableDeviceComponent`:** `ShiftableDeviceComponent` adds
shift-guarded bank navigation and `ChannelTranslationSelector` on top of `DeviceComponent`.
The 16-param mode never needs bank navigation (both rows are locked to params 1-16). A
direct `DeviceComponent` subclass is simpler and avoids the translation-selector complexity.

**Why not call `set_parameter_controls` twice on the existing `ShiftableDeviceComponent`:**
`set_parameter_controls` stores a single `_parameter_controls` reference. Calling it a
second time replaces the first. Two separate `DeviceComponent` instances with 8 controls
each would fight over `_device_bank_registry.set_device_bank` and `appointed_device`
listener — they would step on each other on every device change.

### Mode activation wiring

`EncModeSelectorComponent.update()` is called every time the mode changes. In the
`_mode_index == 0` branch (Pan mode), add:

1. For each of the 8 mixer strips: call `strip.set_pan_control(None)` (releases panning
   assignment from top encoders).
2. Enable the `SixteenParamDeviceComponent` with combined 16-encoder tuple.
3. In all other mode branches: disable `SixteenParamDeviceComponent` and restore the normal
   `strip.set_pan_control(control)` assignments.

`EncModeSelectorComponent` already holds a `_mixer` reference and calls
`self._mixer.channel_strip(index).set_pan_control(...)` — this is the exact hook needed.
Add a `_sixteen_param_device` reference injected at construction time.

**Confidence: HIGH** — `EncModeSelectorComponent.update()` already owns this switching
logic; the pattern is a direct extension of what exists.

### LED ring modes on the top encoders in Pan mode

`RingedEncoderElement.set_ring_mode_button` links the CC 56-63 buttons to the encoder ring
display. In Pan mode, the top encoders will show device parameter feedback via
`connect_to(parameter)`. The ring mode button is already wired; no changes needed there.
The ring mode will display whatever the connected parameter reports.

---

## Feature 2: Toggle/Momentary for Send A/B/C Buttons

### What these buttons are

The four buttons at MIDI note 87-90 (channel 0) are the global encoder mode selectors:

| Note | Name | Current behavior |
|------|------|-----------------|
| 87 | Pan_Button | Sets encoder mode to 0 (Pan/device panning) |
| 88 | Send_A_Button | Sets encoder mode to 1 (Send A) |
| 89 | Send_B_Button | Sets encoder mode to 2 (Send B) |
| 90 | Send_C_Button | Sets encoder mode to 3 (Send C) |

These are NOT per-track send enable/disable buttons. They select which parameter the 8 top
encoders control. Toggle/momentary on these buttons means: short press locks that encoder
mode; long press temporarily enters that encoder mode while held, then reverts to the
previous mode on release.

### Existing partial implementation in `EncModeSelectorComponent`

`EncModeSelectorComponent` already implements long-press for the Pan button specifically via
`_pan_to_vol_ticks_delay` and `_on_timer`. The logic switches between Pan and Volume
sub-modes. This is the exact pattern to generalise across all four buttons.

The existing timer infrastructure is already registered (`_register_timer_callback` called in
`__init__`, `_unregister_timer_callback` called in `disconnect`). No new timer wiring is
needed.

### Recommended implementation

Extend `EncModeSelectorComponent._mode_value` and `_on_timer` to track a
`_mode_before_long_press` state and revert on release, using the same `LONG_PRESS_DELAY = 4`
constant from v1.0:

```python
LONG_PRESS_DELAY = 4  # 4 ticks x 100ms = ~400ms (matches Solo/Mute threshold)

# In __init__:
self._send_momentary_ticks = -1
self._mode_before_long_press = -1

# In _mode_value:
def _mode_value(self, value, sender):
    if self.is_enabled():
        index = self._modes_buttons.index(sender)
        if value != 0:
            if self._shift_pressed:  # existing shift guard pattern
                return
            self._mode_before_long_press = self._mode_index
            self.set_mode(index)
            self._send_momentary_ticks = LONG_PRESS_DELAY
        else:  # release
            if self._send_momentary_active:
                self.set_mode(self._mode_before_long_press)
                self._send_momentary_active = False
            self._send_momentary_ticks = -1

# In _on_timer:
if self._send_momentary_ticks > -1:
    if self._send_momentary_ticks == 0:
        self._send_momentary_active = True
    self._send_momentary_ticks -= 1
```

This replaces the existing `_pan_to_vol_ticks_delay` mechanism with a unified approach that
covers all four mode buttons.

**Confidence: HIGH** — directly mirrors `ToggleMomentaryChannelStripComponent` pattern which
is proven in this codebase. `EncModeSelectorComponent` already has the timer registered and
the `_modes_buttons` list populated.

### Shift guard requirement

`EncModeSelectorComponent._mode_value` has no shift guard today. Add the same guard used in
`_handle_toggle_momentary`:

```python
if self._shift_pressed:
    return
```

`EncModeSelectorComponent` does not currently track `_shift_pressed`. Either add a
`set_shift_button` setter (same pattern as `ShiftableDeviceComponent`) or check whether
`ShiftableEncoderSelectorComponent._toggle_pressed` is accessible via `self._parent`. The
simpler approach is adding `set_shift_button` directly to `EncModeSelectorComponent` — it
already has `self._mixer` so the constructor can take an extra optional button.

**Confidence: HIGH** — `ShiftableDeviceComponent` provides the exact reference implementation
for this pattern.

---

## APIs Used (New or Changed for This Milestone)

| API | Location | Purpose | Confidence |
|-----|----------|---------|------------|
| `device.parameters[1:17]` | `Live.Device` | Direct sequential parameter access, bypasses bank system | HIGH |
| `control.connect_to(parameter)` | `_Framework.InputControlElement` | Connect encoder to Live parameter | HIGH |
| `control.release_parameter()` | `_Framework.InputControlElement` | Disconnect encoder from parameter | HIGH |
| `DeviceComponent.set_parameter_controls(controls)` | `_Framework.DeviceComponent` | Register controls with device component | HIGH |
| `DeviceComponent.set_device(device)` | `_Framework.DeviceComponent` | Point component at selected device | HIGH |
| `song().add_appointed_device_listener` | `Live.Song` | Respond to device selection changes | HIGH |
| `_register_timer_callback` / `_unregister_timer_callback` | `_Framework.ControlSurfaceComponent` | Already used in this codebase | HIGH |
| `ChannelStripComponent.set_pan_control(None)` | `_Framework.ChannelStripComponent` | Release pan assignment when Pan mode activates | HIGH |

---

## APIs NOT to Use

### `parameter_banks(device)` for 16-param mapping

`parameter_banks` returns column-interleaved groups of 8, not sequential rows. Using it
for the 16-param case gives wrong parameter ordering on any device with more than 8
parameters. Access `device.parameters[1:17]` directly.

### `ChannelTranslationSelector` on 16 controls

`ShiftableDeviceComponent` wraps the 8 device encoders in a `ChannelTranslationSelector(8)`
for bank navigation. For the 16-param mode, bank navigation is disabled — both encoder rows
are locked to params 1-16. Do not pass the 16 combined controls through a translation
selector.

### Modifying `ShiftableDeviceComponent` to hold 16 controls

`ShiftableDeviceComponent` hardcodes 8-control assumptions in `set_parameter_controls`
(assertion `len(controls) == 8` is not there, but `ChannelTranslationSelector(8)` is). More
importantly, `ShiftableDeviceComponent` already has its own device-tracking and bank
navigation that serves the existing 8-param mode. Expanding it to 16 in-place would entangle
two unrelated modes and make both harder to test. Keep them separate.

### Modifying `EncoderDeviceComponent` for 16-param mode

`EncoderDeviceComponent` manages an alternative device control path that wraps
`DeviceComponent` internally. It has its own lock, on/off, and device-follow logic. It is
not the right base for the 16-param map because its wiring assumptions (4 mode buttons, lock
button as buttons[0]) conflict with what the Pan-mode use case needs.

---

## Files to Create or Modify

| File | Action | Why |
|------|--------|-----|
| `SixteenParamDeviceComponent.py` | **Create** | New `DeviceComponent` subclass, overrides `_assign_parameters` for direct 16-param mapping |
| `EncModeSelectorComponent.py` | **Modify** | Extend existing `_on_timer` + `_mode_value` for send button toggle/momentary; add shift guard; accept `_sixteen_param_device` reference |
| `APC_64_40_9.py` | **Modify** | Instantiate `SixteenParamDeviceComponent`, wire combined 16-encoder tuple, pass reference to `EncModeSelectorComponent` |

**Do not modify:** `ToggleMomentaryChannelStripComponent`, `SpecialChanStripComponent`,
`ShiftableDeviceComponent`, `SpecialMixerComponent`, `ShiftableEncoderSelectorComponent`,
`EncoderUserModesComponent`. None of these are in the change path.

---

## Test Stub Requirements

The existing `framework_stubs.py` needs additions for new test coverage:

- `DeviceStub` with `parameters` list (index 0 = on/off placeholder, indices 1-16 = mock
  params). Each parameter stub needs `connect_to` / `release_parameter` tracking.
- `SixteenParamDeviceComponentStub` or direct instantiation with stubs — same pattern as
  `SpecialChanStripStub`.

The v1.0 `TrackStub`, `SongStub`, `ButtonStub` patterns do not need to change.

---

## Sources

- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/DeviceComponent.py` — `_assign_parameters`, `set_parameter_controls`, `_current_bank_details` (source timestamp 2025-03-17)
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Generic/Devices.py` — `parameter_banks`, `group` usage, `number_of_parameter_banks` (source timestamp 2025-03-17)
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/Util.py` — `group(lst, n)` column-major interleave implementation
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ChannelStripComponent.py` — `set_send_controls`, `_connect_parameters`, send index mapping
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ControlSurfaceComponent.py` — `_register_timer_callback`, `_unregister_timer_callback`
- `/Users/stoersignal/Dev/APC_64_40_12/EncModeSelectorComponent.py` — existing `_pan_to_vol_ticks_delay` / `_on_timer` pattern
- `/Users/stoersignal/Dev/APC_64_40_12/ToggleMomentaryChannelStripComponent.py` — reference implementation for toggle/momentary timer pattern
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` — encoder CC assignments, mode wiring, global bank button assignments
- `/Users/stoersignal/Dev/APC_64_40_12/ShiftableDeviceComponent.py` — shift guard pattern, `ChannelTranslationSelector` usage
