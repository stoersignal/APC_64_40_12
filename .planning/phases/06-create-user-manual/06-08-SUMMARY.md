---
phase: 06-create-user-manual
plan: 08
subsystem: documentation
tags: [docs, readme, entry-pointer, terminology-gate]
requires:
  - docs/INSTALL.md (Plan 07, wave 2)
  - docs/manual.html (Plan 01, wave 1)
  - docs/TROUBLESHOOTING.md (Plan 07, wave 2)
  - docs/apc40-layout.svg (Plan 06, wave 2)
provides:
  - README.md as thin entry pointer (≤25 lines)
affects:
  - GitHub repo landing page
tech-stack:
  added: []
  patterns:
    - thin-entry-pointer README pattern (D-02)
    - terminology gate (no `snapshot` in user-facing docs — D-09/D-10)
key-files:
  created:
    - README.md
  modified: []
decisions:
  - D-02: README is a thin entry pointer (project blurb + 3 doc links + Credits); install paragraph migrates to docs/INSTALL.md; PDF reference + broken blogspot instructional links dropped.
  - D-09/D-10: README contains 0 occurrences of `snapshot` (terminology gate).
metrics:
  duration_seconds: ~180
  tasks_completed: 1
  files_changed: 1
  completed: 2026-05-02
one-liner: README rewritten to a 19-line thin entry pointer linking to docs/INSTALL.md, docs/manual.html, docs/TROUBLESHOOTING.md, and docs/apc40-layout.svg, with Credits preserved verbatim and the broken PDF / blogspot / YouTube references dropped.
---

# Phase 6 Plan 8: README rewrite to thin entry pointer Summary

## Outcome

`README.md` is now a 19-line landing page that points GitHub visitors at the four documentation artifacts produced by waves 1 and 2 of this phase, while preserving the project blurb, device image, and the original Credits section verbatim.

## Verification Results

All acceptance criteria from the plan's `<verify><automated>` block passed in a single check:

| Check                                                         | Result                                                                          |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `test -f README.md`                                           | PASS                                                                            |
| Contains `[Install` link                                      | PASS                                                                            |
| Contains `docs/INSTALL.md` link                               | PASS                                                                            |
| Contains `docs/manual.html` link                              | PASS                                                                            |
| Contains `docs/TROUBLESHOOTING.md` link                       | PASS                                                                            |
| Contains `docs/apc40-layout.svg` link                         | PASS                                                                            |
| Contains `## Credits` heading                                 | PASS                                                                            |
| Contains `Hanz Petrov` credit                                 | PASS                                                                            |
| Contains `Will Marshall` credit                               | PASS                                                                            |
| Line count ≤ 25                                               | PASS (`wc -l README.md` = **19**)                                               |
| Case-insensitive count of `snapshot`                          | **0** (terminology gate — D-09 / D-10)                                          |
| No `APC_64_40_quickstart_guide_rev_1.pdf` reference           | PASS                                                                            |
| No `remotescripts.blogspot.com/p/apc-64-40.html.*Mappings`    | PASS                                                                            |
| `test -f docs/INSTALL.md`                                     | PASS (Plan 07, wave 2)                                                          |
| `test -f docs/manual.html`                                    | PASS (Plan 01, wave 1)                                                          |
| `test -f docs/TROUBLESHOOTING.md`                             | PASS (Plan 07, wave 2)                                                          |
| `test -f docs/apc40-layout.svg`                               | PASS (Plan 06, wave 2)                                                          |

## Link-target Disk Check

All four link targets verified present on disk at task completion (per the I-05 split safety check):

| Path                       | Status  | Source plan         |
| -------------------------- | ------- | ------------------- |
| `docs/INSTALL.md`          | present | Plan 07 (wave 2)    |
| `docs/manual.html`         | present | Plan 01 (wave 1)    |
| `docs/TROUBLESHOOTING.md`  | present | Plan 07 (wave 2)    |
| `docs/apc40-layout.svg`    | present | Plan 06 (wave 2)    |

