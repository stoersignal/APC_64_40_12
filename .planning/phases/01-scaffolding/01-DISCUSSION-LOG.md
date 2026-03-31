# Phase 1: Scaffolding - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 1-Scaffolding
**Areas discussed:** Class design, Timer approach, State variables

---

## Class Design

| Option | Description | Selected |
|--------|-------------|----------|
| New subclass (Recommended) | New file ToggleMomentaryChannelStripComponent.py inheriting from SpecialChanStripComponent — keeps original untouched, clean separation | ✓ |
| Modify in-place | Add toggle/momentary logic directly into SpecialChanStripComponent.py — simpler, but mixes concerns | |
| You decide | Claude picks the best approach based on codebase patterns | |

**User's choice:** New subclass (Recommended)
**Notes:** None

---

## Timer Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Extend _on_timer (Recommended) | Override _on_timer, call super()._on_timer() for fold delay, add tick counting for solo/mute. One timer callback handles both. | ✓ |
| Separate timer callback | Register a second timer callback for press-duration tracking. Two independent timers per strip. | |
| You decide | Claude picks based on _Framework patterns | |

**User's choice:** Extend _on_timer (Recommended)
**Notes:** None

---

## State Variables

| Option | Description | Selected |
|--------|-------------|----------|
| Tick counters + state snapshot (Recommended) | Per-button: _solo_ticks_delay (countdown like fold delay), _solo_state_before_press (bool to restore on release). Mirror for mute. Matches existing TRACK_FOLD_DELAY pattern. | ✓ |
| Timestamp-based | Store press-down timestamp, calculate duration on release. Simpler but doesn't use the established tick pattern. | |
| You decide | Claude picks the approach that best fits existing codebase patterns | |

**User's choice:** Tick counters + state snapshot (Recommended)
**Notes:** None

## Claude's Discretion

- Import style and module docstring format

## Deferred Ideas

None
