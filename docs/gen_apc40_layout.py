#!/usr/bin/env python3
"""Generate docs/apc40-layout.svg — static APC40 layout poster matching the
actual APC40 hardware footprint (per the user's reference image, 2026-05-02).
Run from any cwd: python3 docs/gen_apc40_layout.py — output is written next
to this script regardless of cwd."""

import os

# Colors — kept compatible with the original generator's palette.
color_grid = "#2563eb"      # clip-grid pads (default ClipLaunch matrix mode)
color_top  = "#3b82f6"      # top encoders
color_dev  = "#64748b"      # device encoders
color_rsb  = "#10b981"      # scene launch column
color_lsb  = "#06b6d4"      # solo row
color_mute = "#f59e0b"      # mute row
color_arm  = "#22c55e"      # activator-arm row
color_stop = "#94a3b8"      # track-stop row
color_tsel = "#475569"      # track-selection row
color_pan  = "#ef4444"      # pan/send physical buttons
color_xprt = "#475569"      # transport / detail-row
color_text = "#ffffff"
color_dim  = "#64748b"
color_shft = "#a855f7"      # shift button

# Layout constants — left zone (clip launch + tracks + sliders).
# 8 cols of pads, 65px stride, 50px pad size.
PAD = 50
GAP = 15
COL = PAD + GAP                    # 65
ROW = PAD + GAP                    # 65 (rectangular pads use 35px h + 15px gap)
H_RECT = 35                        # height of rectangular pads
H_RECT_ROW = H_RECT + GAP          # 50 stride for rectangular rows

# Origins
LEFT_X = 90                        # left edge of clip-grid col 1
TOP_Y = 110                        # top edge of clip-grid row 1
SCENE_X = LEFT_X + 8 * COL         # col 9 (scene launch / master)
RIGHT_X = SCENE_X + COL + 25       # right zone start (with spacer)

svg_out = []
svg_out.append(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 1000" '
    'width="1280" height="1000" '
    'style="background-color:#0f172a; border-radius:12px; font-family:sans-serif;">'
)


def rect(x, y, w, h, fill, label="", font_size=10, color=color_text, weight="bold"):
    svg_out.append(
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="{fill}" stroke="#0f172a" stroke-width="1.5"/>'
    )
    if label:
        cx = x + w / 2
        cy = y + h / 2 + font_size / 3
        svg_out.append(
            f'  <text x="{cx}" y="{cy}" font-size="{font_size}" fill="{color}" '
            f'text-anchor="middle" font-weight="{weight}">{label}</text>'
        )


def circle(cx, cy, r, fill, label="", font_size=10, color=color_text):
    svg_out.append(
        f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="#0f172a" stroke-width="1.5"/>'
    )
    if label:
        svg_out.append(
            f'  <text x="{cx}" y="{cy + font_size / 3}" font-size="{font_size}" '
            f'fill="{color}" text-anchor="middle" font-weight="bold">{label}</text>'
        )


# Device outline
svg_out.append(
    '  <rect x="40" y="40" width="1200" height="920" rx="30" '
    'fill="#1e293b" stroke="#334155" stroke-width="4"/>'
)

# Title
svg_out.append(
    '  <text x="640" y="80" font-size="22" fill="#ffffff" text-anchor="middle" '
    'font-weight="bold">APC40 Layout (default state — Pan + ClipLaunch, no overlays)</text>'
)
svg_out.append(
    '  <text x="640" y="100" font-size="11" fill="#cbd5e1" text-anchor="middle">'
    'v1.2 — see manual.html for the interactive mode reference</text>'
)

# ============================================================================
# LEFT ZONE — clip launch grid, scene launch, clip-stop, track-selection,
# solo / mute / activator-arm rows, channel sliders + master fader.
# ============================================================================

# Clip Launch grid: 5 rows × 8 cols (rows 1..5).
for r in range(5):
    for c in range(8):
        x = LEFT_X + c * COL
        y = TOP_Y + r * ROW
        rect(x, y, PAD, PAD, color_grid, f"T{c+1}·S{r+1}", font_size=10)

# Scene Launch column (5 cells, col 9, rows 1..5).
for r in range(5):
    x = SCENE_X
    y = TOP_Y + r * ROW + (PAD - H_RECT) / 2
    rect(x, y, PAD, H_RECT, color_rsb, f"Scn{r+1}", font_size=10)

# Clip Stop row (row 6, cols 1..8) + Stop-All-Clips (row 6, col 9).
y_stop = TOP_Y + 5 * ROW + 5
for c in range(8):
    x = LEFT_X + c * COL
    rect(x, y_stop, PAD, H_RECT, color_stop, f"Stop {c+1}", font_size=9)
