#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CMR par timepoint — 3 panels: OR (R/R12 + R/R24), Log-rank p-value, C-index
Justifie le choix du timepoint optimal pour l'analyse ponctuelle CMR → EFS/R/R"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import fisher_exact
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

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

# Correction J0
def _parse_dt(v):
    s = str(v).strip()
    try:
        n = float(s.replace(',', '.'))
        return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(n))
    except Exception:
        for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d']:
            try: return pd.to_datetime(s, format=fmt)
            except: pass
    return pd.NaT
surv['_dl'] = surv['Start of leukapheresis'].apply(_parse_dt)
surv['_dj'] = surv['Date of Axi-cel infusion (numeric)'].apply(_parse_dt)
surv['efs_time'] = surv['efs_time'] - (surv['_dj'] - surv['_dl']).dt.days / 30.44

is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')
valid['rr_12'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 12)).astype(int)
valid['rr_24'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 24)).astype(int)

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])

timepoints = ['J14', 'M1', 'M3', 'M6', 'M9', 'M12']
tp_months = {'J14': 0.46, 'M1': 1.02, 'M3': 2.99, 'M6': 6.03, 'M9': 9.05, 'M12': 11.99}

# === COMPUTE METRICS PER TIMEPOINT ===
results = []

for tp in timepoints:
    # Get CMR status at this timepoint for each patient
    tp_data = df[df['visite_std'] == tp][['randomisation', 'MRD_quali']].drop_duplicates('randomisation')
    tp_data['cmr'] = (tp_data['MRD_quali'] == 'NEGATIF').astype(int)

    merged = tp_data.merge(valid[['randomisation', 'rr_12', 'rr_24', 'efs_event', 'efs_time']], on='randomisation')
    n = len(merged)
    if n < 10:
        continue

    n_cmr = int(merged['cmr'].sum())
    n_no_cmr = n - n_cmr

    # --- OR for R/R 12m (adequate follow-up only) ---
    adeq12 = (merged['efs_time'] >= 12) | (merged['efs_event'] == 1)
    m12 = merged[adeq12]
    a = int(((m12['cmr'] == 0) & (m12['rr_12'] == 1)).sum())
    b = int(((m12['cmr'] == 0) & (m12['rr_12'] == 0)).sum())
    c = int(((m12['cmr'] == 1) & (m12['rr_12'] == 1)).sum())
    d = int(((m12['cmr'] == 1) & (m12['rr_12'] == 0)).sum())
    table_12 = [[a, b], [c, d]]
    or_12, p_fisher_12 = fisher_exact(table_12)
    if 0 in [a, b, c, d]:
        or_12_lo, or_12_hi = np.nan, np.nan
    else:
        se_log_or = np.sqrt(1/a + 1/b + 1/c + 1/d)
        or_12_lo = np.exp(np.log(or_12) - 1.96 * se_log_or)
        or_12_hi = np.exp(np.log(or_12) + 1.96 * se_log_or)

    # --- OR for R/R 24m (adequate follow-up only) ---
    adeq24 = (merged['efs_time'] >= 24) | (merged['efs_event'] == 1)
    m24 = merged[adeq24]
    a24 = int(((m24['cmr'] == 0) & (m24['rr_24'] == 1)).sum())
    b24 = int(((m24['cmr'] == 0) & (m24['rr_24'] == 0)).sum())
    c24 = int(((m24['cmr'] == 1) & (m24['rr_24'] == 1)).sum())
    d24 = int(((m24['cmr'] == 1) & (m24['rr_24'] == 0)).sum())
    table_24 = [[a24, b24], [c24, d24]]
    or_24, p_fisher_24 = fisher_exact(table_24)
    if 0 in [a24, b24, c24, d24]:
        or_24_lo, or_24_hi = np.nan, np.nan
    else:
        se_or24 = np.sqrt(1/a24 + 1/b24 + 1/c24 + 1/d24)
        or_24_lo = np.exp(np.log(or_24) - 1.96 * se_or24)
        or_24_hi = np.exp(np.log(or_24) + 1.96 * se_or24)

    # --- Log-rank EFS: CMR vs no CMR (landmark) ---
    h_time = tp_months[tp]
    lm = merged[merged['efs_time'] > h_time].copy()
    lm['surv_time'] = lm['efs_time'] - h_time
    if len(lm) >= 10 and lm['cmr'].nunique() == 2:
        lr = logrank_test(
            lm.loc[lm['cmr'] == 1, 'surv_time'], lm.loc[lm['cmr'] == 0, 'surv_time'],
            lm.loc[lm['cmr'] == 1, 'efs_event'], lm.loc[lm['cmr'] == 0, 'efs_event'])
        lr_p = lr.p_value
    else:
        lr_p = np.nan

    # --- C-index (Cox): CMR as binary predictor for EFS (landmark) ---
    if len(lm) >= 10 and lm['cmr'].nunique() == 2 and lm['efs_event'].sum() >= 3:
        try:
            cph = CoxPHFitter()
            cph.fit(lm[['surv_time', 'efs_event', 'cmr']], duration_col='surv_time', event_col='efs_event')
            c_index = cph.concordance_index_
        except Exception:
            c_index = np.nan
    else:
        c_index = np.nan

    # --- Se/Sp/PPV/NPV ---
    # Test positif = pas de CMR (cmr==0), maladie = R/R
    def calc_metrics(cmr_col, rr_col):
        tp_ = (cmr_col == 0) & (rr_col == 1)  # no CMR + R/R
        fp_ = (cmr_col == 0) & (rr_col == 0)  # no CMR + no R/R
        fn_ = (cmr_col == 1) & (rr_col == 1)  # CMR + R/R
        tn_ = (cmr_col == 1) & (rr_col == 0)  # CMR + no R/R
        tp, fp, fn, tn = int(tp_.sum()), int(fp_.sum()), int(fn_.sum()), int(tn_.sum())
        se = tp / max(tp + fn, 1)
        sp = tn / max(tn + fp, 1)
        ppv = tp / max(tp + fp, 1)
        npv = tn / max(tn + fn, 1)
        return se, sp, ppv, npv

    # Filter for adequate follow-up before computing Se/Sp/PPV/NPV
    adeq12 = (merged['efs_time'] >= 12) | (merged['efs_event'] == 1)
    adeq24 = (merged['efs_time'] >= 24) | (merged['efs_event'] == 1)
    se12, sp12, ppv12, npv12 = calc_metrics(merged.loc[adeq12, 'cmr'], merged.loc[adeq12, 'rr_12'])
    se24, sp24, ppv24, npv24 = calc_metrics(merged.loc[adeq24, 'cmr'], merged.loc[adeq24, 'rr_24'])

    results.append({
        'tp': tp, 'n': n, 'n_cmr': n_cmr, 'n_no_cmr': n_no_cmr,
        'or_12': or_12, 'or_12_lo': or_12_lo, 'or_12_hi': or_12_hi, 'p_fisher_12': p_fisher_12,
        'or_24': or_24, 'or_24_lo': or_24_lo, 'or_24_hi': or_24_hi, 'p_fisher_24': p_fisher_24,
        'lr_p': lr_p, 'c_index': c_index,
        'n_lm': len(lm) if len(lm) >= 10 else np.nan,
        'se_12': se12, 'sp_12': sp12, 'ppv_12': ppv12, 'npv_12': npv12,
        'se_24': se24, 'sp_24': sp24, 'ppv_24': ppv24, 'npv_24': npv24,
    })

