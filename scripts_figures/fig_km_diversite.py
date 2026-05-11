#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""KM EFS par diversité variante (nbre_doublets_fv) à la leucaphérèse"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

df = pd.read_excel(os.path.join(DATA_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['visite_std'] = df['visite'].map({'Leucaph\xe9r\xe8se': 'Leuca'}).fillna(df['visite'])

surv = pd.read_excel(os.path.join(DATA_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')
is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')

leuca = df[df['visite_std'] == 'Leuca'][['randomisation', 'nbre_doublets_fv']].dropna()
merged = leuca.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)
merged['rr_24'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 24)).astype(int)

SEUIL = 55

# === Panel gauche: max(Leuca, J-5, J0) par patient ===
df['visite_std2'] = df['visite'].map({'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0'}).fillna(df['visite'])
baseline_tps = df[df['visite_std2'].isin(['Leuca', 'J-5', 'J0'])][['randomisation', 'visite_std2', 'nbre_doublets_fv']].dropna()
# Pour chaque patient, prendre le max
max_div = baseline_tps.groupby('randomisation')['nbre_doublets_fv'].max().reset_index()
max_div.columns = ['randomisation', 'max_doublets']
merged_max = max_div.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
merged_max['rr_12'] = ((merged_max['efs_event'] == 1) & (merged_max['efs_time'] <= 12)).astype(int)
merged_max['rr_24'] = ((merged_max['efs_event'] == 1) & (merged_max['efs_time'] <= 24)).astype(int)

print(f'Panel gauche (max baseline): n={len(merged_max)}, median={merged_max["max_doublets"].median():.0f}')

# === Panel droite: Leuca seul ===
# (merged already computed above)

fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
fig.suptitle(f'EFS par diversité variante (seuil = {SEUIL} doublets PV, R/R strict)',
             fontsize=13, fontweight='bold', y=0.98)

panels = [
    (ax_left, merged_max, 'max_doublets', 'Max(Leuca, J-5, J0)'),
    (ax_right, merged, 'nbre_doublets_fv', 'Leucaphérèse seule'),
]

for ax, data, col, title in panels:
    g_lo = data[data[col] <= SEUIL]
    g_hi = data[data[col] > SEUIL]

    kmf_lo = KaplanMeierFitter()
    kmf_lo.fit(g_lo['efs_time'], g_lo['efs_event'],
               label=f'≤ {SEUIL} (n={len(g_lo)})')
    kmf_lo.plot_survival_function(ax=ax, color='#1565C0', ci_show=True, ci_alpha=0.12)

    kmf_hi = KaplanMeierFitter()
    kmf_hi.fit(g_hi['efs_time'], g_hi['efs_event'],
               label=f'> {SEUIL} (n={len(g_hi)})')
    kmf_hi.plot_survival_function(ax=ax, color='#C62828', ci_show=True, ci_alpha=0.12)

    lr = logrank_test(g_lo['efs_time'], g_hi['efs_time'],
                      event_observed_A=g_lo['efs_event'], event_observed_B=g_hi['efs_event'])

    data_tmp = data.copy()
    data_tmp['grp'] = (data_tmp[col] > SEUIL).astype(int)
    cph = CoxPHFitter()
    cph.fit(data_tmp[['efs_time', 'efs_event', 'grp']], 'efs_time', 'efs_event')
    hr = np.exp(cph.params_['grp'])
    ci_lo_v = np.exp(cph.confidence_intervals_.iloc[0, 0])
    ci_hi_v = np.exp(cph.confidence_intervals_.iloc[0, 1])

    stats_lines = []
    for rr_col, rr_label in [('rr_12', 'R/R 12m'), ('rr_24', 'R/R 24m')]:
        tp_v = int(g_hi[rr_col].sum())
        fp_v = len(g_hi) - tp_v
        fn_v = int(g_lo[rr_col].sum())
        tn_v = len(g_lo) - fn_v
        se = tp_v / (tp_v + fn_v) if (tp_v + fn_v) > 0 else 0
        sp = tn_v / (tn_v + fp_v) if (tn_v + fp_v) > 0 else 0
        ppv = tp_v / (tp_v + fp_v) if (tp_v + fp_v) > 0 else 0
        npv = tn_v / (tn_v + fn_v) if (tn_v + fn_v) > 0 else 0
        stats_lines.append(f'{rr_label}: Se={se:.0%} Sp={sp:.0%} PPV={ppv:.0%} NPV={npv:.0%}')

    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_xlabel('Temps (mois)', fontsize=10)
    ax.set_xlim(0, 42)
    ax.legend(loc='upper right', fontsize=8.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    stats_text = (f'Log-rank p={lr.p_value:.4f}\n'
                  f'Cox: HR={hr:.2f} [{ci_lo_v:.1f}\u2013{ci_hi_v:.1f}]\n'
                  f'{stats_lines[0]}\n{stats_lines[1]}')
    ax.text(0.03, 0.03, stats_text, transform=ax.transAxes,
            fontsize=7.5, va='bottom', ha='left', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5F5F5',
                      edgecolor='#CCCCCC', alpha=0.95))

    print(f'{title}: p={lr.p_value:.4f}, HR={hr:.2f} [{ci_lo_v:.1f}-{ci_hi_v:.1f}]')

ax_left.set_ylabel('Probabilité EFS', fontsize=11)
plt.tight_layout(rect=[0, 0, 1, 0.94])
outfile = os.path.join(SCRIPT_DIR, 'fig_km_diversite.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')
print(f'p={lr.p_value:.4f}, HR={hr:.2f} [{ci_lo_v:.1f}-{ci_hi_v:.1f}]')
print('Done.')
