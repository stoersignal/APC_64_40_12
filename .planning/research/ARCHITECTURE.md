# Architecture Patterns

**Domain:** Toggle/Momentary button behavior in Ableton _Framework control surface script
**Researched:** 2026-03-31
**Confidence:** HIGH — based on direct source analysis of existing codebase

---

## Recommended Architecture

Add a new `ToggleMomentaryChannelStripComponent` class that extends the existing
`SpecialChanStripComponent`. All timing logic lives at the channel strip (per-track)
component level. The composition layer (`APC_64_40_9.py`) changes only the factory
method inside `SpecialMixerComponent`.

This mirrors the already-proven pattern used by `SpecialChanStripComponent` for
fold-delay detection and by `EncModeSelectorComponent` for press-and-hold mode
switching — both use the Framework's `_register_timer_callback` mechanism.

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `ToggleMomentaryChannelStripComponent` | Press-duration detection, solo/mute state inversion logic, LED feedback | `self._track.solo`, `self._track.mute`, parent `ChannelStripComponent` LED update chain |
| `SpecialMixerComponent` | Factory for per-track strips — override `_create_strip()` to return new class | `ToggleMomentaryChannelStripComponent` (8 instances) |
| `APC_64_40_9._setup_mixer_control()` | Wires `ButtonElement` instances to strips via `set_solo_button()` / `set_mute_button()` | `SpecialMixerComponent` — no change needed here |
| `ChannelStripComponent` (Framework base) | Owns `_solo_value()` and `_mute_value()` listener signatures; exposes `self._track` | Overridden by `ToggleMomentaryChannelStripComponent` |

No new top-level component file is required for the composition layer. The change
is self-contained inside the channel strip and mixer factory.

---

## Timing Mechanism

### Framework Timer Facts

`_register_timer_callback(self._on_timer)` fires the callback at the Framework's
`TIMER_DELAY` rate, which is **100ms per tick** (confirmed in
`_Framework/Defaults.py`: `TIMER_DELAY = 0.1`).

A 400ms threshold therefore equals **4 ticks**.

`_register_timer_callback` / `_unregister_timer_callback` is the standard in-codebase
mechanism. It is used in:
- `SpecialChanStripComponent` — fold delay (5 ticks = 500ms)
- `EncModeSelectorComponent` — Pan/Vol press-hold (5 ticks = 500ms)
- `DetailViewCntrlComponent` — show-playing-clip delay (5 ticks = 500ms)
- `StepSequencerComponent` — scroll repeat (4 tick initial, 1 tick interval)
- `CustomTransportComponent` — FF/Rewind repeat

The constant `TRACK_FOLD_DELAY = 5` in `SpecialChanStripComponent` is the direct
precedent. For this feature, define `LONG_PRESS_DELAY = 4` (400ms).

### Why Timer Ticks and Not `schedule_message`

`schedule_message(N, callback)` fires once after N ticks — appropriate for deferred
one-shot actions. For press-hold detection we need to measure elapsed ticks while
a button remains held: timer callback is correct. `schedule_message` cannot be
cancelled on release; the tick countdown approach can.

---

## Data Flow

### Short Press (toggle)

```
Hardware MIDI note-on  →  ButtonElement.receive_value(127)
  →  ChannelStripComponent._solo_value(127)          [inherited; records press-down]
  →  _press_ticks_remaining = LONG_PRESS_DELAY        [new state]

Hardware MIDI note-off →  ButtonElement.receive_value(0)
  →  OverriddenClass._solo_value(0)
     IF _press_ticks_remaining > 0:                   [still counting → short press]
       self._track.solo = not self._track.solo         [toggle]
       _press_ticks_remaining = -1                     [disarm]
```

### Long Press (momentary)

```
Hardware MIDI note-on  →  _solo_value(127)
  →  _press_ticks_remaining = LONG_PRESS_DELAY
  →  record _state_before_press = self._track.solo

_on_timer (tick 1..3):  _press_ticks_remaining > 0, decrement

_on_timer (tick 4):     _press_ticks_remaining == 0
  →  _momentary_active = True
  →  self._track.solo = not _state_before_press       [activate momentary inversion]
  →  LED update fires automatically via Live listener

Hardware MIDI note-off →  _solo_value(0)
  IF _momentary_active:
    self._track.solo = _state_before_press             [revert]
    _momentary_active = False
```

