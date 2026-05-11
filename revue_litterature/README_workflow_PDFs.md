# Récupérer les 120 PDFs de la revue ALYCANTE — workflow AP-HP

Ce dossier contient le script `fetch_pdfs.py` qui automatise la récupération des PDFs des 120 références bibliographiques de la revue, en combinant **sources gratuites légales** et **abonnements AP-HP/Inserm**.

## Stratégie en 4 niveaux

| Niveau | Source | Couverture attendue | Authentification |
|---|---|---|---|
| 1 | **PubMed Central (PMC)** | ~50-60% (open access) | Aucune |
| 2 | **Unpaywall** (Author Manuscript, preprints) | +10-20% | Aucune |
| 3 | **BiblioInserm / Click & Read** | ~25-30% restants | Identifiants AP-HP / Inserm |
| 4 | **Demande à la bibliothèque AP-HP** | <5% (articles très récents/payants) | Sur demande |

Le script automatise les niveaux 1 et 2 et **génère un index HTML cliquable + fichier RIS** pour traiter rapidement les niveaux 3-4.

## Installation et exécution

```bash
pip install requests
cd revue_litterature/
python fetch_pdfs.py --email votre.adresse@aphp.fr --out ./pdfs_revue
```

Durée : ~3-4 minutes pour les 120 références (rate limit NCBI).

## Fichiers produits

Le script crée le dossier de sortie avec :

```
pdfs_revue/
├── pdfs/                          # 60-80 PDFs téléchargés automatiquement
│   ├── 25842160_PMC4460610.pdf    # Roschewski 2015 (PMC OA)
│   ├── 30125215_PMC6161832.pdf    # Kurtz 2018 (PMC OA)
│   ├── 34294911_OA.pdf            # Kurtz PhasED-Seq (Author Manuscript via Unpaywall)
│   └── ...
├── index.html                     # Index cliquable des 120 références
├── references.ris                 # Pour Zotero / EndNote
├── references.bib                 # BibTeX (LaTeX)
└── manifest.json                  # Log structuré
```

## Niveau 3 — récupération via abonnement AP-HP / Inserm

**Option A — Extension Click & Read** (recommandée pour usage quotidien)

1. Installez l'extension [Click & Read](https://www.biblioinserm.fr/click-and-read) sur Chrome / Firefox
2. Connectez-vous une fois à [BiblioInserm](https://www.biblioinserm.inserm.fr/)
3. Ouvrez `pdfs_revue/index.html` dans le navigateur
4. Cliquez sur le bouton **DOI** des articles manquants — Click & Read détecte automatiquement le DOI et offre le PDF si l'AP-HP/Inserm y est abonné

**Option B — Import Zotero avec proxy AP-HP**

1. Téléchargez Zotero ([zotero.org](https://www.zotero.org))
2. Importez `references.ris` (File → Import)
3. Préférences → Avancé → Proxies → Ajouter le proxy AP-HP/Inserm (URL fournie par votre bibliothèque)
4. Sélectionnez toutes les références → clic droit → **Find Available PDF**
5. Zotero récupère automatiquement les PDFs via votre abonnement

**Option C — Recherche manuelle ciblée**

Pour les rares articles très récents (2026 *in press*) ou inaccessibles :
- Recherche par DOI sur [BiblioInserm](https://www.biblioinserm.inserm.fr/)
- Service de demande d'articles (DSI/DEPP AP-HP) : envoyer la liste des DOI manquants

## Limites légales et pratiques

⚠️ **À respecter** :
- L'usage doit rester dans le cadre des conditions d'abonnement (recherche personnelle, pas de redistribution)
- Ne pas utiliser Sci-Hub ou autres sources illégales — l'AP-HP a normalement un abonnement suffisant
- Les PDFs téléchargés via Unpaywall sont **toujours légaux** (Author Accepted Manuscript, preprints, OA gold/green)

⚠️ **Plateformes parfois capricieuses** :
- Nature et NEJM peuvent bloquer le téléchargement direct ; il faut alors passer par le portail BiblioInserm/Click&Read
- Certains éditeurs (Elsevier, Wiley) nécessitent l'authentification SSO avant le DOI

## Mise à jour des références

Si vous ajoutez des références à la revue :

```bash
# Editer references_v3.json (ou créer references_v4.json)
# Puis relancer :
python fetch_pdfs.py --email votre.adresse@aphp.fr --out ./pdfs_revue --refs references.json references_v2.json references_v3.json references_v4.json
```

## En cas de problème

| Symptôme | Cause probable | Solution |
|---|---|---|
| "elink HTTP error" | Rate limit NCBI dépassé | Ajouter `--no-unpaywall` puis relancer (déjà un délai par défaut) |
| Beaucoup de "manq" | Articles récents sans PMC encore | Normal, utiliser Click & Read |
| Click & Read ne propose rien | Pas d'abonnement AP-HP/Inserm pour ce journal | Demander via DEPP AP-HP |
| PDF corrompu (0 KB) | Redirection vers landing page | Refaire le téléchargement manuellement via DOI |

## Liens utiles AP-HP / Inserm

- [BiblioInserm — portail principal](https://www.biblioinserm.inserm.fr/)
- [Click & Read — extension navigateur](https://www.biblioinserm.fr/click-and-read)
- [Inserm Pro — portails documentaires](https://pro.inserm.fr/rubriques/en-labo/science-ouverte/les-portails-documentaires-de-inserm)
- [Zotero — gestionnaire de références](https://www.zotero.org)

---
*Dernière mise à jour : 11 mai 2026 (revue ALYCANTE v4)*