rect(SCENE_X, y_stop, PAD, H_RECT, "#dc2626", "Stop\nAll", font_size=9)
# multiline support
svg_out[-1] = svg_out[-1].replace("Stop\nAll", "Stop All")

# Track Selection row (row 7, cols 1..8) + Master Select.
y_tsel = y_stop + H_RECT + GAP
for c in range(8):
    x = LEFT_X + c * COL
    rect(x, y_tsel, PAD, H_RECT, color_tsel, f"Track {c+1}", font_size=8)
rect(SCENE_X, y_tsel, PAD, H_RECT, color_tsel, "Master Sel", font_size=8)

# Solo row (row 8).
y_solo = y_tsel + H_RECT + GAP
for c in range(8):
    x = LEFT_X + c * COL
    rect(x, y_solo, PAD, H_RECT, color_lsb, f"Solo {c+1}", font_size=9)

# Mute row (row 9).
y_mute = y_solo + H_RECT + GAP
for c in range(8):
    x = LEFT_X + c * COL
    rect(x, y_mute, PAD, H_RECT, color_mute, f"Mute {c+1}", font_size=9)

# Activator-Arm row (row 10).
y_arm = y_mute + H_RECT + GAP
for c in range(8):
    x = LEFT_X + c * COL
    rect(x, y_arm, PAD, H_RECT, color_arm, f"Arm {c+1}", font_size=9)

# Channel sliders (8) + Master fader (col 9). Tall rectangles.
y_sld = y_arm + H_RECT + GAP + 5
SLD_H = 110
for c in range(8):
    x = LEFT_X + c * COL
    rect(x, y_sld, PAD, SLD_H, color_dim, f"Vol {c+1}", font_size=9)
rect(SCENE_X, y_sld, PAD, SLD_H, color_dim, "Master Vol", font_size=8)

# Cue Level knob (between PADS and FX, below Master fader).
y_cue = y_sld + SLD_H + GAP + 5
circle(SCENE_X + PAD / 2, y_cue + PAD / 2, PAD / 2 - 2, "#475569", "Cue\nLevel", font_size=8)
# (multiline label fallback — render two text lines manually)
svg_out[-1] = svg_out[-1].replace("Cue\nLevel", "Cue")
svg_out.append(
    f'  <text x="{SCENE_X + PAD / 2}" y="{y_cue + PAD / 2 + 12}" font-size="8" '
    f'fill="#ffffff" text-anchor="middle" font-weight="bold">Level</text>'
)

# ============================================================================
# RIGHT ZONE — TRACK CONTROL (top encoders + pan/send buttons),
# SELECT cursor pad cluster, TAP TEMPO + NUDGE, DEVICE CONTROL (FX),
# CLIP/TRACK + DEV ON/OFF + bank arrows, DETAIL row, PLAY/STOP/REC, crossfader.
# ============================================================================

# Top encoders T1..T4 (row 1) + rings (row 2).
ENC_R = PAD / 2 - 2
RING_H = 8
for c in range(4):
    cx = RIGHT_X + c * COL + PAD / 2
    cy = TOP_Y + PAD / 2
    circle(cx, cy, ENC_R, color_top, f"T{c+1}", font_size=10)
    rect(RIGHT_X + c * COL, TOP_Y + PAD + 4, PAD, RING_H, color_top, "", font_size=8)

# Top encoders T5..T8 (row 3) + rings (row 4).
y_top2 = TOP_Y + PAD + RING_H + 12
for c in range(4):
    cx = RIGHT_X + c * COL + PAD / 2
    cy = y_top2 + PAD / 2
    circle(cx, cy, ENC_R, color_top, f"T{c+5}", font_size=10)
    rect(RIGHT_X + c * COL, y_top2 + PAD + 4, PAD, RING_H, color_top, "", font_size=8)

# Pan / Send A / Send B / Send C physical buttons (row 5).
y_pan = y_top2 + PAD + RING_H + 12
labels_pan = ["Pan", "Send A", "Send B", "Send C"]
for c, lbl in enumerate(labels_pan):
    rect(RIGHT_X + c * COL, y_pan, PAD, H_RECT, color_pan, lbl, font_size=9)

# SHIFT button + TAP TEMPO + NUDGE cluster + cursor pad — fits to the right
# of the top encoders. Position it as a 2-column sub-cluster at cols 15-16
# (anchored to the right of the top encoders' Y range).
CURSOR_X = RIGHT_X + 4 * COL + 25
shift_y = TOP_Y
rect(CURSOR_X, shift_y, PAD, H_RECT, color_shft, "SHIFT", font_size=10)
rect(CURSOR_X + COL, shift_y, PAD, H_RECT, color_xprt, "Tap", font_size=10)

