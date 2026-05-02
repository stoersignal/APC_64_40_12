---
phase: 06-create-user-manual
plan: 01
subsystem: documentation
tags: [docs, html, manual, scaffold, tooltips]
requires: []
provides:
  - "docs/manual.html page skeleton with inline CSS palette and tooltip JS"
  - "#encoder-mode-strip empty container for Plan 03"
  - "#matrix-mode-strip empty container for Plan 04"
  - "#modifier-overlay-strip empty container for Plan 05"
  - "#device empty container for Plan 02"
  - "PLAN-02 marker comment anchor in <script> block"
  - "Module-level state: currentEncoderMode='Pan', currentMatrixMode='ClipLaunch', modifierOverlays"
affects:
  - "docs/ directory created"
tech_stack:
  added:
    - "Static HTML5 + inline CSS + inline JS (no external assets)"
  patterns:
    - "Verbatim port from example/lp-interactive-map.html with two CSS-token renames"
    - "350ms tooltip hover-delay pattern with edge-flip and contentGetter indirection"
key_files:
  created:
    - "docs/manual.html (304 lines)"
  modified: []
decisions:
  - "Renamed only --lp-case -> --apc-case and --lp-border -> --apc-border; other 14 CSS tokens remain identical to the example so the dark-theme/neon-accent palette is preserved verbatim (CONTEXT D-07)."
  - "Kept the example's 8x8 grid-template-areas as-is for now — the .device container is empty in this plan; Plan 02 reshapes the grid to APC40 5x8 + transport + sliders."
  - "Placed three sibling mode-strip <div>s (encoder / matrix / modifier-overlay) above .device per CONTEXT D-04a so the layout reads top-to-bottom: header -> legend-desc -> three mode strips -> device -> tooltip target -> placeholder."
  - "Used a single shared .mode-strip CSS class (flex + gap + center) so Plans 03/04/05 don't each invent their own button-row styling."
  - "Wrote tooltip JS as a verbatim port (showTooltip / hideTooltip / addTooltipEvents) — no behavioral changes; the contentGetter closure indirection is preserved so Plan 03+ tooltips can re-evaluate against current mode state on every hover (CONTEXT D-04b)."
metrics:
  duration_min: ~3
  completed_date: "2026-05-02"
  task_count: 1
  file_count: 1
---

# Phase 6 Plan 1: Manual scaffold Summary

Bootstrapped `docs/manual.html` as a single self-contained HTML5 file (304 lines) with the APC40-renamed CSS palette, verbatim tooltip JS from `example/lp-interactive-map.html`, three empty mode-strip stubs, an empty `.device` container, and a working placeholder pad that proves the tooltip pipeline is alive — providing the foundation Plans 02–05 will build into.

## Changes

### Created

- **docs/manual.html** (304 lines) — single self-contained HTML5 file, no external CSS / JS / fonts. Structure:
  - Inline `<style>` block (lines 7–203) ported verbatim from `example/lp-interactive-map.html` lines 7–195 with two renames.
  - `<header>` with gradient `<h1>` and dim subtitle.
  - `<div id="legend-desc">` placeholder.
  - Three sibling `<div class="mode-strip">` containers with ids `encoder-mode-strip`, `matrix-mode-strip`, `modifier-overlay-strip` — each wrapped in a comment marker pointing at the plan that fills it.
  - `<div class="device" id="device">` (empty — Plan 02 fills it).
  - `<div id="tooltip">` floating tooltip target.
  - `<div id="placeholder-pad" class="pad">` "Hover me" pad pinned bottom-left (Plan 02 deletes).
  - `<script>` block with:
    - `let tooltipTimeout` + `showTooltip()` + `hideTooltip()` + `addTooltipEvents()` — verbatim from example lines 401–451 (350ms timeout, edge-flip, mousemove handler, mouseleave cleanup).
    - One-line wiring of the placeholder pad's tooltip.
    - Module-level state stubs: `currentEncoderMode = 'Pan'`, `currentMatrixMode = 'ClipLaunch'`, `modifierOverlays = { ShiftHeld: false, SaveMode: false }`.
    - Marker comment `// PLAN-02 builds the layout below this line`.

### Modified

None. This plan is purely additive.

## CSS Rename (the only divergence from the example)

| Original (example) | Renamed (manual) | Notes |
|---|---|---|
| `--lp-case: #1e293b` | `--apc-case: #1e293b` | Color value identical; semantic name now matches APC40 |
| `--lp-border: #334155` | `--apc-border: #334155` | Color value identical; semantic name now matches APC40 |