### LED State

`ChannelStripComponent` already listens to `self._track.solo_has_listener` and
calls `update()` on change — Live fires the listener when `self._track.solo` is
written. No additional LED code is needed beyond what the base class already does,
provided the override calls `ChannelStripComponent.update(self)` appropriately.

---

## Where Timing Logic Lives

**Component level — inside `ToggleMomentaryChannelStripComponent`.**

Rationale:
- Each track needs independent timing state (`_press_ticks_remaining`, `_momentary_active`,
  `_state_before_press`) because two tracks can be held simultaneously.
- `ChannelStripComponent` already holds `self._track`, which is the only API needed
  to read and write `.solo` / `.mute`.
- The Framework timer fires per-component (each instance registers its own callback).
- This avoids touching `SpecialMixerComponent`, `ShiftableSelectorComponent`, or the
  composition layer beyond the `_create_strip()` factory one-liner.

**Do not put timing logic in:**
- `SpecialMixerComponent` — it would require distributing per-track state across 8 index
  slots and polling them from a single timer; fragile and harder to test.
- `APC_64_40_9.py` (composition layer) — script setup; should only wire, not behave.
- `ConfigurableButtonElement` — element layer is stateless input abstraction; adding
  duration state there leaks domain logic into the UI element and breaks the element's
  reuse contract.
- A new top-level `*SelectorComponent` — unnecessary indirection; selectors coordinate
  multiple components, not individual button presses.

---

## Integration Points

### 1. `SpecialMixerComponent._create_strip()` — one-line change

```python
# Before
def _create_strip(self):
    return SpecialChanStripComponent()

# After
def _create_strip(self):
    return ToggleMomentaryChannelStripComponent()
```

Add the import at the top of `SpecialMixerComponent.py`. No other change needed.

### 2. `ToggleMomentaryChannelStripComponent` extends `SpecialChanStripComponent`

