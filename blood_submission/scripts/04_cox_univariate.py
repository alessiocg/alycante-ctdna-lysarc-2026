"""
Cox multivarie EFS et OS, JLCM-ctDNA ajuste sur covariables cliniques.
Penalizer Firth-like (0.1) car EFS BON = 4 evenements / 22 vs MAUVAIS = 22/22 (separation parfaite).
n=44 patients avec classe JLCM.
"""
import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from lifelines import CoxPHFitter

# === Path resolution (added for package portability) ===
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _paths import INPUT_DIR, TABLES_DIR
except Exception:
    _here = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(_here, '..', 'input')
    TABLES_DIR = os.path.join(_here, '..', 'output', 'tables')
    os.makedirs(TABLES_DIR, exist_ok=True)

def _resolve_master():
    legacy = os.path.join(INPUT_DIR, "master_dataset.csv")
    return legacy if os.path.exists(legacy) else os.path.join(INPUT_DIR, 'master_dataset.csv')

df = pd.read_csv(_resolve_master())
df['jlcm'] = (df.group == 'MAUVAIS').astype(int)
df_jlcm = df[df.group.isin(['BON', 'MAUVAIS'])].copy()
df_jlcm = df_jlcm.dropna(subset=['MTV_BL_log10', 'ecog_num', 'LDH_num', 'IPI'])
print('Apres dropna covariables :', len(df_jlcm))
print('Events EFS:', df_jlcm.groupby('group').efs_event.agg(['sum', 'count']).to_dict())
print('Events OS :', df_jlcm.groupby('group').os_event.agg(['sum', 'count']).to_dict())

results = []
# Penalizer = 0.1 (Firth-like ridge regularization) pour eviter HR infini en cas de separation


def fit_cox(df, endpoint, vars_, label, pen=0.1):
    sub = df[vars_ + [f'{endpoint}_days', f'{endpoint}_event']].dropna()
    cph = CoxPHFitter(penalizer=pen)
    cph.fit(sub, duration_col=f'{endpoint}_days', event_col=f'{endpoint}_event')
    c = cph.concordance_index_
    for v in vars_:
        hr = float(np.exp(cph.params_[v]))
        ci_l = float(np.exp(cph.confidence_intervals_.loc[v].iloc[0]))
        ci_u = float(np.exp(cph.confidence_intervals_.loc[v].iloc[1]))
        p = float(cph.summary.loc[v, 'p'])
        results.append({
            'endpoint': endpoint, 'model': label, 'var': v,
            'HR': hr, 'CI_low': ci_l, 'CI_up': ci_u, 'p': p, 'C_index': c, 'n': len(sub)
        })
    print(f'\n--- {endpoint.upper()} | {label} (n={len(sub)}, C={c:.3f}, pen={pen}) ---')
    print(cph.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].round(4))


for ep in ['efs', 'os']:
    fit_cox(df_jlcm, ep, ['jlcm'], 'univarie_JLCM')
    fit_cox(df_jlcm, ep, ['jlcm', 'IPI_HIGH'], 'JLCM+IPI')
    fit_cox(df_jlcm, ep, ['jlcm', 'MTV_BL_log10'], 'JLCM+MTV')
    fit_cox(df_jlcm, ep, ['jlcm', 'LDH_HIGH'], 'JLCM+LDH')
    fit_cox(df_jlcm, ep, ['jlcm', 'ECOG_HIGH'], 'JLCM+ECOG')
    fit_cox(df_jlcm, ep, ['jlcm', 'IPI_HIGH', 'MTV_BL_log10', 'LDH_HIGH', 'ECOG_HIGH'], 'multivarie_complet')

res_df = pd.DataFrame(results)
out_csv = os.path.join(TABLES_DIR, 'cox_multivariate_metrics.csv')
res_df.to_csv(out_csv, index=False)
# Also save as cox_univariate_metrics.csv for backward compatibility
res_df.to_csv(os.path.join(TABLES_DIR, 'cox_univariate_metrics.csv'), index=False)

print('\n=== Summary table (HR JLCM par modele) ===')
sub = res_df[res_df['var'] == 'jlcm'][['endpoint', 'model', 'HR', 'CI_low', 'CI_up', 'p', 'C_index', 'n']]
print(sub.round(3).to_string(index=False))
