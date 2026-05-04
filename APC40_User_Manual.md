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
  * **Toggle / Momentary kill switches**: in this mode the **Send A / B / C** buttons act as kill switches for **bass / mids / highs** (FilterEQ3 / Audio Effect Rack — or the first three filter bands on EQ8). They have the same dual behavior as Solo / Mute (v1.0): a short tap toggles the kill, a hold longer than 400 ms acts momentary (kill engages on press, reverts on release). Threshold mirrors `LONG_PRESS_DELAY` in `ToggleMomentaryChannelStripComponent.py:8` for consistency.
  * **FilterEQ3 Slope toggle**: when the active EQ device is a **FilterEQ3**, the **Pan button** toggles the device's **Slope** parameter (24 ↔ 48 dB/oct). LED is **on** when 48 dB/oct is engaged, **off** when 24 dB/oct. Pan reverts to its standard "lock to track" role on Eq8 / Audio Effect Rack tracks (Channel EQ tracks use Pan for Highpass on/off — see below).
  * **EQ Eight (Eq8)**: when the active EQ device is **EQ Eight**, the Track Control section's 2 × 4 encoder grid is laid out as:
    * **Top row** (encoders 1 / 2 / 3 / 4): **Scale** / **Low Freq** / **Mid Freq** / **High Freq**.
    * **Bottom row** (encoders 5 / 6 / 7 / 8): **Output** / **Low Gain** / **Mid Gain** / **High Gain**.
    * Bands wired: **band 1 (Low)**, **band 2 (Mid)**, **band 8 (High)** — Highs land on the topmost band so the band most musicians touch sits under the rightmost gain knob.
    * **Auto Q swap**: when band 1 or band 8 is set to a filter type that has no gain (low-cut / high-cut / notch), that band's gain encoder (Low Gain or High Gain) automatically becomes a **Q (resonance)** control instead. Switching the filter type back to a shape with gain (shelf / bell) restores the gain binding. Mid Gain (encoder 7) is always gain — band 2 is not affected.
    * Send A / B / C kill switches toggle bands 1 / 2 / 8 on / off (with toggle-momentary dual behavior, threshold 400 ms).
    * **Pan button** keeps its standard "lock to track" role on Eq8.
  * **Channel EQ (Live 11+)**: when the track contains Live's **Channel EQ** device, the Track Control row remaps automatically:
    * **Encoder 1** (first knob) → **Mid Freq** (split / sweep frequency).
    * **Encoder 5** (the knob to the left of the band gains) → **Output** (output trim).
    * **Encoders 6 / 7 / 8** (last three knobs) → **Low / Mid / High Gain** — same positions used for FilterEQ3 / Audio Effect Rack so the band gains are always under the same knobs.
    * **Pan button** → **Highpass on/off** (replaces the lock function while Channel EQ is the active EQ device).
    * Send A / B / C kill buttons are inactive on Channel EQ (the device has no per-band on/off switches).

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

### Global Variations Mode (Per-Track Rack Variations)
* **How to access**: Hold **SHIFT** and press **Track Select 7** to enter Matrix Mode 7 — now `Global Variations Mode` (replaces the former User/Note Mode 5).
* **Function**: Each of the 8 grid columns is bound to one of the 8 visible session tracks at mode entry. For each track, the script picks the **first device with stored variations** (any Rack — Drum / MIDI / Instrument / Audio Effect) and shows that rack's variations down the column.
  * **Green pad** — variation slot is stored on this column's rack.
  * **Red pad** — slot is currently selected on this column's rack.
  * **Off pad** — slot is empty, OR the column's track has no rack with variations (the entire column stays dark in that case).
* **Trigger one variation**: Press the pad — sets `selected_variation_index` and recalls instantly on that column's rack only.
* **Trigger across all tracks**: Press a **Scene Launch** button. Scene 1 recalls row 1 across every column that has a variation at that row; tracks without that variation are skipped silently. Scene LED lights green when at least one column has a stored variation at that row.
* **Scroll past 5 variations**: Use **Bank Select ↑ / ↓** to slide the visible window up/down. The same offset is applied to every column.
* **Randomize macros (every column at once)**: Press **Stop All Clips** — calls `device.randomize_macros()` on every column's rack simultaneously. (No-op on columns without a rack.)
* **Track Stop row**: keeps its default clip-stop function in this mode.
* **Storing variations**: still on **Shift + Tap Tempo** (it acts on the appointed device, not necessarily this column's rack — appoint the rack first via the blue-hand icon or **Shift + Nudge Back**).

### Variations Mode (Rack Macro Snapshots)
* **How to access**: Hold **SHIFT** and press the rightmost **Track Select** button (Track Select 8) to enter Matrix Mode 8 — now `Variations Mode` (replaces the former User/Note Mode 6).
* **Function**: Each of the 40 pads in the 5×8 clip grid maps to one variation slot on the **currently appointed Rack** (Drum Rack, MIDI Rack, Instrument Rack — anything with macros). Row-major: top-left = slot 0, bottom-right = slot 39.
  * **Green pad** — variation slot is stored.
  * **Red pad** — variation slot is currently selected.
  * **Off pad** — slot is empty (or no Rack appointed).
* **Trigger a variation**: Press the pad. Sets `selected_variation_index` and recalls instantly. (For ramped/morphed recall, use Tap Tempo as before — this mode is for fast pad triggering.)
* **Real-time LED refresh**: LEDs follow Live in real time — adding a new variation via **Shift + Tap Tempo** (or in Live's UI) lights up the next green pad immediately; switching the selected variation moves the red pad.
* **Randomize the appointed rack's macros**: Press **Stop All Clips** — calls `device.randomize_macros()` on the appointed device. Combine with Shift + Tap Tempo to capture the random state as a new variation.
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
