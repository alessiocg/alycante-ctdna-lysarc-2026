# -*- coding: utf-8 -*-
"""Plot extended Lea trajectories + KM curves + visual diagnosis."""
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
from lifelines.utils import concordance_index

sys.stdout.reconfigure(encoding='utf-8')

NAS = Path("//Hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/protocole ALYCANTE/Réunion LYSARC 2026")
INPUT_DIR = NAS / "output" / "blood_article_package" / "input"
TBL_DIR = NAS / "output" / "blood_article_package" / "output" / "tables"
FIG_DIR = NAS / "output" / "blood_article_package" / "output" / "figures"

# Data
lea_long = pd.read_csv(TBL_DIR / "lea_extended_jlcm_input.csv")
lea_pred = pd.read_csv(TBL_DIR / "lea_extended_jlcm_predict.csv")
aly_long = pd.read_csv(INPUT_DIR / "data_lcmm_long.csv")
aly_pred = pd.read_csv(INPUT_DIR / "jlcm_predict_j14.csv")

# Merge Lea long with classification
lea_pred['group_use'] = lea_pred['group_all'].fillna(lea_pred['group_j14'])
lea_pred['group_en'] = lea_pred['group_use'].map({'BON':'low-risk','MAUVAIS':'high-risk'})
lea_full = lea_long.merge(lea_pred[['ID','group_en','group_use']], on='ID', how='left')
lea_full_c = lea_full[lea_full['group_en'].isin(['low-risk','high-risk'])].copy()

# ALYCANTE class curves
aly_long['randomisation'] = aly_long['randomisation'].astype(str)
aly_pred['randomisation'] = aly_pred['randomisation'].astype(str)
amerged = aly_long.merge(aly_pred[['randomisation','group']], on='randomisation', how='left')
amerged['group_en'] = amerged['group'].map({'BON':'low-risk','MAUVAIS':'high-risk'})
amerged = amerged[amerged['group_en'].isin(['low-risk','high-risk'])]

timepoints_order = ['J0','J14','M1','M3','M6','M9','M12']
time_num = {'J0': 0, 'J14': 0.46, 'M1': 1.02, 'M3': 2.99, 'M6': 6.03, 'M9': 9.05, 'M12': 11.99}

aly_curves = {}
for grp in ['low-risk','high-risk']:
    sub = amerged[amerged['group_en']==grp]
    agg = sub.groupby('timepoint')['heg_log'].agg(['mean','sem']).reset_index()
    agg = agg.set_index('timepoint').reindex(timepoints_order).reset_index()
    agg['t'] = agg['timepoint'].map(time_num)
    aly_curves[grp] = agg.dropna()

# === Plot 1: trajectories ===
COLOR_LOW = "#1f77b4"
COLOR_HIGH = "#d62728"
fig, ax = plt.subplots(figsize=(13, 7))
for grp, color in [('low-risk', COLOR_LOW), ('high-risk', COLOR_HIGH)]:
    a = aly_curves[grp]
    ax.plot(a['t'], a['mean'], color=color, lw=3.5, label=f'ALYCANTE {grp} (mean ± SEM)', zorder=3)
    ax.fill_between(a['t'], a['mean']-a['sem'], a['mean']+a['sem'], color=color, alpha=0.18, zorder=2)

# Lea patients trajectories (extended)
for pat_id in lea_full_c['ID'].unique():
    sub = lea_full_c[lea_full_c['ID']==pat_id].sort_values('time')
    if len(sub) == 0: continue
    grp = sub['group_en'].iloc[0]
    color = COLOR_LOW if grp == 'low-risk' else COLOR_HIGH
    ax.plot(sub['time'], sub['heg_log'], color=color, lw=0.8, alpha=0.55,
            marker='o', markersize=4, zorder=4)

ax.axhline(0, color='grey', ls=':', lw=0.7)
ax.set_xlabel('Time since CAR-T infusion (months)', fontsize=12)
ax.set_ylabel('log10 hEG (per mL plasma, calibration-offset corrected)', fontsize=12)
ax.set_title(f'Extended Henri-Mondor cohort (n={lea_full_c["ID"].nunique()} classifiable, all timepoints D0→M12)\n'
             f'observed trajectories overlaid on ALYCANTE-trained JLCM class trajectories (predictClass using full available data)',
             fontsize=11.5, fontweight='bold')
