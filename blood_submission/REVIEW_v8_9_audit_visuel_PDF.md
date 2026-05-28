# REVIEW — v8.9 audit visuel PDF (28 May 2026, 11:54)

Audit ultra-minutieux du PDF compilé : extraction des 5 images embarquées + comparaison à leurs légendes + recompte arithmétique. Trois problèmes identifiés (1 bloquant, 2 mineurs), tous corrigés.

## 1. 🔴 BLOCKER — Image fausse en Figure 2 (5 versions, depuis v8.5)

**Diagnostic.** L'image embarquée comme Figure 2 dans le docx était une analyse de sensibilité par horizon de troncature (6 panels, EFS uniquement, légendes en français « Probabilité EFS », « Temps depuis J14 ») — manifestement destinée au supplément. La vraie Figure 2 attendue par la légende (« KM curves for EFS (left) and OS (right) anchored at the day-14 landmark ») n'a en fait **jamais été produite** : le script `21_fig2_km_efs_os.R` produit aussi la version 6-panels, et tous les artefacts v8 à v8.8 hébergent la mauvaise figure. Le bug est antérieur à la v8.5 et est passé au travers de toutes les audits précédents (qui n'incluaient pas d'inspection visuelle du PDF).

**Fix.** Création d'un script Python (`generate_fig2_correct.py`) qui produit la vraie Figure 2 :
- 2 panels (A = EFS, B = OS) au landmark D14
- Kaplan-Meier low-risk (n=22, 4 events EFS / 1 OS) vs high-risk (n=22, 22 events EFS / 17 OS)
- 95% CI bands, lignes verticales 12m / 24m
- Annotation titre : HR (Cox L₂ pen 0.1) + C-index (concordance.index) + log-rank P

**Numbers in the new Fig 2** (verified against published manuscript values) :
- **EFS** : HR = 17.7 (6.3–50.0), C-index = 0.81, log-rank P < 0.001
- **OS**  : HR = 8.3 (3.1–22.8), C-index = 0.80, log-rank P < 0.001

L'ancienne Fig 2 incorrecte est archivée à `output/archive/Fig2_km_efs_os_WRONG_6panel_horizons.{png,pdf}` (peut servir de SuppFig sensibilité par horizon si jamais utile).

## 2. 🔴 Compte d'événements EFS — 22 vs 21 — résolu en faveur du texte (22)

**Diagnostic.** La Figure 1A (avant correction) affichait `events=21` pour high-risk, suggérant un total de 25 EFS events (21+4) — incohérent avec le texte §107/§137 qui dit « 22 of 22 high-risk patients ».

**Source de la divergence identifiée empiriquement** : patient `15020101051002` (classifié MAUVAIS, p_mauvais=0.85, **décédé à J67 de toxicité du traitement**).
- `master_dataset.csv` (canonique, post-CRF) : `efs_event=1`, `os_event=1` ✅
- `data_lcmm_long.csv` (figé pour reproductibilité de l'entraînement JLCM) : `efs_event=0` à toutes les timepoints — **n'a jamais été mis à jour après le décès**

Par convention CAR-T (et conforme à la définition pré-spécifiée dans le protocole ALYCANTE : « EFS was defined as time to relapse, progression, or death from any cause »), la mort treatment-related = EFS event. **Le bon chiffre est donc 22 EFS events high-risk**, et c'est la Figure 1A qui affichait un compte erroné.

**Fix.** Régénération de Fig 1A (et Fig 1B et Fig 1 combinée) avec event counts issus de `master_dataset.csv` au lieu de `data_lcmm_long.csv`. Légende désormais : `high-risk (n=22, events=22)` et `low-risk (n=22, events=4)` — cohérent avec le texte.

**Note** : `data_lcmm_long.csv` n'est PAS modifié (préservation de la trace de training du JLCM). Les scripts d'analyse qui en dépendent (essentiellement `21_fig2_km_efs_os.R` et `99_audit_visuel`) sous-estiment d'un événement le compte high-risk, mais (a) la Figure 2 a été régénérée à part avec la source canonique, (b) la Figure 1A a été régénérée avec un override explicite, (c) les Cox univariables/multivariables (HR 17.7, C-index 0.81) utilisent `master_dataset.csv` et sont corrects. Recommandation à long terme : reconstruire `data_lcmm_long.csv` post-CRF complet et retrain le JLCM ; pour Blood v8.9 ce n'est pas nécessaire.

## 3. 🟠 Title page — « References: 50 » alors qu'il y en a 31

**Fix.** Ligne 34 du markdown : `- References: 50` → `- References: 31`. Le bureau éditorial Blood vérifie ce chiffre au quality check.

## 4. 🟡 Table 1 — footnote MRD vs « detectable » clarifiée

**Issue.** La Table 1 indique « MRD-positive at baseline (n=41 evaluable) » tandis que la prose §95+ dit « detectable in 50/54 (92.6%) ». Footnote v8.9 était présente mais ambiguë.

**Fix.** Footnote ré-écrite pour rendre explicite que :
- « MRD-positive at baseline » et « detectable baseline ctDNA » désignent le même critère opérationnel (≥1 variant lymphome-spécifique CAPP-Seq à ≥0.005 VAF, duplex UMI)
- Les deux dénominateurs (41 vs 54) diffèrent uniquement par le sous-ensemble analytique :
  - **Table 1** : 44 classifiables → 41 avec sample baseline QC-pass → 38 MRD+ = 92.7%
  - **Results section** : 57 training set → 54 QC-pass → 50 MRD+ = 92.6%
- Reconciliation des effectifs dans SuppTable S15

## Vérifications finales (28/05 11:54)

| Check | Résultat |
|---|---|
| Title page references | **31** (was 50) ✅ |
| Bibliography entries | **31** ✅ |
| Citation order monotone 1→31 | ✅ |
| `"22 of 22 high-risk"` | 1 occurrence (text) ✅ |
| `"22 EFS events"` | 2 occurrences (text + fig caption matches) ✅ |
| `"26 EFS events"` total (22+4) | 1 occurrence (Discussion §141) ✅ |
| `"21"`/`"25"` leftover | 0 ✅ |
| Cogliati | 0 ✅ |
| Superscript citations | [1-3, 7-16, 18-31] all in range ✅ |
| Out-of-range citations | 0 ✅ |
| Fig 1A : `high-risk events=22` | ✅ (after regen) |
| Fig 2 : 2-panel KM landmark D14 with HR 17.7/8.3 + C-index 0.81/0.80 | ✅ (regenerated from scratch) |
| Fig 3, 4, 5 | unchanged, OK |
| docx images = source PNG (md5 byte-identical) | ✅ all 5 |
| Main docx | 967 KB |
| Supp docx | 2.74 MB |
| 4 fichiers synchronisés (package + revue_litterature × main/supp) | ✅ |

Le package est désormais soumissible pour Blood.
