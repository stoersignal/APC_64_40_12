# Domain Pitfalls: Toggle/Momentary Dual-Mode Button Behavior

**Domain:** MIDI control surface script — press-duration detection, state management, LED feedback
**Project:** APC40 Toggle/Momentary Button Behavior
**Milestone:** v1.1 16Macros (16-parameter encoder mapping + toggle/momentary Send A/B/C)
**Researched:** 2026-03-31
**Overall confidence:** HIGH — derived from direct codebase analysis and verified framework source patterns

---

## Scope of This File

Pitfalls are organized into two sections:

1. **v1.0 pitfalls (Solo/Mute)** — carried forward from the initial research, still valid as regression risks
2. **v1.1 pitfalls (16Macros)** — new pitfalls specific to: (a) 16-parameter encoder mapping via Pan mode, and (b) toggle/momentary Send A/B/C buttons

---

## Part 1: v1.1 Critical Pitfalls — 16-Parameter Encoder Mapping

---

### Pitfall E1: Dual-Assignment of `_global_param_controls` Without Proper Handoff

**What goes wrong:** The 8 global track encoders (`_global_param_controls`, CC 48-55, channel 0) are already assigned to `EncModeSelectorComponent` as well as to `EncoderDeviceComponent` and `EncoderEQComponent` via `EncoderUserModesComponent`. Adding a second set of 8 encoder assignments (the device encoders, CC 16-23) to the same Pan mode without cleanly releasing the encoders from their current owners causes both assignments to fire simultaneously.

**Why it happens:** `EncModeSelectorComponent.update()` calls `self._mixer.channel_strip(index).set_pan_control(self._controls[index])` and `set_send_controls(...)` for mode_index 0. If `device_param_controls` (CC 16-23) are also connected to a `DeviceComponent` via `ShiftableDeviceComponent`, they remain mapped to device parameters. The two mappings coexist silently — the encoder sends its MIDI value to both the pan parameter and the device parameter simultaneously.

**Consequences:**
- Moving an encoder in Pan mode accidentally changes a device parameter
- Device parameter mapping drifts without user intent
- Extremely hard to debug because both effects happen at the same MIDI value arrival

**Prevention:** Before assigning `device_param_controls` to a new device mapping in Pan mode, call `release_parameter()` on each control. Follow the pattern in `EncoderUserModesComponent._set_modes()` (lines 116-118): iterate `_param_controls` and call `control.release_parameter()` before reassigning. The mode that "takes over" the encoders owns the release responsibility.

**Detection (warning signs):**
- Moving a top encoder in Pan mode causes a visible change in the device's parameter display in Ableton's Device View
- `ShiftableDeviceComponent.update()` is observed to call `_assign_parameters()` after a mode switch to Pan
- Two separate `connect_to()` calls on the same encoder without an intervening `release_parameter()`

**Phase:** Phase 1 — encoder mapping implementation

---

### Pitfall E2: `EncModeSelectorComponent.update()` Only Iterates 8 Strips — Mismatch With 16-Parameter Intent

**What goes wrong:** The current `EncModeSelectorComponent.update()` iterates `range(len(self._controls))` which is 8 (the global track encoders). When Pan mode is extended to also map the 8 device encoders to parameters 9-16, a naive approach passes the combined 16 controls as `self._controls`. This breaks the assertion `len(controls) == 8` in `set_controls()` (line 52) and also breaks the inner loop that maps `self._controls[index]` to `channel_strip(index)` — there are only 8 visible channel strips but 16 controls.

**Why it happens:** The architecture of `EncModeSelectorComponent` assumes a 1:1 relationship between encoder index and channel strip index. Extending to 16 parameters requires a different mental model: the top 8 encoders still map to channel strips (as pan or send), but the bottom 8 encoders map to device parameters 9-16 of the *selected device*, not to additional channel strips.

**Consequences:**
- If `set_controls()` is naively called with a 16-element tuple, the assertion fails and the mode selector crashes on component load
- If the loop is extended to 16 without restricting to available channel strips, `self._mixer.channel_strip(index)` at index 8-15 will throw an IndexError or return `None`
- Misassigned parameter targets: encoders 9-16 need a device parameter path, not a mixer strip path

