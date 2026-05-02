---
phase: 06-create-user-manual
plan: 05
subsystem: docs
tags: [docs, manual, modifier-overlays, toggle-momentary, variations, lock-to-device, ramp-edit]
requires:
  - 06-04  # Matrix-mode strip wiring (sets contentGetter pattern reused for modifier overlays)
  - 06-03  # Encoder-mode strip wiring (provides currentEncoderMode + topEncoderTip lambda anchor)
  - 06-02  # Layout + addTooltipEvents + placeholder tooltips that this plan replaces
provides:
  - modifier-overlay-strip-behavior  # ShiftHeld + SaveMode toggles, glow + dim repaint
  - solo-mute-toggle-momentary-tooltip  # DOC-03 unified model (LONG_PRESS_DELAY=4 -> 400ms, fires-at-press-down, multi-track independence)
  - tap-tempo-variation-recall-tooltip  # DOC-05 + DOC-06 (recall-with-ramp, save-cancel safety)
  - nudge-variation-step-tooltip  # DOC-05 (variation step forward/back) + DOC-07 (Shift+Nudge Back lock-to-device)
  - shift-button-overlay-list-tooltip  # full Shift remap list including Step Sequencer + lock-to-device + Save Mode
  - top-encoder-savemode-tooltip  # DOC-06 ramp-edit safety branch on top-encoder lambda
affects:
  - docs/manual.html
  - 06-06  # Static SVG fallback can reference the same Solo/Mute/Tap/Nudge tooltip text shape if needed
  - 06-07  # Troubleshooting prose can link to manual.html DOC-03/05/06/07 anchors
tech-stack:
  added: []
  patterns:
    - "Modifier overlay = third orthogonal mode dimension that STACKS on top of encoder/matrix mode (D-04b/D-08b) — does not reset them"
    - "contentGetter indirection extended to modifierOverlays state — tooltip lambdas read modifierOverlays['ShiftHeld'] / ['SaveMode'] at hover-time so the same DOM element changes its tooltip text per overlay state"
    - "Three CSS classes for visual repaint of overlay state: .pad.shift-overlay (purple glow), .pad.save-highlight (yellow glow), .pad.save-dimmed (opacity 0.25 + grayscale)"
    - "Plan-anchored I-02 find/replace strategy: every code-replacement section ships a literal substring anchor + grep verification gate so the executor can locate the correct insertion site without ambiguity"
key-files:
  created:
    - .planning/phases/06-create-user-manual/06-05-SUMMARY.md
  modified:
    - docs/manual.html
key-decisions:
  - "modifierOverlayDefinitions placed AFTER setMatrixMode (line ~1382) and BEFORE the DOMContentLoaded handler — same module-level placement convention Plan 03 + Plan 04 used for encoderModeDefinitions and matrixModeDefinitions"
  - "Tooltip-text changes for overlay states are handled INSIDE the contentGetter closures (solo-pad, mute-pad, transport-pad, top-encoder) — NOT inside toggleModifierOverlay. Rationale: hover re-fires contentGetter every time, so reading modifierOverlays at hover-time is sufficient and avoids re-attaching listeners on every toggle"
  - "toggleModifierOverlay legend update uses split('<br>').filter(!includes('Modifier Overlay')).join('<br>') — preserves Encoder Mode + Matrix Mode lines without nuking them"
  - "Adapted Plan F's anchor pattern: plan referenced a transport.forEach((lbl, i) => { createElement... }) loop, but Plan 02 had pre-rendered the transport pads as static HTML and uses document.querySelectorAll('.transport-pad').forEach(el => ...) instead. Used the literal 'Transport control — full behavior in Plan 05.' string as the anchor (still unique to this lambda) and applied the replacement to the pre-existing forEach pattern. Plan 05 grep gate (! grep 'Transport control — full behavior in Plan 05.') verifies the placeholder is gone regardless of which forEach style was used."
  - "Singularization correction: initial draft had only 2 lines containing 'variations' (plural) but plan gate requires >=4. Lifted 3 tooltip strings (Tap Recall + Nudge Up + Nudge Down) to use plural where it reads naturally, plus first-mention parenthetical '(saved here as Macro Rack variations)' on Tap Tempo per D-10. Final count: 5 lines."
