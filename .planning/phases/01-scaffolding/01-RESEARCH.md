# Phase 1: Scaffolding - Research

**Researched:** 2026-03-31
**Domain:** Ableton Live _Framework control surface component subclassing and timer infrastructure
**Confidence:** HIGH — all findings verified directly against project source files

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Create a new file `ToggleMomentaryChannelStripComponent.py` inheriting from `SpecialChanStripComponent` — keeps original untouched, clean separation of concerns
- **D-02:** Swap factory in `SpecialMixerComponent._create_strip()` to return `ToggleMomentaryChannelStripComponent()` instead of `SpecialChanStripComponent()`
- **D-03:** Override `_on_timer` in the new subclass, calling `SpecialChanStripComponent._on_timer(self)` (super) to preserve existing fold-delay behavior — one timer callback handles both fold delay and press-duration tracking
- **D-04:** No new timer registration needed — the existing `_register_timer_callback(self._on_timer)` from `SpecialChanStripComponent.__init__` will dispatch to the overridden method
- **D-05:** Use tick counters matching existing `TRACK_FOLD_DELAY` pattern: `_solo_ticks_delay` (countdown, -1 = inactive), `_solo_state_before_press` (bool snapshot to restore on release). Mirror for mute: `_mute_ticks_delay`, `_mute_state_before_press`
- **D-06:** Define `LONG_PRESS_DELAY = 4` constant (400ms at 100ms/tick) matching the `TRACK_FOLD_DELAY = 5` pattern

### Claude's Discretion

- Import style and module docstring format — follow existing conventions in the codebase

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INTG-02 | Timer callback properly cleaned up on disconnect (no phantom callbacks) | Parent `SpecialChanStripComponent` already shows the correct paired pattern: `_register_timer_callback` in `__init__` (line 16) and `_unregister_timer_callback` in `disconnect()` (line 19). D-04 confirms no new registration — the overridden `_on_timer` fires via the parent's registration. No additional register/unregister call is needed. Disconnect implementation should call `SpecialChanStripComponent.disconnect(self)` which already unregisters. |
| INTG-03 | Script loads and initializes without errors after modification | Requires exactly two code changes: (1) new file `ToggleMomentaryChannelStripComponent.py`, (2) import + one-line change in `SpecialMixerComponent._create_strip()`. The new class must pass-through `__init__` to parent and initialize the six state variables before Phase 2 adds behavioral logic. |
</phase_requirements>

---

## Summary

Phase 1 is a scaffolding change with zero new user-visible behavior. It creates the class hierarchy and state variables that Phase 2 will fill in. The two deliverables are: (1) a new file containing `ToggleMomentaryChannelStripComponent` that extends `SpecialChanStripComponent` with state variables and an `_on_timer` override that calls the parent, and (2) a one-line change in `SpecialMixerComponent._create_strip()` plus its import.

The critical insight for the timer: decision D-04 means no new `_register_timer_callback` call is made. The parent `SpecialChanStripComponent.__init__` already calls `_register_timer_callback(self._on_timer)`. Because Python method dispatch is virtual, this registration refers to `self._on_timer` at call time — so when the new subclass overrides `_on_timer`, the Framework will call the overridden version. This is the correct and safe approach, matching the existing fold-delay mechanism.

The new class's `disconnect()` simply calls `SpecialChanStripComponent.disconnect(self)`, which already unregisters the callback (line 19 of `SpecialChanStripComponent.py`). No additional unregistration is needed. State variable cleanup (setting counters to -1) in `disconnect()` is defensive hygiene for Phase 2.

**Primary recommendation:** Create the minimal new class with state variables and a pass-through `_on_timer`, swap the factory, verify the script loads in Live with all existing behavior intact — then stop.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `_Framework.ChannelStripComponent` | Bundled with Live 11/12 | Grandparent class providing `_solo_value`, `_mute_value`, `set_solo_button`, `set_mute_button`, `_track` reference | Framework base; all channel strip components in this codebase descend from it |
| `_Framework.EncoderElement` | Bundled with Live 11/12 | Already imported by parent — import carried through | Used by `set_send_controls`, `set_pan_control`, `set_volume_control` overrides in parent |

### No New Dependencies

