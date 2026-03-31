# Roadmap: APC40 Toggle/Momentary Button Behavior

## Milestones

- ✅ **v1.0 Toggle/Momentary** — Phases 1-3 (shipped 2026-03-31) — [archive](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1 16Macros** — Phases 4-5 (in progress)

## Phases

<details>
<summary>✅ v1.0 Toggle/Momentary (Phases 1-3) - SHIPPED 2026-03-31</summary>

**Phases completed:** 3 phases, 3 plans, 6 tasks

Key accomplishments:
- ToggleMomentaryChannelStripComponent subclass created with six press-state variables, timer stub calling parent fold-delay logic first, and SpecialMixerComponent factory switched to new class
- Toggle/momentary state machine: press-down inversion, 4-tick countdown via _on_timer, release-time revert, shift guard in set_solo/mute_button — 43 unit tests all passing
- 18-test multi-track suite proves MULTI-01/02/03 per-instance isolation via two simultaneous strip instances; disconnect() hardened with momentary revert guards matching the set_solo_button() pattern

</details>

### 🚧 v1.1 16Macros (In Progress)

**Milestone Goal:** Expand encoder control to 16 device parameters via Pan mode and add toggle/momentary behavior to Send A/B/C mode buttons.

- [ ] **Phase 4: 16-Parameter Encoder Mapping** - Pan mode maps both encoder rows to device params 1-16 with clean teardown
- [ ] **Phase 5: Toggle/Momentary Send Mode Buttons** - Send A/B/C mode buttons gain short-press toggle / long-press momentary behavior

## Phase Details

### Phase 4: 16-Parameter Encoder Mapping
**Goal**: Pan mode simultaneously maps device parameters 1-8 to the top encoder row and parameters 9-16 to the device encoder row, with correct LED ring feedback and clean teardown on mode exit
**Depends on**: Phase 3 (v1.0 complete)
**Requirements**: ENC-01, ENC-02, ENC-03, ENC-04, ENC-05, ENC-06, ENC-07, MINT-01, MINT-02
**Success Criteria** (what must be TRUE):
  1. In Pan mode, turning any top encoder (CC 48-55) moves the corresponding device parameter 1-8 and the ring LED reflects the parameter value
  2. In Pan mode, turning any device encoder (CC 16-23) moves device parameter 9-16 and the ring LED reflects the parameter value
  3. Switching out of Pan mode (to Send A, B, or C) stops the encoders from affecting device parameters and rings return to normal
  4. Short-pressing Send A, B, or C from Pan mode switches to that mode without any stuck encoder connections (no regression on existing mode switching)
  5. The script loads in Ableton Live without errors after all Phase 4 changes
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — TDD: Pan16DeviceComponent with fixed-bank isolation tests
- [x] 04-02-PLAN.md — Wire: promote device_param_controls, instantiate Pan16 instances, add EncModeSelectorComponent setter
- [x] 04-03-PLAN.md — Implement: rewrite EncModeSelectorComponent.update() Pan mode routing + on_enabled_changed()

### Phase 5: Toggle/Momentary Send Mode Buttons
**Goal**: Send A/B/C mode buttons behave as toggle/momentary selectors — short press permanently selects the mode, long press activates while held and reverts to the previous mode on release, with shift guard and disconnect hardening matching v1.0
**Depends on**: Phase 4
**Requirements**: SEND-01, SEND-02, SEND-03, SEND-04, MINT-03
**Success Criteria** (what must be TRUE):
  1. Short press (< 400ms) on Send A, B, or C permanently switches encoder mode to that selection, identical to pre-v1.1 behavior
  2. Long press (>= 400ms) on Send A, B, or C activates that mode at press-down and reverts to the previously active mode when the button is released
  3. Mode activation on long press happens at the moment of press-down with no perceptible delay
  4. Holding Shift and pressing a Send mode button does not trigger momentary behavior
  5. Toggle/momentary Send mode behavior does not interfere with Solo/Mute toggle/momentary — both operate independently
**Plans**: 2 plans

Plans:
- [x] 05-01-PLAN.md — TDD: Send mode state machine (RED tests + GREEN implementation in EncModeSelectorComponent)
- [x] 05-02-PLAN.md — Verify: MINT-03 isolation tests confirming Send and Solo/Mute independence

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. State Machine | v1.0 | 1/1 | Complete | 2026-03-31 |
| 2. Hardening | v1.0 | 1/1 | Complete | 2026-03-31 |
| 3. Multi-Track Hardening | v1.0 | 1/1 | Complete | 2026-03-31 |
| 4. 16-Parameter Encoder Mapping | v1.1 | 2/3 | In Progress|  |
| 5. Toggle/Momentary Send Mode Buttons | v1.1 | 1/2 | In Progress|  |