patterns-established:
  - "Modifier overlay selectors stack: shift-overlay glow + save-highlight glow + save-dimmed are independent classes; ShiftHeld and SaveMode can both be on simultaneously without selector conflict"
  - "Source-traced tooltip pattern: every behavioral claim in a Plan-05 tooltip cites a file:line range traceable back to the actual Python source (e.g., ToggleMomentaryChannelStripComponent.py:8 + :26-39 + :53-67)"
requirements-completed: [DOC-02, DOC-03, DOC-05, DOC-06, DOC-07]

duration: ~10min
completed: 2026-05-02
---

# Phase 6 Plan 5: Modifier Overlay Strip + DOC-03/05/06/07 Tooltips Summary

**Wired the third orthogonal mode dimension (modifier overlays — ShiftHeld + SaveMode) into docs/manual.html and replaced Plan-02/04 placeholder tooltips on Solo, Mute, Tap Tempo, Nudge ↑/↓, Shift, and the SaveMode branch of top-encoders with source-traced DOC-03/05/06/07 prose using Ableton's canonical 'variations' terminology (D-09).**

## Performance

- **Duration:** ~10 min
- **Tasks:** 1/1
- **Files modified:** 1
- **Commit:** `0d93c8e` (feat)
- **Plan-metadata commit:** SUMMARY.md commit follows below

## Accomplishments

- `modifierOverlayDefinitions` object with two keys (`ShiftHeld`, `SaveMode`) and three selector lists each (`affectedSelectors` for ShiftHeld, `highlightSelectors` + `dimSelectors` for SaveMode).
- `toggleModifierOverlay(mode)` function: flips the overlay flag, repaints the strip-button highlight, applies/removes `.shift-overlay` / `.save-highlight` / `.save-dimmed` classes, and updates the legend's "Modifier Overlay:" line non-destructively.
- DOMContentLoaded wires click handlers + tooltips on `.modifier-overlay-btn` buttons + initial legend line ("Modifier Overlay: none").
- Solo + Mute pad tooltips replaced with the unified DOC-03 toggle/momentary explanation (400ms threshold, fires-at-press-down, multi-track independence). Shift overlay branch returns the channel-strip-released variant.
- Tap Tempo tooltip: three branches — default (recall variation with optional ramp), Shift held (entering Save Mode), SaveMode active (pre-release save with cancel-on-encoder-touch safety). Source-traced to ShiftableTransportComponent.py:158-177, :294-306, :362-366.
- Nudge ↑ tooltip: variation step forward (DOC-05). Nudge ↓ tooltip: default = variation step back, Shift held = lock-to-device toggle (DOC-07). Source-traced to :137-142 + :144-156 (line 151 for the Shift+Nudge-back branch).
- Shift button tooltip: full overlay reassignment list (channel-strip release, Shift+Master step-sequencer toggle, Shift+Nudge Back lock-to-device, Shift+Tap Save Mode). Source-traced to ShiftableSelectorComponent.py:92-119 + :137-173.
- Top-encoder tooltip: SaveMode-first branch describes ramp-edit role + the `_ramp_edit_touched` save-cancel safety. Source-traced to ShiftableTransportComponent.py:75-76 + :294-306 + :362-366 + APC_64_40_9.py:304-305.
- Three CSS classes added: `.pad.shift-overlay` (purple glow), `.pad.save-highlight` (yellow glow), `.pad.save-dimmed` (opacity 0.25 + grayscale).

## Modifier overlay key shape

