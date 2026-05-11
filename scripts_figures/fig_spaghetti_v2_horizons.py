#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Spaghetti trajectoires hEG — classification V2, 6 horizons (J14→M12)
BON=bleu, MAUVAIS=rouge, triangle noir=R/R. Layout 2x3 comme fig_km_landmark_jlcm"""
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
pat_surv = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])

tps_eval = ['J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']
tp_months = {'J0': 0, 'J14': 0.46, 'M1': 1.02, 'M3': 2.99, 'M6': 6.03, 'M9': 9.05, 'M12': 11.99}

piv_mrd = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quali', aggfunc='first')
piv_heg = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')

# === Classification V2 (simplified: reuse sankey logic) ===
SEUIL_REPO = 1.5

def classify_v2(pat, max_tp=None):
    """Classify patient using V2 rules on data up to max_tp (truncated)."""
    tps_allowed = tps_eval if max_tp is None else [tp for tp in tps_eval if tps_eval.index(tp) <= tps_eval.index(max_tp)]
    points = []
    for tp in tps_allowed:
        if tp not in piv_mrd.columns or tp not in piv_heg.columns:
            continue
        mrd = piv_mrd.loc[pat, tp] if pd.notna(piv_mrd.loc[pat, tp]) else None
        val = piv_heg.loc[pat, tp] if pd.notna(piv_heg.loc[pat, tp]) else None
        if mrd in ('POSITIF', 'NEGATIF'):
            heg = val if (val is not None and val > 0) else 0.0
            points.append((tp, mrd, heg))
    if len(points) == 0:
        return None

    first_neg_idx = None
    for i, (tp, mrd, val) in enumerate(points):
        if mrd == 'NEGATIF':
            first_neg_idx = i
            break

    pre_cmr_pos = [(tp, val) for tp, mrd, val in points[:first_neg_idx] if mrd == 'POSITIF'] if first_neg_idx is not None else [(tp, val) for tp, mrd, val in points if mrd == 'POSITIF']

    montee_pre_cmr = False
    if len(pre_cmr_pos) >= 2:
        for i in range(len(pre_cmr_pos) - 1):
            if pre_cmr_pos[i + 1][1] > pre_cmr_pos[i][1]:
                montee_pre_cmr = True
                break

    atteint_cmr = first_neg_idx is not None

    if montee_pre_cmr and not atteint_cmr:
        return 'MAUVAIS'
    if not atteint_cmr:
        if len(pre_cmr_pos) <= 1:
            return 'MAUVAIS'
        if all(pre_cmr_pos[i][1] > pre_cmr_pos[i+1][1] for i in range(len(pre_cmr_pos)-1)):
            return 'BON'
        return 'MAUVAIS'

    first_neg_tp = points[first_neg_idx][0]
    repo_tps = [(tp, val) for tp, mrd, val in points if mrd == 'POSITIF' and tps_eval.index(tp) > tps_eval.index(first_neg_tp)]

    if len(repo_tps) == 0:
        return 'BON'
    repo_names = [r[0] for r in repo_tps]
    consecutive = any(tps_eval.index(repo_names[i+1]) == tps_eval.index(repo_names[i]) + 1 for i in range(len(repo_names)-1))
    if consecutive:
        return 'MAUVAIS'
    if max(v for _, v in repo_tps) >= SEUIL_REPO:
        return 'MAUVAIS'
    return 'BON'


# === FIGURE 2x3 — classification V2 tronquee par horizon ===
horizons = [('J14', 0.46), ('M1', 1.02), ('M3', 2.99), ('M6', 6.03), ('M9', 9.05), ('M12', 11.99)]
# Map horizon name to tps_eval name for truncation
horizon_tp_map = {'J14': 'J14', 'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}

all_pats = [p for p in piv_mrd.index if p in pat_surv['randomisation'].values]

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Trajectoires ctDNA (hEG) par horizon \u2014 Classification V2 (donn\u00e9es tronqu\u00e9es)',
             fontsize=14, fontweight='bold', y=0.98)

for idx, (h_name, h_time) in enumerate(horizons):
    ax = axes[idx // 3, idx % 3]
    max_tp = horizon_tp_map[h_name]

    # Classify each patient on TRUNCATED data up to this horizon
    classif_h = {}
    for pat in all_pats:
        cl = classify_v2(pat, max_tp=max_tp)
        if cl is not None:
            classif_h[pat] = cl

    n_bon = sum(1 for c in classif_h.values() if c == 'BON')
    n_mauv = sum(1 for c in classif_h.values() if c == 'MAUVAIS')

    for pat, classe in classif_h.items():
        ps = pat_surv[pat_surv['randomisation'] == pat]
        if len(ps) == 0:
            continue
        ps = ps.iloc[0]

        # Get ALL trajectory points (full, not truncated) for visual context
        pat_tps = []
        pat_vals = []
        for tp in tps_eval:
            if tp in piv_heg.columns and pd.notna(piv_heg.loc[pat, tp]):
                pat_tps.append(tp_months[tp])
                pat_vals.append(piv_heg.loc[pat, tp])

        if len(pat_tps) == 0:
            continue

        col = '#1565C0' if classe == 'BON' else '#C62828'
        ax.plot(pat_tps, pat_vals, color=col, alpha=0.35, linewidth=0.8, zorder=1)

        # Triangle for R/R event
        if ps['efs_event'] == 1:
            # Find closest timepoint to R/R time
            valid_tps = [i for i, t in enumerate(pat_tps) if t <= ps['efs_time'] + 1]
            if valid_tps:
                last_idx = valid_tps[-1]
                ax.plot(pat_tps[last_idx], pat_vals[last_idx], marker='v', color='black',
                        markersize=5, zorder=5)

    # Vertical line at horizon
    ax.axvline(x=h_time, color='black', linewidth=1.2, linestyle='--', alpha=0.6)
    ax.text(h_time + 0.15, 6.5, h_name, fontsize=9, fontweight='bold', color='black')

    # Horizontal line at 1.5 hEG
    ax.axhline(y=1.5, color='#E65100', linewidth=1, linestyle=':', alpha=0.6)
    ax.text(12.5, 1.65, '1.5', fontsize=7, color='#E65100', ha='right')

    # Zero line
    ax.axhline(y=0, color='grey', linewidth=0.5, alpha=0.3)

    ax.set_xlim(-0.5, 13)
    ax.set_ylim(-0.5, 7)
    ax.set_xticks([tp_months[tp] for tp in tps_eval])
    ax.set_xticklabels(tps_eval, fontsize=8)
    # Se/Sp R/R 12m (followup adequat)
    classif_surv = []
    for pat, cl in classif_h.items():
        ps = pat_surv[pat_surv['randomisation'] == pat]
        if len(ps) == 0:
            continue
        ps = ps.iloc[0]
        classif_surv.append({'classe': cl, 'efs_time': ps['efs_time'], 'efs_event': ps['efs_event'],
                             'rr_12': int(ps['efs_event'] == 1 and ps['efs_time'] <= 12)})
    cs = pd.DataFrame(classif_surv)
    cs_a = cs[(cs['efs_time'] >= 12) | (cs['efs_event'] == 1)]
    tp_v = int(((cs_a['classe'] == 'MAUVAIS') & (cs_a['rr_12'] == 1)).sum())
    fp_v = int(((cs_a['classe'] == 'MAUVAIS') & (cs_a['rr_12'] == 0)).sum())
    fn_v = int(((cs_a['classe'] == 'BON') & (cs_a['rr_12'] == 1)).sum())
    tn_v = int(((cs_a['classe'] == 'BON') & (cs_a['rr_12'] == 0)).sum())
    se = tp_v / max(tp_v + fn_v, 1) * 100
    sp = tn_v / max(tn_v + fp_v, 1) * 100

    ax.set_title(f'Horizon {h_name} (n={n_bon + n_mauv}, BON={n_bon}, MAUVAIS={n_mauv})\n'
                 f'R/R12: Se={se:.0f}%, Sp={sp:.0f}% (n={len(cs_a)})',
                 fontsize=10, fontweight='bold')
    ax.set_xlabel('Timepoint', fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    if idx % 3 == 0:
        ax.set_ylabel('hEG (log10)', fontsize=11)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='#1565C0', linewidth=2, label='BON'),
    Line2D([0], [0], color='#C62828', linewidth=2, label='MAUVAIS'),
    Line2D([0], [0], marker='v', color='black', linestyle='None', markersize=6, label='R/R'),
    Line2D([0], [0], color='#E65100', linewidth=1, linestyle=':', label='hEG = 1.5'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=11,
           bbox_to_anchor=(0.5, 0.005), frameon=True)

plt.tight_layout(rect=[0, 0.04, 1, 0.96])
outfile = os.path.join(SCRIPT_DIR, 'fig_spaghetti_v2_horizons.png')
plt.savefig(outfile, dpi=200, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_spaghetti_v2_horizons.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
