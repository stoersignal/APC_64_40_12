# External Integrations

**Analysis Date:** 2026-03-31

## Hardware Integration

**MIDI Controller:**
- Akai APC40 - Primary hardware interface
  - Vendor ID: 2536
  - Product ID: 115
  - Input: MIDI notes, control changes (CC), SysEx messages
  - Output: LED feedback, display updates via MIDI
  - Connection: USB/MIDI interface

**MIDI Specifications:**
- Notes and CC messages for button, encoder, and slider input
- SysEx protocol for device identification and version negotiation
- Supports multiple synchronized APC40 units (combine mode)

## Software APIs

**Ableton Live Python API:**
- Read access: Song state, tracks, clips, devices, mixer settings, transport state
- Write access: Track/device selection, clip launching, parameter automation
- Event system: Listeners for selection changes, clip changes, transport updates

**Framework Integration Points:**
- `_Framework.ControlSurface` - Main script integration point
- `_Framework.ControlSurfaceComponent` - Component lifecycle management
- `_Generic.Devices` - Device parameter mapping for Ableton's native instruments

## Device Control

**Native Ableton Instruments & Effects:**

**EQ Devices:**
- Eq8 (8-band EQ) - Parameter mapping via `EncoderEQComponent.py`
  - Mapped to 8 gains, 8 filter toggles
- FilterEQ3 (3-band EQ) - Parameter mapping
  - Mapped to LowGain, MidGain, HighGain
- Audio Effect Group Device - Macro mapping
  - Mapped to Macros 2-8

**Filter Devices:**
- AutoFilter - Frequency and Resonance parameters
- Operator - Filter Freq and Filter Res
- OriginalSimpler - Filter frequency control
- MultiSampler - Filter frequency control
- UltraAnalog - F1 Frequency and F1 Resonance
- StringStudio - Filter frequency and resonance
- Audio Effect Group Device - Macro 1 and Macro 2

**Implementation:**
- `EncoderEQComponent.py` - EQ and filter parameter mapping via encoders
- `EncoderDeviceComponent.py` - Generic device parameter control
- Device detection via `Live.Device.Device` class inspection

## Session & Transport Control

**Ableton Song Control:**
- Session navigation (track/scene selection)
- Clip launching and stopping
- Scene launching
- Transport control (play, stop, record, tempo, punch in/out)
- Metronome and overdub toggling
- Recording quantization control

**Implementation:**
- `PedaledSessionComponent.py` - Session grid control with footpedal support
- `CustomTransportComponent.py` - Transport control (tempo, nudge, tap)
- `ShiftableTransportComponent.py` - Shift-modifier based transport features

## Mixer Control

**Track & Channel Strip Control:**
- Fader control for track volumes
- Mute, solo, arm (record) buttons per track
- Device chain selection per track
- Send control (send levels and toggles)
- Pan and crossfader control

**Implementation:**
- `SpecialMixerComponent.py` - Custom mixer with special button handling
- `SpecialChanStripComponent.py` - Custom channel strip features
- Extends `_Framework.MixerComponent` and `_Framework.ChannelStripComponent`

## Detail View Navigation

**Device Detail Control:**
- Navigation between device parameters
- Visual detail view updates in Ableton
- Left/right navigation via `Live.Application.Application.View.NavDirection`

**Implementation:**
- `DetailViewCntrlComponent.py` - Detail view parameter navigation

## Step Sequencer

**MIDI Note Sequencing:**
- 64-step sequencer for MIDI note entry
- Note velocity control
- Pattern recording and playback

**Implementation:**
- `StepSequencerComponent.py` - Custom step sequencer with matrix-based note entry

## Encoder & Control Mapping

**Hardware Control Elements:**

**MIDI Input Mapping:**
- Button Matrix: 8x5 grid of buttons (40 clip launchers)
- Scene Launch Buttons: 5 buttons for scene triggering
- Track Stop Buttons: 8 buttons for clip stopping
- Navigation Buttons: Up/Down/Left/Right for banking
- Shift Button: Modifier key for alternate functions
- Encoders: 8 rotary encoders with relative/absolute modes
- Faders: Vertical faders for mixer control
- Prehear Control: Dedicated encoder for monitor mixing

**Mapping Modes:**
- Absolute mode (`Live.MidiMap.MapMode.absolute`) - Direct value mapping
- Relative mode (`Live.MidiMap.MapMode.relative_two_compliment`) - Incremental changes
- CC messages for encoders and continuous controls

**Implementation:**
- `RingedEncoderElement.py` - Visual feedback ring for encoder position
- `ConfigurableButtonElement.py` - Dynamic button behavior switching
- `EncoderUserModesComponent.py` - User-selectable encoder function modes
- `MatrixModesComponent.py` - Mode switching for clip matrix display

## Webhooks & Callbacks

**Not Applicable:**
- This is a MIDI control surface script with no web/network integration
- All communication is local MIDI protocol between hardware and Ableton Live
- No outgoing webhooks or remote API calls

## Environment Configuration

**Required Components:**
- Akai APC40 hardware connected via USB/MIDI
- Ableton Live 11+ installed with this script in MIDI Remote Scripts folder

**Optional Configuration:**
- Script runs in Ableton's sandbox with no external configuration files
- No credentials, API keys, or secrets required
- All configuration is hardcoded in Python files (MIDI channel/note mappings, parameter lists)

## Data Storage

**Not Applicable:**
- No database, file storage, or persistent data layer
- Script is stateless except for real-time runtime variables
- All state comes from Ableton Live's active song
- No caching layer beyond runtime memory

## Monitoring & Observability

**Logging:**
- Uses Ableton Live's built-in logging via `ControlSurface.log_message()`
- Messages appear in Ableton's preferences/log window
- Example: Version information logged on controller connection

**Debugging:**
- No error tracking, no external monitoring
- Errors logged to Ableton's internal log
- Manual testing against Live's UI

---

*Integration audit: 2026-03-31*
