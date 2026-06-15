# -*- coding: utf-8 -*-
"""
V4 rebuild — Cohorte de validation routine (CAR-T DLBCL : axi-cel / tisa-cel / liso-cel).
SOURCE UNIQUE, recette PROPRE (aucun hack : pas d'offset de calibration, pas d'anti-log,
pas de floor -6) :
  variants tumoraux = font rouge (FFFF0000) sinon PREDICTED=Mutation / is_mutation=1,
                      FILTRES : VAF>0.35 (germinal/CH haut-VAF), gnomAD>0.001 (polymorphisme),
                                genes CHIP stricts exclus.
  MRD+ : heg = log10( VAF_moyenne_filtree x Cell_Free_DNA )      [Cell_Free_DNA deja en hEG]
  MRD- : heg = log10( Cell_Free_DNA / Profondeur_UMI )           [floor B = LOD per-sample]
Sortie ANONYMISEE (identifiants LEA001..) ; mapping nom<->LEAxxx ecrit a part (PRIVE).
Toutes les sorties vont dans input/ (git-ignore : PHI / patient-level), jamais commitees.

Chemin DB : variable d'env NGS_DB_CACHE, sinon input/ngs_database.db (aucun chemin utilisateur en dur).
"""
import os, sys, sqlite3, openpyxl, re, unicodedata, csv, math
from datetime import datetime, timedelta
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import input_path
sys.stdout.reconfigure(encoding='utf-8')

DB  = os.environ.get('NGS_DB_CACHE', input_path('ngs_database.db'))
LEA = input_path('Base_CART.xlsx')
OUT_INP     = input_path('lea_all_jlcm_input.csv')       # anonymise, PHI -> git-ignore
OUT_INFO    = input_path('lea_all_jlcm_info.csv')        # anonymise (covariables), git-ignore
OUT_MAPPING = input_path('lea_id_mapping_PRIVE.csv')     # PRIVE : nom<->LEAxxx, NE JAMAIS versionner

CH_GENES = {'TET2', 'DNMT3A', 'ASXL1', 'PPM1D', 'GNB1', 'CBL', 'SF3B1', 'SRSF2'}    # CHIP non drivers lymphome
VAF_GERMLINE = 0.35
GNOMAD_MAX   = 0.001
PROF_UMI_FALLBACK = 5e4

def norm(s):
    if s is None: return ''
    s = str(s).strip().upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 -]', '', s)).strip()
def td(v):
    if v is None: return None
    if isinstance(v, datetime): return v
    if isinstance(v, str):
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y'):
            try: return datetime.strptime(v.strip(), fmt)
            except: pass
    return None
