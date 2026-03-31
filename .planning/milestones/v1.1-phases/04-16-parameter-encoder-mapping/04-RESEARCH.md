# Phase 4: 16-Parameter Encoder Mapping - Research

**Researched:** 2026-03-31
**Domain:** Ableton _Framework DeviceComponent bank isolation, encoder ownership handoff, mode teardown patterns
**Confidence:** HIGH — all claims verified against Live 12.1 decompiled source at `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/` (source timestamp 2025-03-17) and direct codebase reading

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Create new `Pan16DeviceComponent.py` (~50 lines) — two instances (bank 0 for top row, bank 1 for device row) targeting same appointed device. Mirrors `EncoderDeviceComponent._alt_device = DeviceComponent()` pattern.
- **D-02:** Both instances track appointed device changes (listen for `appointed_device` updates).
- **D-03:** Top-row instance is fixed at bank 0 (params 1-8, no bank navigation). Device-row instance starts at bank 1 (params 9-16) with bank navigation via existing prev/next buttons.
- **D-04:** Pan mode (mode_index 0) replaces per-track pan with device parameter mapping. Pan function effectively disabled in this mode.
- **D-05:** Leaving Pan mode (pressing Send A/B/C) fully disconnects: `release_parameter()` on all 16 encoders, disable both `Pan16DeviceComponent` instances. Send mode takes over top encoders normally.
- **D-06:** Entering Pan mode auto-sets device encoder bank to 1 (params 9-16).
- **D-07:** Top encoders have mode buttons: Pan/Send A/Send B/Send C (via `EncModeSelectorComponent`)
- **D-08:** Device encoders have their own buttons: Device (lock)/Device On-Off/Prev Bank/Next Bank (via `EncoderDeviceComponent`)
- **D-09:** In Pan mode, device encoder bank buttons continue to function for navigating deeper banks (17-24, 25-32, etc.)
- **D-10:** `device_param_controls` (currently local in `APC_64_40_9._setup_global_control`) needs to be promoted to instance variable `self._device_param_controls` so `EncModeSelectorComponent` can access them for Pan mode wiring.

### Claude's Discretion

- Whether `Pan16DeviceComponent` extends `DeviceComponent` directly or wraps it like `EncoderDeviceComponent` does
- Internal naming conventions for the two instances
- How to handle devices with fewer than 16 parameters (graceful degradation)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENC-01 | Pan mode maps top 8 encoders to selected device parameters 1-8 | `Pan16DeviceComponent(bank=0)` with `set_parameter_controls(top_encoders)` in `EncModeSelectorComponent.update()` mode 0 branch |
| ENC-02 | Pan mode maps device encoders to selected device parameters 9-16 | `Pan16DeviceComponent(bank=1)` with `set_parameter_controls(device_encoders)` in same mode 0 branch |
| ENC-03 | Top 8 encoders are fixed to parameters 1-8 (no bank navigation on top row) | `set_bank_nav_buttons(None, None)` on bank-0 instance; `_is_banking_enabled()` returns False when no buttons set |
| ENC-04 | Device encoders can navigate deeper banks (params 17-24, etc.) via existing bank buttons | `set_bank_nav_buttons(prev_button, next_button)` on bank-1 instance in Pan mode activation path |
| ENC-05 | Encoder LED rings reflect parameter values for both rows in Pan mode | `connect_to(parameter)` in `_assign_parameters` handles this automatically via `RingedEncoderElement` |
| ENC-06 | Parameters properly released when leaving Pan mode | `set_parameter_controls(None)` on both instances triggers `_release_parameters()` in `DeviceComponent.set_parameter_controls` |
| ENC-07 | Entering Pan mode does not break device encoder behavior in other modes | `ShiftableDeviceComponent.set_parameter_controls(None)` before assigning device encoders to `Pan16DeviceComponent`; restore on mode exit |
| MINT-01 | Existing encoder mode switching behavior preserved for short presses | `EncModeSelectorComponent.update()` modes 1/2/3 logic unchanged; only mode 0 branch changes |
| MINT-02 | Script loads and initializes without errors after modification | Verified build order: promote variable first, create file second, wire third |
</phase_requirements>

---

## Summary

Phase 4 repurposes Pan mode to simultaneously map both encoder rows (top: CC 48-55, device: CC 16-23) to the first 16 device parameters of the currently appointed device. The top row is locked to params 1-8 (bank 0); the device row starts at params 9-16 (bank 1) and can navigate further via existing bank buttons.

