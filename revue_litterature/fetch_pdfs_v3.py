"""
V3 multi-sources legales : maximise la recuperation des PDFs.

Cascade en 5 niveaux :
  1. NCBI OA Bulk API (oa.fcgi)         - PDFs FTP des articles OA
  2. PMC HTML parsing                   - extrait le vrai lien PDF
  3. Unpaywall                          - Author Manuscripts, preprints
  4. Semantic Scholar API               - openAccessPdf field
  5. OpenAIRE API                       - agregateur europeen OA

Toutes les sources sont legales. Pour les articles non-OA :
- utiliser le VPN AP-HP ou abonnement personnel
- index.html genere donne acces a tous les liens directs
"""
import os
import sys
import json
import time
import re
import argparse
import requests
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).parent
REFS_DIR = BASE  # references.json dans le meme dossier

UA = {'User-Agent': 'ALYCANTE-research/3.0 (academic use)'}


def load_metadata():
    """Charge pmid -> pmc map depuis les batches si dispo."""
    pmc_map = {}
    for f in BASE.glob("batch*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                for r in json.load(fp):
                    if r.get('pmid') and r.get('pmc'):
                        pmc_map[r['pmid']] = r['pmc']
        except Exception:
            pass
    return pmc_map


def load_all_refs():
    """Charge les 120 references depuis les 3 fichiers."""
    paths = [
        REFS_DIR / "references.json",
        REFS_DIR / "references_v2.json",
        REFS_DIR / "references_v3.json",
        # fallback dans docgen/ si lance depuis un autre dossier
        Path(__file__).parent.parent / "docgen" / "references.json",
        Path(__file__).parent.parent / "docgen" / "references_v2.json",
        Path(__file__).parent.parent / "docgen" / "references_v3.json",
    ]
    all_refs = []
    seen_paths = set()
    for p in paths:
        if not p.exists() or str(p) in seen_paths:
            continue
        seen_paths.add(str(p))
        with open(p, 'r', encoding='utf-8') as fp:
            d = json.load(fp)
        for k in ('refs', 'additional_refs', 'additional_refs_v3'):
            if k in d:
                all_refs.extend(d[k])
    seen = set()
    unique = []
    for r in all_refs:
        if r.get('pmid') and r['pmid'] not in seen:
            seen.add(r['pmid'])
            unique.append(r)
    return sorted(unique, key=lambda x: x['id'])


def is_pdf(content):
    return content[:4] == b'%PDF'


def save_pdf(content, out_dir, pmid, suffix='OA'):
    out = out_dir / f"{pmid}_{suffix}.pdf"
    out.write_bytes(content)
    return out


# === Source 1 : NCBI OA Bulk API ===
def try_ncbi_oa_bulk(pmc_id, out_dir, session, pmid):
    """Utilise l'API officielle NCBI OA bulk qui renvoie l'URL du PDF."""
    pmc = pmc_id if pmc_id.startswith('PMC') else f'PMC{pmc_id}'
    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmc}"
    try:
        r = session.get(url, timeout=15, headers=UA)
        if r.status_code != 200:
            return None, f"OA bulk HTTP {r.status_code}"
        # Parse XML : <link format="pdf" href="..."/>
        m = re.search(r'<link\s+format="pdf"\s+href="([^"]+)"', r.text)
        if not m:
            # Format tgz fallback (contient le pdf)
            m_tgz = re.search(r'<link\s+format="tgz"\s+href="([^"]+)"', r.text)
            if not m_tgz:
                return None, "pas de lien PDF dans OA bulk"
            return None, "PDF dispo seulement dans tgz (skip)"
        pdf_url = m.group(1).replace('ftp://', 'https://')
        r2 = session.get(pdf_url, timeout=30, headers=UA)
        if r2.status_code == 200 and is_pdf(r2.content):
            return save_pdf(r2.content, out_dir, pmid, f"PMC_{pmc}"), f"NCBI OA bulk ({len(r2.content)//1024} KB)"
        return None, f"PDF inaccessible (HTTP {r2.status_code})"
    except Exception as e:
        return None, f"err NCBI OA: {type(e).__name__}"


