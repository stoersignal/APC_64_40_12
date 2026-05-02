# APC_64_40_11 — Install & First-Run Setup

This guide walks you from a fresh clone or ZIP download to a working APC40 controller in Ableton Live 11 or Live 12. Tested on Windows and macOS. Linux is not officially supported (Ableton Live does not ship for Linux).

## What you need

- An Akai APC40 (vendor ID `2536`, product ID `115` — see `__init__.py:30-32`)
- Ableton Live 11 or Live 12 installed
- The `APC_64_40_11` folder from this repo (download as ZIP from GitHub, or `git clone`)

## Step 1 — Place the script in Ableton's MIDI Remote Scripts directory

The script must live in Ableton's `MIDI Remote Scripts` folder. The folder is in different places on Windows and macOS.

### Windows

Default location:

```
c:\programdata\Ableton\Live 11 Suite\Resources\MIDI Remote Scripts
```

(Replace `Live 11 Suite` with your installed edition, e.g. `Live 12 Standard`. The path always ends in `Resources\MIDI Remote Scripts`.)

After placing the folder, you should see all this repo's `.py` files inside:

```
c:\programdata\Ableton\Live 11 Suite\Resources\MIDI Remote Scripts\APC_64_40_11
```

**GitHub ZIP gotcha:** if you downloaded a ZIP from GitHub, the extracted folder may be named `APC_64_40_11-MAIN` (or `APC_64_40_12-main`). Rename it to `APC_64_40_11` (drop the `-MAIN` / `-main` suffix) — Live ignores folders with non-standard names.

### macOS

1. In Finder, locate the `Ableton Live 11 Suite.app` (or `Ableton Live 12 Suite.app`) bundle.
2. Right-click → **Show Package Contents**.
3. Navigate into:

   ```
   Contents/App-Resources/MIDI Remote Scripts
   ```

4. Drop the `APC_64_40_11` folder here.

## Step 2 — Select the script in Live's preferences

1. Launch Ableton Live.
2. Open `Live → Preferences` (or `Ableton Live → Settings` on macOS).
3. Switch to the **MIDI / Sync** tab.
4. In the **Control Surface** column, click the dropdown for the row matching your APC40 and select **APC_64_40_11**.
5. In the **Input** and **Output** columns, set both to your APC40's port.
6. Make sure the **Track**, **Sync**, and **Remote** toggle checkboxes match the standard pattern (Track and Remote on for both input and output). The script declares its port capabilities via `__init__.py` `get_capabilities()`, advertising `NOTES_CC`, `SCRIPT`, and `REMOTE` on input plus `SCRIPT` and `REMOTE` on output.

## Step 3 — Verify the handshake

With the APC40 connected and the script selected, the controller initialization performs an identity + dongle handshake (see `APC.py:71-100` for the sequence: `handle_sysex` → `_on_identity_response` → `_on_handshake_successful`). Confirm the handshake worked using the existing gesture:

> Hold the **Shift** button on the APC40 and press the various **Track Selection** buttons to switch matrix modes. If the clip grid changes layout (e.g. flips into Note Mode 1, Session Overview, etc.), the script is loaded and talking to the controller.

The script supports both Live 11 and Live 12. Live 12 changed the introduction-message API; the script handles the fallback automatically (`APC.py:127-148` `_send_introduction_message` — tries `application().get_major_version()` first, falls back to `(12, 0, 0)` if the API raises `AttributeError`).

## Next

- [Interactive controller manual](manual.html) — open in any browser to learn every control.
- [Troubleshooting](TROUBLESHOOTING.md) — if the handshake fails or behavior surprises you.
