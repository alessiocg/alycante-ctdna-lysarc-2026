# -*- coding: utf-8 -*-
"""
investigate_lea_drop.py
Pourquoi HR EFS chute de 8.32 (J0+J14 n=18) à 5.19 (extended n=41) ?

4 hypothèses :
H1. SELECTION : les patients J0+J14 sont enrichis en cas "purs" (bons + très mauvais),
    les late-only sont plus hétérogènes.
H2. SPARSITY : predictClass avec seulement M1+ (pas de D0/D14) extrapole, donne classification noisy.
H3. PRODUIT CAR-T : Léa a 3 produits (Yescarta/Kymriah/Breyanzi), ALYCANTE n'a qu'Axi-cel.
    Les non-Yescarta peuvent avoir une kinetique différente.
H4. EVENT MIX : les events "extended" peuvent inclure morts non-lymphome, diluant l'effet.
"""
import sys, pandas as pd, numpy as np, openpyxl, re, unicodedata
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test
from lifelines.utils import concordance_index

NAS = Path("//Hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/protocole ALYCANTE/Réunion LYSARC 2026")
TBL = NAS / "output" / "blood_article_package" / "output" / "tables"
LEA_XLSX = NAS / "input" / "Base CART 02.04.xlsx"

# Load extended data
lea_long = pd.read_csv(TBL / "lea_extended_jlcm_input.csv")
lea_pred = pd.read_csv(TBL / "lea_extended_jlcm_predict.csv")

# Load Lea xlsx for CAR-T product info
wb = openpyxl.load_workbook(LEA_XLSX, data_only=True)
ws = wb['Generalites']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]
c = {n: hdr.index(n) for n in ['Nom','Type_CART','Lignes_avantCART','Cause_deces','Statut_der.nouv','Date.rechute']}
lea_meta = []
for r in rows[1:]:
    nm = r[c['Nom']]
    if not nm: continue
    lea_meta.append({'nom':str(nm).strip().upper(),
                     'type':str(r[c['Type_CART']] or '').strip(),
                     'lignes':r[c['Lignes_avantCART']],
                     'cause':str(r[c['Cause_deces']] or '').strip().upper(),
                     'statut':str(r[c['Statut_der.nouv']] or '').strip(),
                     'date_rechute':r[c['Date.rechute']]})
meta = pd.DataFrame(lea_meta)
print(f"Lea metadata loaded : {len(meta)} patients")

# Merge with predictions
lea_pred['nom_clean'] = lea_pred['nom'].astype(str).str.strip().str.upper()
merged = lea_pred.merge(meta, left_on='nom_clean', right_on='nom', how='left', suffixes=('','_meta'))
print(f"Merged : {len(merged)} patients, {merged['type'].notna().sum()} with CART type metadata")

# ========= STRATIFICATION BY TIMEPOINT PATTERN =========
def has_tp(tps_str, tp):
    return tp in str(tps_str).split(',')

merged['has_J0'] = merged['tps'].apply(lambda x: has_tp(x, 'J0'))
merged['has_J14'] = merged['tps'].apply(lambda x: has_tp(x, 'J14'))
merged['has_J0_AND_J14'] = merged['has_J0'] & merged['has_J14']
merged['has_late'] = merged['tps'].apply(lambda x: any(has_tp(x, t) for t in ['M1','M3','M6','M9','M12']))
merged['n_tp'] = merged['n_tp_all']

# Strata
merged['stratum'] = 'unclassified'
merged.loc[ merged['has_J0_AND_J14'] & ~merged['has_late'], 'stratum'] = 'J0+J14 only'
merged.loc[ merged['has_J0_AND_J14'] &  merged['has_late'], 'stratum'] = 'J0+J14 + late'
merged.loc[~merged['has_J0_AND_J14'], 'stratum'] = 'late only (no J0+J14)'

# Restrict to classifiable
df = merged[merged['group_all'].isin(['BON','MAUVAIS'])].copy()
df['risk'] = (df['group_all']=='MAUVAIS').astype(int)
print(f"\nClassifiable : {len(df)} patients")

