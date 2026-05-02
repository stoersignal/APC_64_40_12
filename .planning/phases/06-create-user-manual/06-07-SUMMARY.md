---
phase: 06-create-user-manual
plan: 07
subsystem: docs
tags: [markdown, install-guide, troubleshooting, ableton-live, midi-remote-scripts]

# Dependency graph
requires:
  - phase: 05-toggle-momentary-send-mode-buttons
    provides: ToggleMomentaryChannelStripComponent + EncModeSelectorComponent (the source of LONG_PRESS_DELAY = 4 cited by TROUBLESHOOTING.md entries 2, 3, 4)
provides:
  - "docs/INSTALL.md — Windows + macOS first-run install walkthrough preserving the verbatim path strings from the README install paragraph"
  - "docs/TROUBLESHOOTING.md — 5 source-traced failure-mode entries in What/Why/What-to-do format"
affects: [06-08-readme-rewrite]

# Tech tracking
tech-stack:
  added: []  # documentation-only plan, no new tech
  patterns:
    - "Source-traced failure-mode entries: every TROUBLESHOOTING.md entry cites a specific file:line range so a curious reader can verify the explanation against the code"
    - "Verbatim-string preservation: INSTALL.md keeps the exact OS path strings and Finder verbs from the legacy README install paragraph, so existing user knowledge transfers"

key-files:
  created:
    - "docs/INSTALL.md"
    - "docs/TROUBLESHOOTING.md"
  modified: []

key-decisions:
  - "Followed plan content blueprint verbatim — the planner had already produced finished prose with verified citations; execution role was to verify citations against current source files and write the files"
  - "Verified all five source-line citations against current source: __init__.py:30-32 (vendor_id=2536, product_ids=[115]), APC.py:71-100 (handshake), APC.py:127-148 (Live 12 fallback), ToggleMomentaryChannelStripComponent.py:8 (LONG_PRESS_DELAY = 4), ToggleMomentaryChannelStripComponent.py:33 (setattr exclusive-solo bypass), EncModeSelectorComponent.py:9-10 (LONG_PRESS_DELAY = 4), EncModeSelectorComponent.py:80-81 (number_of_modes() == 4), ShiftableSelectorComponent.py:101-102 + 112-113 (arm wiring)"

patterns-established:
  - "Failure-mode entry template (D-12): What you might see / Why it happens / What to do — used uniformly across all 5 entries"
  - "Citation style: file.py:start-end for ranges, file.py:N for single lines, embedded inline in the Why-it-happens prose"

requirements-completed: [DOC-01, DOC-08]

# Metrics
duration: 3min
completed: 2026-05-02
---

# Phase 6 Plan 7: Write INSTALL.md and TROUBLESHOOTING.md Summary

**Two prose deliverables shipped: a Windows + macOS install walkthrough preserving the legacy README's verbatim path strings (`Show Package Contents`, `c:\programdata\Ableton\Live 11 Suite\Resources\MIDI Remote Scripts`, `Contents/App-Resources/MIDI Remote Scripts`, `MIDI / Sync`, the `-MAIN` suffix gotcha) and a 5-entry source-traced troubleshooting reference covering handshake failure, exclusive-solo bypass, the fixed 400ms threshold, the absence of per-track Send buttons, and the absence of a momentary Activator/arm mapping.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-02T07:02:24Z
- **Completed:** 2026-05-02T07:05:19Z
- **Tasks:** 1
- **Files created:** 2 (`docs/INSTALL.md` 65 lines, `docs/TROUBLESHOOTING.md` 65 lines)

## Accomplishments

- **DOC-01 covered:** `docs/INSTALL.md` walks a new APC40 user from download → folder placement (Windows + macOS) → Live preferences (MIDI / Sync tab) → handshake verification (Shift + Track Selection gesture). All verbatim path strings from the legacy README install paragraph are preserved so existing user knowledge transfers, and the GitHub-ZIP `-MAIN` suffix gotcha is called out explicitly.
- **DOC-08 covered:** `docs/TROUBLESHOOTING.md` documents exactly the 5 failure modes from D-11, each in the D-12 What/Why/What-to-do template, each with file:line citations to the implementing (or omitting) source. A curious reader can grep the cited files and verify every claim.
- **Version compatibility:** INSTALL.md confirms Live 11 + Live 12 work and points to `APC.py:127-148` for the Live-12 introduction-message API fallback, so a Live-12 user with handshake symptoms can verify the script handles their version.