This phase requires no new imports beyond what `SpecialChanStripComponent` already imports. The new file needs only:

```python
from .SpecialChanStripComponent import SpecialChanStripComponent
```

---

## Architecture Patterns

### Relevant Project Structure

```
APC_64_40_12/
├── SpecialChanStripComponent.py     # Parent class — READ BEFORE WRITING
├── SpecialMixerComponent.py         # Factory to modify — line 48 and import section
├── ToggleMomentaryChannelStripComponent.py   # CREATE THIS
└── APC_64_40_9.py                   # No change needed
```

### Pattern 1: _on_timer Override with Super Call

The parent `SpecialChanStripComponent._on_timer` handles fold delay. The new `_on_timer` must call it first, then add its own logic. The parent's `_register_timer_callback(self._on_timer)` in `__init__` will dispatch to the subclass version via Python's normal method resolution.

```python
# Source: SpecialChanStripComponent.py (direct source read, HIGH confidence)
def _on_timer(self):
    if (self.is_enabled() and (self._track != None)):
        if (self._toggle_fold_ticks_delay > -1):
            assert self._track.is_foldable
            if (self._toggle_fold_ticks_delay == 0):
                self._track.fold_state = (not self._track.fold_state)
            self._toggle_fold_ticks_delay -= 1
```

The new override:
```python
def _on_timer(self):
    SpecialChanStripComponent._on_timer(self)  # preserve fold-delay behaviour
    # Phase 1: no additional logic yet (state vars initialized, counters at -1)
```

### Pattern 2: Tick-Countdown State Variables

Exact model from parent at module level and `__init__`:

```python
# Source: SpecialChanStripComponent.py lines 8 and 15
TRACK_FOLD_DELAY = 5
# ...
self._toggle_fold_ticks_delay = -1
```

New file follows this pattern:

```python
LONG_PRESS_DELAY = 4  # 4 ticks x 100ms/tick = 400ms

class ToggleMomentaryChannelStripComponent(SpecialChanStripComponent):

    def __init__(self):
        SpecialChanStripComponent.__init__(self)
        self._solo_ticks_delay = -1
        self._solo_state_before_press = False
        self._mute_ticks_delay = -1
        self._mute_state_before_press = False
```

### Pattern 3: disconnect() Cleanup

```python
# Source: SpecialChanStripComponent.py lines 18-20
def disconnect(self):
    self._unregister_timer_callback(self._on_timer)
    ChannelStripComponent.disconnect(self)
```

The new class's `disconnect()` calls the parent, which already handles timer unregistration:

```python
def disconnect(self):
    self._solo_ticks_delay = -1
    self._mute_ticks_delay = -1
    SpecialChanStripComponent.disconnect(self)  # unregisters timer
```

### Pattern 4: Factory Method

```python
# Source: SpecialMixerComponent.py line 48-49 (direct source read, HIGH confidence)
# Before:
def _create_strip(self):
    return SpecialChanStripComponent()

# After:
def _create_strip(self):
    return ToggleMomentaryChannelStripComponent()
```

Add at top of `SpecialMixerComponent.py` after the existing `SpecialChanStripComponent` import:
```python
from .ToggleMomentaryChannelStripComponent import ToggleMomentaryChannelStripComponent
```

### Pattern 5: File Header Convention

Existing files in this codebase use this header style (from `SpecialChanStripComponent.py`):
```python
# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-
```

The new file should follow this same header pattern.

### Anti-Patterns to Avoid