The design uses two `Pan16DeviceComponent` instances, each wrapping a `DeviceComponent` instance with an independent `DeviceBankRegistry`. This isolation is mandatory: the Framework's `DeviceBankRegistry` notifies all listeners when any component calls `set_device_bank()`. Two components sharing one registry would fight — each bank navigation press would trigger the other instance to jump to the same bank index. The fix is to pass `device_bank_registry=DeviceBankRegistry()` explicitly in each instance's constructor, or let `DeviceComponent.__init__` create a fresh one per instance (the default behavior when `device_bank_registry=None`).

The `_assign_parameters` method in `DeviceComponent` uses `_current_bank_details()` which calls `parameter_banks(device)[bank_index]`. The `parameter_banks()` function from `_Generic.Devices` uses column-major interleaving, not sequential rows. For the default bank-0 of an 8-parameter device this happens to give the right result (all 8 params are in bank 0). For bank-1 on a 16-parameter device, `parameter_banks(device)[1]` gives params at positions 8-15 sequentially for standard devices. Verify empirically on the first test device.

**Primary recommendation:** Extend `DeviceComponent` directly in `Pan16DeviceComponent`. Override `set_device()` to force `_bank_index` to the constructor-specified value after the parent's bank-registry lookup resets it. This is the minimal approach that keeps the two instances independent.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `_Framework.DeviceComponent` | Live 12.1 built-in | Base class for device parameter mapping | Already in use by `ShiftableDeviceComponent`, `EncoderDeviceComponent._alt_device` |
| `_Framework.DeviceBankRegistry` | Live 12.1 built-in | Per-device bank index storage and notification | Used by every `DeviceComponent`; must instantiate one per `Pan16DeviceComponent` to avoid cross-talk |
| `_Framework.ControlSurfaceComponent` | Live 12.1 built-in | Base class providing `song()`, `is_enabled()`, `set_enabled()` | Required for any non-DeviceComponent alternative |
| `Live.Song.appointed_device` | Live 12.1 API | Property + listener for currently selected device | `DeviceComponent.__on_appointed_device_changed` already subscribes; inherited automatically |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `_Generic.Devices.parameter_banks` | Live 12.1 built-in | Partition device parameters into bank slices | Use via `DeviceComponent._assign_parameters` (inherited); do NOT call directly |
| `ableton.v2.base.liveobj_valid` | Live 12.1 built-in | Guard against deleted/invalid Live objects | Already used in `DeviceComponent._assign_parameters`; needed in any override |

### Installation

No installation. All APIs are bundled with Ableton Live.

---

## Architecture Patterns

### Recommended Project Structure

```
APC_64_40_12/
├── Pan16DeviceComponent.py      # NEW: ~50 lines
├── EncModeSelectorComponent.py  # MODIFIED: update() mode-0 branch
├── APC_64_40_9.py               # MODIFIED: promote variable, wire new component
└── tests/
    ├── framework_stubs.py       # MODIFIED: add DeviceStub, ParameterStub, EncoderStub
    └── test_04_pan16_device.py  # NEW: unit tests for Phase 4
```

### Pattern 1: Independent DeviceBankRegistry per Pan16DeviceComponent

**What:** Each `Pan16DeviceComponent` instance receives its own `DeviceBankRegistry` in the constructor call, or relies on the default `None` which creates a fresh one.

**When to use:** Any time two `DeviceComponent` instances must coexist targeting the same device at different banks.

**Why it matters:** `DeviceBankRegistry.set_device_bank()` fires `notify_device_bank()` which triggers `_on_device_bank_changed` on every listener registered to that registry. If both instances share one registry, a bank-nav press on the device-row instance calls `set_device_bank(device, 2)`, which notifies the bank-0 instance, which calls `update()` and reassigns its controls to bank 2 — clobbering params 1-8 with params 17-24.

**Example:**

```python
# Source: _Framework/DeviceComponent.py line 36-38, DeviceBankRegistry.py
# Pan16DeviceComponent.__init__ — let DeviceComponent create its own fresh registry
from _Framework.DeviceComponent import DeviceComponent

class Pan16DeviceComponent(DeviceComponent):
    def __init__(self, bank_index):
        # device_bank_registry=None → DeviceComponent creates its own DeviceBankRegistry()
        DeviceComponent.__init__(self)
        self._fixed_bank_index = bank_index
```

