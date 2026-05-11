#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sankey diagram — Classification V2 (sans seuil, trajectoire J0-M12, inclusion >= J14)

Flow structure:
  Level 1: All patients (N=57)
  Level 2: Traj. monotone / non monotone
  Level 3: Atteint CMR (single node) / Pas de CMR (single node)
  Level 4: Post-CMR rules (R5-R8) + NC sub-rules
  Level 5: R/R 12m oui / non
  Level 6: R/R 24m oui / non
"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import plotly.graph_objects as go

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
OUTDIR = '.'
os.makedirs(OUTDIR, exist_ok=True)

# =====================================================================
# DATA LOADING
# =====================================================================
df = pd.read_excel('data/Donnees.xlsx')
df['visite_std'] = df['visite'].map({
    'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
    'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12',
    'Relapse/Progression': 'R/P'}).fillna(df['visite'])
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0

piv_mrd = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quali', aggfunc='first')
piv_heg = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')

surv = pd.read_excel('data/ALYCANTE_RNASeq_21OCT2025.xlsx')
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_event'] = surv['Event for EFS.1'].map({'Yes': 1, 'No': 0})
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')

# ── Correction J0 : soustraire le delai leucapherese → J0 ──────────────────
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
n_ok  = delay.notna().sum()
print(f"[J0] Delai leuca→J0 : mediane={delay.median():.2f}m, n_valides={n_ok}/{len(surv)}")
surv['efs_time'] = surv['efs_time'] - delay  # maintenant en mois depuis J0
# ───────────────────────────────────────────────────────────────────────────

is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['rr_12'] = ((surv['efs_event'] == 1) & (surv['efs_time'] <= 12) & is_rr).astype(int)
surv['rr_24'] = ((surv['efs_event'] == 1) & (surv['efs_time'] <= 24) & is_rr).astype(int)
pat_surv = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')

tps_eval = ['J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']
SEUIL_REPO = 1.5


# =====================================================================
# CLASSIFICATION V2
# =====================================================================
def get_mrd_and_heg(pat, tp):
    mrd = piv_mrd.loc[pat, tp] if tp in piv_mrd.columns and pd.notna(piv_mrd.loc[pat, tp]) else None
    val = piv_heg.loc[pat, tp] if tp in piv_heg.columns and pd.notna(piv_heg.loc[pat, tp]) else None
    return mrd, val


def classify_v2(pat):
    points = []
    for tp in tps_eval:
        mrd, val = get_mrd_and_heg(pat, tp)
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

    if first_neg_idx is not None:
        pre_cmr_pos = [(tp, val) for tp, mrd, val in points[:first_neg_idx] if mrd == 'POSITIF']
    else:
        pre_cmr_pos = [(tp, val) for tp, mrd, val in points if mrd == 'POSITIF']

    montee_pre_cmr = False
    montee_detail = ''
    if len(pre_cmr_pos) >= 2:
        for i in range(len(pre_cmr_pos) - 1):
            tp1, v1 = pre_cmr_pos[i]
            tp2, v2 = pre_cmr_pos[i + 1]
            if v2 > v1:
                montee_pre_cmr = True
                montee_detail = f'{tp1}({v1:.1f})->{tp2}({v2:.1f})'
                break

    atteint_cmr = first_neg_idx is not None

    if montee_pre_cmr and not atteint_cmr:
        return {'classe': 'MAUVAIS', 'regle': 1, 'sous_groupe': 'Traj. non monotone',
                'atteint_cmr': False, 'montee_pre_cmr': True, 'detail': montee_detail}

    if not atteint_cmr:
        if len(pre_cmr_pos) <= 1:
            tp0, v0 = pre_cmr_pos[0] if pre_cmr_pos else ('?', 0)
            return {'classe': 'MAUVAIS', 'regle': 4, 'sous_groupe': 'NC 1 seul point',
                    'atteint_cmr': False, 'montee_pre_cmr': False, 'detail': f'{tp0}({v0:.1f})'}
        all_decreasing = all(pre_cmr_pos[i][1] > pre_cmr_pos[i+1][1] for i in range(len(pre_cmr_pos)-1))
        if all_decreasing:
            return {'classe': 'BON', 'regle': 2, 'sous_groupe': 'NC decroissant',
                    'atteint_cmr': False, 'montee_pre_cmr': False, 'detail': ''}
        else:
            return {'classe': 'MAUVAIS', 'regle': 3, 'sous_groupe': 'NC stagnant/montant',
                    'atteint_cmr': False, 'montee_pre_cmr': False, 'detail': ''}

    first_neg_tp = points[first_neg_idx][0]
    repo_tps = [(tp, val) for tp, mrd, val in points
                if mrd == 'POSITIF' and tps_eval.index(tp) > tps_eval.index(first_neg_tp)]

    if len(repo_tps) == 0:
        return {'classe': 'BON', 'regle': 5, 'sous_groupe': 'CMR maintenue',
                'atteint_cmr': True, 'montee_pre_cmr': montee_pre_cmr, 'detail': f'1er NEG: {first_neg_tp}'}

    repo_tp_names = [r[0] for r in repo_tps]
    consecutive = any(tps_eval.index(repo_tp_names[i+1]) == tps_eval.index(repo_tp_names[i]) + 1
                      for i in range(len(repo_tp_names)-1))
    if consecutive:
        return {'classe': 'MAUVAIS', 'regle': 6, 'sous_groupe': 'Repo consecutif',
                'atteint_cmr': True, 'montee_pre_cmr': montee_pre_cmr, 'detail': ','.join(repo_tp_names)}

    max_heg = max(v for _, v in repo_tps)
    if max_heg >= SEUIL_REPO:
        return {'classe': 'MAUVAIS', 'regle': 7, 'sous_groupe': 'Repo fort (hEG>=1.5)',
                'atteint_cmr': True, 'montee_pre_cmr': montee_pre_cmr, 'detail': f'max={max_heg:.2f}'}
    else:
        return {'classe': 'BON', 'regle': 8, 'sous_groupe': 'Blip (<1.5)',
                'atteint_cmr': True, 'montee_pre_cmr': montee_pre_cmr, 'detail': f'max={max_heg:.2f}'}


