---
phase: 06-create-user-manual
plan: 04
subsystem: docs
tags: [docs, manual, matrix-modes, step-sequencer, note-modes]
requires:
  - 06-03  # Encoder mode strip wiring (sets pattern setEncoderMode reuses)
provides:
  - matrix-mode-strip-behavior  # 9 modes, click → repaint grid + Track Stop + Scene Launch + Solo/Mute/Arm + Master Select
  - matrix-maps-format-reference  # docs section explaining the 5 Matrix_Maps.py constants
  - matrix-mode-aware-tooltips  # all clip-grid / track-stop / scene-launch / solo / mute / arm / master-select tooltips read currentMatrixMode at hover-time
affects:
  - docs/manual.html
tech-stack:
  added: []
  patterns:
    - "contentGetter indirection: tooltips re-evaluate matrixModeDefinitions[currentMatrixMode] on each hover (PATTERNS section 1e)"
    - "factory function (makeNoteModeDef) generates the 6 Note Mode definitions from a single matrixMapsLiterals source-of-truth (D-05 + DRY)"
    - "static literal embedding of Matrix_Maps.py defaults at write-time (D-05 — no out-of-sync hard-codes)"
key-files:
  created:
    - .planning/phases/06-create-user-manual/06-04-SUMMARY.md
  modified:
    - docs/manual.html
decisions:
  - "matrixMapsLiterals embedded as static JS object — every PATTERN_N / NOTEMAP_N / CHANNEL_N / USE_STOP_ROW_N / IS_NOTE_MODE_N value transcribed verbatim from Matrix_Maps.py:30-177 at write-time. Reverification: matrixMapsLiterals[1].PATTERN[0] === [3,3,3,3,5,5,5,5] === Matrix_Maps.py:40."
  - "makeNoteModeDef(n) is a function declaration (hoisted) so matrixModeDefinitions can call it via NoteMode1: makeNoteModeDef(1) without ordering trouble."
  - "I-01 lock: muteOverride.tip cites APC_64_40_9.py:195 (loop_length ← solo_buttons); soloOverride.tip cites :194 (loop_start ← mute_buttons); lane_mute (sceneTip in StepSequencer) cites :193. 193 appears EXACTLY ONCE."
  - "I-03 lock: armOverride + followOverride keys present in StepSequencer mode definition. arm-pad and master-select tooltip closures read def.armOverride / def.followOverride; setMatrixMode also repaints these regions."
  - "Plan-02 fallback tooltips on .solo-pad and .mute-pad preserved (defer to Plan 05's toggle/momentary unified model). The matrix-mode-aware branch only fires when def.soloOverride / def.muteOverride exists (StepSequencer only)."
metrics:
  completed: 2026-05-02
  duration_seconds: 345
---

# Phase 06 Plan 04: Matrix Mode Strip Wiring Summary

Wired the matrix-mode strip into `docs/manual.html`: 9 modes (ClipLaunch, SessionOverview, NoteMode1–6, StepSequencer), click handlers, repaint logic across grid + Track Stop + Scene Launch + Solo + Mute + Arm + Master-Select regions, mode-aware tooltips, and a `<section id="matrix-maps-format">` reference for users who want to customize Note/User Modes by editing `Matrix_Maps.py`.

## What was built

### `matrixModeDefinitions` keys (9)

```
ClipLaunch
SessionOverview
NoteMode1   ← makeNoteModeDef(1)
NoteMode2   ← makeNoteModeDef(2)
NoteMode3   ← makeNoteModeDef(3)
NoteMode4   ← makeNoteModeDef(4)
NoteMode5   ← makeNoteModeDef(5)
NoteMode6   ← makeNoteModeDef(6)
StepSequencer
```

Each non-StepSequencer entry has: `desc`, `gridColor(r,c)`, `gridLabel(r,c)`, `gridTip(r,c)`, `stopColor()`, `stopLabel(c)`, `stopTip(c)`, `sceneColor()`, `sceneLabel(r)`, `sceneTip(r)`.

`StepSequencer` additionally has: `soloOverride { color, label, tip }`, `muteOverride { color, label, tip }`, `armOverride { color, label, tip }`, `followOverride { color, label, tip }`, `velocityHint`.

