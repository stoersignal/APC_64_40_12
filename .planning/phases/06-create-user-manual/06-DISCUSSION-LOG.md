# Phase 6: Create user manual - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 06-create-user-manual
**Areas discussed:** File location & structure (with format pivot), Mode set for interactive HTML, Static SVG, Snapshot terminology

---

## Initial gray area selection

| Option | Description | Selected |
|--------|-------------|----------|
| File location & structure | Single MANUAL.md at root, README replacement, or split into docs/ folder | ✓ (with redirect) |
| Layout reference format (DOC-02) | Plain table, ASCII diagrams, keep PDF, replace PDF, or text-only | (superseded by HTML pivot) |
| Snapshot terminology (DOC-05/06) | "snapshots" / "variations" / both | ✓ |
| Troubleshooting scope (DOC-08) | Just install/handshake, or every known limitation | (defaulted to comprehensive) |

**User's choice:** "File location & structure, i´ve created a folder in the project root with an example of an interactive guide for a launchpad script. recreate the same but for the apc40 and this script"

**Notes:** Significant pivot — the user's `example/` folder reframed the deliverable from "Markdown manual" to "interactive HTML manual modeled on `example/lp-interactive-map.html`". Subsequent questions narrowed the new format. Questions about layout-format, terminology, and troubleshooting scope folded into the format decision tree below.

---

## Mode set for interactive HTML (after format pivot)

### First pass

| Option | Description | Selected (initial) |
|--------|-------------|----------|
| Pan (default, 16-macro view) | Top encoders → params 1-8, device encoders → 9-16, ring LEDs reflect values | ✓ |
| Send A / Send B / Send C | Three send modes — short-press toggle, long-press momentary | |
| Shift held | Overlay showing what every button does while Shift is held | |
| Snapshot save (Shift+Tap Tempo held) | Live save flow with Nudge buttons as save slots and ramp-encoder cancel-touch | |

**Initial user's choice:** Pan only — translated in first CONTEXT draft to "static layout, rich tooltips, no mode-repaint".

### Second pass (user reversed in same session)

**User's redirect:** "Send A/B/C / Shift / Snapshot-save to repaint the layout the way the Launchpad modes do AND: also document the step sequencer in this script"