**Prevention:** Keep `EncModeSelectorComponent` handling the first 8 encoders to channel strip pan/sends as it does now. Add a separate, dedicated component (or extend `ShiftableDeviceComponent`) to handle the device encoders' parameter 9-16 mapping in Pan mode. The two halves are fundamentally different: mixer strips vs. device parameters.

**Detection (warning signs):**
- Any modification that changes the `len(controls) == 8` assertion in `EncModeSelectorComponent.set_controls()`
- A call to `self._mixer.channel_strip(index)` with `index >= 8`
- A `set_controls()` call passing a 16-element tuple to `EncModeSelectorComponent`

**Phase:** Phase 1 — architecture decision before implementation begins

---

### Pitfall E3: Encoder Parameter Release Not Called on Mode Exit

**What goes wrong:** When leaving Pan mode (switching to Send A, Send B, Send C, or any shift-based mode), the device encoders (CC 16-23) are not released from their parameter 9-16 connections before being reassigned. They carry their previous mapping into the new mode.

**Why it happens:** `EncModeSelectorComponent.update()` currently reassigns the top 8 encoders when mode changes, but does not handle a "second row" of device encoders. When mode switches away from Pan, the device encoder bindings are never cleared because no code owns that cleanup.

**Consequences:**
- Device parameter 9-16 continues changing when user moves the device encoders in Send mode
- The physical encoder LED rings (RingedEncoderElement) show stale parameter position until the parameter is released
- `release_parameter()` for the device encoders is never called, leaving parameters in a "controlled" state that prevents them from being connected to other targets

**Prevention:** In whatever component or method establishes the Pan-mode device parameter mapping, pair every `connect_to()` call with a corresponding `release_parameter()` call in the mode teardown path. Model on `EncoderUserModesComponent._set_modes()` lines 126-128 which explicitly releases `_parameter_controls` before disabling `_encoder_device_modes`.

**Detection (warning signs):**
- After switching from Pan mode to Send A mode, the device encoders still visually track device parameter changes
- `RingedEncoderElement` LED ring shows a value different from the current pan/send level after mode switch
- No `release_parameter()` call paired with the Pan-mode `connect_to()` in the mode teardown path

**Phase:** Phase 1 — must be addressed in the same implementation task as parameter assignment

---

### Pitfall E4: `PAN_TO_VOL_DELAY` Timer in `EncModeSelectorComponent` Conflicts With New Timer

**What goes wrong:** `EncModeSelectorComponent` already uses `_register_timer_callback(self._on_timer)` and manages `_pan_to_vol_ticks_delay` in its `_on_timer`. If the 16-parameter Pan mode implementation adds its own timer logic into the same component (e.g., for a "hold Pan button to activate 16-param mode" behavior), the two timer counters interact and the `_on_timer` method becomes difficult to reason about. In the worst case, a new counter is added that is never reset, causing `_on_timer` to perpetually run its logic.

**Why it happens:** `EncModeSelectorComponent._on_timer()` is already the only timer in this component. It is tempting to add more countdown logic there. But the `PAN_TO_VOL_DELAY` counter is already a timer-within-a-timer pattern (5 ticks for pan-to-vol toggle). Adding a second counter creates two independent state machines in one timer method.

**Consequences:**
- If the new counter is not reset to `-1` after its action fires, `_on_timer` runs every 100ms performing a no-op check indefinitely
- The `_pan_to_vol_ticks_delay` counter and the new counter may fire in the same tick, with both performing conflicting mode updates
- Cascading `update()` calls in the same timer tick may send contradictory LED states to the hardware

**Prevention:** If a new timer-based behavior is needed for the 16-parameter mode, manage it in a separate component. Keep `EncModeSelectorComponent._on_timer()` responsible only for `_pan_to_vol_ticks_delay`. Follow single-responsibility: one component, one timer, one concern.

