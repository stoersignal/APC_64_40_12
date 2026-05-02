# Phase 6: Create user manual — Pattern Map

**Mapped:** 2026-05-02
**Files analyzed:** 6 new/modified files
**Analogs found:** 5 / 6 (TROUBLESHOOTING.md synthesized — no direct analog)

This phase is **documentation-only**. No source `.py` files are modified. The "analogs" are template files in `example/` and the existing `README.md`. The manual must be **traceable** to behavioral source code; this map records the exact line ranges that downstream writers must read to ground every claim.

---

## File Classification

| New / Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------------|------|-----------|----------------|---------------|
| `docs/manual.html` | doc-interactive | static HTML + DOM repaint | `example/lp-interactive-map.html` | exact (template) |
| `docs/gen_apc40_layout.py` | doc-generator | file-I/O (SVG write-out) | `example/gen_svg.py` | exact (template) |
| `docs/apc40-layout.svg` | doc-static | n/a (generated artifact) | `example/lp-pro-mk3-layout.svg` | exact (output style) |
| `docs/INSTALL.md` | doc-prose | n/a | `README.md` lines 7–20 (install paragraph) | role-match |
| `docs/TROUBLESHOOTING.md` | doc-prose | n/a | none (synthesize from CONTEXT D-11/D-12, REQUIREMENTS DOC-08, source code) | no analog |
| `README.md` (rewrite) | doc-prose | n/a | current `README.md` (in place) | exact |

---

## Pattern Assignments

### 1. `docs/manual.html` (doc-interactive, mode-driven repaint)

**Analog:** `example/lp-interactive-map.html` (637 lines, single self-contained file).

**Strategy:** Port the file verbatim, then (a) rename CSS tokens `--lp-*` → `--apc-*`, (b) reshape the CSS Grid `grid-template-areas` from 8×8 to APC40 proportions (5×8 clip grid + transport row + encoder strips + sliders), (c) generalize the single `currentMode` + `setMode()` into **three orthogonal mode strips** (encoder mode / matrix mode / modifier overlay) with their own state variables and repaint regions, (d) replace `modeDefinitions` content with APC40-specific definitions sourced from `EncModeSelectorComponent.py`, `MatrixModesComponent.py`, `Matrix_Maps.py`, `StepSequencerComponent.py`, `ShiftableSelectorComponent.py`.

#### 1a. CSS variable block to port (lines 8–25)

Copy verbatim, then rename `--lp-case` → `--apc-case`, `--lp-border` → `--apc-border`. Keep all `--glow-*` and `--tooltip-*` tokens unchanged — they are semantic, not Launchpad-specific.

```css
:root {
    --bg-color: #0f172a;
    --lp-case: #1e293b;          /* RENAME → --apc-case */
    --lp-border: #334155;        /* RENAME → --apc-border */
    --pad-off: #334155;
    --text-main: #f8fafc;
    --text-dim: #94a3b8;
    --glow-cyan: #06b6d4;
    --glow-magenta: #ec4899;
    --glow-blue: #3b82f6;
    --glow-green: #10b981;
    --glow-yellow: #f59e0b;
    --glow-red: #ef4444;
    --glow-orange: #f97316;
    --glow-purple: #a855f7;
    --tooltip-bg: rgba(15, 23, 42, 0.95);
    --tooltip-border: rgba(56, 189, 248, 0.5);
}
```

**Acceptance criterion for the planner:** the planner's PLAN.md must list these exact 16 token names and instruct that only `--lp-case` and `--lp-border` get renamed; the rest are kept. The dark-theme/neon-accent palette is preserved.

#### 1b. CSS Grid layout pattern (lines 60–82) — must be reshaped for APC40

Source pattern (Launchpad 8×8):

```css
.device {
    background: var(--lp-case);
    padding: 40px;
    border-radius: 30px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 2px 4px rgba(255, 255, 255, 0.05);
    border: 2px solid var(--lp-border);
    display: grid;
    gap: 20px;
    grid-template-areas:
        ". t t t t t t t t ."
        ". tx tx tx tx tx tx tx tx ."
        "l g g g g g g g g r"
        "l g g g g g g g g r"
        "l g g g g g g g g r"
        ...
        ". b b b b b b b b ."
        "s c c c c c c c c .";
    position: relative;
}
```

For APC40 the grid must reshape per CONTEXT D-07 — 5×8 clip grid (not 8×8), plus dedicated areas for transport row, encoder strips (top + device), sliders, and three mode strips. The planner is to define the new `grid-template-areas`. **The CSS pattern (display: grid + named areas + gap) is preserved verbatim.**

#### 1c. Pad styles (lines 84–125) — ported verbatim