# === Source 2 : PMC HTML parsing ===
def try_pmc_html(pmc_id, out_dir, session, pmid):
    """Parse la page HTML PMC pour trouver le vrai lien PDF."""
    pmc = pmc_id if pmc_id.startswith('PMC') else f'PMC{pmc_id}'
    article_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/"
    try:
        r = session.get(article_url, timeout=15, headers=UA, allow_redirects=True)
        if r.status_code != 200:
            return None, f"PMC HTML {r.status_code}"
        html = r.text
        # Cherche les patterns courants : /articles/PMC{ID}/pdf/{name}.pdf
        matches = re.findall(r'/articles/' + pmc + r'/pdf/[^"\s]+\.pdf', html)
        if not matches:
            # Pattern alternatif data-pdf-url ou href avec .pdf
            matches = re.findall(r'href="([^"]+\.pdf)"', html)
        if not matches:
            return None, "pas de lien PDF dans HTML"
        # Construire URL absolue
        pdf_path = matches[0]
        if pdf_path.startswith('/'):
            pdf_url = f"https://pmc.ncbi.nlm.nih.gov{pdf_path}"
        else:
            pdf_url = pdf_path
        r2 = session.get(pdf_url, timeout=30, headers=UA, allow_redirects=True)
        if r2.status_code == 200 and is_pdf(r2.content):
            return save_pdf(r2.content, out_dir, pmid, f"PMC_{pmc}_html"), f"PMC HTML ({len(r2.content)//1024} KB)"
        return None, f"PDF HTML {r2.status_code}"
    except Exception as e:
        return None, f"err PMC HTML: {type(e).__name__}"


# === Source 3 : Unpaywall ===
def try_unpaywall(doi, email, out_dir, session, pmid):
    if not doi:
        return None, "no DOI"
    try:
        r = session.get(f"https://api.unpaywall.org/v2/{doi}?email={email}", timeout=15, headers=UA)
        if r.status_code != 200:
            return None, f"UPW {r.status_code}"
        d = r.json()
        for loc in [d.get('best_oa_location')] + (d.get('oa_locations') or []):
            if not loc:
                continue
            pdf_url = loc.get('url_for_pdf') or loc.get('url')
            if not pdf_url:
                continue
            try:
                r2 = session.get(pdf_url, timeout=20, headers=UA, allow_redirects=True)
                if r2.status_code == 200 and is_pdf(r2.content):
                    return save_pdf(r2.content, out_dir, pmid, 'UPW'), f"Unpaywall {loc.get('host_type','?')} ({len(r2.content)//1024} KB)"
            except Exception:
                continue
        return None, "OA pas accessible"
    except Exception as e:
        return None, f"err UPW: {type(e).__name__}"


# === Source 4 : Semantic Scholar ===
def try_semantic_scholar(doi, out_dir, session, pmid):
    if not doi:
        return None, "no DOI"
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf,externalIds"
        r = session.get(url, timeout=15, headers=UA)
        if r.status_code != 200:
            return None, f"S2 {r.status_code}"
        d = r.json()
        oa = d.get('openAccessPdf') or {}
        pdf_url = oa.get('url')
        if not pdf_url:
            return None, "no S2 OA"
        r2 = session.get(pdf_url, timeout=20, headers=UA, allow_redirects=True)
        if r2.status_code == 200 and is_pdf(r2.content):
            return save_pdf(r2.content, out_dir, pmid, 'S2'), f"Semantic Scholar ({len(r2.content)//1024} KB)"
        return None, f"S2 PDF {r2.status_code}"
    except Exception as e:
        return None, f"err S2: {type(e).__name__}"


# === Source 5 : OpenAIRE ===
def try_openaire(doi, out_dir, session, pmid):
    if not doi:
        return None, "no DOI"
    try:
        url = f"https://api.openaire.eu/search/publications?doi={doi}&format=json"
        r = session.get(url, timeout=15, headers=UA)
        if r.status_code != 200:
            return None, f"OAIRE {r.status_code}"
        d = r.json()
        results = d.get('response', {}).get('results', {}).get('result', [])
        if not results:
            return None, "no OAIRE result"
        # Trouver instance avec full text
        for res in results[:3]:
            try:
                metadata = res.get('metadata', {}).get('oaf:entity', {}).get('oaf:result', {})
                instances = metadata.get('children', {}).get('instance', [])
                if not isinstance(instances, list):
                    instances = [instances]
                for inst in instances:
                    urls = inst.get('webresource', {})
                    if not isinstance(urls, list):
                        urls = [urls]
                    for u in urls:
                        web_url = u.get('url') if isinstance(u, dict) else None
                        if not web_url:
                            continue
                        try:
                            r2 = session.get(web_url, timeout=15, headers=UA, allow_redirects=True)
                            if r2.status_code == 200 and is_pdf(r2.content):
                                return save_pdf(r2.content, out_dir, pmid, 'OAIRE'), f"OpenAIRE ({len(r2.content)//1024} KB)"
                        except Exception:
                            continue
            except Exception:
                continue
        return None, "no OAIRE PDF"
    except Exception as e:
        return None, f"err OAIRE: {type(e).__name__}"


