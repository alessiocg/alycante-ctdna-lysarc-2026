# -*- coding: utf-8 -*-
"""
extend_lea_all_timepoints.py
Étend la cohorte de validation Léa à tous les timepoints disponibles
(J0, J14, M1, M3, M6, M9, M12) en utilisant la même formule hEG +
offset de calibration que jlcm_lea_extend_all.py original.

Sources :
  - Base CART 02.04.xlsx (caractéristiques cliniques)
  - ngs_database.db (patients_clinical + variants_full_materialized)
  - data_lcmm_long.csv ALYCANTE (pour offset de calibration sur médiane heg)

Output :
  - lea_extended_jlcm_input.csv (long format avec timepoints étendus)
  - Affiche un récap par patient
"""
import sqlite3, sys, openpyxl, re, unicodedata, csv, math
from datetime import datetime, timedelta
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

DB = r'C:\Users\4067048\AppData\Local\Temp\ngs_database_local_cache.db'
NAS = r'\\Hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL\protocole ALYCANTE\Réunion LYSARC 2026'
LEA_XLSX = NAS + r'\input\Base CART 02.04.xlsx'
ALY_LONG = NAS + r'\output\blood_article_package\input\data_lcmm_long.csv'
OUT_DIR = NAS + r'\output\blood_article_package\output\tables'
OUT_CSV = OUT_DIR + r'\lea_extended_jlcm_input.csv'

# Time windows (in months from CAR-T infusion date d_reinj)
WINDOWS = {
    'J0':  (-30/30.44,  3/30.44),    # baseline
    'J14': ( 5/30.44, 28/30.44),     # day-14
    'M1':  (28/30.44, 50/30.44),     # ~1 month
    'M3':  (75/30.44,105/30.44),     # ~3 months
    'M6':  (165/30.44,200/30.44),    # ~6 months
    'M9':  (255/30.44,290/30.44),    # ~9 months
    'M12': (345/30.44,400/30.44),    # ~12 months
}
TIME_VAL = {'J0': 0.0, 'J14': 14/30.44, 'M1': 30/30.44,
            'M3': 91/30.44, 'M6': 182/30.44, 'M9': 274/30.44, 'M12': 365/30.44}

def norm(s):
    if s is None: return ''
    s = str(s).strip().upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+',' ', re.sub(r'[^A-Z0-9 -]','', s)).strip()

def td(v):
    if v is None: return None
    if isinstance(v, datetime): return v
    if isinstance(v, str):
        for fmt in ('%Y-%m-%d','%d/%m/%Y','%Y-%m-%d %H:%M:%S','%d-%m-%Y'):
            try: return datetime.strptime(v.strip(), fmt)
            except: pass
    return None