## Terminology Gate (D-09 / D-10)

`grep -ci 'snapshot' README.md` returned **0**. The user-facing README uses Ableton's canonical "variations" terminology (where the term comes up at all — in this README it does not, because variation behavior is documented in `docs/manual.html`, not the landing page).

## Final README.md Line Count

**19 lines** (limit: ≤25). Breakdown:

- Title (`# APC_64_40_11`) — 1 line
- Project blurb paragraph — 1 line
- Device image — 1 line
- `## Documentation` heading + 3 doc-link bullets + SVG poster link — 7 lines
- `## Credits` heading + 2 prose paragraphs (Hanz Petrov / Fabrizio Poce / matthewcieplak chain + Will Marshall acknowledgement) — 3 lines
- Blank separators — 6 lines

## What Was Dropped

Per D-02, the following content from the previous (untracked) README is no longer present in the new README:

- The "Below you can find the original README..." sentence.
- The Installation paragraph (Windows path, macOS Show Package Contents step, MIDI / Sync setup) — migrated to `docs/INSTALL.md` by Plan 07.
- The Instructions section: broken `remotescripts.blogspot.com/p/apc-64-40.html?Mappings...` links, the `APC_64_40_quickstart_guide_rev_1.pdf` reference, the YouTube features-video link.
- The "Enjoy!!!!" closing line.

## What Was Preserved Verbatim

- Project blurb sentence: `Remote script for the Akai APC40 with Ableton Live 11 (and seems to be working with 12) based on APC_40_9 Remote script. Bumped the remote script version to Ableton Live 11 by converting the whole codestack from Python 2 to 3.`
- Device image markdown: `![IMAGE](https://cdn.mos.cms.futurecdn.net/70f75473c4327722ce7a9e6d7f31b82d-1200-80.jpg)`
- Credits content (Hanz Petrov bio link + Fabrizio Poce + Ableton forums thread + matthewcieplak + Will Marshall APCAdvanced acknowledgement) — folded under a new `## Credits` heading. The bare `remotescripts.blogspot.com/p/apc-64-40.html` URL inside Hanz Petrov's bio link is intentionally retained per the acceptance criteria (it's a credit, not a broken instruction).

## Deviations from Plan

None — plan executed exactly as written. The rewritten README content is byte-for-byte the markdown block specified in the plan's `<task><action>` section.

### Note on the "current README" reference

The plan's `read_first` block points at `README.md` as the source for the project blurb / image / Credits content. In this worktree base (commit `a19ec50`), no `README.md` is tracked in HEAD — the previous README was untracked and never committed. The plan inlined the verbatim content (project blurb, image URL, full Credits text) directly in the `<action>` block, so this was not a blocker. The new README is the first committed README in this repo.

## Auth Gates

None.

## Threat Flags

None — README.md is read-only static prose. The plan's threat register entry (T-06-08) explicitly accepted documentation-only risk, and the rewrite did not introduce any new trust boundary.

## Commits

| Task | Description                                          | Hash    | Files       |
| ---- | ---------------------------------------------------- | ------- | ----------- |
| 1    | Rewrite README.md to thin entry pointer per D-02     | 5d94f5c | `README.md` |

## Phase 6 Closing Note

This is the final user-facing deliverable for phase 6. With `docs/manual.html` (Plans 01 + 02 + 03 + 04 + 05), `docs/apc40-layout.svg` (Plan 06), `docs/INSTALL.md` and `docs/TROUBLESHOOTING.md` (Plan 07), and now `README.md` (this plan), the documentation bundle is complete and the GitHub-repo landing experience funnels users through a single thin entry point. Ready for phase verification.

## Self-Check: PASSED

- README.md exists at repo root: FOUND
- Commit 5d94f5c exists: FOUND
- All four link targets exist: FOUND (docs/INSTALL.md, docs/manual.html, docs/TROUBLESHOOTING.md, docs/apc40-layout.svg)
- Line count: 19 (≤25) — FOUND
- Snapshot count: 0 — FOUND