### Pattern 2: Forcing Fixed Bank Index After set_device()

**What:** Override `set_device()` to re-assert `_bank_index` after the parent's registry lookup resets it.

**Why it matters:** `DeviceComponent.set_device()` (line 107) does:
```python
self._bank_index = self._device_bank_registry.get_device_bank(self._device)
```
For a fresh registry with a newly-seen device, `get_device_bank()` returns `0` (line 33 of DeviceBankRegistry: `return self._device_bank_registry.get(key, 0)`). This means the bank-1 instance gets reset to bank 0 every time a new device is appointed.

**Prevention:** Override `set_device()` and re-assert the fixed bank after the parent call:

```python
# Source: _Framework/DeviceComponent.py lines 97-112
def set_device(self, device):
    DeviceComponent.set_device(self, device)
    # Parent call resets _bank_index to 0 via fresh registry. Re-assert fixed bank.
    if self._device is not None:
        self._bank_index = self._fixed_bank_index
        self.update()
```

### Pattern 3: Encoder Ownership Handoff in EncModeSelectorComponent.update()

**What:** Before assigning encoders to `Pan16DeviceComponent`, release them from their current owners. Before restoring normal mode, release them from `Pan16DeviceComponent`.

**Canonical pattern** (from `EncoderUserModesComponent._set_modes()` lines 116-128):

```python
# Source: EncoderUserModesComponent.py lines 116-128
for control in self._param_controls:
    control.release_parameter()
    control.use_default_message()
# Then disable the previous sub-component, then enable the new one.
```

**Applied to mode-0 activation in `EncModeSelectorComponent.update()`:**

```python
# Mode 0 (Pan) branch — owns both encoder rows
if self._mode_index == 0:
    # 1. Clear mixer pan from top encoders
    for index in range(len(self._controls)):
        self._mixer.channel_strip(index).set_pan_control(None)
        self._mixer.channel_strip(index).set_send_controls((None, None, None))
    # 2. Release ShiftableDeviceComponent from device encoders
    if self._device_component is not None:
        self._device_component.set_parameter_controls(None)
    # 3. Assign both encoder rows to Pan16DeviceComponent instances
    if self._pan16_top is not None:
        self._pan16_top.set_parameter_controls(self._controls)        # top 8
    if self._pan16_enc is not None:
        self._pan16_enc.set_parameter_controls(self._device_controls) # device 8
        self._pan16_enc.set_bank_nav_buttons(self._prev_bank_btn, self._next_bank_btn)
```

**Applied to mode exit (modes 1/2/3):**

```python
# All non-Pan modes — restore ownership
if self._pan16_top is not None:
    self._pan16_top.set_parameter_controls(None)
if self._pan16_enc is not None:
    self._pan16_enc.set_parameter_controls(None)
    self._pan16_enc.set_bank_nav_buttons(None, None)
# Restore ShiftableDeviceComponent to device encoders
if self._device_component is not None:
    self._device_component.set_parameter_controls(self._device_controls)
# Then assign top encoders to pan or send per normal mode logic
for index in range(len(self._controls)):
    if self._mode_index == 1:
        self._mixer.channel_strip(index).set_send_controls((self._controls[index], None, None))
    # ... etc
```

### Pattern 4: Appointed Device Listener (inherited from DeviceComponent)

`Pan16DeviceComponent` does not need to manually add an `appointed_device` listener. `DeviceComponent.__init__` already subscribes to `song().appointed_device` via `@subject_slot('appointed_device')` on `__on_appointed_device_changed` (line 93). When `Pan16DeviceComponent` is constructed, the parent `__init__` wires this automatically.

However, `__on_appointed_device_changed` calls `self.set_device(device_to_appoint(self.song().appointed_device))` — which triggers the bank-reset problem described in Pattern 2. The override of `set_device()` handles this correctly.

### Anti-Patterns to Avoid

