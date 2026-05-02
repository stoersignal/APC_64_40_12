# APC40 Custom Control Surface

## What This Is

A customized APC40 MIDI control surface script for Ableton Live with toggle/momentary dual-behavior on Solo, Mute, and Send mode buttons, plus expanded 16-parameter encoder control in Pan mode. Short press toggles; long press (~400ms) acts momentary.

## Core Value

Controls must feel responsive and predictable — short taps toggle, longer holds act momentary, with feedback always reflecting real-time state.

## Requirements

### Validated

- ✓ APC40 control surface connects and communicates with Ableton Live — existing
- ✓ Track Solo/Mute buttons toggle state per track (8 tracks) — existing
- ✓ Button LEDs reflect current track state — existing
- ✓ Session, mixer, device, transport controls function — existing
- ✓ Shift-modified button behaviors work — existing
- ✓ Short press (<400ms) toggles Solo/Mute on/off — v1.0
- ✓ Long press (>=400ms) acts momentary for Solo/Mute — v1.0
- ✓ State fires immediately at press-down (zero latency) — v1.0
- ✓ Long press on already-active track temporarily inverts — v1.0
- ✓ Multi-track simultaneous holds work independently — v1.0
- ✓ Timer infrastructure correctly wired — v1.0
- ✓ Shift guards prevent stuck states — v1.0
- ✓ disconnect() reverts active momentary state — v1.0
- ✓ Pan mode: top 8 encoders map to device params 1-8 — v1.1
- ✓ Pan mode: device encoders map to device params 9-16 with bank nav — v1.1
- ✓ Encoder LED rings reflect parameter values in Pan mode — v1.1
- ✓ Parameters released on mode exit (no stale bindings) — v1.1
- ✓ Send A/B/C toggle/momentary mode switching — v1.1
- ✓ Send long press reverts to Pan mode on release — v1.1
- ✓ Send/Solo/Mute toggle/momentary operate independently — v1.1
- ✓ Tap Tempo + Nudge buttons save/recall rack macro snapshots — v1.2
- ✓ Shift+Tap Tempo save cancels when ramp encoders are touched — v1.2
- ✓ Ramp encoders interpolate between snapshots using absolute mapping over visible_macro_count — v1.2
- ✓ Lock-to-device moved from Tap Tempo to Shift+Nudge Back — v1.2

### Active

**v1.2 Documentation** — user manual for shipped controller features. See `.planning/REQUIREMENTS.md` (DOC-01..08).

### Out of Scope

- Track Activator (arm) buttons — user chose not to include
- Configurable threshold — fixed at ~400ms
- Exclusive-solo propagation — direct track.solo write, acceptable for timing focus
- Per-track Send A/B/C buttons — APC40 hardware has global mode selectors only

## Current Milestone: v1.2 Documentation

**Goal:** Ship a user manual that lets a non-developer install the script and operate every shipped controller feature without reading source code.

**Target features (documentation deliverables):**
- Installation & first-time setup (Win/Mac)
- Controller layout reference (interactive HTML with mode-repaint + static SVG fallback)
- Toggle/momentary unified model (Solo, Mute, Send)
- 16-macro Pan mode encoder mapping
- Rack macro variations save/recall (Tap Tempo + Nudge)
- Ramp encoders for variation interpolation
- Lock-to-device (Shift+Nudge Back)
- Step sequencer (64-step overlay engaged via Shift)
- Matrix modes (Clip Launch / Session Overview / Note-User Modes 1–6 with `Matrix_Maps.py` editing guide)
- Troubleshooting & known limitations

**Phases:** 1 (Phase 6: Create user manual)

## Context

Shipped v1.1 with:
- `ToggleMomentaryChannelStripComponent.py` — Solo/Mute toggle/momentary (95 LOC)
- `Pan16DeviceComponent.py` — Sequential parameter bank override (57 LOC)
- `EncModeSelectorComponent.py` — 16-param Pan mode + Send toggle/momentary (200 LOC)
- 80 tests across 6 test files, zero regressions
- Runtime bugfix for init ordering and ChannelTranslationSelector None crash

Post-v1.1 ad-hoc work (now scoped under v1.2 documentation):
- Rack macro snapshot save/recall reassigned to Tap Tempo + Nudge buttons
- Ramp function for rack variation interpolation (absolute encoder mapping)
- Lock-to-device relocated from Tap Tempo to Shift+Nudge Back

## Constraints

- **Runtime**: Ableton Live embedded Python — no external packages
- **Framework**: Ableton `_Framework` APIs for MIDI I/O and track state
- **Timing**: Press duration via 100ms timer ticks (LONG_PRESS_DELAY = 4)
- **Compatibility**: Must not break existing button behaviors
- **Hardware**: APC40 controller — fixed MIDI note/CC assignments

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ~400ms threshold (LONG_PRESS_DELAY=4) | 4 ticks at 100ms/tick, forgiving for fast fingers | ✓ Good |
| Fire state at press-down, not threshold | Zero latency on both short and long paths | ✓ Good |
| Shared helper via getattr/setattr | DRY — one method serves both solo and mute | ✓ Good |
| Sequential _parameter_banks() override | Framework's column-major interleaving gives wrong param order | ✓ Good |
| Two Pan16DeviceComponent instances | Bank 0 (top) + Bank 1 (device), independent registries | ✓ Good |
| Send long-press always reverts to Pan | Simpler than tracking previous mode, natural default | ✓ Good |
| Pan button keeps pan-to-vol toggle | Only Send A/B/C get momentary; Pan has its own behavior | ✓ Good |
| Exclusive-solo bypassed | Direct track.solo write, not base class iteration | ⚠️ Revisit if needed |

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
*Last updated: 2026-05-02 — v1.2 Documentation milestone scaffolded*
