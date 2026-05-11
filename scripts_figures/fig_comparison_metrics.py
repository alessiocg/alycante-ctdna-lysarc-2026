#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Comparaison Se/Sp/PPV/NPV pour R/R12 et R/R24 — 3 approches:
JLCM J14, CMR M3, Delta hEG Leuca-M1"""
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
    'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}).fillna(df['visite'])
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0

surv = pd.read_excel(os.path.join(DATA_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')

# Correction J0: soustraire delai leucapherese → J0
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
delay = (surv['_dj'] - surv['_dl']).dt.days / 30.44
surv['efs_time'] = surv['efs_time'] - delay  # maintenant en mois depuis J0

is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')
valid['rr_12'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 12)).astype(int)
valid['rr_24'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 24)).astype(int)
# Adequate follow-up flags: exclude censored patients before threshold
valid['adeq_12'] = ((valid['efs_time'] >= 12) | (valid['efs_event'] == 1)).astype(bool)
valid['adeq_24'] = ((valid['efs_time'] >= 24) | (valid['efs_event'] == 1)).astype(bool)

piv_heg = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')
piv_mrd = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quali', aggfunc='first')


def calc_metrics(d, group_col='group'):
    """Calculate Se/Sp/PPV/NPV for R/R 12m and 24m with proper follow-up filtering."""
    # R/R 12m: only patients with adequate follow-up
    d12 = d[d['adeq_12']].copy()
    tp12 = int(((d12[group_col] == 'MAUVAIS') & (d12['rr_12'] == 1)).sum())
    fp12 = int(((d12[group_col] == 'MAUVAIS') & (d12['rr_12'] == 0)).sum())
    fn12 = int(((d12[group_col] == 'BON') & (d12['rr_12'] == 1)).sum())
    tn12 = int(((d12[group_col] == 'BON') & (d12['rr_12'] == 0)).sum())
    n12 = tp12 + fp12 + fn12 + tn12
    se12 = tp12 / max(tp12 + fn12, 1)
    sp12 = tn12 / max(tn12 + fp12, 1)
    ppv12 = tp12 / max(tp12 + fp12, 1)
    npv12 = tn12 / max(tn12 + fn12, 1)

    # R/R 24m: only patients with adequate follow-up
    d24 = d[d['adeq_24']].copy()
    tp24 = int(((d24[group_col] == 'MAUVAIS') & (d24['rr_24'] == 1)).sum())
    fp24 = int(((d24[group_col] == 'MAUVAIS') & (d24['rr_24'] == 0)).sum())
    fn24 = int(((d24[group_col] == 'BON') & (d24['rr_24'] == 1)).sum())
    tn24 = int(((d24[group_col] == 'BON') & (d24['rr_24'] == 0)).sum())
    n24 = tp24 + fp24 + fn24 + tn24
    se24 = tp24 / max(tp24 + fn24, 1)
    sp24 = tn24 / max(tn24 + fp24, 1)
    ppv24 = tp24 / max(tp24 + fp24, 1)
    npv24 = tn24 / max(tn24 + fn24, 1)

    return (se12, sp12, ppv12, npv12, n12,
            se24, sp24, ppv24, npv24, n24)


# === 1. DELTA hEG Leuca-M1 (seuil -3.0) ===
delta = (piv_heg['M1'] - piv_heg['Leuca']).dropna()
df_d = pd.DataFrame({'randomisation': delta.index, 'delta': delta.values})
df_d = df_d.merge(valid[['randomisation', 'rr_12', 'rr_24', 'adeq_12', 'adeq_24']], on='randomisation')
df_d['group'] = np.where(df_d['delta'] > -3.0, 'MAUVAIS', 'BON')
se12_d, sp12_d, ppv12_d, npv12_d, n12_d, se24_d, sp24_d, ppv24_d, npv24_d, n24_d = calc_metrics(df_d)
print(f'Delta (n12={n12_d}, n24={n24_d}): Se12={se12_d:.0%} Sp12={sp12_d:.0%} PPV12={ppv12_d:.0%} NPV12={npv12_d:.0%}')
print(f'                                   Se24={se24_d:.0%} Sp24={sp24_d:.0%} PPV24={ppv24_d:.0%} NPV24={npv24_d:.0%}')

# === 2. CMR M3 ===
cmr = piv_mrd['M3'].dropna()
df_c = pd.DataFrame({'randomisation': cmr.index, 'cmr': cmr.values})
df_c = df_c.merge(valid[['randomisation', 'rr_12', 'rr_24', 'adeq_12', 'adeq_24']], on='randomisation')
df_c['group'] = np.where(df_c['cmr'] == 'NEGATIF', 'BON', 'MAUVAIS')
se12_c, sp12_c, ppv12_c, npv12_c, n12_c, se24_c, sp24_c, ppv24_c, npv24_c, n24_c = calc_metrics(df_c)
print(f'CMR M3 (n12={n12_c}, n24={n24_c}): Se12={se12_c:.0%} Sp12={sp12_c:.0%} PPV12={ppv12_c:.0%} NPV12={npv12_c:.0%}')
print(f'                                     Se24={se24_c:.0%} Sp24={sp24_c:.0%} PPV24={ppv24_c:.0%} NPV24={npv24_c:.0%}')

# === 3. JLCM J14 ===
jlcm = pd.read_csv(os.path.join(DATA_DIR, 'jlcm_predict_j14.csv'))
df_j = jlcm.dropna(subset=['group']).merge(valid[['randomisation', 'rr_12', 'rr_24', 'adeq_12', 'adeq_24']], on='randomisation')
se12_j, sp12_j, ppv12_j, npv12_j, n12_j, se24_j, sp24_j, ppv24_j, npv24_j, n24_j = calc_metrics(df_j)
print(f'JLCM J14 (n12={n12_j}, n24={n24_j}): Se12={se12_j:.0%} Sp12={sp12_j:.0%} PPV12={ppv12_j:.0%} NPV12={npv12_j:.0%}')
print(f'                                       Se24={se24_j:.0%} Sp24={sp24_j:.0%} PPV24={ppv24_j:.0%} NPV24={npv24_j:.0%}')

# === FIGURE ===
n_tot_j = len(df_j)
n_tot_c = len(df_c)
n_tot_d = len(df_d)
approaches = ['JLCM J14\n(n={})'.format(n_tot_j),
              'CMR M3\n(n={})'.format(n_tot_c),
              '\u0394hEG Leuca\u2192M1\nseuil=\u22123.0\n(n={})'.format(n_tot_d)]
metrics = ['Se', 'Sp', 'PPV', 'NPV']
colors_app = ['#7B1FA2', '#1565C0', '#C62828']  # purple, blue, red

data_12 = np.array([
    [se12_j, sp12_j, ppv12_j, npv12_j],
    [se12_c, sp12_c, ppv12_c, npv12_c],
    [se12_d, sp12_d, ppv12_d, npv12_d],
]) * 100

data_24 = np.array([
    [se24_j, sp24_j, ppv24_j, npv24_j],
    [se24_c, sp24_c, ppv24_c, npv24_c],
    [se24_d, sp24_d, ppv24_d, npv24_d],
]) * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
fig.suptitle('Performances diagnostiques — 3 approches de stratification',
             fontsize=14, fontweight='bold', y=0.98)

x = np.arange(len(metrics))
n_app = len(approaches)
width = 0.25

for panel_idx, (ax, data, rr_label) in enumerate([(ax1, data_12, 'R/R 12m'), (ax2, data_24, 'R/R 24m')]):
    for i, (app_label, color) in enumerate(zip(approaches, colors_app)):
        bars = ax.bar(x + i * width, data[i], width, color=color, alpha=0.85,
                      label=app_label if panel_idx == 0 else None)
        # Annotate
        for j, v in enumerate(data[i]):
            ax.text(x[j] + i * width, v + 1.5, f'{v:.0f}%', ha='center', va='bottom',
                    fontsize=8, fontweight='bold', color=color)

    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics, fontsize=12, fontweight='bold')
    ax.set_title(rr_label, fontsize=12, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.axhline(y=50, color='grey', linewidth=0.5, linestyle=':', alpha=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.15)

ax1.set_ylabel('(%)', fontsize=11)
fig.legend(loc='lower center', ncol=3, fontsize=10, bbox_to_anchor=(0.5, -0.02),
           frameon=True, framealpha=0.9)

plt.tight_layout(rect=[0, 0.05, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_comparison_metrics.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'\nOK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\R\u00e9union LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_comparison_metrics.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
