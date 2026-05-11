"""
Fusion index.html (multi-sources) + telecharger.html (design soigne).
Detecte automatiquement TOUS les PDFs presents (PMID_* + noms manuels via DOI).
"""
import os, re, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

PDF_DIR = Path(r"//Hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/protocole ALYCANTE/Réunion LYSARC 2026/output/pdfs_revue_litterature")
PDFS = PDF_DIR / "pdfs"
DOCGEN = Path("C:/Users/4067048/AppData/Local/Temp/alycante_lit/docgen")

# Charge refs
refs = []
for fp in [DOCGEN/"references.json", DOCGEN/"references_v2.json", DOCGEN/"references_v3.json"]:
    with open(fp, encoding='utf-8') as f:
        d = json.load(f)
    for k in ('refs','additional_refs','additional_refs_v3'):
        if k in d: refs.extend(d[k])
seen = set(); unique_refs = []
for r in refs:
    if r.get('pmid') and r['pmid'] not in seen:
        seen.add(r['pmid'])
        unique_refs.append(r)
unique_refs.sort(key=lambda x: x['id'])

# PMC IDs depuis les batches
pmc_map = {}
for f in Path("C:/Users/4067048/AppData/Local/Temp/alycante_lit").glob("batch*.json"):
    try:
        with open(f, encoding='utf-8') as fp:
            for r in json.load(fp):
                if r.get('pmid') and r.get('pmc'):
                    pmc_map[r['pmid']] = r['pmc']
    except: pass

# Liste tous les fichiers PDF du dossier
files = sorted(os.listdir(PDFS))
pdf_by_pmid = {}  # pmid -> filename
extra_files = []

# 1) Fichiers PMID_*.pdf : direct
pmid_pat = re.compile(r'^(\d{7,8})_')
for f in files:
    m = pmid_pat.match(f)
    if m:
        pdf_by_pmid[m.group(1)] = f
    else:
        extra_files.append(f)

# 2) Match les fichiers extras via DOI
doi_to_pmid = {r.get('doi','').lower(): r['pmid'] for r in unique_refs if r.get('doi')}
for f in extra_files:
    f_lower = f.lower().replace('_','-').replace('.','-')
    matched = None
    for doi, pmid in doi_to_pmid.items():
        doi_tail = doi.split('/')[-1].replace('.','-').lower()
        parts = [p for p in doi_tail.split('-') if len(p) > 6]
        if any(p in f_lower for p in parts) or doi_tail in f_lower:
            matched = pmid
            break
    # Match par nom d'auteur si nom du fichier contient "kurtz-et-al-2018"
    if not matched:
        for r in unique_refs:
            first_author_last = r.get('authors','').split(';')[0].split()[0].lower() if r.get('authors') else ''
            year = str(r.get('year',''))
            if first_author_last and year and first_author_last in f_lower and year in f_lower:
                matched = r['pmid']
                break
    if matched and matched not in pdf_by_pmid:
        pdf_by_pmid[matched] = f
    elif matched:
        # PMID deja couvert par un fichier PMID_*, on laisse
        pass

n_ok = len(pdf_by_pmid)
n_manq = len(unique_refs) - n_ok

# Generation HTML
HTML = []
HTML.append('''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>ALYCANTE - Index unifié des 120 PDFs</title>
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #222; }
h1 { color: #2F5496; }
.summary { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;
           box-shadow: 0 2px 8px rgba(0,0,0,.1); border-left: 5px solid #2F5496; }
.legend { display: flex; gap: 12px; margin: 12px 0; flex-wrap: wrap; }
.legend-item { padding: 4px 10px; border-radius: 14px; font-size: 12px; font-weight: 600; }
.article { background: white; padding: 13px 18px; margin: 8px 0; border-radius: 8px;
           box-shadow: 0 1px 3px rgba(0,0,0,.08);
           display: flex; gap: 15px; align-items: flex-start; }
.article.dispo { border-left: 5px solid #1a7f37; }
.article.manq { border-left: 5px solid #cf222e; }
.info { flex: 1; min-width: 0; }
.id-badge { display: inline-block; padding: 2px 7px; background: #2F5496; color: white;
            border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 6px; }
.title { font-weight: 600; color: #222; margin: 3px 0; font-size: 14px; line-height: 1.3; }
.meta { font-size: 11.5px; color: #666; line-height: 1.4; }
.actions { display: flex; flex-direction: column; gap: 4px; min-width: 200px; }
.btn { display: block; padding: 7px 12px; border-radius: 5px; text-decoration: none;
       font-weight: 600; font-size: 12px; text-align: center; transition: filter .12s;
       color: white; }
.btn:hover { filter: brightness(1.1); }
.btn-pdf { background: #1a7f37; }
.btn-doi { background: #cf222e; }
.btn-pubmed { background: #2F5496; }
.btn-s2 { background: #fb8c00; }
.btn-hal { background: #9d4edd; }
.btn-rg { background: #00ccc0; }
.btn-pmc { background: #1a7f37; opacity: .85; }
.btn-secondary { background: #6b7280; }
.filter { background: white; padding: 12px 18px; border-radius: 8px; margin: 15px 0;
          display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter button { padding: 7px 14px; border-radius: 5px; border: 1px solid #ddd;
                 background: white; cursor: pointer; font-size: 12px; }
.filter button.active { background: #2F5496; color: white; border-color: #2F5496; }
input[type="search"] { padding: 7px 12px; border: 1px solid #ddd; border-radius: 5px;
                       width: 280px; font-size: 13px; }
.tag { display: inline-block; padding: 2px 6px; border-radius: 3px;
       font-size: 10px; font-weight: 600; margin-left: 4px; }
.tag-ok { background: #d4f4dd; color: #1a7f37; }
.tag-manq { background: #ffe0e0; color: #cf222e; }
.help-box { background: #fff8e1; border-left: 4px solid #f59e0b; padding: 11px 15px;
            margin: 12px 0; border-radius: 4px; font-size: 12.5px; line-height: 1.5; }
code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 11px; }
</style>
</head>
<body>
''')

