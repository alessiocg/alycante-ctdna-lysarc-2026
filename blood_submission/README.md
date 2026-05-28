# ALYCANTE — Blood biomarker submission package

**Manuscript** : *Day-14 ctDNA joint latent class modeling stratifies risk in transplant-ineligible R/R LBCL after axi-cel*
**Companion paper (parent)** : Houot et al., *J Clin Oncol* 2026 (ALYCANTE final analysis; in revision)
**Current version** : **v8.9** (submission-ready)
**Corresponding author** : Marie-Hélène Delfau-Larue (marie-helene.delfau@aphp.fr)
**First author** : Alexis Claudel
**Senior author / PI ALYCANTE** : Roch Houot

---

## What this package contains

A fully autonomous reproducibility package for the Blood biomarker substudy submission. **No external NAS path or Temp folder is required** — all inputs are in `input/`, all outputs are written to `output/`, all scripts use the path resolver `scripts/_paths.{R,py}`.

```
blood_article_package/
├── README.md                                  ← this file
├── REVIEW_*.md                                ← 13 change logs (v1 to v8.9)
├── input/                                     ← 15 raw / pre-processed inputs
│   ├── ALYCANTE_export_20260505.xlsx          (CRF CDISC, 25 sheets, 62 mFAS)
│   ├── ALYCANTE_PET_20260518.csv              (PET-CT central review)
│   ├── ALYCANTE_RNASeq_21OCT2025.xlsx         (transcriptomic adjunct)
│   ├── Donnees.xlsx / Donnees_brutes2.xlsx    (CRF source extracts)
│   ├── data_lcmm_long.csv                     (ctDNA long format, 57 patients × 7 TP)
│   ├── data_lcmm_mtv_long.csv                 (MTV long format)
│   ├── data_pet_full_long.csv                 (PET long format)
│   ├── jlcm_heg_random_time_model.rds         (final trained JLCM, seed=123)
│   ├── jlcm_mtv_model.rds                     (JLCM-MTV)
│   ├── jlcm_predict_j14.csv                   (day-14 class assignments)
│   ├── jlcm_mtv_predict_j14.csv               (MTV class assignments)
│   ├── lea_all_jlcm_predict.csv               (Henri-Mondor external validation classes)
│   ├── master_dataset.csv                     (consolidated patient-level data)
│   └── rr_strict_mapping.csv                  (RR12 / RR24 strict event mapping)
├── scripts/
│   ├── _paths.R / _paths.py                   ← Path resolver (autonomous)
│   ├── data_prep/                             ← Phase 0 — preparation from CRF (optional)
│   │   ├── 00a_prepare_data_lcmm.R            (CRF -> data_lcmm_long.csv)
│   │   ├── 00b_reseed_jlcm_rt.R               (20-seed sweep — selects seed=123)
│   │   ├── 00c_build_master.py                (CRF -> master_dataset.csv)
│   │   ├── 00d_gen_loo_data_57.R              (LOO-CV data preparation)
│   │   ├── 00e_fig_jlcm_all.R                 ★ Initial Jointlcmm fit; saves
│   │   │                                          jlcm_heg_random_time_model.rds
│   │   ├── 00f_fig_jlcm_courbes_theoriques_r1.R (theoretical trajectories dev)
│   │   └── 00g_fig_jlcm_loo_predict.R         (LOO predictClass diagnostics)
│   ├── 01_train_jlcm_ctdna.R          ← Phase 1 — modeling (assumes inputs ready)
│   ├── 02_predict_j14.R
│   ├── 03_train_jlcm_mtv.R
│   ├── 04_cox_univariate.py
│   ├── 05_cox_multivariate_v2.py
│   ├── 06_cox_bimarker.R
│   ├── 07_nri_12m.py
│   ├── 08_subgroup_analysis.py
│   ├── 09_toxicity_by_jlcm.py
│   ├── 10_table1_jlcm.py
│   ├── 11_validation_lea.R
│   ├── 15_blood_v2_analyses.py        ← Phase 1bis — Blood v2 analyses
│   ├── 16_deauville_analyses.R
│   ├── 20-24_fig*.{py,R}              ← Phase 2 — Figures main
│   ├── 30-37_fig_supp*.py             ← Phase 3 — Figures supplemental
│   ├── 46_cox_continuous_benchmark.R  ← Phase 4 — Reviewer rang A benchmarks
│   ├── 47_frank_style_j28.R
│   ├── 48_ridge_lambda_sensitivity.R
│   ├── 59_build_blood_article_v8_9.py ← Phase 5 — Build docx final (v8.9)
│   ├── 99_audit_visuel_low_risk_high_risk.py
│   ├── run_all.sh / run_all.ps1       ← Single-command pipeline
│   ├── requirements.txt
│   └── 40-58_build_blood_article_v*.py (legacy build scripts for trace v2-v8.8)
└── output/
    ├── Blood_article_v8_9.{docx,md}            ★ Main manuscript
    ├── Blood_article_v8_9_supplemental.docx    ★ Supplemental
    ├── tables/                                 (27 CSV — Table1, Table2, S1-S19)
    └── figures/                                (16 figures Fig1-5 + S1-S12 + visual abstract)
```

---

## Quick-start — reproduce all results in one command

### Prerequisites

- **R 4.3+** with packages `lcmm`, `survival`, `survminer`, `coxphf`, `pROC`
  ```r
  install.packages(c("lcmm", "survival", "survminer", "coxphf", "pROC"))
  ```
- **Python 3.11+** with packages from `scripts/requirements.txt`
  ```bash
  pip install -r scripts/requirements.txt
  ```

### Run the full pipeline

