# Domain Pitfalls: Toggle/Momentary Dual-Mode Button Behavior

**Domain:** MIDI control surface script — press-duration detection, state management, LED feedback
**Project:** APC40 Toggle/Momentary Button Behavior
**Researched:** 2026-03-31
**Overall confidence:** HIGH — verified against _Framework source at `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/` and existing codebase patterns in this project

---

## Critical Pitfalls

Mistakes that cause incorrect behavior, hard-to-reproduce bugs, or silent regressions.

---

### Pitfall 1: Activating State at the Threshold Instead of at Press-Down

**What goes wrong:** Implementation waits until the 400ms threshold fires before applying any state change. The button feels unresponsive — the action happens 400ms late, every time. Both short and long presses feel delayed.

**Why it happens:** It seems "clean" to wait until classification is complete before acting. But press-duration classification and state activation are separate concerns. The framework convention (confirmed in `_Framework/MomentaryModeObserver.py` and `_Framework/ModesComponent.py`) is always to act immediately on press and classify on release or after threshold — not the reverse.

**Consequences:**
- 400ms of perceived latency on every button press
- Long presses feel sluggish (the visual response should be instantaneous)
- Short press toggle also loses its immediacy

**Prevention:** Apply the state change immediately on press-down (`value != 0`). Start the timer at the same moment. The timer's role is only to mark "this press has now crossed the threshold" — not to trigger the action. The action already happened.

**Detection (warning signs):**
- During testing, pressing a button and counting "one Mississippi" before seeing the LED respond
- Logic that sets `track.solo = True` or `track.mute = True` inside `_on_timer` rather than in the value handler's `value != 0` branch

**Phase:** Core implementation (the single implementation phase for this milestone)

---

### Pitfall 2: Forgetting to Unregister the Timer Callback in `disconnect()`

**What goes wrong:** `_register_timer_callback` is called in `__init__` but the corresponding `_unregister_timer_callback` is not called in `disconnect()`. The timer continues firing after the component is destroyed. It may reference now-invalid track objects or a `None` internal state.

**Why it happens:** This is the exact bug already present in `StepSequencerComponent` (documented in `CONCERNS.md` — "Missing Timer Cleanup", line 84 registers `_on_timer`, `disconnect` does not show unregistration). It is easy to forget because Python does not warn about this — the callback just keeps running silently.

**Consequences:**
- Memory leak
- `_on_timer` fires and attempts to access `self._track`, which may be `None` after disconnect
- Phantom state updates — long-press state machine continues ticking after the script is no longer active
- AttributeError exceptions in the Live log after controller disconnects, making debugging difficult

**Prevention:** The pattern in `SpecialChanStripComponent` is correct — it pairs `_register_timer_callback` in `__init__` (line 16) with `_unregister_timer_callback` in `disconnect()` (line 19). Reproduce this pattern exactly. Never add a `_register_timer_callback` call without immediately writing its `_unregister_timer_callback` counterpart in `disconnect()`.

**Detection (warning signs):**
- Searching for `_register_timer_callback` in the modified file and not finding an equal number of `_unregister_timer_callback` calls
- Errors in Live's log file (`Log.txt`) after controller reconnect containing the timer callback's function name
- Ableton Live becoming slightly slower over repeated reconnects of the controller (timer firing rate increases)

**Phase:** Core implementation — must be in the initial implementation, not added later

---

### Pitfall 3: Overriding `_on_solo_changed` / `_on_mute_changed` Instead of the Value Handler

**What goes wrong:** Logic for toggle/momentary is placed in `_on_solo_changed` (the listener that fires when `track.solo` changes) instead of in `_solo_value` (the handler that fires when the physical button is pressed). This causes the logic to run on every external change to solo state, not just button presses.

**Why it happens:** `_on_solo_changed` and `_solo_value` have similar-sounding names. When reading `ChannelStripComponent.py`, a developer might confuse the two. `_on_solo_changed` fires when Ableton internally changes the track's solo state (e.g., via the GUI, via another controller, or via the script itself). `_solo_value` fires when MIDI value 127 or 0 arrives from the hardware button.

