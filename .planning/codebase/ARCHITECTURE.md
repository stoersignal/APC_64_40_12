# Architecture

**Analysis Date:** 2026-03-31

## Pattern Overview

**Overall:** Hierarchical Component-Based Control Surface Framework

This is a MIDI control surface script for Ableton Live that extends the Ableton `_Framework` library. The architecture follows a component-based pattern where specialized components manage different aspects of the APC40 controller hardware interaction.

**Key Characteristics:**
- Extends Ableton's `ControlSurface` base class from `_Framework`
- Component hierarchy with base class inheritance (APC → APC_64_40_9)
- Mode selection pattern for contextual button/control reassignment
- Shiftable components that change behavior when shift button is held
- Real-time MIDI message handling and hardware synchronization
- Device parameter mapping with visual feedback (LED rings)

## Layers

**Hardware Control Layer:**
- Purpose: Direct MIDI communication with APC40 controller
- Location: `APC.py`
- Contains: Base ControlSurface class with MIDI send/receive, handshake protocols, hardware initialization
- Depends on: Ableton Live API (`Live` module), `_Framework.ControlSurface`
- Used by: APC_64_40_9 (main implementation)

**Composition Layer:**
- Purpose: Assemble and wire together functional components
- Location: `APC_64_40_9.py`
- Contains: Instantiation and configuration of all sub-components, button/control assignments, component interconnections
- Depends on: APC base class, all custom components, Ableton Framework components
- Used by: `__init__.py` (entry point factory)

**Component Layer:**
- Purpose: Encapsulate specific control functionality (session, mixer, device, transport, etc.)
- Location: Individual component files (`*Component.py`)
- Contains: Session control, mixer management, device parameter mapping, transport controls, step sequencer, zooming, encoder modes
- Depends on: Framework components, other custom components, Ableton Live API
- Used by: APC_64_40_9 composition layer

**UI Element Layer:**
- Purpose: Map hardware controls (buttons, sliders, encoders) to logical inputs
- Location: `RingedEncoderElement.py`, `ConfigurableButtonElement.py`, and Framework components
- Contains: Button elements, slider elements, encoder elements with custom LED ring support
- Depends on: Framework element classes (`ButtonElement`, `SliderElement`, `EncoderElement`)
- Used by: Components and composition layer

## Data Flow

**Initialization Flow:**

1. `__init__.py` → `create_instance()` instantiates `APC_64_40_9(c_instance)`
2. `APC_64_40_9.__init__()` calls parent `APC.__init__()`
3. `APC.__init__()` inside `component_guard()` calls setup methods:
   - `_setup_session_control()` - Creates session, buttons, matrix
   - `_setup_mixer_control()` - Creates mixer, sliders, creates all mode selectors
   - `_setup_custom_components()` - Calls:
     - `_setup_device_and_transport_control()` - Device parameters, transport buttons
     - `_setup_global_control()` - Global encoders and modes
4. `_on_handshake_successful()` enables all components

**MIDI Input Flow:**

1. Hardware button/knob sends MIDI message
2. Mapped UI element (`ButtonElement`, `EncoderElement`, etc.) receives MIDI value
3. Element triggers registered listeners
4. Component listener method (e.g., `_mode_value()`) handles the change
5. Component updates internal state and triggers Ableton Live action
6. Live responds with parameter/state changes

**Mode Selection Flow:**

1. Shift button held down (MIDI_NOTE_TYPE, channel 0, note 98)
2. `ShiftableSelectorComponent` receives shift button press
3. Mode context changes (normal mode → shift mode)
4. Button/control reassignments activate (managed by `ModeSelectorComponent`)
5. Components' listeners re-route to shift-specific behaviors
6. When shift released, reverts to normal mode

**State Management:**

- Component state maintained in instance variables (e.g., `_mode_index` in mode selectors)
- Session state (track offset, scene offset) tracked in `PedaledSessionComponent`
- Device state (selected device, parameter page) tracked in `ShiftableDeviceComponent`
- Sequencer state (playing clip, notes, loop) tracked in `StepSequencerComponent`
- Application state from Ableton Live: `song()`, `track()`, `device()` references

## Key Abstractions

**SessionComponent Chain:**
- Purpose: Manage clip/scene launching, session navigation, grid visualization
- Examples: `PedaledSessionComponent` (extends `APCSessionComponent`), `ShiftableZoomingComponent`
- Pattern: Extends Framework's `SessionComponent`, adds pedal support and zoom features