print("\n=== H1/H2 : Stratification by timepoint pattern ===")
for stratum, sub in df.groupby('stratum'):
    n = len(sub)
    n_ev = int(sub['efs_event'].sum())
    nb = int((sub['group_all']=='BON').sum())
    nm = int((sub['group_all']=='MAUVAIS').sum())
    print(f"\n{stratum} (n={n}, BON={nb}, MAUVAIS={nm}, events={n_ev}):")
    if n < 4 or n_ev < 1 or nb < 1 or nm < 1:
        print('  (too few events/patients for Cox)'); continue
    try:
        cph = CoxPHFitter(penalizer=0.1)
        cph.fit(sub[['efs_time','efs_event','risk']].rename(columns={'efs_time':'T','efs_event':'E'}), 'T','E')
        hr = float(np.exp(cph.params_.iloc[0]))
        ci_lo, ci_hi = (float(np.exp(x)) for x in cph.confidence_intervals_.iloc[0])
        ci_idx = concordance_index(sub['efs_time'], -sub['risk'], sub['efs_event'])
        lr = logrank_test(sub[sub['group_all']=='BON']['efs_time'], sub[sub['group_all']=='MAUVAIS']['efs_time'],
                          sub[sub['group_all']=='BON']['efs_event'], sub[sub['group_all']=='MAUVAIS']['efs_event'])
        print(f"  HR EFS = {hr:.2f} ({ci_lo:.2f}-{ci_hi:.2f})  C-index = {ci_idx:.3f}  log-rank P = {lr.p_value:.4f}")
    except Exception as e:
        print(f"  Error : {e}")

# ========= H3 : CART product =========
print("\n=== H3 : CART product ===")
print(df['type'].value_counts(dropna=False))
for prod, sub in df.groupby('type'):
    n = len(sub); n_ev = int(sub['efs_event'].sum())
    nb = int((sub['group_all']=='BON').sum()); nm = int((sub['group_all']=='MAUVAIS').sum())
    print(f"\n{prod} (n={n}, BON={nb}, MAUVAIS={nm}, events={n_ev}):")
    if n < 4 or n_ev < 2 or nb < 1 or nm < 1:
        print('  (too few)'); continue
    try:
        cph = CoxPHFitter(penalizer=0.1)
        cph.fit(sub[['efs_time','efs_event','risk']].rename(columns={'efs_time':'T','efs_event':'E'}), 'T','E')
        hr = float(np.exp(cph.params_.iloc[0]))
        ci_lo, ci_hi = (float(np.exp(x)) for x in cph.confidence_intervals_.iloc[0])
        print(f"  HR EFS = {hr:.2f} ({ci_lo:.2f}-{ci_hi:.2f})")
    except Exception as e: print(f"  Error : {e}")

# ========= H4 : Event composition (lymphoma vs not) =========
# Use Cause_deces from metadata
print("\n=== H4 : Event composition for those with events ===")
events_df = df[df['efs_event']==1].copy()
print(events_df.groupby(['group_all','cause']).size().unstack(fill_value=0))

# Now classify events: lymphoma-related vs other
def is_lymph_event(row):
    statut = str(row.get('statut','')).lower()
    statut = ''.join(ch for ch in unicodedata.normalize('NFD', statut) if unicodedata.category(ch) != 'Mn')
    cause = str(row.get('cause','')).upper()
    if 'LYMPHOM' in cause or 'PROGRESSION' in cause or 'RECHUTE' in statut or 'PROGRESS' in statut or 'RECIDIVE' in statut:
        return 1
    return 0

events_df['is_lymph'] = events_df.apply(is_lymph_event, axis=1)
print(f"\nEvents lymph-related : {events_df['is_lymph'].sum()}/{len(events_df)}")
print(events_df.groupby(['group_all','is_lymph']).size().unstack(fill_value=0))

# Recompute Cox with lymph-only events
df['efs_event_lymph'] = 0
for idx, row in df.iterrows():
    if row['efs_event']==1:
        if is_lymph_event(row): df.at[idx,'efs_event_lymph'] = 1
print(f"\nLymph-only events in full extended cohort : {df['efs_event_lymph'].sum()}/{len(df)}")
print(df.groupby('group_all').agg(n=('ID','count'), evt_all=('efs_event','sum'), evt_lymph=('efs_event_lymph','sum')))

try:
    cph = CoxPHFitter(penalizer=0.1)
    cph.fit(df[['efs_time','efs_event_lymph','risk']].rename(columns={'efs_time':'T','efs_event_lymph':'E'}), 'T','E')
    hr = float(np.exp(cph.params_.iloc[0]))
    ci_lo, ci_hi = (float(np.exp(x)) for x in cph.confidence_intervals_.iloc[0])
    ci_idx = concordance_index(df['efs_time'], -df['risk'], df['efs_event_lymph'])
    print(f"\n=== H4 Sensitivity : Cox with LYMPHOMA-only events (extended cohort) ===")
    print(f"  HR EFS = {hr:.2f} ({ci_lo:.2f}-{ci_hi:.2f})  C-index = {ci_idx:.3f}")
except Exception as e: print(f"  Error : {e}")

# ========= Bonus : effect of n_tp on classification quality =========
print("\n=== Bonus : Effect of n_tp on prediction ===")
print(df.groupby('n_tp').agg(n=('ID','count'), bon=('group_all', lambda x: (x=='BON').sum()),
                              mauv=('group_all', lambda x: (x=='MAUVAIS').sum()),
                              evt=('efs_event','sum')).reset_index())
