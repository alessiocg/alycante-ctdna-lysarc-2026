"""
Figures de synthese ALYCANTE v3 - corrigees (taille raisonnable)
- Fig 1 : Forest plot HR ctDNA (corrigee)
- Fig 2 : Timeline etudes 2015-2026
- Fig 3 : Sensibilite analytique des methodes
- Fig 4 : ctDNA-MRD vs PET-CMR
- Fig 5 : Protocole ALYCANTE schematique (timeline visits)
- Fig 6 : KM ALYCANTE vs Lea (deja dans figures_cohorte, reutiliser)
"""
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrow

OUT_DIR = r"C:\Users\4067048\AppData\Local\Temp\alycante_lit\figures_v3"
os.makedirs(OUT_DIR, exist_ok=True)

# =========================================================
# FIGURE 1 : Forest plot HR ctDNA - CORRIGE
# =========================================================
forest_data = [
    ('A', 'Baseline ctDNA - Kurtz 2018 [5]', 217, 2.6, 1.6, 4.2, 'EFS'),
    ('B', 'Baseline ctDNA - Alig 2021 [21]', 267, 1.5, 1.2, 2.0, 'EFS'),
    ('C', 'Baseline ctDNA - Le Goff 2023 [50]', 112, 3.8, 2.0, 7.2, 'PFS'),
    ('D', 'Baseline ctDNA - Li 2022 [38]', 73, 2.47, 1.34, 4.56, 'PFS'),
    ('E', 'Baseline ctDNA - Moia 2025 [68]', 166, 2.1, 1.3, 3.4, 'PFS'),
    ('F', 'EMR (apres C1) - Kurtz 2018 [5]', 217, 3.1, 1.8, 5.4, 'EFS'),
    ('G', 'MMR (apres C2) - Kurtz 2018 [5]', 217, 3.4, 2.0, 5.8, 'EFS'),
    ('H', 'ctDNA clearance C1 - Narkhede 2024 [65]', 50, 6.5, 1.9, 22.0, 'EFS'),
    ('I', 'MMR C2 - Alcoceba 2024 [62]', 68, 8.2, 2.5, 27.0, 'PFS'),
    ('J', 'Interim ctDNA (C2) - Roschewski 2015 [2]', 108, 4.3, 2.0, 9.4, 'TTP'),
    ('K', 'EoT ctDNA detect. - Roschewski 2025 [75]', 137, 28.7, 6.8, 121.0, 'PFS'),
    ('L', 'EoT PET positif - Roschewski 2025 [75]', 137, 3.6, 1.5, 8.4, 'PFS'),
    ('M', 'ctDNA J7 detect post-axi-cel - Frank 2021 [25]', 72, 6.0, 2.5, 14.5, 'PFS'),
    ('N', 'ctDNA J28 detect post-axi-cel - Frank 2021 [25]', 72, 14.0, 5.0, 39.0, 'PFS'),
    ('O', 'ctDNA J43 detect post-liso-cel - Stepan 2026 [90]', 136, 4.2, 2.1, 8.5, 'EFS'),
    ('P', 'Meta DLBCL pooled - Yao 2021 [23]', 379, 2.01, 1.42, 2.85, 'PFS'),
    ('Q', 'Meta Hodgkin baseline - Shahsavand 2026 [110]', 1158, 2.74, 1.30, 5.75, 'PFS'),
    ('R', 'Meta Hodgkin EoT - Shahsavand 2026 [110]', 1158, 13.4, 3.97, 41.87, 'PFS'),
]

# Use GridSpec to have left labels column + plot column - avoids ax.text negative coords
fig, axes = plt.subplots(1, 2, figsize=(13, 10), gridspec_kw={'width_ratios': [3.5, 6.5], 'wspace': 0.02})
ax_labels, ax_plot = axes

y_pos = np.arange(len(forest_data))[::-1]

colors = {
    'A': '#1f77b4', 'B': '#1f77b4', 'C': '#1f77b4', 'D': '#1f77b4', 'E': '#1f77b4',
    'F': '#ff7f0e', 'G': '#ff7f0e', 'H': '#ff7f0e', 'I': '#ff7f0e',
    'J': '#2ca02c', 'K': '#2ca02c', 'L': '#d62728',
    'M': '#9467bd', 'N': '#9467bd', 'O': '#9467bd',
    'P': '#7f7f7f', 'Q': '#7f7f7f', 'R': '#7f7f7f',
}

