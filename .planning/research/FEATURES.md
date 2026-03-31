# Feature Landscape: 16Macros Milestone

**Domain:** MIDI control surface script — 16-parameter encoder control + toggle/momentary send buttons
**Researched:** 2026-03-31
**Confidence:** HIGH — All analysis is grounded in the existing codebase. No external sources required for implementation patterns; v1.0 implementation provides a proven template.

---

## Context: What Is Already Built

This is a subsequent milestone. The following features are complete and not in scope here:

- Toggle/momentary Solo (short press = toggle, long press >= 400ms = momentary, revert on release)
- Toggle/momentary Mute (same behavior)
- Shift guards on Solo/Mute (mid-hold button reassignment does not corrupt state)
- `disconnect()` hardening (reverts active momentary holds before teardown)
- DRY helper `_handle_toggle_momentary` in `ToggleMomentaryChannelStripComponent`
- Timer infrastructure registered/unregistered through `SpecialChanStripComponent`

The new milestone adds two independent feature clusters: encoder expansion and send buttons.

---

## Feature Cluster 1: 16-Parameter Encoder Mapping via Pan Mode

### What Exists

The APC40 has two physical encoder rows:

- **Top row (8 encoders):** CC 16-23 on channel 0. Managed by `ShiftableDeviceComponent` via `device_param_controls`. Currently maps to device parameters 1-8 (bank 0) through the framework's `DeviceComponent._assign_parameters()`.
- **Track control row (8 encoders):** CC 48-55 on channel 0. Managed by `EncModeSelectorComponent` via `_global_param_controls`. In mode_index 0 (Pan mode), these route to per-track pan via `channel_strip.set_pan_control()`.

`EncModeSelectorComponent.update()` at mode_index 0 calls `set_pan_control(self._controls[index])` on each of the 8 mixer channel strips. This is the currently unused capacity that the 16Macros feature repurposes.

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Top 8 encoders map to device params 1-8 in Pan mode | User's stated goal. In device modes (non-Pan), the top row already does this via `ShiftableDeviceComponent`. The 16Macros feature makes Pan mode a dedicated 16-param view. | Low | Top row behavior may be the same as today depending on approach; confirm whether Pan mode needs to detach the top row from `ShiftableDeviceComponent` or can leave it as-is |
| Track control row maps to device params 9-16 in Pan mode | This is the net-new capability. Instead of routing to per-track pan, the 8 track control encoders connect to device params 9-16 of the currently selected/locked device. | Medium | Requires either a new mode branch in `EncModeSelectorComponent.update()` or a separate component that takes ownership of `_global_param_controls` when Pan mode is active |
| Params follow selected device | Params 1-16 should map to the currently selected device, consistent with how the existing top-row device control works. | Low | Already provided by `ShiftableDeviceComponent`'s appointed_device listener and `EncoderDeviceComponent._on_device_changed()` pattern |
| Encoder LED rings reflect parameter position | RingedEncoderElement already handles ring display. The ring mode follows the mapped parameter's type (pan = bi-polar, volume = unipolar, etc.). This must continue to work for the lower 8 encoders when mapped to device params. | Low | `RingedEncoderElement.update_ring()` reads the parameter type from `Live.MidiMap.MapMode`; as long as the connection is made via standard `connect_to()`, this is automatic |
| Switching away from Pan mode releases device params | When the user presses Send A/B/C (modes 1, 2, 3), the track control row must release device parameters and restore per-track send routing. Leaving orphaned parameter connections causes stuck encoders. | Low | Pattern already exists in `EncModeSelectorComponent.update()` — each mode branch calls `set_pan_control(None)` on exit. The 16Macros implementation must follow the same cleanup discipline. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Device lock carries over to 16-param view | If the device is locked (via the lock button in EncoderDeviceComponent), the 16-param view should follow the locked device, not the selected track's device. Consistent with existing lock behavior for the top 8 encoders. | Medium | Requires `EncoderDeviceComponent._is_locked` state to be readable by the new mode logic, or the new component to share the same lock state |
| Bank navigation stays functional for params 1-8 | The top row has bank navigation (Previous/Next Device buttons shift which 8 params are shown). In a 16-param view, bank 0 always = params 1-16, with no bank shifting needed. Make this explicit. | Low | If the top 8 encoders in Pan mode use `ShiftableDeviceComponent` unchanged, bank nav will still be active. Decision: does 16Macros mean "always params 1-16, no bank nav" or "bank nav on top row only"? Needs explicit decision before implementation. |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Remapping Pan mode globally for all uses | The existing mixer Pan mode is used by other components (EQ mode, Send mode), and `ChannelTranslationSelector` has mode buttons wired to all 4 modes including Pan. Wholesale replacement breaks existing behavior. | Intercept or augment Pan mode behavior within `EncoderUserModesComponent` or a new subcomponent — do not modify `EncModeSelectorComponent.update()` for mode_index 0 if it is shared by other paths |
| Two separate device connections fighting over the same encoders | Both `ShiftableDeviceComponent` (top row) and the new 16Macros mode would try to connect to device params. Two concurrent connections to the same parameter via different controls is an undefined state in Live's framework. | Ensure exactly one component "owns" the param connections at any time. The 16Macros implementation must explicitly release the top row from `ShiftableDeviceComponent` before connecting it to the new 16-param path, or use the existing `EncoderDeviceComponent._alt_device` which already manages param ownership. |
| A third encoder component class | `EncoderDeviceComponent` already wraps `DeviceComponent` for an alternate 8-param device view. Adding a third component class for 16-param behavior creates three overlapping abstractions. | Extend `EncoderDeviceComponent` to accept 16 controls instead of 8, or implement the 16-param routing within the existing `EncoderUserModesComponent._set_modes()` dispatch (mode_index 0 branch). |

