# Requirements: v1.1 16Macros

**Defined:** 2026-03-31
**Core Value:** Expanded parameter control and responsive mode switching for live performance.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### 16-Parameter Encoder Mapping

- [x] **ENC-01**: Pan mode maps top 8 encoders to selected device parameters 1-8
- [x] **ENC-02**: Pan mode maps device encoders to selected device parameters 9-16
- [x] **ENC-03**: Top 8 encoders are fixed to parameters 1-8 (no bank navigation on top row)
- [x] **ENC-04**: Device encoders can navigate deeper banks (params 17-24, 25-32, etc.) via existing bank buttons
- [x] **ENC-05**: Encoder LED rings reflect parameter values for both encoder rows in Pan mode
- [x] **ENC-06**: Parameters are properly released when leaving Pan mode (no stale encoder bindings)
- [x] **ENC-07**: Entering Pan mode does not break device encoder behavior in other modes (Send A/B/C)

### Toggle/Momentary Send Mode Buttons

- [ ] **SEND-01**: Short press (<400ms) on Send A/B/C switches encoder mode (existing behavior preserved)
- [ ] **SEND-02**: Long press (>=400ms) on Send A/B/C acts momentary — mode switches on press-down, reverts to previous mode on release
- [ ] **SEND-03**: Mode change fires immediately at press-down (no classification delay)
- [ ] **SEND-04**: Long press on already-active Send mode temporarily reverts to previous mode while held

### Integration

- [x] **MINT-01**: Existing encoder mode switching behavior preserved for short presses (no regression)
- [x] **MINT-02**: Script loads and initializes without errors after modification
- [ ] **MINT-03**: Pan mode toggle/momentary works alongside Solo/Mute toggle/momentary without interference

## Future Requirements

### Extended Encoder Control

- **FENC-01**: Lock state persists across mode switches
- **FENC-02**: Per-device parameter name display

### Extended Mode Buttons

- **FMODE-01**: LED feedback on mode buttons during momentary holds
- **FMODE-02**: Shift guard for mid-hold safety on mode buttons

## Out of Scope

| Feature | Reason |
|---------|--------|
| Per-track Send A/B/C buttons | APC40 hardware has no per-track send buttons — only global mode selectors |
| Modifying ShiftableDeviceComponent | Gets disconnected in Pan mode, reconnected in other modes — no internal changes |
| Bank navigation on top 8 encoders | User specified: top row fixed to params 1-8 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENC-01 | Phase 4 | Complete |
| ENC-02 | Phase 4 | Complete |
| ENC-03 | Phase 4 | Complete |
| ENC-04 | Phase 4 | Complete |
| ENC-05 | Phase 4 | Complete |
| ENC-06 | Phase 4 | Complete |
| ENC-07 | Phase 4 | Complete |
| SEND-01 | Phase 5 | Pending |
| SEND-02 | Phase 5 | Pending |
| SEND-03 | Phase 5 | Pending |
| SEND-04 | Phase 5 | Pending |
| MINT-01 | Phase 4 | Complete |
| MINT-02 | Phase 4 | Complete |
| MINT-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after roadmap creation*