# Left ax: labels only
ax_labels.set_xlim(0, 1)
ax_labels.set_ylim(-0.5, len(forest_data) - 0.5)
ax_labels.axis('off')
for i, (key, label, n, hr, lcl, ucl, outcome) in enumerate(forest_data):
    y = y_pos[i]
    ax_labels.text(0.98, y, label, ha='right', va='center', fontsize=9)

# Right ax: plot + HR values
ax = ax_plot
for i, (key, label, n, hr, lcl, ucl, outcome) in enumerate(forest_data):
    y = y_pos[i]
    color = colors[key]
    ax.plot([lcl, ucl], [y, y], color=color, lw=2, zorder=2)
    size = 60 + 8 * np.log10(n)
    ax.scatter([hr], [y], s=size, color=color, edgecolor='black', linewidth=0.8, zorder=3)
    # Right text: HR + CI + outcome inside the axes (positive x in log scale)
    txt_x = 280  # all positions on log scale will be valid
    ax.text(txt_x, y, f"N={n}, HR={hr:.2f} [{lcl:.2f}-{ucl:.2f}], {outcome}",
            ha='left', va='center', fontsize=8, color='#333')

ax.axvline(x=1, color='red', linestyle='--', lw=1, alpha=0.6, zorder=1)
ax.text(1, len(forest_data) - 0.3, 'HR=1', color='red', fontsize=9, ha='center')

# Shading par categorie
ax.axhspan(len(forest_data) - 5.5, len(forest_data) - 0.5, color='#e6f0fa', alpha=0.4, zorder=0)
ax.axhspan(len(forest_data) - 9.5, len(forest_data) - 5.5, color='#fff0e0', alpha=0.4, zorder=0)
ax.axhspan(len(forest_data) - 12.5, len(forest_data) - 9.5, color='#e0f0e0', alpha=0.4, zorder=0)
ax.axhspan(len(forest_data) - 15.5, len(forest_data) - 12.5, color='#f0e0f0', alpha=0.4, zorder=0)
ax.axhspan(-0.5, len(forest_data) - 15.5, color='#eeeeee', alpha=0.4, zorder=0)