def fnum(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip().replace(',', '.').replace(' ', '').replace('%', '')
    try: return float(s)
    except: return None
def glims_norm(gl):
    return None if gl is None else str(gl).replace('-', '').strip()

wb = openpyxl.load_workbook(LEA, data_only=True); ws = wb['Generalites']
rows = list(ws.iter_rows(values_only=True)); hdr = rows[0]
c = {n: hdr.index(n) for n in ['Nom', 'DDN', 'Date_reinjection', 'Type_CART', 'Lignes_avantCART',
                                'OMS2016', 'AutogreffeL1', 'Statut_der.nouv', 'Date_der.nouv',
                                'Date.rechute', 'Cause_deces', 'Centre', 'Brige', 'IPI.diag', 'Sexe']}
lea = []; type_counter = {}
for r in rows[1:]:
    nm = r[c['Nom']]
    if not nm: continue
    dr = td(r[c['Date_reinjection']])
    if not dr: continue
    type_c = str(r[c['Type_CART']] or '').strip(); oms = str(r[c['OMS2016']] or '')
    type_counter[type_c] = type_counter.get(type_c, 0) + 1
    if 'DLBCL' not in oms.upper(): continue
    ddn = td(r[c['DDN']]); age = (dr - ddn).days / 365.25 if ddn else None
    lea.append({'nom': str(nm), 'nom_n': norm(nm), 'ddn': ddn, 'age': age, 'd_reinj': dr,
                'type': type_c, 'lignes': r[c['Lignes_avantCART']], 'autoL1': str(r[c['AutogreffeL1']] or ''),
                'oms': oms, 'statut': str(r[c['Statut_der.nouv']] or ''), 'der': td(r[c['Date_der.nouv']]),
                'rechute': td(r[c['Date.rechute']]), 'cause': str(r[c['Cause_deces']] or ''),
                'centre': str(r[c['Centre']] or ''), 'bridge': str(r[c['Brige']] or ''),
                'ipi': r[c['IPI.diag']], 'sexe': str(r[c['Sexe']] or '')})
print(f"Lea DLBCL (toutes CAR-T) : {len(lea)}")
print(f"Distribution Type_CART DLBCL : {Counter(p['type'] for p in lea)}")

conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row; cur = conn.cursor()
noms_lea = tuple(p['nom'].upper() for p in lea); ph = ','.join('?' * len(noms_lea))
clin = cur.execute(f"""SELECT Glims, NOM, DDN, DDN_glims, date_prelevement_imputee,
                              Cell_Free_DNA, Profondeur_UMI
                       FROM patients_clinical WHERE UPPER(NOM) IN ({ph})""", noms_lea).fetchall()
clin_by_name = {}
for r in clin: clin_by_name.setdefault(norm(r['NOM']), []).append(r)

elig = []
for p in lea:
    cands = clin_by_name.get(p['nom_n'], [])
    if p['ddn']:
        cm = [r for r in cands if (td(r['DDN']) and abs((td(r['DDN']) - p['ddn']).days) <= 2)
              or (td(r['DDN_glims']) and abs((td(r['DDN_glims']) - p['ddn']).days) <= 2)]
        if cm: cands = cm
    d0 = p['d_reinj']; d14 = d0 + timedelta(days=14); j0 = j14 = None
    for r in cands:
        d_pr = td(r['date_prelevement_imputee'])
        if not d_pr: continue
        delta0 = (d_pr - d0).days
        if -30 <= delta0 <= 3 and (j0 is None or abs(delta0) < abs((td(j0['date_prelevement_imputee']) - d0).days)): j0 = r
        if 5 <= delta0 <= 28 and (j14 is None or abs((d_pr - d14).days) < abs((td(j14['date_prelevement_imputee']) - d14).days)): j14 = r
    if j0 and j14: elig.append({'p': p, 'j0': j0, 'j14': j14})
print(f"Lea DLBCL avec NGS J0 ET J14 : {len(elig)}")
print(f"  par Type_CART : {Counter(e['p']['type'] for e in elig)}")

glims_set = set()
for e in elig: glims_set.add(glims_norm(e['j0']['Glims'])); glims_set.add(glims_norm(e['j14']['Glims']))
ph2 = ','.join('?' * len(glims_set))
rows_var = cur.execute(f"""SELECT glims_norm, VAF, vaf_font_color, PREDICTED, is_mutation,
                                  Gene_symbol, gnomad_genomes_AF, gnomad_exomes_AF
                           FROM variants_full_materialized
                           WHERE glims_norm IN ({ph2})
                             AND (vaf_font_color='FFFF0000' OR PREDICTED='Mutation' OR is_mutation='1')
                             AND is_best_run=1""", tuple(glims_set)).fetchall()
by_glims_raw = {}
for r in rows_var: by_glims_raw.setdefault(r['glims_norm'], []).append(r)

def filtered_vafs(gn):
    rs = by_glims_raw.get(gn, [])
    rouge = [r for r in rs if r['vaf_font_color'] == 'FFFF0000']
    chosen = rouge if rouge else [r for r in rs if r['PREDICTED'] == 'Mutation' or str(r['is_mutation']) == '1']
    vafs = []
    for r in chosen:
        v = fnum(r['VAF'])
        if v is None or v > VAF_GERMLINE: continue
        g = fnum(r['gnomad_genomes_AF']) or fnum(r['gnomad_exomes_AF'])
        if g and g > GNOMAD_MAX: continue
        if str(r['Gene_symbol']) in CH_GENES: continue
        vafs.append(v)
    return vafs

records = []; info = []; mapping = []; n_both = 0; npos = Counter(); nneg = Counter()
for i, e in enumerate(elig, 1):
    p = e['p']; lid = f"LEA{i:03d}"
    mapping.append({'LEA_ID': lid, 'nom': p['nom']})
    rechute = p['rechute']; der = p['der']
    sn = ''.join(ch for ch in unicodedata.normalize('NFD', p['statut']) if unicodedata.category(ch) != 'Mn').lower()
    is_dead = any(x in sn for x in ('dece', 'decede', 'dcd', 'mort'))
    is_relapse = any(x in sn for x in ('rechute', 'progress', 'recidive'))
    efs_event = 1 if (rechute is not None or is_dead or is_relapse) else 0
    if rechute is not None and rechute > p['d_reinj']: efs_time = (rechute - p['d_reinj']).days / 30.44
    elif der is not None: efs_time = (der - p['d_reinj']).days / 30.44
    else: efs_time = 0
    os_event = 1 if is_dead else 0
    os_time = (der - p['d_reinj']).days / 30.44 if der else 0
    has_j0 = has_j14 = False; j0_h = j14_h = None
    for tp, j in [('J0', e['j0']), ('J14', e['j14'])]:
        gn = glims_norm(j['Glims']); cfdna = fnum(j['Cell_Free_DNA']); prof = fnum(j['Profondeur_UMI'])
        if not cfdna or cfdna <= 0: continue
        vafs = filtered_vafs(gn); vaf_m = (sum(vafs) / len(vafs)) if vafs else 0.0
        if vaf_m > 0:
            heg = round(math.log10(vaf_m * cfdna), 4); mrd = 1; npos[tp] += 1
        else:                                            # MRD- -> floor B (LOD per-sample), JAMAIS -6
            p_used = prof if (prof and prof > 0) else PROF_UMI_FALLBACK
            heg = round(math.log10(cfdna / p_used), 4); mrd = 0; nneg[tp] += 1
        time_m = 0.0 if tp == 'J0' else 14 / 30.44
        records.append({'ID': i, 'randomisation': lid, 'time': round(time_m, 4), 'timepoint': tp,
                        'heg': heg, 'mrd_pos': mrd, 'vaf_moy_filtree': round(vaf_m, 5), 'n_var_kept': len(vafs),
                        'profondeur_umi': prof, 'efs_time': round(efs_time, 4), 'efs_event': efs_event,
                        'os_time': round(os_time, 4), 'os_event': os_event})
        if tp == 'J0': has_j0 = True; j0_h = heg
        else: has_j14 = True; j14_h = heg
    if has_j0 and has_j14: n_both += 1
    info.append({'ID': i, 'LEA_ID': lid, 'type': p['type'], 'lignes': p['lignes'], 'autoL1': p['autoL1'],
                 'age': round(p['age'], 1) if p['age'] else None, 'sexe': p['sexe'], 'ipi': p['ipi'],
                 'bridge': p['bridge'], 'centre': p['centre'], 'has_both': has_j0 and has_j14,
                 'efs_time': round(efs_time, 2), 'efs_event': efs_event, 'os_time': round(os_time, 2), 'os_event': os_event})
conn.close()

with open(OUT_INP, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['ID', 'randomisation', 'time', 'timepoint', 'heg', 'mrd_pos', 'vaf_moy_filtree',
                                      'n_var_kept', 'profondeur_umi', 'efs_time', 'efs_event', 'os_time', 'os_event'])
    w.writeheader(); w.writerows(records)
with open(OUT_INFO, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(info[0].keys()), delimiter=';'); w.writeheader(); w.writerows(info)
with open(OUT_MAPPING, 'w', encoding='utf-8', newline='') as f:        # PRIVE
    w = csv.DictWriter(f, fieldnames=['LEA_ID', 'nom']); w.writeheader(); w.writerows(mapping)

print(f"\nMRD+ J0={npos['J0']} J14={npos['J14']} | MRD- J0={nneg['J0']} J14={nneg['J14']}")
print(f"heg J0 ET J14 complet : {n_both}/{len(elig)}")
print(f"CSV (anonymise) : {OUT_INP}")
