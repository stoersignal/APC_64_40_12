# Codebase Structure

**Analysis Date:** 2026-03-31

## Directory Layout

```
APC_64_40_12/
├── __init__.py                          # Script entry point, factory method, capabilities
├── APC.py                               # Base ControlSurface class with MIDI handshake
├── APC_64_40_9.py                       # Main composition, component instantiation
├── README.md                            # Installation and usage documentation
├── APC_64_40_quickstart_guide_rev_1.pdf # Visual guide to mappings
├── __pycache__/                         # Generated Python bytecode
├── .planning/                           # GSD planning documentation
│   └── codebase/                        # This analysis
│
├── Session & Grid Control:
│   ├── APCSessionComponent.py           # Extended SessionComponent with track offset support
│   ├── PedaledSessionComponent.py       # SessionComponent variant with pedal clip firing
│   ├── ShiftableZoomingComponent.py     # Session zooming with shift mode support
│   └── StepSequencerComponent.py        # 64-step sequencer on 8x5 grid
│
├── Mixer & Channels:
│   ├── SpecialMixerComponent.py         # MixerComponent that includes return tracks
│   └── SpecialChanStripComponent.py     # Channel strip with extra device controls
│
├── Device & Parameter Control:
│   ├── ShiftableDeviceComponent.py      # Device parameter selection with shift modes
│   ├── EncoderDeviceComponent.py        # Encoder mode for device parameters
│   ├── EncoderEQComponent.py            # Encoder mode for EQ device parameters
│   ├── EncModeSelectorComponent.py      # Mode selector for encoder global controls (Pan/Send)
│   ├── RingedEncoderElement.py          # Custom encoder with LED ring visualization
│   └── Matrix_Maps.py                   # Mapping constants for sequencer/matrix
│
├── Transport & Global Control:
│   ├── ShiftableTransportComponent.py   # Transport (play/stop/record) with shift modes
│   ├── CustomTransportComponent.py      # Extended transport component
│   ├── DetailViewCntrlComponent.py      # Toggle device/clip detail view
│   ├── ShiftTranslatorComponent.py      # Re-translate button meanings under shift
│   ├── EncoderUserModesComponent.py     # User-defined encoder mode selector
│   └── ShiftableEncoderSelectorComponent.py # Shift-aware encoder mode switching
│
├── UI Elements:
│   ├── ConfigurableButtonElement.py     # Button with configurable behavior
│   └── (Framework classes: ButtonElement, SliderElement, EncoderElement)
│
├── Mode & Control Management:
│   ├── ShiftableSelectorComponent.py    # Main shift mode orchestrator for all controls
│   ├── MatrixModesComponent.py          # Matrix layout selector (session/sequencer/zoom)
│   └── SliderModesComponent.py          # Slider behavior mode selector
│
└── Data & Documentation:
    └── APC_64_40_9.py                   # Historical version (alternate name)
```

## Directory Purposes

**Root Directory:**
- Purpose: Contains all script files and direct Ableton Live Framework integration
- Contains: Component classes, element classes, configuration, documentation
- Key files: `__init__.py`, `APC.py`, `APC_64_40_9.py`

**Session & Grid Control:**
- Purpose: Manage clip launching, scene navigation, step sequencer functionality
- Contains: Components that control the 8x5 button matrix and scene buttons
- Key files: `PedaledSessionComponent.py` (clip firing), `StepSequencerComponent.py` (note editing)

**Mixer & Channels:**
- Purpose: Volume, mute, solo, arm controls for tracks and return tracks
- Contains: Specialized mixer component that includes return tracks alongside regular tracks
- Key files: `SpecialMixerComponent.py` (mixer with returns), `SpecialChanStripComponent.py` (per-track controls)

**Device & Parameter Control:**
- Purpose: Map 8 rotary encoders to device parameters with visual feedback
- Contains: Components for selecting devices, parameter pages, and EQ controls
- Key files: `RingedEncoderElement.py` (encoder with LED ring), `EncoderEQComponent.py` (EQ mode)

**Transport & Global Control:**
- Purpose: Play/stop/record buttons, quantization, metronome, tempo, detail view toggling
- Contains: Transport controls and global encoder mode selectors
- Key files: `ShiftableTransportComponent.py` (transport with shift variants)