```css
.pad {
    background: var(--pad-off);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-size: 0.65rem;
    font-weight: 600;
    width: 60px;
    height: 60px;
    color: white;
    box-shadow: inset 0 2px 4px rgba(255,255,255,0.1), inset 0 -2px 4px rgba(0,0,0,0.3);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    word-break: break-word;
    padding: 2px;
    border: 1px solid rgba(0,0,0,0.3);
    text-shadow: 0 1px 2px rgba(0,0,0,0.8);
    position: relative;
    box-sizing: border-box;
}
.pad.rect-h { height: 35px; border-radius: 8px; }
.pad.rect-v { width: 60px; height: 60px; border-radius: 30px; }
.pad.circle { width: 60px; height: 60px; border-radius: 50%; }
.pad.active {
    transform: scale(0.95);
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.2);
}
.pad:hover { filter: brightness(1.2); }
```

#### 1d. Tooltip CSS (lines 154–194) — ported verbatim

```css
#tooltip {
    position: fixed;
    background: var(--tooltip-bg);
    color: var(--text-main);
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid var(--tooltip-border);
    max-width: 280px;
    font-size: 0.85rem;
    line-height: 1.4;
    pointer-events: none;
    opacity: 0;
    transform: translateY(10px);
    transition: opacity 0.2s ease, transform 0.2s ease;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    z-index: 1000;
    backdrop-filter: blur(8px);
}
#tooltip.visible { opacity: 1; transform: translateY(0); }
#tooltip strong {
    display: block;
    color: #38bdf8;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 0.25rem;
}
#tooltip .related {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: var(--text-dim);
    border-top: 1px dashed rgba(255,255,255,0.1);
    padding-top: 0.5rem;
}
```

#### 1e. Tooltip JS function shapes (lines 401–451) — ported verbatim, no changes

```javascript
let tooltipTimeout;

function showTooltip(e, content) {
    clearTimeout(tooltipTimeout);
    tooltipTimeout = setTimeout(() => {
        tooltip.innerHTML = content;
        tooltip.classList.add('visible');
        const x = e.clientX, y = e.clientY;
        const w = window.innerWidth, h = window.innerHeight;
        let tx = x + 15, ty = y + 15;
        if (tx + tooltip.offsetWidth > w) tx = x - tooltip.offsetWidth - 15;
        if (ty + tooltip.offsetHeight > h) ty = y - tooltip.offsetHeight - 15;
        tooltip.style.left = `${tx}px`;
        tooltip.style.top = `${ty}px`;
    }, 350); // 350ms hover delay
}

function hideTooltip() {
    clearTimeout(tooltipTimeout);
    tooltip.classList.remove('visible');
}

function addTooltipEvents(element, contentGetter) {
    element.addEventListener('mouseenter', (e) => {
        const content = contentGetter();
        if (content && content !== '') showTooltip(e, content);
    });
    element.addEventListener('mousemove', (e) => {
        if (tooltip.classList.contains('visible')) {
            const x = e.clientX, y = e.clientY;
            let tx = x + 15, ty = y + 15;
            if (tx + tooltip.offsetWidth > window.innerWidth) tx = x - tooltip.offsetWidth - 15;
            if (ty + tooltip.offsetHeight > window.innerHeight) ty = y - tooltip.offsetHeight - 15;
            tooltip.style.left = `${tx}px`;
            tooltip.style.top = `${ty}px`;
        }
    });
    element.addEventListener('mouseleave', hideTooltip);
}
```

**Acceptance criterion:** The 350ms hover delay, the offscreen-edge flip logic, and the `contentGetter` indirection (so tooltips re-evaluate on each hover and reflect the *current* mode) must all be preserved.

#### 1f. `modeDefinitions` object structure (lines 236–386) — port the **shape**, replace the content

The Launchpad version is a single object keyed by mode id, each value supplying repaint functions per region:

```javascript
const modeDefinitions = {
    'Standard': {
        desc: '...HTML for legend...',
        color: 'var(--pad-off)',
        grid: (r, c) => `S${r}<br>Slc ${c}`,           // label generator
        gridColor: (r, c) => '#2563eb',                 // bg-color generator
        gridTip: (r, c) => `<strong>...</strong>...`,  // tooltip HTML generator
        lsb: (r) => `Select<br>Strip ${r}`,
        lsbColor: '#10b981',
        lsbTip: (r) => `<strong>...</strong>...`,
        rsb: (r) => `Group<br>Cycle ${r}`,
        rsbColor: '#f59e0b',
        rsbTip: (r) => `<strong>...</strong>...`,
        // optional tAux / bAux overrides
    },
    'Record': { /* same shape */ },
    'Pattern': { /* same shape */ },
    // ... 8 entries total
};
```

**APC40 generalization (per CONTEXT D-04, D-04a):** split into three independent definition tables, each driving a different region:

