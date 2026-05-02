---
phase: 06-create-user-manual
plan: 03
subsystem: documentation
tags: [docs, html, javascript, encoder-mode, tooltip, contentGetter, pan16, sendABC, user-modes]
requires:
  - phase: 06-02
    provides: "Pre-rendered .top-encoder, .device-encoder, .top-encoder-ring, .device-bank-nav, .encoder-mode-btn elements with data-col / data-idx / data-mode attributes; #legend-desc target div; addTooltipEvents() helper; module-level let currentEncoderMode = 'Pan'"
provides:
  - "encoderModeDefinitions object — 7 mode definitions (Pan, SendA, SendB, SendC, User1, User2, User3) each with desc + topEncoderColor / deviceEncoderColor + topEncoderTip / deviceEncoderTip / bankNavTip / ringTip getter functions"
  - "setEncoderMode(modeId) function — repaints .encoder-mode-btn highlight, .top-encoder + .device-encoder backgroundColor, and #legend-desc innerHTML"
  - "Click handlers wired on every .encoder-mode-btn → setEncoderMode(btn.dataset.mode)"
  - "Tooltip-getter wiring for the 7 .encoder-mode-btn buttons themselves (per-button tooltip with mode-specific 'extra' block — Pan rest-state note, Send 400ms toggle/momentary citation, User unmapped citation)"
  - "Top encoder / device encoder / ring LED / device-bank-nav tooltips converted from placeholder strings to contentGetter closures that read encoderModeDefinitions[currentEncoderMode] at hover time"
  - "Initial paint setEncoderMode('Pan') call inside DOMContentLoaded after buildLayout() (per D-04b — Pan is the rest state default)"
affects:
  - "Plan 04 (matrix mode wiring) — same setMode() pattern + matrixModeDefinitions object structure to follow"
  - "Plan 05 (modifier overlay) — same contentGetter indirection for Solo/Mute/Send button tooltips"

tech-stack:
  added:
    - "modeDefinitions object pattern (per-mode getter closures over color + tip text)"
    - "contentGetter indirection for tooltips (re-evaluate on each hover) — confirmed working pattern for downstream plans"
  patterns:
    - "setMode(modeId) repaint — single function per mode-strip, mutates module-level current*Mode + repaints DOM affordances + updates #legend-desc"
    - "Source-of-truth citation in tooltip prose (PATTERNS Behavioral-accuracy traceability constraint)"

key-files:
  created: []
  modified:
    - "docs/manual.html (731 → 897 lines, +173 inserted, -7 deleted)"

key-decisions:
  - "Used dataset.idx for .device-bank-nav tooltips (the closure receives the bank-nav index 0..3 rather than re-deriving from textContent). The data-idx attribute was already set by Plan 02 — switching from textContent-based to dataset-based lookup makes the contentGetter closure deterministic across DOM mutations."
  - "Wired .encoder-mode-btn click + tooltip handlers inside the existing DOMContentLoaded callback (rather than creating a second listener) — single ordered initialization (placeholder removal → buildLayout → encoder-mode wiring → initial paint) keeps tooltip handlers attached only after their target elements exist."
  - "Kept the User1/2/3 desc text explicit about number_of_modes() == 4 and the EncModeSelectorComponent.py:80–81 line range, rather than hand-waving 'reserved'. Per PATTERNS Behavioral-accuracy traceability constraint and the must-have truth #6."

patterns-established:
  - "encoderModeDefinitions[modeId] shape: { desc, topEncoderColor, deviceEncoderColor, topEncoderTip(c), deviceEncoderTip(c), bankNavTip(i), ringTip(c) } — Plan 04 will mirror this with matrixModeDefinitions and Plan 05 with modifierOverlayDefinitions."
  - "setEncoderMode(modeId) does THREE things: (1) update module-level currentEncoderMode, (2) repaint mode-strip .active class + encoder backgroundColor, (3) refresh #legend-desc innerHTML. No re-attaching of tooltip handlers — they read currentEncoderMode at hover time."

requirements-completed: [DOC-02, DOC-03, DOC-04, DOC-06]

duration: ~6 min
completed: 2026-05-02
---

# Phase 6 Plan 3: Wire Encoder Mode Strip Behavior Summary

