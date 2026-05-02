# APC_64_40_11 — Troubleshooting & Known Limitations

This document covers the failure modes and intentional limitations a user is likely to encounter. Every entry is traced to the source file and line range that implements (or omits) the behavior.

## 1. The script doesn't appear in Live's MIDI preferences (handshake failure)

**What you might see:** You select `APC_64_40_11` in Live's Control Surface dropdown, but the APC40's clip grid stays dark, or you can't get any feedback from the controller. Or the dropdown doesn't list `APC_64_40_11` at all.

**Why it happens:** Live discovers control surface scripts by scanning the `MIDI Remote Scripts` folder at startup and matching against `get_capabilities()` in `__init__.py:30-32` (which declares `vendor_id=2536` and `product_ids=[115]` for Akai APC40). If the folder is misnamed (e.g. `APC_64_40_11-MAIN` from a GitHub ZIP), Live skips it. If the script loads but the handshake doesn't complete, the LED feedback never enables — `APC.py:94-100` `_on_handshake_successful` is what flips every component to enabled (`component.set_enabled(True)`), and until that runs, the matrix and the LEDs stay dark. Live 12 also changed the version-introspection API used during the introduction message, which the script handles via a try/except fallback (`APC.py:127-148`).

**What to do:**

1. Confirm the folder name is exactly `APC_64_40_11` (no `-MAIN` / `-main` suffix).
2. Confirm you're in the right `Resources/MIDI Remote Scripts` folder for your installed Live edition (Suite vs. Standard, Live 11 vs. Live 12).
3. Restart Ableton Live after dropping the folder — Live only scans for scripts at startup.
4. In Live's MIDI preferences, set both Input and Output to the APC40 ports.
5. Disconnect / reconnect the APC40 USB cable, then re-select the script.
6. If you're on Live 12 and the script seems to load but never lights up, this script handles Live 12's API change (`APC.py:127-148`) — confirm you have the latest version of this repo.

## 2. Pressing Solo on track A doesn't un-solo track B (exclusive-solo bypass)

**What you might see:** Live's mixer normally has "exclusive solo" — soloing one track un-solos all others. With this script, pressing Solo on the APC40 leaves other soloed tracks soloed too.

**Why it happens:** This is intentional. The script's Solo state machine writes `track.solo` directly via `setattr(self._track, track_attr, not current)` (`ToggleMomentaryChannelStripComponent.py:33`). It does NOT call Live's exclusive-solo coordinator, because the toggle/momentary unified model needs deterministic per-track state — exclusive solo would interfere with the momentary "release reverts to prior state" semantics that the long-press behavior relies on.

**What to do:**

- To un-solo all tracks, click solo on each soloed track to toggle it off, or use Live's mixer (mouse), which goes through the exclusive coordinator.
- This is by design and not user-configurable.

## 3. The 400ms long-press threshold feels wrong (not adjustable)

**What you might see:** Some users want a shorter (e.g. 250ms) momentary threshold. Some want longer (600ms+). The current 400 ms threshold is fixed.

**Why it happens:** The threshold is hardcoded in two places: `ToggleMomentaryChannelStripComponent.py:8` (`LONG_PRESS_DELAY = 4`) for Solo / Mute, and `EncModeSelectorComponent.py:9-10` (also `LONG_PRESS_DELAY = 4`) for Send A / B / C mode buttons. The constant is in 100ms ticks (Ableton's MIDI timer fires every 100ms), so 4 ticks × 100ms = 400ms.

**What to do:**

- The threshold is not exposed as a user-configurable setting. Adjusting it requires editing the source code.
- The 400ms value was chosen to be long enough that a deliberate hold feels distinct from an accidental long press, while short enough that holding doesn't feel laggy. If you decide to change it, edit both files (Solo/Mute and Send mode use the same threshold by design — a shared `LONG_PRESS_DELAY` constant in each file).

## 4. There are no per-track Send A / B / C buttons

**What you might see:** You're looking for a button that lets you adjust Track 5's Send B without first switching to Send B mode globally.

**Why it happens:** The APC40 hardware has only global Send-mode selectors (the Pan / Send A / B / C row), not per-track Send buttons. The script reflects the hardware: `EncModeSelectorComponent.py:80-81` declares `number_of_modes() == 4` (Pan / Send A / Send B / Send C are the only encoder modes the script wires), and there is no per-track equivalent because no per-track button exists on the controller.

**What to do:**

- To adjust Track 5's Send B, press Send B (the encoder mode button), then turn Track 5's top encoder. The Send A / B / C buttons themselves use the toggle/momentary unified model — short tap latches the mode; hold ≥400ms for a temporary jump that reverts to Pan on release.

## 5. There are no Track Activator (arm-record) buttons in the toggle/momentary row

**What you might see:** You expect the row of buttons under each track to include Track Activator / arm-record (the way some other APC40 scripts wire them).

**Why it happens:** Deliberate scope. The script wires the per-track button rows for Solo and Mute under the toggle/momentary model. Arm-record is mapped only conditionally inside the channel-strip when not in step-sequencer mode and not in shift mode (`ShiftableSelectorComponent.py:101-102` for the wire, `ShiftableSelectorComponent.py:112-113` for the unwire when Shift is held). There is no momentary / Activator-style mapping for arm.

**What to do:**

- To arm a track for recording, use Live's mixer (mouse), or use a different control surface script. This script is intentionally focused on the Solo / Mute / Pan / Send / variation use cases.

## Notes

- "Variations" in this script means Ableton's canonical Macro Rack variations. Use this term when searching Ableton's documentation or forums.
- Source files referenced in this document live at the repo root (e.g. `APC.py`, `__init__.py`, `ToggleMomentaryChannelStripComponent.py`, `EncModeSelectorComponent.py`, `ShiftableSelectorComponent.py`). They are read-only references from a user's perspective; modifying them is out of scope for end-user use.
