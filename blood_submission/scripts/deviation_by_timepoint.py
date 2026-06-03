# -*- coding: utf-8 -*-
"""
À partir de quel timepoint le modèle JLCM ALYCANTE dévie sur les données Léa ?

Approche : la calibration offset (heg_log_cal = log10(heg_raw) + offset) a été
fitté sur les MEDIANES J0+J14. Si le modèle est cohérent à tous les timepoints,
la déviation [médiane Léa_calibrée - médiane ALYCANTE] devrait rester ~0 à
chaque timepoint. Si elle explose à M3+, c'est le signal que le modèle dévie.

On regarde aussi cette déviation séparément pour low-risk vs high-risk.
"""
import sys, pandas as pd, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAS = Path("//Hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/protocole ALYCANTE/Réunion LYSARC 2026")
IN = NAS / "output" / "blood_article_package" / "input"
TBL = NAS / "output" / "blood_article_package" / "output" / "tables"
FIG = NAS / "output" / "blood_article_package" / "output" / "figures"

# ALYCANTE data + class
aly_long = pd.read_csv(IN / "data_lcmm_long.csv")
aly_pred = pd.read_csv(IN / "jlcm_predict_j14.csv")
aly_long['randomisation'] = aly_long['randomisation'].astype(str)
aly_pred['randomisation'] = aly_pred['randomisation'].astype(str)
aly = aly_long.merge(aly_pred[['randomisation','group']], on='randomisation', how='left')
aly = aly[aly['group'].isin(['BON','MAUVAIS'])].copy()
aly['group_en'] = aly['group'].map({'BON':'low-risk','MAUVAIS':'high-risk'})

# Léa data (calibrated, J0+J14 anchored)
lea_long = pd.read_csv(TBL / "lea_extended_jlcm_input.csv")
lea_pred = pd.read_csv(TBL / "lea_extended_jlcm_predict.csv")
lea_pred['nom_clean'] = lea_pred['nom'].astype(str).str.strip().str.upper()
lea_long['randomisation'] = lea_long['randomisation'].astype(str).str.strip().str.upper()
lea = lea_long.merge(lea_pred[['nom_clean','group_all','group_j14']], left_on='randomisation', right_on='nom_clean', how='left')
# Use group_all for class assignment (extended)
lea['group_en'] = lea['group_all'].map({'BON':'low-risk','MAUVAIS':'high-risk'})

# === 1. Per timepoint, MEDIAN log10(heg) per cohort × class ===
TPS = ['J0','J14','M1','M3','M6','M9','M12']

print("=== Median log10(heg) per timepoint × class ===")
print(f"{'Timepoint':10} {'class':12} {'ALYCANTE (n, med)':>22} {'Léa calibré (n, med)':>26} {'Déviation':>11}")
print("-" * 92)
records = []
for tp in TPS:
    for cls in ['low-risk','high-risk']:
        a = aly[(aly['timepoint']==tp) & (aly['group_en']==cls)]['heg_log']
        l = lea[(lea['timepoint']==tp) & (lea['group_en']==cls)]['heg_log']
        if len(a)==0 or len(l)==0:
            continue
        med_a, med_l = float(a.median()), float(l.median())
        dev = med_l - med_a
        records.append({'tp':tp, 'class':cls, 'n_aly':len(a), 'med_aly':med_a,
                        'n_lea':len(l), 'med_lea':med_l, 'deviation':dev})
        print(f"{tp:10} {cls:12} ({len(a):3d}, {med_a:>+6.2f})              ({len(l):3d}, {med_l:>+6.2f})    {dev:>+8.2f}")

dev_df = pd.DataFrame(records)
print()

# === 2. ALL-class deviation per timepoint (overall median) ===
print("=== Median log10(heg) per timepoint (BOTH classes combined) ===")
print(f"{'Timepoint':10} {'ALYCANTE (n, med)':>22} {'Léa calibré (n, med)':>26} {'Déviation':>11}")
print("-" * 75)
for tp in TPS:
    a = aly[aly['timepoint']==tp]['heg_log']
    l = lea[lea['timepoint']==tp]['heg_log']
    if len(a)==0 or len(l)==0: continue
    print(f"{tp:10} ({len(a):3d}, {a.median():>+6.2f})              ({len(l):3d}, {l.median():>+6.2f})    {l.median()-a.median():>+8.2f}")

