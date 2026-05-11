#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Taux cumulé de CMR par timepoint — 3 groupes: Pas de R/R 24m, R/R 12-24m, R/R ≤12m"""
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

groups = [
    ('Pas de R/R 24m', 'no_rr', '#1565C0'),
    ('R/R 12\u201324m', 'rr_12_24', '#FF8F00'),
    ('R/R \u226412m', 'rr_12', '#C62828'),
]

# Compute cumulative CMR for each group
# For each patient: has_ever_been_neg up to each timepoint
all_tps_ordered = ['Leuca', 'J-5', 'J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']

cumul_data = {}  # {pat: {tp: bool}}
for pat in valid['randomisation'].values:
    pat_data = df[df['randomisation'] == pat]
    ever_neg = False
    cumul_data[pat] = {}
    for tp in all_tps_ordered:
        tp_row = pat_data[pat_data['visite_std'] == tp]
        if len(tp_row) > 0 and tp_row['MRD_quali'].values[0] == 'NEGATIF':
            ever_neg = True
        cumul_data[pat][tp] = ever_neg

fig, ax = plt.subplots(figsize=(14, 6))
fig.suptitle('Taux cumulé de CMR (au moins 1 NÉGATIF) par timepoint et groupe pronostique',
             fontsize=13, fontweight='bold', y=0.98)

n_grp = len(groups)
n_tp = len(timepoints)
width = 0.25
x = np.arange(n_tp)

for g_idx, (g_label, g_col, g_color) in enumerate(groups):
    pats = valid[valid[g_col] == 1]['randomisation'].values
    n_total = len(pats)

    rates = []
    labels = []
    for tp in timepoints:
        n_ever_neg = sum(1 for p in pats if p in cumul_data and cumul_data[p].get(tp, False))
        rate = n_ever_neg / n_total * 100 if n_total > 0 else 0
        rates.append(rate)
        labels.append(f'{n_ever_neg}/{n_total}')

    bars = ax.bar(x + g_idx * width, rates, width, color=g_color, alpha=0.8, label=g_label)

    for i, (rate, label) in enumerate(zip(rates, labels)):
        ax.text(x[i] + g_idx * width, rate + 2, label, ha='center', va='bottom',
                fontsize=7, color=g_color, fontweight='bold')

ax.set_xticks(x + width)
ax.set_xticklabels(timepoints, fontsize=11)
ax.set_xlabel('Timepoint', fontsize=11)
ax.set_ylabel('% patients avec au moins 1 CMR', fontsize=11)
ax.set_ylim(0, 115)
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.2, linestyle='--')

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_cmr_cumule_3grp.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')
print('Done.')
