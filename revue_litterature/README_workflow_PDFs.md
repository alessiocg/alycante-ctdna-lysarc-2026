# Récupérer les 120 PDFs de la revue ALYCANTE — workflow AP-HP **sans BiblioInserm**

Vous n'avez pas de compte BiblioInserm ? Pas de problème : 70-80 % des articles peuvent être récupérés gratuitement et légalement par le script automatique, et plusieurs alternatives existent pour le reste.

## Stratégie en 4 niveaux (sans compte BiblioInserm)

| Niveau | Source | Couverture attendue | Authentification |
|---|---|---|---|
| 1 | **PubMed Central (PMC)** open access | ~50-60% | Aucune |
| 2 | **Unpaywall** (Author Manuscript, preprints) | +10-20% | Aucune |
| 3 | **VPN AP-HP** ou **DUMAS** / **HAL** | ~10% | Compte AP-HP standard (VPN) |
| 4 | **Demande à la documentation AP-HP** | <10% | Email professionnel |

## Niveau 1-2 : Téléchargement automatique gratuit

```bash
pip install requests
cd revue_litterature/
python fetch_pdfs.py --email votre.adresse@aphp.fr --out ./pdfs_revue
```

Durée : ~3-4 minutes pour les 120 références. Le script télécharge **tous les articles open access** sans authentification, légalement.

## Niveau 3 : Accès aux journaux via le VPN AP-HP

L'AP-HP fournit à tous ses agents un **VPN d'accès distant** (Pulse Secure / Forticlient selon le site). Une fois connecté au VPN, vous accédez aux journaux abonnés **comme depuis le réseau interne**, sans login supplémentaire.

**Procédure type** (variable selon le site AP-HP) :
1. Demander l'accès VPN à votre DSI locale (HEGP, Mondor, Salpêtrière, etc.)
2. Une fois connecté au VPN, ouvrir l'`index.html` généré par le script
3. Cliquer sur les boutons **DOI** des articles manquants — la plupart des grands éditeurs (Nature, NEJM, Elsevier, Wiley, Springer) reconnaissent l'IP institutionnelle et donnent l'accès direct

**Si pas de VPN disponible**, alternatives :
- **HAL** (archive ouverte française) : `https://hal.science/search/index/?q=<DOI>` — beaucoup d'articles AP-HP/Inserm y sont déposés
- **DUMAS** (mémoires/thèses) : `https://dumas.ccsd.cnrs.fr/`
- **ResearchGate** : demande directe à l'auteur (souvent réponse en 24-48h)
- **arXiv / bioRxiv / medRxiv** : pour les preprints récents

## Niveau 4 : Demande à la documentation AP-HP

Chaque site AP-HP dispose d'un **service de documentation médicale** (souvent dénommé DSI/DEPP ou bibliothèque) qui peut commander des articles via le **prêt entre bibliothèques (PEB)**, généralement gratuitement pour les agents AP-HP. Le délai est habituellement de 24-72h.

**Pour faire une demande groupée** :
1. Le script génère `manifest.json` qui liste tous les articles avec leur statut
2. Filtrer ceux marqués `"status": "manq"` 
3. Envoyer la liste des DOI manquants par email au service documentation de votre site

## Alternatives sans aucun compte

Si le service documentation n'est pas accessible, plusieurs options existent :

**Open access élargi** :
- [OpenAIRE](https://explore.openaire.eu/) — agrégateur européen de publications OA
- [CORE](https://core.ac.uk/) — moteur de recherche OA
- [Semantic Scholar](https://www.semanticscholar.org/) — souvent donne accès au PDF
- [Europe PMC](https://europepmc.org/) — variante européenne de PMC, parfois plus de couverture

**Demande directe aux auteurs** :
- Email à l'auteur correspondant (souvent listé sur PubMed) avec demande polie de reprint
- Réponse fréquente, surtout pour les articles récents

**Partage légal entre chercheurs** :
- Forum de discussion entre collègues (avec respect strict du droit d'auteur)

## Fichiers produits par le script

```
pdfs_revue/
├── pdfs/                       # PDFs téléchargés automatiquement (60-80)
├── index.html                  # Index cliquable avec boutons DOI/PubMed
├── references.ris              # Pour Zotero / EndNote
├── references.bib              # BibTeX
└── manifest.json               # Liste structurée avec statut "ok"/"manq"
```

L'`index.html` contient pour chaque référence :
- Bouton **PubMed** (toujours accessible)
- Bouton **DOI** (résolution standard, accès si VPN AP-HP)
- Bouton **PDF local** (si téléchargé automatiquement)

## Cas particulier : avoir un compte BiblioInserm

Si vous **demandez** votre compte BiblioInserm (procédure simple, gratuite, accessible à tout chercheur AP-HP/Inserm) :
1. Inscription : <https://www.biblioinserm.fr/> → "S'inscrire"
2. Validation : 24-48h par l'administration Inserm
3. Une fois le compte créé, l'extension [Click & Read](https://www.biblioinserm.fr/click-and-read) automatise les accès via Chrome/Firefox

## Limites légales

- L'usage doit rester dans le cadre de votre activité de recherche personnelle
- Les PDFs récupérés via Unpaywall ou PMC sont toujours légaux (OA gold/green)
- Pour les articles sous abonnement, le VPN AP-HP est la voie légitime
- Sci-Hub et autres sources non légales sont à proscrire

---
*Dernière mise à jour : 11 mai 2026 — workflow adapté à un usage sans compte BiblioInserm dédié.*