def fnum(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip().replace(',', '.').replace(' ', '').replace('%','')
    try: return float(s)
    except: return None

def glims_norm(gl):
    if gl is None: return None
    return str(gl).replace('-', '').strip()

# === ALYCANTE median heg for calibration ===
aly_heg = []
with open(ALY_LONG, encoding='utf-8') as f:
    rd = csv.DictReader(f)
    for r in rd:
        try:
            v = float(r['heg'])
            if v > 0: aly_heg.append(v)
        except: pass
aly_heg.sort()
aly_med_log = math.log10(aly_heg[len(aly_heg)//2])
print(f"ALYCANTE median heg log10 = {aly_med_log:.3f}\n")

# === Léa cohort metadata ===
print(f"Reading {LEA_XLSX}...")
wb = openpyxl.load_workbook(LEA_XLSX, data_only=True)
ws = wb['Generalites']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]
required = ['Nom','DDN','Date_reinjection','Type_CART','Lignes_avantCART',
            'OMS2016','AutogreffeL1','Statut_der.nouv','Date_der.nouv',
            'Date.rechute','Cause_deces','Centre','Brige','IPI.diag','Sexe']
c = {n: hdr.index(n) for n in required}
lea = []
for r in rows[1:]:
    nm = r[c['Nom']]
    if not nm: continue
    dr = td(r[c['Date_reinjection']])
    if not dr: continue
    oms = str(r[c['OMS2016']] or '')
    if 'DLBCL' not in oms.upper(): continue
    ddn = td(r[c['DDN']])
    age = (dr-ddn).days/365.25 if ddn else None
    lea.append({'nom':str(nm),'nom_n':norm(nm),'ddn':ddn,'age':age,'d_reinj':dr,
                'type':str(r[c['Type_CART']] or '').strip(),
                'lignes':r[c['Lignes_avantCART']],
                'autoL1':str(r[c['AutogreffeL1']] or ''),
                'statut':str(r[c['Statut_der.nouv']] or ''),
                'der':td(r[c['Date_der.nouv']]),'rechute':td(r[c['Date.rechute']]),
                'cause':str(r[c['Cause_deces']] or ''),
                'centre':str(r[c['Centre']] or ''),
                'bridge':str(r[c['Brige']] or ''),
                'ipi':r[c['IPI.diag']], 'sexe':str(r[c['Sexe']] or '')})
print(f"Léa DLBCL : {len(lea)} patients\n")

# === SQL : récupérer TOUTES les samples cliniques pour ces patients ===
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()
noms = tuple(p['nom'].upper() for p in lea)
ph = ','.join('?'*len(noms))
clin = cur.execute(f"""SELECT Glims, NOM, DDN, DDN_glims, date_prelevement_imputee,
                              Cell_Free_DNA, Moyenne_VAF
                       FROM patients_clinical
                       WHERE UPPER(NOM) IN ({ph})""", noms).fetchall()
print(f"patients_clinical rows for Léa cohort : {len(clin)}")

clin_by_name = {}
for r in clin: clin_by_name.setdefault(norm(r['NOM']), []).append(r)

# === Match chaque sample à un timepoint window pour chaque patient ===
elig = []
all_matched_samples = []
for p in lea:
    cands = clin_by_name.get(p['nom_n'], [])
    if p['ddn']:
        cm = [r for r in cands if (td(r['DDN']) and abs((td(r['DDN'])-p['ddn']).days)<=2)
              or (td(r['DDN_glims']) and abs((td(r['DDN_glims'])-p['ddn']).days)<=2)]
        if cm: cands = cm
    if not cands: continue
    d0 = p['d_reinj']
    matched_tps = {}  # tp -> (best_row, delta_months)
    for r in cands:
        d_pr = td(r['date_prelevement_imputee'])
        if not d_pr: continue
        delta_m = (d_pr - d0).days / 30.44
        for tp, (low, high) in WINDOWS.items():
            if low <= delta_m <= high:
                # Choose row closest to center of window
                center = (low + high) / 2
                if tp not in matched_tps or abs(delta_m - center) < abs(matched_tps[tp][1] - center):
                    matched_tps[tp] = (r, delta_m)
    if matched_tps:
        elig.append({'p': p, 'tps': matched_tps})
        for tp, (r, dm) in matched_tps.items():
            all_matched_samples.append({'nom': p['nom'], 'tp': tp, 'delta_m': dm, 'glims': r['Glims']})

print(f"\nPatients eligible (≥1 timepoint matched) : {len(elig)}")
# Distribution timepoints
tp_dist = Counter()
for e in elig:
    for tp in e['tps']: tp_dist[tp] += 1
print(f"Timepoint distribution : {dict(sorted(tp_dist.items()))}")

# Patients with J0+J14 (current published cohort)
n_j0_j14 = sum(1 for e in elig if 'J0' in e['tps'] and 'J14' in e['tps'])
n_with_late = sum(1 for e in elig if any(tp in e['tps'] for tp in ['M1','M3','M6','M9','M12']))
print(f"Patients with J0+J14 : {n_j0_j14}")
print(f"Patients with ≥1 late timepoint (M1+) : {n_with_late}")

# === Récup VAF pour tous les glims des samples matched ===
glims_set = set()
for e in elig:
    for tp, (r, dm) in e['tps'].items():
        gn = glims_norm(r['Glims'])
        if gn: glims_set.add(gn)
ph2 = ','.join('?'*len(glims_set))
q = f"""SELECT glims_norm, VAF, vaf_font_color, PREDICTED, is_mutation
        FROM variants_full_materialized
        WHERE glims_norm IN ({ph2})
          AND (vaf_font_color='FFFF0000' OR PREDICTED='Mutation' OR is_mutation='1')
          AND is_best_run=1"""
rows_var = cur.execute(q, tuple(glims_set)).fetchall()
print(f"\nVariants rows found : {len(rows_var)}")
by_glims_raw = {}
for r in rows_var:
    by_glims_raw.setdefault(r['glims_norm'], []).append(r)
# Hiérarchie : rouge > mutation classique
vbg = {}
for gn, rows in by_glims_raw.items():
    rouge = [r for r in rows if r['vaf_font_color'] == 'FFFF0000']
    chosen = rouge if rouge else [r for r in rows if r['PREDICTED']=='Mutation' or str(r['is_mutation'])=='1']
    for r in chosen:
        v = fnum(r['VAF'])
        if v is not None:
            vbg.setdefault(gn, []).append(v)

# === Calibration sur J0+J14 SEULEMENT (cohérent avec le manuscript) ===
lea_heg_log_j0_j14 = []
for e in elig:
    for tp in ['J0', 'J14']:
        if tp not in e['tps']: continue
        r, dm = e['tps'][tp]
        gn = glims_norm(r['Glims'])
        cfdna = fnum(r['Cell_Free_DNA'])
        if gn in vbg and cfdna and cfdna > 0:
            vaf_m = sum(vbg[gn]) / len(vbg[gn])
            heg = vaf_m * cfdna
            if heg > 0: lea_heg_log_j0_j14.append(math.log10(heg))
lea_heg_log_j0_j14.sort()
if not lea_heg_log_j0_j14:
    print("FATAL : pas de heg pour calibration"); sys.exit(1)
lea_med_log = lea_heg_log_j0_j14[len(lea_heg_log_j0_j14)//2]
offset = aly_med_log - lea_med_log
print(f"\nLéa J0+J14 median log10 = {lea_med_log:.3f}")
print(f"Calibration offset (= aly_med - lea_med) = {offset:.3f}\n")

# === Build long format with ALL timepoints + survie ===
records = []
print(f"{'ID':>3} {'Nom':25} {'Type':10} {'n_tp':>5} {'tps':25} {'efs_m':>7} {'evt':>4} {'os_m':>7} {'os_e':>5}")
print('-'*110)
for i, e in enumerate(elig, 1):
    p = e['p']
    # Survival
    rechute = p['rechute']; der = p['der']
    statut_norm = ''.join(ch for ch in unicodedata.normalize('NFD', p['statut']) if unicodedata.category(ch) != 'Mn').lower()
    is_dead = any(x in statut_norm for x in ('dece','decede','dcd','mort'))
    is_relapse = any(x in statut_norm for x in ('rechute','progress','recidive'))
    efs_event = 1 if (rechute is not None or is_dead or is_relapse) else 0
    if rechute is not None and rechute > p['d_reinj']:
        efs_time = (rechute - p['d_reinj']).days / 30.44
    elif der is not None:
        efs_time = (der - p['d_reinj']).days / 30.44
    else:
        efs_time = 0
    os_event = 1 if is_dead else 0
    os_time = (der - p['d_reinj']).days / 30.44 if der else 0

    tps_added = []
    for tp in ['J0','J14','M1','M3','M6','M9','M12']:
        if tp not in e['tps']: continue
        r, dm = e['tps'][tp]
        gn = glims_norm(r['Glims'])
        cfdna = fnum(r['Cell_Free_DNA'])
        if gn in vbg and cfdna and cfdna > 0:
            vaf_m = sum(vbg[gn]) / len(vbg[gn])
            heg_raw = vaf_m * cfdna
            if heg_raw > 0:
                heg_log_cal = math.log10(heg_raw) + offset
                heg_cal = 10**heg_log_cal
                mrd = 1
            else:
                heg_log_cal = -6; heg_cal = 0; mrd = 0
            records.append({
                'ID': i, 'randomisation': p['nom'],
                'time': round(TIME_VAL[tp], 4),
                'timepoint': tp, 'heg': round(heg_cal, 4),
                'heg_log': round(heg_log_cal, 4), 'mrd_pos': mrd,
                'efs_time': round(efs_time, 4), 'efs_event': efs_event,
                'os_time': round(os_time, 4), 'os_event': os_event,
            })
            tps_added.append(tp)
    if tps_added:
        print(f"{i:>3} {p['nom']:25} {p['type'][:10]:10} {len(tps_added):>5} {','.join(tps_added):25} {efs_time:>7.1f} {efs_event:>4} {os_time:>7.1f} {os_event:>5}")

print(f"\nTotal observations long : {len(records)}")
print(f"Patients with data : {len({r['ID'] for r in records})}")

# Distribution
tp_final = Counter(r['timepoint'] for r in records)
print(f"\nTimepoints in final dataset : {dict(sorted(tp_final.items(), key=lambda x: TIME_VAL.get(x[0], 99)))}")

# Save
import os
os.makedirs(OUT_DIR, exist_ok=True)
with open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['ID','randomisation','time','timepoint','heg','heg_log','mrd_pos','efs_time','efs_event','os_time','os_event'])
    w.writeheader()
    for r in records: w.writerow(r)
print(f"\n[OK] Written : {OUT_CSV}")
con.close()
