#!/usr/bin/env python3
"""
Concordance JLCM-ctDNA vs JLCM-MTV
Tableau croise 2x2 + kappa Cohen + figure heatmap
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import cohen_kappa_score, confusion_matrix

NET = os.path.dirname(OUTPUT_DIR)
DATA_DIR = os.path.join(NET, 'output', 'scripts_figures', 'data')
FIG_DIR  = os.path.join(NET, 'output', 'figures', 'jlcm_pet')
os.makedirs(FIG_DIR, exist_ok=True)

ct  = pd.read_csv(os.path.join(DATA_DIR, 'jlcm_predict_j14.csv'))
mtv = pd.read_csv(os.path.join(DATA_DIR, 'jlcm_mtv_predict_j14.csv'))

ct  = ct.rename(columns={'group':'class_ctdna','p_mauvais':'p_mauvais_ct'})
mtv = mtv.rename(columns={'group':'class_mtv','p_mauvais':'p_mauvais_mtv'})

merged = pd.merge(ct[['randomisation','class_ctdna','p_mauvais_ct']],
                   mtv[['randomisation','class_mtv','p_mauvais_mtv']],
                   on='randomisation', how='inner')
print(f"Merged: {len(merged)} patients")
print(f"ctDNA NA : {merged['class_ctdna'].isna().sum()}")
print(f"MTV   NA : {merged['class_mtv'].isna().sum()}")

# On garde uniquement les patients classifies pour les 2
ok = merged.dropna(subset=['class_ctdna','class_mtv'])
print(f"\n2-marker classified: {len(ok)} patients\n")

# Tableau croise
ct_lvls = ['BON','MAUVAIS']
ok['class_ctdna'] = pd.Categorical(ok['class_ctdna'], categories=ct_lvls)
ok['class_mtv']   = pd.Categorical(ok['class_mtv'],   categories=ct_lvls)
tab = pd.crosstab(ok['class_ctdna'], ok['class_mtv'],
                  rownames=['ctDNA'], colnames=['MTV'],
                  dropna=False)
print("Tableau croise:")
print(tab)
print()

# Cohen kappa
kap = cohen_kappa_score(ok['class_ctdna'], ok['class_mtv'],
                        labels=ct_lvls)
agreement_pct = (ok['class_ctdna']==ok['class_mtv']).mean() * 100

# Sensitivite/specificite (MTV par rapport a ctDNA comme reference)
tn, fp, fn, tp = confusion_matrix(ok['class_ctdna'], ok['class_mtv'],
                                    labels=ct_lvls).ravel()
# tn = BON-BON; fp = BON-MAUVAIS (FAUX positif MTV); fn = MAUVAIS-BON (FAUX negatif MTV); tp = MAUVAIS-MAUVAIS
se_mtv = tp / (tp + fn) if (tp+fn)>0 else float('nan')
sp_mtv = tn / (tn + fp) if (tn+fp)>0 else float('nan')
ppv_mtv = tp / (tp + fp) if (tp+fp)>0 else float('nan')
npv_mtv = tn / (tn + fn) if (tn+fn)>0 else float('nan')

print(f"Cohen kappa  : {kap:.3f}")
print(f"Agreement %  : {agreement_pct:.1f}%")
print(f"Se MTV / ctDNA ref : {se_mtv:.2f}")
print(f"Sp MTV / ctDNA ref : {sp_mtv:.2f}")
print(f"PPV MTV / ctDNA ref: {ppv_mtv:.2f}")
print(f"NPV MTV / ctDNA ref: {npv_mtv:.2f}")

# Sauvegarder tableau + kappa
tab.to_csv(os.path.join(DATA_DIR, 'jlcm_ctdna_mtv_crosstab.csv'))

metrics = pd.DataFrame([
    {'metric':'n','value':len(ok)},
    {'metric':'cohen_kappa','value':kap},
    {'metric':'agreement_pct','value':agreement_pct},
    {'metric':'se_mtv_vs_ctdna','value':se_mtv},
    {'metric':'sp_mtv_vs_ctdna','value':sp_mtv},
    {'metric':'ppv_mtv_vs_ctdna','value':ppv_mtv},
    {'metric':'npv_mtv_vs_ctdna','value':npv_mtv},
])
metrics.to_csv(os.path.join(DATA_DIR, 'jlcm_ctdna_mtv_concordance.csv'), index=False)

# Heatmap figure
fig, ax = plt.subplots(figsize=(7.5, 6), dpi=130)
mat = tab.values.astype(int)
im = ax.imshow(mat, cmap='YlOrRd', aspect='auto', vmin=0, vmax=max(mat.flatten()))
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax.text(j, i, f"{mat[i,j]}", ha='center', va='center',
                fontsize=22, fontweight='bold',
                color='black' if mat[i,j] < mat.max()*0.6 else 'white')
ax.set_xticks([0,1]); ax.set_xticklabels(['BON','MAUVAIS'], fontsize=12)
ax.set_yticks([0,1]); ax.set_yticklabels(['BON','MAUVAIS'], fontsize=12)
ax.set_xlabel('JLCM-MTV class (early PET D14)', fontsize=12, fontweight='bold')
ax.set_ylabel('JLCM-ctDNA class (early ctDNA J14)', fontsize=12, fontweight='bold')
ax.set_title(f'Concordance JLCM-ctDNA vs JLCM-MTV\nALYCANTE (n={len(ok)}) | kappa={kap:.2f} | agreement={agreement_pct:.0f}%',
             fontsize=13, fontweight='bold')
plt.colorbar(im, ax=ax, label='N patients')
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig_concordance_ctdna_mtv.png'),
            dpi=130, bbox_inches='tight', facecolor='white')
plt.close()
print(f"\nFigure sauvee : {os.path.join(FIG_DIR, 'fig_concordance_ctdna_mtv.png')}")

# Sauve merged pour Cox bi-marqueur
long = pd.read_csv(os.path.join(DATA_DIR, 'data_lcmm_long.csv'))
long['randomisation'] = long['randomisation'].astype(str)
ok['randomisation']   = ok['randomisation'].astype(str)
surv = long[['randomisation','efs_time','efs_event','os_time','os_event']].drop_duplicates()
final = pd.merge(ok, surv, on='randomisation', how='left')
final.to_csv(os.path.join(DATA_DIR, 'jlcm_bimarker_alycante.csv'), index=False)
print(f"Sauvegarde bimarker : {os.path.join(DATA_DIR, 'jlcm_bimarker_alycante.csv')}")
print(f"n final = {len(final)} | events EFS = {final['efs_event'].sum()} | events OS = {final['os_event'].sum()}")
