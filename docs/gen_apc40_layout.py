#!/usr/bin/env python3
"""Generate docs/apc40-layout.svg — static APC40 layout poster (default state: Pan + Clip Launch, no overlays). Run from any cwd: python3 docs/gen_apc40_layout.py — output is written next to this script regardless of cwd."""

import os

svg_out = []
svg_out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" width="1200" height="900" style="background-color:#0f172a; border-radius:12px; font-family:sans-serif;">')

# Colors
color_grid = "#cbd5e1"      # clip-grid pads (default Pan + Clip Launch)
color_top  = "#3b82f6"      # encoder mode strip
color_bot  = "#64748b"      # bottom regions (sliders, transport)
color_rsb  = "#10b981"      # scene launch column
color_lsb  = "#06b6d4"      # solo column
color_mute = "#f59e0b"      # mute column
color_stop = "#94a3b8"      # track stop row
color_text = "#ffffff"
color_dim  = "#64748b"      # inactive / unmapped

# Layout constants
grid_start_x = 280
grid_start_y = 220
spacing = 65
pad_size = 50

def draw_rect(x, y, w, h, fill, text, font_size=12, text_color=color_text):
    svg_out.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="#0f172a" stroke-width="2"/>')
    if text:
        cx = x + w / 2
        cy = y + h / 2 + font_size / 3
        svg_out.append(f'  <text x="{cx}" y="{cy}" font-size="{font_size}" fill="{text_color}" text-anchor="middle" font-weight="bold">{text}</text>')

# Device outline
svg_out.append('  <rect x="60" y="60" width="1080" height="780" rx="30" fill="#1e293b" stroke="#334155" stroke-width="4"/>')

# Title + subtitle
svg_out.append('  <text x="600" y="100" font-size="28" fill="#ffffff" text-anchor="middle" font-weight="bold">APC40 Layout (Default — Pan + Clip Launch)</text>')
svg_out.append('  <text x="600" y="130" font-size="14" fill="#cbd5e1" text-anchor="middle">v1.2 — see manual.html for interactive mode reference</text>')

# Top encoder row (8 encoders + small ring-LED indicators)
for c in range(8):
    x = grid_start_x + c * spacing
    y = 160
    # Encoder cap
    svg_out.append(f'  <circle cx="{x + pad_size/2}" cy="{y + pad_size/2}" r="{pad_size/2 - 2}" fill="{color_top}" stroke="#0f172a" stroke-width="2"/>')
    svg_out.append(f'  <text x="{x + pad_size/2}" y="{y + pad_size/2 + 4}" font-size="11" fill="{color_text}" text-anchor="middle" font-weight="bold">T{c+1}</text>')
    # Ring LED indicator
    draw_rect(x, y + pad_size + 4, pad_size, 8, color_top, '', font_size=8)

# Solo row (above the grid)
for c in range(8):
    x = grid_start_x + c * spacing
    y = grid_start_y - spacing - 30
    draw_rect(x, y, pad_size, pad_size * 0.4, color_lsb, f"Solo {c+1}", font_size=9)

# Mute row (just below Solo)
for c in range(8):
    x = grid_start_x + c * spacing
    y = grid_start_y - spacing + 5
    draw_rect(x, y, pad_size, pad_size * 0.4, color_mute, f"Mute {c+1}", font_size=9)

# Stop-All-Clips and Master select buttons (right of Solo/Mute strip)
draw_rect(grid_start_x + 8 * spacing + 20, grid_start_y - spacing - 30, pad_size, pad_size * 0.4, "#1e293b", "Stop All", font_size=9)
draw_rect(grid_start_x + 8 * spacing + 20, grid_start_y - spacing + 5, pad_size, pad_size * 0.4, "#1e293b", "Master", font_size=9)

# 5x8 clip grid (default Clip Launch — blue/active)
for r in range(5):
    for c in range(8):
        x = grid_start_x + c * spacing
        y = grid_start_y + r * spacing
        draw_rect(x, y, pad_size, pad_size, "#2563eb", f"T{c+1}/S{r+1}", font_size=10)

# Track Stop row (below grid)
for c in range(8):
    x = grid_start_x + c * spacing
    y = grid_start_y + 5 * spacing
    draw_rect(x, y, pad_size, pad_size * 0.5, color_stop, f"Stop {c+1}", font_size=10)

# Scene Launch column (right of grid)
for r in range(5):
    x = grid_start_x + 8 * spacing + 20
    y = grid_start_y + r * spacing
    draw_rect(x, y, pad_size, pad_size * 0.5, color_rsb, f"Scene {r+1}", font_size=10)

