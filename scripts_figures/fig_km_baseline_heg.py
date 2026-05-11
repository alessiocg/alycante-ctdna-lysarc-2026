#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""KM EFS par hEG baseline (Leuca, J-5, J0) — seuils = médianes, R/R strict"""
import sys, io, os, shutil
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
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0

surv = pd.read_excel(os.path.join(DATA_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')

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

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])
piv = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')

# Compute medians (positifs only) rounded to 0.5
for tp in ['Leuca', 'J-5', 'J0']:
    vals_pos = piv[tp].dropna()
    vals_pos = vals_pos[vals_pos > 0]
    med = vals_pos.median()
    med_round = round(med * 2) / 2
    print(f'{tp}: mediane={med:.2f}, arrondi 0.5={med_round:.1f}, n_pos={len(vals_pos)}')

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 7), sharey=True)
fig.suptitle('EFS par hEG baseline (R/R strict, seuil = m\u00e9diane)', fontsize=13, fontweight='bold', y=0.98)

configs = [
    (ax1, 'Leuca', 3.5),
    (ax2, 'J-5', 3.5),
    (ax3, 'J0', 3.0),
]

for ax, tp, seuil in configs:
    vals = piv[tp].dropna()
    vals = vals[vals > 0]  # only positive hEG
    merged = pd.DataFrame({'randomisation': vals.index, 'heg': vals.values})
    merged = merged.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
    merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)
    merged['rr_24'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 24)).astype(int)

    g_lo = merged[merged['heg'] <= seuil]
    g_hi = merged[merged['heg'] > seuil]

    kmf_lo = KaplanMeierFitter()
    kmf_lo.fit(g_lo['efs_time'], g_lo['efs_event'],
               label=f'hEG \u2264 {seuil:.1f} (n={len(g_lo)})')
    kmf_lo.plot_survival_function(ax=ax, color='#1565C0', ci_show=True, ci_alpha=0.12)

    kmf_hi = KaplanMeierFitter()
    kmf_hi.fit(g_hi['efs_time'], g_hi['efs_event'],
               label=f'hEG > {seuil:.1f} (n={len(g_hi)})')
    kmf_hi.plot_survival_function(ax=ax, color='#C62828', ci_show=True, ci_alpha=0.12)

    lr = logrank_test(g_lo['efs_time'], g_hi['efs_time'],
                      event_observed_A=g_lo['efs_event'], event_observed_B=g_hi['efs_event'])

    try:
        merged['grp'] = (merged['heg'] > seuil).astype(int)
        cph = CoxPHFitter()
        cph.fit(merged[['efs_time', 'efs_event', 'grp']], 'efs_time', 'efs_event')
        hr = np.exp(cph.params_['grp'])
        ci_lo_v = np.exp(cph.confidence_intervals_.iloc[0, 0])
        ci_hi_v = np.exp(cph.confidence_intervals_.iloc[0, 1])
    except:
        hr, ci_lo_v, ci_hi_v = np.nan, np.nan, np.nan

    # Se/Sp/PPV/NPV — adequate follow-up
    stats_lines = []
    for rr_col, threshold, rr_label in [('rr_12', 12, 'R/R 12m'), ('rr_24', 24, 'R/R 24m')]:
        adeq = (merged['efs_time'] >= threshold) | (merged['efs_event'] == 1)
        m_a = merged[adeq]
        g_m_a = m_a[m_a['grp'] == 1]
        g_b_a = m_a[m_a['grp'] == 0]
        tp_v = int(g_m_a[rr_col].sum())
        fp_v = len(g_m_a) - tp_v
        fn_v = int(g_b_a[rr_col].sum())
        tn_v = len(g_b_a) - fn_v
        n_a = tp_v + fp_v + fn_v + tn_v
        se = tp_v / (tp_v + fn_v) if (tp_v + fn_v) > 0 else 0
        sp = tn_v / (tn_v + fp_v) if (tn_v + fp_v) > 0 else 0
        ppv = tp_v / (tp_v + fp_v) if (tp_v + fp_v) > 0 else 0
        npv = tn_v / (tn_v + fn_v) if (tn_v + fn_v) > 0 else 0
        stats_lines.append(f'{rr_label}(n={n_a}): Se={se:.0%} Sp={sp:.0%} PPV={ppv:.0%} NPV={npv:.0%}')

    ax.set_title(f'hEG {tp}, seuil = {seuil:.1f} (m\u00e9diane)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Temps depuis J0 (mois)', fontsize=10)
    ax.set_xlim(0, 42)
    ax.legend(loc='upper right', fontsize=8.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    stats_text = (f'Log-rank p={lr.p_value:.4f}\n'
                  f'Cox: HR={hr:.1f} [{ci_lo_v:.1f}\u2013{ci_hi_v:.1f}]\n'
                  f'{stats_lines[0]}\n{stats_lines[1]}')
    ax.text(0.03, 0.03, stats_text, transform=ax.transAxes,
            fontsize=7, va='bottom', ha='left', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5F5F5',
                      edgecolor='#CCCCCC', alpha=0.95))

    print(f'{tp} seuil={seuil}: p={lr.p_value:.4f}, HR={hr:.2f} [{ci_lo_v:.1f}-{ci_hi_v:.1f}]')

ax1.set_ylabel('Probabilit\u00e9 EFS', fontsize=11)
plt.tight_layout(rect=[0, 0, 1, 0.94])
outfile = os.path.join(SCRIPT_DIR, 'fig_km_baseline_heg.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_km_baseline_heg.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