**Consequences:**
- The momentary/toggle logic runs twice per press (once when value arrives, once when track state propagates back through the listener)
- The logic also runs when other things change the solo state (automating solo, clicking in the GUI, CLIP launch scenes that affect solo), causing the state machine to fire unexpectedly
- Revert logic may undo external changes — if the user clicks solo in the Ableton GUI while the button has been pressed before, the release handler may revert that too

**Prevention:** The press-duration logic belongs in `_solo_value` / `_mute_value`. These are the correct override points. `_on_solo_changed` / `_on_mute_changed` exist solely to update LEDs and should be left alone unless LED behavior needs to change (which it does not — the existing automatic LED update path already works correctly).

**Detection (warning signs):**
- Any press-duration timer state variables being set inside `_on_solo_changed` or `_on_mute_changed`
- Momentary revert triggering unexpectedly when another track's solo changes (because exclusive-solo mode in Live fires `_on_solo_changed` on all tracks when one changes)
- Logic that reads `value` inside `_on_solo_changed` — this method receives no `value` argument; it reads `self._track.solo` directly

**Phase:** Core implementation

---

### Pitfall 4: Pre-Press State Not Captured at Button-Down

**What goes wrong:** The pre-press track state (what solo/mute was before the press) is captured at release time instead of at press-down time. If any intermediate event changes the track state while the button is held (automation, scene launch, another controller, exclusive-solo propagation), the release handler reverts to the wrong state.

**Why it happens:** "Capture state when I need it" (lazy capture) feels natural. The revert happens at release time, so it seems natural to read the current state at release time. But the "pre-press state" is a snapshot of the moment just before the button changed anything — that moment is press-down.

**Consequences:**
- Long-pressing solo on an unsoloed track, having a scene launch that solos another track (and unsoles everything else) during the hold, then releasing — the handler may incorrectly try to revert to a state that has already been changed by the scene launch
- Subtle, non-deterministic behavior that is hard to reproduce in testing but happens in live performance

**Prevention:** On button-down (`value != 0`), immediately read and store `self._track.solo` (for solo buttons) or `self._track.mute` (for mute buttons) into an instance variable (e.g., `self._solo_state_before_press`). Use this stored value at release time for the revert decision, not a fresh read.

**Detection (warning signs):**
- Instance variable for "pre-press state" being set in the release branch (`value == 0`) of the value handler
- Reading `self._track.solo` at release time to decide what state to restore
- Tests that involve external state changes during a hold failing unexpectedly

**Phase:** Core implementation

---

### Pitfall 5: Shift-Modified Solo/Mute Behavior Broken by New Value Handler

**What goes wrong:** The existing `_solo_value` and `_mute_value` override logic in `SpecialChanStripComponent` (or its parent `ChannelStripComponent`) already has a shift-button check. A new override that does not preserve this check breaks `shift + solo` and `shift + mute` functionality.

**Why it happens:** When overriding `_solo_value`, developers read only the parent class signature and forget to inspect the existing logic for shift handling. In this codebase, `ChannelStripComponent._solo_value` does not natively handle shift — the shift handling is added at the component level (via `strip.set_shift_button(self._shift_button)` in `APC_64_40_9.py` line 159). Looking at `SpecialChanStripComponent`, the `_select_value` method already shows the shift pattern (`self._select_button.is_momentary()`), which is the model to follow.

**Consequences:**
- Shift + Solo no longer performs its existing function (which in this script provides sequencer loop-length page control when the sequencer is active — `self._sequencer.set_loop_length_buttons(tuple(solo_buttons))` at `APC_64_40_9.py` line 191)
- Regression is invisible during simple testing but fails in any session that uses the step sequencer

**Prevention:** At the start of any new `_solo_value` / `_mute_value` override, check whether `_shift_pressed` is True and return early (or call through to existing behavior). Review `APC_64_40_9.py` lines 188-192 to understand that solo and mute buttons are also wired to the sequencer as `set_loop_length_buttons` and `set_loop_start_buttons`. The press-duration logic must only activate when shift is NOT pressed.

