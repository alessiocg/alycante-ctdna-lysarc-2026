"""
Forest plot Cox multivarie v2 : JLCM + IPI >=3 + MTV baseline log10 (sans LDH/ECOG).
Trois covariables sur EFS et OS. Met en evidence l independance de JLCM ctDNA J14
apres ajustement sur seuls predicteurs cliniques NON redondants avec l'IPI.
"""
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

plt.rcParams.update({
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'font.family': 'DejaVu Sans', 'font.size': 9, 'savefig.facecolor': 'white',
})

CSV = os.path.join(INPUT_DIR, "cox_multivariate_v2_metrics.csv")
res = pd.read_csv(CSV)
final = res[res.model == 'multivarie_v2'].copy()

# Trois covariables, ordre fixe
var_order = ['jlcm', 'IPI_HIGH', 'MTV_BL_log10']
labels = {
    'jlcm': 'JLCM ctDNA D14\n(high-risk vs low-risk)',
    'IPI_HIGH': 'IPI >= 3 vs < 3',
    'MTV_BL_log10': 'log10(MTV baseline)\n(per unit)',
}

fig, axes = plt.subplots(1, 2, figsize=(13, 5.0), constrained_layout=True)

for ax, ep, title in zip(axes, ['efs', 'os'], ['Event-free survival', 'Overall survival']):
    sub = final[final.endpoint == ep].set_index('var').loc[var_order].reset_index()
    ypos = np.arange(len(sub))[::-1]
    cidx = sub.C_index.iloc[0]
    nn = int(sub.n.iloc[0])
    for i, row in sub.iterrows():
        y = ypos[i]
        hr, lo, hi, p = row.HR, row.CI_low, row.CI_up, row.p
        color = '#d62728' if row['var'] == 'jlcm' else '#1f77b4'
        marker = 's' if row['var'] == 'jlcm' else 'o'
        # Borne le CI affiche
        hi_disp = min(hi, 80)
        ax.plot([max(lo, 0.05), hi_disp], [y, y], color=color, lw=2.4)
        ax.plot(hr, y, marker=marker, color=color, markersize=11, zorder=5,
                markeredgecolor='black', markeredgewidth=0.6)
        pstr = '<0.0001' if p < 0.0001 else f'={p:.3f}'
        ax.text(110, y, f'HR={hr:.2f} [{lo:.2f}-{hi:.2f}]  p{pstr}',
                va='center', fontsize=9.5)
    ax.set_yticks(ypos)
    ax.set_yticklabels([labels[v] for v in sub['var']], fontsize=10)
    ax.axvline(1, color='gray', ls='--', lw=1.1)
    ax.set_xscale('log')
    ax.set_xlim(0.3, 80)
    ax.set_xlabel('Adjusted hazard ratio (95% CI)', fontsize=10)
    ax.set_title(f'{title} — C-index = {cidx:.3f} (n={nn})', fontsize=11, weight='bold')
    ax.grid(axis='x', alpha=0.3, which='both')

plt.suptitle(
    'Cox multivariable v2 : JLCM ctDNA day-14 class remains independent of IPI and baseline MTV\n'
    '(LDH and ECOG omitted because they are IPI components)',
    fontsize=11.5, weight='bold', y=1.06,
)

NAS_BASE = os.path.dirname(OUTPUT_DIR)
out_png = os.path.join(NAS_BASE, 'output', 'figures', 'clinical', 'fig_forest_multivariate_v2.png')
os.makedirs(os.path.dirname(out_png), exist_ok=True)
plt.savefig(out_png, dpi=160, bbox_inches='tight')
plt.savefig(os.path.join(FIGURES_DIR, "fig_forest_multivariate_v2.png"), dpi=160, bbox_inches='tight')
print('Saved:', out_png)
