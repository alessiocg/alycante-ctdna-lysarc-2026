#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Taux de CMR (ctDNA NEGATIF) par timepoint — 4 courbes: Pas de R/R, R/R 12-24m, R/R ≤12m, R/R ≤24m"""
import sys, io, os
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

timepoints = ['J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']
tp_x = range(len(timepoints))

groups = [
    ('Pas de R/R 24m', 'no_rr', '#1565C0', 'o'),
    ('R/R 12–24m', 'rr_12_24', '#FF8F00', 's'),
    ('R/R ≤ 12m', 'rr_12', '#C62828', '^'),
]

fig, ax = plt.subplots(figsize=(14, 6))
fig.suptitle('Taux de CMR (ctDNA NÉGATIF) par timepoint et groupe pronostique',
             fontsize=13, fontweight='bold', y=0.98)

for g_label, g_col, g_color, g_marker in groups:
    pats = valid[valid[g_col] == 1]['randomisation'].values
    rates = []
    labels = []

    for tp in timepoints:
        tp_data = df[(df['visite_std'] == tp) & (df['randomisation'].isin(pats))]
        n_total = len(tp_data)
        n_neg = (tp_data['MRD_quali'] == 'NEGATIF').sum()
        if n_total > 0:
            rate = n_neg / n_total * 100
            rates.append(rate)
            labels.append(f'{n_neg}/{n_total}')
        else:
            rates.append(np.nan)
            labels.append('')

    ax.plot(tp_x, rates, color=g_color, marker=g_marker, markersize=7,
            linewidth=2, label=g_label, zorder=3)

    # Annotations
    for i, (rate, label) in enumerate(zip(rates, labels)):
        if not np.isnan(rate) and label:
            y_offset = 4 if rate < 90 else -6
            ax.annotate(label, (i, rate), textcoords='offset points',
                       xytext=(0, y_offset), ha='center', fontsize=7.5,
                       color=g_color, fontweight='bold')

ax.set_xticks(tp_x)
ax.set_xticklabels(timepoints, fontsize=11)
ax.set_ylabel('% NÉGATIF (CMR)', fontsize=11)
ax.set_ylim(-5, 105)
ax.set_xlim(-0.3, len(timepoints) - 0.7)
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_taux_cmr_3grp.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')
print('Done.')
