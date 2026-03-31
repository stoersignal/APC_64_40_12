# APC40 Toggle/Momentary Button Behavior

## What This Is

A modification to the APC40 MIDI control surface script for Ableton Live that adds dual-behavior (toggle/momentary) to Solo and Mute buttons. Short press toggles state on/off; long press (~400ms threshold) acts as momentary — activating on press-down and reverting on release.

## Core Value

Solo and Mute buttons must feel responsive and predictable — short taps toggle, longer holds act momentary, with LED feedback always reflecting the current real-time state.

## Requirements

### Validated

- ✓ APC40 control surface connects and communicates with Ableton Live — existing
- ✓ Track Solo buttons toggle solo state per track (8 tracks) — existing
- ✓ Track Mute buttons toggle mute state per track (8 tracks) — existing
- ✓ Button LEDs reflect current track state — existing
- ✓ Session, mixer, device, transport controls function — existing
- ✓ Shift-modified button behaviors work — existing
- ✓ ToggleMomentaryChannelStripComponent scaffolding in place — Phase 1
- ✓ Timer infrastructure correctly wired (register/unregister) — Phase 1
- ✓ Toggle/momentary state machine for Solo and Mute buttons — Phase 2
- ✓ Shared helper, shift guards, timer countdown — Phase 2
- ✓ LEDs update in real-time during momentary holds — Phase 2

### Active

- [ ] Solo buttons: short press (<400ms) toggles solo on/off
- [ ] Solo buttons: long press (>=400ms) activates momentary mode — solo on press-down, revert on release
- [ ] Mute buttons: short press (<400ms) toggles mute on/off
- [ ] Mute buttons: long press (>=400ms) activates momentary mode — mute on press-down, revert on release
- [ ] Long press on already-soloed/muted track temporarily inverts (unsolos/unmutes while held)
- [ ] LEDs update in real-time during momentary holds
- [ ] ~400ms threshold separates short from long press

### Out of Scope

- Track Activator (arm) buttons — user chose not to include these
- Configurable threshold — fixed at ~400ms for now
- Other button types (clip launch, transport, etc.)

## Context

- Brownfield project: modifying existing APC40 control surface script (APC_64_40_12)
- Python 3 codebase running inside Ableton Live 11/12 MIDI Remote Scripts framework
- Component-based architecture extending `_Framework.ControlSurface`
- Existing codebase map at `.planning/codebase/`
- Solo/Mute are currently pure toggle — each press flips state
- 8 tracks with individual Solo and Mute buttons
- The script uses `ConfigurableButtonElement` for dynamic button behavior and `ShiftableComponent` patterns

## Constraints

- **Runtime**: Must run within Ableton Live's embedded Python environment — no external packages
- **Framework**: Must use Ableton `_Framework` APIs for MIDI I/O and track state
- **Timing**: Press duration detection must be reliable within Live's MIDI processing loop
- **Compatibility**: Must not break existing button behaviors (shift-modified, etc.)
- **Hardware**: APC40 controller — fixed MIDI note/CC assignments

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ~400ms threshold for short/long | Forgiving for fast fingers, still clearly distinguishable from quick tap | — Pending |
| Long press inverts current state | More useful than "always activate" — lets you temporarily unsolo/unmute too | — Pending |
| Solo + Mute only (not Track Activator) | User's current scope — can extend later | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-31 after Phase 2 completion*