- **Adding a second `_register_timer_callback` call:** D-04 is explicit — the parent's registration already dispatches to the overridden `_on_timer`. Adding a second call would result in `_on_timer` firing twice per tick.
- **Calling `_unregister_timer_callback` in the new class's `__init__` before calling `super().__init__`:** The callback is not registered yet; this would either fail or be a no-op, but indicates confused intent. Always init parent first.
- **Using `super()` syntax:** The existing codebase consistently uses explicit parent calls (`SpecialChanStripComponent.__init__(self)`) rather than `super().__init__()`. Follow the established pattern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timer firing at 100ms intervals | Custom threading.Timer or time.sleep | `_register_timer_callback` (inherited from parent's `__init__`) | Threading is unsafe in Live's main thread; `_register_timer_callback` is main-thread, already proven in this codebase |
| Press-duration countdown | Custom polling loop or schedule_message | Tick-counter decrement in `_on_timer` | `schedule_message` has no cancellation API; tick counter can be disarmed by setting to -1 on button release |

**Key insight:** The Framework's timer mechanism is already wired in. Phase 1 inherits it for free through the parent's `__init__`. No new infrastructure needs to be built.

---

## Common Pitfalls

### Pitfall 1: Adding a Second Timer Registration

**What goes wrong:** Adding `self._register_timer_callback(self._on_timer)` in the new class's `__init__` when the parent already does this. Because the Framework stores callbacks in a list, `_on_timer` fires twice per tick.
**Why it happens:** It looks like "the new class needs to register its timer." But the registration already exists from the parent.
**How to avoid:** Decision D-04 is explicit. Do not add a `_register_timer_callback` call. Verify by searching the new file for `_register_timer_callback` after writing — it must appear zero times.
**Warning signs:** Timer-driven logic fires at double speed during testing.

### Pitfall 2: Forgetting to Call Parent in `_on_timer`

**What goes wrong:** `_on_timer` override handles new tick counters but does not call `SpecialChanStripComponent._on_timer(self)`. The fold-delay behavior in the parent silently stops working.
**Why it happens:** Override replaces rather than extends.
**How to avoid:** First line of the new `_on_timer` must always be `SpecialChanStripComponent._on_timer(self)`. Decision D-03 is explicit.
**Warning signs:** Track fold (expand/collapse group tracks) no longer delays after the change.

### Pitfall 3: Phantom Timer Callback After Reconnect

**What goes wrong:** Timer continues firing after the component is destroyed because `disconnect()` does not call `SpecialChanStripComponent.disconnect(self)`, which is the method that calls `_unregister_timer_callback`.
**Why it happens:** Implementing a custom `disconnect()` that only cleans up new state variables and forgets to call the parent.
**How to avoid:** The new `disconnect()` should call `SpecialChanStripComponent.disconnect(self)` — the parent handles timer unregistration.
**Warning signs:** Live log (`Log.txt`) shows timer callback errors after controller reconnect.

### Pitfall 4: Script Fails to Load Due to Import Error

**What goes wrong:** New file created but import in `SpecialMixerComponent.py` is wrong (wrong path, wrong class name, typo).
**Why it happens:** The import style in this project uses relative dot notation (`from .ClassName import ClassName`). Using an absolute import or wrong module path causes an `ImportError` at Live startup.
**How to avoid:** Match the existing import style: `from .ToggleMomentaryChannelStripComponent import ToggleMomentaryChannelStripComponent`. Filename must exactly match class name.
**Warning signs:** Live log shows `ImportError` or `ModuleNotFoundError`; the control surface script fails to appear in Live's MIDI preferences.

---

## Code Examples

### Verified Patterns from Direct Source Reads

#### Complete SpecialChanStripComponent (parent to inherit from)

```python
# Source: /Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py (HIGH confidence)
from _Framework.ChannelStripComponent import ChannelStripComponent
from _Framework.EncoderElement import EncoderElement
TRACK_FOLD_DELAY = 5

class SpecialChanStripComponent(ChannelStripComponent):
    ' Subclass of channel strip component using select button for (un)folding tracks '
    __module__ = __name__

    def __init__(self):
        ChannelStripComponent.__init__(self)
        self._toggle_fold_ticks_delay = -1
        self._register_timer_callback(self._on_timer)

    def disconnect(self):
        self._unregister_timer_callback(self._on_timer)
        ChannelStripComponent.disconnect(self)
    # ...
    def _on_timer(self):
        if (self.is_enabled() and (self._track != None)):
            if (self._toggle_fold_ticks_delay > -1):
                assert self._track.is_foldable
                if (self._toggle_fold_ticks_delay == 0):
                    self._track.fold_state = (not self._track.fold_state)
                self._toggle_fold_ticks_delay -= 1
```

#### Factory method to modify

```python
# Source: /Users/stoersignal/Dev/APC_64_40_12/SpecialMixerComponent.py line 48 (HIGH confidence)
# Current state:
def _create_strip(self):
    return SpecialChanStripComponent()

# Phase 1 target:
def _create_strip(self):
    return ToggleMomentaryChannelStripComponent()
```

#### New file skeleton (Phase 1 deliverable)

```python
# http://remotescripts.blogspot.com

# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-

from .SpecialChanStripComponent import SpecialChanStripComponent

LONG_PRESS_DELAY = 4  # 4 ticks x 100ms/tick = 400ms

class ToggleMomentaryChannelStripComponent(SpecialChanStripComponent):
    ' Channel strip subclass with toggle/momentary dual-behavior for solo and mute buttons '
    __module__ = __name__

    def __init__(self):
        SpecialChanStripComponent.__init__(self)
        # Solo press state (Phase 2 will use these)
        self._solo_ticks_delay = -1
        self._solo_state_before_press = False
        # Mute press state (Phase 2 will use these)
        self._mute_ticks_delay = -1
        self._mute_state_before_press = False
        # Note: timer registration is inherited from SpecialChanStripComponent.__init__
        # Do NOT add _register_timer_callback here (D-04)

    def disconnect(self):
        self._solo_ticks_delay = -1
        self._mute_ticks_delay = -1
        SpecialChanStripComponent.disconnect(self)  # handles timer unregistration

    def _on_timer(self):
        SpecialChanStripComponent._on_timer(self)  # preserve fold-delay (D-03)
        # Phase 2 will add solo/mute tick countdown logic here
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python 2 syntax (`print` statements, `has_key()`) | Python 3 compatible | Live 11 migration | Code is already Python 3; use Python 3 style in new file |
| `super()` with arguments | Explicit parent calls (`ParentClass.method(self)`) | N/A — project convention | Use explicit parent call style throughout |

---

## Open Questions

1. **`__module__ = __name__` necessity**
   - What we know: Present in `SpecialChanStripComponent` and several other classes in this codebase. It is a Python 2 pattern for correct module path display in tracebacks.
   - What's unclear: Whether it has any functional effect in Python 3 / Live 12. It is harmless but may be vestigial.
   - Recommendation: Include it in the new class to match the parent class pattern. Convention consistency outweighs the uncertainty.

2. **`_solo_momentary_active` and `_mute_momentary_active` variables**
   - What we know: The ARCHITECTURE.md code sketch includes these flags. They are needed in Phase 2 for the momentary revert path.
   - What's unclear: Whether to initialize them in Phase 1 (scaffolding) or Phase 2 (behavior).
   - Recommendation: Initialize them in `__init__` during Phase 1 alongside the other state variables (`self._solo_momentary_active = False`, `self._mute_momentary_active = False`). They are zero-cost and make the Phase 2 plan cleaner by not requiring a `__init__` edit.

---

## Sources

### Primary (HIGH confidence)

- `/Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py` — direct source read: timer registration pattern, `_on_timer` tick countdown, `TRACK_FOLD_DELAY` constant, `disconnect()` cleanup
- `/Users/stoersignal/Dev/APC_64_40_12/SpecialMixerComponent.py` — direct source read: `_create_strip()` factory at line 48, import section structure, relative import style
- `.planning/phases/01-scaffolding/01-CONTEXT.md` — locked implementation decisions D-01 through D-06
- `.planning/research/ARCHITECTURE.md` — component boundaries, data flow, timer mechanism analysis, integration points, code sketch
- `.planning/research/PITFALLS.md` — pitfall catalogue with verified Framework source citations

### Secondary (MEDIUM confidence)

- `.planning/research/ARCHITECTURE.md` cites `_Framework/Defaults.py` at `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/` confirming `TIMER_DELAY = 0.1` (100ms per tick) — not re-verified directly in this research pass, but cited by prior research with source path

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — read directly from source files
- Architecture: HIGH — all patterns verified against existing project source
- Pitfalls: HIGH — two pitfalls (double-registration, missing parent `_on_timer` call) are novel to this phase; others are from the verified PITFALLS.md

**Research date:** 2026-03-31
**Valid until:** Stable — no external dependencies; only invalidated if `SpecialChanStripComponent.py` or `SpecialMixerComponent.py` is modified