cat_labels = [
    ('Baseline ctDNA', len(forest_data) - 3),
    ('Reponse moleculaire (C1-C2)', len(forest_data) - 7.5),
    ('Fin de traitement (EoT)', len(forest_data) - 10.5),
    ('Post-CAR-T', len(forest_data) - 13.5),
    ('Meta-analyses', 1),
]
for lab, ypos in cat_labels:
    ax.text(1.4, ypos, lab, ha='left', va='center', fontsize=9,
            fontweight='bold', color='#222', style='italic',
            bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.3', alpha=0.85))

ax.set_xscale('log')
ax.set_xlim(0.5, 2000)  # large enough to fit text labels
ax.set_xticks([0.5, 1, 2, 5, 10, 30, 100])
ax.set_xticklabels(['0.5', '1', '2', '5', '10', '30', '100'])
ax.set_xlabel('Hazard Ratio (echelle logarithmique)', fontsize=11)
ax.set_yticks([])
ax.set_ylim(-0.5, len(forest_data) - 0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)

fig.suptitle('Figure 1. Forest plot - Valeur pronostique du ctDNA dans les lymphomes B agressifs\n(18 estimations issues de 13 etudes publiees 2015-2026)',
             fontsize=12, fontweight='bold', y=0.99)

fig.text(0.5, 0.01,
         'Notes : Taille du marqueur proportionnelle a log(N). Reference (PET EoT) en rouge pour comparaison avec ctDNA EoT (vert).\n'
         'HR brutes (univariees) extraites des publications.',
         ha='center', fontsize=8, color='#555', style='italic')

plt.savefig(os.path.join(OUT_DIR, 'fig1_forest_plot_HR_ctDNA.png'), dpi=120, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("Fig 1 saved")

# =========================================================
# FIGURE 2 : Timeline 2015-2026 (deja OK)
# =========================================================
timeline_data = [
    (2015, 'Roschewski', 'IgH-NGS surveillance ctDNA\n5-year TTP 41% vs 80% [2]', 'top', '#1f77b4'),
    (2016, 'Scherer (CAPP-Seq)', 'Sous-types DLBCL sur ctDNA\nGenotypage non invasif [3]', 'bottom', '#ff7f0e'),
    (2018, 'Kurtz (EMR/MMR)', 'Seuils 2-log/2.5-log\nIndependant IPI/PET [5]', 'top', '#1f77b4'),
    (2019, 'Kurtz (CIRI)', 'Prediction dynamique\nctDNA+IPI+PET integres [11]', 'bottom', '#1f77b4'),
    (2021, 'Frank (post-axi-cel)', 'ctDNA J7/J28 predit progression\navant PET [25]', 'top', '#9467bd'),
    (2021, 'Kurtz (PhasED-Seq)', 'Sensibilite 1 ppm\n+25% MRD vs CAPP-Seq [26]', 'bottom', '#ff7f0e'),
    (2021, 'Locke (ZUMA-7)', 'Axi-cel 2L > SOC\nEFS 8.3 vs 2 m [18]', 'top', '#9467bd'),
    (2022, 'Dickinson (glofitamab)', 'Bispecifique CD20xCD3\nCR 39% [94]', 'bottom', '#d62728'),
    (2023, 'Houot (ALYCANTE)', 'Axi-cel 2L non-eligible ASCT\nCMR M3 71% [45]', 'top', '#9467bd'),
    (2024, 'Locke (ZUMA-7 MTV)', 'MTV haut predit EFS\net toxicite [59]', 'bottom', '#9467bd'),
    (2024, 'Alcoceba', 'MMR + DeltaSUV PET\n3 strates [62]', 'top', '#ff7f0e'),
    (2025, 'Roschewski (LBCL)', 'EoT ctDNA HR=28.7\nvs PET HR=3.6 [75]', 'bottom', '#1f77b4'),
    (2025, 'Cartron (LYSA-glofit)', 'Glofitamab post-CAR-T\nOS 14.7 mois [97]', 'top', '#d62728'),
    (2026, 'Stepan (TRANSFORM)', 'Liso-cel vs ASCT 2L\nMRD ctDNA > PET [90]', 'bottom', '#9467bd'),
    (2026, 'Charton (ALYCANTE QoL)', 'QoL recuperee a 3 mois\nmieux que ZUMA-7 [86]', 'top', '#9467bd'),
]

fig, ax = plt.subplots(figsize=(14, 7.5))
years_x = list(range(2014, 2027))
ax.plot([min(years_x), max(years_x)], [0, 0], color='#333', lw=2, zorder=2)
for y in years_x:
    ax.plot([y, y], [-0.05, 0.05], color='#333', lw=1, zorder=2)
    ax.text(y, -0.15, str(y), ha='center', va='top', fontsize=10, fontweight='bold')

# Stagger same-year items
year_offset = {}
for year, study, desc, position, color in timeline_data:
    key = (year, position)
    year_offset[key] = year_offset.get(key, 0) + 1

stagger_count = {}
for year, study, desc, position, color in timeline_data:
    y_offset = 1.0 if position == 'top' else -1.0
    key = (year, position)
    stagger_count[key] = stagger_count.get(key, 0) + 1
    same_year_n = year_offset[key]
    rank = stagger_count[key]
    # Stagger horizontally if multiple
    x_off = (rank - (same_year_n + 1) / 2) * 0.0  # no horizontal stagger
    y_stagger = (rank - 1) * (0.35 if position == 'top' else -0.35)

    ax.scatter([year], [0], s=80, color=color, edgecolor='black', linewidth=1.2, zorder=3)
    ax.plot([year, year], [0, y_offset * 0.18], color=color, lw=1.2, zorder=2)

    text = f"{year} - {study}\n{desc}"
    ax.annotate(
        text,
        xy=(year, y_offset * 0.18),
        xytext=(year, y_offset * (0.55 + abs(y_stagger))),
        ha='center',
        va='center',
        fontsize=8,
        arrowprops=dict(arrowstyle='-', color=color, lw=1.0),
        bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor=color, lw=1.0)
    )

legend_items = [
    ('Methodes ctDNA', '#ff7f0e'),
    ('ctDNA pronostic', '#1f77b4'),
    ('Essais CAR-T', '#9467bd'),
    ('Bispecifiques', '#d62728'),
]
legend_handles = [Line2D([0], [0], marker='o', color='w', label=lab, markerfacecolor=col, markersize=10, markeredgecolor='black') for lab, col in legend_items]
ax.legend(handles=legend_handles, loc='lower right', fontsize=9, frameon=True, title='Categorie')

ax.set_xlim(2013.5, 2026.5)
ax.set_ylim(-1.4, 1.4)
ax.set_yticks([])
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(False)
ax.set_title('Figure 2. Timeline des etudes pivot ctDNA / CAR-T / bispecifiques dans le DLBCL (2015-2026)',
             fontsize=12, fontweight='bold', loc='left', pad=12)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'fig2_timeline_etudes.png'), dpi=120, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("Fig 2 saved")

