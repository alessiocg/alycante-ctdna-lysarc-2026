# -*- coding: utf-8 -*-
"""Isolate the published J0+J14 subset and re-apply lymphoma-strict EFS to find apples-to-apples HR."""
import sys, pandas as pd, numpy as np, openpyxl, unicodedata
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from lifelines.statistics import logrank_test

NAS = Path("//Hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/protocole ALYCANTE/Réunion LYSARC 2026")
TBL = NAS / "output" / "blood_article_package" / "output" / "tables"
LEA_XLSX = NAS / "input" / "Base CART 02.04.xlsx"

lea_pred = pd.read_csv(TBL / "lea_extended_jlcm_predict.csv")
# Load Lea xlsx
wb = openpyxl.load_workbook(LEA_XLSX, data_only=True)
ws = wb['Generalites']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]
c = {n: hdr.index(n) for n in ['Nom','Type_CART','Cause_deces','Statut_der.nouv','Date.rechute']}
meta = pd.DataFrame([{'nom':str(r[c['Nom']]).strip().upper(),
                       'type':str(r[c['Type_CART']] or '').strip(),
                       'cause':str(r[c['Cause_deces']] or '').strip().upper(),
                       'statut':str(r[c['Statut_der.nouv']] or '').strip(),
                       'date_rechute':r[c['Date.rechute']]} for r in rows[1:] if r[c['Nom']]])

lea_pred['nom_clean'] = lea_pred['nom'].astype(str).str.strip().str.upper()
df = lea_pred.merge(meta, left_on='nom_clean', right_on='nom', how='left', suffixes=('','_meta'))

def is_lymph_event(row):
    if int(row.get('efs_event', 0)) != 1: return 0
    statut = str(row.get('statut','')).lower()
    statut = ''.join(ch for ch in unicodedata.normalize('NFD', statut) if unicodedata.category(ch) != 'Mn')
    cause = str(row.get('cause','')).upper()
    # rechute date present = R/R event
    date_rechute = row.get('date_rechute')
    if date_rechute is not None and not pd.isna(date_rechute): return 1
    # Or DC_CAUSE = Lymphoma
    if 'LYMPHOM' in cause: return 1
    # Or status mentions rechute/progression/recidive (without specifying date)
    if any(k in statut for k in ['rechute','progress','recidive']): return 1
    return 0

df['efs_event_lymph'] = df.apply(is_lymph_event, axis=1)

# === SUBSET 1: Published-like (J0+J14, with or without late) ===
df_j14 = df[df['group_j14'].isin(['BON','MAUVAIS'])].copy()
df_j14['risk_j14'] = (df_j14['group_j14']=='MAUVAIS').astype(int)
df_j14 = df_j14[df_j14['efs_time'] > 0]

# === SUBSET 2: Extended (all-tp classifiable) ===
df_ext = df[df['group_all'].isin(['BON','MAUVAIS'])].copy()
df_ext['risk_all'] = (df_ext['group_all']=='MAUVAIS').astype(int)
df_ext = df_ext[df_ext['efs_time'] > 0]

print(f"Subset published-like J0+J14: n={len(df_j14)} ({sum(df_j14['group_j14']=='BON')} BON / {sum(df_j14['group_j14']=='MAUVAIS')} MAUVAIS)")
print(f"Subset extended all-tp     : n={len(df_ext)} ({sum(df_ext['group_all']=='BON')} BON / {sum(df_ext['group_all']=='MAUVAIS')} MAUVAIS)")
print()
print("=" * 80)

def cox_summary(subset, group_col, event_col, label):
    sub = subset.copy()
    sub['risk'] = (sub[group_col]=='MAUVAIS').astype(int)
    n = len(sub); evt = int(sub[event_col].sum())
    nb = sum(sub[group_col]=='BON'); nm = sum(sub[group_col]=='MAUVAIS')
    ev_b = int(sub[sub[group_col]=='BON'][event_col].sum())
    ev_m = int(sub[sub[group_col]=='MAUVAIS'][event_col].sum())
    print(f"\n--- {label} (n={n}: {nb} BON ({ev_b} ev), {nm} MAUVAIS ({ev_m} ev), total events={evt}) ---")
    if nb < 1 or nm < 1 or evt < 1:
        print("  insufficient for Cox"); return
    try:
        cph = CoxPHFitter(penalizer=0.1)
        cph.fit(sub[['efs_time', event_col, 'risk']].rename(columns={'efs_time':'T', event_col:'E'}), 'T','E')
        hr = float(np.exp(cph.params_.iloc[0]))
        ci_lo, ci_hi = (float(np.exp(x)) for x in cph.confidence_intervals_.iloc[0])
        c = concordance_index(sub['efs_time'], -sub['risk'], sub[event_col])
        try:
            lr = logrank_test(sub[sub[group_col]=='BON']['efs_time'], sub[sub[group_col]=='MAUVAIS']['efs_time'],
                              sub[sub[group_col]=='BON'][event_col], sub[sub[group_col]=='MAUVAIS'][event_col])
            p = lr.p_value
        except: p = float('nan')
        print(f"  HR EFS = {hr:.2f} ({ci_lo:.2f}-{ci_hi:.2f})  C-index = {c:.3f}  log-rank P = {p:.4f}")
    except Exception as e:
        print(f"  Cox error: {e}")

# === ALL 4 COMBINATIONS ===
cox_summary(df_j14, 'group_j14', 'efs_event', 'PUBLISHED-LIKE (J0+J14, broad EFS)')
cox_summary(df_j14, 'group_j14', 'efs_event_lymph', 'PUBLISHED-LIKE (J0+J14, LYMPHOMA-strict EFS)')
cox_summary(df_ext, 'group_all', 'efs_event', 'EXTENDED (all-tp, broad EFS)')
cox_summary(df_ext, 'group_all', 'efs_event_lymph', 'EXTENDED (all-tp, LYMPHOMA-strict EFS)')

# === Diagnose: in the J0+J14 subset, what's the event composition? ===
print("\n" + "=" * 80)
print("=== Event composition diagnosis ===")
print("\nIn PUBLISHED-LIKE subset (J0+J14, n={}):".format(len(df_j14)))
ev_j14 = df_j14[df_j14['efs_event']==1]
print(f"  All EFS events (broad)    : {len(ev_j14)}")
print(f"  Lymphoma-only events      : {ev_j14['efs_event_lymph'].sum()}")
print(f"  Non-lymphoma events       : {(ev_j14['efs_event']-ev_j14['efs_event_lymph']).sum()}")
if len(ev_j14) > 0:
    print(f"\n  Cause de décès / Statut breakdown:")
    for _, r in ev_j14.iterrows():
        print(f"    {r['nom']:20s} | {r['statut']:30s} | DC_CAUSE: {r['cause'][:50]}")

print("\nIn EXTENDED subset (all-tp, n={}):".format(len(df_ext)))
ev_ext = df_ext[df_ext['efs_event']==1]
print(f"  All EFS events (broad)    : {len(ev_ext)}")
print(f"  Lymphoma-only events      : {ev_ext['efs_event_lymph'].sum()}")
print(f"  Non-lymphoma events       : {(ev_ext['efs_event']-ev_ext['efs_event_lymph']).sum()}")
print()
print("  Non-lymphoma causes:")
for _, r in ev_ext[ev_ext['efs_event_lymph']==0].iterrows():
    print(f"    {r['nom']:20s} | {r['statut']:30s} | DC_CAUSE: {r['cause'][:50]}")
