# ALYCANTE — Blood biomarker submission package

**Manuscript**: *Day-14 ctDNA joint latent class modeling stratifies risk in transplant-ineligible R/R LBCL after axi-cel*
**Companion paper (parent)**: Houot et al., *J Clin Oncol* 2026 (ALYCANTE final analysis; in revision)
**Current version**: **v8.9** (submission-ready, 29 May 2026)
**Corresponding author**: Marie-Hélène Delfau-Larue (marie-helene.delfau@aphp.fr)
**First author**: Alexis Claudel — **Senior author / PI**: Roch Houot

---

## What this package contains

A fully autonomous reproducibility package. **No external NAS or Temp path is required** — inputs live in `input/`, outputs in `output/`, every script resolves paths through `scripts/_paths.{R,py}` (override with `BLOOD_PKG_ROOT`).

```
blood_submission/                              (== blood_article_package/ on the NAS)
├── README.md                                  ← this file
├── reviews/                                   ← change logs & audit reports
│   ├── REVIEW_v8_8_to_v8_9_package.md
│   ├── REVIEW_v8_9_final.md                   (25→26→21 events, citation renumber)
│   ├── REVIEW_v8_9_audit_visuel_PDF.md        (Fig 2 image fix, title-page refs)
│   └── REVIEW_v8_9_jlcm_robustness_check.md   (classification robust to EFS def)
├── explorations/                              ← EXPLORATORY (not part of the submission)
│   ├── EXPLO_lea_extended_validation.md       (Léa with all timepoints D0→M12)
│   └── EXPLO_lea_drop_investigation.md        (pipeline-mismatch root cause)
├── input/                                     ← raw + pre-processed inputs (gitignored: PHI)
│   ├── ALYCANTE_export*.xlsx                  (CRF CDISC, 62 mFAS)
│   ├── ALYCANTE_RNASeq_21OCT2025.xlsx         (EFS/OS + leuca/J0 dates)
│   ├── Donnees.xlsx                           (ctDNA CRF extract)
│   ├── data_lcmm_long.csv                     (ctDNA long, 57 patients × ≤7 TP; EFS = R/R lymphoma strict)
│   ├── master_dataset.csv                     (patient-level; Cox covariates)
│   ├── jlcm_heg_random_time_model.rds         (trained JLCM, seed=123, BIC 1254.6)
│   ├── jlcm_predict_j14.csv                   (day-14 class assignments)
│   ├── rr_strict_mapping.csv                  (R/R12 / R/R24 strict mapping)
│   └── … (MTV model, PET long, derived CSVs)
├── scripts/                                   ← reproducibility scripts (R + Python)
│   ├── _paths.{R,py}                          ← path resolver (BLOOD_PKG_ROOT)
│   ├── data_prep/00a–00g                      ← Phase 0: CRF → tidy data + JLCM fit
│   ├── 01–11                                  ← Phase 1: JLCM, Cox, NRI, validation
│   ├── 15–16                                  ← Phase 1bis: bootstrap C-index, Schoenfeld, Deauville
│   ├── 20–24_fig*                             ← Phase 2: main figures
│   ├── 30–37_fig_supp*                        ← Phase 3: supplemental figures
│   ├── 46–48                                  ← Phase 4: reviewer benchmarks
│   ├── 59_build_blood_article_v8_9.py         ← Phase 5: build .docx from .md
│   ├── 99_audit_visuel_*.py                   ← sanity check (regenerate all figures)
│   ├── extend_lea_all_timepoints.py / investigate_lea_* / deviation_by_timepoint.py
│   │                                            ← exploratory (cross-pipeline analysis)
│   ├── run_all.{sh,ps1}                       ← single-command pipeline
│   └── requirements.txt
└── output/
    ├── Blood_article_v8_9.{docx,md}           ★ Main manuscript
    ├── Blood_article_v8_9_supplemental.docx   ★ Supplemental (19 tables + 13 figures)
    ├── Blood_cover_letter_v8_9.{docx,md}      ★ Cover letter
    ├── tables/                                (30 CSV — Table 1, Table 2, SuppTable S1–S19)
    └── figures/                               (Fig 1–5 + SuppFig S1–S13 + visual abstract)
```

---

## Quick-start — reproduce all results

```bash
cd blood_submission/scripts
pip install -r requirements.txt              # Python 3.11
# R 4.3+: install.packages(c("lcmm","survival","survminer","coxphf","pROC"))
bash run_all.sh                              # Linux/macOS  (.\run_all.ps1 on Windows)
```

The pipeline runs **without Phase 0** by default (inputs pre-processed). To rebuild inputs from raw CRF, enable the Phase 0 block. Relocate anywhere with `export BLOOD_PKG_ROOT=/abs/path/to/blood_submission`.

---

## Execution DAG