**Detection (warning signs):**
- Not having a `_shift_pressed` guard at the top of the new `_solo_value` / `_mute_value` implementation
- Step sequencer loop-length paging stops working after the change
- Integration testing that exercises shift + solo returns unexpected results

**Phase:** Core implementation — must be validated in the testing phase

---

### Pitfall 6: Using Python `threading` Module for Timer

**What goes wrong:** Using `import threading` and `threading.Timer(0.4, callback).start()` to implement the 400ms delay. This works in isolation but creates serious problems in the Live environment.

**Why it happens:** `threading.Timer` is the obvious Python way to "call a function after N seconds." The Remotify community documents threading as a viable approach for LED animations. It looks correct.

**Consequences:**
- The callback fires from a background thread, not from Live's main thread. All Live API calls (`track.solo`, `track.mute`) must be made from the main thread. Calling them from a thread causes either silent failure, a runtime crash, or corrupted state in Live's internal data model.
- The thread is not paused when the component is disabled (e.g., during shift mode, or when the script restarts). The callback fires regardless of component state.
- No built-in cleanup mechanism — threads that are created but whose callbacks fire after disconnect may reference freed objects.
- Live's embedded Python environment does not guarantee standard library thread behavior, and thread safety in this context is untested by the community.

**Prevention:** Use `_register_timer_callback` with a tick counter as documented in `STACK.md`. This runs on Live's main thread, is component-aware, and is already proven in this codebase. Do not use `threading` for timing.

**Detection (warning signs):**
- Any `import threading` in `SpecialChanStripComponent.py`
- Any `time.sleep()` call in a value handler
- Intermittent crashes in `Log.txt` mentioning thread context or Live API calls from non-main threads

**Phase:** Core implementation

---

## Moderate Pitfalls

Mistakes that cause incorrect behavior in specific edge cases. Not show-stoppers, but produce unprofessional results.

---

### Pitfall 7: Tick Counter Not Reset After Release

**What goes wrong:** The tick counter that tracks press duration (`_solo_press_ticks`) is not reset to a sentinel value (e.g., `-1`) after the button is released. On the next press, the counter starts from its previous value instead of zero, causing the threshold to be hit on a shorter press or a very short press to behave as a long press.

**Why it happens:** The reset step happens after the decision branch at release time and is easy to forget or to place in the wrong branch.

**Consequences:**
- Second press of the same button always triggers long-press behavior
- Threshold appears to "drift" — first press feels right, subsequent presses feel wrong
- Bug is masked if only one press is tested in isolation

**Prevention:** On release (`value == 0`), unconditionally reset the tick counter to its sentinel value (`-1` or `None`) as the last action in the handler, regardless of which branch (short or long press) was taken.

**Detection (warning signs):**
- Testing with two consecutive short presses: second press triggers momentary mode unexpectedly
- Counter variable not being set back to `-1` in the `value == 0` branch of the value handler

**Phase:** Core implementation

---

### Pitfall 8: LED Forced to Update Manually When Framework Already Handles It

**What goes wrong:** The implementation calls `self._solo_button.turn_on()` or `turn_off()` directly inside the value handler to update the LED. This creates two sources of truth for LED state: the script's manual calls and the framework's automatic `_on_solo_changed` listener.

**Why it happens:** The impulse to "make sure the LED is right" causes developers to add explicit LED calls. This seems harmless but creates race conditions and double-fires.

**Consequences:**
- LED flickers briefly as both updates land within the same tick
- Manual LED call fires before `track.solo` actually changes, showing incorrect state for one tick
- If `track.solo` assignment fails silently (e.g., track is in a state that prevents solo changes), LED shows the wrong state permanently because it was forced manually

**Prevention:** Trust the framework's automatic LED update path. `_on_solo_changed` fires automatically whenever `track.solo` changes (this is a Live listener registered in `ChannelStripComponent.__init__`). It calls `self._solo_button.turn_on()` / `turn_off()` based on the actual track state. Do not duplicate this. The only explicit LED calls needed are during momentary transitions if the framework's update path is somehow bypassed — and it should not be.