- `encoderModeDefinitions` — keys: `'Pan'`, `'SendA'`, `'SendB'`, `'SendC'`, `'User1'`, `'User2'`, `'User3'`. Each entry supplies repaint functions for the 8 top encoders, the 8 device encoders, and the device bank-nav buttons. Source: `EncModeSelectorComponent.py:107–159` (the `update()` method).
- `matrixModeDefinitions` — keys: `'ClipLaunch'`, `'SessionOverview'`, `'NoteMode1'`–`'NoteMode6'`, `'StepSequencer'`. Each entry supplies repaint functions for the 5×8 clip grid + Track Stop row. Sources: `MatrixModesComponent.py:114–207` (the `_set_modes()` and `_set_note_mode()` methods); `Matrix_Maps.py` (the `PATTERN_N`/`CHANNEL_N`/`NOTEMAP_N` literals — read from the file at writing time, do not hard-code an out-of-sync copy per CONTEXT D-05); `StepSequencerComponent.py` (sequencer overlay behavior).
- `modifierOverlays` — keys: `'ShiftHeld'`, `'SaveMode'`. Each entry supplies a per-button outline/glow class and replacement tooltip HTML. They **stack on top** of the active encoder + matrix modes. Sources: `ShiftableSelectorComponent.py:92–119` (the `update()` method showing what Shift remaps); `APC_64_40_9.py:158–176` (the Shift+Tap-Tempo save flow).

#### 1g. `setMode()` repaint logic (lines 565–631) — port the structure, generalize to three strips

Source pattern (one mode at a time):

```javascript
function setMode(modeId) {
    currentMode = modeId;
    let renderId = getRenderId();
    const def = modeDefinitions[renderId];
    if (!def) return;

    legendDesc.innerHTML = `<span style="...">${modeId}</span> <br/> ` +
        (modeDefinitions[modeId] ? modeDefinitions[modeId].desc : def.desc);

    document.querySelectorAll('.top-row-btn').forEach(btn => {
        if (btn.dataset.mode === modeId) {
            btn.style.backgroundColor = topModes.find(m=>m.id === modeId).color;
            btn.style.color = '#000';
            btn.style.boxShadow = `0 0 15px ${topModes.find(m=>m.id === modeId).color}`;
        } else {
            btn.style.backgroundColor = 'var(--pad-off)';
            btn.style.color = 'white';
            btn.style.boxShadow = 'none';
        }
    });

    document.querySelectorAll('.lsb-pad').forEach((btn, r) => {
        btn.innerHTML = def.lsb(r);
        btn.style.backgroundColor = def.lsbColor;
        btn.style.boxShadow = `0 0 10px ${def.lsbColor}40`;
    });
    // ... rsb, grid, tAux, bAux similarly
}
```

**Generalization for APC40:** three sibling functions `setEncoderMode(id)`, `setMatrixMode(id)`, `toggleModifierOverlay(id)`, each scoped to its own region. Defaults are `Pan + ClipLaunch + no overlay` (CONTEXT D-04b). Click the same mode button again to revert (preserve the toggle behavior at line 469: `currentMode === mode.id ? 'Standard' : mode.id`).

#### 1h. `buildLayout()` DOM construction (lines 460–563) — port the idiom, change the regions

Source pattern: one element loop per region, each element gets `addTooltipEvents(btn, () => modeDefinitions[getRenderId()]?.gridTip(r, c) ?? '')`. The `contentGetter` is a closure so tooltips re-evaluate on hover and pick up the latest mode.

```javascript
function buildLayout() {
    // Top Row mode buttons
    topModes.forEach((mode, i) => {
        const btn = document.createElement('div');
        btn.className = 'pad rect-h top-row-btn';
        btn.dataset.mode = mode.id;
        btn.innerHTML = mode.label;
        btn.style.gridColumn = `${i + 2}`;
        btn.style.gridRow = `1`;
        btn.onclick = () => setMode(currentMode === mode.id ? 'Standard' : mode.id);
        addTooltipEvents(btn, () => `<strong>Mode: ${mode.id}</strong>...`);
        device.appendChild(btn);
    });

    // Central Grid (8x8 → APC40 will be 5x8)
    for (let r = 0; r < 8; r++) {
        for (let c = 0; c < 8; c++) {
            const btn = document.createElement('div');
            btn.className = `pad grid-pad r${r} c${c}`;
            btn.style.gridColumn = `${c + 2}`;
            btn.style.gridRow = `${r + 3}`;
            addTooltipEvents(btn, () => {
                const renderId = getRenderId();
                return modeDefinitions[renderId]?.gridTip ? modeDefinitions[renderId].gridTip(r, c) : '';
            });
            device.appendChild(btn);
        }
    }
    // ... lsb, rsb, b-aux, t-aux, shift similarly
}
```

For APC40, regions to construct (per CONTEXT D-07):
- 5×8 clip-launch grid (`r` in 0..4, `c` in 0..7)
- 8 Track Stop buttons (one row below the grid; doubles as Note/User Mode row when `USE_STOP_ROW_*` is True)
- 8 Solo + 8 Mute + 8 Activator/Arm columns (per-track)
- 8 Scene Launch buttons (right column)
- 8 top encoders + their ring-LED indicators
- 8 device encoders + 8 device bank buttons
- 9 sliders + crossfader (rendered as labeled rectangles, NOT interactive — see D-07)
- Transport row: Play / Stop / Record / Tap Tempo / Nudge± / Detail View
- Encoder mode strip: Pan / Send A / Send B / Send C / User1 / User2 / User3
- Matrix mode strip: Clip Launch / Session Overview / Note Modes 1–6 / Step Sequencer
- Shift, Save mode toggle