## Task Commits

1. **Task 1: Write docs/INSTALL.md and docs/TROUBLESHOOTING.md** — `7a25a2a` (docs)

## Files Created/Modified

- `docs/INSTALL.md` (created, 65 lines) — Windows + macOS install walkthrough, version-compatibility note, handshake-verification gesture, source citations to `__init__.py:30-32` and `APC.py:71-100` / `APC.py:127-148`.
- `docs/TROUBLESHOOTING.md` (created, 65 lines) — 5 source-traced entries.

### TROUBLESHOOTING.md entry titles + source citations

| # | Entry title | Cited source |
|---|-------------|--------------|
| 1 | The script doesn't appear in Live's MIDI preferences (handshake failure) | `__init__.py:30-32`, `APC.py:94-100` (`_on_handshake_successful`), `APC.py:127-148` (Live 12 fallback) |
| 2 | Pressing Solo on track A doesn't un-solo track B (exclusive-solo bypass) | `ToggleMomentaryChannelStripComponent.py:33` (`setattr(self._track, track_attr, not current)`) |
| 3 | The 400ms long-press threshold feels wrong (not adjustable) | `ToggleMomentaryChannelStripComponent.py:8`, `EncModeSelectorComponent.py:9-10` (both `LONG_PRESS_DELAY = 4`) |
| 4 | There are no per-track Send A / B / C buttons | `EncModeSelectorComponent.py:80-81` (`number_of_modes() == 4`) |
| 5 | There are no Track Activator (arm-record) buttons in the toggle/momentary row | `ShiftableSelectorComponent.py:101-102` (wire) + `ShiftableSelectorComponent.py:112-113` (unwire under Shift) |

### Terminology gate (D-09 / D-10)

Case-insensitive `snapshot` count is 0 in BOTH `docs/INSTALL.md` and `docs/TROUBLESHOOTING.md`. Verified via:

```bash
grep -ci 'snapshot' docs/INSTALL.md           # 0
grep -ci 'snapshot' docs/TROUBLESHOOTING.md   # 0
```

## Decisions Made

None beyond the planner's blueprint. The plan provided finished prose with citations; the executor's role was to verify each citation against the current source file (lines did match) and to write the files. No content drift from the plan blueprint was needed.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. The plan's automated verification command (a long chained `&&` grep sequence) ran clean on the first attempt, including the `grep -c 'What you might see' == 5` check and both terminology-gate checks.

## Plan-Level Note

This plan is one of two leaves in Phase 6 wave 2 (alongside Plan 02 and Plan 06). Plan 08 (separate) handles the README rewrite, which links to the artifacts created here plus `docs/manual.html` (Plan 01) and `docs/apc40-layout.svg` (Plan 06).

## Next Phase Readiness

- Plan 08 (README rewrite) can now reference `docs/INSTALL.md` and `docs/TROUBLESHOOTING.md` from a top-level "Documentation" section.
- No blockers. No pending source-code changes.

## Self-Check: PASSED

Verified post-commit:

- `docs/INSTALL.md` exists in the working tree.
- `docs/TROUBLESHOOTING.md` exists in the working tree.
- Commit `7a25a2a` is reachable from HEAD: `git log --oneline | head -3` shows `7a25a2a docs(06-07): write INSTALL.md and TROUBLESHOOTING.md (DOC-01, DOC-08)`.
- All 22 plan-verification grep clauses pass (chained `&&` returned exit code 0).
- Both files pass the `grep -ci 'snapshot' == 0` terminology gate.

---
*Phase: 06-create-user-manual*
*Completed: 2026-05-02*