**Detection (warning signs):**
- Any `self._solo_button.turn_on()` or `self._solo_button.turn_off()` calls inside `_solo_value`
- Visible LED flicker on rapid presses (two updates in the same tick)

**Phase:** Core implementation

---

### Pitfall 9: Long-Press Inversion Logic Not Checking Current Track State

**What goes wrong:** The "long press on already-active state inverts" requirement means the behavior on press-down depends on the current track state. A naive implementation always applies the same action on press-down without checking whether the track is already in the active state. Long-pressing a soloed track then unsolos it (correct), but long-pressing an unsoloed track also unsolos it (already unsoloed — nothing happens, but no momentary solo activates).

**Why it happens:** Treating the press-down action as "always flip to active" (e.g., `track.solo = True`) rather than "flip away from current state" (e.g., `track.solo = not track.solo`).

**Consequences:**
- Long-pressing an already-muted track during performance to "temporarily unmute" it does nothing on press-down
- The feature requirement from `PROJECT.md` line 28 — "Long press on already-soloed/muted track temporarily inverts" — is not met

**Prevention:** On press-down, capture the pre-press state and apply its inverse. `new_state = not current_state`. This works uniformly for both cases: inactive track (activates), active track (deactivates). On release, restore the captured pre-press state.

**Detection (warning signs):**
- Code that sets `track.solo = True` unconditionally on press-down, rather than `track.solo = not self._solo_state_before_press`
- Testing the inversion case (long-pressing an already-soloed track) does not temporarily unsolo it

**Phase:** Core implementation

---

### Pitfall 10: State Machine Left in Inconsistent State on Component Disable

**What goes wrong:** A button is pressed (press-down received, state changed, timer started), and then the component is disabled mid-press (e.g., shift mode activates while the button is held). The component disable fires, but the button-release MIDI message may never be processed, leaving the press state machine in "holding" state permanently.

**Why it happens:** The Framework can call `set_enabled(False)` on a component at any time. MIDI messages received while the component is disabled are typically dropped by the framework's routing. So the press-down fires, the component disables, and the note-off is never delivered.

**Consequences:**
- On re-enable, the timer continues counting from where it stopped, and the next press immediately appears to be a "continuation" of the last one
- Track state may be stuck in the momentary-active condition (soloed/muted) because the release handler never fired to revert it

**Prevention:** Override `set_enabled()` (or respond in an existing `update()` or `on_enabled_changed()` method) to clean up any in-progress press state. If a press is in progress when the component disables, treat it as a release and revert any applied state. Reset the timer counter to its sentinel value.

**Detection (warning signs):**
- After pressing a button and then pressing Shift before releasing the button, subsequent behavior is wrong
- Timer counter has a non-sentinel value when the component starts up fresh (test by checking the counter value at `set_enabled(True)`)

**Phase:** Core implementation — consider the "shift pressed mid-hold" scenario explicitly in the test plan

---

## Minor Pitfalls

Mistakes that cause code quality issues, test fragility, or subtle bugs that appear rarely.

---

### Pitfall 11: Duplicating Timer Logic for Solo and Mute Instead of Abstracting

**What goes wrong:** Separate, near-identical tick counter variables and conditionals are written for each solo button and each mute button — 16 total per component instance. The `_on_timer` method becomes a long series of nearly identical blocks. When a bug is found, it must be fixed in every copy.

**Why it happens:** Each of the 8 `SpecialChanStripComponent` instances manages one track. So per-instance, there are only 2 variables (one for solo, one for mute) — this is actually fine. The risk is writing the timer handler as two large parallel blocks rather than extracting a helper method.

**Prevention:** Extract a helper: `_handle_press_timer(self, ticks_attr, long_press_attr)`. Call it twice in `_on_timer`. Keep the core logic in one place.

**Detection (warning signs):**
- `_on_timer` body contains near-duplicate blocks for solo and mute
- A fix applied to the solo logic does not get applied to the mute logic

**Phase:** Refactor opportunity — can be addressed at implementation or review

---

### Pitfall 12: Hardcoded Tick Count Instead of Named Constant

**What goes wrong:** `4` is used directly in `_on_timer` instead of a named constant like `LONG_PRESS_THRESHOLD_TICKS`. When the value needs to change (for tuning or the future configurable-threshold milestone), it requires tracking down a bare integer.

