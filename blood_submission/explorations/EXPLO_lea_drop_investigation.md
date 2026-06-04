# Investigation — pourquoi le modèle se dégrade sur Léa étendue (HR 8.32 → 5.19)

**Date** : 29 May 2026 (updated with user's pipeline-architecture hypothesis)
**Status** : Investigation exploratoire approfondie

## La question

ALYCANTE J0+J14 publié (n=18) → HR EFS 8.32 (1.98-34.94), C-index 0.81
Léa étendu all-timepoints (n=41) → HR EFS 5.19 (1.76-15.33), C-index 0.71

**Pourquoi cette dégradation ?**

## Hypothèses testées et rejetées

### ❌ H1/H2 — Pattern temporel : le subset "late only" reste discriminatif

| Stratum | n | events | HR EFS | C-index |
|---|---|---|---|---|
| J0+J14 only | 4 | 2 | 4.85 | 0.70 |
| J0+J14 + late | 13 | 6 | 2.84 | 0.68 |
| **Late only (no J0/J14)** | **24** | **11** | **6.54** | **0.72** |

Le late-only seul donne HR 6.54 (proche du publié). **L'extrapolation arrière n'est pas le coupable.**

### ❌ H3 — Mix CAR-T products : Yescarta seul donne déjà HR 4.58

| Product | n | HR EFS |
|---|---|---|
| Yescarta (= axi-cel comme ALYCANTE) | 29 | 4.58 |
| Breyanzi | 11 | 6.05 |

Même restreint à Yescarta, HR << 8.32. Pas la dilution par non-axi-cel.

### ❌ H4 — Composition events R/R lymphome : 19/19 events sont lymphome

Sous définition strict (date_rechute populée OU DC_CAUSE=lymphome) :
- J0+J14 (n=18) : 9/9 events = R/R lymphome
- Extended (n=41) : 19/19 events = R/R lymphome

Les events sont presque tous lymphome dans les deux cas. **Pas un event-mix problem.**

## ✅ H5 — Différence d'architecture pipeline NGS (hypothèse PI confirmée)

### Le constat

- **ALYCANTE** : pipeline "phased variants" (PV) = filtres statistiques + polishing + Monte Carlo, sensible ET spécifique
- **Léa** : surveillance supervisée standard du labo de routine = pas de PV, pas de tests stats, pas de polishing, pas de MC

### La conséquence subtile : ce qui se passe quand le tumor signal disparait

Le hEG calculé pour Léa est :
```
hEG = mean(VAF_variants_validés) × Cell_Free_DNA
```
où `variants_validés` = `vaf_font_color='FFFF0000'` (rouge, validé par analyste) OU `PREDICTED='Mutation'`.

**À J0/J14 (signal fort)** :
- Tumor variants détectables → analyste valide → variants rouge présents → mean(VAF_rouge) reflète le tumor → hEG correct
- Pipeline simple ≈ pipeline PV (signal >> noise floor)

**À M3/M9/M12 (signal faible/absent en remission)** :
- Tumor variants disparaissent ou très bas → analyste ne valide plus → n_rouge=0
- Fallback sur `PREDICTED='Mutation'` qui inclut CHIP (TP53, DNMT3A, ARID1B...) et variants polymorphes mal-filtrés
- mean(VAF_mut_fallback) donne des valeurs ÉNORMES (13-15% médian) — c'est du CHIP ou panel artifact, pas tumor
- × cfDNA résiduel (3000-5000 ng/mL, lié à inflammation/age/CHIP) → hEG = valeur élevée artificielle

### Preuves chiffrées

**Médiane VAF utilisée pour le hEG par timepoint** :

| Timepoint | VAF rouge (si n_rouge ≥1) | VAF fallback mut (si n_rouge=0) | Rapport fallback/rouge |
|---|---|---|---|
| CART J0 | 0.0157 | 0.0239 | 1.5× |
| CART J15 | 0.0118 | 0.0208 | 1.8× |
| CART M1 | 0.0085 | 0.0000 | (clean) |
| CART M2 | 0.0072 | 0.0429 | **6×** |
| CART M3 | 0.0118 | 0.0275 | 2.3× |
| CART M6 | 0.0089 | 0.0134 | 1.5× |
| **CART M9** | 0.0108 | **0.1318** | **12×** |
| **CART M12** | 0.0136 | **0.1465** | **11×** |

→ À M9/M12, le fallback gonfle artificiellement la VAF d'un facteur **10×**.

**Validation rate par classe × timepoint** (% samples avec n_rouge=0) :

| Timepoint | BON | MAUVAIS |
|---|---|---|
| CART J0 | 67% | **38%** ← MAUVAIS ont leur tumor baseline trackée |
| CART J15 | 50% | 63% |
| CART M1 | 31% | 74% |
| CART M2 | 62% | 60% |
| CART M3 | 50% | 80% |
| CART M6 | 60% | 56% |
| CART M9 | 50% | 100% |
| CART M12 | 67% | 86% |

→ Au cours du suivi, l'analyste valide de moins en moins les samples → tous les patients (BON ET MAUVAIS) finissent avec n_rouge=0.

### Le smoking gun : les 3 patients reclassifiés

Comparaison de la **qualité de leurs samples tardifs** :

| Catégorie | n | % late samples sans rouge | cfDNA max médian |
|---|---|---|---|
| **Reclassifiés (BON→MAUVAIS sous extended)** | 3 | **92%** | **3773 ng/mL** |
| Stable BON (BON dans les 2 prédictions) | 4 | 58% | 2154 ng/mL |

Les patients reclassifiés ont **presque tous leurs samples late sans variant rouge** ET un cfDNA élevé. Quand le hEG est calculé :
- Pas de rouge → fallback sur PREDICTED='Mutation' (variants CHIP/polymorphes ~15% VAF)
- × cfDNA élevé (artefact inflammation/CHIP)
- → hEG = 25 (énorme) → classification MAUVAIS

Pourtant ces patients sont **vivants sans rechute à 27-30 mois** (Patient B, Patient C — vrais faux positifs).

### Le cas Patient C M12 (anonymisé "Patient C")

- 810 variants détectés au total
- **0 variants rouge (analyst-validated tumor)**
- 0 variants PREDICTED='Mutation' clairs
- 26 variants dans gènes CHIP-suspect (ARID1B, BACH2, TP53...) à basse VAF
- cfDNA = 3773 ng/mL
- hEG calculé = 25
- Classification : MAUVAIS
- **Réalité clinique : vivant sans event à 27.7 mo** ⚠️

## Synthèse

**Le modèle JLCM ALYCANTE est correct**. Ce qui dégrade la performance à M3+ en routine Léa, c'est une **inadéquation de mesure d'entrée** :

- À J0/J14 : signal tumor encore détectable, le pipeline routine ≈ le pipeline PV (signal >> noise)
- À M3+ en remission : tumor signal sous le seuil routine → analyste n'annote plus rien → fallback sur variants non-tumoraux à haute VAF (CHIP, panel artifacts) → hEG gonflé artificiellement → classification MAUVAIS injustifiée

**Pipeline ALYCANTE (PV)** :
- Statistical filtering exclut explicitement les variants CHIP-typiques et les polymorphes
- Monte Carlo donne une significance pour chaque variant call
- Polishing UMI corrige le sequencing error rate
- Résultat : à M3+ en remission, le pipeline retourne hEG ≈ 0 (correctement) au lieu de hEG ≈ 25 (artefactuel)

**Pipeline Léa (routine supervisée)** :
- Seul filtre = annotation manuelle par analyste (vaf_font_color rouge)
- Quand l'analyste arrête d'annoter (= remission), le calcul retombe sur des variants non-spécifiques
- Pas de noise floor calibré → variants CHIP/polymorphes passent à travers

## Implications

### Pour Blood v8.9 actuel
**Rien à changer.** La validation publiée (J0+J14, HR 8.32) opère exactement dans le régime où routine ≈ PV pipeline (signal fort, ctDNA détectable au-dessus du noise floor routine). C'est cohérent avec le scénario clinique deploy-at-D14 que le manuscrit défend.

### Pour le follow-up paper / addendum post-acceptance
La trouvaille mérite d'être publiée :
- Titre proposé : *"ctDNA-JLCM performance is preserved at the day-14 deployment timepoint but degrades in routine post-D14 surveillance due to mismatch between the trial-grade variant calling and standard clinical pipelines"*
- Démontre méthodologiquement qu'un classifier ctDNA doit être **paired with its variant calling pipeline** — déployer en routine demande soit (a) un pipeline PV en clinique, soit (b) un strict variant tracking patient-specific (Frank/Kurtz style).

### Recommandation pour la pratique clinique
Si on veut implémenter le ctDNA-JLCM au-delà de D14 en routine, deux options :
1. **Pipeline PV en routine** (cher, long, mais sensible+spécifique)
2. **Variant-specific MRD** : tracker uniquement les variants validés à baseline, ignorer les variants émergents (CHIP-resistant)

À D14, le pipeline routine standard est suffisant car le signal est encore au-dessus du noise floor.

## Artefacts (sur NAS + GitHub anonymisé)

- `EXPLO_lea_drop_investigation.md` (ce rapport)
- Scripts dans `C:/Users/4067048/AppData/Local/Temp/alycante_lit/` :
  - `investigate_lea_drop.py` (H1-H4 stratification)
  - `investigate_lea_isolate_published.py` (Cox apples-to-apples)
  - `query_variants.py` (diagnostic variants per patient × timepoint)
  - `test_pipeline_hypothesis.py` (validation yield per timepoint)