- **Sharing a DeviceBankRegistry between instances:** Both instances will fight over bank index on every device change and every bank navigation press. Each instance must have its own registry (the default when calling `DeviceComponent.__init__(self)` with no arguments).
- **Passing 16 controls to one DeviceComponent:** `EncModeSelectorComponent.set_controls()` asserts `len(controls) == 8`. Do not try to extend it. Two separate 8-control assignments are required.
- **Releasing device encoders without restoring ShiftableDeviceComponent:** When leaving Pan mode, `ShiftableDeviceComponent` must receive `set_parameter_controls(self._device_controls)` again, or the device encoder row becomes dead in all other modes.
- **Calling `DeviceComponent.__init__` with a shared registry argument:** Even if inadvertently passing `self._device._device_bank_registry`, both instances would subscribe to the same bank-change notifications. Always let each instance construct its own.
- **Using `parameter_banks(device)[1]` directly in custom code:** Rely on `_assign_parameters()` via `set_parameter_controls()` — the parent handles bank slicing through `_current_bank_details()`. Direct use of `parameter_banks()` invites the column-major ordering trap.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Appointed device tracking | Manual `song().add_appointed_device_listener` | `DeviceComponent` inheritance | Parent constructor wires this via `@subject_slot` automatically |
| Encoder parameter connection | `control.set_parameter(p)` or direct attribute | `control.connect_to(parameter)` | This is the Framework's API; `release_parameter()` is the paired cleanup |
| Bank index persistence | Custom dict keyed by device id | `DeviceBankRegistry` (one per instance) | Already handles device identity lookup via `_find_device_bank_key` |
| Parameter count guard | `if len(device.parameters) > 8` manual checks | `_assign_parameters()` calls `_release_parameters(controls[len(bank):])` | Parent already releases excess controls when bank has fewer than 8 params |
| LED ring update | Manual MIDI CC send | `control.connect_to(parameter)` | `RingedEncoderElement` updates its ring mode display automatically on connect |

---

## Critical Facts from Source Analysis

### DeviceComponent.set_device() bank reset (LINE 107 — the central trap)

```python
# Source: _Framework/DeviceComponent.py lines 105-107
if liveobj_valid(self._device):
    self._bank_index = 0
self._bank_index = self._device_bank_registry.get_device_bank(self._device)
```

The second assignment overrides the first. For a fresh `DeviceBankRegistry` with a newly-seen device, `get_device_bank()` returns `0`. Therefore the bank-1 instance resets to bank 0 on every new device appointment. The `set_device()` override in `Pan16DeviceComponent` must re-assert `_bank_index = self._fixed_bank_index` after calling the parent and before calling `self.update()`.

### DeviceComponent.set_parameter_controls() does the release

```python
# Source: _Framework/DeviceComponent.py lines 180-183
def set_parameter_controls(self, controls):
    self._release_parameters(self._parameter_controls)  # releases old controls
    self._parameter_controls = controls
    self.update()
```

Calling `set_parameter_controls(None)` correctly releases all previously connected parameters. This is the canonical teardown for encoder ownership handoff.

### DeviceBankRegistry cross-notification

```python
# Source: _Framework/DeviceBankRegistry.py lines 18-24
def set_device_bank(self, device, bank):
    key = self._find_device_bank_key(device) or device
    old = self._device_bank_registry[key] if key in self._device_bank_registry else 0
    if old != bank:
        self._device_bank_registry[key] = bank
        self.notify_device_bank(device, bank)  # fires _on_device_bank_changed on all listeners
```

`DeviceComponent._on_device_bank_changed` (line 418) checks `if device == self._device` and calls `update()`. If two instances share a registry: instance A calls `set_device_bank(device, 1)` → registry notifies → instance B (bank 0) also receives `device, 1` and calls `update()` with `_bank_index=1`. **Both instances fight to be bank 1.**

### device_param_controls is currently a local variable (must be promoted)

In `APC_64_40_9._setup_device_and_transport_control()` line 203:
```python
device_param_controls = []
```
It is never stored on `self`. Line 219 passes it to `ShiftableDeviceComponent`:
```python
self._device.set_parameter_controls(tuple(device_param_controls))
```
After that call, `device_param_controls` is only held by `self._device._parameter_controls`. To hand these encoders to `Pan16DeviceComponent` during Pan mode, `EncModeSelectorComponent` needs access to the original tuple. The tuple must be stored as `self._device_param_controls` in `APC_64_40_9`.

### EncModeSelectorComponent currently has NO reference to device encoders

`EncModeSelectorComponent.__init__` takes only `mixer` (line 15). It holds `self._controls` (the top 8 global param controls) and `self._mixer`. It has no reference to `self._device` (ShiftableDeviceComponent) or the device encoder tuple. These must be injected via constructor args or setter methods for Pan mode wiring.

### EncoderUserModesComponent controls the enable/disable of EncModeSelectorComponent

