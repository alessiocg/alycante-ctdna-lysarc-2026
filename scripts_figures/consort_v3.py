#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CONSORT flowchart — style publication médicale (NEJM/JCO)"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.patheffects as pe
import numpy as np

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

fig, ax = plt.subplots(1, 1, figsize=(10, 14), dpi=250)
ax.set_xlim(0, 10)
ax.set_ylim(0, 20)
ax.axis('off')
fig.patch.set_facecolor('white')

# Colors — minimal, professional
BLACK = '#000000'
DARK = '#333333'
GREY_BORDER = '#666666'
LIGHT_GREY = '#F5F5F5'
WHITE = '#FFFFFF'

def draw_box(x, y, w, h, text, fontsize=9.5, bold=False, border_width=1.0):
    """Simple rectangle, white fill, thin black border"""
    rect = Rectangle((x - w/2, y - h/2), w, h,
                      facecolor=WHITE, edgecolor=GREY_BORDER,
                      linewidth=border_width, zorder=2)
    ax.add_patch(rect)
    weight = 'bold' if bold else 'normal'
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight=weight, color=DARK, linespacing=1.35, zorder=3)

def arrow_down(x, y1, y2, lw=0.8):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='-|>', color=DARK, lw=lw,
                               mutation_scale=10))

def line_right(x1, y, x2, lw=0.8):
    ax.plot([x1, x2], [y, y], color=DARK, lw=lw, zorder=1)

def arrow_right(x1, y, x2, lw=0.8):
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='-|>', color=DARK, lw=lw,
                               mutation_scale=10))

# Layout constants — centré
LEFT_X = 4.0       # center of left column (timepoint boxes)
RIGHT_X = 7.8      # center of right column (missing boxes)
BOX_W_L = 2.8      # width left boxes
BOX_W_R = 3.2      # width right boxes
BOX_H = 0.55       # height timepoint boxes
TOP_Y = 19.3
STEP = 1.55

# ═══════════════════════════════════════════════════════════════
# TOP SECTION
# ═══════════════════════════════════════════════════════════════

# Enrollment box
draw_box(LEFT_X, TOP_Y, 3.5, 0.7,
         '62 patients randomisés\n(cohorte ALYCANTE)',
         fontsize=11, bold=True, border_width=1.5)

# Exclusion arrow + box
arrow_right(LEFT_X + 1.75, TOP_Y, RIGHT_X - BOX_W_R/2)
draw_box(RIGHT_X, TOP_Y, BOX_W_R, 0.6,
         '5 exclus\n(Non Informatif)', fontsize=9)

# Arrow down to analyzable
arrow_down(LEFT_X, TOP_Y - 0.35, TOP_Y - 1.05)

# Analyzable box
draw_box(LEFT_X, TOP_Y - 1.35, 3.5, 0.6,
         '57 patients analysables', fontsize=11, bold=True, border_width=1.5)

arrow_down(LEFT_X, TOP_Y - 1.65, TOP_Y - 2.25)

# ═══════════════════════════════════════════════════════════════
# TIMEPOINTS
# ═══════════════════════════════════════════════════════════════

timepoints = [
    ('Leucaphérèse',  56,  1,  0),
    ('D-5',           55,  2,  0),
    ('D0 (injection)', 54, 3,  0),
    ('J14',           52,  5,  0),
    ('M1',            51,  6,  0),
    ('M3',            45, 12,  8),
    ('M6',            36, 21, 16),
    ('M9',            29, 28, 22),
    ('M12',           29, 28, 26),
]

y_start = TOP_Y - 2.6

for i, (tp_name, n, n_missing, n_sortie) in enumerate(timepoints):
    y = y_start - i * STEP

    # Timepoint box
    draw_box(LEFT_X, y, BOX_W_L, BOX_H,
             f'{tp_name}\nn = {n}', fontsize=9.5, bold=True)

    # Missing details (right side)
    if n_missing > 0:
        line_right(LEFT_X + BOX_W_L/2, y, RIGHT_X - BOX_W_R/2)
        arrow_right(RIGHT_X - BOX_W_R/2 - 0.05, y, RIGHT_X - BOX_W_R/2)

        n_na = n_missing - n_sortie
        if n_sortie > 0:
            detail = f'−{n_missing} manquants\n({n_sortie} sortie d\'étude, {n_na} NA ponctuel)'
        else:
            detail = f'−{n_missing} manquants\n({n_na} NA ponctuel)'

        draw_box(RIGHT_X, y, BOX_W_R, BOX_H, detail, fontsize=8.5)

    # Arrow to next timepoint
    if i < len(timepoints) - 1:
        arrow_down(LEFT_X, y - BOX_H/2, y - STEP + BOX_H/2)

# ═══════════════════════════════════════════════════════════════
# LEGEND (bottom right, discrete)
# ═══════════════════════════════════════════════════════════════
leg_x, leg_y = RIGHT_X, y_start - (len(timepoints)) * STEP + 0.3
ax.text(leg_x, leg_y + 0.3, 'Sortie d\'étude = R/P ou décès avant le timepoint',
        fontsize=7.5, color='#666666', style='italic', ha='center')
ax.text(leg_x, leg_y, 'NA ponctuel = patient en étude, échantillon manquant',
        fontsize=7.5, color='#666666', style='italic', ha='center')

plt.tight_layout(pad=0.5)
outfile = 'output/consort_flowchart_v3.png'
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white',
            edgecolor='none')
print(f'OK: {outfile}')

import shutil, os
net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'consort_flowchart_v3.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