# =========================================================
# FIGURE 3 : Sensibilite (deja OK, regenerer)
# =========================================================
methods_data = [
    ('PET-CT (Lugano)', 1e-1, '~10^-1', 'Imagerie volumique >5mm', '#888888'),
    ('CT scan', 1e0, '~1', 'Volume macroscopique', '#aaaaaa'),
    ('ddPCR (mutation single)', 1e-3, '~10^-3', 'Une mutation specifique', '#ffd166'),
    ('Flow cytometry MRD', 1e-4, '~10^-4', 'Phenotype B residuel', '#06d6a0'),
    ('CAPP-Seq', 1e-5, '~10^-5', 'Multi-mutations + UMI', '#118ab2'),
    ('IgH-NGS clonotype', 1e-6, '~10^-6', 'Clonotype VDJ unique', '#073b4c'),
    ('PhasED-Seq', 7e-7, '~7e10^-7', 'Variants phases co-lies', '#ef476f'),
]

fig, ax = plt.subplots(figsize=(12, 6.5))
y_methods = list(range(len(methods_data)))[::-1]

for i, (name, lod, lod_label, descr, color) in enumerate(methods_data):
    y = y_methods[i]
    ax.scatter([lod], [y], s=250, color=color, edgecolor='black', linewidth=1.5, zorder=3, marker='o')
    ax.text(3e0, y, name, ha='left', va='center', fontsize=11, fontweight='bold')
    ax.text(1e0, y - 0.1, descr, ha='left', va='top', fontsize=8.5, color='#444', style='italic')
    ax.text(lod, y + 0.25, lod_label, ha='center', va='bottom', fontsize=9, color=color, fontweight='bold')

ax.axvline(x=1e-4, color='gray', linestyle=':', lw=0.8, alpha=0.7)
ax.text(1e-4, len(methods_data) - 0.5, 'Seuil MRD classique', ha='center', va='bottom', fontsize=8, color='gray')
ax.axvline(x=1e-6, color='gray', linestyle=':', lw=0.8, alpha=0.7)
ax.text(1e-6, len(methods_data) - 0.5, 'Seuil ultra-sensible (ppm)', ha='center', va='bottom', fontsize=8, color='gray')

ax.set_xscale('log')
ax.set_xlim(2e-7, 1e2)
ax.invert_xaxis()
ax.set_xticks([1e0, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7])
ax.set_xticklabels([r'$10^{0}$', r'$10^{-1}$', r'$10^{-2}$', r'$10^{-3}$', r'$10^{-4}$', r'$10^{-5}$', r'$10^{-6}$', r'$10^{-7}$'])
ax.set_xlabel('Limite de detection (fraction tumorale)', fontsize=11)
ax.set_yticks([])
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.set_ylim(-0.5, len(methods_data) - 0.3)

ax.set_title('Figure 3. Sensibilite analytique des methodes de detection (DLBCL)',
             fontsize=12, fontweight='bold', loc='left', pad=12)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'fig3_methodes_sensibilite.png'), dpi=120, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("Fig 3 saved")

# =========================================================
# FIGURE 4 : ctDNA-MRD vs PET-CMR - CORRIGE
# =========================================================
comparison_data = [
    ('Roschewski 2025 LBCL pooled\n(PhasED-Seq, 137pts) [75]', 28.7, (6.8, 121), 3.6, (1.5, 8.4), 137),
    ('Alcoceba 2024 DLBCL R-CHOP\n(EuroClonality, 68pts) [62]', 8.2, (2.5, 27), 2.8, (1.3, 6.0), 68),
    ('Vodicka 2025 real-world DLBCL\n(NGS 521g, ~150pts) [76]', 4.5, (1.8, 11.3), 2.2, (1.1, 4.4), 150),
    ('Le Goff 2023 LBCL frontline\n(panel 40g, 112pts) [50]', 3.8, (2.0, 7.2), 1.9, (1.0, 3.6), 112),
    ('Frank 2021 post-axi-cel\n(IgH-NGS, 72pts) [25]', 14.0, (5.0, 39), 4.5, (1.8, 11), 72),
    ('Stepan 2026 TRANSFORM post-liso-cel\n(PhasED-Seq, 136pts) [90]', 4.2, (2.1, 8.5), 2.5, (1.2, 5.0), 136),
]