res = pd.DataFrame(results)
print(res[['tp', 'n', 'n_cmr', 'or_12', 'p_fisher_12', 'or_24', 'p_fisher_24', 'lr_p', 'c_index']].to_string())

# === FIGURE: 3 panels ===
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle('Pouvoir discriminant de la CMR ponctuelle par timepoint',
             fontsize=14, fontweight='bold', y=0.98)

x = np.arange(len(res))
tp_labels = res['tp'].values

# --- Panel 1: OR ---
OR_CAP = 80
width = 0.35

# R/R 12m
or12_vals = np.minimum(res['or_12'].values, OR_CAP)
or12_lo = np.minimum(res['or_12_lo'].values, OR_CAP)
or12_hi = np.minimum(res['or_12_hi'].values, OR_CAP)
yerr12_lo = or12_vals - or12_lo
yerr12_hi = or12_hi - or12_vals
bars1 = ax1.bar(x - width/2, or12_vals, width, color='#C62828', alpha=0.8, label='R/R ≤12m')
ax1.errorbar(x - width/2, or12_vals, yerr=[yerr12_lo, yerr12_hi],
             fmt='none', color='#C62828', capsize=3, linewidth=1.5)

# R/R 24m
or24_vals = np.minimum(res['or_24'].values, OR_CAP)
or24_lo = np.minimum(res['or_24_lo'].values, OR_CAP)
or24_hi = np.minimum(res['or_24_hi'].values, OR_CAP)
yerr24_lo = or24_vals - or24_lo
yerr24_hi = or24_hi - or24_vals
bars2 = ax1.bar(x + width/2, or24_vals, width, color='#FF8F00', alpha=0.8, label='R/R ≤24m')
ax1.errorbar(x + width/2, or24_vals, yerr=[yerr24_lo, yerr24_hi],
             fmt='none', color='#FF8F00', capsize=3, linewidth=1.5)