All 14 other tokens (`--bg-color`, `--pad-off`, `--text-main`, `--text-dim`, `--glow-cyan`, `--glow-magenta`, `--glow-blue`, `--glow-green`, `--glow-yellow`, `--glow-red`, `--glow-orange`, `--glow-purple`, `--tooltip-bg`, `--tooltip-border`) are unchanged. Every `var(--lp-case)` and `var(--lp-border)` reference in the CSS body was updated to use the new `--apc-*` names — no leftover `--lp-*` references remain.

## Three mode-strip ids exposed for downstream plans

| Strip id | Populated by | Purpose |
|---|---|---|
| `#encoder-mode-strip` | Plan 03 | Pan / Send A / Send B / Send C / User1–3 buttons (sources from `EncModeSelectorComponent.py`) |
| `#matrix-mode-strip`  | Plan 04 | Clip Launch / Session Overview / Note Modes 1–6 / Step Sequencer (sources from `MatrixModesComponent.py`, `Matrix_Maps.py`, `StepSequencerComponent.py`) |
| `#modifier-overlay-strip` | Plan 05 | Shift held / Save mode toggles (sources from `ShiftableSelectorComponent.py`, `APC_64_40_9.py`) |

Each strip starts as an empty `<div>` so downstream plans append button children with `appendChild()` without restructuring the DOM.

## Marker-comment anchor

The line `// PLAN-02 builds the layout below this line` is inside the `<script>` block immediately after the state-stub declarations. Plan 02 inserts the `buildLayout()` function and its invocation immediately below this marker so the file's top-to-bottom read order remains: imports → state → layout build → mode-switch handlers → wiring.

## Terminology gate (CONTEXT D-09 / D-10)

`grep -ci 'snapshot' docs/manual.html` = **0** — passes the terminology gate. The user-facing manual will use Ableton's canonical "variations" exclusively; "snapshot" never appears in `docs/manual.html`.

## Deviations from Plan

None — the plan executed exactly as written. No bugs found, no missing critical functionality, no blocking issues, no architectural changes needed.

## Verification

### Automated (from plan)

```
test -f docs/manual.html
grep -q '--apc-case' docs/manual.html
grep -q '--apc-border' docs/manual.html
! grep -q -- '--lp-case' docs/manual.html
! grep -q -- '--lp-border' docs/manual.html
grep -q 'function showTooltip(' docs/manual.html
grep -q 'function hideTooltip()' docs/manual.html
grep -q 'function addTooltipEvents(' docs/manual.html
grep -q '350' docs/manual.html
grep -q 'id="encoder-mode-strip"' docs/manual.html
grep -q 'id="matrix-mode-strip"' docs/manual.html
grep -q 'id="modifier-overlay-strip"' docs/manual.html
grep -q 'id="tooltip"' docs/manual.html
[ "$(grep -ci 'snapshot' docs/manual.html)" = "0" ]
```

**Result: PASS — all 14 checks succeeded.**

### Acceptance criteria (extended)

| Criterion | Result |
|---|---|
| docs/manual.html exists | PASS |
| `--apc-case` and `--apc-border` present | PASS (1 occurrence each in `:root`) |
| No `--lp-case` or `--lp-border` leftovers | PASS (zero matches) |
| `function showTooltip(`, `function hideTooltip()`, `function addTooltipEvents(` all present | PASS |
| Literal string `350` (hover delay ms) present | PASS |
| Three mode-strip ids present | PASS |
| `id="tooltip"` present | PASS |
| `PLAN-02 builds the layout below this line` marker present | PASS |
| `currentEncoderMode = 'Pan'`, `currentMatrixMode = 'ClipLaunch'`, `modifierOverlays = {` all present | PASS |
| 14 unchanged tokens all appear (`grep -c '--glow-' = 15`) | PASS |
| `snapshot` count = 0 (D-09 / D-10 gate) | PASS |

### Manual verification (deferred to user)

The plan's `<verification>` block asks the user to open the file in a browser and confirm:
- Page renders with dark background and white-on-gradient header text.
- No JS console errors.
- The "Hover me" placeholder pad in the bottom-left shows the test tooltip after ~350ms.
- View source: three `mode-strip` divs exist; the `.device` div is empty.

These are deferred to the user; downstream plans do not depend on visual confirmation here, only on the structural anchors verified above.

## Self-Check: PASSED

- File `docs/manual.html` exists at expected path: FOUND.
- Commit `837ce6a` (`feat(06-01): scaffold docs/manual.html with renamed CSS palette and tooltip JS`) exists: FOUND.
- All automated and acceptance checks pass.

## Commits

| Task | Description | Commit | Files |
|---|---|---|---|
| 1 | Scaffold docs/manual.html with renamed CSS palette and tooltip JS | `837ce6a` | `docs/manual.html` (new, 304 lines) |