def generate_html_index(refs, results, out_dir, pmc_map):
    """HTML cliquable avec multiples sources legales par article."""
    n_ok = sum(1 for r in results if r['status'] == 'ok')
    html = ['<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">',
            '<title>ALYCANTE - 120 PDFs (multi-sources legales)</title>',
            '<style>',
            'body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:1200px;margin:0 auto;padding:20px;background:#f5f5f5}',
            'h1{color:#2F5496}',
            '.summary{background:white;padding:20px;border-radius:10px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.1);border-left:5px solid #2F5496}',
            '.article{background:white;padding:15px;margin:8px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08)}',
            '.article.ok{border-left:5px solid #1a7f37}',
            '.article.manq{border-left:5px solid #cf222e}',
            '.btn{display:inline-block;padding:6px 12px;background:#0969da;color:white;border-radius:4px;text-decoration:none;font-size:12px;margin:2px;font-weight:500}',
            '.btn:hover{filter:brightness(1.1)}',
            '.btn-pdf{background:#1a7f37}',
            '.btn-aphp{background:#cf222e}',
            '.btn-hal{background:#9d4edd}',
            '.btn-rg{background:#00ccc0}',
            '.btn-s2{background:#fb8c00}',
            '.title{font-weight:600;font-size:14px;margin:5px 0}',
            '.meta{font-size:12px;color:#666}',
            '</style></head><body>',
            f'<h1>Telechargement des 120 PDFs</h1>',
            f'<div class="summary"><p><strong>{n_ok}</strong> PDFs telecharges automatiquement, <strong>{len(refs)-n_ok}</strong> a recuperer.</p>',
            '<p>Pour chaque article manquant, cliquez sur les boutons dans l ordre :</p>',
            '<ol style="font-size:13px;color:#444"><li><strong>DOI</strong> : tente l acces editeur direct (marche si VPN AP-HP)</li>',
            '<li><strong>ResearchGate</strong> : demandez une copie a l auteur (reponse rapide)</li>',
            '<li><strong>HAL</strong> : archive ouverte francaise (Inserm/AP-HP y publient souvent)</li>',
            '<li><strong>S2</strong> : Semantic Scholar (parfois cache un PDF non liste par Unpaywall)</li>',
            '<li><strong>EPMC</strong> : Europe PMC, alternative a PubMed Central</li></ol></div>']

    by_pmid = {r['pmid']: r for r in results}
    for r in refs:
        pmid = r['pmid']
        doi = r.get('doi', '')
        res = by_pmid.get(pmid, {'status': 'manq', 'msg': '?'})
        is_ok = res['status'] == 'ok'
        cls = 'ok' if is_ok else 'manq'
        html.append(f'<div class="article {cls}">')
        html.append(f'<div class="meta">#{r["id"]} - {r["authors"][:60]} ({r["year"]}) - <em>{r["journal"]}</em></div>')
        html.append(f'<div class="title">{r["title"]}</div>')
        html.append(f'<div class="meta">PMID {pmid} - DOI <code>{doi}</code> - <small>{res.get("msg","")}</small></div>')
        html.append('<div style="margin-top:8px">')
        if is_ok and res.get('file'):
            fname = os.path.basename(res['file'])
            html.append(f'<a class="btn btn-pdf" href="pdfs/{fname}" download>📄 PDF local</a>')
        # Toujours afficher les sources externes
        html.append(f'<a class="btn" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank">PubMed</a>')
        if doi:
            html.append(f'<a class="btn btn-aphp" href="https://doi.org/{doi}" target="_blank">DOI (acces editeur)</a>')
            # ResearchGate via DOI
            html.append(f'<a class="btn btn-rg" href="https://www.researchgate.net/search/publication?q={doi}" target="_blank">ResearchGate</a>')
            # HAL
            html.append(f'<a class="btn btn-hal" href="https://hal.science/search/index/?q={doi}" target="_blank">HAL</a>')
            # Semantic Scholar
            html.append(f'<a class="btn btn-s2" href="https://www.semanticscholar.org/search?q={r["title"][:60]}" target="_blank">S2</a>')
        if pmc_map.get(pmid):
            pmc = pmc_map[pmid]
            html.append(f'<a class="btn" href="https://europepmc.org/article/MED/{pmid}" target="_blank">EPMC</a>')
            html.append(f'<a class="btn" href="https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/" target="_blank">PMC</a>')
        html.append('</div></div>')
    html.append('</body></html>')
    out = out_dir / 'index.html'
    out.write_text('\n'.join(html), encoding='utf-8')
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='pdfs_revue')
    parser.add_argument('--email', default='chercheur@aphp.fr')
    args = parser.parse_args()

    out_dir = Path(args.out)
    pdf_dir = out_dir / 'pdfs'
    pdf_dir.mkdir(parents=True, exist_ok=True)

    pmc_map = load_metadata()
    refs = load_all_refs()
    print(f"References : {len(refs)} | PMC IDs dispo : {len(pmc_map)}")

    session = requests.Session()
    stats = {'ncbi_oa': 0, 'pmc_html': 0, 'unpaywall': 0, 's2': 0, 'oaire': 0, 'cached': 0, 'manq': 0}
    results = []

    for i, r in enumerate(refs, 1):
        pmid = r['pmid']
        doi = r.get('doi', '')
        existing = list(pdf_dir.glob(f"{pmid}_*.pdf"))
        if existing:
            print(f"[{i:3d}/{len(refs)}] {pmid} CACHE ({existing[0].name})")
            results.append({'pmid': pmid, 'status': 'ok', 'file': str(existing[0]), 'msg': 'cache', 'source': 'cache'})
            stats['cached'] += 1
            continue

        title_short = r['title'][:50]
        print(f"[{i:3d}/{len(refs)}] {pmid} - {title_short}...", end=' ', flush=True)
        result = None

        # 1) NCBI OA bulk (officiel)
        pmc = pmc_map.get(pmid)
        if pmc:
            path, msg = try_ncbi_oa_bulk(pmc, pdf_dir, session, pmid)
            if path:
                print(f"OK NCBI-OA {msg}")
                results.append({'pmid': pmid, 'status': 'ok', 'file': str(path), 'msg': msg, 'source': 'ncbi_oa'})
                stats['ncbi_oa'] += 1
                time.sleep(0.4)
                continue
            # 2) PMC HTML parsing fallback
            path, msg = try_pmc_html(pmc, pdf_dir, session, pmid)
            if path:
                print(f"OK PMC-HTML {msg}")
                results.append({'pmid': pmid, 'status': 'ok', 'file': str(path), 'msg': msg, 'source': 'pmc_html'})
                stats['pmc_html'] += 1
                time.sleep(0.4)
                continue

        # 3) Unpaywall
        if doi:
            path, msg = try_unpaywall(doi, args.email, pdf_dir, session, pmid)
            if path:
                print(f"OK UPW {msg}")
                results.append({'pmid': pmid, 'status': 'ok', 'file': str(path), 'msg': msg, 'source': 'unpaywall'})
                stats['unpaywall'] += 1
                time.sleep(0.4)
                continue

        # 4) Semantic Scholar
        if doi:
            path, msg = try_semantic_scholar(doi, pdf_dir, session, pmid)
            if path:
                print(f"OK S2 {msg}")
                results.append({'pmid': pmid, 'status': 'ok', 'file': str(path), 'msg': msg, 'source': 's2'})
                stats['s2'] += 1
                time.sleep(0.4)
                continue

        # 5) OpenAIRE
        if doi:
            path, msg = try_openaire(doi, pdf_dir, session, pmid)
            if path:
                print(f"OK OAIRE {msg}")
                results.append({'pmid': pmid, 'status': 'ok', 'file': str(path), 'msg': msg, 'source': 'oaire'})
                stats['oaire'] += 1
                time.sleep(0.4)
                continue

        print(f"MANQ")
        results.append({'pmid': pmid, 'status': 'manq', 'msg': msg if 'msg' in dir() else 'no source', 'source': 'none'})
        stats['manq'] += 1
        time.sleep(0.3)

    # Generer outputs
    idx = generate_html_index(refs, results, out_dir, pmc_map)
    with open(out_dir / 'manifest.json', 'w', encoding='utf-8') as f:
        json.dump({'total': len(refs), 'stats': stats, 'results': results}, f, indent=2)

    print()
    print('=' * 60)
    print(f"TOTAL : {len(refs)} references")
    for k, v in stats.items():
        if v:
            print(f"  {k:15s} : {v:3d} ({100*v/len(refs):.0f} %)")
    total_ok = sum(v for k, v in stats.items() if k != 'manq')
    print(f"  TOTAL automatique : {total_ok}/{len(refs)} ({100*total_ok/len(refs):.0f} %)")
    print('=' * 60)
    print(f"Index : {idx}")


if __name__ == '__main__':
    main()