# =====================================================================
# CLASSIFY ALL PATIENTS
# =====================================================================
results = []
for pat in piv_mrd.index:
    ps = pat_surv[pat_surv['randomisation'] == pat]
    if len(ps) == 0:
        continue
    res = classify_v2(pat)
    if res is None:
        continue
    res['pat'] = pat
    res['rr_12'] = ps['rr_12'].values[0]
    res['rr_24'] = ps['rr_24'].values[0]
    results.append(res)

df_res = pd.DataFrame(results)
N = len(df_res)

print(f"\n{'='*90}")
print(f"  CLASSIFICATION V2 — Sankey (sans seuil, J0-M12, inclusion >= J14)")
print(f"  N = {N} patients")
print(f"{'='*90}")

# Groups
traj_non_mono = df_res[df_res['montee_pre_cmr'] == True]
traj_monotone = df_res[df_res['montee_pre_cmr'] == False]
cmr_oui = df_res[df_res['atteint_cmr'] == True]
cmr_non = df_res[df_res['atteint_cmr'] == False]
nc_decroissant = df_res[(df_res['atteint_cmr'] == False) & (df_res['regle'] == 2)]
nc_stagnant = df_res[(df_res['atteint_cmr'] == False) & (df_res['regle'] == 3)]
nc_1point = df_res[(df_res['atteint_cmr'] == False) & (df_res['regle'] == 4)]
nc_nonmono = df_res[(df_res['atteint_cmr'] == False) & (df_res['regle'] == 1)]
cmr_maintenue = df_res[df_res['regle'] == 5]
repo_consec = df_res[df_res['regle'] == 6]
repo_fort = df_res[df_res['regle'] == 7]
blip = df_res[df_res['regle'] == 8]

# Cross-tabulations for monotone/non-monotone -> CMR oui/non
mono_cmr = df_res[(df_res['montee_pre_cmr'] == False) & (df_res['atteint_cmr'] == True)]
mono_nc = df_res[(df_res['montee_pre_cmr'] == False) & (df_res['atteint_cmr'] == False)]
nonmono_cmr = df_res[(df_res['montee_pre_cmr'] == True) & (df_res['atteint_cmr'] == True)]
nonmono_nc = df_res[(df_res['montee_pre_cmr'] == True) & (df_res['atteint_cmr'] == False)]