### `matrixMapsLiterals` — shape

```js
{
  1: { USE_STOP_ROW: bool, IS_NOTE_MODE: bool, CHANNEL: int 0–15,
       PATTERN: 6×8 int matrix (LED color codes 0–127),
       NOTEMAP: 6×8 int matrix (MIDI notes 0–127) },
  2: { …same shape… },
  3: { … },
  4: { … },
  5: { … },
  6: { … },
}
```

Spot-check sync with Matrix_Maps.py (verified at write-time via Node eval):

| Mode | Field           | matrixMapsLiterals (HTML) | Matrix_Maps.py        |
|------|-----------------|---------------------------|-----------------------|
| 1    | PATTERN row 0   | `[3,3,3,3,5,5,5,5]`       | line 40               |
| 1    | NOTEMAP row 0   | `[56,57,58,59,80,81,82,83]` | line 56            |
| 1    | CHANNEL         | `9`                       | line 51               |
| 4    | USE_STOP_ROW    | `false`                   | line 112              |
| 5    | NOTEMAP row 5   | `[36,42,48,54,60,66,72,78]` | line 153           |
| 6    | IS_NOTE_MODE    | `false` (User Mode)       | line 159              |

### `LED_COLOR_MAP`

Ports the legend from `Matrix_Maps.py:37`:
- `0` = off → `#1e293b`
- `1` = green → `#10b981`
- `2` = green blink → `#10b981`
- `3` = red → `#ef4444`
- `4` = red blink → `#ef4444`
- `5` = yellow → `#f59e0b`
- `6` = yellow blink → `#f59e0b`
- `7`–`127` = green (handled by `colorCodeToCss` fallback)

## Source-line citations embedded in tooltips

| Citation                                       | Where it appears                                      |
|------------------------------------------------|-------------------------------------------------------|
| `MatrixModesComponent.py:114–172`              | ClipLaunch + SessionOverview gridTip                  |
| `MatrixModesComponent.py:176–207`              | Note Mode stopTip (USE_STOP_ROW_N application)        |
| `StepSequencerComponent.py:38–84`              | StepSequencer gridTip (init state)                    |
| `StepSequencerComponent.py:387–412`            | StepSequencer Track Stop / bank pages                 |
| `StepSequencerComponent.py:461-487`            | StepSequencer arm / velocity tooltip (I-03)           |
| `StepSequencerComponent.py:489-498`            | StepSequencer follow toggle tooltip (I-03)            |
| `StepSequencerComponent.py:490–520`            | soloOverride.tip (loop start handler)                 |
| `StepSequencerComponent.py:523–547`            | muteOverride.tip (loop length handler)                |
| `StepSequencerComponent.py:549–571`            | StepSequencer scene-launch (lane mute + q_step)       |
| `ShiftableSelectorComponent.py:137–173`        | StepSequencer matrix-mode-strip tooltip (engagement)  |
| `APC_64_40_9.py:186`                           | StepSequencer gridTip (sequencer instantiation)       |
| `APC_64_40_9.py:187`                           | StepSequencer Track Stop (set_bank_buttons wiring)    |
| `APC_64_40_9.py:190`                           | followOverride.tip (set_follow_button wiring)         |
| `APC_64_40_9.py:191`                           | armOverride.tip + arm-pad fallback (velocity wiring)  |
| `APC_64_40_9.py:193`                           | StepSequencer scene-launch (lane_mute wiring) — 1×    |
| `APC_64_40_9.py:194`                           | soloOverride.tip (loop_start ← mute_buttons)          |
| `APC_64_40_9.py:195`                           | muteOverride.tip (loop_length ← solo_buttons) — 2×    |

## Note Mode tooltip → format-reference link

Every Note Mode 1–6 grid pad tooltip ends with:

