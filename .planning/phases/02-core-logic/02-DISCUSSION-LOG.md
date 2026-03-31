# Phase 2: Core Logic - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 2-Core Logic
**Areas discussed:** State machine flow, Already-active handling, Shift button guard, Implementation split

---

## State Machine Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle immediately (Recommended) | Press-down always toggles right away. Hold >=400ms: release reverts. Release <400ms: stays toggled. | ✓ |
| Defer until release | Don't change on press-down, decide on release. Adds latency. | |
| You decide | Claude picks based on research | |

**User's choice:** Toggle immediately (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Strict threshold (Recommended) | Released before tick 0 = toggle. Clean boundary. | ✓ |
| Fuzzy threshold | Grace window around threshold. More complex. | |

**User's choice:** Strict threshold (Recommended)

---

## Already-Active Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, same pattern (Recommended) | Press-down always inverts current state immediately. | ✓ |
| Different pattern | Only invert after threshold reached. | |

**User's choice:** Same pattern (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Unsolo it (toggle off) | Same as current — short press always toggles | ✓ |
| Keep it soloed (no-op) | Short press only activates, never deactivates | |

**User's choice:** Unsolo it (toggle off)

---

## Shift Button Guard

| Option | Description | Selected |
|--------|-------------|----------|
| Basic reset guard (Recommended) | Reset tick counter, revert state if momentary active. Minimal code. | ✓ |
| Skip entirely | Trust shift disconnection. Fix in Phase 3 if issues. | |
| You decide | Claude prevents stuck states with minimal code | |

**User's choice:** Basic reset guard (Recommended)

---

## Implementation Split

| Option | Description | Selected |
|--------|-------------|----------|
| Shared helper (Recommended) | One method called by both _solo_value and _mute_value. DRY. | ✓ |
| Duplicated code | Separate logic in each. Easier to read, harder to maintain. | |
| You decide | Claude picks based on codebase conventions | |

**User's choice:** Shared helper (Recommended)

## Claude's Discretion

- Method parameter naming in shared helper
- getattr/setattr vs explicit attribute access
- Comment style

## Deferred Ideas

None
