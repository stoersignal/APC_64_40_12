---
phase: 06-create-user-manual
plan: 06
subsystem: docs
tags: [svg, python3, stdlib, layout-poster, generator, apc40]

# Dependency graph
requires:
  - phase: 06-create-user-manual
    provides: docs/ directory exists with manual.html (Plan 06-01)
provides:
  - Self-contained Python 3 SVG generator (docs/gen_apc40_layout.py)
  - Static APC40 layout poster (docs/apc40-layout.svg) — default state, Pan + Clip Launch, no overlays
  - Cwd-independent path resolution pattern using os.path.dirname(os.path.abspath(__file__))
affects: [06-07, 06-08]

# Tech tracking
tech-stack:
  added: [Python stdlib os module for __file__-relative path resolution]
  patterns:
    - "Cwd-independent script output path via os.path.dirname(os.path.abspath(__file__))"
    - "list-of-strings + final '\\n'.join() SVG assembly (mirrors example/gen_svg.py)"
    - "draw_rect helper that appends both <rect> and centred <text> in one call"

key-files:
  created:
    - docs/gen_apc40_layout.py
    - docs/apc40-layout.svg
  modified: []

key-decisions:
  - "Resolved output path via __file__ instead of relative 'docs/apc40-layout.svg' to make the script cwd-independent (per I-06)"
  - "Dropped the unused 'json' import from the example/gen_svg.py template; replaced it with 'os' which is actually needed for path resolution"
  - "Highlighted Pan in encoder mode strip and Clip in matrix mode strip per D-08a (default state)"

patterns-established:
  - "Generator script + committed artifact: both .py source and .svg output land in the repo so users without Python installed can view the SVG directly (per D-03)"
  - "Idempotent SVG generation: re-running the script produces a byte-identical SVG (verified by SHA-256 across two consecutive runs)"

requirements-completed: [DOC-02, DOC-08]

# Metrics
duration: ~2min
completed: 2026-05-02
---

# Phase 06 Plan 06: APC40 Layout SVG Generator Summary

**Stdlib-only Python 3 SVG generator + committed default-state APC40 layout poster, cwd-independent via __file__-based path resolution**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-05-02T07:02:32Z
- **Completed:** 2026-05-02T07:04:45Z
- **Tasks:** 1
- **Files modified:** 2 (both created)

## Accomplishments
- Wrote `docs/gen_apc40_layout.py` (167 lines) — a self-contained Python 3 SVG generator that mirrors the structure of `example/gen_svg.py` (list-of-strings assembly, `draw_rect` helper, color/layout constants, ordered region drawing).
- Generated `docs/apc40-layout.svg` (276 lines, ~30 KB) — a static APC40 layout poster representing the default state (Pan + Clip Launch, no modifier overlays).
- Made the script cwd-independent: output path is resolved via `os.path.dirname(os.path.abspath(__file__))` so `python3 docs/gen_apc40_layout.py` produces the same on-disk file regardless of current working directory.
- Verified the script is idempotent (two consecutive runs produce a byte-identical SVG by SHA-256).
- Confirmed the terminology gate: zero `snapshot` occurrences in either file (case-insensitive).

## Task Commits

Each task was committed atomically:

1. **Task 1: Write docs/gen_apc40_layout.py + run to produce docs/apc40-layout.svg** — `8625243` (feat)

## Files Created/Modified
- `docs/gen_apc40_layout.py` (created, 167 lines) — Python 3 SVG generator. Stdlib-only (`os`). Defines `draw_rect(x, y, w, h, fill, text, font_size=12, text_color=color_text)`. Resolves output path via `os.path.dirname(os.path.abspath(__file__))`. When run, prints `Wrote <abs-path>/docs/apc40-layout.svg (277 lines)` and writes the SVG.
- `docs/apc40-layout.svg` (created, 276 lines, ~30 KB) — Static APC40 layout poster, well-formed XML, opens in any browser.

## Regions Drawn in the SVG

In drawing order (matching the order they appear in the script):