### Feature Dependencies

```
Pan mode active (mode_index 0 in EncModeSelectorComponent or EncoderUserModesComponent)
    --> Top 8 encoders (device_param_controls) connected to device params 1-8
    --> Track control row (global_param_controls) connected to device params 9-16
        --> Both sets released when mode changes to 1/2/3 (Send A/B/C)
            --> Ring LED display correct for both rows via RingedEncoderElement

Device lock state
    --> 16-param view follows locked device if locked
    --> 16-param view follows selected track's device if not locked
```

---

## Feature Cluster 2: Toggle/Momentary Send A/B/C Buttons

### What Exists

Send A/B/C are per-track buttons on the APC40. In the current script, they are repurposed in `EncModeSelectorComponent` as mode-select buttons (choosing which send to control via the track control row encoders). They are **not** wired as per-track send toggle buttons.

The v1.0 implementation proves the toggle/momentary pattern works cleanly via `_handle_toggle_momentary` in `ToggleMomentaryChannelStripComponent`. The framework's `ChannelStripComponent` has `_send_value` handlers and the `Live.Track` API provides `mixer_device.sends[index]` for send amount access.

The goal: pressing Send A on a given track acts as a toggle/momentary for that track's Send A enable state (active/inactive), using the same ~400ms pattern as Solo/Mute.

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Short press toggles send on/off | The same contract as Solo/Mute. Short tap = commit the toggle. No regression to the current mode-select behavior (that is now handled by the global encoder mode buttons, not per-track). | Low-Medium | Need to confirm the per-track Send A/B/C MIDI notes and whether they are currently free for this use, or if they are consumed by `EncModeSelectorComponent` globally |
| Long press momentary send | Hold = send active while held, release = revert to prior state. Same 400ms threshold. | Medium | Direct reuse of `_handle_toggle_momentary` with the attribute name pointing to `mixer_device.sends[index].value` — but sends use float values (0.0-1.0), not booleans, so the "toggle" semantic requires a decision (see below) |
| State reverts on release | Release after a long press reverts the send to its pre-press value. | Low | Same pattern as Solo/Mute, captured at press-down |
| LEDs reflect live state | Send button LEDs light when send is active (non-zero). | Low | The existing `ChannelStripComponent._update_track_states()` handles LED updates when track state changes; ensure that lighting path is preserved |
| Shift guards | Mid-hold button reassignment (from shift mode changes) must not leave a send in a stuck momentary state. | Low | Direct reuse of the existing shift guard pattern — check `self._shift_pressed` on press-down and return early if true |
| disconnect() reverts active send holds | Same hardening as Solo/Mute: `disconnect()` must revert any send that is currently in a momentary hold. | Low | Direct reuse of the disconnect pattern in `ToggleMomentaryChannelStripComponent.disconnect()` |