**Why it happens:** Quick coding. The concern from `CONCERNS.md` explicitly documents this as a tech debt pattern in this codebase ("Hardcoded Magic Numbers").

**Prevention:** Define `LONG_PRESS_THRESHOLD_TICKS = 4` at the module level in `SpecialChanStripComponent.py` alongside any related comment explaining the math (`4 ticks * 100ms/tick = 400ms`). This is consistent with `TRACK_FOLD_DELAY = 5` already defined at line 8 of the same file.

**Detection (warning signs):**
- A bare `4` compared against the tick counter in `_on_timer`
- No module-level constant documenting the relationship between ticks and milliseconds

**Phase:** Core implementation

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Core implementation: press-down action | Activating state at threshold instead of at press-down (Pitfall 1) | Write the state change in `value != 0` branch, before starting the timer |
| Core implementation: timer setup | Forgetting `_unregister_timer_callback` in `disconnect()` (Pitfall 2) | Write the disconnect call immediately when adding the register call |
| Core implementation: value handler override | Placing logic in `_on_solo_changed` instead of `_solo_value` (Pitfall 3) | Read `ChannelStripComponent.py` source before writing the override to confirm the correct method |
| Core implementation: pre-press state | Capturing state at release time instead of press-down (Pitfall 4) | The `_solo_state_before_press` assignment must be inside `if value != 0:`, not `else:` |
| Core implementation: shift compatibility | Breaking sequencer loop-length buttons by not guarding shift (Pitfall 5) | Add `if self._shift_pressed: return` (or equivalent) as the first line of the value handler |
| Core implementation: timing mechanism | Using threading instead of `_register_timer_callback` (Pitfall 6) | Do not import `threading` — this is non-negotiable |
| Testing: regression check | Shift + Solo and Shift + Mute behaviors must be tested explicitly | Test matrix: short press (solo off), short press (solo on), long press (solo off), long press (solo on), shift + solo |
| Testing: tick counter reset | Tick counter not resetting between presses (Pitfall 7) | Test two consecutive short presses on same button — second press must behave identically to first |
| Testing: component disable mid-press | State machine inconsistency on enable/disable (Pitfall 10) | Test: press button, press shift before releasing, release shift, press button again — all must behave correctly |

---

## Sources

**Framework source (verified, HIGH confidence):**
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/Defaults.py` — `TIMER_DELAY = 0.1`, `MOMENTARY_DELAY = 0.3`, `MOMENTARY_DELAY_TICKS = 3`
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ControlSurfaceComponent.py` — `_register_timer_callback`, `_unregister_timer_callback`
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ChannelStripComponent.py` — `_solo_value`, `_mute_value`, `_on_solo_changed`, `_on_mute_changed`
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/MomentaryModeObserver.py` — `_timer_count >= Defaults.MOMENTARY_DELAY_TICKS` tick-counting pattern (canonical example of how the framework detects momentary vs. toggle)

**Codebase evidence (verified, HIGH confidence):**
- `/Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py` — existing `_register_timer_callback` / `_unregister_timer_callback` pair (correct pattern to replicate)
- `/Users/stoersignal/Dev/APC_64_40_12/StepSequencerComponent.py` line 84 — timer registration without paired unregistration (the exact bug to avoid, documented in `CONCERNS.md`)
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` lines 151-159, 188-192 — solo and mute buttons wired to both mixer and sequencer (context for shift/sequencer compatibility)

**External (MEDIUM confidence — community practice, not official docs):**
- Ableton Forum: Python API timer callbacks at ~100ms resolution — https://forum.ableton.com/viewtopic.php?t=179893
- Remotify Community: Threading for timer animation in Ableton — threading approach documented but shown to carry Live API thread-safety risks — https://community.remotify.io/questions/question/found-a-way-to-use-timers-animation-with-ableton/
- Control-Surface GitHub Issue #235: LED state management for toggle vs momentary — https://github.com/tttapa/Control-Surface/issues/235

---

*Pitfalls audit: 2026-03-31*