1. **Device outline** — outer rounded rect (1080×780) framing the entire layout.
2. **Title** — "APC40 Layout (Default — Pan + Clip Launch)" centred at the top.
3. **Subtitle** — "v1.2 — see manual.html for interactive mode reference".
4. **Top encoder row** — 8 encoders (T1–T8), drawn as `<circle>` caps with small ring-LED indicator rects below.
5. **Solo row** — 8 cyan rectangles labelled `Solo 1` through `Solo 8`.
6. **Mute row** — 8 amber rectangles labelled `Mute 1` through `Mute 8`.
7. **Stop-All-Clips + Master select** — 2 dark rectangles to the right of the Solo/Mute strip.
8. **5×8 clip grid** — 40 blue (#2563eb) pads labelled `T{c}/S{r}` in the centre of the layout.
9. **Track Stop row** — 8 grey rectangles labelled `Stop 1` through `Stop 8` directly below the grid.
10. **Scene Launch column** — 5 green rectangles labelled `Scene 1` through `Scene 5` to the right of the grid.
11. **Device encoder row** — 8 device encoders (D1–D8), `<circle>` caps with bold labels.
12. **Device bank navigation** — 4 buttons: ◀ Bank, Bank ▶, ◀ Dev, Dev ▶.
13. **Channel volume sliders** — 8 tall grey rectangles labelled `Vol 1` through `Vol 8`.
14. **Master slider** — 1 tall grey rectangle labelled `Master`.
15. **Crossfader** — horizontal grey rectangle labelled `Crossfader`.
16. **Transport row** — 7 buttons: Play, Stop, Rec, Tap, Nudge ↑, Nudge ↓, Detail.
17. **Encoder mode strip** — 7 buttons (Pan / SendA / SendB / SendC / User1 / User2 / User3); **Pan** highlighted as default.
18. **Matrix mode strip** — 9 buttons (Clip / Session / Note1–6 / Step); **Clip** highlighted as default.
19. **Shift button** — purple rectangle in the bottom-left, labelled `SHIFT`.
20. **Track navigation** — ◀ Trk / Trk ▶ buttons next to Shift.
21. **Legend** — 5 entries at the bottom: Clip Grid, Solo, Mute, Scene Launch, Encoders / Active mode.

## Verification Results

| Gate | Result |
|------|--------|
| `python3 -m py_compile docs/gen_apc40_layout.py` | exit 0 |
| `python3 docs/gen_apc40_layout.py` from repo root | exit 0, prints `Wrote <abs-path>/docs/apc40-layout.svg (277 lines)` |
| Cwd-independence: `(cd /tmp && python3 <abs>/docs/gen_apc40_layout.py)` | rewrites repo's `docs/apc40-layout.svg` (mtime changes); no stray `/tmp/apc40-layout.svg`; no `docs/docs/apc40-layout.svg` |
| `xml.etree.ElementTree.parse('docs/apc40-layout.svg')` | parses without exception |
| Idempotence: two consecutive runs | SHA-256 identical (`ae50a692…79adaa9`) |
| Terminology gate: `grep -ci snapshot` | 0 in both files |
| `def draw_rect(` count in script | 1 |
| `os.path.dirname(os.path.abspath(__file__))` count in script | 1 |
| Hard-coded `'docs/apc40-layout.svg'` literal in script | 0 |
| SVG file size | 30 KB (≥ 5 KB sanity threshold) |
| Required label substrings | all 17 present (`T1/S1`, `Solo 1`, `Mute 1`, `Stop 1`, `Scene 1`, `T1`, `D1`, `Vol 1`, `Master`, `Crossfader`, `Play`, `Tap`, `Pan`, `Clip`, `SHIFT`, `<svg `, `APC40 Layout`) |
| Full plan automated verifier | PASS |

## Decisions Made
- **Used `os` import instead of `json`:** the example/gen_svg.py imports `json` but never uses it; the APC40 generator drops `json` and adds `os` (needed for `__file__`-relative path resolution per I-06).
- **Cleaned `docs/__pycache__/` after `py_compile`:** treated as a verification side effect, not a deliverable. Did not commit it. (No `.gitignore` was added since none existed and creating one is out of scope for this single-task plan; future generated artefacts should be handled by a follow-up.)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Idempotence + Cwd-Independence Confirmation

- **Idempotent:** running `python3 docs/gen_apc40_layout.py` twice produces a byte-identical SVG (SHA-256 `ae50a6923caaa33ff79673906ebf984db9361cdca13826c6a50210edc79adaa9` both times).
- **Cwd-independent:** running from `/tmp` writes to `<repo>/docs/apc40-layout.svg` (mtime updated, contents unchanged), with NO stray `/tmp/apc40-layout.svg` and NO `<repo>/docs/docs/apc40-layout.svg`.

## Terminology Gate Confirmation

- `grep -ci snapshot docs/gen_apc40_layout.py` → 0
- `grep -ci snapshot docs/apc40-layout.svg` → 0

## User Setup Required

None — no external service configuration required. Maintainer can re-run `python3 docs/gen_apc40_layout.py` from any working directory whenever the layout needs regeneration.

## Next Phase Readiness

- DOC-02 (controller layout reference — printable static fallback) is satisfied.
- DOC-08 (default-state layout, no overlays per D-08a) is satisfied.
- Plan 06-08 (manual finalisation / cross-link check) can now reference `docs/apc40-layout.svg` from `docs/manual.html` if/when the cross-link is added.
- The script is independent of the HTML mode-strip work in Plans 03/04/05 — they can land in any order.

## Self-Check: PASSED

- Created files exist: `docs/gen_apc40_layout.py` FOUND, `docs/apc40-layout.svg` FOUND.
- Task commit `8625243` exists in `git log`.

---
*Phase: 06-create-user-manual*
*Completed: 2026-05-02*
