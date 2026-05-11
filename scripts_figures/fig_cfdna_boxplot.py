#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Boxplot cfDNA total par timepoint"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

df = pd.read_excel(os.path.join(DATA_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['visite_std'] = df['visite'].map({
    'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
    'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}).fillna(df['visite'])

# cfDNA total en log10
df['cfdna_log10'] = pd.to_numeric(df.get('cfDNA_concentration_log10', df.get('MRD_quanti_cfDNA', pd.Series(dtype=float))), errors='coerce')

# Chercher la bonne colonne cfDNA
cfdna_cols = [c for c in df.columns if 'cfdna' in c.lower() or 'cf_dna' in c.lower() or 'cfDNA' in c]
print(f'Colonnes cfDNA trouvees: {cfdna_cols}')

# Utiliser la colonne qui existe
for col in cfdna_cols:
    vals = pd.to_numeric(df[col], errors='coerce')
    if vals.notna().sum() > 10:
        df['cfdna_val'] = vals
        print(f'Utilisation de: {col} ({vals.notna().sum()} valeurs)')
        break

timepoints = ['Leuca', 'J-5', 'J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']

data_by_tp = []
labels = []
for tp in timepoints:
    vals = df.loc[df['visite_std'] == tp, 'cfdna_val'].dropna()
    if len(vals) > 0:
        data_by_tp.append(vals.values)
        labels.append(tp)

fig, ax = plt.subplots(figsize=(12, 5.5))
fig.suptitle('Distribution cfDNA total par timepoint', fontsize=13, fontweight='bold', y=0.98)

bp = ax.boxplot(data_by_tp, patch_artist=True, widths=0.6,
                boxprops=dict(facecolor='#FFF9C4', edgecolor='#F57F17', linewidth=1.2),
                medianprops=dict(color='#E65100', linewidth=2),
                whiskerprops=dict(color='#F57F17', linewidth=1),
                capprops=dict(color='#F57F17', linewidth=1),
                flierprops=dict(marker='o', markerfacecolor='none', markeredgecolor='black', markersize=5))

ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel('cfDNA total (log10)', fontsize=11)
ax.set_ylim(0, 5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.2, linestyle='--')

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_cfdna_boxplot.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_cfdna_boxplot.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