def fmt(name, df_sub, rr_col='rr_12'):
    n = len(df_sub)
    rr = int(df_sub[rr_col].sum()) if n > 0 else 0
    pct = f"{rr/n*100:.0f}%" if n > 0 else "-"
    return f"{name}: n={n}, R/R={rr} ({pct})"


# Text flowchart
print(f"\n  FLOWCHART")
print(f"  {'='*80}")
print(f"  {fmt('Tous patients', df_res)}")
print(f"  +-- {fmt('Traj. monotone', traj_monotone)}")
print(f"  |   +-- CMR: {len(mono_cmr)}, NC: {len(mono_nc)}")
print(f"  +-- {fmt('Traj. non monotone', traj_non_mono)}")
print(f"      +-- CMR: {len(nonmono_cmr)}, NC: {len(nonmono_nc)}")
print(f"  Atteint CMR (fused): n={len(cmr_oui)}")
print(f"  Pas de CMR (fused): n={len(cmr_non)}")
print(f"  Post-CMR: R5={len(cmr_maintenue)}, R6={len(repo_consec)}, R7={len(repo_fort)}, R8={len(blip)}")
print(f"  NC: R1={len(nc_nonmono)}, R2={len(nc_decroissant)}, R3={len(nc_stagnant)}, R4={len(nc_1point)}")

# R/R 12m and 24m for each rule group
for rr_col in ['rr_12', 'rr_24']:
    label = '12m' if rr_col == 'rr_12' else '24m'
    print(f"\n  R/R {label}:")
    for name, grp in [('CMR maintenue', cmr_maintenue), ('Blip', blip), ('NC decr', nc_decroissant),
                       ('Repo consec', repo_consec), ('Repo fort', repo_fort),
                       ('NC nonmono', nc_nonmono), ('NC stag', nc_stagnant), ('NC 1pt', nc_1point)]:
        if len(grp) > 0:
            print(f"    {fmt(name, grp, rr_col)}")

from scipy.stats import fisher_exact
# Filter for adequate follow-up before computing Fisher/PPV/NPV
adeq_12_pats = pat_surv[(pat_surv['efs_time'] >= 12) | (pat_surv['efs_event'] == 1)]['randomisation']
adeq_24_pats = pat_surv[(pat_surv['efs_time'] >= 24) | (pat_surv['efs_event'] == 1)]['randomisation']

df_a12 = df_res[df_res['pat'].isin(adeq_12_pats)]
bon12 = df_a12[df_a12['classe'] == 'BON']
mauv12 = df_a12[df_a12['classe'] == 'MAUVAIS']
table = [[int(mauv12['rr_12'].sum()), len(mauv12) - int(mauv12['rr_12'].sum())],
         [int(bon12['rr_12'].sum()), len(bon12) - int(bon12['rr_12'].sum())]]
odds, pval = fisher_exact(table)
ppv = int(mauv12['rr_12'].sum()) / max(len(mauv12), 1) * 100
npv = (len(bon12) - int(bon12['rr_12'].sum())) / max(len(bon12), 1) * 100
print(f"\n  Fisher 12m (n={len(df_a12)}): p={pval:.6f}, OR={odds:.1f}, PPV={ppv:.0f}%, NPV={npv:.0f}%")

df_a24 = df_res[df_res['pat'].isin(adeq_24_pats)]
bon24 = df_a24[df_a24['classe'] == 'BON']
mauv24 = df_a24[df_a24['classe'] == 'MAUVAIS']
table24 = [[int(mauv24['rr_24'].sum()), len(mauv24) - int(mauv24['rr_24'].sum())],
           [int(bon24['rr_24'].sum()), len(bon24) - int(bon24['rr_24'].sum())]]
odds24, pval24 = fisher_exact(table24)
ppv24 = int(mauv24['rr_24'].sum()) / max(len(mauv24), 1) * 100
npv24 = (len(bon24) - int(bon24['rr_24'].sum())) / max(len(bon24), 1) * 100
print(f"  Fisher 24m (n={len(df_a24)}): p={pval24:.6f}, OR={odds24:.1f}, PPV={ppv24:.0f}%, NPV={npv24:.0f}%")


