# ALYCANTE — Day-14 ctDNA biomarker substudy

**Status :** Blood submission package **v8.9** ready (28 May 2026)
**Companion paper :** Houot et al., ALYCANTE final analysis, *J Clin Oncol* 2026 (in revision)
**Repository visibility :** 🔒 **Private** until publication; will be made public upon acceptance.

> ⚠️ **No patient-level data is versioned in this repository.** All analyses described here run against the source CRF on the secure AP-HP NAS. Aggregate metrics and the manuscript files are included for reviewer verification.

---

## What is this project, in plain English?

**ALYCANTE** is a French academic phase 2 trial (LYSARC sponsorship): **axicabtagene ciloleucel (axi-cel)** CAR T-cell therapy as **2nd-line** treatment in patients with **relapsed/refractory large B-cell lymphoma (R/R LBCL)** who are **ineligible for autologous stem-cell transplantation** (transplant-ineligible, ti-LBCL). The trial enrolled 62 patients across French centers (LYSARC network); the primary analysis was published as Houot et al., *Nat Med* 2023; the final analysis is in revision at *JCO* (2026).

**This biomarker substudy** asks one question: *can we identify, very early after CAR-T infusion, which patients are heading toward relapse?* The marker we study is **circulating tumor DNA (ctDNA)** measured serially in plasma by **CAPP-Seq** (a targeted deep-sequencing assay). We measured ctDNA at 7 post-infusion timepoints (D0, D14, M1, M3, M6, M9, M12) in 57 patients with usable longitudinal samples (a pre-leukapheresis sample at D-5 is collected for assay setup but is not used in the JLCM training set).

**Statistical approach.** Rather than thresholding a single timepoint, we fit a **Joint Latent Class Mixed Model (JLCM)** that simultaneously models (a) the longitudinal ctDNA trajectory and (b) the time-to-event for relapse — and uses this joint structure to assign each patient to one of two latent classes. Then, at **day 14** (already after one cycle of CAR-T expansion), the trained model can be deployed via `predictClass()` to assign a new patient to **low-risk** or **high-risk**, and decisions can follow.

**Headline result.** The day-14 ctDNA-JLCM class separates the cohort strongly:
- 22 patients classified **high-risk** → 18 lymphoma EFS events (82% relapsed/progressed; the 4 others died of treatment-related toxicity or intercurrent illness, censored at death)
- 22 patients classified **low-risk** → 3 lymphoma EFS events (14%, all late ≥17 months); 1 additional patient died of intercurrent illness, censored
- **HR EFS 15.1** (95% CI 5.1–44.3), C-index 0.81; HR OS 8.4 (3.1–22.8), C-index 0.80
  - EFS = lymphoma-specific events only (relapse/progression/lymphoma death); non-lymphoma deaths censored — see §107 of the manuscript
  - OS = all-cause death (standard)
- Outperforms day-14 PET (Deauville ≥4), day-14 single-timepoint ctDNA, and month-3 CMR
- External validation on Henri-Mondor real-world cohort (n=18) directionally confirms

The manuscript (v8.9) develops, justifies, and benchmarks this approach for *Blood* submission.

---

## Repository structure

```
.
├── README.md                                ← you are here
├── LICENSE                                  ← MIT (code only)
├── blood_submission/                        ← ★ Blood manuscript v8.9 (canonical) ★
│   ├── README.md                            ← detailed submission-package readme
│   ├── REVIEW_v8_8_to_v8_9_package.md       ← change log v8.8 → v8.9
│   ├── output/
│   │   ├── Blood_article_v8_9.docx          ← Main manuscript (Blood format)
│   │   ├── Blood_article_v8_9.md            ← Source markdown
│   │   ├── Blood_article_v8_9_supplemental.docx
│   │   ├── figures/                         ← Fig1–5 (main) + SuppFig1–12 + Visual abstract, each in PNG + PDF
│   │   └── tables/                          ← Aggregate CSVs (Table 1, Table 2, SuppTable S1–S19)
│   └── scripts/                             ← 50+ reproducibility scripts
│       ├── _paths.{R,py}                    ← portable path resolver
│       ├── 00*_data_prep/                   ← Phase 0: CRF → tidy data
│       ├── 01–11_*.{R,py}                   ← Phase 1: JLCM modeling + Cox + NRI + validation
│       ├── 15–16_*.{R,py}                   ← Phase 1bis: Bootstrap C-index, Schoenfeld, Deauville
│       ├── 20–24_fig*.py/R                  ← Phase 2: Main figures
│       ├── 30–37_fig_supp*.py               ← Phase 3: Supplemental figures
│       ├── 46–48_*.R                        ← Phase 4: Reviewer benchmarks (Cox continuous, Frank-style, Ridge λ)
│       ├── 59_build_blood_article_v8_9.py   ← Phase 5: Builds the .docx files from the .md source
│       ├── 99_audit_visuel_*.py             ← Sanity check: regenerates all figures from CSV
│       ├── run_all.{sh,ps1}                 ← Single-command full pipeline
│       └── requirements.txt
├── revue_litterature/                       ← Literature review work (earlier project phase)
│   ├── references_pubmed.json               ← 120 PubMed refs (verified)
│   ├── build_revue_doc_v3.js                ← Word doc generator
│   ├── fetch_pdfs.py                        ← Auto-fetch PDFs (PMC + Unpaywall + BiblioInserm)
│   └── ...
├── scripts_figures/                         ← Earlier figure scripts (legacy, ~35 scripts)
├── figures/                                 ← Earlier figure outputs
└── docs/                                    ← Methodology memos
```

