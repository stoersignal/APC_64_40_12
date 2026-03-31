# Phase 5: Toggle/Momentary Send Mode Buttons - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Add toggle/momentary dual-behavior to Send A, Send B, and Send C mode buttons in `EncModeSelectorComponent`. Short press (<400ms) permanently switches encoder mode (existing behavior). Long press (>=400ms) activates mode at press-down and reverts to Pan mode (mode 0) on release. Pan button keeps its existing pan-to-vol toggle behavior unchanged.

</domain>

<decisions>
## Implementation Decisions

### Timer Unification
- **D-01:** Single counter replaces `_pan_to_vol_ticks_delay`: new `_send_ticks_delay` (countdown, -1 = inactive), `_send_momentary_active` (bool), `_mode_before_send_press` (int, stores mode index before press). Only one mode button can be held at a time.
- **D-02:** Reuse `LONG_PRESS_DELAY = 4` constant (same 400ms threshold as v1.0 Solo/Mute). Import or define locally.
- **D-03:** Keep existing `_pan_to_vol_ticks_delay` / `_mode_is_pan` logic for Pan button (mode 0). Send buttons (modes 1-3) use the new `_send_ticks_delay` mechanism.

### Previous Mode Tracking
- **D-04:** Long press on Send A/B/C always reverts to Pan mode (mode 0) on release. No need to store previous mode — hardcoded revert target.
- **D-05:** Short press behavior unchanged: `set_mode(index)` permanently switches to that mode.

### Pan Button Behavior
- **D-06:** Pan button (mode 0) keeps its existing long-press pan-to-vol toggle behavior. NOT converted to toggle/momentary. Only Send A/B/C (modes 1-3) get the new behavior.

### State Machine (mirrors v1.0 pattern)
- **D-07:** Press-down on Send A/B/C (value != 0): immediately `set_mode(index)` (zero latency). Start `_send_ticks_delay = LONG_PRESS_DELAY`.
- **D-08:** Release on Send A/B/C (value == 0): if `_send_momentary_active` is True, revert to Pan mode (`set_mode(0)`), set `_send_momentary_active = False`. Reset `_send_ticks_delay = -1` unconditionally.
- **D-09:** Timer countdown: when `_send_ticks_delay` reaches 0, set `_send_momentary_active = True`. Decrement to -1 (disarmed).

### Shift Guard
- **D-10:** When shift is pressed (component disabled via `on_enabled_changed`), reset `_send_ticks_delay = -1` and if `_send_momentary_active`, revert to Pan mode. Prevents stuck modes.

### Claude's Discretion
- Whether to define `LONG_PRESS_DELAY` locally or import from `ToggleMomentaryChannelStripComponent`
- Exact placement of new state variables in `__init__`
- Whether the existing `_mode_value` method is extended or a new handler wraps it

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Implementation Target
- `EncModeSelectorComponent.py` — The file to modify. Already has `_on_timer`, `_mode_value`, `_pan_to_vol_ticks_delay`. Timer is registered.

### v1.0 Pattern Reference
- `ToggleMomentaryChannelStripComponent.py` — The proven toggle/momentary pattern. `_handle_toggle_momentary` shows the state machine. `LONG_PRESS_DELAY = 4` constant.

### Phase 4 Context
- `.planning/phases/04-16-parameter-encoder-mapping/04-CONTEXT.md` — Phase 4 decisions. Pan mode now routes to device params, not per-track pan. `on_enabled_changed()` already added.

### Research
- `.planning/research/ARCHITECTURE.md` — `EncModeSelectorComponent._on_timer` integration point
- `.planning/research/STACK.md` — Timer unification recommendation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EncModeSelectorComponent._on_timer` — Already registered and ticking. Has `_pan_to_vol_ticks_delay` countdown. Add `_send_ticks_delay` countdown alongside it.
- `EncModeSelectorComponent._mode_value(value, sender)` — Button press handler. `value != 0` = press, `value == 0` = release. `sender.is_momentary()` check exists.
- `_pan_to_vol_ticks_delay` pattern — Exact model for `_send_ticks_delay`: set to N on press, decrement per tick, fire at 0, -1 = inactive.

### Established Patterns
- Mode switching: `self.set_mode(index)` + `self.update()` handles all routing
- Button identification: `self._modes_buttons.index(sender)` gives mode index (0=Pan, 1=SendA, 2=SendB, 3=SendC)
- Timer: 100ms ticks, countdown pattern proven

### Integration Points
- `_mode_value()` — Add release handling for modes 1-3 (currently only fires on press-down)
- `_on_timer()` — Add `_send_ticks_delay` countdown block after existing `_pan_to_vol_ticks_delay` block
- `__init__()` — Add 3 new state variables
- `disconnect()` — Reset state variables
- `on_enabled_changed()` — Add send momentary revert (Phase 4 already added this method)

</code_context>

<specifics>
## Specific Ideas

- The implementation is a near-direct transposition of the v1.0 pattern but simpler: only one counter (not per-track), hardcoded revert target (mode 0), and the timer infrastructure already exists.
- `_mode_value` currently ignores release events (`value == 0` with `sender.is_momentary()` returns early). The release branch needs to be added for modes 1-3 only.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-toggle-momentary-send-mode-buttons*
*Context gathered: 2026-03-31*