#### 1i. Tooltip HTML markup pattern (verbatim from example, lines 229, 234, 269, 281, 304, 471, 560)

The example uses `<strong>HEADING</strong> body text <div class="related"><em>label:</em> related-info</div>`. Concrete excerpts:

```html
<!-- Example from line 269 (Pattern mode bar-length tooltip) -->
<strong>Bar Length: 4</strong>Selects the length of the recording loop for the new strip. When 'Manual', stops only when pressed again.<div class="related"><em>Works with:</em> RSB to arm recording.</div>

<!-- Example from line 304 (Pattern mode slot tooltip) -->
<strong>Activate Slot 3</strong>Activates this slot for sequential playback.<div class="related"><em>Shift:</em> Shift+Tap selects for edit. Shift+Double-Tap clears it entirely!</div>

<!-- Example from line 560 (Shift button tooltip) -->
<strong>Shift Key</strong>Held down in conjunction with Aux keys or Grid keys to access deeper setup menus, preset swapping, or secondary track states.
```

**APC40 ports** (per CONTEXT specifics — port the *structure* verbatim, write the *content* against source):

```html
<!-- Solo button (Track 1) — sourced from ToggleMomentaryChannelStripComponent.py:8,26-39 -->
<strong>Solo (Track 1) — Toggle / Momentary</strong>Short tap toggles solo on/off. Hold ≥400ms acts momentary — solo activates on press-down and reverts on release.<div class="related"><em>Long-press on already-soloed track:</em> temporarily inverts (un-solos) until release.<em>Multi-track:</em> Each Solo button operates independently.</div>

<!-- Pan button — sourced from EncModeSelectorComponent.py:117-137, Pan16DeviceComponent.py:30-42 -->
<strong>Pan (Encoder Mode)</strong>Maps top 8 encoders to device parameters 1–8 and device 8 encoders to parameters 9–16. Per-track pan is disabled in this mode. Bank navigation lives on the device row only.<div class="related"><em>Click again:</em> Default Pan mode is the rest state — no toggle revert.</div>

<!-- Send A button — sourced from EncModeSelectorComponent.py:97-105 -->
<strong>Send A (Encoder Mode) — Toggle / Momentary</strong>Short tap latches Send A onto the top 8 encoders. Hold ≥400ms acts momentary — reverts to Pan on release.<div class="related"><em>Same model as Solo/Mute:</em> 4 ticks × 100ms threshold.</div>

<!-- Tap Tempo — sourced from ShiftableTransportComponent.py:158-176 -->
<strong>Tap Tempo — Recall Variation</strong>Press to recall the currently selected Macro Rack variation, with optional ramp interpolation.<div class="related"><em>Shift+Tap (hold):</em> save the current macro state into the active variation slot. Save is cancelled if any top encoder is touched during the hold (ramp-edit safety).</div>

<!-- Nudge buttons — sourced from ShiftableTransportComponent.py:137-156 -->
<strong>Nudge ↑ / ↓ — Variation Step</strong>Step forward / back through the appointed device's variation slots.<div class="related"><em>Shift+Nudge Back:</em> toggle lock-to-device (device-follow-selection on/off).</div>

<!-- Note Mode pad — sourced from MatrixModesComponent.py:176-207 + Matrix_Maps.py -->
<strong>Note Mode 1 — Pad (Row 0, Col 3)</strong>Sends MIDI note 59 on channel 10 (CHANNEL_1). LED color: red (PATTERN_1 = 3).<div class="related"><em>Customizing this mode:</em> open <code>Matrix_Maps.py</code> in any text editor and edit PATTERN_1 / CHANNEL_1 / NOTEMAP_1.</div>
```

**Acceptance criterion:** every tooltip in the rendered HTML must trace to a numbered source line in the canonical-refs files (Section 5 below). Writers may not invent behavior.

---

### 2. `docs/gen_apc40_layout.py` (doc-generator, file-I/O)

**Analog:** `example/gen_svg.py` (92 lines, plain Python, no deps).

**Strategy:** mirror the structure exactly — list-of-strings + final `'\n'.join(...)` write. Adjust loop bounds and labels for APC40 layout. The static SVG renders the **default state only** (Pan + Clip Launch, no overlays) per CONTEXT D-08a.

#### 2a. Generator scaffold (lines 1–4, 89–92) — port verbatim

```python
import json

svg_out = []
svg_out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="1000" height="1000" style="background-color:#0f172a; border-radius:12px; font-family:sans-serif;">')

# ... body ...

svg_out.append('</svg>')

with open('lp-pro-mk3-layout.svg', 'w') as f:   # change filename to apc40-layout.svg
    f.write('\n'.join(svg_out))
```

#### 2b. Color tokens (lines 9–15) — port verbatim

