# Phase 2: Core Logic - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the full toggle/momentary state machine for both Solo and Mute buttons in `ToggleMomentaryChannelStripComponent`. Override `_solo_value` and `_mute_value` to intercept button press/release events, add tick countdown logic in `_on_timer`, and ensure LEDs reflect real-time state during momentary holds.

This phase delivers the core user-facing behavior: short press toggles, long press acts momentary. All 8 tracks must work correctly.

</domain>

<decisions>
## Implementation Decisions

### State Machine Flow
- **D-01:** Toggle immediately on press-down — state change fires at button press, not at threshold. Zero latency on all paths.
- **D-02:** On release: if `_ticks_delay > 0` (less than 400ms held), state stays toggled (short press = toggle). If `_ticks_delay <= 0` (reached threshold), revert to `_state_before_press` (long press = momentary revert).
- **D-03:** Strict threshold boundary — if released before tick count reaches 0, it's a toggle. No fuzzy grace window.
- **D-04:** Press-down starts the tick countdown at `LONG_PRESS_DELAY` (4). Timer decrements each tick. At 0, the press is classified as "long" for release behavior.

### Already-Active Handling
- **D-05:** Same pattern for already-active tracks — press-down always inverts current state immediately. If track is already soloed, press-down unsolos. Release after threshold restores solo. Release before threshold keeps unsolo (toggle off).
- **D-06:** Short press on already-soloed/muted track toggles it off (unsolo/unmute) — same as current behavior, no special casing.

### Shift Button Guard
- **D-07:** Basic reset guard when `set_solo_button(None)` or `set_mute_button(None)` is called mid-hold: reset tick counter to -1, if `_momentary_active` is True revert state to `_state_before_press`, set `_momentary_active = False`. Prevents stuck states from shift transitions.

### Implementation Split
- **D-08:** Shared helper method `_handle_toggle_momentary(value, track_property, ticks_attr, state_attr, momentary_attr)` called by both `_solo_value` and `_mute_value`. DRY — one place to fix bugs.
- **D-09:** `_on_timer` also uses shared approach: check both solo and mute tick counters, decrement if active.

### LED Feedback
- **D-10:** No additional LED code needed — framework's `_on_solo_changed`/`_on_mute_changed` listeners fire automatically when `track.solo`/`track.mute` changes, updating LEDs in real-time. Confirmed in Phase 1 research.

### Claude's Discretion
- Method parameter naming and internal variable naming within the shared helper
- Whether to use `getattr`/`setattr` or explicit attribute access in the helper
- Comment style within the new methods

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Implementation Target
- `ToggleMomentaryChannelStripComponent.py` — The file to modify. Phase 1 scaffolding with state variables and _on_timer stub already in place.

### Parent Classes (must understand before overriding)
- `SpecialChanStripComponent.py` — Direct parent. Has `_on_timer` for fold delay, `_select_value` pattern.
- `_Framework/ChannelStripComponent` — Grandparent. Contains `_solo_value`, `_mute_value`, `_on_solo_changed`, `_on_mute_changed` that Phase 2 overrides.

### Shift Wiring
- `ShiftableSelectorComponent.py` — Calls `set_solo_button(None)` when shift pressed. The guard in D-07 must hook into this.

### Research
- `.planning/research/ARCHITECTURE.md` — Override targets, integration points
- `.planning/research/PITFALLS.md` — Timing pitfalls, state machine edge cases
- `.planning/research/FEATURES.md` — Fire-at-press-down pattern rationale

### Phase 1 Context
- `.planning/phases/01-scaffolding/01-CONTEXT.md` — Decisions D-01 through D-06 (class design, timer, state vars)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ToggleMomentaryChannelStripComponent.py` lines 17-23: All six state variables already initialized (`_solo_ticks_delay`, `_solo_state_before_press`, `_solo_momentary_active` + mute mirrors)
- `LONG_PRESS_DELAY = 4` constant already defined at line 8
- `_on_timer` already calls parent at line 32 — add tick countdown after that call

### Established Patterns
- `ChannelStripComponent._solo_value(self, value)`: Called with MIDI value (0 = release, >0 = press). Toggles `self._track.solo`. This is the method to override.
- `ChannelStripComponent._mute_value(self, value)`: Same pattern for mute, toggles `self._track.mute`.
- Track state access: `self._track.solo` (bool, read/write), `self._track.mute` (bool, read/write)
- Button check: `self._solo_button.is_momentary()` returns True for APC40 buttons

### Integration Points
- Override `_solo_value` and `_mute_value` — do NOT call super (parent does pure toggle which conflicts)
- Override `set_solo_button` and `set_mute_button` — add reset guard before calling super
- Extend `_on_timer` — add tick countdown logic after existing parent call

</code_context>

<specifics>
## Specific Ideas

- The state machine is symmetrical: press-down inverts current state, timer counts down, release either keeps (short) or reverts (long). This symmetry means the same logic works for both "activating" and "deactivating" — no need to check current state differently.
- `getattr`/`setattr` may be useful in the shared helper to avoid duplicating attribute access code for solo vs mute.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-core-logic*
*Context gathered: 2026-03-31*
