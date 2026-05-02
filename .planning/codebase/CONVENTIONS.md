# Coding Conventions

**Analysis Date:** 2026-03-31

## Naming Patterns

**Files:**
- PascalCase for class-based components: `ConfigurableButtonElement.py`, `ShiftableDeviceComponent.py`, `StepSequencerComponent.py`
- Descriptive names indicating component purpose and functionality
- Files typically contain a single class matching the filename

**Classes:**
- PascalCase with full descriptive names: `TrackEQComponent`, `DetailViewCntrlComponent`, `ShiftableSelectorComponent`
- Suffix patterns for specialized components: `*Component` for control surface components, `*Element` for UI elements
- Descriptive abbreviations acceptable: `Cntrl` (Control), `Enc` (Encoder)

**Functions/Methods:**
- snake_case for all methods: `_setup_session_control()`, `_update_hardware()`, `set_mixer()`
- Private methods prefixed with single underscore: `_on_identity_response()`, `_shift_value()`
- Callback methods prefixed with `_on_`: `_on_devices_changed()`, `_on_cut_changed()`, `_on_timer()`
- Setter methods use `set_` prefix: `set_mixer()`, `set_shift_button()`, `set_parameter_controls()`

**Variables:**
- snake_case for all local and instance variables: `self._device_id`, `self._suppress_send_midi`, `track_offset`
- Private instance variables prefixed with underscore: `self._bank_index`, `self._shift_pressed`
- Constants in UPPER_CASE with underscore separation: `MANUFACTURER_ID`, `INITIAL_SCROLLING_DELAY`, `OFF`, `GREEN`, `RED_BLINK`
- Descriptive names for state variables: `self._is_linked()`, `self._is_enabled`, `self._shift_pressed`

**Parameters:**
- snake_case: `is_momentary`, `msg_type`, `channel`, `identifier`
- Boolean parameters prefixed with `is_` or descriptive: `is_momentary`, `identify_sender`
- Default parameter values shown explicitly: `optimized = None`, `force = False`

## Code Style

**Formatting:**
- No explicit linter/formatter detected; code follows Python 2/3 compatible style
- 4-space indentation (consistent throughout)
- Long method signatures broken across multiple lines when needed
- Dictionary/list literals formatted with clear structure

**Line Length:**
- Generally follows reasonable limits; some lines exceed 80 chars for readability
- Multi-line tuples and lists use trailing commas: `(self._track_stop_buttons)` pattern

**Spacing:**
- No blank lines between method definitions in some files
- Inconsistent spacing around operators in conditional assertions
- Method chains maintain spacing: `self.set_mixer(self._mixer)`

## Import Organization

**Order (Observed Pattern):**
1. Built-in modules: `import Live`, `import random`
2. Framework imports: `from _Framework.ControlSurface import ControlSurface`
3. Generic/Generic imports: `from _Generic.Devices import *`
4. Relative imports from project: `from .APC import APC`, `from .ConfigurableButtonElement import ConfigurableButtonElement`

**Path Aliases:**
- Relative imports use dot notation: `from .RingedEncoderElement import RingedEncoderElement`
- Underscore-prefixed framework paths indicate third-party: `_Framework.*`, `_Generic.*`
- Wildcard imports used selectively: `from _Generic.Devices import *`, `from _Framework.SessionComponent import SessionComponent`

**Module Documentation:**
- Docstrings use triple-quoted format for classes: `""" Script for Akai's line of APC Controllers """`
- File-level headers include URL and copyright information
- Emacs mode declarations at top: `# emacs-mode: -*- python-*-`

## Error Handling

**Patterns:**
- Assertion-based validation predominates: `raise AssertionError` with descriptive messages
- Type checking via assertions: `assert ((button == None) or (isinstance(button, ButtonElement)))`
- Conditional assertions for preconditions: `assert (track_offset >= 0)`
- Value range assertions: `assert (value in range(128))`

**Bare Exception Handling:**
- Broad try-except blocks used for API compatibility fallbacks (see `APC.py` lines 11-14, 128-136)
- Pattern: Try newer API, catch `AttributeError`, fall back to defaults
- No specific exception types caught in most handlers; uses bare `except:` for compatibility

**Error Messages:**
- Abstract messages for subclass requirements: `'Function _setup_session_control must be overridden by subclass'`
- Error messages passed directly to `AssertionError`

**State Validation:**
- Assertions validate object state before operations: `assert (self._shift_button != None)`
- Pre-condition checks at method entry: `if not (track == None or isinstance(track, Live.Track.Track)): raise AssertionError`
- Listener/callback state management checked: `if not self._is_notifying:` before adding listeners