```python
color_grid = "#cbd5e1"
color_top  = "#3b82f6"
color_bot  = "#64748b"
color_rsb  = "#f59e0b"
color_lsb  = "#10b981"
color_text = "#ffffff"
```

#### 2c. Layout constants (lines 17–20) — adjust for APC40 proportions

```python
grid_start_x = 180
grid_start_y = 180
spacing = 70
pad_size = 55
```

For APC40 the planner may keep these constants and reshape the grid loop bounds (5 rows × 8 cols instead of 8×8) plus add areas for the Track Stop row, Solo/Mute/Arm columns, Scene Launch column, encoders, sliders, transport.

#### 2d. `draw_rect` helper (lines 22–27) — port verbatim

```python
def draw_rect(x, y, w, h, fill, text, font_size=12, text_color=color_text):
    svg_out.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="#0f172a" stroke-width="2"/>')
    if text:
        cx = x + w/2
        cy = y + h/2 + font_size/3
        svg_out.append(f'  <text x="{cx}" y="{cy}" font-size="{font_size}" fill="{text_color}" text-anchor="middle" font-weight="bold">{text}</text>')
```

#### 2e. Section ordering (lines 29–87) — preserve the order

```
1. Device outline (single rounded rect)
2. Main grid loop          (8×8 in example → 5×8 in APC40)
3. Top row mode buttons    (8 in example → 7 encoder mode buttons + transport row in APC40)
4. Aux rows                (top + bottom in example → Track Stop row, Solo/Mute/Arm rows in APC40)
5. Side buttons            (LSB, RSB in example → Scene Launch column in APC40)
6. Shift / setup button
7. Legend                  (4 swatches + labels in example)
8. Title text              (h1 + subtitle in example)
```

Per CONTEXT discretion: the SVG legend stays minimal — labels only, not full tooltip content.

---

### 3. `docs/apc40-layout.svg` (doc-static, generated artifact)

**Analog:** `example/lp-pro-mk3-layout.svg` (222 lines of `<rect>` + `<text>` pairs).

**Strategy:** This file is generated by `docs/gen_apc40_layout.py` and committed. Match the example's overall visual style: dark background `#0f172a`, rounded device case `#1e293b` with `#334155` border, color-coded button regions, legend at bottom, title at top. **No interactivity** — purely a printable poster.

Header pattern (line 1 — port verbatim):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="1000" height="1000" style="background-color:#0f172a; border-radius:12px; font-family:sans-serif;">
  <rect x="50" y="50" width="900" height="900" rx="30" fill="#1e293b" stroke="#334155" stroke-width="4"/>
```

Title pattern (lines 221–222 — port the structure):

```svg
<text x="500" y="70" font-size="28" fill="#ffffff" text-anchor="middle" font-weight="bold">APC40 Layout (Default — Pan + Clip Launch)</text>
<text x="500" y="95" font-size="16" fill="#cbd5e1" text-anchor="middle">v1.2 — see manual.html for interactive mode reference</text>
```

---

### 4. `docs/INSTALL.md` (doc-prose)

**Analog:** `README.md` lines 7–20 (the existing install paragraph). Move it into `docs/INSTALL.md` and expand per CONTEXT D-13.

#### 4a. README install excerpts to paste verbatim into INSTALL.md acceptance criteria

```markdown
Installation
------------

To install the script, just download this repository and move the entire "APC_64_40_11"
containing folder to the Ableton Remote Scripts directory.

Tip: Default Windows location:
  c:\programdata\Ableton\Live 11 Suite\Resources\MIDI Remote Scripts

So as an example all the files in this repository should be visible in
"c:\programdata\Ableton\Live 11 Suite\Resources\MIDI Remote Scripts\APC_64_40_11"
when you download the zip and extract it. It is possible that the folder name will end
with -MAIN. -MAIN should be removed, otherwise the script won't run.

On Mac OS X, find the Ableton application file and right click → "Show Package Contents".
You'll find the Remote Script folder in
  Contents/App-Resources/MIDI Remote Scripts

Once the script is in place, launch Live and open the preferences window.
In the "MIDI / Sync" tab, you'll find a listing of your connected MIDI gear.
Find your APC40, and in the left column, change the default selection to "APC_64_40_11".
Hold the shift button and press the various Track Selection buttons to switch modes.
If the clip grid changes to show new layouts, it's installed correctly.
```

**Acceptance criterion:** the planner's PLAN.md must enumerate the exact strings the install doc preserves:
- `c:\programdata\Ableton\Live 11 Suite\Resources\MIDI Remote Scripts` (Windows path)
- `Contents/App-Resources/MIDI Remote Scripts` (macOS path inside `Show Package Contents`)
- `Show Package Contents` (the macOS Finder verb)
- `MIDI / Sync` (the Live preferences tab name)
- The "shift + Track Selection" handshake-verification gesture
- The `-MAIN` folder-suffix gotcha (when downloading via GitHub ZIP)

Per CONTEXT D-13 the INSTALL.md must additionally cover:
- Live 11 + Live 12 confirmed compatibility (sourced from `__init__.py:31` `vendor_id=2536, product_ids=[115]` and `APC.py:127–148` Live-12-aware version fallback in `_send_introduction_message`).
- Input/Output rows + Track/Remote toggle checkboxes in MIDI prefs (sourced from `__init__.py:31` `inport(props=[NOTES_CC, SCRIPT, REMOTE]), outport(props=[SCRIPT, REMOTE])`).
- Verifying handshake via LED feedback (matrix lights up after `_on_handshake_successful` fires — `APC.py:94–100`).

---

### 5. `docs/TROUBLESHOOTING.md` (doc-prose, no analog)

**No direct analog.** Synthesize from CONTEXT D-11/D-12 (failure-mode list) and REQUIREMENTS DOC-08, with each entry traced to source code.

#### 5a. Entry template (per CONTEXT D-12)

```markdown
## <Failure mode title>

