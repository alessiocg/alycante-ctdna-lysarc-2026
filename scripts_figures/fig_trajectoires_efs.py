#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Spaghetti plot — trajectoires ctDNA individuelles stratifiées par EFS (R/R strict)
Style publication médicale."""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE_DIR = "C:/Users/4067048/AppData/Local/Temp/alycante_v2"
OUT_DIR  = os.path.join(BASE_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# =====================================================================
# DATA
# =====================================================================
df = pd.read_excel(os.path.join(BASE_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')

# NEGATIF → hEG = 0 (but keep original value if negative — distinguishes true 0 from low signal)
df.loc[(df['MRD_quali'] == 'NEGATIF') & (df['MRD_quanti_heg'].isna()), 'MRD_quanti_heg'] = 0.0
# Keep negative hEG values as-is for visual distinction

surv = pd.read_excel(os.path.join(BASE_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')
# Ajustement J0: soustraire le délai leucaphérèse→J0 par patient
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
surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)  # R/R strict
valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')

# Timepoints
tp_order = ['Leucaphérèse', 'D-5', 'D0', 'D14', 'M1', 'M3', 'M6', 'M9', 'M12']
tp_labels = ['Leuca', 'J-5', 'J0', 'J14', 'M1', 'M3', 'M6', 'M9', 'M12']
tp_map = {
    'Leucaphérèse': 0, 'D-5': 1, 'D0': 2, 'D14': 3,
    'M1': 4, 'M3': 5, 'M6': 6, 'M9': 7, 'M12': 8
}

# Build trajectory matrix
trajectories = []
for pat in df['randomisation'].unique():
    pat_data = df[df['randomisation'] == pat]
    ps = valid[valid['randomisation'] == pat]
    if len(ps) == 0:
        continue
    efs_ev = ps['efs_event'].values[0]

    traj = {'pat': pat, 'efs_event': efs_ev}
    for _, row in pat_data.iterrows():
        v = row['visite']
        if v in tp_map:
            traj[tp_map[v]] = row['MRD_quanti_heg']
    trajectories.append(traj)

traj_df = pd.DataFrame(trajectories)
n_event = traj_df['efs_event'].sum()
n_no_event = len(traj_df) - n_event

print(f'N={len(traj_df)}, EFS event (R/R): {n_event}, No event: {n_no_event}')

# =====================================================================
# FIGURE
# =====================================================================
# Compute R/R groups
surv_map = valid.set_index('randomisation')
traj_df['rr_12'] = traj_df['pat'].map(lambda p: int(surv_map.loc[p, 'efs_event'] == 1 and surv_map.loc[p, 'efs_time'] <= 12) if p in surv_map.index else 0)
traj_df['rr_24'] = traj_df['pat'].map(lambda p: int(surv_map.loc[p, 'efs_event'] == 1 and surv_map.loc[p, 'efs_time'] <= 24) if p in surv_map.index else 0)
traj_df['rr_12_24'] = ((traj_df['rr_24'] == 1) & (traj_df['rr_12'] == 0)).astype(int)
traj_df['no_rr'] = (traj_df['efs_event'] == 0).astype(int)

grp_no_rr = traj_df[traj_df['no_rr'] == 1]
grp_rr12 = traj_df[traj_df['rr_12'] == 1]
grp_rr24 = traj_df[traj_df['rr_24'] == 1]
grp_rr12_24 = traj_df[traj_df['rr_12_24'] == 1]

print(f'Pas de R/R: {len(grp_no_rr)}, R/R 12m: {len(grp_rr12)}, R/R 12-24m: {len(grp_rr12_24)}, R/R 24m: {len(grp_rr24)}')

fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True, sharex=True)
fig.suptitle('Cinétique longitudinale du ctDNA (hEG)',
             fontsize=14, fontweight='bold', y=0.98)

panels = [
    (axes[0, 0], grp_no_rr, f'Pas de R/R (n={len(grp_no_rr)})', '#6699CC', '#003366'),
    (axes[0, 1], grp_rr12, f'R/R ≤ 12 mois (n={len(grp_rr12)})', '#CC6666', '#660000'),
    (axes[1, 0], grp_rr12_24, f'R/R 12–24 mois (n={len(grp_rr12_24)})', '#CC9966', '#663300'),
    (axes[1, 1], grp_rr24, f'R/R ≤ 24 mois (n={len(grp_rr24)})', '#CC4444', '#880000'),
]

for ax, sub, title, color_line, color_med in panels:
    for _, row in sub.iterrows():
        xs, ys = [], []
        for t in range(9):
            if t in row and pd.notna(row[t]):
                xs.append(t)
                ys.append(row[t])  # keep raw values
        if len(xs) > 1:
            ax.plot(xs, ys, color=color_line, alpha=0.25, linewidth=0.8, zorder=1)

    # Median points (not connected — no trend line)
    for t in range(9):
        vals = sub[t].dropna() if t in sub.columns else pd.Series()
        if len(vals) > 0:
            ax.plot(t, vals.median(), color=color_med, marker='o',
                    markersize=6, zorder=3, linestyle='none')

    # Zero line (dashed, starts at x=0)
    ax.axhline(y=0, color='grey', linewidth=0.5, linestyle=':', zorder=0)

    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(range(9))
    ax.set_xticklabels(tp_labels, rotation=45, ha='right', fontsize=9)
    ax.set_ylim(-0.7, 5.5)
    ax.set_xlim(-0.3, 8.3)

    # Y-axis
    ax.set_yticks([0, 1, 2, 3, 4, 5])
    ax.tick_params(axis='y', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

for ax in [axes[0, 0], axes[1, 0]]:
    ax.set_ylabel('hEG (log$_{10}$)', fontsize=11)

# Shared legend at bottom
fig.text(0.5, 0.005,
         'Lignes fines : trajectoires individuelles  |  '
         'Points : médiane par timepoint  |  '
         'hEG < 0 = signal sous le bruit de fond  |  '
         'R/R = rechute/progression uniquement',
         ha='center', fontsize=8, color='#666666', style='italic')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

outfile = os.path.join(OUT_DIR, 'fig_trajectoires_efs.png')
plt.savefig(outfile, dpi=250, bbox_inches='tight', facecolor='white')
print(f'OK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'fig_trajectoires_efs.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