**Encoder mode strip becomes interactive: clicking Pan / SendA-C / User1-3 repaints the 16 encoders, ring LEDs, and #legend-desc, with mode-aware tooltips citing EncModeSelectorComponent.py and Pan16DeviceComponent.py source line ranges.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-05-02 (worktree-agent-a35e1c877767ffaf9 base a19ec50)
- **Completed:** 2026-05-02
- **Tasks:** 1
- **Files modified:** 1 (docs/manual.html)

## Accomplishments

- All 7 encoder modes (Pan / SendA / SendB / SendC / User1 / User2 / User3) defined in `encoderModeDefinitions` with per-mode color palette + tooltip getters covering top encoders, device encoders, ring LEDs, and the four bank-nav buttons.
- `setEncoderMode(modeId)` repaints in three steps (mode-strip highlight → encoder backgroundColor → #legend-desc innerHTML) and is invoked initially with `'Pan'` per D-04b.
- The four placeholder tooltip closures from Plan 02 (top encoder / ring LED / device encoder / bank-nav) replaced with the contentGetter indirection pattern (`encoderModeDefinitions[currentEncoderMode]` lookup) — per PATTERNS section 1e.
- Mode-button tooltips include mode-specific `<div class="related">` extras: Pan = rest-state note (D-04b), Send A/B/C = 400ms / 4-ticks toggle/momentary citation (DOC-03 unification), User1-3 = unmapped citation (number_of_modes() == 4).
- Pan tooltips reference `device.parameters[1:9]` and `device.parameters[9:17]` per Pan16DeviceComponent.py:30–42; Send tooltips reference EncModeSelectorComponent.py:84–105 (`_mode_value`); ramp tooltip references `visible_macro_count` per ShiftableTransportComponent.py:362–366 (DOC-06).
- Terminology gate: zero occurrences of `snapshot` (case-insensitive); the word `variations` appears once inside the Pan tooltip's ramp `.related` block (intentional, references Plan 05 territory).

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement encoderModeDefinitions, setEncoderMode(), and re-wire encoder/ring/bank-nav tooltips** — `ff41370` (feat)

## Files Created/Modified

- `docs/manual.html` (731 → 897 lines) — added `encoderModeDefinitions` object literal, `setEncoderMode(modeId)` function, `.encoder-mode-btn` click + tooltip wiring inside `DOMContentLoaded`, and replaced 4 placeholder tooltip closures with contentGetter indirection.

## encoderModeDefinitions keys (per D-04a)

| Key | desc summary | topEncoderColor | deviceEncoderColor |
|---|---|---|---|
| `Pan` | 16-macro mapping; per-track pan disabled | `#3b82f6` (blue) | `#3b82f6` |
| `SendA` | Send A per track; toggle/momentary; device row stays Pan16 bank 1 | `#10b981` (green) | `#3b82f6` |
| `SendB` | Send B; same model as SendA | `#f59e0b` (amber) | `#3b82f6` |
| `SendC` | Send C; same model as SendA | `#ef4444` (red) | `#3b82f6` |
| `User1` | Unmapped; number_of_modes() == 4 | `var(--pad-off)` | `var(--pad-off)` |
| `User2` | Unmapped (same as User1) | `var(--pad-off)` | `var(--pad-off)` |
| `User3` | Unmapped (same as User1) | `var(--pad-off)` | `var(--pad-off)` |

## Source-line citations in tooltip prose

| Citation | Where used | What it grounds |
|---|---|---|
| `Pan16DeviceComponent.py:30–42` | Pan top-encoder tooltip `.related` | parameter_banks slices [1:17] into 8-param chunks |
| `Pan16DeviceComponent.py:17–28` | Pan device-encoder tooltip `.related` | set_device override re-asserts _fixed_bank_index for bank-1 instance (two-instance bank isolation) |
| `EncModeSelectorComponent.py:84–105` | SendA/B/C tooltips `.related` and SendA/B/C mode-button tooltips `.related` | `_mode_value` toggle/momentary state machine with hardcoded revert to mode 0 |
| `EncModeSelectorComponent.py:9–10` (LONG_PRESS_DELAY = 4) | SendA tooltip `.related` (`4 ticks × 100ms`) | 400ms threshold derivation |
| `EncModeSelectorComponent.py:80–81` | User1/2/3 tooltips `.related` and User mode-button tooltips `.related` | `number_of_modes() == 4` only covers Pan + SendA + SendB + SendC |
| `visible_macro_count` (ShiftableTransportComponent.py:362–366) | Pan top-encoder tooltip `.related` | DOC-06 ramp absolute 0–127 mapping |

## contentGetter pattern adopted

Four `addTooltipEvents(...)` calls inside `buildLayout()` were converted from inline-string getters to the contentGetter closure pattern (PATTERNS section 1e):

```js
addTooltipEvents(el, () => {
  const def = encoderModeDefinitions[currentEncoderMode];
  return def && def.topEncoderTip ? def.topEncoderTip(c) : '';
});
```

Targets:
- `.top-encoder` (8 cells) → `def.topEncoderTip(c)` where `c = parseInt(el.dataset.col, 10)`
- `.top-encoder-ring` (8 cells) → `def.ringTip(c)`
- `.device-encoder` (8 cells) → `def.deviceEncoderTip(c)`
- `.device-bank-nav` (4 cells) → `def.bankNavTip(i)` where `i = parseInt(el.dataset.idx, 10)`

Verifiable: `grep -c 'encoderModeDefinitions\[currentEncoderMode\]' docs/manual.html` = **4** (≥ 4 required).

This means flipping `currentEncoderMode` via `setEncoderMode('SendA')` is sufficient to refresh tooltip text on next hover — no re-attaching of handlers needed.

## User1/User2/User3 unmapped — explicit confirmation

Each User-mode tooltip explicitly states `(unmapped)` or "Not bound by this script" or "User1/User2/User3 are not bound by this script", and the `desc` field cites `EncModeSelectorComponent.py:80–81 — number_of_modes() == 4`. The mode-button tooltip extra block adds: `Unmapped: User1/User2/User3 are not bound by this script. See EncModeSelectorComponent.py:80–81 (number_of_modes() == 4).`

`grep -q 'unmapped' docs/manual.html` → **PASS**.

## Terminology gate (D-09 / D-10)

`grep -ci 'snapshot' docs/manual.html` = **0** — passes.

The word `variations` appears in the Pan top-encoder tooltip's ramp `.related` block (`interpolates between variations (DOC-06)`) — acceptable per the plan's must-haves truth #7 ("the words 'variation' / 'variations' may appear (foreshadowing Plan 05)").

## Decisions Made

- **`dataset.idx` for bank-nav tooltips.** Switched from `el.textContent`-based to `parseInt(el.dataset.idx, 10)` so the closure receives the index (0..3) and the lookup table inside `bankNavTip(i)` (`['◀ Bank', 'Bank ▶', '◀ Dev', 'Dev ▶'][i]`) is deterministic. data-idx was already set on each `.device-bank-nav` cell by Plan 02.
- **Single `DOMContentLoaded` callback.** Wired the `.encoder-mode-btn` click handlers + tooltip handlers + initial `setEncoderMode('Pan')` paint inside the existing DOMContentLoaded callback (after `buildLayout()`) rather than registering a second listener. Keeps initialization order deterministic: placeholder removal → buildLayout (attaches all per-pad tooltips) → encoder-mode wiring (attaches mode-button click + tooltips) → initial paint.
- **User1/2/3 `desc` is verbose, not "reserved".** The desc cites `EncModeSelectorComponent.py:80–81 (number_of_modes() == 4)` directly so a reader who hovers the User1 button immediately sees the source-of-truth line range. Per PATTERNS Behavioral-accuracy traceability constraint.

## Deviations from Plan

None — plan executed exactly as written. The plan's `<action>` block was prescriptive about all eight components (A–F): the 7-key `encoderModeDefinitions` literal, the `setEncoderMode()` body, the 4 contentGetter replacements, the click-handler wiring, and the mode-button tooltip extras. All eight were applied verbatim.

Minor refinement (not a deviation, internal): the bank-nav contentGetter uses `parseInt(el.dataset.idx, 10)` rather than the plan's `(i)` placeholder. This matches the existing data-idx attribute on each `.device-bank-nav` cell (Plan 02) and keeps the closure pure.

## Issues Encountered

None.

## Verification

### Acceptance criteria (from plan)

| Criterion | Result |
|---|---|
| `function setEncoderMode(` defined exactly once | PASS (`grep -c` = 1) |
| `encoderModeDefinitions` contains 7 keys: Pan / SendA / SendB / SendC / User1 / User2 / User3 | PASS (all 7 present) |
| String `400ms` appears | PASS |
| String `4 ticks` appears | PASS |
| String `EncModeSelectorComponent.py` appears | PASS (multiple cites) |
| String `Pan16DeviceComponent.py` appears | PASS (2 cites) |
| String `visible_macro_count` appears | PASS (Pan ramp tooltip) |
| String `parameters[1:17]` OR `device.parameters[` appears | PASS (`device.parameters[` present) |
| DOMContentLoaded calls `setEncoderMode('Pan')` after `buildLayout()` | PASS |
| Click handlers wired on every `.encoder-mode-btn` | PASS |
| `grep -c 'encoderModeDefinitions\[currentEncoderMode\]'` ≥ 4 | PASS (= 4) |
| Case-insensitive count of `snapshot` is 0 | PASS |
| User1/2/3 tooltips call out "unmapped" / "not bound by this script" | PASS |

### Automated chain (plan's `<verify><automated>`)

```bash
grep -q 'function setEncoderMode(' docs/manual.html && \
grep -q 'encoderModeDefinitions' docs/manual.html && \
grep -q "encoderModeDefinitions\['Pan'\]\|'Pan': {" docs/manual.html && \
grep -q "'SendA': {" docs/manual.html && \
grep -q "'SendB': {" docs/manual.html && \
grep -q "'SendC': {" docs/manual.html && \
grep -q "'User1': {" docs/manual.html && \
grep -q "'User2': {" docs/manual.html && \
grep -q "'User3': {" docs/manual.html && \
grep -q '400ms' docs/manual.html && \
grep -q '4 ticks' docs/manual.html && \
grep -q 'parameters\[1:17\]\|device.parameters\[' docs/manual.html && \
grep -q 'visible_macro_count' docs/manual.html && \
grep -q 'EncModeSelectorComponent.py' docs/manual.html && \
grep -q 'Pan16DeviceComponent.py' docs/manual.html && \
[ "$(grep -ci 'snapshot' docs/manual.html)" = "0" ]
```

**Result: PASS** — full chain returns true.

### JS syntax check

```bash
node -e "const fs=require('fs'); const html=fs.readFileSync('docs/manual.html','utf8');
         const m=html.match(/<script>([\s\S]*?)<\/script>/);
         new Function(m[1]); console.log('JS parses cleanly');"
```

**Result: PASS** — JS parses cleanly.

### Manual verification (deferred to user)

Open `docs/manual.html` in a browser:
- Click `Pan` → 16 encoders blue, legend shows "Encoder Mode: Pan — 16-macro mapping…", Pan button cyan-glow.
- Click `SendA` → top encoders green, device encoders stay blue, legend shows Send A description, SendA button cyan-glow.
- Click `SendB` → top encoders amber, device encoders stay blue, legend shows Send B description.
- Click `SendC` → top encoders red, device encoders stay blue, legend shows Send C description.
- Click `User1` → all 16 encoders gray, legend shows User1 description with EncModeSelectorComponent.py:80–81 reference.
- Hover any top encoder in `Pan` mode → tooltip mentions `device.parameters[N]`, `Pan16DeviceComponent.py:30–42`, `visible_macro_count`.
- Hover any top encoder in `SendA` mode → tooltip mentions `Track N's Send A level`, `400ms`, `4 ticks × 100ms`, `EncModeSelectorComponent.py:84–105`.
- Hover any top encoder in `User1` mode → tooltip says `(unmapped)`, references `EncModeSelectorComponent.py:80–81`.

## Self-Check: PASSED

- File `docs/manual.html` exists at expected path: FOUND.
- Commit `ff41370` (`feat(06-03): wire encoder mode strip + setEncoderMode() repaint`) exists in `git log`: FOUND.
- All automated grep checks pass.
- All acceptance criteria from the plan satisfied.
- Embedded JavaScript parses cleanly via `new Function(...)`.
- No untracked files left in the worktree after the commit.
- No file deletions in the commit.

## Commits

| Task | Description | Commit | Files |
|---|---|---|---|
| 1 | Wire encoder mode strip + setEncoderMode() repaint + contentGetter tooltips | `ff41370` | `docs/manual.html` (modified, 731 → 897 lines) |

## Next Phase Readiness

- Plan 04 (matrix mode wiring) can mirror this structure: `matrixModeDefinitions` + `setMatrixMode(modeId)` + same contentGetter indirection on `.grid-pad` / `.scene-launch` / `.arm-pad` / `#master-select`.
- Plan 05 (modifier overlay) can adopt the same pattern for Solo/Mute/Send button tooltips (toggle/momentary unified model, DOC-03).
- No blockers.

---
*Phase: 06-create-user-manual*
*Completed: 2026-05-02*