**Final scope:** Full mode-repaint UI (matching the Launchpad example's pattern), plus step sequencer documentation as a new requirement.

| Mode region | Modes included | Source of truth |
|-------------|----------------|-----------------|
| Encoder mode strip | Pan / Send A / Send B / Send C / User1 / User2 / User3 | `EncModeSelectorComponent.py` |
| Matrix mode strip | Clip Launch / Session Overview / Note Mode 1–6 / Step Sequencer | `MatrixModesComponent.py` (modes 0–7 from `Matrix_Maps.py` defaults) + `ShiftableSelectorComponent._step_sequencer_active` |
| Modifier overlays | Shift held, Save mode (Shift+Tap Tempo held) | `ShiftableSelectorComponent.py` + `APC_64_40_9.py` |

**Notes on the reversal:** The original "tooltip-only" interpretation was a misread of an under-constrained answer. Once the user explicitly asked for the Launchpad mode-repaint pattern AND step sequencer coverage, the design flipped: D-04 in CONTEXT.md now says full mode-repaint, three orthogonal mode selectors. The previously-deferred "live mode-repaint UI" is no longer deferred; it is the headline feature.

---

## Layout location and HTML scope

| Option | Description | Selected |
|--------|-------------|----------|
| docs/ folder, HTML + Markdown split (Recommended) | docs/manual.html for layout/modes; docs/INSTALL.md and docs/TROUBLESHOOTING.md for prose | ✓ |
| docs/ folder, single HTML | Everything in docs/manual.html with collapsible install/troubleshooting sections | |
| Project root, single HTML next to README | manual.html at repo root | |
| Inside example/ folder | Treat existing example/ as the live home | |

**User's choice:** docs/ folder, HTML + Markdown split.

**Notes:** Confirmed `docs/` as the user-facing-doc home (separate from `example/` which stays as the reference). Three artifacts: `docs/manual.html`, `docs/INSTALL.md`, `docs/TROUBLESHOOTING.md`. README.md becomes a thin pointer.

---

## Static SVG layout reference

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, generated via Python script (Recommended) | gen_apc40_svg.py outputs printable SVG; mirrors example exactly | ✓ |
| Yes, hand-written SVG only (no generator) | Ship SVG without generator script | |
| No static SVG — interactive HTML only | Skip the SVG; replace existing PDF reference with HTML link | |

**User's choice:** Yes, generated via Python script.

**Notes:** Mirrors `example/gen_svg.py` + `example/lp-pro-mk3-layout.svg` pipeline. Filename `docs/gen_apc40_layout.py` → `docs/apc40-layout.svg`. Both committed.

---

## Snapshot terminology

| Option | Description | Selected |
|--------|-------------|----------|
| 'Snapshots' (project-internal term) | Matches user's spoken vocabulary and commit messages | |
| 'Variations' (Ableton-canonical) | Matches Ableton's official UI label exactly | ✓ |
| Both — alternate based on context | 'snapshots' in interactive labels, 'variations' in prose | |

**User's choice:** 'Variations' (Ableton-canonical).

**Notes:** Despite project-internal memory recording "user says 'snapshots' for Ableton's 'variations'", the user explicitly chose Ableton-canonical "variations" for user-facing docs. Rationale: discoverability (users searching Ableton docs/forums recognize the term). Internal code/git history retain "snapshot" — only `docs/` artifacts use "variations". Memory note remains accurate for spoken interaction; this decision applies to written manual only.

---

## Claude's Discretion

- CSS variable names, palette tweaks, grid spacing — match example aesthetic with APC40 proportions.
- Tooltip phrasing voice — terse heading + body + related-block.
- Filename casing inside `docs/` (default UPPERCASE for prose docs to match repo convention).
- Whether the static SVG legend duplicates tooltip content (default: minimal, label-only).
- Whether INSTALL.md covers Git clone vs ZIP (default: ZIP-first per existing README, Git as a one-liner aside).
- Whether to delete `APC_64_40_quickstart_guide_rev_1.pdf` (default: keep, but stop referencing).

## Scope Additions Captured Mid-Discussion

- **Step sequencer documentation** — `StepSequencerComponent.py` (~600 lines) covers a 64-step sequencer not enumerated in DOC-01..08. User explicitly added to scope. CONTEXT.md flags REQUIREMENTS.md update needed (proposed DOC-09 + DOC-02 re-scope).
- **Matrix modes documentation (DOC-10)** — User followed up with "document the MatrixModes as well". This promotes `MatrixModesComponent.py` (8 base modes: Clip Launch, Session Overview, Note/User Modes 1–6) and `Matrix_Maps.py` (the user-editable pattern/channel/notemap definitions for Note Modes 1–6) from "implicit DOC-02 detail" to a first-class requirement. Includes documenting the `Matrix_Maps.py` format so users can edit Note Mode layouts.
- **Full mode-repaint UI** — moved from Deferred Ideas to D-04 (the headline interactive feature).

## Deferred Ideas

- **Animated playhead in Step Sequencer view** — static representation + tooltips suffice for v1.2.
- **Annotated screenshots in INSTALL.md** — deferred until writing reveals genuine ambiguity in text-only steps.
- **Developer documentation** (DEV-01, DEV-02, DEV-03 from REQUIREMENTS.md Future) — separate future milestone.
- **Release notes / changelog** (REL-01) — separate future milestone.
- **Deletion of legacy `APC_64_40_quickstart_guide_rev_1.pdf`** — kept for historical context, no longer referenced from docs.
- **Live-tweak interface for `Matrix_Maps.py` patterns** — manual explains the configurability; in-page editor would be a future enhancement.
