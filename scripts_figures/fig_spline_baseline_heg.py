#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Spline Cox quadratique penalise — hEG baseline (Leuca, J-5, J0)
3 panels cote a cote, meme style que fig_spline_delta_heg"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lifelines import CoxPHFitter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === DATA ===
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

configs = [('Leuca', 3.5), ('J-5', 3.5), ('J0', 3.0)]

fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=True)
fig.suptitle('Spline Cox quadratique — hEG baseline (effet sur le HR)',
             fontsize=13, fontweight='bold', y=0.98)

for ax, (tp, seuil) in zip(axes, configs):
    vals = piv[tp].dropna()
    vals = vals[vals > 0]
    m = pd.DataFrame({'randomisation': vals.index, 'heg': vals.values})
    m = m.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
    m = m[m['efs_time'] > 0].copy()

    m['heg2'] = m['heg'] ** 2

    try:
        cph = CoxPHFitter(penalizer=0.1)
        cph.fit(m[['efs_time', 'efs_event', 'heg', 'heg2']], 'efs_time', 'efs_event')

        # Predict log-HR over grid
        heg_grid = np.linspace(m['heg'].min() - 0.3, m['heg'].max() + 0.3, 200)
        X_grid = pd.DataFrame({'heg': heg_grid, 'heg2': heg_grid ** 2})

        med = m['heg'].median()
        X_ref = np.array([med, med ** 2])
        beta = cph.params_.values
        log_hr = X_grid.values @ beta - X_ref @ beta

        # SE
        vcov = cph.variance_matrix_.values
        diff = X_grid.values - X_ref
        se = np.sqrt(np.diag(diff @ vcov @ diff.T))

        # Plot
        ax.plot(heg_grid, log_hr, color='#C62828', linewidth=2.5)
        ax.fill_between(heg_grid, log_hr - 1.96 * se, log_hr + 1.96 * se,
                        alpha=0.15, color='#C62828')

        p_heg = cph.summary['p']['heg']
        p_heg2 = cph.summary['p']['heg2']
        ax.text(0.03, 0.97, f'p(lin)={p_heg:.3f}\np(quad)={p_heg2:.3f}',
                transform=ax.transAxes, fontsize=8, va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    except Exception as e:
        ax.text(0.5, 0.5, f'Erreur: {e}', transform=ax.transAxes, ha='center')

    ax.axhline(y=0, color='grey', linewidth=0.8, linestyle='--')
    ax.axvline(x=seuil, color='black', linewidth=1.2, linestyle=':',
               label=f'Seuil {seuil:.1f} (m\u00e9diane)')

    # Rug plot
    for _, row in m.iterrows():
        col = '#C62828' if row['efs_event'] == 1 else '#1565C0'
        ax.plot(row['heg'], -0.6, '|', color=col, alpha=0.6, markersize=8, markeredgewidth=1.5)

    ax.set_xlabel(f'hEG {tp} (log10)', fontsize=11)
    ax.set_title(f'{tp} (n={len(m)}, seuil={seuil:.1f})', fontsize=11, fontweight='bold')
    ax.legend(fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    print(f'{tp}: n={len(m)}, p_lin={p_heg:.4f}, p_quad={p_heg2:.4f}')

axes[0].set_ylabel('log(HR) centr\u00e9 sur la m\u00e9diane', fontsize=11)

plt.tight_layout(rect=[0, 0, 1, 0.94])
outfile = os.path.join(SCRIPT_DIR, 'fig_spline_baseline_heg.png')
plt.savefig(outfile, dpi=200, bbox_inches='tight', facecolor='white')
print(f'\nOK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_spline_baseline_heg.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