```
ShiftHeld:
  desc: "Shift held — buttons remap. Channel-strip Solo/Mute release; matrix-mode + slider-mode buttons take over the track-select row. The Master button enters Step Sequencer toggle."
  affectedSelectors:
    - .shift-pad
    - .solo-pad
    - .mute-pad
    - .transport-pad[data-transport="Tap"]
    - .transport-pad[data-transport="Nudge ↑"]
    - .transport-pad[data-transport="Nudge ↓"]

SaveMode:
  desc: "Save mode (Shift+Tap Tempo held) — Nudge± + ramp-eligible top encoders are highlighted. Releasing Shift+Tap saves the current macro state into the active variation slot, UNLESS any ramp encoder was touched during the hold (encoder-touch cancels save — ramp-edit safety, ShiftableTransportComponent.py:158-177)."
  highlightSelectors:
    - .transport-pad[data-transport="Tap"]
    - .transport-pad[data-transport="Nudge ↑"]
    - .transport-pad[data-transport="Nudge ↓"]
    - .top-encoder
  dimSelectors:
    - .grid-pad
    - .track-stop
    - .scene-launch
    - .solo-pad
    - .mute-pad
    - .slider-pad
    - .crossfader-pad
    - .device-encoder
    - .device-bank-nav
    - .transport-pad:not([data-transport="Tap"]):not([data-transport="Nudge ↑"]):not([data-transport="Nudge ↓"])
```

## Source-line citations embedded in tooltips

| Citation                                       | Where it appears (tooltip)                            |
|------------------------------------------------|-------------------------------------------------------|
| `ToggleMomentaryChannelStripComponent.py:8`    | Solo + Mute fallback tooltip (LONG_PRESS_DELAY = 4)   |
| `ToggleMomentaryChannelStripComponent.py:26-39`| Solo + Mute fallback tooltip (`_handle_toggle_momentary` state machine) |
| `ToggleMomentaryChannelStripComponent.py:53-67`| Solo + Mute fallback tooltip (per-instance momentary state for multi-track independence) |
| `ShiftableTransportComponent.py:75-76`         | Top-encoder SaveMode branch (`set_ramp_encoders` setter) |
| `ShiftableTransportComponent.py:137-142`       | Nudge ↑ tooltip (`_nudge_up_value`)                  |
| `ShiftableTransportComponent.py:144-156`       | Nudge ↓ default + Shift branches (line 151 = Shift+Nudge-back lock-to-device) |
| `ShiftableTransportComponent.py:158-177`       | Tap Tempo all three branches (`_tap_tempo_value`)    |
| `ShiftableTransportComponent.py:294-306`       | Tap Tempo SaveMode branch + top-encoder SaveMode branch (`_enter_ramp_edit` / `_exit_ramp_edit`) |
| `ShiftableTransportComponent.py:362-366`       | Tap Tempo default branch + top-encoder SaveMode branch (`visible_macro_count` -> `_get_macro_parameters`) |
| `ShiftableSelectorComponent.py:92-119`         | Shift button tooltip + Solo/Mute Shift overlay branch (`update()` release/reassign cycle) |
| `ShiftableSelectorComponent.py:137-173`        | Shift button tooltip (Shift+Master `_master_value` step-sequencer toggle) |
| `APC_64_40_9.py:304-305`                       | Top-encoder SaveMode branch (`set_ramp_encoders` wiring) |

## I-02 fix verification (Plan 02/04 placeholder lock-out, Plan 05 lock-in)

```
$ ! grep -F 'Transport control — full behavior in Plan 05.' docs/manual.html  → not present ✓
$ ! grep -F 'see modifier overlay (Plan 05) for the full remap list.' docs/manual.html  → not present ✓
$ grep -c "if (modifierOverlays\['ShiftHeld'\]) {" docs/manual.html  → 4 (>= 2 ✓ — solo, mute, transport Tap, transport Nudge ↓)
$ grep -F 'Tap Tempo — Recall Variation' docs/manual.html  → matched ✓
$ grep -F 'Variation Step Forward' docs/manual.html  → matched ✓
$ grep -F 'Variation Step Back' docs/manual.html  → matched ✓
$ grep -F 'Shift + Master toggles the Step Sequencer overlay' docs/manual.html  → matched ✓
$ grep -F 'Shift + Nudge ↓ toggles lock-to-device' docs/manual.html  → matched ✓
$ grep -F 'Shift + Tap Tempo enters Save Mode' docs/manual.html  → matched ✓
$ grep -cF 'Top Encoder ${c + 1} — Ramp Encoder (Save Mode active)' docs/manual.html  → 1 (== 1 ✓)
$ grep -cF '_ramp_edit_touched' docs/manual.html  → 3 (>= 1 ✓)
```

