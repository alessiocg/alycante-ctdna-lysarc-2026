#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Decision Curve Analysis — 3 méthodes superposées, style propre
JLCM J14, Delta hEG Leuca-M1, CMR M3
2 panels : R/R 12m et R/R 24m, landmark, followup adéquat"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 11

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

piv_heg = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')
piv_mrd = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quali', aggfunc='first')


# === DCA ===
def net_benefit(y_true, y_prob, threshold):
    n = len(y_true)
    if n == 0 or threshold >= 1 or threshold <= 0:
        return np.nan
    pred_pos = (y_prob >= threshold).astype(int)
    tp = ((pred_pos == 1) & (y_true == 1)).sum()
    fp = ((pred_pos == 1) & (y_true == 0)).sum()
    return tp / n - fp / n * threshold / (1 - threshold)


def dca_curve(y_true, y_prob, thresholds):
    return np.array([net_benefit(y_true, y_prob, t) for t in thresholds])


# === Prepare 3 methods ===

# 1. JLCM J14
jlcm = pd.read_csv(os.path.join(DATA_DIR, 'jlcm_predict_j14.csv'))
jlcm_m = jlcm.dropna(subset=['group', 'p_mauvais']).merge(
    valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
jlcm_m['rr_12'] = ((jlcm_m['efs_event'] == 1) & (jlcm_m['efs_time'] <= 12)).astype(int)
jlcm_m['rr_24'] = ((jlcm_m['efs_event'] == 1) & (jlcm_m['efs_time'] <= 24)).astype(int)

# 2. Delta hEG → logistic proba
delta = (piv_heg['M1'] - piv_heg['Leuca']).dropna()
delta_m = pd.DataFrame({'randomisation': delta.index, 'delta': delta.values})
delta_m = delta_m.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
delta_m['rr_12'] = ((delta_m['efs_event'] == 1) & (delta_m['efs_time'] <= 12)).astype(int)
delta_m['rr_24'] = ((delta_m['efs_event'] == 1) & (delta_m['efs_time'] <= 24)).astype(int)
for rr_col in ['rr_12', 'rr_24']:
    th = 12 if '12' in rr_col else 24
    d_a = delta_m[(delta_m['efs_time'] >= th) | (delta_m['efs_event'] == 1)].copy()
    lr = LogisticRegression()
    lr.fit(d_a[['delta']], d_a[rr_col])
    delta_m[f'prob_{rr_col}'] = lr.predict_proba(delta_m[['delta']])[:, 1]

# 3. CMR M3 → logistic proba (0/1 → proba via logistic sur le statut CMR)
cmr = piv_mrd['M3'].dropna()
cmr_m = pd.DataFrame({'randomisation': cmr.index, 'cmr_neg': (cmr == 'NEGATIF').astype(int).values})
cmr_m = cmr_m.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
cmr_m['rr_12'] = ((cmr_m['efs_event'] == 1) & (cmr_m['efs_time'] <= 12)).astype(int)
cmr_m['rr_24'] = ((cmr_m['efs_event'] == 1) & (cmr_m['efs_time'] <= 24)).astype(int)
cmr_m['prob_mauv'] = 1 - cmr_m['cmr_neg']  # binary: 0 (CMR) or 1 (pas CMR)


# === FIGURE ===
thresholds = np.arange(0.01, 0.99, 0.005)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

for ax, rr_col, rr_label in [(ax1, 'rr_12', 'R/R 12m'), (ax2, 'rr_24', 'R/R 24m')]:
    th = 12 if '12' in rr_col else 24

    # Smoothing function
    def smooth(y, window=15):
        s = pd.Series(y).rolling(window=window, center=True, min_periods=1).mean()
        return s.values

    # JLCM J14
    j_a = jlcm_m[(jlcm_m['efs_time'] >= th) | (jlcm_m['efs_event'] == 1)]
    nb_jlcm = smooth(dca_curve(j_a[rr_col].values, j_a['p_mauvais'].values, thresholds))
    ax.plot(thresholds, nb_jlcm, color='#1565C0', linewidth=2.5, solid_capstyle='round',
            label=f'JLCM J14 (n={len(j_a)})')

    # Delta hEG
    d_a = delta_m[(delta_m['efs_time'] >= th) | (delta_m['efs_event'] == 1)]
    nb_delta = smooth(dca_curve(d_a[rr_col].values, d_a[f'prob_{rr_col}'].values, thresholds))
    ax.plot(thresholds, nb_delta, color='#7B1FA2', linewidth=2.5, solid_capstyle='round',
            label=f'\u0394hEG Leuca\u2192M1 (n={len(d_a)})')

    # CMR M3 (binaire — pas de lissage)
    c_a = cmr_m[(cmr_m['efs_time'] >= th) | (cmr_m['efs_event'] == 1)]
    nb_cmr = dca_curve(c_a[rr_col].values, c_a['prob_mauv'].values, thresholds)
    ax.plot(thresholds, nb_cmr, color='#2E7D32', linewidth=2.5, solid_capstyle='round',
            label=f'CMR M3 (n={len(c_a)})')

    # Treat all
    prevalence = j_a[rr_col].mean()
    nb_all = np.array([prevalence - (1 - prevalence) * t / (1 - t) if t < 1 else np.nan for t in thresholds])
    ax.plot(thresholds, nb_all, color='#C62828', linewidth=1.2, linestyle='--', label='Traiter tous')

    # Treat none
    ax.axhline(y=0, color='grey', linewidth=1, linestyle=':', label='Ne traiter personne')

    # Prevalence
    ax.axvline(x=prevalence, color='green', linewidth=1.2, linestyle='--', alpha=0.6)
    ax.text(prevalence + 0.015, ax.get_ylim()[1] * 0.8 if ax.get_ylim()[1] > 0.1 else 0.35,
            f'Pr\u00e9valence\n{prevalence:.1%}', fontsize=9, color='green', fontweight='bold')

    ax.set_xlabel('Probabilit\u00e9 seuil', fontsize=12)
    ax.set_ylabel('B\u00e9n\u00e9fice net', fontsize=12)
    ax.set_title(f'Decision Curve Analysis \u2014 {rr_label}\n(endpoint R/R strict, followup ad\u00e9quat)',
                 fontsize=12, fontweight='bold')
    ax.set_xlim(0, 1)
    ymin = min(np.nanmin(nb_all[np.isfinite(nb_all)]), -0.05) if np.any(np.isfinite(nb_all)) else -0.15
    ax.set_ylim(max(ymin, -0.15), 1.0)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.9,
              edgecolor='#CCCCCC', fancybox=True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.15, linestyle='-')

plt.tight_layout()
outfile = os.path.join(SCRIPT_DIR, 'fig_dca_3methods.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_dca_3methods.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
