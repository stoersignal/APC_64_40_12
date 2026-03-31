# Requirements: APC40 Toggle/Momentary Button Behavior

**Defined:** 2026-03-31
**Core Value:** Solo and Mute buttons must feel responsive and predictable — short taps toggle, longer holds act momentary, with LED feedback always reflecting the current real-time state.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Behavior

- [ ] **CORE-01**: Short press (<400ms) on Solo button toggles solo state on/off
- [ ] **CORE-02**: Long press (>=400ms) on Solo button acts momentary — solo activates on press-down, reverts on release
- [ ] **CORE-03**: Short press (<400ms) on Mute button toggles mute state on/off
- [ ] **CORE-04**: Long press (>=400ms) on Mute button acts momentary — mute activates on press-down, reverts on release
- [ ] **CORE-05**: State change fires immediately at press-down (no classification delay)
- [ ] **CORE-06**: Long press on already-soloed track temporarily unsolos while held, restores on release
- [ ] **CORE-07**: Long press on already-muted track temporarily unmutes while held, restores on release

### LED Feedback

- [ ] **LED-01**: Solo button LED reflects real-time solo state during momentary holds
- [ ] **LED-02**: Mute button LED reflects real-time mute state during momentary holds

### Multi-Track

- [ ] **MULTI-01**: User can hold Solo momentary on multiple tracks simultaneously
- [ ] **MULTI-02**: User can hold Mute momentary on multiple tracks simultaneously
- [ ] **MULTI-03**: User can hold Solo on one track and Mute on another simultaneously

### Integration

- [ ] **INTG-01**: Existing toggle behavior preserved for short presses (no regression)
- [ ] **INTG-02**: Timer callback properly cleaned up on disconnect (no phantom callbacks)
- [ ] **INTG-03**: Script loads and initializes without errors after modification

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
| CORE-01 | — | Pending |
| CORE-02 | — | Pending |
| CORE-03 | — | Pending |
| CORE-04 | — | Pending |
| CORE-05 | — | Pending |
| CORE-06 | — | Pending |
| CORE-07 | — | Pending |
| LED-01 | — | Pending |
| LED-02 | — | Pending |
| MULTI-01 | — | Pending |
| MULTI-02 | — | Pending |
| MULTI-03 | — | Pending |
| INTG-01 | — | Pending |
| INTG-02 | — | Pending |
| INTG-03 | — | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 0
- Unmapped: 15 (pending roadmap creation)

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after initial definition*