# Same fix: split into 2 axes
fig, axes = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={'width_ratios': [3.5, 6.5], 'wspace': 0.02})
ax_labels, ax_plot = axes

y_pos = np.arange(len(comparison_data))[::-1]
bar_height = 0.35

ax_labels.set_xlim(0, 1)
ax_labels.set_ylim(-0.7, len(comparison_data) - 0.3)
ax_labels.axis('off')
for i, (label, *_) in enumerate(comparison_data):
    y = y_pos[i]
    ax_labels.text(0.98, y, label, ha='right', va='center', fontsize=9)

ax = ax_plot
for i, (label, ctdna_hr, ctdna_ci, pet_hr, pet_ci, n) in enumerate(comparison_data):
    y = y_pos[i]
    ax.plot([ctdna_ci[0], ctdna_ci[1]], [y + bar_height/2, y + bar_height/2], color='#1f77b4', lw=2)
    ax.scatter([ctdna_hr], [y + bar_height/2], s=90, color='#1f77b4', edgecolor='black', linewidth=1, zorder=3)
    ax.plot([pet_ci[0], pet_ci[1]], [y - bar_height/2, y - bar_height/2], color='#ff7f0e', lw=2)
    ax.scatter([pet_hr], [y - bar_height/2], s=90, color='#ff7f0e', edgecolor='black', linewidth=1, zorder=3)
    ax.text(200, y + bar_height/2, f"HR={ctdna_hr:.1f}", ha='left', va='center', fontsize=8, color='#1f77b4', fontweight='bold')
    ax.text(200, y - bar_height/2, f"HR={pet_hr:.1f}", ha='left', va='center', fontsize=8, color='#ff7f0e', fontweight='bold')

ax.axvline(x=1, color='red', linestyle='--', lw=1, alpha=0.6)
ax.text(1, len(comparison_data) - 0.2, 'HR=1', color='red', fontsize=9, ha='center')

ax.set_xscale('log')
ax.set_xlim(0.5, 500)
ax.set_xticks([0.5, 1, 2, 5, 10, 30, 100])
ax.set_xticklabels(['0.5', '1', '2', '5', '10', '30', '100'])
ax.set_xlabel('Hazard Ratio (PFS) - echelle logarithmique', fontsize=11)
ax.set_yticks([])
ax.set_ylim(-0.7, len(comparison_data) - 0.3)
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)

legend_handles = [
    Line2D([0], [0], marker='o', color='w', label='ctDNA-MRD', markerfacecolor='#1f77b4', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker='o', color='w', label='PET / CMR', markerfacecolor='#ff7f0e', markersize=10, markeredgecolor='black'),
]
ax.legend(handles=legend_handles, loc='upper right', fontsize=10, frameon=True, title='Modalite')

fig.suptitle('Figure 4. ctDNA-MRD vs PET-CMR en fin de traitement / post-CAR-T (HR plus eleve = meilleure discrimination)',
             fontsize=11.5, fontweight='bold', y=0.99)