**UI Elements:**
- Purpose: Hardware input abstraction (buttons, sliders, encoders)
- Contains: Custom elements extending Framework classes
- Key files: `ConfigurableButtonElement.py`, `RingedEncoderElement.py`

**Mode & Control Management:**
- Purpose: Context-sensitive control routing and mode switching
- Contains: Components that change button/control meanings based on shift state or user selection
- Key files: `ShiftableSelectorComponent.py` (main orchestrator), `MatrixModesComponent.py` (grid layouts)

## Key File Locations

**Entry Points:**
- `__init__.py`: Factory method `create_instance(c_instance)` returns `APC_64_40_9(c_instance)` instance
- `APC.py`: Base `ControlSurface` class; `handle_sysex()` receives hardware handshake
- `APC_64_40_9.py`: Main implementation with three setup methods called during init

**Configuration:**
- `APC.py` lines 7-8: Manufacturer ID (71) and Ableton mode constants
- `RingedEncoderElement.py` lines 8-11: Ring visualization mode constants (OFF, SIN, VOL, PAN)
- `StepSequencerComponent.py` lines 29-37: Color and step constants (OFF, GREEN, RED, YELLOW)
- `Matrix_Maps.py`: Mapping constants for sequencer/matrix layout

**Core Logic:**
- `APC.py`: MIDI handshake, hardware initialization, component enabling/disabling
- `APC_64_40_9.py`: Component instantiation and wiring (700+ lines)
  - Lines 72-132: Session control setup (matrix, scene buttons, track nav)
  - Lines 134-195: Mixer control and mode selector setup
  - Lines 200-258: Device and transport control setup
  - Lines 260-293: Global encoder modes setup

**Components (Functional Units):**
- `PedaledSessionComponent.py`: Clip grid + pedal (22 lines) - simple extension
- `StepSequencerComponent.py`: Step sequencer logic (400+ lines) - complex state management
- `SpecialMixerComponent.py`: Mixer with returns (50 lines) - specialized container
- `RingedEncoderElement.py`: Encoder with LED ring (81 lines) - UI enhancement
- `ShiftableSelectorComponent.py`: Shift mode orchestrator (200+ lines) - complex wiring

**Testing:**
- No tests present - Ableton Live script verification is manual through Live GUI

## Naming Conventions

**Files:**
- CamelCase for component classes: `ShiftableDeviceComponent.py`, `PedaledSessionComponent.py`
- Capital first letter for class names: `class APC(ControlSurface)`, `class EncModeSelectorComponent`
- Snake_case for utility/data files: `Matrix_Maps.py`

**Directories:**
- All files in root directory (no subdirectories) - flat structure for Ableton script directory requirement
- Grouped logically by function in this documentation, but physically all files coexist

**Classes:**
- CamelCase with descriptive suffixes: `*Component`, `*Element`, `*Selector`, `*Translator`
- Base names describe function: `Device`, `Mixer`, `Transport`, `Session`, `Encoder`
- Shift variants: `Shiftable*Component` (e.g., `ShiftableDeviceComponent`)
- Special variants: `Special*Component`, `Pedaled*Component`, `Ringed*Element`

**Methods:**
- Private methods: Leading underscore `_setup_session_control()`, `_on_handshake_successful()`
- Event handlers: `_*_value()` pattern for MIDI listeners: `_shift_value()`, `_mode_value()`
- Setup/configuration: `set_*()` pattern: `set_mode()`, `set_controls()`, `set_shift_button()`
- State queries: `is_*()` or `*_to_use()`: `is_enabled()`, `tracks_to_use()`

**Variables:**
- Private state: Leading underscore `_mixer`, `_session`, `_shift_pressed`, `_mode_index`
- Button/control collections: Plural names `_scene_launch_buttons`, `_track_stop_buttons`
- Mode flags: Boolean prefixes `_is_locked`, `_device_selection_follows_track_selection`
- Indices: `_index`, `_offset` suffixes: `_bank_index`, `_velocity_index`

## Where to Add New Code

**New Feature (e.g., new encoder mode):**
- Primary code: Create `NewModeComponent.py` extending `ModeSelectorComponent` in root directory
  - Pattern: `class NewModeComponent(ModeSelectorComponent)` with `__init__`, `disconnect`, `set_controls()`, `_mode_value()` methods
- Integration: Import in `APC_64_40_9.py` and instantiate in `_setup_global_control()` or similar
- Wiring: Add to `ShiftableSelectorComponent` if it needs shift support

