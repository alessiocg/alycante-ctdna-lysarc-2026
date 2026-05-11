#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""KM EFS landmark CMR à M3 — même style que fig_km_delta_v2"""
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

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])
piv_mrd = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quali', aggfunc='first')

# CMR at M3 — landmark a M3 (tous les 45 patients evaluables)
LM = 2.99
cmr_m3 = piv_mrd['M3'].dropna()
merged = pd.DataFrame({'randomisation': cmr_m3.index, 'cmr': (cmr_m3 == 'NEGATIF').astype(int).values})
merged = merged.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
merged = merged.copy()  # Pas d'exclusion landmark — garder les 45 patients evaluables
merged['efs_time_lm'] = merged['efs_time'] - LM
merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)
merged['rr_24'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 24)).astype(int)
merged['adeq_12'] = ((merged['efs_time'] >= 12) | (merged['efs_event'] == 1))
merged['adeq_24'] = ((merged['efs_time'] >= 24) | (merged['efs_event'] == 1))

g_bon = merged[merged['cmr'] == 1]   # CMR = BON
g_mauv = merged[merged['cmr'] == 0]  # pas de CMR = MAUVAIS

print(f'CMR M3 landmark: n={len(merged)} | CMR+ (BON)={len(g_bon)} | CMR- (MAUVAIS)={len(g_mauv)}')

# === FIGURE ===
fig, ax = plt.subplots(figsize=(8, 7))
fig.suptitle('CMR ponctuelle M3 \u2014 EFS landmark (R/R strict)',
             fontsize=14, fontweight='bold', y=0.98)

# KM
kmf_bon = KaplanMeierFitter()
kmf_bon.fit(g_bon['efs_time_lm'], g_bon['efs_event'],
            label=f'CMR M3 (n={len(g_bon)})')
kmf_bon.plot_survival_function(ax=ax, color='#1565C0', ci_show=True, ci_alpha=0.12)

kmf_mauv = KaplanMeierFitter()
kmf_mauv.fit(g_mauv['efs_time_lm'], g_mauv['efs_event'],
             label=f'Pas de CMR M3 (n={len(g_mauv)})')
kmf_mauv.plot_survival_function(ax=ax, color='#C62828', ci_show=True, ci_alpha=0.12)

# Log-rank
lr = logrank_test(g_bon['efs_time_lm'], g_mauv['efs_time_lm'],
                  event_observed_A=g_bon['efs_event'],
                  event_observed_B=g_mauv['efs_event'])

# Cox univarié (cmr=0 = MAUVAIS = ref inversée → grp=1-cmr)
merged['grp'] = 1 - merged['cmr']  # 1=MAUVAIS
try:
    cph = CoxPHFitter()
    cph.fit(merged[['efs_time_lm', 'efs_event', 'grp']], 'efs_time_lm', 'efs_event')
    hr = np.exp(cph.params_['grp'])
    ci_lo = np.exp(cph.confidence_intervals_.iloc[0, 0])
    ci_hi = np.exp(cph.confidence_intervals_.iloc[0, 1])
    cox_p = cph.summary['p']['grp']
except:
    hr, ci_lo, ci_hi, cox_p = np.nan, np.nan, np.nan, np.nan

# Se/Sp/PPV/NPV — with adequate follow-up filtering
stats_lines = []
for rr_col, adeq_col, rr_label in [('rr_12', 'adeq_12', 'R/R 12m'), ('rr_24', 'adeq_24', 'R/R 24m')]:
    m_adeq = merged[merged[adeq_col]]
    g_m_a = m_adeq[m_adeq['cmr'] == 0]
    g_b_a = m_adeq[m_adeq['cmr'] == 1]
    tp_v = int(g_m_a[rr_col].sum())
    fp_v = len(g_m_a) - tp_v
    fn_v = int(g_b_a[rr_col].sum())
    tn_v = len(g_b_a) - fn_v
    n_a = tp_v + fp_v + fn_v + tn_v
    sens = tp_v / (tp_v + fn_v) if (tp_v + fn_v) > 0 else 0
    spec = tn_v / (tn_v + fp_v) if (tn_v + fp_v) > 0 else 0
    ppv = tp_v / (tp_v + fp_v) if (tp_v + fp_v) > 0 else 0
    npv = tn_v / (tn_v + fn_v) if (tn_v + fn_v) > 0 else 0
    stats_lines.append(f'{rr_label} (n={n_a}): Se={sens:.0%} Sp={spec:.0%} PPV={ppv:.0%} NPV={npv:.0%}')
    print(f'  {stats_lines[-1]}')

ax.set_xlabel('Temps depuis M3 (mois)', fontsize=11)
ax.set_ylabel('Probabilit\u00e9 EFS', fontsize=11)
ax.set_xlim(0, 40)
ax.legend(loc='upper right', fontsize=9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Stats box
cox_str = f'Cox: HR={hr:.1f} [{ci_lo:.1f}\u2013{ci_hi:.1f}], p={cox_p:.4f}'
lr_str = f'Log-rank p={lr.p_value:.4f}'
stats_text = f'{lr_str}\n{cox_str}\n{stats_lines[0]}\n{stats_lines[1]}'

ax.text(0.03, 0.03, stats_text, transform=ax.transAxes,
        fontsize=8, va='bottom', ha='left', family='monospace',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5F5F5',
                  edgecolor='#CCCCCC', alpha=0.95))

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_km_cmr_m3.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'\nOK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\R\u00e9union LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_km_cmr_m3.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
