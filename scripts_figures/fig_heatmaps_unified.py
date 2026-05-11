#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Heatmaps AUC + C-index au même format exact"""
import sys, io, os, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
from lifelines.utils import concordance_index

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

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14', 'M1': 'M1', 'M3': 'M3'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])
piv = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')

tp_landmark = {'J14': 0.46, 'M1': 1.02, 'M3': 2.99}
baselines = ['Leuca', 'J-5', 'J0']
targets = ['J14', 'M1', 'M3']
bl_order = {'Leuca': 0, 'J-5': 1, 'J0': 2}
tp_order_map = {'J14': 3, 'M1': 4, 'M3': 5}

# Compute all metrics
auc_12 = np.full((3, 3), np.nan)
auc_24 = np.full((3, 3), np.nan)
ci_12 = np.full((3, 3), np.nan)
ci_24 = np.full((3, 3), np.nan)
ns = np.full((3, 3), np.nan)

for i, bl in enumerate(baselines):
    for j, tp in enumerate(targets):
        if bl not in piv.columns or tp not in piv.columns:
            continue
        if bl_order[bl] >= tp_order_map[tp]:
            continue
        delta = (piv[tp] - piv[bl]).dropna()
        merged = pd.DataFrame({'randomisation': delta.index, 'delta': delta.values})
        merged = merged.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
        lm = tp_landmark[tp]
        merged = merged[merged['efs_time'] > lm].copy()
        merged['efs_time_lm'] = merged['efs_time'] - lm
        merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)
        merged['rr_24'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 24)).astype(int)
        # Adequate follow-up filter
        merged['adeq_12'] = ((merged['efs_time'] >= 12) | (merged['efs_event'] == 1))
        merged['adeq_24'] = ((merged['efs_time'] >= 24) | (merged['efs_event'] == 1))
        if len(merged) < 10:
            continue
        ns[i, j] = len(merged)

        # AUC (adequate follow-up only)
        try:
            m_a12 = merged[merged['adeq_12']]
            m_a24 = merged[merged['adeq_24']]
            if len(m_a12) >= 10 and m_a12['rr_12'].nunique() == 2:
                auc_12[i, j] = roc_auc_score(m_a12['rr_12'], m_a12['delta'])
            if len(m_a24) >= 10 and m_a24['rr_24'].nunique() == 2:
                auc_24[i, j] = roc_auc_score(m_a24['rr_24'], m_a24['delta'])
        except:
            pass

        # C-index truncated 12m (adequate follow-up only)
        m12 = merged[merged['adeq_12']].copy()
        m12['ev'] = ((m12['efs_event'] == 1) & (m12['efs_time'] <= 12)).astype(int)
        m12['t'] = np.where(m12['efs_time'] <= 12, m12['efs_time_lm'], 12 - lm)
        m12 = m12[m12['t'] > 0]
        try:
            ci_12[i, j] = concordance_index(m12['t'], -m12['delta'], m12['ev'])
        except:
            pass

        # C-index truncated 24m (adequate follow-up only)
        m24 = merged[merged['adeq_24']].copy()
        m24['ev'] = ((m24['efs_event'] == 1) & (m24['efs_time'] <= 24)).astype(int)
        m24['t'] = np.where(m24['efs_time'] <= 24, m24['efs_time_lm'], 24 - lm)
        m24 = m24[m24['t'] > 0]
        try:
            ci_24[i, j] = concordance_index(m24['t'], -m24['delta'], m24['ev'])
        except:
            pass


def make_heatmap(data_left, data_right, ns, title_main, title_left, title_right,
                 vmin, vmax, label, outfile):
    """Produce exactly identical format heatmap pair."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.2))
    fig.suptitle(title_main, fontsize=12, fontweight='bold', y=1.02)

    for ax, data, subtitle in [(ax1, data_left, title_left), (ax2, data_right, title_right)]:
        im = ax.imshow(data, cmap='RdYlGn', vmin=vmin, vmax=vmax, aspect='auto')
        ax.set_xticks(range(3))
        ax.set_xticklabels(targets)
        ax.set_yticks(range(3))
        ax.set_yticklabels(baselines)
        ax.set_xlabel('Timepoint cible')
        ax.set_ylabel('Baseline')
        ax.set_title(subtitle, fontsize=11, pad=8)

        for ii in range(3):
            for jj in range(3):
                val = data[ii, jj]
                n = ns[ii, jj]
                if np.isnan(val):
                    ax.text(jj, ii, '\u2014', ha='center', va='center',
                            color='grey', fontsize=11)
                else:
                    color = 'white' if val > 0.70 else 'black'
                    ax.text(jj, ii, f'{val:.3f}\n(n={int(n)})', ha='center', va='center',
                            color=color, fontsize=10,
                            fontweight='bold' if val == np.nanmax(data) else 'normal')

        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label=label)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'OK: {outfile}')


# Common scale for both heatmaps
VMIN = 0.45
VMAX = 0.85

# AUC heatmap
make_heatmap(
    auc_12, auc_24, ns,
    'AUC ROC du \u0394ctDNA (hEG) par combinaison baseline \u2192 timepoint\n(analyse landmark, R/R strict)',
    'AUC R/R \u2264 12 mois', 'AUC R/R \u2264 24 mois',
    VMIN, VMAX, 'AUC',
    os.path.join(OUT_DIR, 'fig_heatmap_auc_delta.png')
)

# C-index heatmap
make_heatmap(
    ci_12, ci_24, ns,
    'C-index du \u0394ctDNA (hEG) par combinaison baseline \u2192 timepoint\n(analyse landmark, R/R strict)',
    'C-index R/R \u2264 12 mois', 'C-index R/R \u2264 24 mois',
    VMIN, VMAX, 'C-index',
    os.path.join(OUT_DIR, 'fig_heatmap_cindex_delta.png')
)

# Copy to network
for f in ['fig_heatmap_auc_delta.png', 'fig_heatmap_cindex_delta.png']:
    subprocess.run(['cp', os.path.join(OUT_DIR, f),
                    '//hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/'
                    'SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/'
                    'protocole ALYCANTE/Réunion LYSARC 2026/output/'],
                   capture_output=True)
print('Done.')
