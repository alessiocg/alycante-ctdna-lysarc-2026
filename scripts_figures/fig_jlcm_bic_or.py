#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""JLCM: BIC + OR par nombre de classes"""
import sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# Load results — garder seulement ng=1,2,3
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

res = pd.read_csv('data/jlcm_ng_comparison.csv')
res = res[res['ng'] <= 3].reset_index(drop=True)
print(res)

# Replace Inf with a display cap
OR_CAP = 200  # for display

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
fig.suptitle('Sélection du nombre de classes JLCM', fontsize=13, fontweight='bold', y=0.98)

# === Panel 1: BIC ===
ax1.plot(res['ng'], res['bic'], 'o-', color='#1565C0', linewidth=2, markersize=8)

# Annoter ng=2 comme modele choisi (meilleur BIC parmi ng=1,2,3)
chosen_ng  = 2
chosen_bic = res.loc[res['ng'] == chosen_ng, 'bic'].values[0]
ax1.plot(chosen_ng, chosen_bic, 'o', color='#C62828', markersize=14, zorder=5)
ax1.annotate(f'Modèle choisi : ng=2\nBIC={chosen_bic:.1f}',
             (chosen_ng, chosen_bic), textcoords='offset points', xytext=(15, -25),
             fontsize=9, color='#C62828', fontweight='bold')

for _, r in res.iterrows():
    if r['ng'] != chosen_ng:
        ax1.annotate(f'{r["bic"]:.1f}', (r['ng'], r['bic']),
                     textcoords='offset points', xytext=(8, 5), fontsize=8, color='grey')

ax1.set_xlabel('Nombre de classes', fontsize=11)
ax1.set_ylabel('BIC', fontsize=11)
ax1.set_title('Sélection par BIC', fontsize=11, fontweight='bold')
ax1.set_xticks([1, 2, 3])
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# === Panel 2: OR barplot ===
ng_vals = [2, 3]
x = np.arange(len(ng_vals))
width = 0.25

colors = {'R/R ≤12m': '#C62828', 'R/R ≤24m': '#FF8F00', 'R/R 12–24m': '#1565C0'}

for i, (label, col, color) in enumerate([
    ('R/R ≤12m', 'or_12', '#C62828'),
    ('R/R ≤24m', 'or_24', '#FF8F00'),
    ('R/R 12–24m', 'or_12_24', '#1565C0'),
]):
    vals = []
    for ng in ng_vals:
        row = res[res['ng'] == ng]
        v = row[col].values[0]
        if np.isinf(v) or v > OR_CAP:
            vals.append(OR_CAP)
        else:
            vals.append(v)

    bars = ax2.bar(x + i * width, vals, width, color=color, alpha=0.8, label=label)

    # Annotate
    for j, (ng, v) in enumerate(zip(ng_vals, vals)):
        row = res[res['ng'] == ng]
        raw = row[col].values[0]
        if np.isinf(raw) or raw > OR_CAP:
            txt = '∞'
        elif raw < 1:
            txt = f'{raw:.1f}'
        else:
            txt = f'{raw:.0f}'
        ax2.text(x[j] + i * width, v + 3, txt, ha='center', va='bottom',
                fontsize=8, fontweight='bold', color=color)

ax2.set_xticks(x + width)
ax2.set_xticklabels([f'{ng} classes' for ng in ng_vals], fontsize=10)
ax2.set_ylabel('Odds Ratio', fontsize=11)
ax2.set_title('OR par endpoint et nombre de classes', fontsize=11, fontweight='bold')
ax2.set_ylim(0, OR_CAP + 30)
ax2.axhline(y=1, color='grey', linewidth=0.5, linestyle='--')
ax2.legend(fontsize=8.5, loc='upper right')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Note about Inf
ax2.text(0.02, 0.95, '∞ = séparation parfaite', transform=ax2.transAxes,
         fontsize=7.5, color='grey', style='italic', va='top')

plt.tight_layout(rect=[0, 0, 1, 0.94])
outfile = 'fig_jlcm_bic_or.png'
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

subprocess.run(['cp', outfile,
                '//hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/'
                'SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/'
                'protocole ALYCANTE/Réunion LYSARC 2026/output/'], capture_output=True)
print('Done.')
