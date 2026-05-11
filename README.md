# ALYCANTE — ctDNA dans le DLBCL post-CAR-T (LYSARC 2026)

Code et matériel pour le projet biomarqueur de l'étude **ALYCANTE** (axicabtagene ciloleucel en 2ème ligne chez les patients DLBCL non éligibles à l'autogreffe), présenté à la réunion **LYSARC 2026**.

> ⚠️ **Aucune donnée patient n'est versionnée dans ce dépôt.** Les scripts attendent les fichiers source côté serveur sécurisé AP-HP.

## Contexte

- **57 patients non-NI**, 421 mesures ctDNA longitudinales (J-5, J0, J14, M1, M3, M6, M9, M12)
- Biomarqueur principal : **hEG** (haploid Equivalent Genome) en log10
- Méthodologie : **JLCM** (Joint Latent Class Mixed Model, package R `lcmm`, seed=123, random=~time)
- Comparaison ctDNA vs CMR PET M3 (Lugano) pour la prédiction d'EFS et R/R
- Validation externe par cohorte CART Léa (N=158, multicentrique LYSARC)

## Structure du dépôt

```
.
├── README.md
├── revue_litterature/          # Revue exhaustive (120 références PubMed)
│   ├── build_revue_doc_v3.js   # Générateur du document Word
│   ├── build_figures_v3.py     # Figures de synthèse (forest plot, timeline, etc.)
│   ├── references_pubmed.json  # Bibliographie 1-93 (vérifiée PubMed)
│   ├── references_v2.json      # Bibliographie 94-112
│   └── references_v3.json      # Bibliographie 113-120
├── comparaison_cohortes/        # ALYCANTE vs Léa (PFS/EFS/OS)
│   └── compare_alycante_lea.py
├── scripts_figures/             # Scripts de génération des figures cliniques
│   ├── consort_v3.py
│   ├── fig_jlcm_*.R
│   ├── fig_km_*.py
│   ├── fig_swimmer_leadtime.py
│   └── ...                      # 35 scripts au total
└── docs/                        # Documentation
    ├── PlanStat_ALYCANTE.md
    └── memo_seed_jlcm.md
```

## Conventions méthodologiques importantes

1. **hEG est DÉJÀ en log10** dans le fichier source — ne jamais re-transformer
2. **JLCM seed=123** obligatoire (les seeds 456, 2024, etc. font crasher `predictClass()`)
3. **Filtre followup adéquat** : exclure les patients avec `efs_time < seuil` ET `efs_event == 0` avant tout calcul de R/R12, R/R24, Se, Sp, PPV, NPV
4. **R/R strict** : Progression OU Relapse uniquement (pas de censure-comme-pas-R/R)

## Reproductibilité

### Revue de littérature

```bash
cd revue_litterature
python build_figures_v3.py        # génère les 5 figures
npm install -g docx               # une fois
node build_revue_doc_v3.js out.docx
```

### Comparaison de cohortes

```bash
cd comparaison_cohortes
# Nécessite Base_CART_Lea.xlsx et data_lcmm_long.csv (non versionnés)
python compare_alycante_lea.py
```

### JLCM (R)

```r
library(lcmm)
set.seed(123)
m <- Jointlcmm(heg ~ time, random = ~time, ng = 2, ...)
```

## Environnement

- R 4.3.1 (lcmm, survival, prodlim)
- Python 3.11 (pandas, matplotlib, lifelines, scipy, statsmodels)
- Node.js 24 + docx 9.6 (génération Word)

## Citation

Si vous utilisez ces scripts, merci de citer la présentation LYSARC 2026 et l'étude originale ALYCANTE (Houot et al., Nat Med 2023, [doi:10.1038/s41591-023-02572-5](https://doi.org/10.1038/s41591-023-02572-5)).

## Licence

Code source : [MIT](LICENSE).
La revue de littérature reste sous le contrôle des auteurs ; les références PubMed sont publiques.

## Auteurs

- Service d'Immunologie Biologique, Secteur Maladies Lymphoprolifératives, AP-HP
- Assistance Claude (Anthropic) pour la génération du code et de la revue de littérature

---
*Dernière mise à jour : 11 mai 2026 (v3)*