## Logging

**Framework:** Ableton Live built-in logging via `self.log_message()`

**Patterns:**
- Used for lifecycle messages and system events
- Example from `APC.py` line 84: `self.log_message(message)` for version information
- Log messages are informational, not for debugging
- No structured logging or log levels observed

## Comments

**When to Comment:**
- Explain non-obvious control flow logic and workarounds
- Document decompiled code sources: `# Partial --== Decompile ==-- with fixes`
- Note API deprecation issues: `# Bypass the deprecated encrypt_challenge verification and enable directly`
- Mark temporary disabling: `##self._rebuild_callback()` (double-hash for disabled code)

**Inline Comments:**
- Brief explanations of why, not what
- Example: `# invert on/offs for follow, since stop_all_clips button has no LED...`
- Commented-out code preserved in files (not actively cleaned)

**JSDoc/TSDoc:**
- Python docstrings use simple triple-quote format
- Class docstrings are single-line: `""" Special SessionComponent for the APC controllers' combination mode """`
- No parameter documentation observed; self-documenting parameter names preferred

**File Headers:**
- Include original blog/source reference: `# http://remotescripts.blogspot.com`
- Copyright and license information for significant files
- Encoding declaration: `# -*- coding: utf-8 -*-`
- Emacs mode indicator: `# emacs-mode: -*- python-*-`

## Function Design

**Size:**
- Methods typically 5-50 lines
- Larger methods (100+ lines) handle complex state management or configuration
- Example: `StepSequencerComponent._on_timer()` manages sequencer timing and updates

**Parameters:**
- Constructors receive minimal parameters; configuration via setter methods pattern
- Example: `__init__(self, parent, session, matrix, playing_position_buttons)`
- Boolean flags frequently used: `is_momentary`, `identify_sender=False`
- Optional parameters use `None` as default: `set_on_off_values(self, on_value, off_value)`

**Return Values:**
- Most methods return `None` (implicit or explicit)
- Some older code includes explicit `return None` statements (decompiled code style)
- Getters return values directly: `width()`, `height()`, `number_of_modes()`

**Method Chaining:**
- Setters don't return self; each setter call on separate line
- Pattern used for builder-style configuration:
  ```python
  self._shift_modes = ShiftableSelectorComponent(...)
  self._shift_modes.name = 'Shift_Modes'
  self._shift_modes.set_mode_toggle(self._shift_button)
  ```

## Module Design

**Exports:**
- Main entry point defined as `create_instance()` in `__init__.py`
- Pattern: `def create_instance(c_instance): return APC_64_40_9(c_instance)`
- Capabilities exposed via `get_capabilities()` function using `_Framework.Capabilities`

**Inheritance:**
- Single inheritance hierarchy from framework base classes
- Example: `class APC(ControlSurface):`, `class APC_64_40_9(APC):`
- Method overriding for specialization: `_setup_session_control()`, `_setup_mixer_control()`
- Abstract methods in base classes raise `AssertionError` requiring override

**Initialization:**
- Parent class initialization called explicitly: `ControlSurface.__init__(self, c_instance)`
- Configuration happens post-initialization via setter methods
- Component guard context manager used during setup: `with self.component_guard():`

**Cleanup:**
- Explicit `disconnect()` methods for resource cleanup
- Pattern: Remove listeners, release parameters, null out references
- Called when component disabled or script unloaded

**Barrel Files:**
- Wildcard imports from `_Generic.Devices`: `from _Generic.Devices import *`
- Specific imports from framework: `from _Framework.ControlSurface import ControlSurface`
- No barrel exports observed in project files

## Specific Patterns

**Listener Management:**
- Add listeners in setters: `self._shift_button.add_value_listener(self._shift_value)`
- Remove listeners in cleanup: `self._shift_button.remove_value_listener(self._shift_value)`
- Null check before remove: `if (self._shift_button != None): ...`
- Pending listener queue for safe re-entrance: `ConfigurableButtonElement._pending_listeners`

**Parameter Binding:**
- Encoders/controls connected to device parameters: `self._gain_controls[index].connect_to(parameter)`
- Parameters released when disconnected: `control.release_parameter()`
- Dynamic parameter lookup by name: `get_parameter_by_name(self._device, gain_names[index])`

**MIDI Configuration:**
- Constants for MIDI types: `MIDI_NOTE_TYPE`, `MIDI_CC_TYPE`
- Message types indicated by constants: `ButtonElement(is_momentary, MIDI_NOTE_TYPE, channel, identifier)`
- SysEx handled separately: `handle_sysex(self, midi_bytes)` method

---

*Convention analysis: 2026-03-31*
