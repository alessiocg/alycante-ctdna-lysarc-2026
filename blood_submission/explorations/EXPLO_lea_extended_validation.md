# EXPLORATORY — Henri-Mondor validation cohort with full ctDNA trajectory

**Date** : 29 May 2026
**Status** : Exploratory analysis, not part of v8.9 submission
**Question** : the published validation uses only J0+J14 (n=18) — what happens if we apply predictClass with all available timepoints (D0 through M12) ?

## Data recovery

The hEG formula reverse-engineered from `jlcm_lea_extend_all.py` (script that originally produced `lea_all_jlcm_input.csv` for the published n=18 cohort) is :

```
heg_raw = mean(VAF_validated_variants) × Cell_Free_DNA
offset  = aly_median_log10(heg) − lea_median_log10(heg_raw)   [calibration on J0+J14 only]
heg     = 10^(log10(heg_raw) + offset)
```

Source : SQLite `\\Hmn-cifs-hnas...\NGS\bases_de_donnees\ngs_database.db`
- `patients_clinical` table → Cell_Free_DNA, Glims, date_prelevement_imputee
- `variants_full_materialized` table → VAF (hierarchical: vaf_font_color = FFFF0000 (red, analyst-validated tumor variant) > PREDICTED='Mutation' / is_mutation=1)

Same formula applied to all timepoints in matching windows around CAR-T infusion :
- J0: [−30, +3] d, J14: [+5, +28] d, M1: [+25, +50] d, M3: [+75, +105] d, M6: [+165, +200] d, M9: [+255, +290] d, M12: [+345, +400] d

## Recovered data

| Timepoint | n samples |
|---|---|
| J0 | 40 |
| J14 | 32 |
| **M1** | **33** |
| **M3** | **22** |
| **M6** | **14** |
| **M9** | **6** |
| **M12** | **8** |
| **Total observations** | **155** |
| **Patients with ≥1 timepoint** | **67** |

→ **34 patients have ≥1 late timepoint (M1+)** that wasn't used in the published validation.

## predictClass results — comparison J0+J14 vs full trajectory

| Metric | Published cohort (J0+J14 only) | Extended (all timepoints) |
|---|---|---|
| Patients classifiable | 18 | **41** (+128%) |
| Patients with both predictions | — | 17 |
| **Class concordance (J14 vs all)** | — | **14/17 (82%)** |

### 3 patients reclassified by extended trajectory

| Patient | Timepoints | J0+J14 → All | Truth (EFS) | Verdict |
|---|---|---|---|---|
| **Patient A** | J0+J14+M1+M12 | BON → MAUVAIS | event=1 at 26.7 mo | ✅ **True positive recovered** — J14 missed it |
| Patient B | J0+J14+M3+M12 | BON → MAUVAIS | event=0 at 30.5 mo | ⚠️ Possible false positive (alive without event ≥30 mo) |
| Patient C | J0+J14+M3+M6+M12 | BON → MAUVAIS | event=0 at 27.7 mo | ⚠️ Possible false positive (alive without event ≥27 mo) |

→ Net : +1 true positive, +2 possible false positives on the discordant set. Trade-off favors specificity but introduces some over-classification.

## KM EFS — extended classification

Applied predictClass with ALL available timepoints (anchor at infusion, not landmark D14, because extension uses post-D14 data) :

| Group | n | Events | 6-mo EFS | 12-mo EFS | 24-mo EFS |
|---|---|---|---|---|---|
| Low-risk (BON) | 16 | 1 | 100% | 90% | 90% |
| **High-risk (MAUVAIS)** | **25** | **18** | 52% | 48% | **30.5%** |

**Cox EFS** : HR = **5.19** (95% CI 1.76–15.33), C-index = **0.71**, log-rank P < 0.001

Compared to published validation (J0+J14 only, n=18) :
- HR : 8.32 → 5.19 (lower but still strong)
- 95% CI width : 33 → 13.6 (**3× tighter**)
- C-index : (not previously reported for Henri-Mondor cohort) = 0.71 (vs ALYCANTE 0.81 — slight degradation in real-world)

## Key findings

1. **The full trajectory generalizes well** — direction (low-risk vs high-risk) and significance (P<0.001) preserved when extending beyond D14.

2. **CI tightens substantially with the larger cohort** — the published wide CI (1.98-34.94) reflected sample size rather than effect heterogeneity.

3. **Class-assignment is stable in 82% of patients** when comparing J0+J14-only vs full-trajectory predictClass — supports the manuscript's *train-rich, deploy-early* claim: a D14 readout captures most of the information that later timepoints could add.

4. **Discrimination degrades modestly in real-world** (C-index 0.81 ALYCANTE → 0.71 extended Henri-Mondor) — consistent with retrospective, multi-product (axi-cel + liso-cel + tisa-cel), routine-surveillance data quality vs uniformly-processed trial samples.

5. **Trajectory visualization** (`Explo_lea_extended_trajectories.png`) shows Léa low-risk patients tend to stay relatively flat around log10(hEG) ≈ 0 rather than dropping to −5 like ALYCANTE — even after calibration offset. This is a real-world phenomenon: probably reflects different tumor burden distribution + retrospective sample processing variability. The classifier compensates by discriminating on relative position.

## What does this NOT change for the current submission

- **Published validation HR 8.32 (1.98-34.94) on n=18 with J0+J14 remains the reported figure** for the manuscript. It reflects the deploy-at-D14 scenario the paper actually defends.
- **Class definitions and Cox HRs in the ALYCANTE cohort itself are unchanged.**
- **No new analyses to add to Blood v8.9**.

## What this could become

This is a candidate for a post-acceptance addendum or a separate follow-up paper :
- *"Generalizability of the day-14 ctDNA-JLCM classifier across the full longitudinal ctDNA trajectory in real-world CAR-T patients"*
- Demonstrates the model architecture (train-rich, deploy-early) holds beyond the deployment timepoint
- Quantifies the discrimination degradation in real-world conditions

## Artifacts

- Input data : `output/blood_article_package/output/tables/lea_extended_jlcm_input.csv` (155 rows × 11 cols)
- Prediction comparison : `output/blood_article_package/output/tables/lea_extended_jlcm_predict.csv`
- Trajectories figure : `output/blood_article_package/output/figures/Explo_lea_extended_trajectories.png`
- KM EFS figure : `output/blood_article_package/output/figures/Explo_lea_extended_KM_EFS.png`
- Scripts (in `C:/Users/4067048/AppData/Local/Temp/alycante_lit/`) :
  - `extend_lea_all_timepoints.py` — data extraction from SQLite + hEG calibration
  - `predict_lea_extended.R` — predictClass comparison
  - `plot_lea_extended.py` — visualization + KM

Source database : `\\Hmn-cifs-hnas...\NGS\bases_de_donnees\ngs_database.db` (read-only, local cache used at runtime).