### The Toggle Semantic for Sends (Critical Decision)

Solo and Mute are boolean (True/False). Sends are continuous (float 0.0 to 1.0, or the framework may expose them as `on/off` separately from the amount).

Two valid interpretations:

1. **Toggle the send amount between 0.0 and the stored non-zero value.** This preserves the user's send level. Press = mute the send (set to 0). Release (if long press) or press again (if short press) = restore to the stored value. Requires storing both "was active" and "what was the level."

2. **Toggle a send enable/disable if the Live API exposes one.** In Live 11+, `mixer_device.sends[index]` is a `DeviceParameter` with a `value` property. There is no separate boolean "send enabled" flag accessible via the Python API at the `ChannelStrip` level — enable is encoded in whether the value is 0.0 or a positive float.

**Recommendation:** Use interpretation 1 (toggle amount between 0.0 and stored value). This matches the mental model of "send active = amount > 0," preserves the user's send level across toggles, and maps cleanly onto the existing `_handle_toggle_momentary` helper with a float state variable instead of a boolean.

**Complexity note:** The `_handle_toggle_momentary` helper uses `getattr`/`setattr` on `self._track` attributes, which works for `solo` and `mute` (bool properties). For sends, the target is `self._track.mixer_device.sends[index].value` — a nested attribute with an index. The helper will need either a direct override or a small adaptation to handle send access by index.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Toggle stores and restores pre-press send level | Preserves user's intent (their configured send level is not lost by a toggle). | Medium | Requires storing a float, not a bool. Revert logic: if pre-press value was 0.0, set to a default "active" level (typically 1.0 or 0.85 = unity send); if pre-press was > 0, set to 0 on toggle, and restore on release. |
| Correct behavior when send is already at 0 | If a send is already off (value 0), a short press should activate it (set to a default non-zero level). Long press should activate while held, then return to 0 on release. | Medium | Needs a defined "default activation level." Unity (1.0) is the safest default. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| All three sends (A, B, C) behave consistently | One per-send state tuple (ticks, prior_value, momentary_active) per strip, indexed [0, 1, 2]. Consistent DX across all three. | Medium | Three send slots means 9 state variables per strip (3 per send * 3 sends), manageable but not trivial. Or: a list of 3 per-send dicts/tuples. |
| Reuse of `_handle_toggle_momentary` helper | Avoids divergent implementations. The DRY value is high — any bug fixed in the helper applies to all six buttons (Solo, Mute, Send A, Send B, Send C). | Medium | The helper's `getattr/setattr` model needs to be extended or the send handler needs its own method that shares the timer/revert logic but accesses sends by index. |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Separate timer registration for sends | `ToggleMomentaryChannelStripComponent` inherits a single timer callback from `SpecialChanStripComponent`. Adding a second registered timer for send state creates two concurrent timer callbacks fighting for the same tick rate. | Extend `_on_timer` in `ToggleMomentaryChannelStripComponent` to also handle the 3 send tick delays — same approach used for solo and mute ticks. |
| Making sends "exclusive" across tracks | Implementing logic like "activating Send A on track 1 deactivates it on other tracks" is not requested and would replicate exclusive-solo complexity for sends. | One send toggle per strip, independent. |
| Conflating send toggle buttons with send amount encoders | The Send A/B/C mode buttons in `EncModeSelectorComponent` route the track control row encoders to send A/B/C amounts respectively. The per-track Send A/B/C buttons are different hardware (MIDI note per track, not a global mode button). Do not confuse these two roles. | Verify MIDI note assignments to confirm per-track Send A/B/C notes are distinct from the global mode buttons. |

### Feature Dependencies