**What you might see:** <observable symptom from the user's perspective>

**Why it happens:** <one-paragraph explanation, technically grounded but plain language>

**What to do:** <ordered checklist of user-actionable steps>
```

#### 5b. Required entries (verbatim from CONTEXT D-11, source-traced)

| Entry | Source code reference |
|-------|----------------------|
| Handshake failures (script not in MIDI prefs, version mismatch, install path wrong) | `APC.py:71–100` (`handle_sysex`, `_on_identity_response`, `_on_dongle_response`, `_on_handshake_successful`); `APC.py:127–148` (`_send_introduction_message` Live 12 fallback); `__init__.py:30–32` (`get_capabilities`, vendor_id 2536, product_id 115) |
| Exclusive-solo bypass (Solo on track A doesn't un-solo track B) | `ToggleMomentaryChannelStripComponent.py:33` (`setattr(self._track, track_attr, not current)` writes `track.solo` directly without going through Live's exclusive-solo coordinator) |
| Fixed 400ms long-press threshold (not user-configurable) | `ToggleMomentaryChannelStripComponent.py:8` (`LONG_PRESS_DELAY = 4`); `EncModeSelectorComponent.py:10` (same constant) — comment explicitly notes "4 ticks x 100ms/tick = 400ms" |
| No per-track Send A/B/C buttons (hardware constraint) | `EncModeSelectorComponent.py:80–81` (`number_of_modes() == 4` — Pan/Send A/B/C are global mode selectors only) |
| No Track Activator (arm-record) buttons mapped (deliberate scope) | `ShiftableSelectorComponent.py:101–102, 112–113` — arm buttons are wired to channel-strip arm only when not in step-sequencer mode and not in shift mode; no momentary/Activator-style mapping |

---

### 6. `README.md` (rewrite — thin entry pointer)

**Analog:** the current `README.md` itself (38 lines).

**Strategy per CONTEXT D-02:** ~15–20 lines after rewrite. Structure:

```markdown
# APC_64_40_11

<one-paragraph project description — preserve the current opening line:
"Remote script for the Akai APC40 with Ableton Live 11 (and seems to be working
with 12) based on APC_40_9 Remote script. Bumped the remote script version to
Ableton Live 11 by converting the whole codestack from Python 2 to 3.">

