# Phase 1: Scaffolding - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a new `ToggleMomentaryChannelStripComponent` class that inherits from `SpecialChanStripComponent`, wire it into the factory method in `SpecialMixerComponent._create_strip()`, and verify the script loads in Ableton Live with all existing behavior intact. Timer infrastructure is registered and properly cleaned up on disconnect.

This phase delivers zero new behavior — it's a scaffolding change that sets up the class hierarchy and timer infrastructure for Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Class Design
- **D-01:** Create a new file `ToggleMomentaryChannelStripComponent.py` inheriting from `SpecialChanStripComponent` — keeps original untouched, clean separation of concerns
- **D-02:** Swap factory in `SpecialMixerComponent._create_strip()` to return `ToggleMomentaryChannelStripComponent()` instead of `SpecialChanStripComponent()`

### Timer Approach
- **D-03:** Override `_on_timer` in the new subclass, calling `SpecialChanStripComponent._on_timer(self)` (super) to preserve existing fold-delay behavior — one timer callback handles both fold delay and press-duration tracking
- **D-04:** No new timer registration needed — the existing `_register_timer_callback(self._on_timer)` from `SpecialChanStripComponent.__init__` will dispatch to the overridden method

### State Variables
- **D-05:** Use tick counters matching existing `TRACK_FOLD_DELAY` pattern: `_solo_ticks_delay` (countdown, -1 = inactive), `_solo_state_before_press` (bool snapshot to restore on release). Mirror for mute: `_mute_ticks_delay`, `_mute_state_before_press`
- **D-06:** Define `LONG_PRESS_DELAY = 4` constant (400ms at 100ms/tick) matching the `TRACK_FOLD_DELAY = 5` pattern

### Claude's Discretion
- Import style and module docstring format — follow existing conventions in the codebase

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Component Pattern
- `SpecialChanStripComponent.py` — The parent class. Shows timer registration/unregistration pattern, `_on_timer` tick countdown, `TRACK_FOLD_DELAY` constant, `_toggle_fold_ticks_delay` state variable
- `SpecialMixerComponent.py` — Contains `_create_strip()` factory method at line 48. Single line to modify

### Framework Base
- `_Framework/ChannelStripComponent` — Grandparent class. Contains `_solo_value`, `_mute_value`, `_on_solo_changed`, `_on_mute_changed` that Phase 2 will override

### Research
- `.planning/research/ARCHITECTURE.md` — Full integration analysis, component boundaries, build order
- `.planning/research/STACK.md` — Timer API details, tick rate confirmation (100ms)
- `.planning/research/PITFALLS.md` — Timer cleanup in disconnect(), phantom callback prevention

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SpecialChanStripComponent`: Already has timer infrastructure (`_register_timer_callback`, `_unregister_timer_callback`, `_on_timer`). New class inherits all of this.
- `TRACK_FOLD_DELAY = 5` constant pattern: Exact model for `LONG_PRESS_DELAY = 4`

### Established Patterns
- Timer tick countdown: Set delay to N, decrement each tick, fire action at 0, set to -1 when inactive
- `disconnect()` must call `_unregister_timer_callback` before `super().disconnect()` — already done in parent, but new class should NOT re-register a separate callback (inherits parent's registration)
- Class naming: `PascalCase` with descriptive suffix (`*Component`, `*Element`)
- File naming: One class per file, filename matches class name

### Integration Points
- `SpecialMixerComponent._create_strip()` line 48 — single return statement to change
- `SpecialMixerComponent.py` import section — add import for new class
- `__init__.py` — no changes needed (factory handles instantiation)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — this is pure scaffolding following established patterns. The tick counter + state snapshot approach mirrors the existing fold-delay mechanism exactly.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-scaffolding*
*Context gathered: 2026-03-31*