> *Customizing this mode:* open `Matrix_Maps.py` in any text editor and edit `PATTERN_N` / `CHANNEL_N` / `NOTEMAP_N`. [See the Matrix_Maps.py format reference below.](#matrix-maps-format)

Verified anchor present in document (`<section id="matrix-maps-format">`) and `<a href="#matrix-maps-format">` appears in every Note Mode gridTip + every NoteMode mode-strip-button tooltip.

## I-01 fix verification (BLOCKER lock-in)

```
$ grep -cF 'APC_64_40_9.py:195' docs/manual.html              → 2  (≥1 required ✓)
$ grep -cF 'APC_64_40_9.py:194' docs/manual.html              → 2  (≥1 required ✓)
$ grep -cF 'APC_64_40_9.py:193' docs/manual.html              → 1  (== 1 required ✓)
$ grep -F 'wired to solo-buttons in APC_64_40_9.py:195' …     → matched ✓
$ grep -F 'wired to mute-buttons in APC_64_40_9.py:194' …     → matched ✓
$ ! grep -F 'wired to solo-buttons in APC_64_40_9.py:193' … → not present ✓
$ ! grep -F 'note: source comment vs. wiring may differ' …  → not present ✓
```

## I-03 fix verification (follow + velocity)

```
$ grep -F 'StepSequencerComponent.py:461-487' docs/manual.html  → matched ✓
$ grep -F 'StepSequencerComponent.py:489-498' docs/manual.html  → matched ✓
$ grep -q 'armOverride'                                          → matched ✓
$ grep -q 'followOverride'                                       → matched ✓
```

`setMatrixMode` repaints `.arm-pad` cells when `def.armOverride` exists and the master-select element when `def.followOverride` exists. Default branches restore Plan-02 paint (Arm/MasterSel labels with the dimmed `.arm-pad` / `.master-select` CSS class styling).

## Snapshot terminology gate

```
$ grep -ci 'snapshot' docs/manual.html → 0 ✓
```

## Deviations from Plan

None — plan executed exactly as written. The pre-flight verification in `<read_first>` was honored: `APC_64_40_9.py:188-196` was read at task time and confirmed `set_velocity_buttons` is on line 191 (matching the I-03 canonical citation), `set_bank_buttons` is on line 187 (one line earlier than the plan's hint of 189; updated the gridTip in the docs to cite :187 — note this is a correctness-driven deviation, not a plan deviation since the plan instructed "If your local file's line numbers have drifted, use the actual line numbers"). All 5 wiring lines verified verbatim before transcription.

## Verification

```
$ grep -q 'function setMatrixMode(' docs/manual.html              ✓
$ grep -q 'matrixModeDefinitions' docs/manual.html                ✓
$ grep -q 'matrixMapsLiterals' docs/manual.html                   ✓
$ grep -q "'ClipLaunch':" docs/manual.html                        ✓
$ grep -q "'SessionOverview':" docs/manual.html                   ✓
$ grep -q "'StepSequencer':" docs/manual.html                     ✓
$ grep -q 'makeNoteModeDef(1)' docs/manual.html                   ✓
$ grep -q 'makeNoteModeDef(6)' docs/manual.html                   ✓
$ grep -q 'LED_COLOR_MAP' docs/manual.html                        ✓
$ grep -q 'id="matrix-maps-format"' docs/manual.html              ✓
$ grep -q 'PATTERN_N' docs/manual.html                            ✓
$ grep -q 'CHANNEL_N' docs/manual.html                            ✓
$ grep -q 'NOTEMAP_N' docs/manual.html                            ✓
$ grep -q 'USE_STOP_ROW_N' docs/manual.html                       ✓
$ grep -q 'IS_NOTE_MODE_N' docs/manual.html                       ✓
$ grep -q 'StepSequencerComponent.py' docs/manual.html            ✓
$ grep -q 'MatrixModesComponent.py' docs/manual.html              ✓
$ grep -q 'ShiftableSelectorComponent.py' docs/manual.html        ✓
$ grep -q '#matrix-maps-format' docs/manual.html                  ✓
$ grep -c '<strong>' docs/manual.html                             → 61 (≥12 ✓)
$ grep -ci 'snapshot' docs/manual.html                            → 0 ✓
$ node --check (extracted JS)                                     ✓ (no syntax errors)
```

## Self-Check: PASSED

- File `docs/manual.html` exists and contains all required additions.
- Commit `781380f` exists in `git log --all`.
- All grep gates pass; JS parses without syntax errors; matrixMapsLiterals values match Matrix_Maps.py at write-time.
