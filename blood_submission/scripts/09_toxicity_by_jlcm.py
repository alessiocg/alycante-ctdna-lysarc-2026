"""
Toxicite par classe JLCM-ctDNA (BON vs MAUVAIS).
CRS/ICANS any grade et grade >= 3, mortalite liee toxicite.
Fisher exact (effectifs petits).
"""
import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from scipy import stats

# === Path resolution (added for package portability) ===
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _paths import INPUT_DIR, TABLES_DIR
except Exception:
    _here = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(_here, '..', 'input')
    TABLES_DIR = os.path.join(_here, '..', 'output', 'tables')
    os.makedirs(TABLES_DIR, exist_ok=True)

_legacy_xls = os.path.join(INPUT_DIR, "ALYCANTE_export.xlsx")
_pkg_xls = os.path.join(INPUT_DIR, 'ALYCANTE_export_20260505.xlsx')
xls = _legacy_xls if os.path.exists(_legacy_xls) else _pkg_xls
_legacy_master = os.path.join(INPUT_DIR, "master_dataset.csv")
df = pd.read_csv(_legacy_master if os.path.exists(_legacy_master) else os.path.join(INPUT_DIR, 'master_dataset.csv'))
df['SUBJID'] = df.SUBJID.astype(str)
df_jlcm = df[df.group.isin(['BON', 'MAUVAIS'])].copy()
print('n classifie:', len(df_jlcm))

# AE / Toxicite par patient
ae = pd.read_excel(xls, sheet_name='AE')
ae['SUBJID'] = ae.SUBJID.astype(str)

# CRS
crs = ae[ae.AESI_SPEC == 'Cytokine Release Syndrome'].copy()
crs['INTENS_ASTCT_num'] = pd.to_numeric(crs.INTENS_ASTCT, errors='coerce')
crs_max = crs.groupby('SUBJID').INTENS_ASTCT_num.max().reset_index()
crs_max.columns = ['SUBJID', 'crs_max']

# ICANS
icans = ae[ae.AESI_SPEC == 'Neurotoxicity (ICANS)'].copy()
icans['INTENS_ICANS_num'] = pd.to_numeric(icans.INTENS_ICANS, errors='coerce')
icans_max = icans.groupby('SUBJID').INTENS_ICANS_num.max().reset_index()
icans_max.columns = ['SUBJID', 'icans_max']

df_tox = df_jlcm.merge(crs_max, on='SUBJID', how='left').merge(icans_max, on='SUBJID', how='left')
df_tox['crs_any'] = df_tox.crs_max.notna().astype(int)
df_tox['crs_3plus'] = (df_tox.crs_max >= 3).astype(int)
df_tox['icans_any'] = df_tox.icans_max.notna().astype(int)
df_tox['icans_3plus'] = (df_tox.icans_max >= 3).astype(int)

# Death cause "Toxicity of study treatment"
death = pd.read_excel(xls, sheet_name='DEATH')
death['SUBJID'] = death.SUBJID.astype(str)
tox_death_pts = death[death.DC_CAUSE.str.contains('Toxicity', na=False)].SUBJID.tolist()
df_tox['tox_death'] = df_tox.SUBJID.isin(tox_death_pts).astype(int)


def fisher(df, col):
    tab = pd.crosstab(df.group, df[col]).reindex(index=['BON', 'MAUVAIS'], columns=[0, 1], fill_value=0)
    p = stats.fisher_exact(tab.values)[1]
    return tab, p


rows = []
for col, label in [('crs_any', 'CRS any grade'),
                   ('crs_3plus', 'CRS grade >= 3 (ASTCT)'),
                   ('icans_any', 'ICANS any grade'),
                   ('icans_3plus', 'ICANS grade >= 3'),
                   ('tox_death', 'Mortalite liee toxicite')]:
    tab, p = fisher(df_tox, col)
    bon = tab.loc['BON', 1]
    mau = tab.loc['MAUVAIS', 1]
    rows.append({'event': label,
                 'BON_n': int(bon), 'BON_pct': 100 * bon / 22,
                 'MAUVAIS_n': int(mau), 'MAUVAIS_pct': 100 * mau / 22,
                 'fisher_p': p})

res = pd.DataFrame(rows)
out_csv = os.path.join(TABLES_DIR, 'toxicity_by_jlcm_class.csv')
res.to_csv(out_csv, index=False)
# Legacy best-effort
for _p in (
    os.path.dirname(OUTPUT_DIR),
    os.path.join(TABLES_DIR, "toxicity_by_jlcm_class.csv"),
):
    try:
        res.to_csv(_p, index=False)
    except Exception:
        pass
print('\nToxicite par classe JLCM (n=22 / n=22):')
print(res.round(3).to_string(index=False))
print('\nSaved:', out_csv)
