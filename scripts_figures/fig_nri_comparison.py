#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NRI — Net Reclassification Improvement
Compare JLCM J14, CMR M3, Delta hEG pour R/R 12m et R/R 24m
Montre combien de patients sont mieux/moins bien classes par chaque methode"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# === DATA ===
df = pd.read_excel(os.path.join(DATA_DIR, 'Donnees.xlsx'))
ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
df = df[~df['randomisation'].isin(ni)]
df['visite_std'] = df['visite'].map({
    'Leucaph\xe9r\xe8se': 'Leuca', 'D-5': 'J-5', 'D0': 'J0', 'D14': 'J14',
    'M1': 'M1', 'M3': 'M3'}).fillna(df['visite'])
df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0

surv = pd.read_excel(os.path.join(DATA_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')

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
valid['rr_12'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 12)).astype(int)
valid['rr_24'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 24)).astype(int)
valid['adeq_12'] = ((valid['efs_time'] >= 12) | (valid['efs_event'] == 1))
valid['adeq_24'] = ((valid['efs_time'] >= 24) | (valid['efs_event'] == 1))

piv_heg = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quanti_heg', aggfunc='first')
piv_mrd = df.pivot_table(index='randomisation', columns='visite_std', values='MRD_quali', aggfunc='first')

# === Classifications ===
# JLCM J14
jlcm = pd.read_csv(os.path.join(DATA_DIR, 'jlcm_predict_j14.csv'))
jlcm_cl = jlcm.dropna(subset=['group']).set_index('randomisation')['group']

# CMR M3
cmr = piv_mrd['M3'].dropna()
cmr_cl = cmr.map(lambda x: 'BON' if x == 'NEGATIF' else 'MAUVAIS')

# Delta hEG
delta = (piv_heg['M1'] - piv_heg['Leuca']).dropna()
delta_cl = delta.map(lambda x: 'BON' if x <= -3.0 else 'MAUVAIS')


def compute_nri(ref_cl, new_cl, outcome, label_ref, label_new):
    """Compute NRI between reference and new classification."""
    common = ref_cl.index.intersection(new_cl.index).intersection(outcome.index)
    ref = ref_cl[common]
    new = new_cl[common]
    out = outcome[common]
    n = len(common)

    # Events: correctly reclassified up (BON→MAUVAIS for events) = good
    # Non-events: correctly reclassified down (MAUVAIS→BON for non-events) = good
    events = out == 1
    non_events = out == 0

    # Up = moved to higher risk (BON→MAUVAIS), Down = moved to lower risk (MAUVAIS→BON)
    up = (ref == 'BON') & (new == 'MAUVAIS')
    down = (ref == 'MAUVAIS') & (new == 'BON')
    same = ref == new

    # NRI events = P(up|event) - P(down|event)
    n_ev = events.sum()
    n_nev = non_events.sum()
    nri_ev = (up & events).sum() / max(n_ev, 1) - (down & events).sum() / max(n_ev, 1)
    nri_nev = (down & non_events).sum() / max(n_nev, 1) - (up & non_events).sum() / max(n_nev, 1)
    nri_total = nri_ev + nri_nev

    return {
        'ref': label_ref, 'new': label_new, 'n': n,
        'up_events': int((up & events).sum()), 'down_events': int((down & events).sum()),
        'up_nonevents': int((up & non_events).sum()), 'down_nonevents': int((down & non_events).sum()),
        'same': int(same.sum()),
        'nri_events': nri_ev, 'nri_nonevents': nri_nev, 'nri_total': nri_total,
        'n_events': int(n_ev), 'n_nonevents': int(n_nev),
    }


# === Compute NRI for all pairs ===
results = []
for rr_col, adeq_col, rr_label in [('rr_12', 'adeq_12', 'R/R 12m'), ('rr_24', 'adeq_24', 'R/R 24m')]:
    outcome = valid[valid[adeq_col]].set_index('randomisation')[rr_col]

    pairs = [
        (cmr_cl, jlcm_cl, 'CMR M3', 'JLCM J14'),
        (delta_cl, jlcm_cl, '\u0394hEG', 'JLCM J14'),
        (delta_cl, cmr_cl, '\u0394hEG', 'CMR M3'),
    ]

    for ref, new, ref_lab, new_lab in pairs:
        r = compute_nri(ref, new, outcome, ref_lab, new_lab)
        r['endpoint'] = rr_label
        results.append(r)
        print(f'{rr_label} | {ref_lab} \u2192 {new_lab}: NRI={r["nri_total"]:.3f} '
              f'(events={r["nri_events"]:.3f}, non-events={r["nri_nonevents"]:.3f}, n={r["n"]})')

res = pd.DataFrame(results)

# === FIGURE ===
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
fig.suptitle('Net Reclassification Improvement (NRI)',
             fontsize=14, fontweight='bold', y=0.98)

for ax, rr_label in [(ax1, 'R/R 12m'), (ax2, 'R/R 24m')]:
    sub = res[res['endpoint'] == rr_label]

    labels = [f'{r["new"]} vs {r["ref"]}' for _, r in sub.iterrows()]
    x = np.arange(len(labels))
    width = 0.25

    nri_ev = sub['nri_events'].values
    nri_nev = sub['nri_nonevents'].values
    nri_tot = sub['nri_total'].values

    bars1 = ax.bar(x - width, nri_ev * 100, width, color='#C62828', alpha=0.8, label='NRI events')
    bars2 = ax.bar(x, nri_nev * 100, width, color='#1565C0', alpha=0.8, label='NRI non-events')
    bars3 = ax.bar(x + width, nri_tot * 100, width, color='#2E7D32', alpha=0.8, label='NRI total')

    # Annotate
    for i in range(len(sub)):
        for bars, val in [(bars1, nri_ev[i]), (bars2, nri_nev[i]), (bars3, nri_tot[i])]:
            b = bars[i]
            y_pos = b.get_height() + 1 if b.get_height() >= 0 else b.get_height() - 3
            ax.text(b.get_x() + b.get_width() / 2, y_pos, f'{val*100:.0f}%',
                    ha='center', va='bottom' if val >= 0 else 'top',
                    fontsize=8, fontweight='bold')

    ax.axhline(y=0, color='grey', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_title(rr_label, fontsize=12, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.15)

ax1.set_ylabel('NRI (%)', fontsize=11)
ax1.legend(fontsize=9, loc='upper left')

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = os.path.join(SCRIPT_DIR, 'fig_nri_comparison.png')
plt.savefig(outfile, dpi=200, bbox_inches='tight', facecolor='white')
print(f'\nOK: {outfile}')

net_dir = (r'\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE'
           r'\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL'
           r'\protocole ALYCANTE\Réunion LYSARC 2026\output')
try:
    shutil.copy2(outfile, os.path.join(net_dir, 'Figures',
                 'Figure relues et validées', 'fig_nri_comparison.png'))
    print('Copied to network')
except Exception as e:
    print(f'Warning: {e}')
print('Done.')