```bash
cd blood_article_package/scripts
bash run_all.sh                # Linux / macOS
# or
.\run_all.ps1                  # Windows PowerShell
```

The pipeline runs **without Phase 0** by default (inputs are already pre-processed in `input/`). To regenerate inputs from the raw CRF, uncomment the Phase 0 block in `run_all.sh` / `run_all.ps1`.

### Run from a different location

```bash
export BLOOD_PKG_ROOT=/absolute/path/to/blood_article_package    # bash
$env:BLOOD_PKG_ROOT = "C:\absolute\path\to\blood_article_package" # PowerShell
```

---

## DAG of execution (dependency graph)

```
   ┌── input/ALYCANTE_export_*.xlsx (CRF source)
   │
   ├── [Phase 0 - data_prep/, optional, OFF by default]
   │       00a_prepare_data_lcmm.R ──┐
   │       00c_build_master.py     ──┴──> data_lcmm_long.csv, master_dataset.csv
   │       00e_fig_jlcm_all.R ────────> jlcm_heg_random_time_model.rds  (seed=123)
   │       00b_reseed_jlcm_rt.R ──────> seed stability sweep (sensitivity)
   │       00d_gen_loo_data_57.R ─────> LOO-CV folds
   │
   ├── [Phase 1 - modeling + survival]
   │       01-03  JLCM ctDNA / predict / JLCM-MTV
   │       04-05  Cox univariate + multivariate
   │       06     Cox bimarker ctDNA+MTV
   │       07     NRI 12-month
   │       08-09  Subgroup + toxicity
   │       10     Table 1 by class
   │       11     Henri-Mondor external validation
   │
   ├── [Phase 1bis - Blood v2 + Deauville]
   │       15-16  Bootstrap C-index, Schoenfeld, DCA, tdROC, calibration, Deauville
   │
   ├── [Phase 2 - Figures main]      20-24  Fig1, Fig2, Fig3, Fig4, Fig5
   │
   ├── [Phase 3 - Figures supplemental]  30-37  SuppFig1..10 + visual abstract
   │
   ├── [Phase 4 - Reviewer rang A]
   │       46  Cox continuous benchmark (M_a, M_b vs JLCM)
   │       47  Frank-style day-28 refit
   │       48  Ridge λ sensitivity + Firth
   │
   └── [Phase 5 - Build docx]
           59  build_blood_article_v8_9.py  →  Blood_article_v8_9.docx + supplemental
```

---

## Quick verification (sanity checks)

To verify the package independently of the full pipeline, run a single key script:

```bash
cd blood_article_package/scripts
python 04_cox_univariate.py    # Recomputes HR EFS 17.7, HR OS 8.4 from input/
```

Expected console output:
- HR EFS high-risk vs low-risk : ≈17.7 (95% CI ~6.3-50.0)
- HR OS : ≈8.4 (95% CI ~3.1-22.8)
- C-index EFS univariate : 0.81

For a full check of figure regeneration:

```bash
python 99_audit_visuel_low_risk_high_risk.py
```

Regenerates all 16 figures and verifies no "BON"/"MAUVAIS"/French residual.

---

## GitHub repository

The project repository is `https://github.com/alessiocg/alycante-ctdna-lysarc-2026` (`alessiocg` is the personal GitHub username of the first author, A. Claudel). The repository is **private until publication** and will be made public upon acceptance. Reviewer access is granted via a time-limited token included in the cover letter.

---

## Versions / change log

| Version | Date | Key change |
|---|---|---|
| v1 to v7 | 17-22 May | First draft, iterative rang-A reviews, benchmark Blood style |
| v8 (initial) | 22 May | First version with full Title Page, 19 SuppTables, accents corrected |
| v8.1 / v8.2 | 22-23 May | Word count compression then re-decompression |
| v8.3 / v8.4 | 23-24 May | Inspection findings reviewer + Title Page Blood + cohérence chiffres |
| v8.5 | 24 May | Réécriture style "lymphome paper" (récit clinique en surface, biostat en profondeur) |
| v8.6 | 24 May | Nettoyage liste d'auteurs (correction d'une attribution erronée résiduelle d'un draft initial) |
| v8.7 | 27 May | 6 corrections : MAR-likelihood explicite, cascade 48 paired / 6 baseline-only / 3 D14-only, seed criterion clarifié, train-rich/deploy-early en avant, titles ctDNA vs PET, Toxicity resserrée |
| v8.8 | 27 May | URL GitHub `alessiocg/alycante-ctdna-lysarc-2026` ajoutée dans Data Sharing Statement |
| **v8.9** | **27 May** | **Propagation : "paired" + seed criterion harmonisés dans Abstract + Limitations + SuppTable S14** |

Detailed change logs are in `REVIEW_*.md` files (12 reports).

---

## Submission status

- ✅ Manuscript main + supplemental compliant with Blood limits (Abstract 247/250, Body 4378/4500, Key Points ≤140 chars)
- ✅ 50 references in AMA format
- ✅ Title Page Blood (auteurs + corresponding + Word counts + Data Sharing Statement)
- ✅ All 19 SuppTables and 12 SuppFigures explicitly cited
- ✅ All figures with low-risk/high-risk labels (no French residuals)
- ✅ All CSV files translated to English
- ✅ Package autonomous (no NAS/Temp dependency, BLOOD_PKG_ROOT relocatable)
- 🟡 **Pending PI action** : await ALYCANTE final analysis (Houot et al. JCO 2026) acceptance for companion submission to Blood
- 🟡 **Pending PI action** : confirm all coauthor disclosures align with parent paper

---

## Contact

For questions about reproducibility or to obtain access to the private GitHub repository before publication, contact the corresponding author (marie-helene.delfau@aphp.fr) or the first author (alexis.claudel via institutional email).
