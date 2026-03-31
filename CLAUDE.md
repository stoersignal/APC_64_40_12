<!-- GSD:project-start source:PROJECT.md -->
## Project

**APC40 Toggle/Momentary Button Behavior**

A modification to the APC40 MIDI control surface script for Ableton Live that adds dual-behavior (toggle/momentary) to Solo and Mute buttons. Short press toggles state on/off; long press (~400ms threshold) acts as momentary — activating on press-down and reverting on release.

**Core Value:** Solo and Mute buttons must feel responsive and predictable — short taps toggle, longer holds act momentary, with LED feedback always reflecting the current real-time state.

### Constraints

- **Runtime**: Must run within Ableton Live's embedded Python environment — no external packages
- **Framework**: Must use Ableton `_Framework` APIs for MIDI I/O and track state
- **Timing**: Press duration detection must be reliable within Live's MIDI processing loop
- **Compatibility**: Must not break existing button behaviors (shift-modified, etc.)
- **Hardware**: APC40 controller — fixed MIDI note/CC assignments
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3 - Entire codebase is Python 3, converted from Python 2 for Ableton Live 11+ compatibility
## Runtime
- Ableton Live 11+ (tested with versions 11 and 12)
- MIDI Remote Scripts Framework (bundled with Ableton Live)
- No external package manager (system-level Python modules only)
- No lockfile (no external dependencies beyond bundled framework)
## Frameworks
- Ableton Live Control Surface Framework (`_Framework.*`) - MIDI control surface scripting
- Generic Devices Framework (`_Generic.Devices.*`) - Hardware device abstraction
- `ButtonElement` - MIDI button input handling
- `EncoderElement` - MIDI encoder/knob input handling
- `SliderElement` - MIDI fader input handling
- `ButtonMatrixElement` - Grid-based button matrix support
## Key Dependencies
- Ableton Live API (`Live` module) - Provides access to Live application state, song data, tracks, devices
- Custom framework extensions built on top of Ableton's `_Framework`
## Configuration
- Akai APC40 controller (vendor_id=2536, product_id=115)
- MIDI ports: Input (notes, CC, script, remote), Output (script, remote)
- Supports multiple APC40 controllers with combine mode
- Runs within Ableton Live's sandboxed remote script environment
- No environment variables required
- No external configuration files
- No build process required
- Direct script deployment to Ableton's MIDI Remote Scripts directory
- On Windows: `C:\ProgramData\Ableton\Live [VERSION]\Resources\MIDI Remote Scripts`
- On macOS: `[Ableton.app]/Contents/App-Resources/MIDI Remote Scripts`
## Platform Requirements
- Python 3.x interpreter (tested with Python 3.11.2)
- Text editor or IDE (any Python-compatible editor)
- Ableton Live 11 or higher installed
- Ableton Live 11 or higher (tested through Live 12)
- Akai APC40 hardware controller connected via USB or MIDI
- Host operating system: Windows, macOS, or Linux (wherever Ableton Live runs)
## API Integrations
- Hardware communication via MIDI over USB/serial
- System Exclusive (SysEx) messages for device identification and handshaking
- MIDI notes and control change (CC) messages for control input/output
- Direct Python API to Ableton's internal state and controls
- Read/write access to tracks, clips, devices, mixer settings
- Real-time event listeners for track/device selection changes
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- PascalCase for class-based components: `ConfigurableButtonElement.py`, `ShiftableDeviceComponent.py`, `StepSequencerComponent.py`
- Descriptive names indicating component purpose and functionality
- Files typically contain a single class matching the filename
- PascalCase with full descriptive names: `TrackEQComponent`, `DetailViewCntrlComponent`, `ShiftableSelectorComponent`
- Suffix patterns for specialized components: `*Component` for control surface components, `*Element` for UI elements
- Descriptive abbreviations acceptable: `Cntrl` (Control), `Enc` (Encoder)
- snake_case for all methods: `_setup_session_control()`, `_update_hardware()`, `set_mixer()`
- Private methods prefixed with single underscore: `_on_identity_response()`, `_shift_value()`
- Callback methods prefixed with `_on_`: `_on_devices_changed()`, `_on_cut_changed()`, `_on_timer()`
- Setter methods use `set_` prefix: `set_mixer()`, `set_shift_button()`, `set_parameter_controls()`
- snake_case for all local and instance variables: `self._device_id`, `self._suppress_send_midi`, `track_offset`
- Private instance variables prefixed with underscore: `self._bank_index`, `self._shift_pressed`
- Constants in UPPER_CASE with underscore separation: `MANUFACTURER_ID`, `INITIAL_SCROLLING_DELAY`, `OFF`, `GREEN`, `RED_BLINK`
- Descriptive names for state variables: `self._is_linked()`, `self._is_enabled`, `self._shift_pressed`
- snake_case: `is_momentary`, `msg_type`, `channel`, `identifier`
- Boolean parameters prefixed with `is_` or descriptive: `is_momentary`, `identify_sender`
- Default parameter values shown explicitly: `optimized = None`, `force = False`
## Code Style
- No explicit linter/formatter detected; code follows Python 2/3 compatible style
- 4-space indentation (consistent throughout)
- Long method signatures broken across multiple lines when needed
- Dictionary/list literals formatted with clear structure
- Generally follows reasonable limits; some lines exceed 80 chars for readability
- Multi-line tuples and lists use trailing commas: `(self._track_stop_buttons)` pattern
- No blank lines between method definitions in some files
- Inconsistent spacing around operators in conditional assertions
- Method chains maintain spacing: `self.set_mixer(self._mixer)`
## Import Organization
- Relative imports use dot notation: `from .RingedEncoderElement import RingedEncoderElement`
- Underscore-prefixed framework paths indicate third-party: `_Framework.*`, `_Generic.*`
- Wildcard imports used selectively: `from _Generic.Devices import *`, `from _Framework.SessionComponent import SessionComponent`
- Docstrings use triple-quoted format for classes: `""" Script for Akai's line of APC Controllers """`
- File-level headers include URL and copyright information
- Emacs mode declarations at top: `# emacs-mode: -*- python-*-`
## Error Handling
- Assertion-based validation predominates: `raise AssertionError` with descriptive messages
- Type checking via assertions: `assert ((button == None) or (isinstance(button, ButtonElement)))`
- Conditional assertions for preconditions: `assert (track_offset >= 0)`
- Value range assertions: `assert (value in range(128))`
- Broad try-except blocks used for API compatibility fallbacks (see `APC.py` lines 11-14, 128-136)
- Pattern: Try newer API, catch `AttributeError`, fall back to defaults
- No specific exception types caught in most handlers; uses bare `except:` for compatibility
- Abstract messages for subclass requirements: `'Function _setup_session_control must be overridden by subclass'`
- Error messages passed directly to `AssertionError`
- Assertions validate object state before operations: `assert (self._shift_button != None)`
- Pre-condition checks at method entry: `if not (track == None or isinstance(track, Live.Track.Track)): raise AssertionError`
- Listener/callback state management checked: `if not self._is_notifying:` before adding listeners
## Logging
- Used for lifecycle messages and system events
- Example from `APC.py` line 84: `self.log_message(message)` for version information
- Log messages are informational, not for debugging
- No structured logging or log levels observed
## Comments
- Explain non-obvious control flow logic and workarounds
- Document decompiled code sources: `# Partial --== Decompile ==-- with fixes`
- Note API deprecation issues: `# Bypass the deprecated encrypt_challenge verification and enable directly`
- Mark temporary disabling: `##self._rebuild_callback()` (double-hash for disabled code)
- Brief explanations of why, not what
- Example: `# invert on/offs for follow, since stop_all_clips button has no LED...`
- Commented-out code preserved in files (not actively cleaned)
- Python docstrings use simple triple-quote format
- Class docstrings are single-line: `""" Special SessionComponent for the APC controllers' combination mode """`
- No parameter documentation observed; self-documenting parameter names preferred
- Include original blog/source reference: `# http://remotescripts.blogspot.com`
- Copyright and license information for significant files
- Encoding declaration: `# -*- coding: utf-8 -*-`
- Emacs mode indicator: `# emacs-mode: -*- python-*-`
## Function Design
- Methods typically 5-50 lines
- Larger methods (100+ lines) handle complex state management or configuration
- Example: `StepSequencerComponent._on_timer()` manages sequencer timing and updates
- Constructors receive minimal parameters; configuration via setter methods pattern
- Example: `__init__(self, parent, session, matrix, playing_position_buttons)`
- Boolean flags frequently used: `is_momentary`, `identify_sender=False`
- Optional parameters use `None` as default: `set_on_off_values(self, on_value, off_value)`
- Most methods return `None` (implicit or explicit)
- Some older code includes explicit `return None` statements (decompiled code style)
- Getters return values directly: `width()`, `height()`, `number_of_modes()`
- Setters don't return self; each setter call on separate line
- Pattern used for builder-style configuration:
## Module Design
- Main entry point defined as `create_instance()` in `__init__.py`
- Pattern: `def create_instance(c_instance): return APC_64_40_9(c_instance)`
- Capabilities exposed via `get_capabilities()` function using `_Framework.Capabilities`
- Single inheritance hierarchy from framework base classes
- Example: `class APC(ControlSurface):`, `class APC_64_40_9(APC):`
- Method overriding for specialization: `_setup_session_control()`, `_setup_mixer_control()`
- Abstract methods in base classes raise `AssertionError` requiring override
- Parent class initialization called explicitly: `ControlSurface.__init__(self, c_instance)`
- Configuration happens post-initialization via setter methods
- Component guard context manager used during setup: `with self.component_guard():`
- Explicit `disconnect()` methods for resource cleanup
- Pattern: Remove listeners, release parameters, null out references
- Called when component disabled or script unloaded
- Wildcard imports from `_Generic.Devices`: `from _Generic.Devices import *`
- Specific imports from framework: `from _Framework.ControlSurface import ControlSurface`
- No barrel exports observed in project files
## Specific Patterns
- Add listeners in setters: `self._shift_button.add_value_listener(self._shift_value)`
- Remove listeners in cleanup: `self._shift_button.remove_value_listener(self._shift_value)`
- Null check before remove: `if (self._shift_button != None): ...`
- Pending listener queue for safe re-entrance: `ConfigurableButtonElement._pending_listeners`
- Encoders/controls connected to device parameters: `self._gain_controls[index].connect_to(parameter)`
- Parameters released when disconnected: `control.release_parameter()`
- Dynamic parameter lookup by name: `get_parameter_by_name(self._device, gain_names[index])`
- Constants for MIDI types: `MIDI_NOTE_TYPE`, `MIDI_CC_TYPE`
- Message types indicated by constants: `ButtonElement(is_momentary, MIDI_NOTE_TYPE, channel, identifier)`
- SysEx handled separately: `handle_sysex(self, midi_bytes)` method
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Extends Ableton's `ControlSurface` base class from `_Framework`
- Component hierarchy with base class inheritance (APC → APC_64_40_9)
- Mode selection pattern for contextual button/control reassignment
- Shiftable components that change behavior when shift button is held
- Real-time MIDI message handling and hardware synchronization
- Device parameter mapping with visual feedback (LED rings)
## Layers
- Purpose: Direct MIDI communication with APC40 controller
- Location: `APC.py`
- Contains: Base ControlSurface class with MIDI send/receive, handshake protocols, hardware initialization
- Depends on: Ableton Live API (`Live` module), `_Framework.ControlSurface`
- Used by: APC_64_40_9 (main implementation)
- Purpose: Assemble and wire together functional components
- Location: `APC_64_40_9.py`
- Contains: Instantiation and configuration of all sub-components, button/control assignments, component interconnections
- Depends on: APC base class, all custom components, Ableton Framework components
- Used by: `__init__.py` (entry point factory)
- Purpose: Encapsulate specific control functionality (session, mixer, device, transport, etc.)
- Location: Individual component files (`*Component.py`)
- Contains: Session control, mixer management, device parameter mapping, transport controls, step sequencer, zooming, encoder modes
- Depends on: Framework components, other custom components, Ableton Live API
- Used by: APC_64_40_9 composition layer
- Purpose: Map hardware controls (buttons, sliders, encoders) to logical inputs
- Location: `RingedEncoderElement.py`, `ConfigurableButtonElement.py`, and Framework components
- Contains: Button elements, slider elements, encoder elements with custom LED ring support
- Depends on: Framework element classes (`ButtonElement`, `SliderElement`, `EncoderElement`)
- Used by: Components and composition layer
## Data Flow
- Component state maintained in instance variables (e.g., `_mode_index` in mode selectors)
- Session state (track offset, scene offset) tracked in `PedaledSessionComponent`
- Device state (selected device, parameter page) tracked in `ShiftableDeviceComponent`
- Sequencer state (playing clip, notes, loop) tracked in `StepSequencerComponent`
- Application state from Ableton Live: `song()`, `track()`, `device()` references
## Key Abstractions
- Purpose: Manage clip/scene launching, session navigation, grid visualization
- Examples: `PedaledSessionComponent` (extends `APCSessionComponent`), `ShiftableZoomingComponent`
- Pattern: Extends Framework's `SessionComponent`, adds pedal support and zoom features
- Purpose: Control track volume, mute, solo, arm recording
- Examples: `SpecialMixerComponent`, `SpecialChanStripComponent`
- Pattern: Extends Framework's `MixerComponent` and `ChannelStripComponent` to include return tracks
- Purpose: Map 8 encoders to device parameters with visual feedback
- Examples: `ShiftableDeviceComponent`, `RingedEncoderElement`, `EncoderEQComponent`, `EncoderDeviceComponent`
- Pattern: Encoders with LED ring mode buttons, parameter bank switching via shift modes
- Purpose: Context-dependent control reassignment
- Examples: `ShiftableSelectorComponent`, `ShiftableEncoderSelectorComponent`, `EncModeSelectorComponent`, `MatrixModesComponent`
- Pattern: Extend Framework's `ModeSelectorComponent`, toggle between modes with button or shift key
- Purpose: Play/stop/record, quantization, metronome, tempo
- Examples: `ShiftableTransportComponent`, `CustomTransportComponent`
- Pattern: Extend Framework's transport components with shift variants and encoder tempo control
- Purpose: 64-step sequencer interface using the 8x5 clip grid
- Examples: `StepSequencerComponent`
- Pattern: Custom MIDI note editing with loop start/length controls, velocity control, lane muting
## Entry Points
- Location: `__init__.py`
- Triggers: Ableton Live loads script when device is connected
- Responsibilities: Factory method `create_instance()` returns `APC_64_40_9` instance; `get_capabilities()` declares controller ID and MIDI ports
- Location: `APC.handle_sysex()`, `_on_identity_response()`, `_on_dongle_response()`, `_on_handshake_successful()`
- Triggers: Controller responds to identity and dongle challenge messages
- Responsibilities: Verify hardware identity, establish bidirectional communication, enable all components
- Location: `APC_64_40_9.__init__()`, `_setup_session_control()`, `_setup_mixer_control()`, `_setup_custom_components()`
- Triggers: During initialization after parent `APC.__init__()` completes
- Responsibilities: Create all components, wire button/control mappings, establish component relationships
- Location: `_on_selected_track_changed()`
- Triggers: User selects different track in Ableton
- Responsibilities: Update device selection to follow track selection if enabled (`_device_selection_follows_track_selection`)
## Error Handling
- Assertions validate component types: `assert isinstance(mixer, MixerComponent)` (`EncModeSelectorComponent.py` line 16)
- Try/catch blocks around deprecated API calls: `_send_introduction_message()` tries new version API, falls back for Live 12+ (`APC.py` lines 128-136)
- Suppress MIDI sends during initialization: `_suppress_send_midi` flag prevents invalid state transitions (`APC.py` lines 36, 103-124)
- Component guard context manager: `with self.component_guard()` wraps initialization to prevent partial state (`APC.py` line 35)
- Graceful disconnection: `disconnect()` methods clean up listeners and references (`APC.py` lines 58-65, component files)
## Cross-Cutting Concerns
- Uses Ableton's `log_message()` method for controller version reporting and debug messages (`APC.py` line 84)
- Type assertions on button/control parameters: `assert isinstance(button, ButtonElement)` patterns throughout components
- Condition checks: `if self._device_to_control != None` guards parameter access
- Value listeners registered on all interactive elements: `button.add_value_listener(callback)`
- Listeners call handler methods that check enabled state: `if self.is_enabled()` (`PedaledSessionComponent.py` line 38)
- Shift button routing: Many components check `_shift_pressed` flag to change behavior
- Hardware updates sent via `_send_midi(midi_bytes)`
- Session highlighting suppressed during initialization: `_suppress_session_highlight` flag
- Handshake protocol ensures version compatibility
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