The current working folder is **`blood_submission/`**. Everything else is earlier project context.

---

## How a naive reader can verify the work

The full reproducibility package lives in `blood_submission/` and is **autonomous** — it has its own README, requirements file, and `_paths` resolver. The only thing missing from this repo is the patient-level source data (gitignored: kept on the AP-HP secure NAS).

### To browse the manuscript

Open `blood_submission/output/Blood_article_v8_9.docx` — that's the Blood-formatted Word file ready for submission, ~4400 words (Intro → Discussion), Abstract 247/250 words, 31 references in citation-order. Supplemental file `Blood_article_v8_9_supplemental.docx` contains the 19 SuppTables and 12 SuppFigures.

### To verify a specific number from the manuscript

Each headline metric maps to one script. Examples:

| Claim in the manuscript | Script that produced it | Output file |
|---|---|---|
| HR EFS 15.1, C-index 0.81 | `04_cox_univariate.py` | `output/tables/cox_univariate_metrics.csv` |
| HR OS 8.4 | `04_cox_univariate.py` | idem |
| Multivariable C-index 0.84 + .632+ optimism | `05_cox_multivariate_v2.py` + `30_fig_supp_bootstrap_cindex.py` | `output/tables/SuppTable_bootstrap_cindex.csv` |
| ctDNA-JLCM vs MTV-JLCM κ = 0.32 | `24_fig5_ctdna_vs_mtv.py` | `output/tables/SuppTable_concordance.csv` |
| External validation HR EFS 8.3 (Henri-Mondor) | `11_validation_lea.R` | (output in figure 4 + manuscript text) |
| 18/22 + 3/22 = 21 lymphoma EFS events in n=44 | `04_cox_univariate.py` + `master_dataset.csv` | (computed from CRF merge ; lymphoma-specific definition) |

### To reproduce the entire pipeline

You need the patient source data, which is not in this repo. With that data placed in `blood_submission/input/`:

```bash
cd blood_submission/scripts
bash run_all.sh                    # Linux/macOS
# or
.\run_all.ps1                      # Windows PowerShell
```

The pipeline runs Phase 0 (data prep, optional — inputs are pre-processed by default) → Phase 1 (modeling) → Phase 1bis (benchmarks) → Phase 2 (figures) → Phase 3 (supplemental figures) → Phase 4 (reviewer-asked sensitivity analyses) → Phase 5 (builds the .docx).

To run from a different location:
```bash
export BLOOD_PKG_ROOT=/absolute/path/to/blood_submission  # bash
$env:BLOOD_PKG_ROOT = "C:\absolute\path\to\blood_submission"  # PowerShell
```

---

## Key methodological choices (read this before reviewing the code)

1. **`hEG` is already log10-transformed in the source CSV** — never re-transform. We use `heg` as the linear-scale haploid Equivalent Genome quantity, but the longitudinal model fits `log10(hEG)` because that's the natural scale of ctDNA dynamics.

2. **JLCM seed = 123, hard-coded.** R's `Jointlcmm()` with `random=~time` is sensitive to initialization. We pre-specified a 20-seed sweep (`00b_reseed_jlcm_rt.R`); seed 123 was selected on the basis of **`predictClass` stability** (the operational criterion for a deployable classifier) with BIC as a secondary tie-breaker. Seeds 456, 2024, etc. crash `predictClass()`. See SuppTable S14 for seed-stability sweep results.