**Detection (warning signs):**
- More than one `*_ticks_delay` instance variable in `EncModeSelectorComponent`
- `_on_timer` in `EncModeSelectorComponent` performing two unrelated countdown actions in the same method
- `update()` called twice in the same timer tick via different timer branches

**Phase:** Phase 1 — architectural decision, establish before any timer additions

---

### Pitfall E5: Device Encoder Bank State Not Preserved Across Mode Switches

**What goes wrong:** `ShiftableDeviceComponent` tracks `_bank_index` (which group of 8 parameters is displayed). When Pan mode maps device encoders to parameters 9-16 (bank 1), the bank index changes. When the user switches to a different encoder mode and back, the bank index is not restored to 1 and the encoders revert to parameters 1-8.

**Why it happens:** `ShiftableDeviceComponent.set_device()` calls `self._control_translation_selector.set_mode(self._bank_index)`, and `update()` calls `_assign_parameters()`. Neither of these remembers that "in Pan mode, the device encoders should be pinned to bank 1." The bank is freely switchable via shift + bank buttons.

**Consequences:**
- User switches to device mode and back to Pan mode — device encoders now show parameters 1-8 again
- The 16-parameter mapping appears to "reset" randomly during a performance session
- Shift + device bank buttons (CC 58-65) still change the bank while the device encoders are supposed to be locked to params 9-16 in Pan mode

**Prevention:** Pan mode's device encoder assignment must explicitly force bank_index to 1 and prevent shift-bank switching from changing it while Pan mode is active. This requires either disabling the bank buttons in Pan mode or adding a "mode-active" guard in `_bank_value`. Document the locking behavior clearly.

**Detection (warning signs):**
- After navigating to device bank 0 and back to Pan mode, device encoders respond to parameters 1-8
- Shift + bank button while in Pan mode changes which parameters the device encoders control
- No explicit `set_mode(1)` or equivalent bank-lock call in the Pan mode activation path

**Phase:** Phase 1 — must be considered at design time

---

## Part 2: v1.1 Critical Pitfalls — Toggle/Momentary Send A/B/C Buttons

---

### Pitfall S1: Send A/B/C Buttons Have Dual Physical Roles — Mode Selector AND Per-Track Send

**What goes wrong:** The Pan/Send A/Send B/Send C buttons (MIDI notes 87-90, channel 0) are `ConfigurableButtonElement` instances stored as `_global_bank_buttons`. They are currently wired as mode buttons to both `EncModeSelectorComponent` (via `set_modes_buttons`) and `ChannelTranslationSelector` (via `set_mode_buttons`) and `EncoderUserModesComponent` (via `set_mode_buttons`). Adding toggle/momentary send enable to these same physical buttons means a single button press now has two interpretations: change the global encoder mode AND toggle/momentarily activate the per-track send.

**Why it happens:** The APC40 has a fixed button layout. The Send A/B/C buttons are the only dedicated per-track send controls on the hardware. They must serve both as the "which send do the encoders control" mode selector and as the "enable this send on this track" toggle. Without explicit coordination, pressing Send A causes `EncModeSelectorComponent._mode_value` to fire (switching all encoders to Send A), and simultaneously it should trigger the per-track toggle/momentary on the selected track.

**Consequences:**
- Every short press of Send A both (1) switches encoder mode to Send A AND (2) toggles the send on the selected track — these may conflict or produce confusing behavior
- Long press acting as momentary send: the encoder mode has already switched at press-down, but on release the momentary reverts the send — the user sees encoder mode change without the send staying on
- The `EncModeSelectorComponent` is enabled only when `ShiftableEncoderSelectorComponent` is in the non-shift mode. The toggle/momentary behavior needs to know whether the button is acting as a mode button or as a send toggle at any given moment

**Prevention:** Decide the disambiguation rule before implementation: does the toggle/momentary apply to the *selected* track's send level (the channel strip that the encoder mode selector would control), or does it apply to the track beneath the encoder? Confirm with the design whether pressing Send A always means "toggle this send on the focused/selected track" regardless of what the encoder does. If so, the toggle/momentary behavior belongs on the same component that receives the button's value and can run independently of the encoder mode path.