```
Send toggle/momentary (per-track)
    --> Requires per-track Send A/B/C MIDI notes to be free (not consumed by mode-select)
        --> Confirm: global mode buttons = notes 87-90 (Pan, Send A, B, C row 0); per-track = separate notes per channel
    --> Reuses timer infrastructure from SpecialChanStripComponent
    --> Reuses shift guard from ToggleMomentaryChannelStripComponent
    --> Requires float-value pre-press storage (not boolean like Solo/Mute)
    --> Requires disambiguation of "send active level" when toggling from 0

_handle_toggle_momentary extension or per-send override method
    --> Drives all three send slots (indexed 0, 1, 2)
    --> Shares the same 400ms LONG_PRESS_DELAY constant
    --> Feeds into extended _on_timer (must tick for 3 send delays + solo + mute)
```

---

## MIDI Hardware Note: Send Button Assignments

From `APC_64_40_9._setup_global_control()` and `EncModeSelectorComponent`:

- **Global mode buttons** (encoder mode row): MIDI notes 87-90, channel 0 — `Pan_Button` (87), `Send_A_Button` (88), `Send_B_Button` (89), `Send_C_Button` (90). These are `ConfigurableButtonElement` instances routed to `EncModeSelectorComponent` and `EncoderUserModesComponent`.

- **Per-track buttons** on the APC40 hardware: Each track has dedicated MIDI note buttons. Confirmed from `_setup_mixer_control()`: Solo = note 49 per channel, Mute = note 50 per channel. The APC40 also has per-track Send A (note 54?), Send B, Send C buttons — these need verification against the APC40 hardware spec before implementation.

**Research flag:** The per-track Send A/B/C MIDI note assignments are not explicitly coded in the current script (they are not wired to channel strips in `_setup_mixer_control()`). This means either (a) they are unmapped hardware buttons that the script has never used, or (b) they are the same physical buttons as the global mode row (hardware APC40 reuses button positions in different software modes). Clarify against APC40 hardware documentation before implementation begins.

---

## MVP Recommendation

**Phase order:**

1. **Send A/B/C toggle/momentary** — Lower risk. Directly extends proven `ToggleMomentaryChannelStripComponent` pattern. The only new complexity is float vs. bool send values and the per-send index access. No architecture changes, no component ownership conflicts.

2. **16-parameter encoder mapping** — Higher risk. Requires resolving component ownership conflicts between `ShiftableDeviceComponent`, `EncoderDeviceComponent`, and `EncModeSelectorComponent` for Pan mode. Needs the MIDI hardware clarification (see above) and a decision on whether bank nav remains functional.

**Must ship (Send cluster):**
1. Short press toggles Send A per track (off = 0.0, on = stored non-zero or default 1.0)
2. Long press momentary send with immediate activation
3. Revert to prior send level on release
4. Correct behavior when send was already active (inverts while held, restores on release)
5. Shift guards on all three sends
6. `disconnect()` hardening for all three sends
7. Same 400ms threshold as Solo/Mute (shared constant)

**Must ship (Encoder cluster):**
1. Pan mode: top 8 encoders connected to device params 1-8
2. Pan mode: track control row connected to device params 9-16
3. Switching out of Pan mode cleanly releases all 16 connections
4. Device lock state respected (locked device vs. selected track device)
5. Ring LEDs work correctly on both rows

**Defer:**
- Configurable threshold (still out of scope)
- Bank nav behavior in 16-param mode (can be left as-is and documented)
- Any new button types beyond Send A/B/C

---

## Sources

- Codebase analysis: `EncModeSelectorComponent.py`, `EncoderDeviceComponent.py`, `EncoderUserModesComponent.py`, `ShiftableDeviceComponent.py`, `ToggleMomentaryChannelStripComponent.py`, `SpecialChanStripComponent.py`, `APC_64_40_9.py` (all read directly — HIGH confidence)
- `.planning/PROJECT.md` — milestone requirements, validated decisions (HIGH confidence)
- Prior v1.0 FEATURES.md — toggle/momentary pattern documentation (HIGH confidence)
