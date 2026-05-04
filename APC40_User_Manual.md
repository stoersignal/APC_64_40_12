# Akai APC40 Custom Script User Manual

Welcome to the comprehensive guide for the custom APC_64_40 script. This remote script significantly upgrades the default APC40 functionality to include features like an advanced Step Sequencer, Macro Variations, Toggle/Momentary Mute and Solo states, and a 16-Macro mode.

## 1. Global Navigation & Mode Selection

Almost every button on the APC40 has a secondary function accessible by holding the **SHIFT** button (located on the bottom right of the controller). 

### Transport Controls & Device Variations (v1.2)
The standard transport section has been completely repurposed to navigate and trigger Ableton Live 11+ Device Macro Variations (Snapshots).

* **Nudge -**: Selects the **Previous Variation** on the currently appointed device.
* **Nudge +**: Selects the **Next Variation** on the currently appointed device.
* **Tap Tempo**: **Launches (Recalls)** the currently selected Macro Variation.
* **Shift + Nudge -**: Locks control to the currently appointed device.
* **Shift + Tap Tempo (Tap)**: **Creates / Saves** a new Macro Variation.
* **Shift + Tap Tempo (Hold & Turn Encoders)**: Edits the Ramp/Morph Time for smoothly transitioning between variations.

---

## 2. Track & Device Control Modes

The encoders on the right side of the APC40 (Track Control and Device Control) can be switched into various powerful modes.

### Standard Modes
* **Track Control Knobs**: By default, these control Track Pan.
* **Device Control Knobs**: Control the first 8 Macros of the selected device.

### 16 Macros Mode (v1.1)
* **How to access**: Press the **PAN** button (under Track Controls).
* **Function**: This combines both the top 8 Track Encoders and the bottom 8 Device Encoders into one massive 16-parameter device control! Track Encoders control Macros 1-8, while Device Encoders control Macros 9-16.

### Alternate Device & EQ/Filter Smart Control
* **Shift + Send A**: Sets the top Track Control knobs to act as a *secondary* Device Control independent of the bottom ones.
* **Shift + Send B**: Engages **EQ/Filter Smart Control**. The Track Control knobs automatically map to AutoFilter cutoff/resonance, EQ8 bands, and Sends depending on what's in the track.

---

## 3. Matrix Modes (The Grid)

The 8x5 Clip Launch matrix can be transformed into completely different interfaces.

### Standard Clip Launch (Default)
The classic APC40 mode. Grid launches clips. 

### Step Sequencer Mode
* **How to access**: Hold **SHIFT** and press the **Master Track Select** button (bottom right of the Track Select row).
* **Function**: Turns the top 4 rows into a melodic step sequencer (Rows = Pitch, Columns = Time). The bottom row controls Quantization / Zoom levels.
* **Bank Select**: Use Shift + Bank Select arrows to navigate time and pitch.
* **Loop Controls**: Use the Track Select buttons to set Loop Start and Loop Length.

### Note Mode (Drum Rack)
* **How to access**: Hold **SHIFT** and press **Track Select 3**.
* **Function**: Converts the center 4x4 grid into static MIDI note triggers (Velocity 127, Channel 10), perfect for finger-drumming on Drum Racks.

### Variations Mode (Rack Macro Snapshots)
* **How to access**: Hold **SHIFT** and press the rightmost **Track Select** button (Track Select 8) to enter Matrix Mode 8 — now `Variations Mode` (replaces the former User/Note Mode 6).
* **Function**: Each of the 40 pads in the 5×8 clip grid maps to one variation slot on the **currently appointed Rack** (Drum Rack, MIDI Rack, Instrument Rack — anything with macros). Row-major: top-left = slot 0, bottom-right = slot 39.
  * **Green pad** — variation slot is stored.
  * **Red pad** — variation slot is currently selected.
  * **Off pad** — slot is empty (or no Rack appointed).
* **Trigger a variation**: Press the pad. Sets `selected_variation_index` and recalls instantly. (For ramped/morphed recall, use Tap Tempo as before — this mode is for fast pad triggering.)
* **Real-time LED refresh**: LEDs follow Live in real time — adding a new variation via **Shift + Tap Tempo** (or in Live's UI) lights up the next green pad immediately; switching the selected variation moves the red pad.
* **Store a new variation**: use the existing **Shift + Tap Tempo** binding (`ShiftableTransportComponent.py:158-176`). Variations Mode does not provide its own store button — the Track Stop row keeps its default clip-stop function in this mode.
* **Empty pads**: pressing a pad whose slot is not yet stored does nothing.
* **No Rack appointed / non-Rack device**: all pad LEDs off, pad presses are no-ops.

---

## 4. Fader Modes

By default, the 8 faders control Track Volume. You can repurpose them using Shift.

* **Shift + Record Arm 2**: Faders now control **Track Pan**.
* **Shift + Record Arm 3**: Faders now control **Send A** levels.

---

## 5. Channel Strip Enhancements (v1.0)

**Toggle / Momentary Solo and Mute (Dual Behavior)**
The Solo and Activator (Mute) buttons feature a smart state-machine:
* **Short Tap**: Standard toggle (Turns Solo/Mute on or off).
* **Long Hold (>400ms)**: Momentary toggle. The state will revert back to its original setting as soon as you release the button. Ideal for quick performative mutes or solo drops!