**Detection (warning signs):**
- No disambiguation logic in the value handler for "is this press a mode switch or a send toggle?"
- Pressing Send A while in shift mode (where encoder mode buttons are re-routed by `ShiftableEncoderSelectorComponent`) causes unexpected toggle behavior on the selected track
- The encoder mode changes at press-down but the send momentary reverts it on release

**Phase:** Phase 2 — Send button behavior; requires explicit design decision before coding

---

### Pitfall S2: `ChannelStripComponent` Has No `set_send_enable_button` — Send On/Off Is on the Track Object

**What goes wrong:** The existing toggle/momentary implementation (`ToggleMomentaryChannelStripComponent`) works on `track.solo` and `track.mute` because these are direct writable attributes on `Live.Track.Track`. Per-track send enable is different: it is `track.mixer_device.sends[n].enabled` — a property on the `AutomationLane` or `SendAmount` object within the mixer device. There is no `_send_value` method in `ChannelStripComponent` that maps to send enable in the same way `_solo_value` maps to track.solo.

**Why it happens:** Ableton's `ChannelStripComponent` provides `set_send_controls()` which maps an encoder to the send *level* (volume), not the send *enable state*. The framework has no built-in concept of a "send enable button" — that is a custom behavior.

**Consequences:**
- Attempting to use `getattr(self._track, 'send_a')` will fail with AttributeError — this attribute does not exist on `Live.Track.Track`
- The `_handle_toggle_momentary` helper from v1.0 cannot be reused without modification — it assumes the target attribute is on `self._track` directly
- The sends list may be empty (no sends configured in the Live set) — accessing `sends[0]` raises IndexError

**Prevention:** Before implementation, verify the Live API path: `self._track.mixer_device.sends[send_index]` returns a `MixerDevice.Send` object with an `enabled` attribute. Guard against empty sends list. The revert logic must also target `sends[n].enabled`, not a top-level track attribute. Write a helper that accepts `send_index` and handles the nested attribute path safely.

**Detection (warning signs):**
- Any use of `getattr(self._track, 'send_a')` or similar direct attribute access
- No guard for `len(self._track.mixer_device.sends) > send_index` before accessing the send
- The `_handle_toggle_momentary` helper called with `track_attr='sends[0]'` — `getattr`/`setattr` do not support subscript notation

**Phase:** Phase 2 — verify API path in Phase 1's research task before writing any code

---

### Pitfall S3: Send Index Mismatch Between Encoder Mode and Send Toggle

**What goes wrong:** The `EncModeSelectorComponent` uses mode_index 1/2/3 for Send A/B/C (0 = Pan). The send toggle on the channel strip needs to know which send index (0, 1, 2) to toggle. If the toggle always uses a hardcoded send index regardless of which button was pressed, pressing Send B toggles the wrong send (e.g., always send index 0 instead of send index 1).

**Why it happens:** The encoder mode and the per-track send toggle are separate code paths. The mode index is tracked in `EncModeSelectorComponent._mode_index`. The channel strip component does not have visibility into this mode index. Without explicit coordination, the strip has no way to know "which send button was just pressed."

**Consequences:**
- Pressing Send B toggles Send A on the track (index off by one or hardcoded)
- After switching from Send B mode to Send C mode, the toggle still affects Send B
- All three send buttons appear to toggle the same send

**Prevention:** Design the per-track send toggle to receive the send index at call time, not to derive it from a global mode. If the toggle/momentary behavior is implemented in the channel strip, the strip needs either a `set_active_send_index(n)` setter (called when mode changes) or the toggle logic should be invoked directly from the mode selector component with the send index as a parameter. The cleanest path: the toggle/momentary for sends belongs on the component that owns the mode decision (either `EncModeSelectorComponent` or a wrapper), not on the channel strip.

**Detection (warning signs):**
- A hardcoded send index in the send toggle handler (e.g., `self._track.mixer_device.sends[0].enabled`)
- No communication path from `EncModeSelectorComponent` to the strip about which send index is active
- Pressing Send B showing LED feedback for Send A on the track

**Phase:** Phase 2 — architecture issue, must be resolved in design before code

