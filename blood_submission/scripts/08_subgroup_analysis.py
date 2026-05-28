"""
Subgroup forest plot : HR JLCM-ctDNA stratifie par covariables cliniques.
Endpoint EFS (le plus discriminant).
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
from lifelines import CoxPHFitter

plt.rcParams.update({'figure.facecolor': 'white', 'axes.facecolor': 'white',
                     'font.family': 'DejaVu Sans', 'font.size': 9, 'savefig.facecolor': 'white'})

# === Path resolution (added for package portability) ===
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _paths import INPUT_DIR, TABLES_DIR, FIGURES_DIR
except Exception:
    _here = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(_here, '..', 'input')
    TABLES_DIR = os.path.join(_here, '..', 'output', 'tables')
    FIGURES_DIR = os.path.join(_here, '..', 'output', 'figures')
    os.makedirs(TABLES_DIR, exist_ok=True); os.makedirs(FIGURES_DIR, exist_ok=True)

_legacy_master = os.path.join(INPUT_DIR, "master_dataset.csv")
df = pd.read_csv(_legacy_master if os.path.exists(_legacy_master) else os.path.join(INPUT_DIR, 'master_dataset.csv'))
df['jlcm'] = (df.group == 'MAUVAIS').astype(int)
df_jlcm = df[df.group.isin(['BON', 'MAUVAIS'])].copy()

# Mediane MTV pour stratification
mtv_med = df_jlcm.MTV_BL.median()


def cox_hr(sub, ep='efs', pen=0.15):
    sub = sub.dropna(subset=['jlcm', f'{ep}_days', f'{ep}_event'])
    if (sub.jlcm == 0).sum() < 2 or (sub.jlcm == 1).sum() < 2:
        return np.nan, np.nan, np.nan, np.nan, len(sub)
    try:
        cph = CoxPHFitter(penalizer=pen)
        cph.fit(sub[['jlcm', f'{ep}_days', f'{ep}_event']], duration_col=f'{ep}_days', event_col=f'{ep}_event')
        hr = float(np.exp(cph.params_['jlcm']))
        lo = float(np.exp(cph.confidence_intervals_.loc['jlcm'].iloc[0]))
        hi = float(np.exp(cph.confidence_intervals_.loc['jlcm'].iloc[1]))
        p = float(cph.summary.loc['jlcm', 'p'])
        return hr, lo, hi, p, len(sub)
    except Exception:
        return np.nan, np.nan, np.nan, np.nan, len(sub)


subgroups = [
    ('Toute la cohorte', df_jlcm),
    ('IPI < 3', df_jlcm[df_jlcm.IPI_HIGH == 0]),
    ('IPI >= 3', df_jlcm[df_jlcm.IPI_HIGH == 1]),
    ('MTV < mediane', df_jlcm[df_jlcm.MTV_BL < mtv_med]),
    ('MTV >= mediane', df_jlcm[df_jlcm.MTV_BL >= mtv_med]),
    ('ECOG 0-1', df_jlcm[df_jlcm.ECOG_HIGH == 0]),
    ('ECOG >= 2', df_jlcm[df_jlcm.ECOG_HIGH == 1]),
    ('Bridging Yes', df_jlcm[df_jlcm.bridge_yes == 1]),
    ('Bridging No', df_jlcm[df_jlcm.bridge_yes == 0]),
    ('Age < 65', df_jlcm[df_jlcm.AGE_65 == 0]),
    ('Age >= 65', df_jlcm[df_jlcm.AGE_65 == 1]),
    ('Sexe Masculin', df_jlcm[df_jlcm.SEX_M == 1]),
    ('Sexe Feminin', df_jlcm[df_jlcm.SEX_M == 0]),
    ('LDH normal', df_jlcm[df_jlcm.LDH_HIGH == 0]),
    ('LDH > ULN', df_jlcm[df_jlcm.LDH_HIGH == 1]),
]

rows = []
for name, sub in subgroups:
    for ep in ['efs', 'os']:
        hr, lo, hi, p, n = cox_hr(sub, ep)
        rows.append({'subgroup': name, 'endpoint': ep, 'HR': hr, 'CI_low': lo, 'CI_up': hi, 'p': p, 'n': n})

res = pd.DataFrame(rows)
out_csv = os.path.join(TABLES_DIR, 'subgroup_metrics.csv')
res.to_csv(out_csv, index=False)
# Legacy best-effort
try:
    res.to_csv(os.path.dirname(OUTPUT_DIR), index=False)
except Exception:
    pass
print(res.round(3).to_string(index=False))

# Forest plot — EFS et OS
fig, axes = plt.subplots(1, 2, figsize=(14, 8), constrained_layout=True)
for ax, ep, title in zip(axes, ['efs', 'os'], ['EFS', 'OS']):
    sub = res[res.endpoint == ep].reset_index(drop=True)
    ypos = np.arange(len(sub))[::-1]
    for i, row in sub.iterrows():
        if pd.isna(row.HR):
            continue
        y = ypos[i]
        color = 'k' if row.subgroup == 'Toute la cohorte' else '#1f77b4'
        marker = 'D' if row.subgroup == 'Toute la cohorte' else 's'
        # Clip CI very large
        lo = max(row.CI_low, 0.1)
        hi = min(row.CI_up, 1000)
        ax.plot([lo, hi], [y, y], color=color, lw=1.5)
        ax.plot(row.HR, y, marker=marker, color=color, markersize=8, zorder=5)
        ax.text(1500, y, f'HR={row.HR:.2f} [{row.CI_low:.1f}-{row.CI_up:.0f}] n={row.n}', va='center', fontsize=8)
    ax.set_yticks(ypos)
    ax.set_yticklabels(sub.subgroup, fontsize=9)
    ax.axvline(1, color='gray', ls='--', lw=1)
    ax.set_xscale('log')
    ax.set_xlim(0.1, 2000)
    ax.set_xlabel(f'HR ajustee MAUVAIS vs BON ({title})')
    ax.set_title(f'{title} par sous-groupe (penalizer Firth-like = 0.15)', fontsize=10)
    ax.grid(axis='x', alpha=0.3)

plt.suptitle('Analyse en sous-groupes — JLCM-ctDNA J14 dans toute strate clinique', fontsize=11, weight='bold')
out_png = os.path.join(FIGURES_DIR, 'fig_subgroup_forest.png')
plt.savefig(out_png, dpi=130, bbox_inches='tight')
# Legacy best-effort
for _p in (
    os.path.dirname(OUTPUT_DIR),
    os.path.join(FIGURES_DIR, "fig_subgroup_forest.png"),
):
    try:
        os.makedirs(os.path.dirname(_p), exist_ok=True)
        plt.savefig(_p, dpi=130, bbox_inches='tight')
    except Exception:
        pass
print('\nSaved:', out_png)