3. **`predictClass()` is the deployment operator.** The model is **trained on the 57 ALYCANTE patients with at least one exploitable ctDNA timepoint** (5 of the 62 mFAS patients excluded for missing day-14 sample or technical sequencing failure) and is **deployed** at day 14 via `predictClass()` on the day-14 truncated trajectory — this is the *train-rich, deploy-early* design that the manuscript emphasizes. Of the 57 trained, 44 had complete IPI + baseline-MTV covariates and entered all reported Cox/KM analyses.

4. **Filter follow-up for R/R metrics.** When computing R/R12 or R/R24 (Se, Sp, PPV, NPV), patients censored before the horizon (`efs_time < 12m` AND `efs_event == 0`) must be **excluded**, not treated as "no R/R". This is critical for the sensitivity/specificity table in the manuscript.

5. **R/R = strict.** Relapse OR progression only — censoring is censoring, not "no R/R". `rr_strict_mapping.csv` codifies this.

6. **MAR-likelihood for missing ctDNA timepoints.** `Jointlcmm()` natively handles missing-at-random (MAR) — we do not impute. Inputs have 48 paired (D0+D14), 6 baseline-only, 3 D14-only = 57 patients eventually classifiable.

---

## Environment

| Component | Version | Used for |
|---|---|---|
| R | 4.3.1 | JLCM (`lcmm` 2.1.0), survival (`survival` 3.5-7, `survminer`, `coxphf`, `pROC`) |
| Python | 3.11 | Cox univariable/multivariable (`lifelines` 0.27), figures (`matplotlib`), data prep (`pandas`, `openpyxl`) |
| Node.js | 24 | (legacy) literature-review Word document generation (`docx` 9.6) |

Install Python deps :
```bash
pip install -r blood_submission/scripts/requirements.txt
```

Install R deps :
```r
install.packages(c("lcmm", "survival", "survminer", "coxphf", "pROC"))
```

---

## Reviewer access

This repository is private. To grant temporary read access to a *Blood* reviewer, the corresponding author (M.-H. Delfau-Larue) issues a **GitHub time-limited access token** included in the cover-letter accompanying the submission. The reviewer then clones with:
```bash
git clone https://<token>@github.com/alessiocg/alycante-ctdna-lysarc-2026.git
```

Note that even with the access token, the reviewer sees only the **code + manuscript + aggregate metrics**. Patient-level data remains on the AP-HP secure NAS and is not accessible from the repository.

After publication, the repository will be flipped to public.

---

## Citation

If you use these scripts or methodology, please cite:

1. **The biomarker substudy** (this work):
   > Claudel A, Lemoine J, Delfau-Larue M-H, Houot R, on behalf of the ALYCANTE biomarker substudy investigators and the LYSARC. Day-14 ctDNA joint latent class modeling stratifies risk in transplant-ineligible R/R large B-cell lymphoma after axi-cel. *Blood*. 2026; submitted.

2. **The parent trial** (Houot et al., primary and final analyses):
   > Houot R, Bachy E, Cartron G, et al. Axicabtagene ciloleucel as second-line therapy in large B-cell lymphoma ineligible for autologous stem-cell transplantation: a phase 2 trial (ALYCANTE primary analysis). *Nat Med*. 2023;29(10):2593-2601.
   > Houot R, Lemoine J, Claudel A, et al. ALYCANTE final analysis. *J Clin Oncol*. 2026; in revision.

---

## License

Code: [MIT](LICENSE). Manuscript text and figures: © 2026 the authors (LYSARC + AP-HP), all rights reserved until acceptance.

---

## Authors

- **Alexis Claudel** — first author of the biomarker substudy (Henri-Mondor Biological Immunology, AP-HP). GitHub: [@alessiocg](https://github.com/alessiocg).
- **Julien Lemoine** — clinical hematology lead (AP-HP, Université Paris Cité)
- **Marie-Hélène Delfau-Larue** — corresponding author, head of Biological Immunology at Henri-Mondor (AP-HP, UPEC, INSERM U955). Contact: `marie-helene.delfau@aphp.fr`
- **Roch Houot** — senior author, ALYCANTE principal investigator (CHU Rennes, INSERM UMR 1236, EFS)
- **+ ALYCANTE final-analysis core team** (alphabetical, see manuscript Title Page)

Statistical and code review with assistance from **Claude** (Anthropic).

---

*Last updated: 28 May 2026 (v8.9 submission-ready).*