HTML.append(f'''<h1>Revue ALYCANTE — Index unifié des 120 PDFs</h1>

<div class="summary">
  <p style="font-size:15px"><strong>{n_ok}</strong> / 120 PDFs disponibles localement
  <span style="color:#666">(boutons verts pour télécharger directement)</span>.</p>
  <p style="font-size:15px"><strong>{n_manq}</strong> PDFs à récupérer
  <span style="color:#666">(boutons colorés vers PubMed/DOI/HAL/Semantic Scholar/EPMC)</span>.</p>

  <div class="help-box">
    <strong>Pour les manquants — par ordre de chance de succès :</strong>
    <ol style="margin:5px 0 0 0;padding-left:20px">
      <li><strong>DOI</strong> (rouge) — accès éditeur direct, marche si vous êtes sur le réseau AP-HP ou son VPN</li>
      <li><strong>S2</strong> Semantic Scholar — souvent un PDF caché non listé par Unpaywall</li>
      <li><strong>HAL</strong> — archives ouvertes françaises (Inserm/AP-HP y déposent)</li>
      <li><strong>ResearchGate</strong> — demande à l'auteur (réponse en 24-48h)</li>
      <li><strong>EPMC</strong>/<strong>PMC</strong> — PubMed Central (si version OA déposée par auteur)</li>
    </ol>
  </div>

  <div class="legend">
    <span class="legend-item" style="background:#d4f4dd;color:#1a7f37">✓ PDF local</span>
    <span class="legend-item" style="background:#ffe0e0;color:#cf222e">À récupérer</span>
  </div>
</div>

<div class="filter">
  <strong>Filtres :</strong>
  <button onclick="filtrer('tous', event)" class="active">Tous ({len(unique_refs)})</button>
  <button onclick="filtrer('dispo', event)">PDFs dispo ({n_ok})</button>
  <button onclick="filtrer('manq', event)">À faire ({n_manq})</button>
  <input type="search" id="search" placeholder="Rechercher PMID, auteur, titre..."
         oninput="recherche(this.value)">
</div>

<div id="articles">
''')

