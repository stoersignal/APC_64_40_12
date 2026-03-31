# APC40 Custom Control Surface

## What This Is

A customized APC40 MIDI control surface script for Ableton Live with toggle/momentary dual-behavior on Solo, Mute, and Send buttons, plus expanded 16-parameter encoder control. Short press toggles state on/off; long press (~400ms threshold) acts as momentary.

## Current Milestone: v1.1 16Macros

**Goal:** Expand encoder control to 16 device parameters via Pan mode and add toggle/momentary to Send A/B/C buttons

**Target features:**
- Pan mode maps top 8 encoders to device parameters 1-8
- Pan mode maps device encoders to device parameters 9-16
- Send A/B/C per-track buttons get toggle/momentary dual-behavior (reuse v1.0 pattern)

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
- ✓ Short press (<400ms) toggles Solo/Mute on/off — v1.0
- ✓ Long press (>=400ms) acts momentary for Solo/Mute — v1.0
- ✓ State fires immediately at press-down (zero latency) — v1.0
- ✓ Long press on already-active track temporarily inverts — v1.0
- ✓ LEDs update in real-time during momentary holds — v1.0
- ✓ Multi-track simultaneous holds work independently — v1.0
- ✓ Timer infrastructure correctly wired (register/unregister) — v1.0
- ✓ Shift guards prevent stuck states on mid-hold button reassignment — v1.0
- ✓ disconnect() reverts active momentary state — v1.0

### Active

- [ ] Pan mode: top 8 encoders map to device parameters 1-8
- [ ] Pan mode: device encoders map to device parameters 9-16
- [ ] Send A button: toggle/momentary dual-behavior per track
- [ ] Send B button: toggle/momentary dual-behavior per track
- [ ] Send C button: toggle/momentary dual-behavior per track
- [ ] Send toggle/momentary uses same ~400ms threshold and shift guards as Solo/Mute

### Out of Scope

- Track Activator (arm) buttons — user chose not to include these
- Configurable threshold — fixed at ~400ms for now
- Other button types (clip launch, transport, etc.)
- Exclusive-solo propagation — direct track.solo write bypasses base class exclusive-solo; acceptable for timing focus

## Context

Shipped v1.0 with 95 LOC implementation + 836 LOC tests (61 tests).
Tech stack: Python 3, Ableton _Framework, ControlSurface component hierarchy.
Single new file (`ToggleMomentaryChannelStripComponent.py`) + one-line factory swap.
Shift guards and disconnect hardening added for live performance reliability.

## Constraints

- **Runtime**: Must run within Ableton Live's embedded Python environment — no external packages
- **Framework**: Must use Ableton `_Framework` APIs for MIDI I/O and track state
- **Timing**: Press duration detection must be reliable within Live's MIDI processing loop
- **Compatibility**: Must not break existing button behaviors (shift-modified, etc.)
- **Hardware**: APC40 controller — fixed MIDI note/CC assignments

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ~400ms threshold (LONG_PRESS_DELAY=4) | 4 ticks at 100ms/tick, forgiving for fast fingers | ✓ Good |
| Long press inverts current state | More useful than "always activate" — temporary unsolo/unmute | ✓ Good |
| Solo + Mute only (not Track Activator) | User's scope — can extend later | ✓ Good |
| Fire state at press-down, not threshold | Zero latency on both short and long paths | ✓ Good |
| Shared helper via getattr/setattr | DRY — one method serves both solo and mute | ✓ Good |
| No super() in _solo_value/_mute_value | Parent does pure toggle which conflicts with timing logic | ✓ Good |
| Exclusive-solo bypassed | Direct track.solo write, not base class iteration | ⚠️ Revisit if exclusive-solo needed |

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
*Last updated: 2026-03-31 after v1.1 milestone start*
