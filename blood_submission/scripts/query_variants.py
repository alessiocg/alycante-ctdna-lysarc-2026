# -*- coding: utf-8 -*-
"""Query variants for the 3 reclassified Lea patients."""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'C:/Users/4067048/AppData/Local/Temp/ngs_database_local_cache.db'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

CHIP_GENES = {'TP53','DNMT3A','TET2','ASXL1','PPM1D','SRSF2','JAK2','SF3B1','U2AF1','IDH1','IDH2'}

patients = ['B','C','A']
for pat in patients:
    print(f'\n=== {pat} ===')
    rows = con.execute('''
        SELECT pc.Glims, pc.date_prelevement_imputee as dt, pc.PROJET, pc.Cell_Free_DNA,
               v.Gene_symbol, v.VAF, v.vaf_font_color, v.PREDICTED, v.is_mutation, v.hgvs_p
        FROM patients_clinical pc
        LEFT JOIN variants_full_materialized v ON pc.glims_norm = v.glims_norm AND v.is_best_run=1
        WHERE UPPER(pc.NOM) = ? AND pc.PROJET LIKE 'CART%'
        ORDER BY pc.date_prelevement_imputee, v.Gene_symbol
    ''', (pat,)).fetchall()

    by_tp = {}
    for r in rows:
        if not r['dt']: continue
        tp_key = (r['dt'][:10], r['PROJET'])
        if tp_key not in by_tp:
            by_tp[tp_key] = {'cfDNA': r['Cell_Free_DNA'], 'variants': []}
        if r['Gene_symbol']:
            color = 'ROUGE' if r['vaf_font_color']=='FFFF0000' else ('mut' if r['PREDICTED']=='Mutation' else '-')
            is_chip = 'CHIP?' if r['Gene_symbol'] in CHIP_GENES else ''
            by_tp[tp_key]['variants'].append({
                'gene': r['Gene_symbol'], 'hgvs': r['hgvs_p'] or '',
                'vaf': r['VAF'], 'color': color, 'chip': is_chip
            })

    for (dt, projet), data in sorted(by_tp.items()):
        n_var = len(data['variants'])
        n_rouge = sum(1 for v in data['variants'] if v['color']=='ROUGE')
        n_chip = sum(1 for v in data['variants'] if v['chip'])
        cfdna = data['cfDNA'] or '?'
        print(f"  {dt} {projet:10} cfDNA={cfdna} | n_variants={n_var}, n_rouge={n_rouge}, n_chip_gene={n_chip}")
        for v in data['variants'][:15]:
            print(f"     {v['gene']:8} {v['hgvs'][:25]:25} VAF={str(v['vaf'] or '?'):>8} [{v['color']:5}] {v['chip']}")
        if len(data['variants']) > 15:
            print(f"     ... ({len(data['variants'])-15} more)")
con.close()
