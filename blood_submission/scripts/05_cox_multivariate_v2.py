"""
Cox multivarie v2 ALYCANTE — JLCM + IPI cat + MTV baseline log10 SANS LDH / ECOG.
Rationale : LDH eleve et ECOG >=2 sont composantes de l'IPI (avec age >60,
stade Ann Arbor III-IV, sites extranodaux >1). Inclure les 3 ensemble cree
une redondance qui dilue l'effet IPI et inflate les CI.
Modele final :
    coxph(Surv(efs_days, efs_event) ~ jlcm + IPI_HIGH + MTV_BL_log10)
    coxph(Surv(os_days,  os_event)  ~ jlcm + IPI_HIGH + MTV_BL_log10)
IPI_HIGH : 0 si IPI <3, 1 si IPI >=3 (definition ALYCANTE)
MTV_BL_log10 : log10(MTV_baseline) continu
penalizer=0.1 (Firth-like) pour gerer la separation parfaite cote MAUVAIS (22/22 events).
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd

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

_legacy_master = os.path.join(INPUT_DIR, "master_dataset.csv")
INPUT = _legacy_master if os.path.exists(_legacy_master) else os.path.join(INPUT_DIR, 'master_dataset.csv')
OUT_CSV_PKG = os.path.join(TABLES_DIR, 'cox_multivariate_v2_metrics.csv')
# Legacy paths (kept for backward compat with the NAS pipeline if BLOOD_NAS_ROOT set)
_nas = os.environ.get("BLOOD_NAS_ROOT", "")
OUT_CSV_NAS = os.path.join(_nas, 'output', 'scripts_figures', 'data', 'cox_multivariate_v2_metrics.csv') if _nas else None
OUT_CSV_LOCAL = os.path.join(INPUT_DIR, "cox_multivariate_v2_metrics.csv")

df = pd.read_csv(INPUT)
df['jlcm'] = (df.group == 'MAUVAIS').astype(int)
df_jlcm = df[df.group.isin(['BON', 'MAUVAIS'])].copy()
df_jlcm = df_jlcm.dropna(subset=['MTV_BL_log10', 'IPI'])
print(f'Apres dropna covariables (IPI, MTV) : n={len(df_jlcm)}')
print('Events EFS :', df_jlcm.groupby('group').efs_event.agg(['sum', 'count']).to_dict())
print('Events OS  :', df_jlcm.groupby('group').os_event.agg(['sum', 'count']).to_dict())

results = []


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
            'HR': hr, 'CI_low': ci_l, 'CI_up': ci_u, 'p': p,
            'C_index': c, 'n': len(sub)
        })
    print(f'\n--- {endpoint.upper()} | {label} (n={len(sub)}, C={c:.3f}, pen={pen}) ---')
    print(cph.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].round(4))


for ep in ['efs', 'os']:
    fit_cox(df_jlcm, ep, ['jlcm'], 'univarie_JLCM')
    fit_cox(df_jlcm, ep, ['jlcm', 'IPI_HIGH'], 'JLCM+IPI')
    fit_cox(df_jlcm, ep, ['jlcm', 'MTV_BL_log10'], 'JLCM+MTV')
    fit_cox(df_jlcm, ep, ['jlcm', 'IPI_HIGH', 'MTV_BL_log10'], 'multivarie_v2')

res_df = pd.DataFrame(results)
res_df.to_csv(OUT_CSV_PKG, index=False)
print('\nSaved :', OUT_CSV_PKG)
# Legacy best-effort copies
for _p in (OUT_CSV_LOCAL, OUT_CSV_NAS):
    try:
        res_df.to_csv(_p, index=False)
    except Exception:
        pass

print('\n=== Summary HR JLCM par modele ===')
sub = res_df[res_df['var'] == 'jlcm'][['endpoint', 'model', 'HR', 'CI_low', 'CI_up', 'p', 'C_index', 'n']]
print(sub.round(3).to_string(index=False))

print('\n=== Modele final v2 : JLCM + IPI_HIGH + MTV_BL_log10 ===')
final = res_df[res_df['model'] == 'multivarie_v2'][['endpoint', 'var', 'HR', 'CI_low', 'CI_up', 'p', 'C_index', 'n']]
print(final.round(3).to_string(index=False))
