#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Heatmaps AUC + C-index pour biomarqueurs ponctuels (hEG et fraction) à chaque timepoint
+ KM aux meilleurs seuils"""
import sys, io, os, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
from lifelines.utils import concordance_index
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === DATA ===
df = pd.read_excel('Donnees.xlsx')
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df['MRD_quanti_frac'] = pd.to_numeric(df.get('MRD_quanti_frac', pd.Series(dtype=float)), errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_frac'] = 0.0

surv = pd.read_excel('ALYCANTE_RNASeq_21OCT2025.xlsx')
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')
is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])

# Pivot both biomarkers
piv_heg = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')
piv_frac = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_frac', aggfunc='first')

tp_landmark = {'Leuca': 0, 'J-5': 0.8, 'J0': 1, 'J14': 1.5, 'M1': 2, 'M3': 4, 'M6': 7}
timepoints = ['Leuca', 'J-5', 'J0', 'J14', 'M1', 'M3', 'M6']
biomarkers = ['hEG', 'Fraction']
piv_dict = {'hEG': piv_heg, 'Fraction': piv_frac}

# === COMPUTE AUC and C-index for each biomarker x timepoint x endpoint ===
results = []

for bio_name in biomarkers:
    piv = piv_dict[bio_name]
    for tp in timepoints:
        if tp not in piv.columns:
            continue
        lm = tp_landmark[tp]

        vals = piv[tp].dropna()
        merged = pd.DataFrame({'randomisation': vals.index, 'value': vals.values})
        merged = merged.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
        # Landmark
        merged = merged[merged['efs_time'] > lm].copy()
        merged['efs_time_lm'] = merged['efs_time'] - lm
        merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)
        merged['rr_24'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 24)).astype(int)
        merged['rr_12_24'] = ((merged['rr_24'] == 1) & (merged['rr_12'] == 0)).astype(int)

        if len(merged) < 10:
            continue

        row = {'bio': bio_name, 'tp': tp, 'n': len(merged), 'lm': lm}

        # AUC (higher value = more risk)
        for rr_col, rr_label in [('rr_12', '12m'), ('rr_24', '24m'), ('rr_12_24', '12-24m')]:
            if merged[rr_col].sum() < 2 or (merged[rr_col] == 0).sum() < 2:
                row[f'auc_{rr_label}'] = np.nan
                row[f'ci_{rr_label}'] = np.nan
                continue
            try:
                row[f'auc_{rr_label}'] = roc_auc_score(merged[rr_col], merged['value'])
            except:
                row[f'auc_{rr_label}'] = np.nan

            # C-index truncated
            if rr_label == '12-24m':
                # For 12-24m: landmark at 12m, look at events 12-24m
                m_sub = merged[merged['efs_time'] > 12].copy()
                m_sub['ev'] = m_sub['rr_12_24']
                m_sub['t'] = np.where(m_sub['efs_time'] <= 24, m_sub['efs_time'] - 12, 12)
                m_sub = m_sub[m_sub['t'] > 0]
            elif rr_label == '12m':
                m_sub = merged.copy()
                m_sub['ev'] = m_sub['rr_12']
                m_sub['t'] = np.where(m_sub['efs_time'] <= 12, m_sub['efs_time_lm'], 12 - lm)
                m_sub = m_sub[m_sub['t'] > 0]
            else:  # 24m
                m_sub = merged.copy()
                m_sub['ev'] = m_sub['rr_24']
                m_sub['t'] = np.where(m_sub['efs_time'] <= 24, m_sub['efs_time_lm'], 24 - lm)
                m_sub = m_sub[m_sub['t'] > 0]

            try:
                row[f'ci_{rr_label}'] = concordance_index(m_sub['t'], -m_sub['value'], m_sub['ev'])
            except:
                row[f'ci_{rr_label}'] = np.nan

        results.append(row)

res_df = pd.DataFrame(results)

# === PRINT TABLE ===
print(f'\n{"Bio":>8} {"TP":>5} | {"N":>3} | {"AUC 12m":>8} {"AUC 24m":>8} {"AUC 12-24":>9} | {"CI 12m":>7} {"CI 24m":>7} {"CI 12-24":>8}')
print('-' * 85)
for _, r in res_df.iterrows():
    def f(v): return f'{v:.3f}' if not np.isnan(v) else '  —  '
    print(f'{r["bio"]:>8} {r["tp"]:>5} | {r["n"]:3.0f} | {f(r.get("auc_12m", np.nan)):>8} {f(r.get("auc_24m", np.nan)):>8} {f(r.get("auc_12-24m", np.nan)):>9} | {f(r.get("ci_12m", np.nan)):>7} {f(r.get("ci_24m", np.nan)):>7} {f(r.get("ci_12-24m", np.nan)):>8}')

# === HEATMAP FUNCTION ===
def make_heatmap_bio(metric_prefix, metric_label, vmin, vmax, outfile):
    """2 biomarkers x 7 timepoints, 3 panels (12m, 24m, 12-24m)"""
    endpoints = [('12m', 'R/R \u2264 12 mois'), ('24m', 'R/R \u2264 24 mois'), ('12-24m', 'R/R 12\u201324 mois')]

    fig, axes = plt.subplots(1, 3, figsize=(18, 3.5))
    fig.suptitle(f'{metric_label} du ctDNA ponctuel par biomarqueur \u00d7 timepoint\n'
                 f'(analyse landmark, R/R strict)',
                 fontsize=12, fontweight='bold', y=1.05)

    for ax, (ep_key, ep_title) in zip(axes, endpoints):
        col = f'{metric_prefix}_{ep_key}'

        data = np.full((2, len(timepoints)), np.nan)
        ns_data = np.full((2, len(timepoints)), np.nan)

        for i, bio in enumerate(biomarkers):
            for j, tp in enumerate(timepoints):
                row = res_df[(res_df['bio'] == bio) & (res_df['tp'] == tp)]
                if len(row) > 0 and col in row.columns:
                    val = row[col].values[0]
                    data[i, j] = val
                    ns_data[i, j] = row['n'].values[0]

        im = ax.imshow(data, cmap='RdYlGn', vmin=vmin, vmax=vmax, aspect='auto')
        ax.set_xticks(range(len(timepoints)))
        ax.set_xticklabels(timepoints, rotation=45, ha='right')
        ax.set_yticks(range(2))
        ax.set_yticklabels(biomarkers)
        ax.set_title(ep_title, fontsize=10, pad=6)

        best_val = np.nanmax(data)
        for ii in range(2):
            for jj in range(len(timepoints)):
                val = data[ii, jj]
                n = ns_data[ii, jj]
                if np.isnan(val):
                    ax.text(jj, ii, '\u2014', ha='center', va='center', color='grey', fontsize=8)
                else:
                    color = 'white' if val > 0.70 else 'black'
                    fw = 'bold' if val == best_val else 'normal'
                    ax.text(jj, ii, f'{val:.3f}\n(n={int(n)})', ha='center', va='center',
                            color=color, fontsize=8, fontweight=fw)

        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label=metric_label.split()[0])

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'OK: {outfile}')


# AUC heatmaps
make_heatmap_bio('auc', 'AUC ROC', 0.50, 0.85, 'output/fig_heatmap_auc_ponctuel.png')

# C-index heatmaps
make_heatmap_bio('ci', 'C-index', 0.50, 0.80, 'output/fig_heatmap_cindex_ponctuel.png')

# Copy to network
for f in ['fig_heatmap_auc_ponctuel.png', 'fig_heatmap_cindex_ponctuel.png']:
    subprocess.run(['cp', f'output/{f}',
                    '//hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/'
                    'SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/'
                    'protocole ALYCANTE/Réunion LYSARC 2026/output/'],
                   capture_output=True)

# === BEST TIMEPOINT ANALYSIS ===
# Find best for each endpoint x biomarker
print('\n=== MEILLEURS TIMEPOINTS ===')
for ep in ['12m', '24m', '12-24m']:
    for bio in biomarkers:
        sub = res_df[res_df['bio'] == bio].copy()
        auc_col = f'auc_{ep}'
        if auc_col in sub.columns:
            best = sub.loc[sub[auc_col].idxmax()] if sub[auc_col].notna().any() else None
            if best is not None:
                print(f'  {bio} R/R {ep}: best={best["tp"]}, AUC={best[auc_col]:.3f}, n={best["n"]:.0f}')

print('\nDone.')
