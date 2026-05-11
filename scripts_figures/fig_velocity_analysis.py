#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Velocite ctDNA — pente hEG par segment, R/R 12m vs Non R/R
4 panels: J-5→J0, J0→J14, J14→M1, M1→M3"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, fisher_exact

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
valid['rr_12'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 12)).astype(int)
valid['adeq_12'] = ((valid['efs_time'] >= 12) | (valid['efs_event'] == 1))

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])
piv = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')

tp_months = {'Leuca': -1.28, 'J-5': -0.16, 'J0': 0, 'J14': 0.46, 'M1': 1.02, 'M3': 2.99}

segments = [
    ('J-5', 'J0', 'J-5 \u2192 J0'),
    ('J0', 'J14', 'J0 \u2192 J14'),
    ('J14', 'M1', 'J14 \u2192 M1'),
    ('M1', 'M3', 'M1 \u2192 M3'),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('V\u00e9locit\u00e9 ctDNA (pente hEG / mois) par segment \u2014 R/R 12m',
             fontsize=13, fontweight='bold', y=0.98)

for idx, (tp1, tp2, label) in enumerate(segments):
    ax = axes[idx // 2, idx % 2]

    if tp1 not in piv.columns or tp2 not in piv.columns:
        ax.text(0.5, 0.5, f'{label}: pas de donn\u00e9es', transform=ax.transAxes, ha='center')
        continue

    dt = tp_months[tp2] - tp_months[tp1]
    delta = (piv[tp2] - piv[tp1]).dropna()
    slope = delta / dt  # pente par mois

    m = pd.DataFrame({'randomisation': slope.index, 'slope': slope.values})
    m = m.merge(valid[['randomisation', 'rr_12', 'adeq_12']], on='randomisation')
    m_a = m[m['adeq_12']].copy()

    g_norr = m_a[m_a['rr_12'] == 0]['slope']
    g_rr = m_a[m_a['rr_12'] == 1]['slope']

    # Mann-Whitney
    if len(g_norr) >= 3 and len(g_rr) >= 3:
        _, mw_p = mannwhitneyu(g_norr, g_rr, alternative='two-sided')
    else:
        mw_p = np.nan

    # Fisher on median split
    med = m_a['slope'].median()
    m_a['above_med'] = (m_a['slope'] > med).astype(int)
    table = [[int(((m_a['above_med'] == 1) & (m_a['rr_12'] == 1)).sum()),
              int(((m_a['above_med'] == 1) & (m_a['rr_12'] == 0)).sum())],
             [int(((m_a['above_med'] == 0) & (m_a['rr_12'] == 1)).sum()),
              int(((m_a['above_med'] == 0) & (m_a['rr_12'] == 0)).sum())]]
    try:
        or_val, fisher_p = fisher_exact(table)
    except:
        or_val, fisher_p = np.nan, np.nan

    # Boxplot
    bp_data = [g_norr.values, g_rr.values]
    bp = ax.boxplot(bp_data,
                    tick_labels=[f'Non R/R\nn={len(g_norr)}', f'R/R 12m\nn={len(g_rr)}'],
                    patch_artist=True, widths=0.5,
                    medianprops=dict(color='darkred', linewidth=2))
    bp['boxes'][0].set_facecolor('#90CAF9')
    bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor('#EF9A9A')
    bp['boxes'][1].set_alpha(0.7)

    # Zero line
    ax.axhline(y=0, color='grey', linewidth=0.8, linestyle='--')

    # Median line (all patients)
    ax.axhline(y=med, color='#E65100', linewidth=1.2, linestyle=':', alpha=0.7)
    ax.text(2.55, med + 0.05, f'm\u00e9diane={med:.2f}', fontsize=7.5,
            color='#E65100', fontweight='bold', ha='right', va='bottom')

    # Stats
    mw_txt = f'p={mw_p:.3f}' if not np.isnan(mw_p) and mw_p >= 0.001 else 'p<0.001'
    or_txt = f'{or_val:.1f}' if not np.isnan(or_val) and or_val < 100 else '\u221e'
    fisher_txt = f'{fisher_p:.3f}' if not np.isnan(fisher_p) and fisher_p >= 0.001 else '<0.001'
    ax.text(0.97, 0.97,
            f'Mann-Whitney {mw_txt}\n'
            f'Pente > m\u00e9diane : OR={or_txt}, p={fisher_txt}',
            transform=ax.transAxes, ha='right', va='top', fontsize=8.5,
            color='#333333',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F5F5F5', edgecolor='#CCCCCC', alpha=0.9))

    ax.set_title(f'Segment {label}', fontsize=12, fontweight='bold')
    ax.set_ylabel('Pente (hEG / mois)', fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.15, linestyle='--')

    print(f'{label}: n={len(m_a)}, MW p={mw_p:.4f}, OR={or_val:.1f}, Fisher p={fisher_p:.4f}')

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_velocity_analysis.png')
plt.savefig(outfile, dpi=200, bbox_inches='tight', facecolor='white')
print(f'\nOK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_velocity_analysis.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