# =====================================================================
# SANKEY DIAGRAM (PLOTLY) — Landscape
# =====================================================================
def n_rr_label(name, df_sub, rr_col='rr_12'):
    n = len(df_sub)
    rr = int(df_sub[rr_col].sum()) if n > 0 else 0
    pct = f"{rr/n*100:.0f}%" if n > 0 else "-"
    return f"{name}<br>n={n}, R/R 12m={rr} ({pct})"


nodes = []
node_colors = []
node_x = []
node_y = []


def add_node(label, color, x, y):
    idx = len(nodes)
    nodes.append(label)
    node_colors.append(color)
    node_x.append(x)
    node_y.append(y)
    return idx


# Colors
C_TOTAL = '#78909C'
C_MONOTONE = '#66BB6A'
C_NON_MONO = '#E53935'
C_CMR_OUI = '#42A5F5'
C_CMR_NON = '#EF5350'
C_CMR_MAINT = '#1565C0'
C_REPO_CONS = '#C62828'
C_REPO_FORT = '#D32F2F'
C_BLIP = '#2196F3'
C_NC_DECR = '#1E88E5'
C_NC_NONMONO = '#E53935'
C_NC_STAG = '#F44336'
C_NC_1PT = '#FF7043'
C_RR_OUI = '#B71C1C'
C_RR_NON = '#1B5E20'

# Layout: 8 levels across x
# x: 0.01 | 0.14 | 0.28 | 0.44 | 0.60 | 0.78 | 0.92
X1 = 0.01  # Total
X2 = 0.13  # Monotone / Non mono
X3 = 0.26  # CMR oui / non (fused)
X4 = 0.44  # Post-CMR rules + NC sub-rules
X5 = 0.66  # R/R 12m oui/non
X6 = 0.85  # R/R 24m oui/non

# Level 1: Total
i_total = add_node(n_rr_label('Tous patients', df_res), C_TOTAL, X1, 0.45)

# Level 2: Traj monotone / non monotone
i_mono = add_node(n_rr_label('Traj. monotone', traj_monotone), C_MONOTONE, X2, 0.25)
i_nonmono = add_node(n_rr_label('Traj. non monotone', traj_non_mono), C_NON_MONO, X2, 0.82)

# Level 3: CMR oui (fused) / Pas de CMR SPLIT par trajectoire
i_cmr = add_node(n_rr_label('Atteint CMR', cmr_oui), C_CMR_OUI, X3, 0.22)
i_nc_mono = add_node(n_rr_label('Pas de CMR (mono)', mono_nc), C_NC_DECR, X3, 0.60)
i_nc_nonmono_l3 = add_node(n_rr_label('Pas de CMR (non mono)', nonmono_nc), C_NC_NONMONO, X3, 0.85)

# Level 4: Post-CMR rules
# Ordre : CMR maintenue (BON) → Blip (BON) → Repo consec (MAUVAIS) → Repo fort (MAUVAIS)
y4 = 0.04
i_cmr_maint = add_node(n_rr_label('CMR maintenue [R5]', cmr_maintenue), C_CMR_MAINT, X4, y4)
y4 += 0.14
i_blip = None
if len(blip) > 0:
    i_blip = add_node(n_rr_label('Blip <1.5 [R8]', blip), C_BLIP, X4, y4)
    y4 += 0.10
i_repo_cons = None
if len(repo_consec) > 0:
    i_repo_cons = add_node(n_rr_label('Repo consecutif [R6]', repo_consec), C_REPO_CONS, X4, y4)
    y4 += 0.10
i_repo_fort = None
if len(repo_fort) > 0:
    i_repo_fort = add_node(n_rr_label('Repo fort >=1.5 [R7]', repo_fort), C_REPO_FORT, X4, y4)
    y4 += 0.10

# (NC split fait au niveau 3, pas de sous-noeuds NC au niveau 4)