ax.set_xticks([time_num[t] for t in timepoints_order])
ax.set_xticklabels([{'J0':'D0','J14':'D14'}.get(t,t) for t in timepoints_order])
ax.grid(True, alpha=0.3)
ax.legend(loc='best', fontsize=10, frameon=True)
plt.tight_layout()
out1 = FIG_DIR / "Explo_lea_extended_trajectories.png"
fig.savefig(out1, dpi=180, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"Saved: {out1.name}")

# === Plot 2: KM curves with extended classification ===
classified = lea_pred[lea_pred['group_all'].isin(['BON','MAUVAIS'])].copy()
classified['risk'] = (classified['group_all']=='MAUVAIS').astype(int)

# EFS Cox + KM
df_efs = classified[['efs_time','efs_event','risk']].dropna().rename(columns={'efs_time':'T','efs_event':'E'})
df_efs = df_efs[df_efs['T']>0]
cph = CoxPHFitter(penalizer=0.1)
cph.fit(df_efs, 'T', 'E')
hr_efs = float(np.exp(cph.params_.iloc[0]))
ci_lo, ci_hi = (float(np.exp(x)) for x in cph.confidence_intervals_.iloc[0])
c_efs = concordance_index(classified['efs_time'], -classified['risk'], classified['efs_event'])
print(f"\nExtended cohort EFS: HR={hr_efs:.2f} ({ci_lo:.2f}-{ci_hi:.2f}), C-index={c_efs:.3f}")
print(f"  n_total={len(classified)}, n_events={int(classified['efs_event'].sum())}")
print(classified.groupby('group_all').agg(n=('ID','count'), events=('efs_event','sum')))

# Plot KM
fig, ax = plt.subplots(figsize=(10, 5.5))
kmf = KaplanMeierFitter()
for grp_label, grp_col, color in [('low-risk (BON)','BON',COLOR_LOW),('high-risk (MAUVAIS)','MAUVAIS',COLOR_HIGH)]:
    sub = classified[classified['group_all']==grp_col]
    if len(sub) == 0: continue
    n_ev = int(sub['efs_event'].sum())
    kmf.fit(sub['efs_time'], sub['efs_event'], label=f'{grp_label} (n={len(sub)}, events={n_ev})')
    kmf.plot_survival_function(ax=ax, ci_show=True, color=color, lw=2.2)

lr = logrank_test(classified[classified['group_all']=='BON']['efs_time'],
                  classified[classified['group_all']=='MAUVAIS']['efs_time'],
                  classified[classified['group_all']=='BON']['efs_event'],
                  classified[classified['group_all']=='MAUVAIS']['efs_event'])
p_str = "< 0.001" if lr.p_value < 0.001 else f"{lr.p_value:.3f}"
ax.axvline(12, ls="--", color="gray", lw=0.8, alpha=0.5); ax.text(12, 1.02, "12mo", fontsize=8, color="gray", ha="center")
ax.axvline(24, ls="--", color="gray", lw=0.8, alpha=0.5); ax.text(24, 1.02, "24mo", fontsize=8, color="gray", ha="center")
ax.set_title(f"Extended Henri-Mondor cohort (n={len(classified)}, predictClass on ALL available timepoints)\n"
             f"HR EFS = {hr_efs:.2f} ({ci_lo:.2f}-{ci_hi:.2f}); C-index = {c_efs:.2f}; log-rank P {p_str}",
             fontsize=11.5, fontweight='bold')
ax.set_xlabel('Time since CAR-T infusion (months)', fontsize=11)
ax.set_ylabel('EFS probability', fontsize=11)
ax.set_xlim(0, max(40, classified['efs_time'].max()))
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.3)
ax.legend(loc='lower left', fontsize=10, frameon=True)
plt.tight_layout()
out2 = FIG_DIR / "Explo_lea_extended_KM_EFS.png"
fig.savefig(out2, dpi=180, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"Saved: {out2.name}")

# Print survival summary by group
print("\n=== KM EFS estimates ===")
for grp_col, grp_label in [('BON','low-risk'),('MAUVAIS','high-risk')]:
    sub = classified[classified['group_all']==grp_col]
    if len(sub) == 0: continue
    kmf2 = KaplanMeierFitter()
    kmf2.fit(sub['efs_time'], sub['efs_event'])
    for t in [6, 12, 24]:
        sf = kmf2.survival_function_
        idx = sf.index[sf.index<=t]
        if len(idx) > 0:
            s = float(sf.loc[idx[-1]].iloc[0]) * 100
            print(f"  {grp_label} {t:>2}mo EFS = {s:>5.1f}% (n={len(sub)})")