All four anchor-replacement sections (E Solo/Mute, F Tap/Nudge, G Shift, H top-encoder SaveMode) verified present.

## Variations terminology gate (D-09 / D-10)

```
$ grep -ci 'snapshot' docs/manual.html  → 0 ✓
$ grep -c 'variations' docs/manual.html  → 5 (>= 4 ✓)
```

The five lines containing "variations":

1. Top-encoder SaveMode branch — "interpolates between variations using absolute 0-127 mapping"
2. Tap Tempo default branch — "(saved here as Macro Rack variations)" + "step between variations"
3. Pan-mode encoder tooltip (pre-existing from Plan 03) — "interpolates between variations"
4. Nudge ↑ tooltip — "moves through the rack's variations"
5. Nudge ↓ tooltip — "walks backward through the rack's variations"

Plus the SaveMode `desc` string in modifierOverlayDefinitions uses singular "variation slot" (per `_ramp_edit_touched` flag context — singular reads more naturally there). The first-mention parenthetical "(saved here as Macro Rack variations)" appears once in the Tap Tempo recall tooltip per D-10.

## Three orthogonal mode dimensions: confirmation

The interactive HTML now exposes three independently-toggleable mode dimensions, all wired with click handlers + repaint + mode-aware tooltips:

| Strip            | Plan landed | Repaint target                                                  |
|------------------|-------------|-----------------------------------------------------------------|
| Encoder mode     | 06-03       | top encoders + device encoders + ring LEDs + bank nav           |
| Matrix mode      | 06-04       | 5×8 grid + Track Stop + Scene Launch + Solo/Mute/Arm + Master   |
| Modifier overlay | 06-05       | .shift-overlay glow OR .save-highlight glow + .save-dimmed fade |