# Level 5: R/R 12m oui / non — avec Se et Sp (filtre followup adequat)
rr12_oui = df_res[df_res['rr_12'] == 1]
rr12_non = df_res[df_res['rr_12'] == 0]
# Se/Sp sur patients avec suivi adequat seulement
adeq12 = (pat_surv.set_index('randomisation')['efs_time'] >= 12) | (pat_surv.set_index('randomisation')['efs_event'] == 1)
adeq12_pats = adeq12[adeq12].index
df_a12 = df_res[df_res['pat'].isin(adeq12_pats)]
bon_a12 = df_a12[df_a12['classe'] == 'BON']
mauv_a12 = df_a12[df_a12['classe'] == 'MAUVAIS']
TP12 = int(mauv_a12['rr_12'].sum())
FN12 = int(bon_a12['rr_12'].sum())
TN12 = len(bon_a12) - int(bon_a12['rr_12'].sum())
FP12 = len(mauv_a12) - int(mauv_a12['rr_12'].sum())
se12 = TP12 / max(TP12 + FN12, 1) * 100
sp12 = TN12 / max(TN12 + FP12, 1) * 100
i_rr12_oui = add_node(f'R/R 12m OUI<br>n={len(rr12_oui)}<br>Se={se12:.0f}% (n={len(df_a12)})', C_RR_OUI, X5, 0.75)
i_rr12_non = add_node(f'R/R 12m NON<br>n={len(rr12_non)}<br>Sp={sp12:.0f}%', C_RR_NON, X5, 0.20)

# Level 6: R/R 24m oui / non
rr24_oui = df_res[df_res['rr_24'] == 1]
rr24_non = df_res[df_res['rr_24'] == 0]
adeq24 = (pat_surv.set_index('randomisation')['efs_time'] >= 24) | (pat_surv.set_index('randomisation')['efs_event'] == 1)
adeq24_pats = adeq24[adeq24].index
df_a24 = df_res[df_res['pat'].isin(adeq24_pats)]
bon_a24 = df_a24[df_a24['classe'] == 'BON']
mauv_a24 = df_a24[df_a24['classe'] == 'MAUVAIS']
TP24 = int(mauv_a24['rr_24'].sum())
FN24 = int(bon_a24['rr_24'].sum())
TN24 = len(bon_a24) - int(bon_a24['rr_24'].sum())
FP24 = len(mauv_a24) - int(mauv_a24['rr_24'].sum())
se24 = TP24 / max(TP24 + FN24, 1) * 100
sp24 = TN24 / max(TN24 + FP24, 1) * 100
i_rr24_oui = add_node(f'R/R 24m OUI<br>n={len(rr24_oui)}<br>Se={se24:.0f}% (n={len(df_a24)})', C_RR_OUI, X6, 0.75)
i_rr24_non = add_node(f'R/R 24m NON<br>n={len(rr24_non)}<br>Sp={sp24:.0f}%', C_RR_NON, X6, 0.20)

# Links
links = []


def add_link(src, tgt, val, color_hex, opacity=0.40):
    if val > 0 and src is not None and tgt is not None:
        r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
        links.append((src, tgt, val, f'rgba({r},{g},{b},{opacity})'))


# L1 -> L2
add_link(i_total, i_mono, len(traj_monotone), C_MONOTONE)
add_link(i_total, i_nonmono, len(traj_non_mono), C_NON_MONO)

# L2 -> L3 (CMR fused + NC split par trajectoire)
add_link(i_mono, i_cmr, len(mono_cmr), C_CMR_OUI)
add_link(i_mono, i_nc_mono, len(mono_nc), C_NC_DECR)
add_link(i_nonmono, i_cmr, len(nonmono_cmr), C_CMR_OUI)
add_link(i_nonmono, i_nc_nonmono_l3, len(nonmono_nc), C_NC_NONMONO)

# L3 CMR -> L4 post-CMR rules
add_link(i_cmr, i_cmr_maint, len(cmr_maintenue), C_CMR_MAINT)
add_link(i_cmr, i_repo_cons, len(repo_consec), C_REPO_CONS)
add_link(i_cmr, i_repo_fort, len(repo_fort), C_REPO_FORT)
add_link(i_cmr, i_blip, len(blip), C_BLIP)

# L3 NC split -> L5 R/R 12m directement
n_ncmono_rr12 = int(mono_nc['rr_12'].sum())
n_ncmono_no12 = len(mono_nc) - n_ncmono_rr12
add_link(i_nc_mono, i_rr12_oui, n_ncmono_rr12, C_RR_OUI)
add_link(i_nc_mono, i_rr12_non, n_ncmono_no12, C_RR_NON)
n_ncnm_rr12 = int(nonmono_nc['rr_12'].sum())
n_ncnm_no12 = len(nonmono_nc) - n_ncnm_rr12
add_link(i_nc_nonmono_l3, i_rr12_oui, n_ncnm_rr12, C_RR_OUI)
add_link(i_nc_nonmono_l3, i_rr12_non, n_ncnm_no12, C_RR_NON)

