"""
Table 1 : caracteristiques baseline par classe JLCM-ctDNA (BON vs MAUVAIS).
Tests : Wilcoxon pour continues, Fisher pour categorielles.
"""
import os
import sys
import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# === Path resolution (added for package portability) ===
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _paths import INPUT_DIR, TABLES_DIR
except Exception:
    _here = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(_here, '..', 'input')
    TABLES_DIR = os.path.join(_here, '..', 'output', 'tables')
    os.makedirs(TABLES_DIR, exist_ok=True)

_legacy_master = os.path.join(INPUT_DIR, "master_dataset.csv")
df = pd.read_csv(_legacy_master if os.path.exists(_legacy_master) else os.path.join(INPUT_DIR, 'master_dataset.csv'))
df_jlcm = df[df.group.isin(['BON', 'MAUVAIS'])].copy()
bon = df_jlcm[df_jlcm.group == 'BON']
mau = df_jlcm[df_jlcm.group == 'MAUVAIS']

rows = []


def add_cont(label, col, fmt='.0f'):
    b = bon[col].dropna()
    m = mau[col].dropna()
    p = stats.mannwhitneyu(b, m, alternative='two-sided').pvalue if len(b) > 0 and len(m) > 0 else np.nan
    rows.append({'variable': label,
                 'BON': f'{b.median():{fmt}} ({b.quantile(0.25):{fmt}}-{b.quantile(0.75):{fmt}})',
                 'MAUVAIS': f'{m.median():{fmt}} ({m.quantile(0.25):{fmt}}-{m.quantile(0.75):{fmt}})',
                 'p': f'{p:.3f}' if not np.isnan(p) else 'NA'})


def add_cat(label, col, val=1, total_bon=22, total_mau=22):
    b = (bon[col] == val).sum()
    m = (mau[col] == val).sum()
    tab = [[total_bon - b, b], [total_mau - m, m]]
    p = stats.fisher_exact(tab).pvalue
    rows.append({'variable': label,
                 'BON': f'{int(b)} ({100*b/total_bon:.1f} %)',
                 'MAUVAIS': f'{int(m)} ({100*m/total_mau:.1f} %)',
                 'p': f'{p:.3f}'})


add_cont('Age (annees), mediane (IQR)', 'AGE', '.0f')
add_cat('Age >= 65', 'AGE_65')
add_cat('Sexe masculin', 'SEX_M')
add_cat('ECOG >= 2', 'ECOG_HIGH')
add_cat('IPI >= 3', 'IPI_HIGH')
add_cat('LDH > ULN', 'LDH_HIGH')
add_cat('Atteinte medullaire baseline', 'BM_INVOLV')
add_cont('MTV baseline (mL), mediane (IQR)', 'MTV_BL', '.1f')
add_cat('Bridging therapy', 'bridge_yes')

# Stade Ann Arbor
df_jlcm['stade_high'] = df_jlcm.STADE.isin(['III', 'IV']).astype(int)
bon = df_jlcm[df_jlcm.group == 'BON']
mau = df_jlcm[df_jlcm.group == 'MAUVAIS']
add_cat('Stade Ann Arbor III-IV', 'stade_high')

# B symptoms
df_jlcm['bsymp_yes'] = (df_jlcm.B_SYMPTOMS == 'Yes').astype(int)
bon = df_jlcm[df_jlcm.group == 'BON']
mau = df_jlcm[df_jlcm.group == 'MAUVAIS']
add_cat('B symptoms', 'bsymp_yes')

# Type CAR-T (axi-cel pour tous dans ALYCANTE)
rows.append({'variable': 'Type CAR-T (axi-cel)',
             'BON': '22 (100.0 %)', 'MAUVAIS': '22 (100.0 %)', 'p': 'NA'})

table1 = pd.DataFrame(rows)
out_csv = os.path.join(TABLES_DIR, 'table1_by_jlcm_class.csv')
table1.to_csv(out_csv, index=False)
# Legacy best-effort
for _p in (
    os.path.dirname(OUTPUT_DIR),
    os.path.join(TABLES_DIR, "table1_by_jlcm_class.csv"),
):
    try:
        table1.to_csv(_p, index=False)
    except Exception:
        pass
print('TABLE 1 — Caracteristiques baseline par classe JLCM-ctDNA')
print('  BON (n=22) | MAUVAIS (n=22)\n')
print(table1.to_string(index=False))
print('\nSaved:', out_csv)
