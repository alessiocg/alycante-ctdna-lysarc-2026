#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Distribution du ctDNA par timepoint — taux de positivité MRD"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === DATA ===
df = pd.read_excel(os.path.join(DATA_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['visite_std'] = df['visite'].map({
    'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
    'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12',
    'Relapse/Progression': 'R/P'}).fillna(df['visite'])

timepoints = ['Leuca', 'J-5', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12', 'R/P']

rates = []
labels = []
ns = []
for tp in timepoints:
    tp_data = df[df['visite_std'] == tp]
    n_total = tp_data['randomisation'].nunique()
    n_pos = tp_data[tp_data['MRD_quali'] == 'POSITIF']['randomisation'].nunique()
    if n_total > 0:
        rate = n_pos / n_total * 100
    else:
        rate = 0
    rates.append(rate)
    labels.append(f'{rate:.0f}%\n(n={n_total})')
    ns.append(n_total)

# Colors: pre-CAR-T red, post-CAR-T blue/green, R/P green
colors = []
for tp in timepoints:
    if tp in ('Leuca', 'J-5'):
        colors.append('#C62828')  # pre-CAR-T
    elif tp == 'R/P':
        colors.append('#2E7D32')  # relapse
    elif tp in ('J14', 'M1'):
        colors.append('#E53935')  # early post
    elif tp in ('M3',):
        colors.append('#EF5350')
    else:
        colors.append('#1565C0')  # late post

fig, ax = plt.subplots(figsize=(12, 5.5))
fig.suptitle('Taux de positivit\u00e9 ctDNA par timepoint',
             fontsize=13, fontweight='bold', y=0.98)

x = np.arange(len(timepoints))
bars = ax.bar(x, rates, color=colors, alpha=0.85, edgecolor='white', linewidth=0.5)

# Annotate
for i, (rate, label) in enumerate(zip(rates, labels)):
    ax.text(i, rate + 1.5, label, ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(timepoints, fontsize=11)
ax.set_ylabel('% MRD positif', fontsize=11)
ax.set_ylim(0, 110)
ax.set_title('Taux de positivit\u00e9 MRD par timepoint', fontsize=11, fontweight='bold', pad=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.2, linestyle='--')

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_distribution_ctdna.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_distribution_ctdna.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