# Device encoder row + bank nav
for c in range(8):
    x = grid_start_x + c * spacing
    y = grid_start_y + 6 * spacing + 20
    svg_out.append(f'  <circle cx="{x + pad_size/2}" cy="{y + pad_size/2}" r="{pad_size/2 - 4}" fill="{color_top}" stroke="#0f172a" stroke-width="2"/>')
    svg_out.append(f'  <text x="{x + pad_size/2}" y="{y + pad_size/2 + 4}" font-size="11" fill="{color_text}" text-anchor="middle" font-weight="bold">D{c+1}</text>')

# Device bank nav (4 buttons)
bank_labels = ['◀ Bank', 'Bank ▶', '◀ Dev', 'Dev ▶']
for i, lbl in enumerate(bank_labels):
    x = grid_start_x + i * spacing
    y = grid_start_y + 7 * spacing + 30
    draw_rect(x, y, pad_size, pad_size * 0.4, color_top, lbl, font_size=9)

# Channel volume sliders (8) + Master + Crossfader
for c in range(8):
    x = grid_start_x + c * spacing
    y = grid_start_y + 8 * spacing + 30
    draw_rect(x, y, pad_size, pad_size * 1.4, "#475569", f"Vol {c+1}", font_size=10)

# Master slider
x_master = grid_start_x + 8 * spacing + 20
y_slider = grid_start_y + 8 * spacing + 30
draw_rect(x_master, y_slider, pad_size, pad_size * 1.4, "#475569", "Master", font_size=10)

# Crossfader (horizontal, below the channel sliders)
draw_rect(grid_start_x, y_slider + pad_size * 1.5, pad_size * 2.5, pad_size * 0.6, "#475569", "Crossfader", font_size=10)

# Transport row (Play / Stop / Rec / Tap / Nudge↑ / Nudge↓ / Detail)
transport_labels = ['Play', 'Stop', 'Rec', 'Tap', 'Nudge ↑', 'Nudge ↓', 'Detail']
for i, lbl in enumerate(transport_labels):
    x = grid_start_x + i * spacing
    y = grid_start_y + 10 * spacing + 30
    draw_rect(x, y, pad_size, pad_size * 0.6, color_bot, lbl, font_size=10)

# Encoder mode strip (Pan / SendA / SendB / SendC / User1 / User2 / User3 — Pan highlighted)
enc_modes = ['Pan', 'SendA', 'SendB', 'SendC', 'User1', 'User2', 'User3']
for i, lbl in enumerate(enc_modes):
    x = 80 + i * 70
    y = 770
    fill = color_top if lbl == 'Pan' else color_dim
    draw_rect(x, y, 60, 28, fill, lbl, font_size=10)

# Matrix mode strip (ClipLaunch / Session / Note1-6 / Step — ClipLaunch highlighted)
mat_modes = ['Clip', 'Session', 'Note1', 'Note2', 'Note3', 'Note4', 'Note5', 'Note6', 'Step']
for i, lbl in enumerate(mat_modes):
    x = 80 + i * 70
    y = 805
    fill = color_top if lbl == 'Clip' else color_dim
    draw_rect(x, y, 60, 28, fill, lbl, font_size=10)

# Shift button (bottom-left corner area)
draw_rect(80, 700, 80, 50, "#a855f7", "SHIFT", font_size=12)

# Track navigation
draw_rect(170, 700, 50, 24, color_dim, "◀ Trk", font_size=9)
draw_rect(170, 730, 50, 24, color_dim, "Trk ▶", font_size=9)

# Legend (bottom strip)
legend_items = [
    (color_grid, 'Clip Grid'),
    (color_lsb, 'Solo'),
    (color_mute, 'Mute'),
    (color_rsb, 'Scene Launch'),
    (color_top, 'Encoders / Active mode'),
]
for i, (col, lbl) in enumerate(legend_items):
    x = 80 + i * 200
    y = 850
    svg_out.append(f'  <rect x="{x}" y="{y}" width="20" height="20" rx="4" fill="{col}" stroke="#0f172a" stroke-width="1"/>')
    svg_out.append(f'  <text x="{x + 28}" y="{y + 14}" font-size="12" fill="#cbd5e1" font-weight="bold">{lbl}</text>')

svg_out.append('</svg>')

# Resolve output path relative to this script's location, not cwd.
# This lets the script run from anywhere (repo root, docs/, /tmp, etc.)
# without producing nested 'docs/docs/apc40-layout.svg' if cwd happens
# to already be docs/.
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apc40-layout.svg')
with open(OUTPUT_PATH, 'w') as f:
    f.write('\n'.join(svg_out))

print(f'Wrote {OUTPUT_PATH} ({len(svg_out)} lines)')