**New Component/Module:**
- Implementation: Create `DescriptiveNameComponent.py` in root directory
  - Extend appropriate Framework base: `ControlSurfaceComponent`, `Component`, `ModeSelectorComponent`
  - Implement `__init__()`, `disconnect()`, setter methods for controls, listener methods
- Button/Control setup: Define MIDI controls (channel, CC/note) in parent component (e.g., `APC_64_40_9.py`)
- Pattern: Follow existing component patterns in same directory

**Utilities & Helpers:**
- Shared helpers: Create `Helper.py` in root directory (flat structure required by Ableton)
- Data/Constants: Add to `Matrix_Maps.py` or create new file like `Config.py`
- Extend existing elements: Modify `RingedEncoderElement.py` or `ConfigurableButtonElement.py`

**Component Overrides:**
- Extend existing component: Create subclass in new file, import in `APC_64_40_9.py`
- Example: `SpecialMixerComponent` extends `MixerComponent` by overriding `_create_strip()`
- Must maintain same interface (same `__init__` signature, required methods)

## Special Directories

**`.planning/codebase/`:**
- Purpose: GSD (GitHub Smart Deploy) codebase documentation
- Generated: Yes (created by mapping command)
- Committed: Yes (aids in future planning phases)

**`__pycache__/`:**
- Purpose: Python compiled bytecode
- Generated: Yes (Python 3 generates automatically)
- Committed: No (should be in .gitignore)

## Component Dependency Graph

```
__init__.py
└── APC_64_40_9(APC)
    ├── [Session Controls]
    │   ├── PedaledSessionComponent(APCSessionComponent)
    │   │   └── APCSessionComponent(SessionComponent)
    │   ├── ShiftableZoomingComponent(SessionZoomingComponent)
    │   └── StepSequencerComponent(ControlSurfaceComponent)
    │
    ├── [Mixer Controls]
    │   ├── SpecialMixerComponent(MixerComponent)
    │   │   └── SpecialChanStripComponent(ChannelStripComponent)
    │   └── SliderModesComponent(ModeSelectorComponent)
    │
    ├── [Device & Parameters]
    │   ├── ShiftableDeviceComponent(DeviceComponent)
    │   ├── EncoderDeviceComponent(ControlSurfaceComponent)
    │   ├── EncoderEQComponent(ControlSurfaceComponent)
    │   ├── EncModeSelectorComponent(ModeSelectorComponent)
    │   ├── RingedEncoderElement(EncoderElement)
    │   └── EncoderUserModesComponent(ControlSurfaceComponent)
    │
    ├── [Transport & Detail View]
    │   ├── ShiftableTransportComponent(CustomTransportComponent)
    │   │   └── CustomTransportComponent(ControlSurfaceComponent)
    │   ├── DetailViewCntrlComponent(ControlSurfaceComponent)
    │   └── ShiftTranslatorComponent(ChannelTranslationSelector)
    │
    ├── [Mode Management]
    │   ├── ShiftableSelectorComponent(ModeSelectorComponent) - Orchestrates all modes
    │   ├── MatrixModesComponent(ModeSelectorComponent)
    │   └── ShiftableEncoderSelectorComponent(ModeSelectorComponent)
    │
    └── [UI Elements]
        ├── ConfigurableButtonElement(ButtonElement)
        └── RingedEncoderElement(EncoderElement)
```

## File Sizes & Complexity

**Largest Files (main logic):**
- `APC_64_40_9.py` (~700 lines) - Main composition and setup
- `StepSequencerComponent.py` (~600+ lines) - Complex sequencer state machine
- `EncoderEQComponent.py` (~400+ lines) - EQ mode controller
- `ShiftableSelectorComponent.py` (~200+ lines) - Mode orchestrator
- `CustomTransportComponent.py` (~400+ lines) - Transport logic

**Small/Focused Files (extensions/utilities):**
- `APCSessionComponent.py` (24 lines) - Simple SessionComponent wrapper
- `PedaledSessionComponent.py` (39 lines) - Adds pedal button support
- `RingedEncoderElement.py` (81 lines) - Encoder extension with ring feedback
- `ConfigurableButtonElement.py` (~50 lines) - Button extension
- `Matrix_Maps.py` (~200+ lines) - Constants and mappings

---

*Structure analysis: 2026-03-31*