plt.savefig(os.path.join(OUT_DIR, 'fig4_ctDNA_vs_PET.png'), dpi=120, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("Fig 4 saved")

# =========================================================
# FIGURE 5 : Schema protocole ALYCANTE (timeline visits)
# =========================================================
fig, ax = plt.subplots(figsize=(14, 7))
ax.set_xlim(-1.5, 30)
ax.set_ylim(-3.5, 4.5)

# Timeline horizontale
ax.plot([-1, 28], [0, 0], color='#333', lw=2.5, zorder=2)

# Marqueurs des visites (en mois depuis J0)
visites = [
    (-1.0, 'Leuca', 'Leucapherese\n(J-5 a J-30)', '#4d4d4d', 'top'),
    (-0.16, 'J-5', 'Lymphodepletion\n(fludarabine-cyclo)', '#4d4d4d', 'bottom'),
    (0.0, 'J0', 'Reinfusion axi-cel\n(Yescarta)', '#d62728', 'top'),
    (0.5, 'J14', 'Bilan precoce\ncellularite + ctDNA', '#1f77b4', 'bottom'),
    (1.0, 'M1', 'PET interim\n+ ctDNA', '#1f77b4', 'top'),
    (3.0, 'M3', 'CMR primary endpoint\n+ ctDNA', '#2ca02c', 'bottom'),
    (6.0, 'M6', 'Follow-up\n+ ctDNA', '#1f77b4', 'top'),
    (9.0, 'M9', 'Follow-up\n+ ctDNA', '#1f77b4', 'bottom'),
    (12.0, 'M12', 'PFS 1 an\n+ ctDNA', '#2ca02c', 'top'),
    (18.0, 'M18', 'Follow-up', '#1f77b4', 'bottom'),
    (24.0, 'M24', 'PFS 2 ans\n+ ctDNA', '#2ca02c', 'top'),
]

for t, label, desc, color, position in visites:
    y_marker = 0
    y_text = 1.2 if position == 'top' else -1.2
    # Marqueur
    ax.scatter([t], [y_marker], s=160, color=color, edgecolor='black', linewidth=1.5, zorder=4)
    # Label en bold sous le marqueur
    ax.text(t, 0.2 if position == 'top' else -0.4, label, ha='center', va='bottom' if position == 'top' else 'top',
            fontsize=9, fontweight='bold', zorder=5)
    # Description
    ax.annotate(desc, xy=(t, y_text * 0.4), xytext=(t, y_text),
                ha='center', va='center', fontsize=8,
                arrowprops=dict(arrowstyle='-', color=color, lw=0.8),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, lw=1))

# Zone CMR (visualisation du critere principal M3)
ax.axvspan(2.5, 3.5, alpha=0.18, color='#2ca02c', zorder=0)
ax.text(3.0, 2.5, 'Critère\nprincipal', ha='center', va='center', fontsize=10, fontweight='bold', color='#2ca02c',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#2ca02c', lw=1.5))

# Annotations supplementaires
# CAR-T en bas
ax.annotate('', xy=(0, -2.2), xytext=(0, -1.6),
            arrowprops=dict(arrowstyle='->', color='#d62728', lw=2))
ax.text(0, -2.5, 'INFUSION CAR-T', ha='center', va='top', fontsize=11, fontweight='bold', color='#d62728')

# Mesures longitudinales en haut
ax.annotate('', xy=(15, 3.2), xytext=(0, 3.2),
            arrowprops=dict(arrowstyle='->', color='#1f77b4', lw=1.5))
ax.text(7.5, 3.5, 'Mesures longitudinales ctDNA (n=421 obs / 57 patients) → JLCM',
        ha='center', va='center', fontsize=10, fontweight='bold', color='#1f77b4')

# Axe temporel
ax.set_xticks([0, 1, 3, 6, 9, 12, 18, 24])
ax.set_xticklabels(['J0', 'M1', 'M3', 'M6', 'M9', 'M12', 'M18', 'M24'])
ax.set_xlabel('Temps depuis l infusion CAR-T (mois)', fontsize=11)
ax.set_yticks([])
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.set_title('Figure 5. Schema du protocole ALYCANTE - Timeline des visites et critere principal',
             fontsize=12, fontweight='bold', loc='left', pad=12)

# Legend
legend_items = [
    ('Infusion CAR-T', '#d62728'),
    ('Critere principal (CMR M3)', '#2ca02c'),
    ('Mesures ctDNA / PET', '#1f77b4'),
    ('Etapes preparatoires', '#4d4d4d'),
]
legend_handles = [Line2D([0], [0], marker='o', color='w', label=lab, markerfacecolor=col, markersize=10, markeredgecolor='black') for lab, col in legend_items]
ax.legend(handles=legend_handles, loc='lower right', fontsize=9, frameon=True, title='Legende')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'fig5_protocole_ALYCANTE.png'), dpi=120, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("Fig 5 saved")

# =========================================================
# Verify all sizes are reasonable
# =========================================================
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
print("\n=== Verification dimensions finales ===")
for f in sorted(os.listdir(OUT_DIR)):
    if f.endswith('.png'):
        path = os.path.join(OUT_DIR, f)
        img = Image.open(path)
        sz = os.path.getsize(path)
        print(f"  {f}: {img.size[0]}x{img.size[1]} px, {sz:,} bytes")
