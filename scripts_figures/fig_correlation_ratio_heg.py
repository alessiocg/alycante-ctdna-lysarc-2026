#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Correlation ctDNA ratio vs hEG — coloration R/R 12m, R/R 12-24m, pas de R/R"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

df = pd.read_excel(os.path.join(DATA_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df['MRD_quanti_quota'] = pd.to_numeric(df['MRD_quanti_quota'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_quota'] = 0.0

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
valid['rr_12'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 12)).astype(int)
valid['rr_24'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 24)).astype(int)
valid['rr_12_24'] = ((valid['rr_24'] == 1) & (valid['rr_12'] == 0)).astype(int)

# Merge
plot_df = df[['randomisation', 'MRD_quanti_heg', 'MRD_quanti_quota']].dropna().copy()
plot_df = plot_df[(plot_df['MRD_quanti_heg'] > 0) & (plot_df['MRD_quanti_quota'] > 0)]
plot_df = plot_df.merge(valid[['randomisation', 'rr_12', 'rr_12_24']], on='randomisation')

# Log10 du ratio pour meilleure visualisation
plot_df['log_ratio'] = np.log10(plot_df['MRD_quanti_quota'])

# Groupe couleur
def grp_color(row):
    if row['rr_12'] == 1:
        return 'R/R \u226412m'
    elif row['rr_12_24'] == 1:
        return 'R/R 12\u201324m'
    else:
        return 'Pas de R/R'

plot_df['grp'] = plot_df.apply(grp_color, axis=1)

# Spearman
rho, pval = spearmanr(plot_df['MRD_quanti_heg'], plot_df['log_ratio'])
print(f'Spearman: rho={rho:.3f}, p={pval:.2e}, n={len(plot_df)}')

# Figure
colors = {'R/R \u226412m': '#C62828', 'R/R 12\u201324m': '#FF8F00', 'Pas de R/R': '#1565C0'}
markers = {'R/R \u226412m': '^', 'R/R 12\u201324m': 's', 'Pas de R/R': 'o'}

fig, ax = plt.subplots(figsize=(8, 7))

for grp_name in ['Pas de R/R', 'R/R 12\u201324m', 'R/R \u226412m']:
    sub = plot_df[plot_df['grp'] == grp_name]
    ax.scatter(sub['MRD_quanti_heg'], sub['log_ratio'],
               c=colors[grp_name], marker=markers[grp_name],
               s=40, alpha=0.7, edgecolors='white', linewidths=0.3,
               label=f'{grp_name} (n={len(sub)})', zorder=3)

# Regression line
z = np.polyfit(plot_df['MRD_quanti_heg'], plot_df['log_ratio'], 1)
p = np.poly1d(z)
x_line = np.linspace(plot_df['MRD_quanti_heg'].min(), plot_df['MRD_quanti_heg'].max(), 100)
ax.plot(x_line, p(x_line), color='grey', linewidth=1.5, linestyle='--', alpha=0.7, zorder=2)

# Annotation
p_txt = f'{pval:.2e}' if pval < 0.001 else f'{pval:.4f}'
ax.text(0.03, 0.97, f'Spearman \u03c1 = {rho:.3f}\np = {p_txt}\nn = {len(plot_df)} mesures',
        transform=ax.transAxes, fontsize=10, va='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#CCCCCC', alpha=0.9))

ax.set_xlabel('hEG (log10)', fontsize=12)
ax.set_ylabel('ctDNA ratio (log10)', fontsize=12)
ax.set_title('Corr\u00e9lation ctDNA ratio vs hEG', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='lower right', framealpha=0.9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(alpha=0.15)

plt.tight_layout()
outfile = os.path.join(SCRIPT_DIR, 'fig_correlation_ratio_heg.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_correlation_ratio_heg.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