# === 3. Visualization ===
COLOR_LOW = "#1f77b4"
COLOR_HIGH = "#d62728"
time_num = {'J0': 0, 'J14': 0.46, 'M1': 1.02, 'M3': 2.99, 'M6': 6.03, 'M9': 9.05, 'M12': 11.99}

fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=False)

# Left panel : median trajectories
ax = axes[0]
for cls, color in [('low-risk', COLOR_LOW), ('high-risk', COLOR_HIGH)]:
    aly_med = []; lea_med = []; xs = []
    for tp in TPS:
        a = aly[(aly['timepoint']==tp) & (aly['group_en']==cls)]['heg_log']
        l = lea[(lea['timepoint']==tp) & (lea['group_en']==cls)]['heg_log']
        if len(a)>0 and len(l)>0:
            aly_med.append(float(a.median())); lea_med.append(float(l.median())); xs.append(time_num[tp])
    ax.plot(xs, aly_med, color=color, lw=3, marker='o', markersize=8, label=f'ALYCANTE {cls}')
    ax.plot(xs, lea_med, color=color, lw=2, marker='s', markersize=8, linestyle='--', alpha=0.7,
            label=f'Léa calibré {cls}')
ax.axhline(0, color='grey', ls=':', lw=0.5)
ax.set_xticks([time_num[t] for t in TPS])
ax.set_xticklabels([{'J0':'D0','J14':'D14'}.get(t,t) for t in TPS])
ax.set_xlabel('Time since CAR-T infusion (months)', fontsize=11)
ax.set_ylabel('Median log10 hEG (per mL plasma)', fontsize=11)
ax.set_title('A. Median trajectories per class — ALYCANTE (training) vs Léa calibré (validation)',
             fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='best', fontsize=10)

# Right panel : deviation per timepoint × class
ax = axes[1]
for cls, color in [('low-risk', COLOR_LOW), ('high-risk', COLOR_HIGH)]:
    sub = dev_df[dev_df['class']==cls].sort_values('tp', key=lambda s: s.map({tp:i for i,tp in enumerate(TPS)}))
    if len(sub)==0: continue
    xs = sub['tp'].map(time_num).values
    ys = sub['deviation'].values
    ax.plot(xs, ys, color=color, lw=3, marker='o', markersize=10, label=f'{cls}')

ax.axhline(0, color='black', ls='-', lw=1.5, alpha=0.7, label='offset calibration target (J0+J14)')
ax.axvspan(time_num['J0']-0.2, time_num['J14']+0.2, alpha=0.15, color='green',
           label='Calibration window (J0+J14)')
ax.set_xticks([time_num[t] for t in TPS])
ax.set_xticklabels([{'J0':'D0','J14':'D14'}.get(t,t) for t in TPS])
ax.set_xlabel('Time since CAR-T infusion (months)', fontsize=11)
ax.set_ylabel('Déviation : Léa median − ALYCANTE median (log10 hEG)', fontsize=11)
ax.set_title('B. Where does the JLCM model start to deviate ?\n'
             '(deviation = Léa − ALYCANTE, calibration anchor = D0+D14)',
             fontsize=11.5, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='best', fontsize=9)
plt.tight_layout()
out = FIG / "Explo_deviation_by_timepoint.png"
fig.savefig(out, dpi=180, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"\nSaved : {out.name}")

# === 4. Quantify the "deviation drift" ===
print("\n=== Drift summary : how much does Léa drift vs ALYCANTE beyond the J0+J14 calibration window ? ===")
for cls in ['low-risk','high-risk']:
    sub = dev_df[dev_df['class']==cls]
    if len(sub)==0: continue
    print(f"\n{cls}:")
    for _, r in sub.iterrows():
        cal_anchor = "← anchor" if r['tp'] in ['J0','J14'] else ""
        print(f"  {r['tp']:5}  deviation = {r['deviation']:+5.2f} log10  (= {10**r['deviation']:.2f}× ratio)  {cal_anchor}")
