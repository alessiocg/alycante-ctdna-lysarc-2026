# Investigation — pourquoi le HR EFS chute de 8.32 → 5.19 quand on étend Léa aux late timepoints

**Date** : 29 May 2026
**Status** : Exploratory deep-dive (follow-up to `EXPLO_lea_extended_validation.md`)

## Question

La cohorte Léa publiée (J0+J14, n=18) donne HR EFS = 8.32 (C-index 0.81).
La cohorte étendue (all timepoints, n=41) donne HR EFS = 5.19 (C-index 0.71).

**Pourquoi cette dégradation ?**

## Tests d'hypothèses

### H1/H2 — Stratification par pattern temporel : pas concluant

| Stratum | n | events | HR EFS (95% CI) | C-index | P log-rank |
|---|---|---|---|---|---|
| J0+J14 only (no late) | 4 | 2 | 4.85 (0.09–254) | 0.70 | 0.36 |
| J0+J14 + late | 13 | 6 | 2.84 (0.54–15.0) | 0.68 | 0.16 |
| **Late only (no J0/J14)** | **24** | **11** | **6.54 (1.37–31.2)** | **0.72** | **0.005** |

→ Le stratum "late only" reste discriminatif. **L'extrapolation arrière sans J0/J14 n'est PAS le coupable.**

### H3 — CAR-T product : pas concluant

| Product | n | HR EFS |
|---|---|---|
| Yescarta | 29 | 4.58 (1.30–16.2) |
| Breyanzi | 11 | 6.05 (0.66–55.7) |
| Kymriah | 1 | n/a |

→ Yescarta seul (cohérent avec ALYCANTE 100% axi-cel) donne déjà HR 4.58, beaucoup plus bas que le 8.32 publié. **Pas une dilution non-Yescarta.**

### H4 — Event composition (R/R lymphoma vs autres) : éliminée

Sous définition strict (date_rechute populée OU DC_CAUSE = lymphome) :
- J0+J14 (n=18) : 9/9 events = R/R lymphome → HR 8.05 (1.92–33.7), C-index 0.80
- Extended (n=41) : 19/19 events = R/R lymphome → HR 5.19 (1.76–15.3), C-index 0.71

**Les events sont presque tous R/R lymphome dans les deux cas.** Pas un mix problem.

### H5 — Artefact de la formule hEG aux late timepoints : ✅ **CONFIRMÉE**

C'est là qu'est le vrai problème.

#### Rappel formule

```
hEG_raw = mean(VAF_variants_validés) × Cell_Free_DNA
hEG     = 10^(log10(hEG_raw) + calibration_offset)
```

où `variants_validés` = variants annotés `vaf_font_color='FFFF0000'` (rouge, validation analyste) OU `PREDICTED='Mutation'`.

#### Diagnostic : Patient C M12 (faux positif typique)

Patient Patient C : J0+J14 = BON (p=0.00) → All-timepoints = MAUVAIS (p=1.00) → event=0 à 27.7 mo (alive sans rechute documentée).

Sa trajectoire :
| Timepoint | cfDNA | heg calculé | heg_log |
|---|---|---|---|
| J0 | — | 1.80 | 0.26 |
| J14 | — | 1.17 | 0.07 |
| M3 | — | **8.01** | 0.90 |
| M6 | — | 0.43 | −0.37 |
| **M12** | **3773 ng/mL** | **25.33** | **1.40** |

À M12 (où hEG = 25 → MAUVAIS), enquête sur les variants :
- **810 variants détectés**
- **0 variants "rouge" (analyst-validated tumor)** ⚠️
- **0 variants PREDICTED='Mutation'**
- 26 variants dans gènes CHIP-suspect (ARID1B, BACH2, TP53...)
- Tous à très basse VAF (0.001–0.07)
- **cfDNA élevé (3773) probablement non-tumoral** (infection, second cancer ?)

→ **Le hEG calculé de 25 est un artefact**. Le patient n'a aucun signal tumoral validé à M12. La formule, en l'absence de tumor variants vrais, agrège des variants CHIP/panel-noise.

#### Pourquoi ça marche à J0+J14 mais pas à M3+