The new class:
- Calls `_register_timer_callback(self._on_timer)` in `__init__`
- Calls `_unregister_timer_callback(self._on_timer)` in `disconnect` (already called
  by parent's `disconnect` for its own timer, but the new class needs its own)
- Overrides `_solo_value(value)` and `_mute_value(value)` to intercept before
  delegating or replacing the base behaviour
- Adds `_on_timer()` that decrements tick counters per button

Note: `SpecialChanStripComponent` already registers a timer callback in `__init__` and
unregisters in `disconnect`. The `_on_timer` from that class handles fold delay.
The new `_on_timer` must incorporate or call the parent `_on_timer` logic, or the
new class must maintain its own separate callback. The safest approach: call
`SpecialChanStripComponent._on_timer(self)` from the new `_on_timer` to preserve
fold-delay behaviour, then add the press-duration logic.

### 3. Solo/Mute button assignment in `APC_64_40_9._setup_mixer_control()` — no change

Solo and mute buttons are created as `ButtonElement(is_momentary, ...)` and passed to
`strip.set_solo_button()` / `strip.set_mute_button()`. The `is_momentary=True` flag
ensures the Framework fires both note-on (value=127) and note-off (value=0) events —
which is required for press-duration detection. This is already correct.

### 4. `ShiftableSelectorComponent` — no change

In shift mode, `ShiftableSelectorComponent.update()` calls
`self._mixer.channel_strip(index).set_solo_button(None)` to disconnect buttons.
The new component inherits `set_solo_button` from `ChannelStripComponent`, so
disconnect/reconnect of the button works identically. Press-ticks state should be
reset when `set_solo_button(None)` is called — the override must handle this.
The reset ensures a button disconnected mid-hold does not fire a phantom toggle on
reconnect.

### 5. `StepSequencerComponent` — no change

The sequencer uses `mute_buttons` and `solo_buttons` tuples for its own lane-mute
and loop-length functions. These are the same `ButtonElement` objects, but the
sequencer calls `set_mute_button(None)` on the channel strips while active — so
the timer logic is naturally disabled during sequencer mode.

---

## Patterns to Follow

### Pattern: Tick-Countdown Press-Hold Detection

Established in `SpecialChanStripComponent` (fold delay) and `EncModeSelectorComponent`
(Pan/Vol mode switch). Structure:

```python
LONG_PRESS_DELAY = 4  # 4 ticks x 100ms = 400ms

class ToggleMomentaryChannelStripComponent(SpecialChanStripComponent):

    def __init__(self):
        SpecialChanStripComponent.__init__(self)
        # Solo press state
        self._solo_ticks_delay = -1
        self._solo_state_before_press = False
        self._solo_momentary_active = False
        # Mute press state (mirror for mute)
        self._mute_ticks_delay = -1
        self._mute_state_before_press = False
        self._mute_momentary_active = False
        # Note: SpecialChanStripComponent already registers its own timer
        # callback for fold delay. The parent __init__ handles that.
        # This class's _on_timer calls the parent's, then handles its own logic.

    def disconnect(self):
        SpecialChanStripComponent.disconnect(self)
        # State cleanup on disconnect
        self._solo_ticks_delay = -1
        self._mute_ticks_delay = -1

    def set_solo_button(self, button):
        # Reset timing state when button is reassigned (e.g., shift mode)
        self._solo_ticks_delay = -1
        self._solo_momentary_active = False
        ChannelStripComponent.set_solo_button(self, button)

    def set_mute_button(self, button):
        self._mute_ticks_delay = -1
        self._mute_momentary_active = False
        ChannelStripComponent.set_mute_button(self, button)

    def _solo_value(self, value):
        if self.is_enabled() and self._track is not None:
            if value != 0:  # press-down
                self._solo_state_before_press = self._track.solo
                self._solo_ticks_delay = LONG_PRESS_DELAY
            else:           # release
                if self._solo_momentary_active:
                    self._track.solo = self._solo_state_before_press
                    self._solo_momentary_active = False
                elif self._solo_ticks_delay >= 0:
                    self._track.solo = not self._track.solo
                self._solo_ticks_delay = -1
        # Do NOT call ChannelStripComponent._solo_value — we replace it entirely

    def _on_timer(self):
        SpecialChanStripComponent._on_timer(self)  # preserve fold-delay behaviour
        if self.is_enabled() and self._track is not None:
            # Solo countdown
            if self._solo_ticks_delay > -1:
                if self._solo_ticks_delay == 0:
                    self._solo_momentary_active = True
                    self._track.solo = not self._solo_state_before_press
                self._solo_ticks_delay -= 1
            # Mute countdown (same pattern)
            if self._mute_ticks_delay > -1:
                if self._mute_ticks_delay == 0:
                    self._mute_momentary_active = True
                    self._track.mute = not self._mute_state_before_press
                self._mute_ticks_delay -= 1
```

This is illustrative, not final production code — the pattern mirrors existing
components exactly.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Putting Timer in ButtonElement

**What:** Subclassing `ConfigurableButtonElement` or `ButtonElement` to track press duration.

**Why bad:** Element layer is a thin hardware abstraction. Duration is domain behaviour —
the same button (solo note 49, channel 0) already serves three different roles
(solo in normal mode, loop-length in sequencer mode, reassignment in shift mode). A
duration-aware element would fire toggle actions even when the button is being used
for sequencer functions.

**Instead:** Override the `_solo_value` / `_mute_value` listener in the component, where
the enabled/track context is available.

### Anti-Pattern 2: Single Timer in SpecialMixerComponent Managing All 8 Tracks

**What:** One `_on_timer` in `SpecialMixerComponent` with a list of 8 tick counters.

**Why bad:** Requires the mixer to know about press-duration logic, which is track-level
state. Adds coupling between the mixer container and the timing domain. Harder to reason
about when tracks are re-ordered or when only some strips are active.

**Instead:** Each `ChannelStripComponent` instance owns its own timer registration and
per-button state, which is how the Framework is designed.

### Anti-Pattern 3: Using `schedule_message` for Duration Detection

**What:** On press, call `schedule_message(4, self._on_long_press)` then cancel it
on release.

**Why bad:** `schedule_message` has no cancellation API in the Framework. The callback
will fire even after button release. This leads to phantom momentary activations on
short presses.

**Instead:** Use the tick-countdown pattern with the timer callback; release sets
`_ticks_delay = -1` which stops the countdown before threshold is reached.

### Anti-Pattern 4: Calling `ChannelStripComponent._solo_value` and Then Adding Logic

**What:** Call `super()._solo_value(value)` first, then add duration logic on top.

**Why bad:** The base `_solo_value` toggles `self._track.solo` immediately on press-down
(when `value != 0`). Calling it would fire the toggle instantly, then the timer logic
would revert it — double-fire behaviour and inconsistent LED state.

**Instead:** Replace `_solo_value` entirely in the override. Re-implement only the
`is_enabled()` / `self._track is not None` guards from the base.

---

## Scalability Considerations

| Concern | Current (8 tracks) | Future (if extended) |
|---------|--------------------|----------------------|
| Timer registrations | 8 per-strip registrations; Framework handles the list | Scales linearly; no change needed |
| Arm buttons (Track Activator) | Out of scope; same pattern would apply if added later | Third `_arm_ticks_delay` per strip |
| Configurable threshold | Fixed at 4 ticks (400ms); constant lives in new file | Move `LONG_PRESS_DELAY` to `Matrix_Maps.py` or a `Config.py` |
| Shift-mode safety | `set_solo_button(None)` resets state; covered by integration point 4 | No extra work needed |

---

## Suggested Build Order

This sequence minimises risk and makes each step independently verifiable by loading
the script in Ableton Live.

**Step 1 — New component file, no behaviour change yet**

Create `ToggleMomentaryChannelStripComponent.py` that extends `SpecialChanStripComponent`
with no overrides — just the class definition and a passthrough `__init__`. Change
`SpecialMixerComponent._create_strip()` to return it. Verify: script loads, all
existing buttons work identically.

**Step 2 — Timer scaffolding**

Add `_on_timer` registration to the new class. Add the tick-counter state variables.
Have `_on_timer` log a message each call (then remove logging). Verify: script loads,
no errors, no behaviour change.

**Step 3 — Solo toggle/momentary**

Override `_solo_value` for solo buttons only. Implement countdown → momentary path for
solo. Verify: solo short-press toggles; solo long-press activates while held and reverts
on release; LED tracks state correctly; shift mode still disconnects solo properly.

**Step 4 — Mute toggle/momentary**

Mirror the same logic for `_mute_value` and mute tick state. Verify: all four
behaviours (short/long x solo/mute) work; both buttons can be held simultaneously
on different tracks.

**Step 5 — Edge cases**

Test: long-press on already-soloed track (should temporarily un-solo); rapid presses
do not accumulate state; shift held during a solo long-press does not leave track in
wrong state; sequencer mode transitions do not leave stuck-high solo.

---

## Files to Create or Modify

| Action | File | Change |
|--------|------|--------|
| Create | `ToggleMomentaryChannelStripComponent.py` | New component, ~70-90 lines |
| Modify | `SpecialMixerComponent.py` | Import + `_create_strip()` one-liner |
| No change | `APC_64_40_9.py` | Wiring unchanged |
| No change | `ConfigurableButtonElement.py` | Element layer untouched |
| No change | `ShiftableSelectorComponent.py` | Button disconnect/reconnect already correct |
| Optional | `Matrix_Maps.py` | Add `LONG_PRESS_DELAY = 4` constant (or put in new file) |

---

## Sources

- Direct source analysis: `/Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py` — tick-countdown pattern (HIGH confidence)
- Direct source analysis: `/Users/stoersignal/Dev/APC_64_40_12/EncModeSelectorComponent.py` — press-hold mode selection (HIGH confidence)
- Direct source analysis: `/Users/stoersignal/Dev/APC_64_40_12/CustomTransportComponent.py` — register/unregister timer on press/release (HIGH confidence)
- Direct source analysis: `/Users/stoersignal/Dev/APC_64_40_12/ShiftableSelectorComponent.py` — button reconnection pattern in shift mode (HIGH confidence)
- Direct source analysis: `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` lines 134-195 — solo/mute button creation and wiring (HIGH confidence)
- [Ableton Live 11 MIDIRemoteScripts — _Framework/Defaults.py](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts) — `TIMER_DELAY = 0.1` (100ms per tick) (MEDIUM confidence — Live 11 source; Live 12 rate assumed unchanged)
- [_Framework ChannelStripComponent](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts/blob/master/_Framework/ChannelStripComponent.py) — `self._track.solo`, `self._track.mute` read/write pattern (MEDIUM confidence — Live 11 source; API stable)

---

*Architecture analysis: 2026-03-31*
