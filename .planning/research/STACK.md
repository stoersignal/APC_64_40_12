# Technology Stack: Press-Duration Detection

**Project:** APC40 Toggle/Momentary Button Behavior
**Milestone:** Add dual-behavior (short press / long press) to Solo and Mute buttons
**Researched:** 2026-03-31
**Overall confidence:** HIGH — all claims verified against decompiled _Framework source at `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/`

---

## Timer Mechanism

### How the tick system works

Ableton Live's C++ host drives the `_Framework` task system. The root `TaskGroup` is updated by Live at a fixed rate defined in `_Framework/Defaults.py`:

```python
TIMER_DELAY = 0.1        # seconds per tick — 100ms
MOMENTARY_DELAY = 0.3    # seconds — 300ms (3 ticks)
MOMENTARY_DELAY_TICKS = int(MOMENTARY_DELAY / TIMER_DELAY)  # = 3
```

**Confidence: HIGH** — verified in `_Framework/Defaults.py` (source timestamp 2025-03-17).

Each "tick" is approximately 100ms. This is not user-configurable and not dependent on audio buffer size or tempo.

### What "~400ms threshold" means in ticks

400ms / 100ms per tick = **4 ticks**. Use a constant:

```python
LONG_PRESS_DELAY = 4  # ticks at 100ms each = ~400ms
```

---

## The Two Viable Approaches

### Approach 1: `_register_timer_callback` with tick counter (RECOMMENDED)

This is the **same pattern already used in `SpecialChanStripComponent`** — the `_toggle_fold_ticks_delay` mechanism. It is proven in-project, does not require any new imports, and is compatible with the existing class hierarchy.

**How it works:**

1. Register a timer callback in `__init__` — it fires every tick (100ms).
2. On button press-down (`value != 0`): record that button is held, start a counter.
3. On each timer tick: if button is held, increment counter.
4. If counter reaches threshold (4 ticks = 400ms): the press is "long" — activate momentary behavior immediately.
5. On button release (`value == 0`): check whether a long press was in progress.
   - If long press was in progress: revert the momentary state (release the hold).
   - If timer never reached threshold: treat as short press — toggle.

**API:**

```python
# In __init__:
self._register_timer_callback(self._on_timer)

# In disconnect:
self._unregister_timer_callback(self._on_timer)

# In value listener:
def _solo_value(self, value):
    if value != 0:
        self._solo_press_ticks = 0   # start counting
        self._solo_long_press_active = False
        # Apply state immediately for momentary — will revert if short press on release
        self._apply_solo_on_press()
    else:
        self._on_solo_released()

# Timer fires every ~100ms:
def _on_timer(self):
    if self._solo_press_ticks >= 0:   # -1 means no press in progress
        self._solo_press_ticks += 1
        if self._solo_press_ticks == LONG_PRESS_DELAY:
            self._solo_long_press_active = True
            # already applied on press-down; LED is correct
```

**Confidence: HIGH** — `_register_timer_callback` / `_unregister_timer_callback` are confirmed API methods on `ControlSurfaceComponent` (`ControlSurfaceComponent.py` lines 161-172). Their internals use `Task.FuncTask` on the parent task group, ticked at `TIMER_DELAY = 0.1s`.

**Why this approach over alternatives:**
- No new imports needed.
- Already proven working in this exact codebase (`SpecialChanStripComponent._on_timer`).
- Single callback handles all 8 solo buttons and 8 mute buttons efficiently if the per-strip counters are instance variables.
- Minimal surface area — does not touch the Framework's button routing or MIDI map.

---

### Approach 2: `self._tasks.add(Task.sequence(Task.wait(...), ...))` (VIABLE ALTERNATIVE)

This is the pattern used in `pushbase`, `ModesComponent`, and Ableton's own internal long-press detection.

**How it works:**

```python
from _Framework import Task

# In __init__ (create task, start killed):
self._solo_long_press_task = self._tasks.add(
    Task.sequence(
        Task.wait(0.4),           # 400ms in seconds
        Task.run(self._on_solo_long_press)
    )
)
self._solo_long_press_task.kill()

# On press-down:
self._solo_long_press_task.restart()
self._apply_solo_on_press()

# On release:
if self._solo_long_press_task.is_running:
    # Task hasn't fired — short press
    self._solo_long_press_task.kill()
    self._handle_solo_short_press()
# else: long press already handled by task callback
```

**Confidence: HIGH** — confirmed in `_Framework/ModesComponent.py` line 514 and `pushbase/loop_selector_component.py` line 80. `Task.wait` takes seconds. `self._tasks` is a `lazy_attribute` on `ControlSurfaceComponent` that creates a `TaskGroup` on first access.

**Why this is an alternative, not the primary recommendation:**
- `self._tasks` is a `lazy_attribute` that requires the `@depends(parent_task_group=None)` injection chain to be active. It works, but accessing it before `register_component` has run causes a runtime error. The existing codebase (`SpecialChanStripComponent`) deliberately does NOT use `self._tasks` — it uses `_register_timer_callback` instead. Staying consistent with the existing pattern is lower risk.
- One task object per button (16 total for 8 solo + 8 mute) is manageable but adds more state to track in `disconnect()`.