# Annotate OR values
for i in range(len(res)):
    v12 = res['or_12'].values[i]
    txt12 = f'{v12:.1f}' if v12 < OR_CAP else f'{v12:.0f}'
    ax1.text(x[i] - width/2, min(v12, OR_CAP) + 2, txt12, ha='center', va='bottom',
             fontsize=8, fontweight='bold', color='#C62828')
    v24 = res['or_24'].values[i]
    txt24 = f'{v24:.1f}' if v24 < OR_CAP else f'{v24:.0f}'
    ax1.text(x[i] + width/2, min(v24, OR_CAP) + 2, txt24, ha='center', va='bottom',
             fontsize=8, fontweight='bold', color='#FF8F00')

# Fisher p-values as a table below the axis
p_table = 'Fisher p:\n'
p_table += '  12m: ' + '  '.join([f'{res["p_fisher_12"].values[i]:.3f}' if res['p_fisher_12'].values[i] >= 0.001 else '<.001' for i in range(len(res))]) + '\n'
p_table += '  24m: ' + '  '.join([f'{res["p_fisher_24"].values[i]:.3f}' if res['p_fisher_24'].values[i] >= 0.001 else '<.001' for i in range(len(res))])
ax1.text(0.5, -0.18, p_table, transform=ax1.transAxes, ha='center', va='top',
         fontsize=7, family='monospace', color='#333333',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5F5F5', edgecolor='#CCCCCC', alpha=0.9))

ax1.axhline(y=1, color='grey', linewidth=0.8, linestyle='--', zorder=0)
ax1.set_xticks(x)
ax1.set_xticklabels(tp_labels, fontsize=11)
ax1.set_ylabel('Odds Ratio (pas de CMR → R/R)', fontsize=10)
ax1.set_title('OR par timepoint', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9, loc='upper right')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.set_ylim(-2, OR_CAP + 15)

# Annotate n per timepoint
for i in range(len(res)):
    ax1.text(x[i], -10, f'n={res["n"].values[i]}', ha='center', fontsize=7, color='grey')

# --- Panel 2: Log-rank p-value ---
lr_vals = res['lr_p'].values
# Plot as -log10(p) for better visualization
neg_log_p = -np.log10(lr_vals)
colors_lr = ['#C62828' if p < 0.05 else '#78909C' for p in lr_vals]
ax2.bar(x, neg_log_p, color=colors_lr, alpha=0.8, width=0.6)
ax2.axhline(y=-np.log10(0.05), color='red', linewidth=1, linestyle='--', label='p=0.05')
ax2.axhline(y=-np.log10(0.01), color='orange', linewidth=0.8, linestyle=':', label='p=0.01')

for i in range(len(res)):
    p = lr_vals[i]
    p_txt = f'{p:.4f}' if p >= 0.001 else f'{p:.1e}'
    ax2.text(x[i], neg_log_p[i] + 0.1, p_txt, ha='center', va='bottom',
             fontsize=8, fontweight='bold', color=colors_lr[i])

ax2.set_xticks(x)
ax2.set_xticklabels(tp_labels, fontsize=11)
ax2.set_ylabel('-log10(p)', fontsize=10)
ax2.set_title('Log-rank EFS (CMR vs pas de CMR, landmark)', fontsize=12, fontweight='bold')
ax2.legend(fontsize=8, loc='upper right')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# --- Panel 3: C-index ---
c_vals = res['c_index'].values
colors_c = ['#1565C0' if c > 0.6 else '#78909C' for c in c_vals]
ax3.bar(x, c_vals, color=colors_c, alpha=0.8, width=0.6)
ax3.axhline(y=0.5, color='grey', linewidth=1, linestyle='--', label='C=0.5 (aléatoire)')
ax3.axhline(y=0.6, color='blue', linewidth=0.8, linestyle=':', alpha=0.5, label='C=0.6')

for i in range(len(res)):
    ax3.text(x[i], c_vals[i] + 0.01, f'{c_vals[i]:.3f}', ha='center', va='bottom',
             fontsize=9, fontweight='bold', color=colors_c[i])

ax3.set_xticks(x)
ax3.set_xticklabels(tp_labels, fontsize=11)
ax3.set_ylabel('C-index (Harrell)', fontsize=10)
ax3.set_title('C-index EFS (CMR binaire, landmark Cox)', fontsize=12, fontweight='bold')
ax3.set_ylim(0.4, max(c_vals) + 0.08)
ax3.legend(fontsize=8, loc='upper right')
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
outfile = os.path.join(SCRIPT_DIR, 'fig_cmr_timepoint_comparison.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'\nOK: {outfile}')

# Copy to network
import shutil
net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_cmr_timepoint_comparison.png'))
    print(f'Copied to network')
except Exception as e:
    print(f'Warning: {e}')

print('Done.')
