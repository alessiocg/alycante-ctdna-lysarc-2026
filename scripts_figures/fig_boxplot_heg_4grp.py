#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Boxplot ctDNA (hEG) par timepoint — 4 groupes: Total, R/R 12m, R/R 12-24m, Pas de R/R 24m"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === DATA ===
df = pd.read_excel(os.path.join(DATA_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0

surv = pd.read_excel(os.path.join(DATA_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')
is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')
valid['rr_12'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 12)).astype(int)
valid['rr_24'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 24)).astype(int)
valid['rr_12_24'] = ((valid['rr_24'] == 1) & (valid['rr_12'] == 0)).astype(int)
valid['no_rr'] = (valid['rr_24'] == 0).astype(int)

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])

timepoints = ['Leuca', 'J-5', 'J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']

# Colors
C_TOTAL = '#BDBDBD'     # grey
C_NO_RR = '#64B5F6'     # light blue
C_RR12_24 = '#FFB74D'   # orange
C_RR12 = '#E57373'      # red

groups = [
    ('Total', None, C_TOTAL),
    ('Pas de R/R 24m', 'no_rr', C_NO_RR),
    ('R/R 12–24m', 'rr_12_24', C_RR12_24),
    ('R/R ≤ 12m', 'rr_12', C_RR12),
]

fig, ax = plt.subplots(figsize=(18, 7))
fig.suptitle('Distribution ctDNA (hEG) par timepoint et groupe pronostique',
             fontsize=14, fontweight='bold', y=0.98)

n_tp = len(timepoints)
n_grp = len(groups)
width = 0.18
gap = 0.08

for tp_idx, tp in enumerate(timepoints):
    tp_data = df[df['visite_std'] == tp][['randomisation', 'MRD_quanti_heg']].dropna()
    tp_data = tp_data.merge(valid[['randomisation', 'rr_12', 'rr_24', 'rr_12_24', 'no_rr']], on='randomisation')

    for g_idx, (g_label, g_col, g_color) in enumerate(groups):
        if g_col is None:
            vals = tp_data['MRD_quanti_heg'].values
        else:
            vals = tp_data[tp_data[g_col] == 1]['MRD_quanti_heg'].values

        x_pos = tp_idx * (n_grp * width + gap) + g_idx * width

        if len(vals) >= 2:
            bp = ax.boxplot([vals], positions=[x_pos], widths=width * 0.85,
                           patch_artist=True, showfliers=False,
                           medianprops=dict(color='black', linewidth=1.5),
                           whiskerprops=dict(color=g_color, linewidth=0.8),
                           capprops=dict(color=g_color, linewidth=0.8))
            bp['boxes'][0].set_facecolor(g_color)
            bp['boxes'][0].set_alpha(0.5)
            bp['boxes'][0].set_edgecolor(g_color)

            # Jittered points
            jitter = np.random.uniform(-width * 0.3, width * 0.3, len(vals))
            ax.scatter(x_pos + jitter, vals, color=g_color, s=12, alpha=0.6, zorder=3, edgecolors='none')

        # N underneath
        ax.text(x_pos, -0.6, f'{len(vals)}', ha='center', va='top', fontsize=7, color=g_color, fontweight='bold')

# X axis
x_centers = [tp_idx * (n_grp * width + gap) + (n_grp - 1) * width / 2 for tp_idx in range(n_tp)]
ax.set_xticks(x_centers)
ax.set_xticklabels(timepoints, fontsize=11)
ax.set_ylabel('hEG (ctDNA, log$_{10}$)', fontsize=11)
ax.set_ylim(-0.8, 6.5)
ax.axhline(y=0, color='grey', linewidth=0.5, linestyle=':', zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Legend
legend_elements = [Patch(facecolor=c, alpha=0.5, edgecolor=c, label=l) for l, _, c in groups]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)

plt.tight_layout(rect=[0, 0.02, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_boxplot_heg_4grp.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')
print('Done.')