---

## What NOT to Use

### `time.time()` or `time.monotonic()`

**Do not use Python's wall-clock time functions for press duration.**

Ableton's embedded Python environment does include standard `time` module access, but using `time.time()` for press duration detection creates problems:

- You would need to store the press timestamp and compute elapsed time in the release handler. This works, but it runs outside the _Framework task system and is not paused/resumed when the component is disabled.
- More importantly: the _Framework timer system is the correct abstraction layer. Using wall-clock time bypasses it and creates two different timing systems in the same component.

**Confidence: MEDIUM** — `time` module availability confirmed by community practice; the architectural argument against it is reasoning, not an official restriction.

### `schedule_message` (on `ControlSurface`)

**Do not use `self.schedule_message()`** for this feature.

`schedule_message` is defined on `ControlSurface`, not on `ControlSurfaceComponent`. `SpecialChanStripComponent` does not have access to it directly. It is designed for one-shot deferred calls (e.g., delaying hardware updates after a state change), not for press-duration tracking. Using it would require the component to hold a reference to the top-level surface, which violates the existing architectural boundary.

**Confidence: HIGH** — verified by reading `ControlSurface.py` and confirming `ControlSurfaceComponent` does not inherit from `ControlSurface`.

### `_Framework.ButtonElement` subclassing to add timing

**Do not add timing logic to `ConfigurableButtonElement` or a new `ButtonElement` subclass.**

Timing belongs in the component, not the element. Elements are stateless MIDI I/O wrappers. The existing codebase follows this separation strictly — `ConfigurableButtonElement` handles MIDI value routing and LED state only. Adding press-duration state to an element would break the component/element boundary and make the element non-reusable.

**Confidence: HIGH** — this is a direct reading of the existing architecture.

---

## Where the Code Lives

**File to modify:** `SpecialChanStripComponent.py`

This is the correct place because:
- It already owns the solo and mute value handler methods (`_solo_value` is inherited from `ChannelStripComponent` and needs to be overridden here).
- It already has `_register_timer_callback` / `_unregister_timer_callback` wired up — `_on_timer` exists and is called every tick.
- Each `SpecialChanStripComponent` instance corresponds to exactly one track, so instance variables like `_solo_press_ticks` map cleanly to per-track state.

**No other files should need modification** for the core behavior. LED feedback calls (`_solo_button.turn_on()` / `.turn_off()`) are already in `ChannelStripComponent._on_solo_changed()`, which is triggered by Live's property change notification whenever `track.solo` changes — so LED updates happen automatically when the Live track state changes.

---

## Key API Summary

| API | Location | Purpose | Confidence |
|-----|----------|---------|------------|
| `_register_timer_callback(fn)` | `ControlSurfaceComponent` | Register function called every ~100ms tick | HIGH |
| `_unregister_timer_callback(fn)` | `ControlSurfaceComponent` | Remove timer callback (call in `disconnect()`) | HIGH |
| `_on_timer()` (override) | `SpecialChanStripComponent` | Existing hook, already fires every tick | HIGH |
| `track.solo` (read/write) | `Live.Track` | Read or set solo state | HIGH |
| `track.mute` (read/write) | `Live.Track` | Read or set mute state | HIGH |
| `self._tasks` | `ControlSurfaceComponent` | Alternative: task group for `Task.wait`-based timing | HIGH |
| `Task.wait(seconds)` | `_Framework/Task.py` | Wait task consuming real-time seconds | HIGH |
| `Defaults.TIMER_DELAY` | `_Framework/Defaults.py` | Tick rate constant (0.1 seconds) | HIGH |

---

## Tick Rate Calculation Reference

| Desired threshold | Ticks required | Formula |
|------------------|---------------|---------|
| 300ms (Framework default `MOMENTARY_DELAY`) | 3 | 0.3 / 0.1 |
| 400ms (project requirement) | 4 | 0.4 / 0.1 |
| 500ms | 5 | 0.5 / 0.1 |

With `_register_timer_callback`, use tick counting. With `self._tasks + Task.wait()`, pass seconds directly (e.g., `Task.wait(0.4)`).

---

## Sources

- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/Defaults.py` — `TIMER_DELAY = 0.1`, `MOMENTARY_DELAY = 0.3` (source timestamp 2025-03-17)
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ControlSurfaceComponent.py` — `_register_timer_callback`, `_unregister_timer_callback`, `_tasks` lazy attribute
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/Task.py` — `WaitTask`, `FuncTask`, `TaskGroup`, `sequence`, `wait`
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ChannelStripComponent.py` — `_solo_value`, `_mute_value`, `_on_solo_changed`, `_on_mute_changed`
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ModesComponent.py` — `add_mode` using `Task.sequence(Task.wait(MOMENTARY_DELAY), ...)` pattern
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/MomentaryModeObserver.py` — `_timer_count >= Defaults.MOMENTARY_DELAY_TICKS` tick-counting pattern
- `/Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py` — existing `_register_timer_callback` / `_on_timer` usage in this codebase
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/pushbase/loop_selector_component.py` — `self._tasks.add(task.sequence(task.wait(...)))` pattern
