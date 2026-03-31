# Requirements: APC40 Toggle/Momentary Button Behavior

**Defined:** 2026-03-31
**Core Value:** Solo and Mute buttons must feel responsive and predictable — short taps toggle, longer holds act momentary, with LED feedback always reflecting the current real-time state.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Behavior

- [x] **CORE-01**: Short press (<400ms) on Solo button toggles solo state on/off
- [x] **CORE-02**: Long press (>=400ms) on Solo button acts momentary — solo activates on press-down, reverts on release
- [x] **CORE-03**: Short press (<400ms) on Mute button toggles mute state on/off
- [x] **CORE-04**: Long press (>=400ms) on Mute button acts momentary — mute activates on press-down, reverts on release
- [x] **CORE-05**: State change fires immediately at press-down (no classification delay)
- [x] **CORE-06**: Long press on already-soloed track temporarily unsolos while held, restores on release
- [x] **CORE-07**: Long press on already-muted track temporarily unmutes while held, restores on release

### LED Feedback

- [x] **LED-01**: Solo button LED reflects real-time solo state during momentary holds
- [x] **LED-02**: Mute button LED reflects real-time mute state during momentary holds

### Multi-Track

- [ ] **MULTI-01**: User can hold Solo momentary on multiple tracks simultaneously
- [ ] **MULTI-02**: User can hold Mute momentary on multiple tracks simultaneously
- [ ] **MULTI-03**: User can hold Solo on one track and Mute on another simultaneously

### Integration

- [x] **INTG-01**: Existing toggle behavior preserved for short presses (no regression)
- [x] **INTG-02**: Timer callback properly cleaned up on disconnect (no phantom callbacks)
- [x] **INTG-03**: Script loads and initializes without errors after modification

## v2 Requirements

### Configurability

- **CFG-01**: Configurable threshold constant (easy to tune without code changes)
- **CFG-02**: Shift-button safety — clean revert when shift pressed mid-hold

### Extended Scope

- **EXT-01**: Track Activator (arm) buttons with same dual behavior
- **EXT-02**: Per-button configurable behavior mode at runtime

## Out of Scope

| Feature | Reason |
|---------|--------|
| Double-tap detection | Adds latency to every press — anti-feature per research |
| Threading-based timers | Must stay on main thread for Live API safety |
| Track Activator buttons | User excluded from v1 scope |
| Runtime behavior configuration | Overcomplicated for v1; constant is sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 2 | Complete |
| CORE-02 | Phase 2 | Complete |
| CORE-03 | Phase 2 | Complete |
| CORE-04 | Phase 2 | Complete |
| CORE-05 | Phase 2 | Complete |
| CORE-06 | Phase 2 | Complete |
| CORE-07 | Phase 2 | Complete |
| LED-01 | Phase 2 | Complete |
| LED-02 | Phase 2 | Complete |
| MULTI-01 | Phase 3 | Pending |
| MULTI-02 | Phase 3 | Pending |
| MULTI-03 | Phase 3 | Pending |
| INTG-01 | Phase 2 | Complete |
| INTG-02 | Phase 1 | Complete |
| INTG-03 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after roadmap creation*
