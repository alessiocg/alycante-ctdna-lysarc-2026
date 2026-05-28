"""
Build master dataset combining CRF ALYCANTE + JLCM-ctDNA J14 classes.

Output: master_dataset.csv with patient-level data (n=62 mFAS, JLCM class on n=44).
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

xls_path = os.path.join(INPUT_DIR, "ALYCANTE_export.xlsx")

# Admin / infusion
admin = pd.read_excel(xls_path, sheet_name='ADMIN')
admin_inf = admin[admin.PDT_ADMIN == 'Yes'][['SUBJID', 'DAT_INFUSION_TXT']].copy()
admin_inf['SUBJID'] = admin_inf.SUBJID.astype(str)
admin_inf['date_inf'] = pd.to_datetime(admin_inf.DAT_INFUSION_TXT, dayfirst=True, errors='coerce')

# Etat civil
etat = pd.read_excel(xls_path, sheet_name='ETAT_CIV')
etat['SUBJID'] = etat.SUBJID.astype(str)
etat_base = etat[etat.PERIOD == 'Baseline'][['SUBJID', 'SEX', 'AGE']]

# Extens
ext = pd.read_excel(xls_path, sheet_name='EXTENS')
ext['SUBJID'] = ext.SUBJID.astype(str)
ext_base = ext[ext.PERIOD == 'Baseline'][['SUBJID', 'STADE', 'IPI', 'B_SYMPTOMS', 'NBR_VISCER']].copy()
ext_base['IPI'] = pd.to_numeric(ext_base.IPI, errors='coerce')

# BOM + complement PET (BM_INVOLV_PET) pour BM involvement
bom = pd.read_excel(xls_path, sheet_name='BOM')
bom['SUBJID'] = bom.SUBJID.astype(str)
bom_base = bom[bom.PERIOD == 'Baseline'][['SUBJID', 'MYELO']].copy()
ev_full = pd.read_excel(xls_path, sheet_name='EVAL_RESP')
ev_full['SUBJID'] = ev_full.SUBJID.astype(str)
bm_pet = ev_full[ev_full.PERIOD == 'Baseline'][['SUBJID', 'BM_INVOLV_PET']].drop_duplicates('SUBJID')
bom_base = bom_base.merge(bm_pet, on='SUBJID', how='left')
bom_base['BM_INVOLV'] = ((bom_base.MYELO == 'Involved') | (bom_base.BM_INVOLV_PET == 'Yes')).astype(int)

# ECOG (CRF: "Ambulatory able to carry out work" = ECOG 1, "Normal activities" = 0,
# "Ambulatory unable to carry out work" = 2, "Confined to chair more than 50%" = 3, "Totally confined" = 4)
ec = pd.read_excel(xls_path, sheet_name='EVAL_CLIN')
ec['SUBJID'] = ec.SUBJID.astype(str)
ec_base = ec[ec.PERIOD == 'Baseline'][['SUBJID', 'ECOG']].drop_duplicates('SUBJID')
ecog_map = {
    'Normal activities': 0,
    'Asymptomatic': 0,
    'Ambulatory able to carry out work': 1,
    'Restricted activities': 1,
    'Symptomatic, ambulatory, capable of self-care': 1,
    'Ambulatory unable to carry out work': 2,
    'Active less than 50% of waking hours': 2,
    'Active more than 50% of waking hours': 2,
    'Confined to chair more than 50% of waking hours': 3,
    'Totally confined to chair': 4,
    'Bedridden': 4,
}
ec_base['ecog_num'] = ec_base.ECOG.map(ecog_map)

# Biochimie LDH
bio = pd.read_excel(xls_path, sheet_name='BIOCH')
bio['SUBJID'] = bio.SUBJID.astype(str)
ldh_base = bio[bio.PERIOD == 'Baseline'][['SUBJID', 'LDH', 'LDH_STAT']].copy()
ldh_base['LDH_num'] = pd.to_numeric(ldh_base.LDH, errors='coerce')
# LDH baseline n'a presque jamais LDH_STAT renseigne ; on calcule via ULN local
ranges = pd.read_excel(xls_path, sheet_name='LAB_NORM_RANGES')
ranges['SUBJID'] = ranges.SUBJID.astype(str)
ranges['LDH_ULN'] = pd.to_numeric(ranges.LDH_ULN, errors='coerce')
ldh_uln = ranges.groupby('SUBJID').LDH_ULN.median().reset_index()  # 1 ULN par patient
ldh_base = ldh_base.merge(ldh_uln, on='SUBJID', how='left')
ldh_base['LDH_HIGH'] = (ldh_base.LDH_num > ldh_base.LDH_ULN).astype(int)

# Bridge
br = pd.read_excel(xls_path, sheet_name='BRIDGE')
br['SUBJID'] = br.SUBJID.astype(str)
br_leuk = br[br.PERIOD == 'Leukapheresis'][['SUBJID', 'BRIDG_TRT']].copy()
br_leuk['bridge_yes'] = (br_leuk.BRIDG_TRT == 'Yes').astype(int)

# MTV
mtv = pd.read_excel(xls_path, sheet_name='TMTV')
mtv['SUBJID'] = mtv.SUBJID.astype(str)
mtv['MTV_BL'] = pd.to_numeric(mtv.MTVPET_BASELINE, errors='coerce')
mtv_base = mtv[['SUBJID', 'MTV_BL']]

# JLCM
jlcm = pd.read_csv(os.path.join(INPUT_DIR, "jlcm_predict_j14.csv"))
jlcm['SUBJID'] = jlcm.randomisation.astype(str)

# Build master
df = admin_inf.merge(etat_base, on='SUBJID', how='left')
df = df.merge(ext_base, on='SUBJID', how='left')
df = df.merge(bom_base[['SUBJID', 'BM_INVOLV']], on='SUBJID', how='left')
df = df.merge(ec_base[['SUBJID', 'ecog_num']], on='SUBJID', how='left')
df = df.merge(ldh_base[['SUBJID', 'LDH_num', 'LDH_HIGH', 'LDH_ULN']], on='SUBJID', how='left')
df = df.merge(br_leuk[['SUBJID', 'bridge_yes']], on='SUBJID', how='left')
df = df.merge(mtv_base, on='SUBJID', how='left')
df = df.merge(jlcm[['SUBJID', 'group', 'p_mauvais']], on='SUBJID', how='left')

# Survival
prog = pd.read_excel(xls_path, sheet_name='PROG')
prog['SUBJID'] = prog.SUBJID.astype(str)
prog['date_prog'] = pd.to_datetime(prog.R_DAT_RECHUT_TXT, dayfirst=True, errors='coerce')
prog_first = prog.groupby('SUBJID').date_prog.min().reset_index()

death = pd.read_excel(xls_path, sheet_name='DEATH')
death['SUBJID'] = death.SUBJID.astype(str)
death['date_death'] = pd.to_datetime(death.DAT_DC_TXT, dayfirst=True, errors='coerce')
death_min = death.groupby('SUBJID').date_death.min().reset_index()
death_min = death_min.merge(death[['SUBJID', 'DC_CAUSE']].drop_duplicates('SUBJID'), on='SUBJID', how='left')

surv = pd.read_excel(xls_path, sheet_name='SURVIVAL')
surv['SUBJID'] = surv.SUBJID.astype(str)
surv['date_contact'] = pd.to_datetime(surv.DATE_CONTACT_PROG_TXT, dayfirst=True, errors='coerce')
last_contact = surv.groupby('SUBJID').date_contact.max().reset_index()

df = df.merge(prog_first, on='SUBJID', how='left')
df = df.merge(death_min, on='SUBJID', how='left')
df = df.merge(last_contact, on='SUBJID', how='left')

# PFS
df['date_pfs'] = df[['date_prog', 'date_death']].min(axis=1).fillna(df.date_contact)
df['pfs_event'] = (df.date_prog.notna() | df.date_death.notna()).astype(int)
df['pfs_days'] = (df.date_pfs - df.date_inf).dt.days

# OS
df['date_os'] = df.date_death.fillna(df.date_contact)
df['os_event'] = df.date_death.notna().astype(int)
df['os_days'] = (df.date_os - df.date_inf).dt.days

# EFS == PFS (no formal next-line capture in CRF — treat as composite PFS)
df['efs_event'] = df.pfs_event
df['efs_days'] = df.pfs_days

# Catégories
df['IPI_HIGH'] = (df.IPI >= 3).astype(int)
df['ECOG_HIGH'] = (df.ecog_num >= 2).astype(int)
df['AGE_65'] = (df.AGE >= 65).astype(int)
df['MTV_BL_log10'] = np.log10(df.MTV_BL.astype(float).replace(0, 0.001))
df['MTV_HIGH'] = (df.MTV_BL >= df.MTV_BL.median()).astype(int)
df['SEX_M'] = (df.SEX == 'Male').astype(int)

df.to_csv(os.path.join(INPUT_DIR, "master_dataset.csv"), index=False)

print('--- Master dataset built ---')
print('Total rows (mFAS):', len(df))
print('JLCM group:', df.group.value_counts(dropna=False).to_dict())
print('Date census (max contact):', df.date_contact.max())
print('Median PFS days:', df.pfs_days.median())
print('PFS events:', df.pfs_event.sum())
print('OS events:', df.os_event.sum())

# KM
from lifelines import KaplanMeierFitter
kmf = KaplanMeierFitter()
kmf.fit(df.pfs_days.fillna(0), df.pfs_event)
print('\nPFS estimates (full mFAS):')
for d, lab in [(180, '6m'), (365, '12m'), (540, '18m'), (730, '24m')]:
    print(f'  {lab}: {kmf.survival_function_at_times(d).iloc[0]*100:.1f} %')

kmf2 = KaplanMeierFitter()
kmf2.fit(df.os_days.fillna(0), df.os_event)
print('\nOS estimates:')
for d, lab in [(180, '6m'), (365, '12m'), (540, '18m'), (730, '24m')]:
    print(f'  {lab}: {kmf2.survival_function_at_times(d).iloc[0]*100:.1f} %')

# Couverture covariables
print('\n--- Coverage covariables ---')
for c in ['SEX', 'AGE', 'IPI', 'ECOG_HIGH', 'LDH_HIGH', 'MTV_BL', 'bridge_yes', 'BM_INVOLV']:
    print(f'  {c}: n={df[c].notna().sum()}/{len(df)}')