# L4 post-CMR -> L5 R/R 12m
all_rule_nodes = [
    (i_cmr_maint, cmr_maintenue), (i_blip, blip),
    (i_repo_cons, repo_consec), (i_repo_fort, repo_fort)
]
for node_idx, grp in all_rule_nodes:
    if node_idx is not None and len(grp) > 0:
        n_rr = int(grp['rr_12'].sum())
        n_no = len(grp) - n_rr
        add_link(node_idx, i_rr12_oui, n_rr, C_RR_OUI)
        add_link(node_idx, i_rr12_non, n_no, C_RR_NON)

# L5 -> L6 R/R 24m
# R/R 12m OUI -> all were already R/R at 12m, check if also at 24m (they all are by definition)
# R/R 12m NON -> some become R/R at 24m
rr12_oui_and_24_oui = df_res[(df_res['rr_12'] == 1) & (df_res['rr_24'] == 1)]
rr12_oui_and_24_non = df_res[(df_res['rr_12'] == 1) & (df_res['rr_24'] == 0)]
rr12_non_and_24_oui = df_res[(df_res['rr_12'] == 0) & (df_res['rr_24'] == 1)]
rr12_non_and_24_non = df_res[(df_res['rr_12'] == 0) & (df_res['rr_24'] == 0)]

add_link(i_rr12_oui, i_rr24_oui, len(rr12_oui_and_24_oui), C_RR_OUI)
add_link(i_rr12_oui, i_rr24_non, len(rr12_oui_and_24_non), C_RR_NON)
add_link(i_rr12_non, i_rr24_oui, len(rr12_non_and_24_oui), C_RR_OUI)
add_link(i_rr12_non, i_rr24_non, len(rr12_non_and_24_non), C_RR_NON)

# Build Sankey
fig = go.Figure(data=[go.Sankey(
    arrangement='snap',
    node=dict(
        pad=22,
        thickness=16,
        line=dict(color='black', width=0.6),
        label=nodes,
        color=node_colors,
        x=node_x,
        y=node_y,
    ),
    link=dict(
        source=[l[0] for l in links],
        target=[l[1] for l in links],
        value=[l[2] for l in links],
        color=[l[3] for l in links],
    )
)])

fig.update_layout(
    title=dict(
        text=(f'Classification MRD V2 — Trajectoire (J0-M12, sans seuil pre-CMR)<br>'
              f'<sub>N={N} | R/R 12m: {int(df_res["rr_12"].sum())}/{N} '
              f'({int(df_res["rr_12"].sum())/N*100:.0f}%) | '
              f'R/R 24m: {int(df_res["rr_24"].sum())}/{N} '
              f'({int(df_res["rr_24"].sum())/N*100:.0f}%)</sub>'),
        font=dict(size=15),
        x=0.5,
    ),
    font=dict(size=12),
    width=2200,
    height=900,
    margin=dict(l=60, r=120, t=65, b=40),
    paper_bgcolor='white',
    plot_bgcolor='white',
)

outfile_raw = f'{OUTDIR}/sankey_classification_V2_plotly_raw.png'
fig.write_image(outfile_raw, scale=2)

# Auto-crop + white border
from PIL import Image, ImageOps
img = Image.open(outfile_raw)
diff = ImageOps.invert(img.convert('L'))
bbox = diff.getbbox()
if bbox:
    pad = 100
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(img.width, bbox[2] + pad)
    bottom = min(img.height, bbox[3] + pad)
    img_cropped = img.crop((left, top, right, bottom))
else:
    img_cropped = img

outfile = f'{OUTDIR}/sankey_classification_V2_plotly.png'
img_cropped.save(outfile, dpi=(300, 300))
os.remove(outfile_raw)
print(f'\nOK: {outfile} ({img_cropped.size[0]}x{img_cropped.size[1]})')

# Copy to network
net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    os.makedirs(net_dir, exist_ok=True)
    shutil.copy2(outfile, os.path.join(net_dir, 'sankey_classification_V2_plotly.png'))
    print(f'Copied to network: {net_dir}')
except Exception as e:
    print(f'Warning: could not copy to network: {e}')

print('\nDone.')
