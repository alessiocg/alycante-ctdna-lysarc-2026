#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Informativite des echantillons — 3 panels
   Les 3 partagent EXACTEMENT la meme ordonnee : regions couvertes en log10.
   1. Boxplots par timepoint
   2. FN vs VN
   3. Scatter hEG (x) vs regions (y)
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.stats import mannwhitneyu

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === PATHS ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data") if os.path.isdir(os.path.join(SCRIPT_DIR, "data")) else SCRIPT_DIR

# === DATA ===
df = pd.read_excel(os.path.join(DATA_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0
df['regions'] = pd.to_numeric(df['nbre_total_de_regions_couvertes_de_la_WL'], errors='coerce')

surv = pd.read_excel(os.path.join(DATA_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')
# Correction J0
def _parse_dt(v):
    s = str(v).strip()
    try:
        n = float(s.replace(',', '.'))
        return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(n))
    except Exception:
        for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d']:
            try: return pd.to_datetime(s, format=fmt)
            except: pass
    return pd.NaT
surv['_dl'] = surv['Start of leukapheresis'].apply(_parse_dt)
surv['_dj'] = surv['Date of Axi-cel infusion (numeric)'].apply(_parse_dt)
surv['efs_time'] = surv['efs_time'] - (surv['_dj'] - surv['_dl']).dt.days / 30.44
is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')

tp_map = {'\u004c\u0065\u0075\u0063\u0061\u0070\u0068\u00e9\u0072\u00e8\u0073\u0065': 'Leuca',
           'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])
tp_order = ['Leuca', 'J-5', 'J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']

# === Limites log10 communes ===
all_regions = df['regions'].dropna()
all_regions = all_regions[all_regions > 0]
YMIN = 10 ** np.floor(np.log10(all_regions.min()))
YMAX = 10 ** np.ceil(np.log10(all_regions.max()))
LOG_TICKS = [10**i for i in range(int(np.log10(YMIN)), int(np.log10(YMAX)) + 1)]

print(f"Limites communes: {YMIN:.0f} - {YMAX:.0f}")
print(f"Ticks: {LOG_TICKS}")

# === FIGURE : 3 panels, meme Y ===
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6),
                                     gridspec_kw={'width_ratios': [1.2, 1.0, 0.9]})
fig.suptitle('Informativit\u00e9 des \u00e9chantillons', fontsize=14, fontweight='bold', y=0.98)

# --- Fonction unique pour configurer l'axe Y de chaque panel ---
def configure_yaxis(ax, show_label=True):
    ax.set_yscale('log')
    ax.set_ylim(YMIN, YMAX)
    ax.set_yticks(LOG_TICKS)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f'{x:,.0f}' if x >= 1 else f'{x:.1g}'))
    ax.yaxis.set_minor_locator(mticker.NullLocator())  # Pas de ticks mineurs
    if show_label:
        ax.set_ylabel('Nombre de r\u00e9gions couvertes', fontsize=11)
    else:
        ax.set_ylabel('')

# === PANEL 1 : Boxplots par timepoint ===
data_bp, labels_bp = [], []
for tp in tp_order:
    vals = df.loc[df['visite_std'] == tp, 'regions'].dropna()
    vals = vals[vals > 0]
    if len(vals) > 0:
        data_bp.append(vals.values)
        labels_bp.append(tp)

bp1 = ax1.boxplot(data_bp, tick_labels=labels_bp, patch_artist=True,
                  medianprops=dict(color='darkorange', linewidth=1.5))
for patch in bp1['boxes']:
    patch.set_facecolor('cornflowerblue')
    patch.set_alpha(0.6)
configure_yaxis(ax1, show_label=True)
ax1.set_title('Informativit\u00e9 par timepoint', fontsize=12, fontweight='bold')
ax1.tick_params(axis='x', rotation=45)

# === PANEL 2 : FN vs VN pour R/R 12m ET R/R 24m ===
neg = df[df['MRD_quali'] == 'NEGATIF'].copy()
neg = neg.merge(valid[['randomisation', 'efs_event', 'efs_time']], on='randomisation', how='left')
is_rr_neg = neg['efs_event'] == 1
neg['rr_12'] = (is_rr_neg & (neg['efs_time'] <= 12)).astype(int)
neg['rr_24'] = (is_rr_neg & (neg['efs_time'] <= 24)).astype(int)

# FN/VN R/R 12m (followup adequat)
fn12 = neg[neg['rr_12'] == 1]['regions'].dropna()
fn12 = fn12[fn12 > 0]
vn12_cand = neg[(neg['rr_12'] == 0) & ((neg['efs_time'] >= 12) | (neg['efs_event'] == 1))]
vn12 = vn12_cand['regions'].dropna()
vn12 = vn12[vn12 > 0]
_, pval12 = mannwhitneyu(fn12, vn12, alternative='two-sided') if len(fn12) > 0 and len(vn12) > 0 else (0, 1)

# FN/VN R/R 24m (followup adequat)
fn24 = neg[neg['rr_24'] == 1]['regions'].dropna()
fn24 = fn24[fn24 > 0]
vn24_cand = neg[(neg['rr_24'] == 0) & ((neg['efs_time'] >= 24) | (neg['efs_event'] == 1))]
vn24 = vn24_cand['regions'].dropna()
vn24 = vn24[vn24 > 0]
_, pval24 = mannwhitneyu(fn24, vn24, alternative='two-sided') if len(fn24) > 0 and len(vn24) > 0 else (0, 1)

bp2 = ax2.boxplot([fn12.values, vn12.values, fn24.values, vn24.values],
                  tick_labels=[f'FN 12m\n(n={len(fn12)})',
                               f'VN 12m\n(n={len(vn12)})',
                               f'FN 24m\n(n={len(fn24)})',
                               f'VN 24m\n(n={len(vn24)})'],
                  patch_artist=True,
                  medianprops=dict(color='darkorange', linewidth=1.5))
box_colors = ['#EF9A9A', '#A5D6A7', '#E57373', '#66BB6A']
for patch, c in zip(bp2['boxes'], box_colors):
    patch.set_facecolor(c)
    patch.set_alpha(0.7)
configure_yaxis(ax2, show_label=False)
p12_txt = f'{pval12:.4f}' if pval12 >= 0.001 else '<0.001'
p24_txt = f'{pval24:.4f}' if pval24 >= 0.001 else '<0.001'
ax2.set_title(f'FN vs VN\nR/R 12m: p={p12_txt} | R/R 24m: p={p24_txt}', fontsize=10, fontweight='bold')

# === PANEL 3 : hEG (x) vs Regions couvertes (y) ===
plot_df = df[['regions', 'MRD_quanti_heg']].dropna()
plot_df = plot_df[(plot_df['MRD_quanti_heg'] > 0) & (plot_df['regions'] > 0)]

ax3.scatter(plot_df['MRD_quanti_heg'], plot_df['regions'],
            alpha=0.5, s=30, color='mediumpurple', edgecolors='none')
configure_yaxis(ax3, show_label=False)
ax3.set_xlabel('hEG (log10, valeur brute)', fontsize=11)
ax3.set_title('hEG vs r\u00e9gions couvertes', fontsize=12, fontweight='bold')

# === Verification avant sauvegarde ===
for i, ax in enumerate([ax1, ax2, ax3]):
    yl = ax.get_ylim()
    print(f"Panel {i+1}: ylim=({yl[0]:.0f}, {yl[1]:.0f}), yscale={ax.get_yscale()}")

plt.tight_layout(rect=[0, 0, 1, 0.94])

outfile = os.path.join(SCRIPT_DIR, 'fig_informativity.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')
plt.close()