```
input/ALYCANTE_export*.xlsx, RNASeq.xlsx, Donnees.xlsx
   │
   ├─ [Phase 0  data_prep/, optional]
   │     00a prepare_data_lcmm.R ──> data_lcmm_long.csv (EFS = R/R lymphoma strict)
   │     00c build_master.py     ──> master_dataset.csv
   │     00e fig_jlcm_all.R       ──> jlcm_heg_random_time_model.rds (seed=123)
   │     00b reseed sweep, 00d LOO folds
   │
   ├─ [Phase 1]  01–03 JLCM/predict/MTV · 04–05 Cox uni/multi · 06 bimarker
   │             07 NRI 12m · 08–09 subgroup/toxicity · 10 Table 1 · 11 Henri-Mondor validation
   ├─ [Phase 1bis] 15–16 bootstrap C-index, Schoenfeld, DCA, tdROC, calibration, Deauville
   ├─ [Phase 2]  20–24 Fig 1–5
   ├─ [Phase 3]  30–37 SuppFig S1–S10 + visual abstract
   ├─ [Phase 4]  46 Cox continuous · 47 Frank-style J28 · 48 ridge λ + Firth
   └─ [Phase 5]  59 build → Blood_article_v8_9.docx + supplemental (+ mirror to revue_litterature/)
```

---

## Quick verification (one script)

```bash
cd blood_submission/scripts
python 04_cox_univariate.py     # EFS = R/R lymphoma strict
```

Expected console output:
- HR EFS high-risk vs low-risk: **≈15.1** (95% CI ~5.1–44.3)
- HR OS: **≈8.4** (95% CI ~3.1–22.8)
- C-index EFS univariate: **0.81**

Full figure regeneration + residual check:
```bash
python 99_audit_visuel_low_risk_high_risk.py    # regenerates all figures; no BON/MAUVAIS/French residual
```

---

## GitHub repository

`https://github.com/alessiocg/alycante-ctdna-lysarc-2026` — **public** (open for audit). `alessiocg` is the first author's (A. Claudel) personal GitHub username. Patient-level data are **not** versioned (gitignored as PHI); only code, manuscript, aggregate metrics, and figures are committed.

---

## Versions / change log

| Version | Date | Key change |
|---|---|---|
| v1–v7 | 17–22 May | First draft, iterative rang-A reviews, Blood-style benchmark |
| v8 | 22 May | Full Title Page, 19 SuppTables, accents |
| v8.1–v8.4 | 22–24 May | Word-count compression/decompression, Title Page Blood, number coherence |
| v8.5 | 24 May | "Lymphoma-paper" style rewrite |
| v8.6 | 24 May | Author-list cleanup |
| v8.7 | 27 May | MAR-likelihood explicit; 48 paired / 6 baseline-only / 3 D14-only cascade; seed criterion; train-rich/deploy-early |
| v8.8–v8.9 | 27 May | GitHub URL in Data Sharing; "paired" + seed harmonized |
| v8.9 (rev.) | 28 May | Citation renumber (50→31, citation-order); Fig 2 image fix; title-page ref count |
| v8.9 (rev.) | 28 May | **EFS redefined lymphoma-specific** (regex bug fix; HR EFS 17.7→15.1, events 26→21) |
| **v8.9 (final)** | **29 May** | **Cross-pipeline robustness reframe (Option 2): SuppFig S13; D14 = deployment boundary** |
| **v9.0 (V4 rebuild)** | **15 Jun** | **ctDNA MRD ground truth re-derived from FV reports (scripts 50–56); JLCM robust to whitelist definition (27 R/R, RR@12m 100/0); honest LOO-landmark 57/57 (Se/Sp 100% @12m); clean external validation Léa (n=46, log-rank p<0.0001). Manuscript refonte on V4 in progress.** |

Detailed reports in `reviews/` (V4 rebuild: `reviews/REVIEW_v9_0_v4_rebuild.md`). Exploratory analyses behind the cross-pipeline finding in `explorations/`.

---

## Submission status

- ✅ Main + supplemental within Blood limits (Abstract 248/250, Body 4365/4500, Key Points ≤140 chars)
- ✅ 31 references, AMA format, citation-order
- ✅ Title Page Blood (authors, corresponding, word counts, Data Sharing Statement)
- ✅ 19 SuppTables + 13 SuppFigures, all cited
- ✅ EFS = lymphoma-specific (relapse/progression/lymphoma death; non-lymphoma deaths censored); OS = all-cause
- ✅ Cover letter ready (`output/Blood_cover_letter_v8_9.docx`)
- ✅ Cross-pipeline validation reframed; D14 deployment boundary documented (SuppFig S13)
- ✅ Package autonomous (`BLOOD_PKG_ROOT` relocatable); GitHub public for audit
- 🟢 **V4 rebuild** (FV-sourced MRD truth, scripts 50–56) confirms the v8.9 prognostic result from a trusted source and adds a clean external validation (Léa routine CAR-T, log-rank p<0.0001); see `reviews/REVIEW_v9_0_v4_rebuild.md`
- 🟡 **Manuscript refonte on V4 in progress**: recompute Cox/discrimination on V4 classes, then refresh main text + figures + supplement to rest on the FV-sourced ground truth
- 🟡 **Pending PI action**: coordinate companion submission with ALYCANTE FA (Houot et al. JCO 2026) acceptance; confirm coauthor disclosures align with parent paper

---

## Contact

Reproducibility questions: corresponding author (marie-helene.delfau@aphp.fr) or first author (alexis.claudel, institutional email).