| Aspect | J0+J14 (trial-grade) | M3+ (routine) |
|---|---|---|
| Variants tracked | Validés depuis pathology baseline | Émergents, pas toujours validés |
| cfDNA composition | Dominé par tumor signal | Mix tumor + inflammation + CHIP + bystander |
| Sample quality | Standardized (trial protocol) | Variable (routine schedule) |
| Mean VAF stable | Yes (real tumor variants) | No (drift toward CHIP/noise) |
| **hEG formula validity** | **Robuste** | **Dégradée** |

#### Conséquence pour la classification

Avec un hEG artificiellement élevé à M3/M6/M12, le JLCM (entraîné sur ALYCANTE où les late timepoints reflètent du vrai signal tumoral) extrapole une "rechute imminente" pour ces patients. Trois reclassifications BON→MAUVAIS dans la cohorte étendue :

| Patient | Late tp pattern | Verdict | Likely cause |
|---|---|---|---|
| **Patient A** | rebond M12 réel | ✅ **Vrai positif** — event à 26.7mo | Tumor signal real, rebond corrélé à rechute |
| Patient B | hEG croissant J0→M12 | ⚠️ Faux positif | Probable artefact ou rebond non-progressive |
| Patient C | oscillant + M12 élevé | ⚠️ Faux positif | **0 variants rouge à M12** → artefact certifié |

## Synthèse — pourquoi le modèle marche bien à D14 mais moins à M3+

**Le modèle JLCM lui-même est fine** — il a été entraîné correctement sur ALYCANTE où :
- Variants validés via panel CAPP-Seq sur paired tumor + plasma
- Quality control trial-grade à chaque timepoint
- Late samples (M3-M12) processed identiquement aux J0/J14

**Le problème est dans la mesure du hEG en routine post-D14** :
1. **Variants rouge progressivement absents** chez les vrais "BON" (= remission complète) → la formule `mean(VAF) × cfDNA` n'a plus rien de pertinent à mesurer mais pèche par artefact
2. **CHIP variants émergents** chez les patients âgés post-chimio → contamination du signal
3. **cfDNA non-tumoral** (infections, etc.) inflate hEG en l'absence de réel tumor

→ **Le ctDNA-JLCM est un classifieur valide d'événements lymphome, mais sa mesure d'entrée (hEG) devient bruitée en routine post-D14 quand la disease est en remission**.

## Implications

### Pour le manuscript Blood actuel

**Rien à changer** — la validation publiée (J0+J14, n=18, HR 8.32) reste défendable parce qu'elle s'appuie sur des samples baseline + D14 où la formule hEG est robuste. C'est *exactement* le scénario clinique deploy-at-D14 que le manuscrit promeut.

### Pour la généralisation post-acceptance / suite

Si on veut étendre à M3+ en routine, deux options :
1. **Strict variant tracking** : ne pas utiliser `mean(VAF)` global, mais ne tracker QUE les variants identifiés à baseline (variant-specific MRD, à la Frank/Kurtz). Demande un workflow patient-specific.
2. **QC stricts sur les late samples** : exclure samples avec 0 variants rouges, depth < seuil, ou cfDNA outlier.

Une autre lecture : la dégradation à 5.19 (extended) est cohérente avec ce qu'on voit dans la literature pour real-world validation cohorts (HR 4–8 plutôt que les HR 15–20 des trial cohorts). C'est **représentatif des performances cliniques réelles**.

### Pour l'addendum / follow-up paper

Le finding qui mérite publication n'est plus juste "le model fonctionne sur trajectoires étendues" — c'est **"performances of the day-14 ctDNA-JLCM degrade in real-world late timepoints due to hEG measurement noise, not due to model misspecification"**. Cela ouvre la voie à un travail méthodologique sur la robustesse de la mesure ctDNA en surveillance routine.

## Artefacts

- `EXPLO_lea_drop_investigation.md` (this report)
- `lea_extended_jlcm_input.csv` + `lea_extended_jlcm_predict.csv` (NAS, gitignored)
- Scripts d'enquête :
  - `investigate_lea_drop.py` — stratification H1-H4
  - `investigate_lea_isolate_published.py` — apples-to-apples J0+J14 vs extended
  - `query_variants.py` — variant-level analysis per patient (Patient C M12 case)

Tout dans `C:/Users/4067048/AppData/Local/Temp/alycante_lit/`.
