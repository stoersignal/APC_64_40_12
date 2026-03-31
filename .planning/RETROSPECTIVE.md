# Project Retrospective

## Milestone: v1.0 — Toggle/Momentary

**Shipped:** 2026-03-31
**Phases:** 3 | **Plans:** 3 | **Tasks:** 6

### What Was Built
- ToggleMomentaryChannelStripComponent: new subclass with toggle/momentary dual behavior
- Shared DRY helper via getattr/setattr serving both Solo and Mute
- Shift guards preventing stuck states on mid-hold button reassignment
- Hardened disconnect() for mid-hold revert
- 61 unit tests covering single-track, multi-track, shift, rapid press, and disconnect scenarios

### What Worked
- Per-instance architecture meant multi-track (Phase 3) required zero code changes — just tests
- Existing timer pattern (TRACK_FOLD_DELAY) provided a proven model for LONG_PRESS_DELAY
- Research before each phase caught critical insights (fire at press-down, not threshold; _mute_value ignores releases in base class)
- TDD in Phase 3 — tests written RED first, then code fix made them GREEN

### What Was Inefficient
- Phase 1 (scaffolding) could have been combined with Phase 2 for a project this small
- Research agents sometimes re-discovered findings from project-level research

### Patterns Established
- Timer tick countdown pattern: set to N, decrement per tick, fire at 0, -1 = inactive
- Shift guard pattern: revert momentary state + reset counter in set_*_button() overrides
- getattr/setattr DRY helper for symmetric button behaviors

### Key Lessons
- "Fire at press-down" is the critical UX insight — threshold only determines release behavior
- Per-instance state in component-based frameworks naturally supports multi-track without shared state
- disconnect() hardening is easy to forget but prevents real stuck-state bugs in live performance

### Cost Observations
- Sessions: 1 (single context window)
- Model mix: Orchestrator on Opus, agents on Sonnet/Haiku
- Notable: Small project completed end-to-end in single session

## Cross-Milestone Trends

| Milestone | Phases | Plans | Tests | Duration |
|-----------|--------|-------|-------|----------|
| v1.0      | 3      | 3     | 61    | 1 day    |
