# Phase 5: Toggle/Momentary Send Mode Buttons - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-03-31
**Phase:** 5-Toggle/Momentary Send Mode Buttons
**Areas discussed:** Timer unification, Previous mode tracking, Pan button behavior

---

## Timer Unification

| Option | Description | Selected |
|--------|-------------|----------|
| Single counter (Recommended) | One _send_ticks_delay replacing _pan_to_vol_ticks_delay for sends. Only one mode button held at a time. | ✓ |
| Per-button counters | Separate tick counters per button. More complex. | |
| You decide | Claude picks | |

**User's choice:** Single counter

---

## Previous Mode Tracking

| Option | Description | Selected |
|--------|-------------|----------|
| Last active mode (Recommended) | Store mode before press, revert to it | |
| Always Pan | Long press always reverts to Pan (mode 0) | ✓ |
| Cycle back | Revert to mode before current short-press | |

**User's choice:** Always Pan

---

## Pan Button Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| No, keep existing pan-to-vol | Pan button keeps long-press pan/vol toggle. Only Send A/B/C get momentary. | ✓ |
| Yes, replace pan-to-vol | Pan button gets momentary too | |
| You decide | Claude picks | |

**User's choice:** Keep existing pan-to-vol

## Claude's Discretion

- LONG_PRESS_DELAY import vs local definition
- State variable placement in __init__
- _mode_value extension approach

## Deferred Ideas

None
