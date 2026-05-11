#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Heatmap AUC des delta ctDNA + 3 KM du meilleur couple"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === DATA ===
df = pd.read_excel('Donnees.xlsx')
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0

surv = pd.read_excel('ALYCANTE_RNASeq_21OCT2025.xlsx')
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')
is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')

tp_map = {'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
           'M1': 'M1', 'M3': 'M3', 'M6': 'M6', 'M9': 'M9', 'M12': 'M12'}
df['visite_std'] = df['visite'].map(tp_map).fillna(df['visite'])
piv = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')

tp_landmark = {'J14': 1.5, 'M1': 2, 'M3': 4, 'M6': 7}
baselines = ['Leuca', 'J-5', 'J0']
targets = ['J14', 'M1', 'M3']
bl_order = {'Leuca': 0, 'J-5': 1, 'J0': 2}
tp_order_map = {'J14': 3, 'M1': 4, 'M3': 5, 'M6': 6}

# === HEATMAP DATA ===
auc_12 = np.full((len(baselines), len(targets)), np.nan)
auc_24 = np.full((len(baselines), len(targets)), np.nan)
ns = np.full((len(baselines), len(targets)), np.nan)

for i, bl in enumerate(baselines):
    for j, tp in enumerate(targets):
        if bl not in piv.columns or tp not in piv.columns:
            continue
        if bl_order[bl] >= tp_order_map[tp]:
            continue
        delta = (piv[tp] - piv[bl]).dropna()
        merged = pd.DataFrame({'randomisation': delta.index, 'delta': delta.values})
        merged = merged.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
        lm = tp_landmark[tp]
        merged = merged[merged['efs_time'] > lm].copy()
        merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)
        merged['rr_24'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 24)).astype(int)
        if len(merged) < 10 or merged['rr_12'].sum() < 3:
            continue
        try:
            auc_12[i, j] = roc_auc_score(merged['rr_12'], merged['delta'])
            auc_24[i, j] = roc_auc_score(merged['rr_24'], merged['delta'])
            ns[i, j] = len(merged)
        except:
            pass

# === HEATMAP FIGURE ===
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
fig.suptitle('AUC ROC du \u0394ctDNA (hEG) par combinaison baseline \u2192 timepoint\n'
             '(analyse landmark, R/R strict)',
             fontsize=12, fontweight='bold')

for ax, data, title in [(ax1, auc_12, 'AUC R/R \u2264 12 mois'),
                         (ax2, auc_24, 'AUC R/R \u2264 24 mois')]:
    im = ax.imshow(data, cmap='RdYlGn', vmin=0.5, vmax=0.85, aspect='auto')
    ax.set_xticks(range(len(targets)))
    ax.set_xticklabels(targets)
    ax.set_yticks(range(len(baselines)))
    ax.set_yticklabels(baselines)
    ax.set_xlabel('Timepoint cible')
    ax.set_ylabel('Baseline')
    ax.set_title(title, fontsize=11, pad=8)
    for ii in range(len(baselines)):
        for jj in range(len(targets)):
            val = data[ii, jj]
            n = ns[ii, jj]
            if np.isnan(val):
                ax.text(jj, ii, '\u2014', ha='center', va='center', color='grey', fontsize=10)
            else:
                color = 'white' if val > 0.72 else 'black'
                ax.text(jj, ii, f'{val:.3f}\n(n={int(n)})', ha='center', va='center',
                        color=color, fontsize=9,
                        fontweight='bold' if val > 0.7 else 'normal')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='AUC')

plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.savefig('output/fig_heatmap_auc_delta.png', dpi=250, bbox_inches='tight', facecolor='white')
print('OK: output/fig_heatmap_auc_delta.png')

# === BEST COUPLE: Leuca -> M1 ===
delta = (piv['M1'] - piv['Leuca']).dropna()
merged = pd.DataFrame({'randomisation': delta.index, 'delta': delta.values})
merged = merged.merge(valid[['randomisation', 'efs_time', 'efs_event']], on='randomisation')
merged = merged[merged['efs_time'] > 2.0].copy()
merged['efs_time_lm'] = merged['efs_time'] - 2.0
merged['rr_12'] = ((merged['efs_event'] == 1) & (merged['efs_time'] <= 12)).astype(int)

# Scan 0.5-log seuils
seuils_05 = np.arange(-5.0, 1.5, 0.5)
best_youden = -1; best_youden_s = None
best_ppv = 0; best_ppv_s = None
best_npv = 0; best_npv_s = None

print(f'\n{"Seuil":>6} | {"n_bon":>5} {"n_mauv":>5} | {"Sens":>5} {"Spec":>5} {"PPV":>5} {"NPV":>5} | {"Youden":>7}')
print('-' * 65)