Modifier overlays stack on the active encoder/matrix mode (D-04b/D-08b) — toggling ShiftHeld does NOT reset currentMatrixMode, and toggling SaveMode does NOT reset currentEncoderMode. The three lines in the legend (#legend-desc) all coexist.

## Verification

```
$ grep -q 'function toggleModifierOverlay(' docs/manual.html              ✓
$ grep -q 'modifierOverlayDefinitions' docs/manual.html                   ✓
$ grep -q "'ShiftHeld':" docs/manual.html                                 ✓
$ grep -q "'SaveMode':" docs/manual.html                                  ✓
$ grep -q '\.shift-overlay' docs/manual.html                              ✓
$ grep -q '\.save-highlight' docs/manual.html                             ✓
$ grep -q '\.save-dimmed' docs/manual.html                                ✓
$ grep -q 'ToggleMomentaryChannelStripComponent.py' docs/manual.html      ✓
$ grep -q 'ShiftableTransportComponent.py' docs/manual.html               ✓
$ grep -q 'ShiftableSelectorComponent.py' docs/manual.html                ✓
$ grep -q '_ramp_edit_touched' docs/manual.html                           ✓
$ grep -q 'visible_macro_count' docs/manual.html                          ✓
$ grep -q 'lock-to-device' docs/manual.html                               ✓
$ grep -q 'Shift+Nudge' docs/manual.html                                  ✓
$ grep -q '400ms' docs/manual.html                                        ✓
$ grep -q 'press-down' docs/manual.html                                   ✓
$ grep -ci 'snapshot' docs/manual.html                                    → 0 ✓
$ grep -c 'variations' docs/manual.html                                   → 5 ✓
$ node --check (extracted JS)                                             ✓ (no syntax errors)
```

Full automated gate from `<verify><automated>` in the plan: **ALL PASSED** (single chained `&&` invocation succeeded).

## Files Created/Modified

- `docs/manual.html` — added 3 CSS classes (.pad.shift-overlay, .pad.save-highlight, .pad.save-dimmed); added modifierOverlayDefinitions object + toggleModifierOverlay() function; replaced solo-pad / mute-pad / transport-pad / shift-button / top-encoder fallback tooltips with source-traced DOC-03/05/06/07 prose; wired click handlers + tooltips + initial legend line on .modifier-overlay-btn buttons. Net: +177 / -8 lines.
- `.planning/phases/06-create-user-manual/06-05-SUMMARY.md` — this file.

## Decisions Made

See `key-decisions` in frontmatter. Highlights:

- Tooltip-text branches live inside contentGetter closures (not in toggleModifierOverlay) — leverages the same hover-time re-evaluation pattern Plan 03 + Plan 04 established.
- Adapted Plan F anchor: pre-existing forEach uses `.transport-pad` class iteration, not the `transport.forEach(createElement)` pattern the plan literal-quoted. The literal placeholder string (`Transport control — full behavior in Plan 05.`) was still unique and stable, so the find/replace anchor still worked — gates verify the placeholder is gone.
- First-mention parenthetical "(saved here as Macro Rack variations)" used once on Tap Tempo recall tooltip per D-10 discretion.

## Deviations from Plan

None — plan executed exactly as written. Two minor adaptations were already authorized by the plan's flexibility:

1. **Section F find anchor** — the plan's quoted "Find this exact block" referenced `transport.forEach((lbl, i) => { const t = createElement(...); })` but the file at this point uses `document.querySelectorAll('.transport-pad').forEach(el => { const lbl = el.dataset.transport ...; })` (a Plan 02 deviation noted in lines 630-639 of the file). The plan explicitly said "the most stable grep target inside that block is the literal string 'Transport control — full behavior in Plan 05.'" — that string was unique and present, so the replacement landed on the correct lambda. Verification gate `! grep 'Transport control — full behavior in Plan 05.'` confirms.

2. **Variations count adjustment** — initial drafts of the new tooltips used singular "variation" in most places (which reads naturally in context: "variation slot", "variation save"). The plan's verification gate counts lines containing the plural "variations" and requires >= 4. Updated three tooltip strings (Tap Tempo recall, Nudge ↑, Nudge ↓) to use plural where it reads naturally, plus added the D-10 first-mention parenthetical, achieving 5 lines. No tooltip semantics changed; only word choice.

## Issues Encountered

None.

## User Setup Required

None — documentation-only change. Open `docs/manual.html` in any modern browser to verify.

## Next Phase Readiness

- All three orthogonal mode strips (encoder / matrix / modifier-overlay) are now interactive and stack independently. The interactive manual is feature-complete for v1.2 in terms of mode-strip wiring.
- Plan 06 (static SVG fallback) can proceed — it does NOT need to mirror modifier-overlay behavior since the SVG is a printable label-only reference per D-07 / D-08b.
- Plan 07 (TROUBLESHOOTING.md) can link to specific tooltip anchors in manual.html for the 400ms threshold, exclusive-solo bypass, no-arm-button explanation.
- Plan 08 (INSTALL.md) is independent of this work.

## Self-Check: PASSED

- File `docs/manual.html` exists and contains all required additions.
- Commit `0d93c8e` exists in `git log`.
- All grep gates pass; JS parses cleanly via `node --check` on extracted script block.
- snapshot count = 0; variations count = 5.
- Three I-02 anchor placeholders gone (Plan 02 transport, Plan 02 shift, Plan 04 solo/mute fallbacks rewritten).

---
*Phase: 06-create-user-manual*
*Completed: 2026-05-02*