# Cursor pad cluster: ▲ at (col15, row3), ◀ at (col15, row4), ▼ at (col15, row5),
# ▶ at (col16, row3), Nudge- at (col16, row4), Nudge+ at (col16, row5).
cur_y = shift_y + H_RECT + GAP
small = PAD - 14    # 36px square cursor pads
rect(CURSOR_X + 7, cur_y,                small, H_RECT, color_dim, "▲", font_size=12)
rect(CURSOR_X + 7, cur_y + H_RECT + GAP, small, H_RECT, color_dim, "◀", font_size=12)
rect(CURSOR_X + 7, cur_y + 2 * (H_RECT + GAP), small, H_RECT, color_dim, "▼", font_size=12)
rect(CURSOR_X + COL + 7, cur_y, small, H_RECT, color_dim, "▶", font_size=12)
rect(CURSOR_X + COL, cur_y + H_RECT + GAP, PAD, H_RECT, color_xprt, "Nudge -", font_size=9)
rect(CURSOR_X + COL, cur_y + 2 * (H_RECT + GAP), PAD, H_RECT, color_xprt, "Nudge +", font_size=9)

# Device encoders D1..D4 (row 7) + rings (row 8).
y_dev = y_pan + H_RECT + GAP + 8
for c in range(4):
    cx = RIGHT_X + c * COL + PAD / 2
    cy = y_dev + PAD / 2
    circle(cx, cy, ENC_R, color_dev, f"D{c+1}", font_size=10)
    rect(RIGHT_X + c * COL, y_dev + PAD + 4, PAD, RING_H, color_dev, "", font_size=8)

# Device encoders D5..D8 (row 9) + rings (row 10).
y_dev2 = y_dev + PAD + RING_H + 12
for c in range(4):
    cx = RIGHT_X + c * COL + PAD / 2
    cy = y_dev2 + PAD / 2
    circle(cx, cy, ENC_R, color_dev, f"D{c+5}", font_size=10)
    rect(RIGHT_X + c * COL, y_dev2 + PAD + 4, PAD, RING_H, color_dev, "", font_size=8)

# CLIP/TRACK + DEV ON/OFF + bank ◀ + bank ▶ (row 11).
y_devnav = y_dev2 + PAD + RING_H + 12
labels_dnav = ["Clip/Track", "Dev On/Off", "◀ Bank", "Bank ▶"]
for c, lbl in enumerate(labels_dnav):
    rect(RIGHT_X + c * COL, y_devnav, PAD, H_RECT, color_xprt, lbl, font_size=8)

# DETAIL VIEW + REC QUANT + MIDI OVERDUB + METRONOME (row 12).
y_detail = y_devnav + H_RECT + GAP
labels_det = ["Detail View", "Rec Quant", "MIDI Ovrdub", "Metro"]
for c, lbl in enumerate(labels_det):
    rect(RIGHT_X + c * COL, y_detail, PAD, H_RECT, color_xprt, lbl, font_size=7)

# PLAY / STOP / REC (row 13).
y_xprt = y_detail + H_RECT + GAP
labels_xprt = [("Play", "#22c55e"), ("Stop", "#94a3b8"), ("Rec", "#dc2626")]
for c, (lbl, fill) in enumerate(labels_xprt):
    rect(RIGHT_X + c * COL, y_xprt, PAD, H_RECT, fill, lbl, font_size=10)

# Crossfader (row 14, spans 4 cols) — bottom-right.
y_xf = y_xprt + H_RECT + GAP + 5
rect(RIGHT_X, y_xf, 4 * COL - GAP, 28, color_dim, "Crossfader", font_size=10)

# ============================================================================
# Section labels (header chrome).
# ============================================================================
svg_out.append(
    f'  <text x="{LEFT_X + 4 * COL}" y="{TOP_Y - 8}" font-size="11" '
    f'fill="#94a3b8" text-anchor="middle">CLIP LAUNCH / SESSION OVERVIEW</text>'
)
svg_out.append(
    f'  <text x="{RIGHT_X + 2 * COL}" y="{TOP_Y - 8}" font-size="11" '
    f'fill="#94a3b8" text-anchor="middle">TRACK CONTROL</text>'
)
svg_out.append(
    f'  <text x="{RIGHT_X + 2 * COL}" y="{y_dev - 8}" font-size="11" '
    f'fill="#94a3b8" text-anchor="middle">DEVICE CONTROL (FX)</text>'
)
svg_out.append(
    f'  <text x="{LEFT_X + 4 * COL}" y="{y_solo - 8}" font-size="11" '
    f'fill="#94a3b8" text-anchor="middle">PADS  (Solo / Mute / Activator-Arm)</text>'
)

svg_out.append("</svg>")

# Write next to this script (cwd-independent).
script_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(script_dir, "apc40-layout.svg")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(svg_out))

print(f"wrote {out_path} ({len(svg_out)} lines)")
