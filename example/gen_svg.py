import json

svg_out = []
svg_out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="1000" height="1000" style="background-color:#0f172a; border-radius:12px; font-family:sans-serif;">')

# Device outline
svg_out.append('  <rect x="50" y="50" width="900" height="900" rx="30" fill="#1e293b" stroke="#334155" stroke-width="4"/>')

# Colors
color_grid = "#cbd5e1"
color_top = "#3b82f6"
color_bot = "#64748b"
color_rsb = "#f59e0b"
color_lsb = "#10b981"
color_text = "#ffffff"

grid_start_x = 180
grid_start_y = 180
spacing = 70
pad_size = 55

def draw_rect(x, y, w, h, fill, text, font_size=12, text_color=color_text):
    svg_out.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="#0f172a" stroke-width="2"/>')
    if text:
        cx = x + w/2
        cy = y + h/2 + font_size/3
        svg_out.append(f'  <text x="{cx}" y="{cy}" font-size="{font_size}" fill="{text_color}" text-anchor="middle" font-weight="bold">{text}</text>')

# Draw 8x8 Grid
for row in range(8):
    for col in range(8):
        x = grid_start_x + col * spacing
        y = grid_start_y + row * spacing
        # Draw the pad
        draw_rect(x, y, pad_size, pad_size, color_grid, f"R{row} C{col}", font_size=9, text_color="#0f172a")

# Draw Top Row (Mode Buttons)
for col in range(8):
    x = grid_start_x + col * spacing
    y = grid_start_y - spacing - 20
    modes = ["Rec", "Patt", "Stut", "Mac1", "Mac2", "Mac3", "Mac4", "Mash"]
    draw_rect(x, y, pad_size, pad_size*0.6, color_top, modes[col], font_size=10)

# Draw Top Aux Row (Below the Grid)
for col in range(8):
    x = grid_start_x + col * spacing
    y = grid_start_y + 8 * spacing + 10
    draw_rect(x, y, pad_size, pad_size*0.6, color_bot, f"T.Aux{col}", font_size=10)

# Draw Bottom Aux Row (Below T.Aux)
for col in range(8):
    x = grid_start_x + col * spacing
    y = grid_start_y + 9 * spacing + 5
    draw_rect(x, y, pad_size, pad_size*0.6, color_bot, f"B.Aux{col}", font_size=10)

# Draw Shift / Setup (Bottom left, next to B.Aux)
draw_rect(grid_start_x - spacing - 20, grid_start_y + 9 * spacing + 5, pad_size, pad_size*0.6, color_bot, "Shift", font_size=10)


# Draw Left Column (LSB)
for row in range(8):
    x = grid_start_x - spacing - 20
    y = grid_start_y + row * spacing
    draw_rect(x, y, pad_size, pad_size, color_lsb, f"LSB {row}", font_size=10)

# Draw Right Column (RSB)
for row in range(8):
    x = grid_start_x + 8 * spacing + 20
    y = grid_start_y + row * spacing
    draw_rect(x, y, pad_size, pad_size, color_rsb, f"RSB {row}", font_size=10)

# Add Legend
svg_out.append('  <rect x="180" y="860" width="15" height="15" rx="3" fill="#3b82f6"/>')
svg_out.append('  <text x="205" y="872" font-size="14" fill="#cbd5e1">Top Row (Mode) [CC 91-98]</text>')

svg_out.append('  <rect x="180" y="890" width="15" height="15" rx="3" fill="#10b981"/>')
svg_out.append('  <text x="205" y="902" font-size="14" fill="#cbd5e1">LSB - Strip Select [CC 10-80]</text>')

svg_out.append('  <rect x="550" y="860" width="15" height="15" rx="3" fill="#f59e0b"/>')
svg_out.append('  <text x="575" y="872" font-size="14" fill="#cbd5e1">RSB - Group Cycle / Start-Stop [CC 19-89]</text>')

svg_out.append('  <rect x="550" y="890" width="15" height="15" rx="3" fill="#cbd5e1"/>')
svg_out.append('  <text x="575" y="902" font-size="14" fill="#cbd5e1">Pad Grid (8x8) [Note 11-88]</text>')

# Title
svg_out.append('  <text x="500" y="70" font-size="28" fill="#ffffff" text-anchor="middle" font-weight="bold">Launchpad Pro MK3 Layout</text>')
svg_out.append('  <text x="500" y="95" font-size="16" fill="#cbd5e1" text-anchor="middle">Coordinates, Modifiers, and LooP-DiCtAtOr mapping</text>')

svg_out.append('</svg>')

with open('lp-pro-mk3-layout.svg', 'w') as f:
    f.write('\n'.join(svg_out))