---

### Pitfall S4: LED State for Send Enable Requires Manual Management

**What goes wrong:** For Solo and Mute, the framework's `ChannelStripComponent` automatically updates the button LED via `_on_solo_changed` and `_on_mute_changed` listeners. No equivalent framework listener exists for per-track send enable. If the send enable LED is not manually updated after each toggle or momentary revert, it will stay in the wrong state.

**Why it happens:** `ChannelStripComponent` registers listeners for track attributes it manages. Send enable is not a managed attribute in the stock framework — the framework only manages send *level* via encoders. Therefore the LED update path for send enable must be written from scratch.

**Consequences:**
- After toggling send enable, the Send button LED does not change — the button appears dead
- After a momentary revert on release, the LED stays lit even though the send was re-disabled
- Track state and LED state diverge permanently after the first toggle

**Prevention:** After every write to `sends[n].enabled`, explicitly update the button LED: call `self._send_button.turn_on()` or `turn_off()` based on the new value. Also register a `sends[n].add_enabled_listener(callback)` to update the LED if the send state changes through other paths (automation, GUI). Remove this listener in `disconnect()` and when the track changes.

**Detection (warning signs):**
- No `add_enabled_listener` call for the send enable attribute
- Send button LED does not reflect live send state when another controller or the GUI changes send enable
- No `turn_on()` / `turn_off()` call in the toggle/momentary handler for the send button

**Phase:** Phase 2 — LED management is a required part of the feature, not an enhancement

---

### Pitfall S5: Shift Guard Broken Because Send Buttons Already Have Shift-Modified Behavior

**What goes wrong:** In v1.0, the shift guard in `_solo_value` / `_mute_value` (`if self._shift_pressed: return`) prevents toggle/momentary behavior when shift is held. The Send A/B/C buttons in shift mode are re-routed by `ShiftableEncoderSelectorComponent._toggle_value()` — shift hold causes `ShiftableEncoderSelectorComponent` to call `update()` which reassigns the buttons to `EncModeSelectorComponent`. This means shift + Send A fires two handlers: the shift toggle handler (which re-routes encoder modes) AND potentially the send toggle handler (which would try to toggle the send while shift is held).

**Why it happens:** `ShiftableEncoderSelectorComponent._toggle_value()` at line 80-101 of `ShiftableEncoderSelectorComponent.py` handles the shift press and fires `_recalculate_mode()`. The send toggle handler would also fire because the same button element fires all registered listeners. Unless there is a shared `_shift_pressed` state that the send toggle handler can check, it cannot distinguish "shift + Send A" from a plain "Send A".

**Consequences:**
- Shift + Send A (which should only change encoder mode routing) accidentally toggles the per-track send enable
- A track send gets toggled during the button remapping at shift press time
- Shift release triggers a momentary revert for a send that was never intentionally activated

**Prevention:** The send toggle handler must check `_shift_pressed` before acting — same as the Solo/Mute handlers. The `_shift_pressed` flag must be accessible from wherever the send toggle handler lives. If the handler is on the channel strip, the strip must have `set_shift_button()` wired to the same shift button as the rest of the system (pattern already established at `APC_64_40_9.py` line 159).

**Detection (warning signs):**
- No `_shift_pressed` check at the top of the send toggle value handler
- Track sends toggling when shift is pressed
- The `set_shift_button()` setter is not called on the component that handles send toggles during `_setup_mixer_control()`

**Phase:** Phase 2 — must be in the initial implementation, same lesson as Pitfall 5 (v1.0)

---

### Pitfall S6: Momentary Revert Race With EncModeSelectorComponent Mode Change

**What goes wrong:** On a long press of Send B: (1) press-down fires, send B enable toggles immediately, mode switches to Send B, timer starts; (2) user holds; (3) user releases — the momentary revert fires to restore send B enable. But simultaneously, the mode does not change back on release (the mode stays at Send B because `EncModeSelectorComponent` uses non-momentary mode buttons). The send reverted but the mode did not — the UI shows "Send B mode" but the send is now disabled on that track.