for r in unique_refs:
    pmid = r['pmid']
    doi = r.get('doi', '')
    pmc = pmc_map.get(pmid, '')
    pdf_file = pdf_by_pmid.get(pmid)
    is_ok = bool(pdf_file)
    cls = 'dispo' if is_ok else 'manq'

    search_data = f"{pmid} {r['authors']} {r['title']}".lower().replace('"','&quot;')
    title_safe = r['title'].replace('"','&quot;').replace('<','&lt;').replace('>','&gt;')

    HTML.append(f'<div class="article {cls}" data-status="{cls}" data-search="{search_data}">')
    HTML.append('  <div class="info">')
    HTML.append(f'    <div><span class="id-badge">#{r["id"]}</span>')
    HTML.append(f'    <span class="meta">{r["authors"]} ({r["year"]})</span>')
    if is_ok:
        HTML.append('    <span class="tag tag-ok">PDF dispo</span>')
    else:
        HTML.append('    <span class="tag tag-manq">à récupérer</span>')
    HTML.append('    </div>')
    HTML.append(f'    <div class="title">{title_safe}</div>')
    HTML.append(f'    <div class="meta"><em>{r["journal"]}</em> {r.get("vol","")}<br>')
    HTML.append(f'    PMID <a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank">{pmid}</a>')
    if doi:
        HTML.append(f'    &middot; DOI <code>{doi}</code>')
    HTML.append('    </div>')
    HTML.append('  </div>')
    HTML.append('  <div class="actions">')

    if is_ok and pdf_file:
        first_author = r['authors'].split(';')[0].split()[0] if r.get('authors') else 'unknown'
        download_name = f"{pmid}_{first_author}_{r['year']}.pdf"
        HTML.append(f'    <a class="btn btn-pdf" href="pdfs/{pdf_file}" download="{download_name}">📥 Télécharger PDF</a>')
        HTML.append(f'    <a class="btn btn-secondary" href="pdfs/{pdf_file}" target="_blank" style="opacity:.85">Aperçu</a>')
    else:
        # Toujours afficher les sources multiples
        HTML.append(f'    <a class="btn btn-doi" href="https://doi.org/{doi}" target="_blank">🔓 DOI (éditeur)</a>')
        HTML.append(f'    <a class="btn btn-s2" href="https://www.semanticscholar.org/search?q={r["title"][:80].replace(" ","+")}" target="_blank">S2</a>')
        HTML.append(f'    <a class="btn btn-hal" href="https://hal.science/search/index/?q={doi}" target="_blank">HAL</a>')
        HTML.append(f'    <a class="btn btn-rg" href="https://www.researchgate.net/search/publication?q={doi}" target="_blank">ResearchGate</a>')
        if pmc:
            HTML.append(f'    <a class="btn btn-pmc" href="https://europepmc.org/article/MED/{pmid}" target="_blank">EPMC</a>')

    HTML.append('  </div>')
    HTML.append('</div>')

HTML.append('''
</div>

<div style="position:fixed;bottom:10px;right:10px;background:white;padding:8px 14px;
            border-radius:20px;box-shadow:0 2px 8px rgba(0,0,0,.15);font-size:11px;color:#666">
  <span id="autoRefreshStatus">⟳ Auto-refresh actif (toutes les 8s)</span>
  &middot; <a href="#" onclick="event.preventDefault();location.reload()">Forcer maintenant</a>
</div>

<script>
function filtrer(filter, evt) {
  document.querySelectorAll('.filter button').forEach(b => b.classList.remove('active'));
  evt.target.classList.add('active');
  document.querySelectorAll('.article').forEach(a => {
    if (filter === 'tous') a.style.display = '';
    else if (filter === 'dispo' && a.dataset.status === 'dispo') a.style.display = '';
    else if (filter === 'manq' && a.dataset.status === 'manq') a.style.display = '';
    else a.style.display = 'none';
  });
}
function recherche(q) {
  q = q.toLowerCase();
  document.querySelectorAll('.article').forEach(a => {
    a.style.display = (a.dataset.search || '').includes(q) ? '' : 'none';
  });
}

// Auto-refresh : memorise scroll position + filtre + recherche
const STATE_KEY = 'alycante_state';
window.addEventListener('beforeunload', () => {
  const active = document.querySelector('.filter button.active');
  sessionStorage.setItem(STATE_KEY, JSON.stringify({
    scroll: window.scrollY,
    filter: active ? active.textContent : 'Tous',
    search: document.getElementById('search').value
  }));
});
window.addEventListener('load', () => {
  const saved = sessionStorage.getItem(STATE_KEY);
  if (saved) {
    const s = JSON.parse(saved);
    if (s.search) {
      document.getElementById('search').value = s.search;
      recherche(s.search);
    }
    if (s.filter && s.filter !== 'Tous') {
      const btn = Array.from(document.querySelectorAll('.filter button'))
        .find(b => b.textContent.startsWith(s.filter.split(' (')[0]));
      if (btn) btn.click();
    }
    if (s.scroll) setTimeout(() => window.scrollTo(0, s.scroll), 50);
  }
});

// Recharger automatiquement toutes les 8 secondes
let refreshIn = 8;
setInterval(() => {
  refreshIn--;
  if (refreshIn <= 0) {
    location.reload();
  } else {
    document.getElementById('autoRefreshStatus').textContent = `⟳ Rafraichissement dans ${refreshIn}s`;
  }
}, 1000);
</script>
</body></html>
''')

out = PDF_DIR / "INDEX.html"
out.write_text('\n'.join(HTML), encoding='utf-8')
print(f"INDEX.html cree : {out}")
print(f"Taille : {out.stat().st_size:,} bytes")
print(f"PDFs locaux : {n_ok} / {len(unique_refs)}")
print(f"Manquants  : {n_manq}")