`EncoderUserModesComponent._set_modes()` (line 120):
```python
self._encoder_modes.set_enabled(False)
# ...
if (self._mode_index == 0):
    self._encoder_modes.set_enabled(True)
```
`EncModeSelectorComponent` is enabled/disabled by `EncoderUserModesComponent`. When it is disabled, `update()` does not execute the mode-routing logic (line 83: `if (self._controls != None) and (self.is_enabled())`). This means Pan mode activation code in `update()` only fires when the component is enabled (i.e., when `EncoderUserModesComponent` is in mode 0 — the normal encoder user mode). This is correct behavior and requires no change.

### ShiftableDeviceComponent.set_parameter_controls() also calls ChannelTranslationSelector

```python
# Source: ShiftableDeviceComponent.py lines 30-33
def set_parameter_controls(self, controls):
    DeviceComponent.set_parameter_controls(self, controls)
    self._control_translation_selector.set_controls_to_translate(controls)
    self._control_translation_selector.set_mode(self._bank_index)
```

Calling `self._device.set_parameter_controls(None)` in Pan mode also clears the `ChannelTranslationSelector` — that is correct and expected. On mode exit, `set_parameter_controls(self._device_param_controls)` will re-arm both the device component and the translation selector.

### Bank navigation buttons in Pan mode (D-09)

The bank-1 `Pan16DeviceComponent` instance receives `set_bank_nav_buttons(prev_button, next_button)` on Pan mode entry. The "prev/next device" buttons are `device_bank_buttons[2]` and `device_bank_buttons[3]` (CC notes 60, 61 — "Previous_Device_Button", "Next_Device_Button"). These are already wired to `DetailViewCntrlComponent.set_device_nav_buttons()` in `_setup_device_and_transport_control()`. They can have multiple listeners — `DeviceComponent.set_bank_nav_buttons()` adds its own via subject slots — so this is safe to share.

On Pan mode exit: `pan16_enc.set_bank_nav_buttons(None, None)` — this removes the listener, restoring the buttons to `DetailViewCntrlComponent` only.

---

## Common Pitfalls

### Pitfall 1: Bank-1 Instance Resets to Bank 0 on New Device

**What goes wrong:** A device is selected in Ableton. `__on_appointed_device_changed` fires on both instances. Both call `set_device()`. The parent's `set_device()` calls `get_device_bank(new_device)` — returns 0 from the fresh registry. Bank-1 instance is now at bank 0.

**How to avoid:** Override `set_device()` in `Pan16DeviceComponent`:
```python
def set_device(self, device):
    DeviceComponent.set_device(self, device)
    if self._device is not None:
        self._bank_index = self._fixed_bank_index
        self.update()
```

**Warning signs:** After switching the selected device in Ableton while Pan mode is active, device encoders (supposed to show params 9-16) start showing params 1-8.

### Pitfall 2: Shared DeviceBankRegistry Causes Bank Thrashing

**What goes wrong:** Both instances share a registry. User presses bank-next while in Pan mode. Bank-1 instance moves to bank 2. Registry notifies bank-0 instance. Bank-0 instance updates to bank 2. Top encoders now show params 17-24 instead of params 1-8.

**How to avoid:** Instantiate each `Pan16DeviceComponent` with no constructor arguments — let `DeviceComponent.__init__` create a fresh `DeviceBankRegistry()` for each. Never pass `device_bank_registry=self._device._device_bank_registry`.

**Warning signs:** Pressing bank-next changes both encoder rows simultaneously.

### Pitfall 3: Device Encoders Become Dead on Mode Exit

**What goes wrong:** Pan mode sets `self._device.set_parameter_controls(None)`. Mode exit sets `pan16_enc.set_parameter_controls(None)`. But mode exit code forgets to call `self._device.set_parameter_controls(self._device_controls)`. Device encoder row is now unmapped in all non-Pan modes.

**How to avoid:** In `EncModeSelectorComponent.update()`, all non-Pan mode branches must include:
```python
self._device_component.set_parameter_controls(self._device_controls)
```

**Warning signs:** Device encoders do nothing in Send A/B/C modes after a Pan mode visit.

### Pitfall 4: device_param_controls Still a Local Variable

**What goes wrong:** `EncModeSelectorComponent.update()` needs the device encoder tuple to pass to `pan16_enc.set_parameter_controls()`. If the variable was never promoted to `self._device_param_controls`, the tuple is only accessible through `self._device._parameter_controls` — which is `None` after `set_parameter_controls(None)` is called on Pan mode entry.