**Why it happens:** Encoder mode selection (which set of parameters the encoders control) is a persistent latch: pressing Send B mode stays in Send B mode until another button is pressed. Send toggle/momentary, by contrast, is transient. The two behaviors have asymmetric release semantics.

**Consequences:**
- After a momentary hold of Send B, the track's send B is off but the encoders are controlling send B levels — the encoder controls a parameter that appears inactive
- Users who intended to "hold Send B to temporarily enable it" find it still disabled after release
- LED state shows Send B mode active (encoder mode LED) but send enable LED shows off

**Prevention:** Decide whether the momentary behavior applies to (a) the per-track send *enable* (on/off toggle), (b) the encoder mode assignment (Pan/Send A/B/C), or both. These are two separate concepts mapped to the same physical button. The design must specify clearly: does a long press of Send B momentarily turn on the Send B send for the selected track while Send B mode is active, or does it temporarily switch encoder mode to Send B? If both, define their interaction explicitly.

**Detection (warning signs):**
- No explicit statement in the design about what "momentary Send B" means
- After release, encoder mode and send enable state are inconsistent
- LED ambiguity: the mode button and the track send indicator conflict

**Phase:** Phase 2 — design clarification required before any code is written

---

## Part 3: Moderate Pitfalls

---

### Pitfall M1: `SpecialChanStripComponent.set_send_controls()` Calls `update()` — Triggers Full Strip Repaint

**What goes wrong:** `SpecialChanStripComponent.set_send_controls()` (line 22-26) calls `self.update()` whenever controls change. If Pan mode's implementation calls `set_send_controls(None, None, None)` on all 8 strips during mode teardown, then immediately calls `set_pan_control(control)` on each strip, 16 `update()` calls fire in a single mode switch. Each `update()` triggers LED and parameter state refreshes on all controls. This is a performance hit and may produce visible LED flicker.

**Why it happens:** The current mode 0 (Pan) path in `EncModeSelectorComponent.update()` already calls `set_pan_control()` and `set_send_controls()` on all 8 strips in a loop. Extending to 16 parameters adds more iteration without batching.

**Prevention:** Accept this as a known behavior of the existing architecture. Do not add additional unnecessary `set_send_controls()` / `set_pan_control()` calls beyond what the current loop already does. If flicker is observable, suppress LED updates during the mode transition by using `_suppress_send_midi` or batching all changes within a single `with self.component_guard():` block.

**Phase:** Phase 1 — awareness; Phase 2 if optimization is needed

---

### Pitfall M2: `ConfigurableButtonElement._pending_listeners` May Delay Send Toggle Registration

**What goes wrong:** `ConfigurableButtonElement.add_value_listener()` (line 45-49) defers listener registration if the button is notifying. If a send toggle handler is added while the button is in a notification cycle (e.g., during mode switch handling), the handler ends up in `_pending_listeners` and fires on the next notification rather than the current one. This means the send toggle handler may respond to the button press that followed the one that triggered registration.

**Why it happens:** This deferred listener pattern exists to prevent re-entrant listener modifications during notification. It is a correctness mechanism in `ConfigurableButtonElement`, which is the button type used for all global bank buttons (Send A/B/C). Adding listeners from within a value handler (e.g., enabling a component from within `EncModeSelectorComponent._mode_value`) triggers this deferred path.

**Prevention:** Do not add send toggle listeners from inside an active value listener of the same button. Set up listeners during initialization, before any MIDI arrives. If listeners need to be conditionally added based on mode, use `set_enabled(True/False)` on the component rather than adding/removing listeners dynamically.

**Detection (warning signs):**
- The first Send B press does nothing; the second press triggers the toggle (one-press delay)
- `add_value_listener` for the send toggle handler called inside another value handler for the same button

**Phase:** Phase 2

---

### Pitfall M3: Sends List May Be Empty or Shorter Than Expected

**What goes wrong:** `track.mixer_device.sends` is a list that varies in length depending on how many return tracks exist in the Live set. A set with no return tracks has an empty sends list. A set with one return track has sends of length 1. Accessing `sends[1]` or `sends[2]` for Send B or Send C control on a track in a minimal set causes IndexError.