**MixerComponent Specialization:**
- Purpose: Control track volume, mute, solo, arm recording
- Examples: `SpecialMixerComponent`, `SpecialChanStripComponent`
- Pattern: Extends Framework's `MixerComponent` and `ChannelStripComponent` to include return tracks

**Device/Parameter Control:**
- Purpose: Map 8 encoders to device parameters with visual feedback
- Examples: `ShiftableDeviceComponent`, `RingedEncoderElement`, `EncoderEQComponent`, `EncoderDeviceComponent`
- Pattern: Encoders with LED ring mode buttons, parameter bank switching via shift modes

**Mode Selectors (Shiftable Components):**
- Purpose: Context-dependent control reassignment
- Examples: `ShiftableSelectorComponent`, `ShiftableEncoderSelectorComponent`, `EncModeSelectorComponent`, `MatrixModesComponent`
- Pattern: Extend Framework's `ModeSelectorComponent`, toggle between modes with button or shift key

**Transport & Control:**
- Purpose: Play/stop/record, quantization, metronome, tempo
- Examples: `ShiftableTransportComponent`, `CustomTransportComponent`
- Pattern: Extend Framework's transport components with shift variants and encoder tempo control

**Step Sequencer:**
- Purpose: 64-step sequencer interface using the 8x5 clip grid
- Examples: `StepSequencerComponent`
- Pattern: Custom MIDI note editing with loop start/length controls, velocity control, lane muting

## Entry Points

**Script Entry:**
- Location: `__init__.py`
- Triggers: Ableton Live loads script when device is connected
- Responsibilities: Factory method `create_instance()` returns `APC_64_40_9` instance; `get_capabilities()` declares controller ID and MIDI ports

**Hardware Handshake:**
- Location: `APC.handle_sysex()`, `_on_identity_response()`, `_on_dongle_response()`, `_on_handshake_successful()`
- Triggers: Controller responds to identity and dongle challenge messages
- Responsibilities: Verify hardware identity, establish bidirectional communication, enable all components

**Main Composition:**
- Location: `APC_64_40_9.__init__()`, `_setup_session_control()`, `_setup_mixer_control()`, `_setup_custom_components()`
- Triggers: During initialization after parent `APC.__init__()` completes
- Responsibilities: Create all components, wire button/control mappings, establish component relationships

**Track Selection Changed:**
- Location: `_on_selected_track_changed()`
- Triggers: User selects different track in Ableton
- Responsibilities: Update device selection to follow track selection if enabled (`_device_selection_follows_track_selection`)

## Error Handling

**Strategy:** Assertion-based validation with exception suppression in initialization

**Patterns:**
- Assertions validate component types: `assert isinstance(mixer, MixerComponent)` (`EncModeSelectorComponent.py` line 16)
- Try/catch blocks around deprecated API calls: `_send_introduction_message()` tries new version API, falls back for Live 12+ (`APC.py` lines 128-136)
- Suppress MIDI sends during initialization: `_suppress_send_midi` flag prevents invalid state transitions (`APC.py` lines 36, 103-124)
- Component guard context manager: `with self.component_guard()` wraps initialization to prevent partial state (`APC.py` line 35)
- Graceful disconnection: `disconnect()` methods clean up listeners and references (`APC.py` lines 58-65, component files)

## Cross-Cutting Concerns

**Logging:**
- Uses Ableton's `log_message()` method for controller version reporting and debug messages (`APC.py` line 84)

**Validation:**
- Type assertions on button/control parameters: `assert isinstance(button, ButtonElement)` patterns throughout components
- Condition checks: `if self._device_to_control != None` guards parameter access

**Button/Control Routing:**
- Value listeners registered on all interactive elements: `button.add_value_listener(callback)`
- Listeners call handler methods that check enabled state: `if self.is_enabled()` (`PedaledSessionComponent.py` line 38)
- Shift button routing: Many components check `_shift_pressed` flag to change behavior

**MIDI Communication:**
- Hardware updates sent via `_send_midi(midi_bytes)`
- Session highlighting suppressed during initialization: `_suppress_session_highlight` flag
- Handshake protocol ensures version compatibility

---

*Architecture analysis: 2026-03-31*