![IMAGE](https://cdn.mos.cms.futurecdn.net/70f75473c4327722ce7a9e6d7f31b82d-1200-80.jpg)

## Documentation

- [Install & first-run setup](docs/INSTALL.md)
- [Interactive controller manual](docs/manual.html) — open in any browser
- [Troubleshooting & known limitations](docs/TROUBLESHOOTING.md)

Printable layout poster: [docs/apc40-layout.svg](docs/apc40-layout.svg)

Credits
-------
APC 64-40 script Originally developed by [Hanz Petrov](http://remotescripts.blogspot.com/p/apc-64-40.html).
Updated by [Fabrizio Poce](http://www.fabriziopoce.com/download.html) for Live 9.
Final update released [on the Ableton forums](https://forum.ableton.com/viewtopic.php?f=1&t=204713)
and lastly combined by [matthewcieplak](https://github.com/matthewcieplak/APC_64_40_9) and made
the remote script compatible with Ableton 9.x.x.

Uses parts from [Will Marshall's APCAdvanced script](https://github.com/willrjmarshall/AbletonDJTemplateUnsupported)
for the VU metering.
```

**Acceptance criterion:** Credits section preserved verbatim from current `README.md:32–37`. The PDF reference (`APC_64_40_quickstart_guide_rev_1.pdf`) and the broken `remotescripts.blogspot.com` instructions block are dropped per CONTEXT D-02.

---

## Shared Patterns

### Inline-only deliverables

**Source:** `example/lp-interactive-map.html` (single self-contained file, 637 lines, no external assets).
**Apply to:** `docs/manual.html`.
**Constraint:** No external CSS, JS, fonts, or build step. All styling and behavior inline. System-font fallbacks only (`'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).

### Tooltip discipline

**Source:** `example/lp-interactive-map.html` lines 229–305 (the example's tooltip strings).
**Apply to:** every interactive control in `docs/manual.html`.
**Pattern:** `<strong>HEADING</strong> body text <div class="related"><em>label:</em> related info</div>`. The `<strong>` heading is the first thing the user reads; the body is one or two sentences; the `.related` block is optional.

### Behavioral-accuracy traceability

**Source:** all canonical-ref files in CONTEXT lines 138–151.
**Apply to:** every prose claim in `docs/manual.html`, `docs/INSTALL.md`, `docs/TROUBLESHOOTING.md`.
**Constraint:** every behavioral claim must trace to a specific function, constant, or line range in the source. Writers may not invent timing values, button assignments, or feature behaviors. If a discrepancy between code and intended docs is discovered during writing, it is a Phase 6 deviation — flag it in the plan; do not change source code (CONTEXT code-context paragraph 3).

### Terminology discipline

**Source:** CONTEXT D-09, D-10.
**Apply to:** every prose deliverable.
**Constraint:** use Ableton's canonical **"variations"** in user-facing text. Internal code may keep "snapshot" wording. First mention in each artifact may include `(saved here as Macro Rack variations)`; subsequent uses are just "variations".

---

## Source-of-Truth File Index (line-precise read_first targets)

The planner's `read_first` blocks must point to these exact ranges so writers don't load full files:

| File | Lines / Function | What it tells you |
|------|------------------|-------------------|
| `ToggleMomentaryChannelStripComponent.py` | 8 (`LONG_PRESS_DELAY = 4`); 26–39 (`_handle_toggle_momentary` — fires-at-press-down state machine); 53–67 (set_solo/mute_button revert on disconnect); 69–79 (`disconnect()` revert); 81–91 (`_on_timer` countdown) | Solo/Mute toggle/momentary — 400ms threshold, fires on press-down, multi-track independence, disconnect safety |
| `EncModeSelectorComponent.py` | 9–10 (delay constants); 84–105 (`_mode_value` — Send momentary state machine); 107–159 (`update()` — full Pan / Send A / Send B / Send C wiring including Pan16 paths); 161–181 (`on_enabled_changed` — release on shift mode switch); 183–197 (`_on_timer` — `_send_ticks_delay` countdown + Pan-to-Vol delay) | Pan/Send mode selection; Send buttons toggle/momentary with hardcoded revert to Pan |
| `Pan16DeviceComponent.py` | 17–28 (`__init__` + `set_device` override re-asserting `_fixed_bank_index`); 30–42 (`_parameter_banks` — `device.parameters[1:17]` sequential 8-param chunks); 44–53 (bank-name + count) | 16-macro mapping — top encoders → params 1–8 (bank 0), device encoders → params 9–16 (bank 1) |
| `MatrixModesComponent.py` | 31–53 (`__init__` — stop-button matrix construction, PAD_TRANSLATIONS); 67–74 (`set_mode` override); 105–106 (`number_of_modes() == 8`); 114–172 (`_set_modes` — modes 0 Clip Launch, 1 Session Overview, 2–7 Note/User Modes 1–6); 176–207 (`_set_note_mode` — pattern/channel/notemap/use_stop_row/is_note_mode application) | Eight matrix base modes — modes 0/1 are framework-driven; modes 2–7 read from Matrix_Maps.py |
| `Matrix_Maps.py` | 21–22 (file's own "edit with any text editor" comment); 30–46 (Page 1 / User Mode 1 — USE_STOP_ROW_1, IS_NOTE_MODE_1, PATTERN_1 with LED color codes 0–127, CHANNEL_1); 48–62 (CHANNEL + NOTEMAP comments); 64–177 (Pages 2–8 / User Modes 2–6 — same shape); 179–189 (PAD_TRANSLATIONS for Drum Rack — 4×4) | User-editable Note/User Mode patterns. The PATTERN_1 comment (line 37) is the canonical LED-color-code legend (0=off, 1=green, 2=green blink, 3=red, 4=red blink, 5=yellow, 6=yellow blink, 7–127=green) |
| `StepSequencerComponent.py` | 29–37 (LED color constants); 38–84 (`__init__` — full state surface incl. `_velocity_index`, `_quantization_index`, `_loop_start_index`, `_bank_index`, `_key_index`, `_is_following`); 387–412 (`set_bank_buttons` + `_bank_button_value` — 8 bank pages); 414–432 (`set_follow_button` + `_follow_value`); 435–457 (`set_shift_button` + `_shift_value` — quantization toggle); 461–487 (`set_velocity_buttons` + `_velocity_button_value` — 5 vel levels per width); 490–520 (`set_loop_start_buttons` + handler); 523–547 (`set_loop_length_buttons` + handler); 549–571 (`set_lane_mute_buttons` + `q_step` — 5 quant levels); 573–605 (`_lane_mute_button_value` — quantization vs. lane-mute via `_shift_pressed`) | 64-step sequencer: bank pages, velocity, loop start/length, lane mute with shifted quantization, follow |
| `ShiftableSelectorComponent.py` | 32–59 (`__init__` — including `_step_sequencer_active = False` at line 59); 89–91 (`number_of_modes() == 2` — Shift held vs released); 92–119 (`update()` — full Shift overlay: when Shift released, channel-strip mute/solo/arm/select wired; when Shift held, those release and `matrix_modes`/`slider_modes` get the buttons instead); 137–173 (`_master_value` — Shift+Master toggles `_step_sequencer_active`, swaps sequencer enable with session/matrix-modes enable); 175–181 (`_on_note_mode_changed`) | Shift overlay — what gets remapped under Shift, plus the Shift+Master step-sequencer toggle |
| `ShiftableTransportComponent.py` | 28–45 (`__init__` ramp state — `_ramp_ms`, `_ramp_beat_index`, `_ramp_mode`, `_ramp_edit_active`, `_ramp_edit_touched`, `_ramp_active`, `_ramp_start_values`, `_ramp_target_values`, `_ramp_ticks_total`, `_ramp_ticks_remaining`, `_ramp_device`, `_ramp_macros`); 47–52 (disconnect ramp cleanup); 75–76 (`set_ramp_encoders`); 137–142 (`_nudge_up_value` — variation step forward); 144–156 (`_nudge_down_value` — variation step back, **Shift+Nudge Back toggles lock-to-device** at line 151); 158–177 (`_tap_tempo_value` — Tap=recall with ramp; Shift+Tap press=enter ramp edit; Shift+Tap release=save variation only if `_ramp_edit_touched` is False); 294–306 (`_enter_ramp_edit` / `_exit_ramp_edit`); 362–366 (`visible_macro_count` lookup); 368+ (`_recall_with_ramp`); 417+ (`_on_ramp_timer`) | Variation save/recall, ramp interpolation across visible_macro_count, Shift+Tap save-cancel safety, Shift+Nudge Back lock-to-device |
| `APC_64_40_9.py` | 46 (MatrixModesComponent import); 51 (StepSequencerComponent import); 184 (`matrix_modes = MatrixModesComponent(...)` instantiation); 186 (`self._sequencer = StepSequencerComponent(...)` instantiation); 187–195 (sequencer setter wiring — `set_bank_buttons` ← select_buttons, `set_follow_button` ← master_select_button, `set_velocity_buttons` ← arm_buttons, `set_lane_mute_buttons` ← scene_launch_buttons, `set_loop_start_buttons` ← mute_buttons, `set_loop_length_buttons` ← solo_buttons); 196 (`ShiftableSelectorComponent(...)` instantiation receiving sequencer + matrix_modes); 238–254 (Tap Tempo + Nudge button construction at notes 99/100/101 + transport.set_nudge_buttons / set_tap_tempo_button wiring); 304–305 (`self._transport.set_ramp_encoders(tuple(self._global_param_controls))`); 282–303 (`EncModeSelectorComponent` + Pan16 wiring); 321–330 (`_on_selected_track_changed` — device follow); 332–333 (`_product_model_id_byte → 115`) | Composition layer — every wiring point users will read about |
| `APC.py` | 7–9 (`MANUFACTURER_ID = 71`, `ABLETON_MODE = 65`, `DO_COMBINE`); 33–56 (`__init__` — `_device_id`, `_dongle_challenge`); 71–77 (`handle_sysex` — dispatches identity vs dongle by byte index); 78–86 (`_on_identity_response` — version logging, dongle-bypass note); 88–92 (`_on_dongle_response` — bypass deprecated encrypt_challenge); 94–100 (`_on_handshake_successful` — enables all components after `set_session_highlight`); 102–112 (`_update_hardware`); 120–124 (`_send_midi` with suppress flag); 126–148 (`_send_introduction_message` — try newer Live API, fall back to Live 12+ defaults of `major=12, minor=0, bugfix=0`) | Handshake protocol, version-fallback API for Live 12, what "successful handshake" means programmatically |
| `__init__.py` | 24–26 (`create_instance` factory — entry point Live calls); 30–32 (`get_capabilities` — `vendor_id=2536, product_ids=[115], model_name='Akai APC40'`, MIDI port props `NOTES_CC, SCRIPT, REMOTE` in / `SCRIPT, REMOTE` out) | Entry point + capabilities — used in INSTALL.md ("Live recognized your APC40") and TROUBLESHOOTING.md ("script not in MIDI prefs") |

---

## No Analog Found

| File | Reason | Mitigation |
|------|--------|------------|
| `docs/TROUBLESHOOTING.md` | No prior failure-mode catalog exists in repo or example folder | Synthesize from CONTEXT D-11/D-12 entry template + the 5 source-traced failure modes in section 5b above. The `What you might see / Why it happens / What to do` template (D-12) is the binding pattern. |

---

## Metadata

**Analog search scope:** repo root `*.py`, `example/`, current `README.md`.
**Files scanned:** 30 source files (entire repo) + 4 example files.
**Files actually read:** 11 source files + 4 example files + `README.md`.
**Pattern extraction date:** 2026-05-02.