**Why it happens:** The framework's `set_send_controls()` handles this gracefully by silently no-oping when the send index exceeds the list length. Direct attribute access (`track.mixer_device.sends[n].enabled`) does not share this safety.

**Prevention:** Guard every send access: `if len(self._track.mixer_device.sends) > send_index`. When the send does not exist, treat as a no-op: do not toggle, do not show LED, do not start the timer.

**Detection (warning signs):**
- IndexError in Live's Log.txt when pressing Send B or Send C on a track in a set with fewer than 2 or 3 return tracks
- No guard for `len(sends)` before accessing `sends[n]`

**Phase:** Phase 2

---

### Pitfall M4: Timer Leak If `_send_ticks_delay` Not Cleaned Up on Track Change

**What goes wrong:** v1.0's `ToggleMomentaryChannelStripComponent` correctly cleans up `_solo_ticks_delay` and `_mute_ticks_delay` in `set_solo_button()` and `set_mute_button()`. If send toggle timer variables are added, they must also be cleaned up when the track changes (i.e., when the channel strip is reassigned to a different track via `set_track()`). If not, the timer may fire for the wrong track.

**Why it happens:** `ChannelStripComponent.set_track()` changes `self._track` but does not reset custom state variables. Only the variables that belong to stock framework behaviors are handled by the parent. Custom `_send_ticks_delay` variables are invisible to the parent class.

**Prevention:** Override `set_track()` in the send toggle component and reset all active timer state before calling the parent. Pattern: check if a momentary is active, revert it on the old track, reset all delay counters, then call `SpecialChanStripComponent.set_track(self, track)`.

**Detection (warning signs):**
- After Ableton's track bank scrolls and reassigns strips to new tracks, the next timer tick fires a momentary revert on the new track (which was never pressed)
- `set_track()` is not overridden in the send toggle component

**Phase:** Phase 2

---

## Part 4: v1.0 Pitfalls (Carried Forward — Still Relevant as Regression Risks)

These pitfalls were identified for the Solo/Mute toggle/momentary work. They remain valid because the v1.1 Send toggle/momentary work follows the same pattern and can reproduce the same mistakes.

---

### Pitfall 1: Activating State at the Threshold Instead of at Press-Down

Apply state change immediately on press-down (`value != 0`). The timer only marks "threshold crossed." See v1.0 implementation in `ToggleMomentaryChannelStripComponent._handle_toggle_momentary()` — the state change is in the `if value != 0` branch, the timer starts in the same branch.

**Phase:** Phase 2 — send toggle implementation

---

### Pitfall 2: Forgetting to Unregister the Timer Callback in `disconnect()`

Every `_register_timer_callback` must have a paired `_unregister_timer_callback` in `disconnect()`. The v1.0 implementation correctly places this in `SpecialChanStripComponent.disconnect()` (line 19). Any new component managing send timers must follow the same pattern.

**Phase:** Phase 2 — any new component that uses a timer

---

### Pitfall 3: Using Wrong Override Point (`_on_send_changed` vs. value handler)

Send level changes fire framework callbacks. Per-send enable changes are not tracked by the framework. The send toggle logic belongs in the button's value handler, not in any change listener. There is no `_on_send_enabled_changed` in the framework — this must be registered manually as noted in Pitfall S4.

**Phase:** Phase 2

---

### Pitfall 4: Pre-Press State Captured at Release Instead of Press-Down

Store `sends[n].enabled` at press-down time. Use that stored value for the momentary revert at release. Do not re-read the live attribute at release time.

**Phase:** Phase 2

---

### Pitfall 5: Shift Guard Missing — Breaking Other Button Functions

Applies to sends: Send A/B/C buttons in shift mode are re-routed by `ShiftableEncoderSelectorComponent`. The send toggle handler must check `_shift_pressed` first. See Pitfall S5 for the specific interaction.

**Phase:** Phase 2

---

### Pitfall 6: Using Python `threading` Module

Not applicable to send toggles specifically, but the same prohibition applies. Use `_register_timer_callback`. Do not use `import threading`.