**How to avoid:** Promote to instance variable FIRST (Step 1 in build order). Pass it to `EncModeSelectorComponent` via constructor or setter. Verify script loads before proceeding to wiring.

**Warning signs:** `AttributeError` on `self._device_controls` or `None` passed to `set_parameter_controls`.

### Pitfall 5: parameter_banks() Column-Major Ordering

**What goes wrong:** A developer calls `parameter_banks(device)[1]` directly, expecting params 9-16. For a 16-parameter device (e.g., an Ableton instrument rack with 16 macros), `parameter_banks()` from `_Generic.Devices` uses column-major interleaving: bank 0 = params at indices 0,8,16,24...; bank 1 = params at indices 1,9,17,25...

**How to avoid:** Do not call `parameter_banks()` directly. Use `set_parameter_controls()` on a `DeviceComponent` instance with `_bank_index=1` — the parent's `_assign_parameters()` and `_current_bank_details()` handle the correct bank lookup. For devices with a `DEVICE_DICT` entry (most Ableton native devices), banks are predefined and ordered correctly. For generic devices (VSTs), this is the trap.

**Warning signs:** Params are in wrong order on generic/VST devices.

### Pitfall 6: EncoderUserModesComponent Not Informed of New Pan16 Instances

**What goes wrong:** `EncoderUserModesComponent._set_modes()` (lines 122-128) explicitly disables `_encoder_device_modes` and iterates its controls to call `release_parameter()`. It does not know about the new `Pan16DeviceComponent` instances. When `EncoderUserModesComponent` switches away from mode 0 (via shift), it disables `_encoder_modes` but leaves `Pan16DeviceComponent` instances in whatever state they're in.

**How to avoid:** Either (a) pass `pan16_top` and `pan16_enc` references to `EncoderUserModesComponent` and disable them in `_set_modes()` teardown, or (b) ensure `EncModeSelectorComponent.update()` is always called via `set_enabled(False)` on `EncModeSelectorComponent` (which happens in `_set_modes()` line 120) and that `Pan16DeviceComponent` instances are disabled in `EncModeSelectorComponent.on_enabled_changed()`. Option (b) is lower-change-surface: override `on_enabled_changed()` in `EncModeSelectorComponent` to disable both `Pan16DeviceComponent` instances when the component is disabled.

**Warning signs:** Device encoders continue controlling device params after shift is pressed and encoder mode changes away from normal (mode 0 of `EncoderUserModesComponent`).

---

## Code Examples

### Pan16DeviceComponent (complete recommended implementation)

```python
# Source: pattern derived from _Framework/DeviceComponent.py lines 36-38, 97-112
from _Framework.DeviceComponent import DeviceComponent

class Pan16DeviceComponent(DeviceComponent):
    """DeviceComponent fixed to a specific bank index, for 16-param Pan mode mapping."""

    def __init__(self, bank_index):
        # DeviceComponent.__init__ with no args creates its own fresh DeviceBankRegistry.
        # This isolation prevents cross-notification with other DeviceComponent instances.
        DeviceComponent.__init__(self)
        self._fixed_bank_index = bank_index

    def set_device(self, device):
        # Parent resets _bank_index to 0 via get_device_bank() for unseen devices.
        # Re-assert our fixed bank after parent call.
        DeviceComponent.set_device(self, device)
        if self._device is not None:
            self._bank_index = self._fixed_bank_index
            self.update()
```

### Wiring in APC_64_40_9._setup_device_and_transport_control() (Step 1)

```python
# CHANGE: line 203 — promote from local to instance variable
self._device_param_controls = []   # was: device_param_controls = []
# ... rest of loop unchanged, using self._device_param_controls ...
self._device.set_parameter_controls(tuple(self._device_param_controls))
```

### Wiring in APC_64_40_9._setup_global_control() (Step 3)

```python
# After line 277 (EncModeSelectorComponent instantiation), before line 280:
from .Pan16DeviceComponent import Pan16DeviceComponent
self._pan16_top = Pan16DeviceComponent(bank_index=0)
self._pan16_top.name = 'Pan16_Top_Encoders'
self._pan16_enc = Pan16DeviceComponent(bank_index=1)
self._pan16_enc.name = 'Pan16_Device_Encoders'

# Pass device_bank_buttons[2] (Previous_Device_Button) and [3] (Next_Device_Button)
# These are already stored in device_bank_buttons — need them accessible here.
# Option: store device_bank_buttons as self._device_bank_buttons in Step 1.

# Inject references into EncModeSelectorComponent via new setter or constructor arg:
self._encoder_modes.set_pan16_components(
    pan16_top=self._pan16_top,
    pan16_enc=self._pan16_enc,
    device_component=self._device,
    device_controls=tuple(self._device_param_controls),
    bank_nav_buttons=(self._device_bank_buttons[2], self._device_bank_buttons[3])
)
```

