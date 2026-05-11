#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""3 KM Leuca->M1 avec stats sous chaque panel"""
import sys, io, os, shutil, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

BASE_DIR = "C:/Users/4067048/AppData/Local/Temp/alycante_v2"
OUT_DIR  = os.path.join(BASE_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === DATA ===
df = pd.read_excel(os.path.join(BASE_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0

surv = pd.read_excel(os.path.join(BASE_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')
# Ajustement J0: soustraire le délai leucaphérèse→J0 par patient
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
piv = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')

# Leuca -> M1, landmark at M1 (2 months)
delta = (piv['M1'] - piv['Leuca']).dropna()
merged = pd.DataFrame({'randomisation': delta.index, 'delta': delta.values})
merged = merged.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
merged = merged[merged['efs_time'] > 1.02].copy()
merged['efs_time_lm'] = merged['efs_time'] - 1.02
merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)
merged['rr_24'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 24)).astype(int)

seuils = [(-3.0, 'Meilleur Youden / m\u00e9diane (seuil = \u22123.0)')]

fig, axes = plt.subplots(1, 1, figsize=(8, 7.5))
axes = [axes]  # make iterable
fig.suptitle('\u0394ctDNA Leuca\u2192M1 — EFS landmark (R/R strict)',
             fontsize=14, fontweight='bold', y=0.98)

for ax, (seuil, label) in zip(axes, seuils):
    merged['grp'] = (merged['delta'] > seuil).astype(int)  # 1 = MAUVAIS
    g_bon = merged[merged['grp'] == 0]
    g_mauv = merged[merged['grp'] == 1]

    # KM
    kmf_bon = KaplanMeierFitter()
    kmf_bon.fit(g_bon['efs_time_lm'], g_bon['efs_event'],
                label=f'\u0394\u2264{seuil:.1f} (n={len(g_bon)})')
    kmf_bon.plot_survival_function(ax=ax, color='#1565C0', ci_show=True, ci_alpha=0.12)

    kmf_mauv = KaplanMeierFitter()
    kmf_mauv.fit(g_mauv['efs_time_lm'], g_mauv['efs_event'],
                 label=f'\u0394>{seuil:.1f} (n={len(g_mauv)})')
    kmf_mauv.plot_survival_function(ax=ax, color='#C62828', ci_show=True, ci_alpha=0.12)

    # Log-rank
    lr = logrank_test(g_bon['efs_time_lm'], g_mauv['efs_time_lm'],
                      event_observed_A=g_bon['efs_event'],
                      event_observed_B=g_mauv['efs_event'])

    # Cox univarié
    try:
        cph = CoxPHFitter()
        cph.fit(merged[['efs_time_lm', 'efs_event', 'grp']], 'efs_time_lm', 'efs_event')
        hr = np.exp(cph.params_['grp'])
        ci_lo = np.exp(cph.confidence_intervals_.iloc[0, 0])
        ci_hi = np.exp(cph.confidence_intervals_.iloc[0, 1])
        cox_p = cph.summary['p']['grp']
    except:
        hr, ci_lo, ci_hi, cox_p = np.nan, np.nan, np.nan, np.nan

    # Se/Sp/PPV/NPV for R/R 12m and R/R 24m — adequate follow-up only
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
        sens = tp_v / (tp_v + fn_v) if (tp_v + fn_v) > 0 else 0
        spec = tn_v / (tn_v + fp_v) if (tn_v + fp_v) > 0 else 0
        ppv = tp_v / (tp_v + fp_v) if (tp_v + fp_v) > 0 else 0
        npv = tn_v / (tn_v + fn_v) if (tn_v + fn_v) > 0 else 0
        stats_lines.append(f'{rr_label}(n={n_a}): Se={sens:.0%} Sp={spec:.0%} PPV={ppv:.0%} NPV={npv:.0%}')

    ax.set_title(label, fontsize=10, fontweight='bold')
    ax.set_xlabel('Temps depuis M1 (mois)', fontsize=10)
    ax.set_xlim(0, 40)
    ax.legend(loc='upper right', fontsize=8.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Stats box under KM
    cox_str = f'Cox: HR={hr:.1f} [{ci_lo:.1f}\u2013{ci_hi:.1f}], p={cox_p:.4f}'
    lr_str = f'Log-rank p={lr.p_value:.4f}'
    stats_text = f'{lr_str}\n{cox_str}\n{stats_lines[0]}\n{stats_lines[1]}'

    ax.text(0.03, 0.03, stats_text, transform=ax.transAxes,
            fontsize=7.5, va='bottom', ha='left', family='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5F5F5',
                      edgecolor='#CCCCCC', alpha=0.95))

axes[0].set_ylabel('Probabilité EFS', fontsize=11)

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(OUT_DIR, 'fig_km_delta_leuca_m1.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

# Copy to network
subprocess.run(['cp', outfile,
                '//hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/'
                'SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/'
                'protocole ALYCANTE/Réunion LYSARC 2026/output/'],
               capture_output=True)
print('Copied to network. Done.')