for s in seuils_05:
    g_mauv = merged[merged['delta'] > s]
    g_bon = merged[merged['delta'] <= s]
    if len(g_mauv) < 2 or len(g_bon) < 2:
        continue
    tp_v = int(g_mauv['rr_12'].sum())
    fp_v = len(g_mauv) - tp_v
    fn_v = int(g_bon['rr_12'].sum())
    tn_v = len(g_bon) - fn_v
    sens = tp_v / (tp_v + fn_v) if (tp_v + fn_v) > 0 else 0
    spec = tn_v / (tn_v + fp_v) if (tn_v + fp_v) > 0 else 0
    ppv = tp_v / (tp_v + fp_v) if (tp_v + fp_v) > 0 else 0
    npv = tn_v / (tn_v + fn_v) if (tn_v + fn_v) > 0 else 0
    youden = sens + spec - 1

    tags = []
    if youden > best_youden:
        best_youden = youden; best_youden_s = s; tags.append('Y')
    if ppv > best_ppv:
        best_ppv = ppv; best_ppv_s = s; tags.append('P')
    if npv > best_npv:
        best_npv = npv; best_npv_s = s; tags.append('N')
    tag = ' <-- ' + ','.join(tags) if tags else ''
    print(f'{s:6.1f} | {len(g_bon):5d} {len(g_mauv):5d} | {sens:5.0%} {spec:5.0%} {ppv:5.0%} {npv:5.0%} | {youden:7.3f}{tag}')

print(f'\nMeilleur Youden: seuil={best_youden_s:.1f}')
print(f'Meilleure PPV:   seuil={best_ppv_s:.1f}')
print(f'Meilleure NPV:   seuil={best_npv_s:.1f}')

# === 3 KM ===
fig_km, axes_km = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
fig_km.suptitle('EFS selon \u0394ctDNA Leuca\u2192M1 (landmark M1, R/R strict)',
                fontsize=13, fontweight='bold', y=1.02)

km_configs = [
    (axes_km[0], best_npv_s, 'Meilleure NPV'),
    (axes_km[1], best_youden_s, 'Meilleur Youden'),
    (axes_km[2], best_ppv_s, 'Meilleure PPV'),
]

for ax, seuil, label in km_configs:
    g_bon = merged[merged['delta'] <= seuil]
    g_mauv = merged[merged['delta'] > seuil]

    lr = logrank_test(g_bon['efs_time_lm'], g_mauv['efs_time_lm'],
                      event_observed_A=g_bon['efs_event'],
                      event_observed_B=g_mauv['efs_event'])

    kmf0 = KaplanMeierFitter()
    kmf0.fit(g_bon['efs_time_lm'], g_bon['efs_event'],
             label=f'\u0394\u2264{seuil:.1f} (n={len(g_bon)})')
    kmf0.plot_survival_function(ax=ax, color='#1565C0', ci_show=True, ci_alpha=0.15)

    kmf1 = KaplanMeierFitter()
    kmf1.fit(g_mauv['efs_time_lm'], g_mauv['efs_event'],
             label=f'\u0394>{seuil:.1f} (n={len(g_mauv)})')
    kmf1.plot_survival_function(ax=ax, color='#C62828', ci_show=True, ci_alpha=0.15)

    ax.set_title(f'{label} (seuil={seuil:.1f})', fontsize=10, fontweight='bold')
    ax.set_xlabel('Temps depuis M1 (mois)', fontsize=9)
    ax.set_xlim(0, 40)
    ax.legend(loc='lower left', fontsize=8)
    ax.text(0.95, 0.95, f'Log-rank p={lr.p_value:.4f}',
            transform=ax.transAxes, ha='right', va='top', fontsize=9,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

axes_km[0].set_ylabel('Probabilit\u00e9 EFS', fontsize=10)
plt.tight_layout()
plt.savefig('output/fig_km_delta_leuca_m1.png', dpi=250, bbox_inches='tight', facecolor='white')
print('OK: output/fig_km_delta_leuca_m1.png')

# Copy to network
net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\R\u00e9union LYSARC 2026\output')
for f in ['fig_heatmap_auc_delta.png', 'fig_km_delta_leuca_m1.png']:
    try:
        shutil.copy2(f'output/{f}', os.path.join(net_dir, f))
        print(f'Copied {f} to network')
    except Exception as e:
        pass

# Bash copy fallback
import subprocess
for f in ['fig_heatmap_auc_delta.png', 'fig_km_delta_leuca_m1.png']:
    subprocess.run(['cp', f'output/{f}',
                    '//hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/'
                    'SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/'
                    'protocole ALYCANTE/Réunion LYSARC 2026/output/'],
                   capture_output=True)
print('Done.')
