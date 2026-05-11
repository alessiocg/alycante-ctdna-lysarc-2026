"""
Recuperation automatique des PDFs pour les 120 references de la revue ALYCANTE.

Strategie en 4 niveaux :
  1. PubMed Central (PMC) - articles open access, telechargement direct gratuit
  2. Unpaywall API - trouve les versions OA legales (Author Manuscript, preprint)
  3. Genere index.html avec liens DOI cliquables -> ouverture via BiblioInserm/Click&Read
  4. Genere fichiers RIS + BibTeX pour import Zotero/EndNote

Usage:
    python fetch_pdfs.py [--out OUT_DIR] [--email YOUR_EMAIL]

Required: requests
    pip install requests
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installez d abord: pip install requests")
    sys.exit(1)

# Configuration
DEFAULT_REFS = [
    Path(__file__).parent.parent / "docgen" / "references.json",
    Path(__file__).parent.parent / "docgen" / "references_v2.json",
    Path(__file__).parent.parent / "docgen" / "references_v3.json",
]


def load_all_refs(paths):
    """Charge les 120 references depuis les 3 fichiers json."""
    all_refs = []
    for p in paths:
        if not p.exists():
            print(f"  [skip] {p} introuvable")
            continue
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        # cle peut etre 'refs' ou 'additional_refs' ou 'additional_refs_v3'
        for k in ("refs", "additional_refs", "additional_refs_v3"):
            if k in d:
                all_refs.extend(d[k])
    # deduplication par PMID
    seen = set()
    unique = []
    for r in all_refs:
        pmid = r.get("pmid")
        if pmid and pmid not in seen:
            seen.add(pmid)
            unique.append(r)
    return sorted(unique, key=lambda x: x["id"])


def try_pmc_pdf(pmid, out_dir, session):
    """Tente le telechargement du PDF via PMC (Europe PMC mirror, sans cle API NCBI)."""
    # 1) Resoudre PMID -> PMC ID via NCBI elink (no key needed for low volume)
    elink_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        f"?dbfrom=pubmed&db=pmc&id={pmid}&retmode=json"
    )
    try:
        r = session.get(elink_url, timeout=10)
        if r.status_code != 200:
            return None, "elink HTTP error"
        data = r.json()
        # Parcourir la reponse pour trouver pmcid
        pmc_id = None
        for linkset in data.get("linksets", []):
            for ldb in linkset.get("linksetdbs", []):
                if ldb.get("dbto") == "pmc" and ldb.get("links"):
                    pmc_id = ldb["links"][0]
                    break
            if pmc_id:
                break
        if not pmc_id:
            return None, "pas de PMC ID"

        # 2) Tentative de DL via Europe PMC (PDF direct)
        # Format: https://europepmc.org/articles/PMC1234567/pdf/{filename}.pdf
        # Plus simple: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC{id}/fullTextPDF
        pmc_full_id = f"PMC{pmc_id}" if not str(pmc_id).startswith("PMC") else pmc_id
        pdf_url = f"https://europepmc.org/articles/{pmc_full_id}?pdf=render"
        # Note: Europe PMC PDF URL pattern
        pdf_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmc_full_id}&blobtype=pdf"

        r2 = session.get(pdf_url, timeout=30, allow_redirects=True)
        if r2.status_code == 200 and r2.headers.get("Content-Type", "").startswith("application/pdf"):
            pdf_path = out_dir / f"{pmid}_PMC{pmc_id}.pdf"
            pdf_path.write_bytes(r2.content)
            return pdf_path, f"PMC{pmc_id} (Europe PMC, {len(r2.content) // 1024} KB)"
        else:
            return None, f"PMC{pmc_id} trouve mais PDF inaccessible (HTTP {r2.status_code})"
    except Exception as e:
        return None, f"erreur: {e}"


def try_unpaywall(doi, email, out_dir, session, pmid):
    """Tente Unpaywall pour version Open Access legale."""
    if not doi:
        return None, "pas de DOI"
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None, f"Unpaywall HTTP {r.status_code}"
        data = r.json()
        best_oa = data.get("best_oa_location") or {}
        pdf_url = best_oa.get("url_for_pdf") or best_oa.get("url")
        if not pdf_url:
            return None, "pas d OA gratuit"
        r2 = session.get(pdf_url, timeout=30, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r2.status_code == 200 and (
            r2.headers.get("Content-Type", "").startswith("application/pdf") or
            r2.content[:4] == b"%PDF"
        ):
            pdf_path = out_dir / f"{pmid}_OA.pdf"
            pdf_path.write_bytes(r2.content)
            return pdf_path, f"Unpaywall ({best_oa.get('host_type', 'unknown')}, {len(r2.content) // 1024} KB)"
        return None, f"OA URL inaccessible (HTTP {r2.status_code})"
    except Exception as e:
        return None, f"erreur Unpaywall: {e}"


def generate_index_html(refs, results, out_dir):
    """Genere une page HTML avec liens DOI cliquables pour les articles manquants."""
    html_lines = [
        "<!DOCTYPE html>",
        '<html lang="fr">',
        "<head>",
        '<meta charset="UTF-8">',
        "<title>Revue ALYCANTE - Index des references</title>",
        "<style>",
        "body{font-family:Calibri,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;color:#222}",
        "h1{color:#2F5496;border-bottom:2px solid #2F5496;padding-bottom:.3em}",
        "h2{color:#2F5496;margin-top:2em}",
        "table{border-collapse:collapse;width:100%;font-size:13px;margin-top:1em}",
        "th{background:#2F5496;color:white;padding:8px;text-align:left;position:sticky;top:0}",
        "td{padding:6px;border-bottom:1px solid #eee;vertical-align:top}",
        "tr:hover{background:#f5f9ff}",
        ".ok{color:#1a7f37;font-weight:bold}",
        ".manq{color:#cf222e;font-weight:bold}",
        "a{color:#0969da;text-decoration:none}",
        "a:hover{text-decoration:underline}",
        ".btn{display:inline-block;padding:3px 8px;background:#0969da;color:white;",
        "  border-radius:4px;font-size:11px;margin:1px;text-decoration:none}",
        ".btn:hover{background:#0860c4;text-decoration:none}",
        ".btn-pmc{background:#1a7f37}",
        ".btn-aphp{background:#cf222e}",
        ".summary{background:#f5f9ff;border-left:4px solid #2F5496;padding:1em;margin:1.5em 0}",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Revue ALYCANTE — Index des 120 references PubMed</h1>",
        "<div class='summary'>",
    ]

    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_manq = len(results) - n_ok
    html_lines.append(f"<p><strong>Resultats :</strong> {n_ok} PDFs telecharges automatiquement, "
                      f"{n_manq} a recuperer manuellement via BiblioInserm.</p>")
    html_lines.append(
        "<p><strong>Mode d emploi pour les articles manquants</strong> (necessite credentials AP-HP / Inserm) :</p>"
        "<ol>"
        "<li><strong>Option A — extension Click &amp; Read</strong> "
        "(<a href='https://www.biblioinserm.fr/click-and-read'>install</a>) : cliquez sur le DOI ci-dessous, "
        "l extension detecte automatiquement et offre le PDF si abonnement Inserm/AP-HP.</li>"
        "<li><strong>Option B — BiblioInserm direct</strong> "
        "(<a href='https://www.biblioinserm.inserm.fr/'>portail</a>) : authentification puis recherche par DOI.</li>"
        "<li><strong>Option C — Zotero</strong> : importez le fichier "
        "<code>references.ris</code> genere, puis utilisez \"Find Available PDF\" "
        "apres avoir configure le proxy AP-HP dans Zotero (Preferences &gt; Advanced &gt; Config Editor : "
        "<code>extensions.zotero.proxies.autoRecognize</code>).</li>"
        "</ol>"
        "</div>"
    )
    html_lines.append("<h2>Table des references</h2>")
    html_lines.append("<table>")
    html_lines.append("<thead><tr>")
    html_lines.append("<th>#</th><th>Auteurs / Annee</th><th>Titre / Journal</th>"
                      "<th>Statut PDF</th><th>Acces</th>")
    html_lines.append("</tr></thead><tbody>")

    res_by_pmid = {r["pmid"]: r for r in results}
    for r in refs:
        pmid = r["pmid"]
        result = res_by_pmid.get(pmid, {"status": "manq", "msg": "non traite"})
        title = r["title"]
        # Buttons
        btns = []
        btns.append(f'<a class="btn" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" '
                    f'target="_blank" title="PubMed">PubMed</a>')
        btns.append(f'<a class="btn" href="https://doi.org/{r["doi"]}" '
                    f'target="_blank" title="DOI">DOI</a>')
        if result["status"] == "ok":
            local_pdf = result.get("file")
            if local_pdf:
                btns.append(f'<a class="btn btn-pmc" href="pdfs/{os.path.basename(local_pdf)}" '
                            f'target="_blank">PDF local</a>')
            status_html = f'<span class="ok">OK</span><br><small>{result.get("msg", "")}</small>'
        else:
            status_html = f'<span class="manq">A faire</span><br><small>{result.get("msg", "")}</small>'
            # Lien BiblioInserm direct
            btns.append(f'<a class="btn btn-aphp" '
                        f'href="https://www.biblioinserm.inserm.fr/login?url=https://doi.org/{r["doi"]}" '
                        f'target="_blank" title="BiblioInserm">BiblioInserm</a>')

        html_lines.append("<tr>")
        html_lines.append(f"<td>{r['id']}</td>")
        html_lines.append(f"<td>{r['authors'][:80]}<br><small>{r['year']}</small></td>")
        html_lines.append(f"<td>{title}<br><small><em>{r['journal']}. "
                          f"{r.get('vol', '')}</em></small></td>")
        html_lines.append(f"<td>{status_html}</td>")
        html_lines.append(f"<td>{''.join(btns)}</td>")
        html_lines.append("</tr>")

    html_lines.extend(["</tbody>", "</table>", "</body>", "</html>"])
    out = out_dir / "index.html"
    out.write_text("\n".join(html_lines), encoding="utf-8")
    return out


def generate_ris(refs, out_dir):
    """Genere fichier RIS pour import Zotero/EndNote."""
    lines = []
    for r in refs:
        lines.append("TY  - JOUR")
        lines.append(f"ID  - {r['pmid']}")
        # Authors
        for a in r.get("authors", "").split("; "):
            if a.strip():
                lines.append(f"AU  - {a.strip()}")
        lines.append(f"TI  - {r['title']}")
        lines.append(f"JO  - {r['journal']}")
        lines.append(f"PY  - {r['year']}")
        if r.get("vol"):
            lines.append(f"VL  - {r['vol']}")
        if r.get("doi"):
            lines.append(f"DO  - {r['doi']}")
        if r.get("pmid"):
            lines.append(f"AN  - {r['pmid']}")
        lines.append(f"UR  - https://doi.org/{r['doi']}")
        lines.append("ER  - ")
        lines.append("")
    out = out_dir / "references.ris"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def generate_bibtex(refs, out_dir):
    """Genere fichier BibTeX."""
    lines = []
    for r in refs:
        first_author = r["authors"].split(";")[0].split()[0].lower() if r.get("authors") else "anon"
        key = f"{first_author}{r['year']}_{r['pmid']}"
        lines.append(f"@article{{{key},")
        lines.append(f"  author = {{{r.get('authors', '').replace(';', ' and')}}},")
        lines.append(f"  title = {{{r['title']}}},")
        lines.append(f"  journal = {{{r['journal']}}},")
        lines.append(f"  year = {{{r['year']}}},")
        if r.get("vol"):
            lines.append(f"  volume = {{{r['vol']}}},")
        lines.append(f"  doi = {{{r['doi']}}},")
        lines.append(f"  pmid = {{{r['pmid']}}},")
        lines.append("}")
        lines.append("")
    out = out_dir / "references.bib"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="pdfs_revue_alycante",
                        help="Dossier de sortie (default: pdfs_revue_alycante)")
    parser.add_argument("--email", default="anonymous@example.com",
                        help="Email pour l API Unpaywall (obligatoire)")
    parser.add_argument("--no-unpaywall", action="store_true",
                        help="Desactive la tentative Unpaywall (PMC seulement)")
    parser.add_argument("--refs", nargs="*", help="Chemins vers fichiers references.json")
    args = parser.parse_args()

    out_dir = Path(args.out)
    pdf_dir = out_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    ref_paths = [Path(p) for p in args.refs] if args.refs else DEFAULT_REFS
    refs = load_all_refs(ref_paths)
    print(f"Charges {len(refs)} references uniques")

    session = requests.Session()
    session.headers.update({"User-Agent": "ALYCANTE-PDF-fetcher/1.0 (research)"})

    results = []
    for i, r in enumerate(refs, 1):
        pmid = r["pmid"]
        doi = r.get("doi", "")
        print(f"[{i:3d}/{len(refs)}] PMID {pmid} - {r['title'][:60]}...", end=" ", flush=True)

        # 1) Tentative PMC
        path, msg = try_pmc_pdf(pmid, pdf_dir, session)
        if path:
            print(f"OK ({msg})")
            results.append({"pmid": pmid, "status": "ok", "file": str(path), "msg": msg})
            time.sleep(0.5)  # respecter NCBI rate limit
            continue

        # 2) Tentative Unpaywall
        if not args.no_unpaywall and doi:
            path2, msg2 = try_unpaywall(doi, args.email, pdf_dir, session, pmid)
            if path2:
                print(f"OK Unpaywall ({msg2})")
                results.append({"pmid": pmid, "status": "ok", "file": str(path2), "msg": msg2})
                time.sleep(0.3)
                continue

        # 3) Manquant
        print(f"a faire manuellement ({msg})")
        results.append({"pmid": pmid, "status": "manq", "msg": msg})
        time.sleep(0.3)

    # Generer les fichiers d export
    print("\nGeneration des fichiers d index...")
    idx_path = generate_index_html(refs, results, out_dir)
    print(f"  Index HTML : {idx_path}")
    ris_path = generate_ris(refs, out_dir)
    print(f"  RIS (Zotero/EndNote) : {ris_path}")
    bib_path = generate_bibtex(refs, out_dir)
    print(f"  BibTeX : {bib_path}")

    # Manifest des resultats
    manifest = out_dir / "manifest.json"
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump({"total": len(refs), "results": results}, f, indent=2)

    # Sommaire
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_manq = len(results) - n_ok
    print()
    print(f"=== Resume ===")
    print(f"  Total : {len(refs)} references")
    print(f"  PDFs telecharges automatiquement : {n_ok} ({100*n_ok/len(refs):.0f} %)")
    print(f"  A recuperer manuellement via BiblioInserm : {n_manq} ({100*n_manq/len(refs):.0f} %)")
    print()
    print(f"Ouvrir {idx_path} dans un navigateur pour les telecharger.")
    print(f"OU importer {ris_path} dans Zotero puis 'Find Available PDF'.")


if __name__ == "__main__":
    main()