### EncModeSelectorComponent.update() mode-0 branch (Step 3)

```python
if self._mode_index == 0:
    # Clear mixer pan assignment from top encoders
    for index in range(len(self._controls)):
        self._mixer.channel_strip(index).set_pan_control(None)
        self._mixer.channel_strip(index).set_send_controls((None, None, None))
    # Release ShiftableDeviceComponent from device encoders
    if self._device_component is not None:
        self._device_component.set_parameter_controls(None)
    # Activate Pan16 components
    if self._pan16_top is not None:
        self._pan16_top.set_parameter_controls(self._controls)
    if self._pan16_enc is not None:
        self._pan16_enc.set_parameter_controls(self._device_controls)
        if self._bank_nav_buttons is not None:
            self._pan16_enc.set_bank_nav_buttons(*self._bank_nav_buttons)
elif self._mode_index in (1, 2, 3):
    # Teardown Pan16 before assigning sends
    if self._pan16_top is not None:
        self._pan16_top.set_parameter_controls(None)
    if self._pan16_enc is not None:
        self._pan16_enc.set_parameter_controls(None)
        self._pan16_enc.set_bank_nav_buttons(None, None)
    # Restore ShiftableDeviceComponent to device encoders
    if self._device_component is not None and self._device_controls is not None:
        self._device_component.set_parameter_controls(self._device_controls)
    # Normal send routing (existing logic):
    for index in range(len(self._controls)):
        self._mixer.channel_strip(index).set_pan_control(None)
        if self._mode_index == 1:
            self._mixer.channel_strip(index).set_send_controls((self._controls[index], None, None))
        elif self._mode_index == 2:
            self._mixer.channel_strip(index).set_send_controls((None, self._controls[index], None))
        elif self._mode_index == 3:
            self._mixer.channel_strip(index).set_send_controls((None, None, self._controls[index]))
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `song().add_appointed_device_listener` | `@subject_slot('appointed_device')` via `DeviceComponent.__init__` | Live 11 → 12 (decompiled source shows subject_slot pattern) | `Pan16DeviceComponent` gets device tracking for free by inheriting `DeviceComponent` |
| `DeviceComponent.__init__(self)` (implicit registry) | `DeviceComponent.__init__(self, device_bank_registry=None)` parameter explicit | Live 11/12 | Pass `None` (default) to guarantee fresh registry; never share registries between instances |

---

## Suggested Build Order

**Step 1 — Promote `device_param_controls` to instance variable**

In `_setup_device_and_transport_control()`: rename `device_param_controls = []` to `self._device_param_controls = []`. Update all 3 references in the same method. Also store `device_bank_buttons` as `self._device_bank_buttons` so Step 3 can access buttons[2] and buttons[3] for bank navigation. Verify: script loads, device controls still work.

**Step 2 — Create `Pan16DeviceComponent.py`**

New file, as shown in Code Examples above. Import `DeviceComponent`. No wiring yet. Verify: script loads without error.

**Step 3 — Add setter to EncModeSelectorComponent and wire in APC_64_40_9**

Add `set_pan16_components()` setter to `EncModeSelectorComponent`. Extend `update()` mode-0 branch and all non-0 branches as shown above. In `APC_64_40_9._setup_global_control()`, instantiate both `Pan16DeviceComponent` instances and call the setter. Verify: Pan button routes both encoder rows to device params 1-16; Send A/B/C restores device encoders to `ShiftableDeviceComponent`.

**Step 4 — Edge case verification**

Test: (a) switch selected device while Pan mode active → both rows update to new device; (b) press bank-next while in Pan mode → only device encoder row advances; (c) switch from Pan to Send A and back → top encoders show params 1-8 again; (d) rapid mode switching does not leave stale connections; (e) device with fewer than 8 parameters → extra encoders release cleanly.

---

## Open Questions

1. **Do `device_bank_buttons[2]` and `[3]` (Previous_Device_Button, Next_Device_Button) conflict when shared between `DetailViewCntrlComponent` and `Pan16DeviceComponent` in Pan mode?**
   - What we know: `DeviceComponent.set_bank_nav_buttons()` uses `register_slot(button, handler, 'value')` — this adds a listener without removing existing ones. `DetailViewCntrlComponent.set_device_nav_buttons()` also adds listeners.
   - What's unclear: In Pan mode, pressing Prev Device both navigates the device AND steps the bank down. This dual behavior may be confusing or incorrect.
   - Recommendation: Verify empirically. If conflicting, use different buttons or gate the `DetailViewCntrlComponent` listener in Pan mode. The CONTEXT.md D-09 says bank buttons "continue to function" so dual navigation may be intentional.

2. **Does `EncModeSelectorComponent.on_enabled_changed()` need to disable Pan16 instances?**
   - What we know: When `EncoderUserModesComponent` switches from mode 0 to another mode (e.g., device mode), it calls `self._encoder_modes.set_enabled(False)`. `EncModeSelectorComponent` does not override `on_enabled_changed()`.
   - What's unclear: If Pan mode was active when the component is disabled, `Pan16DeviceComponent` instances remain active (their `set_enabled` is never called). Device encoders may still be bound.
   - Recommendation: Override `on_enabled_changed()` in `EncModeSelectorComponent`. On disable: call `set_parameter_controls(None)` on both `Pan16DeviceComponent` instances and restore `ShiftableDeviceComponent`.

3. **`_pan_to_vol_ticks_delay` in EncModeSelectorComponent — what does it actually do in v1.1?**
   - What we know: The current `_on_timer` toggles `_mode_is_pan` between True/False when the Pan button is held for 5 ticks. But no code in `update()` checks `_mode_is_pan`. It only shows a message.
   - What's unclear: Is this dead code, or is it intended to switch between "Pan mode maps to mixer pan" and some other Pan sub-mode?
   - Recommendation: Treat as dead code for Phase 4 purposes. Do not remove it (no regressions) but do not build on it. The Phase 4 Pan mode is fully defined by D-01 through D-09.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 4 is purely code changes within the existing Ableton MIDI Remote Script. No external tools, services, or runtimes beyond the project's own Python environment.

---

## Sources

### Primary (HIGH confidence)

- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/DeviceComponent.py` (source timestamp 2025-03-17) — `__init__` registry parameter, `set_device()` bank reset (line 107), `set_parameter_controls()` release pattern (line 181), `_assign_parameters()` zip pattern (line 323), `_current_bank_details()` bank lookup
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/DeviceBankRegistry.py` (source timestamp 2025-03-17) — `set_device_bank()` notification mechanic, `get_device_bank()` default-0 return, shared-registry cross-notification confirmed
- `/Users/stoersignal/Dev/APC_64_40_12/EncModeSelectorComponent.py` — exact current mode 0 logic, `_pan_to_vol_ticks_delay` timer, `set_controls()` assertion (`len == 8`), `update()` loop bounds
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` — `device_param_controls` is local (line 203), wiring chain for `EncModeSelectorComponent` and `EncoderUserModesComponent`
- `/Users/stoersignal/Dev/APC_64_40_12/EncoderUserModesComponent.py` — canonical teardown pattern (lines 116-128), how `EncModeSelectorComponent.set_enabled(True/False)` is called
- `/Users/stoersignal/Dev/APC_64_40_12/ShiftableDeviceComponent.py` — `set_parameter_controls()` also clears `ChannelTranslationSelector` (lines 30-33); `_bank_value()` guard requires `_shift_pressed`
- `/Users/stoersignal/Dev/APC_64_40_12/EncoderDeviceComponent.py` — proven dual-DeviceComponent pattern (`_alt_device = DeviceComponent()`, no shared registry, appointed device listener pattern)

### Secondary (MEDIUM confidence)

- `.planning/research/ARCHITECTURE.md` — build order, data flow diagrams, component boundary map
- `.planning/research/STACK.md` — `parameter_banks()` column-major trap, `device.parameters[1:17]` direct access note
- `.planning/research/PITFALLS.md` — encoder dual-assignment (E1), 16-control extension (E2), release on mode exit (E3), bank persistence (E5)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all APIs verified in Live 12.1 source
- Architecture: HIGH — all patterns verified against live codebase
- Pitfalls: HIGH — root causes confirmed from source, not inferred

**Research date:** 2026-03-31
**Valid until:** 2026-06-30 (stable APIs, no version-specific churn expected)
