# Technology Stack

**Analysis Date:** 2026-03-31

## Languages

**Primary:**
- Python 3 - Entire codebase is Python 3, converted from Python 2 for Ableton Live 11+ compatibility

## Runtime

**Environment:**
- Ableton Live 11+ (tested with versions 11 and 12)
- MIDI Remote Scripts Framework (bundled with Ableton Live)

**Package Manager:**
- No external package manager (system-level Python modules only)
- No lockfile (no external dependencies beyond bundled framework)

## Frameworks

**Core:**
- Ableton Live Control Surface Framework (`_Framework.*`) - MIDI control surface scripting
  - `ControlSurface` - Base class for all control surface scripts
  - `ControlSurfaceComponent` - Component-based architecture for modular functionality
  - Session, mixer, device, transport control components

**Device Support:**
- Generic Devices Framework (`_Generic.Devices.*`) - Hardware device abstraction
  - Used for mapping to Ableton's built-in devices (EQ, filters, effects)

**MIDI Framework:**
- `ButtonElement` - MIDI button input handling
- `EncoderElement` - MIDI encoder/knob input handling
- `SliderElement` - MIDI fader input handling
- `ButtonMatrixElement` - Grid-based button matrix support

## Key Dependencies

**Critical:**
- Ableton Live API (`Live` module) - Provides access to Live application state, song data, tracks, devices
  - Live.MidiMap - MIDI mapping modes (absolute, relative, two's complement)
  - Live.Application - Application-level features (APC combining, version detection)
  - Live.Track - Track data and operations
  - Live.Song - Song/project data, recording quantization settings

**Internal Components:**
- Custom framework extensions built on top of Ableton's `_Framework`
  - `RingedEncoderElement` (`RingedEncoderElement.py`) - Visual feedback encoder
  - `ConfigurableButtonElement` (`ConfigurableButtonElement.py`) - Dynamic button behavior
  - Device control components for EQ, filters, step sequencing
  - Transport and session control customizations

## Configuration

**Hardware:**
- Akai APC40 controller (vendor_id=2536, product_id=115)
- MIDI ports: Input (notes, CC, script, remote), Output (script, remote)
- Supports multiple APC40 controllers with combine mode

**Environment:**
- Runs within Ableton Live's sandboxed remote script environment
- No environment variables required
- No external configuration files

**Build:**
- No build process required
- Direct script deployment to Ableton's MIDI Remote Scripts directory
- On Windows: `C:\ProgramData\Ableton\Live [VERSION]\Resources\MIDI Remote Scripts`
- On macOS: `[Ableton.app]/Contents/App-Resources/MIDI Remote Scripts`

## Platform Requirements

**Development:**
- Python 3.x interpreter (tested with Python 3.11.2)
- Text editor or IDE (any Python-compatible editor)
- Ableton Live 11 or higher installed

**Production:**
- Ableton Live 11 or higher (tested through Live 12)
- Akai APC40 hardware controller connected via USB or MIDI
- Host operating system: Windows, macOS, or Linux (wherever Ableton Live runs)

## API Integrations

**MIDI Protocol:**
- Hardware communication via MIDI over USB/serial
- System Exclusive (SysEx) messages for device identification and handshaking
- MIDI notes and control change (CC) messages for control input/output

**Ableton Live Python API:**
- Direct Python API to Ableton's internal state and controls
- Read/write access to tracks, clips, devices, mixer settings
- Real-time event listeners for track/device selection changes

---

*Stack analysis: 2026-03-31*