**Phase:** Phase 2

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1 — encoder dual-row design | Dual-assignment of encoders without release (Pitfall E1) | Call `release_parameter()` before every new `connect_to()` |
| Phase 1 — encoder row extension | Extending `EncModeSelectorComponent` to 16 controls (Pitfall E2) | Keep two separate components; do not pass 16-element tuple |
| Phase 1 — mode exit cleanup | Device encoder parameters not released on mode exit (Pitfall E3) | Pair every assign with a teardown release in the mode exit path |
| Phase 1 — timer interaction | Adding timer state to `EncModeSelectorComponent` (Pitfall E4) | Keep encoder mode component timer clean; separate concerns |
| Phase 1 — bank persistence | Device encoder bank index resets on mode switch (Pitfall E5) | Explicit bank lock in Pan mode activation |
| Phase 2 — send button dual role | Same button = mode switch AND send toggle (Pitfall S1) | Design decision required before code; document disambiguation rule |
| Phase 2 — API path verification | `track.send_a` does not exist (Pitfall S2) | Verify `track.mixer_device.sends[n].enabled` before any code |
| Phase 2 — send index coordination | Send toggle always uses wrong index (Pitfall S3) | Send toggle must receive send_index at call time, not infer it |
| Phase 2 — LED management | Send enable LED never updates (Pitfall S4) | Manual LED update + `add_enabled_listener` registration |
| Phase 2 — shift guard | Shift + Send A triggers send toggle (Pitfall S5) | `_shift_pressed` guard as first check in value handler |
| Phase 2 — release semantics | Mode latch + momentary revert conflict (Pitfall S6) | Design specification: what does "momentary Send B" mean? |
| Phase 2 — track reassignment | Timer fires for wrong track after bank scroll (Pitfall M4) | Override `set_track()`, reset all timer state before calling parent |

---

## Sources

**Codebase (verified, HIGH confidence):**
- `/Users/stoersignal/Dev/APC_64_40_12/EncModeSelectorComponent.py` — mode 0 (Pan) assigns `set_pan_control`, modes 1-3 assign `set_send_controls`; timer for `_pan_to_vol_ticks_delay` already present
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` lines 260-292 — `_global_param_controls` (8 encoders, CC 48-55) and `_global_bank_buttons` (CC notes 87-90) wired to `EncModeSelectorComponent`, `ChannelTranslationSelector`, `EncoderUserModesComponent`, `ShiftableEncoderSelectorComponent`
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` lines 200-219 — `device_param_controls` (8 device encoders, CC 16-23) wired to `ShiftableDeviceComponent`
- `/Users/stoersignal/Dev/APC_64_40_12/EncoderUserModesComponent.py` lines 116-128 — canonical pattern for releasing controls before mode switch and disabling sub-components
- `/Users/stoersignal/Dev/APC_64_40_12/ToggleMomentaryChannelStripComponent.py` — v1.0 implementation; reference for send toggle pattern
- `/Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py` line 22-26 — `set_send_controls()` calls `update()` on every change; confirmed via code
- `/Users/stoersignal/Dev/APC_64_40_12/SpecialMixerComponent.py` line 50 — `_create_strip()` returns `ToggleMomentaryChannelStripComponent`; all 8 strips are this type
- `/Users/stoersignal/Dev/APC_64_40_12/ConfigurableButtonElement.py` lines 45-49 — deferred listener queue pattern
- `/Users/stoersignal/Dev/APC_64_40_12/ShiftableEncoderSelectorComponent.py` lines 74-101 — shift toggle re-routes encoder bank buttons
- `.planning/codebase/CONCERNS.md` — Timer cleanup gap in `StepSequencerComponent`, wildcard imports, bare exceptions

**Framework source (verified, HIGH confidence):**
- `_Framework/ChannelStripComponent.py` — `set_send_controls()` maps encoders to send *level*, not send enable; no built-in send enable button support
- `_Framework/ControlSurfaceComponent.py` — `_register_timer_callback`, `_unregister_timer_callback`

---

*Pitfalls audit: 2026-03-31*
