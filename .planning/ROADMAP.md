# Roadmap: APC40 Custom Control Surface

## Milestones

- ✅ **v1.0 Toggle/Momentary** — Phases 1-3 (shipped 2026-03-31) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 16Macros** — Phases 4-5 (shipped 2026-04-01) — [archive](milestones/v1.1-ROADMAP.md)
- 🚧 **v1.2 Documentation** — Phase 6 (in progress)

### 🚧 v1.2 Documentation (In Progress)

**Milestone Goal:** Ship a user manual that lets a non-developer install the script and operate every shipped controller feature — including the post-v1.1 rack snapshot, ramp, and lock-to-device behaviors — without reading source code.

- [ ] **Phase 6: Create user manual** — End-user documentation covering installation, controller layout, toggle/momentary model, 16-macro Pan mode, rack snapshots, ramp encoders, lock-to-device, and troubleshooting

## Phase Details

### Phase 6: Create user manual
**Goal**: A `docs/` bundle (interactive `manual.html` modeled on `example/lp-interactive-map.html` + Markdown for INSTALL and TROUBLESHOOTING + a Python-generated static SVG fallback) that an APC40 owner can follow start-to-finish to install the script and use every documented feature — including the step sequencer and the configurable matrix modes — with no recourse to source code
**Depends on**: v1.1 shipped + post-v1.1 ad-hoc commits (734e357, fd27e58, c6b836e, 7a55453, e95a034, 442f099) — these are the v1.2 feature surface to document
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, DOC-08, DOC-09, DOC-10
**Success Criteria** (what must be TRUE):
  1. A new APC40 user can install the script on Windows or macOS by following the manual alone (no support questions about install paths, handshake, or version compatibility)
  2. Every button and encoder the script handles is mapped in the layout reference, including the v1.2 reassignments (Tap Tempo + Nudge for variations, Shift+Nudge Back for lock-to-device)
  3. The interactive HTML repaints when the user clicks a mode button (encoder modes / matrix modes / step sequencer overlay) and shows modifier overlays for Shift held and Save mode
  4. Toggle/momentary semantics for Solo, Mute, and Send mode buttons are described as a single coherent model — not three independent feature blurbs
  5. Each v1.2 feature (variations, ramp, lock-to-device) is described with its trigger, effect, and any safety/cancel behaviors
  6. The step sequencer's controls (step grid, bank pages, velocity, loop start/length, lane mute, follow) are documented with engagement instructions
  7. The eight matrix base modes are documented, and `Matrix_Maps.py` is explained well enough that a user can edit Note Mode patterns/channels/notemaps without reading source code
  8. Troubleshooting section covers the failure modes a user will plausibly hit (handshake, exclusive-solo, threshold)
**UI hint**: no
**Plans**: 8 plans in 5 waves
Plans:

**Wave 1** *(foundation — must complete before any other wave)*
- [ ] 06-01-PLAN.md — HTML skeleton + APC40-renamed CSS palette + tooltip JS + three empty mode-strip stubs (DOC-02 foundation)

**Wave 2** *(blocked on Wave 1 — three parallel plans on disjoint files)*
- [ ] 06-02-PLAN.md — APC40 hardware layout via buildLayout(): clip grid, Track Stop, Solo/Mute, Arm row + master-select, Scene Launch, encoders, sliders, transport, mode-strip stub buttons (DOC-02, DOC-03, DOC-04, DOC-07, DOC-08, DOC-09, DOC-10) — touches docs/manual.html
- [ ] 06-06-PLAN.md — gen_apc40_layout.py + apc40-layout.svg static printable poster, default state only (DOC-02, DOC-08) — touches docs/gen_apc40_layout.py + docs/apc40-layout.svg
- [ ] 06-07-PLAN.md — INSTALL.md (Win+Mac walkthrough) + TROUBLESHOOTING.md (5 failure modes) (DOC-01, DOC-08) — touches docs/INSTALL.md + docs/TROUBLESHOOTING.md

**Wave 3** *(blocked on Wave 2 — two parallel plans on disjoint files)*
- [ ] 06-03-PLAN.md — Encoder mode strip: setEncoderMode() + encoderModeDefinitions for Pan/SendA/B/C/User1-3 + encoder/ring/bank-nav tooltips with line-traced source (DOC-02, DOC-03, DOC-04, DOC-06) — touches docs/manual.html
- [ ] 06-08-PLAN.md — README.md rewrite to thin pointer linking to docs/manual.html + docs/apc40-layout.svg + INSTALL.md + TROUBLESHOOTING.md (DOC-02) — touches README.md, depends on 06-01 + 06-06

**Wave 4** *(blocked on Wave 3)*
- [ ] 06-04-PLAN.md — Matrix mode strip: setMatrixMode() + matrixModeDefinitions for ClipLaunch/SessionOverview/NoteMode1-6/StepSequencer + Matrix_Maps.py format reference section (DOC-02, DOC-09, DOC-10) — touches docs/manual.html

**Wave 5** *(blocked on Wave 4)*
- [ ] 06-05-PLAN.md — Modifier overlays: toggleModifierOverlay() for ShiftHeld + SaveMode + Solo/Mute toggle/momentary tooltips + Tap/Nudge/Shift transport tooltips (DOC-02, DOC-03, DOC-05, DOC-06, DOC-07) — touches docs/manual.html

**Cross-cutting constraints** *(must_haves.truths shared by 2+ plans):*
- Terminology gate (D-09 / D-10): every plan that produces user-facing prose enforces `grep -ci 'snapshot' = 0` and requires `'variation'` to appear — applies to all 8 plans
- Source-line traceability: every behavioral tooltip cites the source file with line ranges from PATTERNS.md (e.g., `EncModeSelectorComponent.py:84-105`, `APC_64_40_9.py:194/195`, `StepSequencerComponent.py:461-487`, `:489-498`)
- Inline-only HTML (D-08): no external CSS/JS files; single self-contained `docs/manual.html` — applies to plans 01, 02, 03, 04, 05
- Three-orthogonal mode strips (D-04a): encoder / matrix / modifier overlay are independent; no combined strip — applies to plans 01, 02, 03, 04, 05

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. State Machine | v1.0 | 1/1 | Complete | 2026-03-31 |
| 2. Hardening | v1.0 | 1/1 | Complete | 2026-03-31 |
| 3. Multi-Track Hardening | v1.0 | 1/1 | Complete | 2026-03-31 |
| 4. 16-Parameter Encoder Mapping | v1.1 | 3/3 | Complete | 2026-04-01 |
| 5. Toggle/Momentary Send Mode Buttons | v1.1 | 2/2 | Complete | 2026-04-01 |
| 6. Create user manual | v1.2 | 0/8 | Planning complete | |
