# Roadmap: APC40 Toggle/Momentary Button Behavior

## Overview

A focused brownfield modification to one Python file and one new file in the APC40 control surface script. The work scaffolds a new component class, wires it into the existing factory, then implements the full dual-mode state machine for Solo and Mute buttons. A final hardening phase validates edge cases required for live performance reliability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Scaffolding** - Create the new component class with passthrough behavior and verify the existing script loads cleanly with the timer callback infrastructure in place
- [ ] **Phase 2: Core Logic** - Implement the full toggle/momentary state machine for both Solo and Mute buttons with correct LED feedback and shift guard
- [ ] **Phase 3: Hardening** - Verify multi-track simultaneous holds and edge cases required for live performance reliability

## Phase Details

### Phase 1: Scaffolding
**Goal**: The new component class exists, is wired into the factory, and the script loads in Live with all existing behavior intact and the timer infrastructure correctly registered and unregistered
**Depends on**: Nothing (first phase)
**Requirements**: INTG-02, INTG-03
**Success Criteria** (what must be TRUE):
  1. Script loads in Ableton Live without errors after adding the new class and changing the factory method
  2. All existing button behaviors (solo toggle, mute toggle, shift-modified actions) work identically to before the change
  3. The timer callback registers on instantiation and unregisters on disconnect — no phantom callbacks after device reconnect
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md — Create ToggleMomentaryChannelStripComponent class and wire factory

### Phase 2: Core Logic
**Goal**: Short press toggles and long press acts momentary for both Solo and Mute buttons across all 8 tracks, with LEDs reflecting real-time state and no regression on short presses
**Depends on**: Phase 1
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06, CORE-07, LED-01, LED-02, INTG-01
**Success Criteria** (what must be TRUE):
  1. A quick tap (<400ms) on a Solo or Mute button toggles that track's state on/off — identical to pre-modification behavior
  2. Holding a Solo or Mute button (>=400ms) activates the state immediately at press-down and reverts to the pre-press state on release — with no 400ms delay in the activation
  3. Holding a Solo button on an already-soloed track temporarily unsolos that track while held; releasing restores solo
  4. Holding a Mute button on an already-muted track temporarily unmutes that track while held; releasing restores mute
  5. The Solo and Mute button LEDs reflect the actual track state in real time throughout a momentary hold
**Plans**: TBD

### Phase 3: Hardening
**Goal**: The feature works reliably under simultaneous multi-track holds and edge cases encountered in live performance: rapid presses, shift pressed mid-hold, exclusive-solo propagation, and component disable mid-press
**Depends on**: Phase 2
**Requirements**: MULTI-01, MULTI-02, MULTI-03
**Success Criteria** (what must be TRUE):
  1. Holding Solo on two different tracks simultaneously solos both tracks and reverts both independently on release
  2. Holding Mute on two different tracks simultaneously mutes both tracks and reverts both independently on release
  3. Holding Solo on one track and Mute on a different track simultaneously produces correct independent momentary behavior on each
  4. Rapid consecutive short presses do not accumulate tick counts or leave the state machine in a stuck state
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffolding | 0/1 | Not started | - |
| 2. Core Logic | 0/TBD | Not started | - |
| 3. Hardening | 0/TBD | Not started | - |
