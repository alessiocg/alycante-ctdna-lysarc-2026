# ALYCANTE — Day-14 ctDNA biomarker substudy

**Status:** Blood submission package **v8.9** — submission-ready (29 May 2026)
**Companion paper:** Houot et al., ALYCANTE final analysis, *J Clin Oncol* 2026 (in revision)
**Repository visibility:** 🌍 **Public** (open for audit). Patient-level data are **not** versioned here.

> ⚠️ **No patient-level data is in this repository.** All analyses run against the source CRF on the secure AP-HP NAS. Only code, the manuscript files, aggregate metrics (group-level CSVs), and figures are committed here — enough to audit every number in the paper without exposing any individual record.

---

## What is this project, in plain English?

**ALYCANTE** is a French academic phase 2 trial (sponsored by LYSARC): **axicabtagene ciloleucel (axi-cel)** CAR T-cell therapy as **second-line** treatment for **relapsed/refractory large B-cell lymphoma (R/R LBCL)** in patients **ineligible for autologous stem-cell transplantation**. The trial enrolled 62 patients across French centers; the primary analysis is Houot et al., *Nat Med* 2023, and the final analysis is in revision at *JCO* (2026).

**This biomarker substudy** answers one question: *can we tell, within two weeks of the CAR-T infusion, which patients are heading toward relapse?* The marker is **circulating tumor DNA (ctDNA)** measured serially in plasma by **CAPP-Seq** (targeted deep sequencing). We quantified ctDNA at 7 post-infusion timepoints (D0, D14, M1, M3, M6, M9, M12) in 57 patients with usable longitudinal samples (a pre-leukapheresis D-5 sample is collected for assay setup but is not used for training).

**Statistical approach.** Instead of thresholding a single timepoint, we fit a **Joint Latent Class Mixed Model (JLCM)** that models, simultaneously, (a) the longitudinal ctDNA trajectory and (b) the time-to-relapse — and uses that joint structure to assign each patient to one of two latent classes. At **day 14** (after the first wave of CAR-T expansion) the trained model is deployed via `predictClass()` to label a new patient **low-risk** or **high-risk**. This is the *train-rich, deploy-early* design.

**Headline result** (day-14 ctDNA-JLCM, n = 44 classifiable):
- **22 high-risk** → 18 lymphoma EFS events (82% relapsed/progressed; the other 4 died of treatment-related toxicity or intercurrent illness, censored).
- **22 low-risk** → 3 lymphoma EFS events (14%, all late ≥ 17 months); 1 further patient died of intercurrent illness, censored.
- **HR EFS 15.1** (95% CI 5.1–44.3), bootstrap-corrected C-index **0.81**; **HR OS 8.4** (3.1–22.8), C-index 0.80.
- EFS = **lymphoma-specific events only** (relapse / progression / lymphoma death); non-lymphoma deaths are censored. OS = all-cause death (standard).
- Outperforms day-14 PET (Deauville ≥4), day-14 single-timepoint ctDNA, and month-3 complete metabolic response.
- **External validation** in a Henri-Mondor real-world cohort (n = 18): HR EFS 8.32 (1.98–34.94), C-index 0.81 — see the cross-pipeline note below.

---

## Repository structure

```
.
├── README.md                                ← you are here
├── LICENSE                                  ← MIT (code only)
├── blood_submission/                        ← ★ Blood manuscript v8.9 (canonical) ★
│   ├── README.md                            ← detailed package readme
│   ├── reviews/                             ← change logs (v8.8→v8.9, final audits, robustness check)
│   ├── explorations/                        ← EXPLORATORY analyses (NOT part of the submission)
│   │   ├── EXPLO_lea_extended_validation.md ← Léa cohort using all timepoints (D0→M12)
│   │   └── EXPLO_lea_drop_investigation.md  ← why performance drops past D14 (pipeline mismatch)
│   ├── output/
│   │   ├── Blood_article_v8_9.docx          ← Main manuscript (Blood format)
│   │   ├── Blood_article_v8_9.md            ← Source markdown (single source of truth)
│   │   ├── Blood_article_v8_9_supplemental.docx
│   │   ├── Blood_cover_letter_v8_9.{docx,md}← Cover letter (corresponding author)
│   │   ├── figures/                         ← Fig 1–5 + SuppFig S1–S13 + Visual abstract (PNG + PDF)
│   │   └── tables/                          ← Aggregate CSVs (Table 1–2, SuppTable S1–S19)
│   └── scripts/                             ← reproducibility scripts (R + Python)
│       ├── _paths.{R,py}                    ← portable path resolver (BLOOD_PKG_ROOT)
│       ├── data_prep/00*_*.{R,py}           ← Phase 0: CRF → tidy data
│       ├── 01–11_*.{R,py}                   ← Phase 1: JLCM + Cox + NRI + external validation
│       ├── 15–16_*.{R,py}                   ← Phase 1bis: bootstrap C-index, Schoenfeld, Deauville
│       ├── 20–24_fig*.{py,R}               ← Phase 2: main figures
│       ├── 30–37_fig_supp*.py               ← Phase 3: supplemental figures
│       ├── 46–48_*.R                        ← Phase 4: reviewer benchmarks (Cox continuous, Frank-style, ridge λ)
│       ├── 59_build_blood_article_v8_9.py   ← Phase 5: builds the .docx from the .md source
│       ├── 99_audit_visuel_*.py             ← sanity check: regenerates all figures from CSV
│       ├── extend_lea_all_timepoints.py     ← exploratory: extended Léa cohort builder
│       ├── investigate_lea_drop.py / ...    ← exploratory: pipeline-mismatch investigation
│       ├── run_all.{sh,ps1}                 ← single-command pipeline
│       └── requirements.txt
├── revue_litterature/                       ← Literature review (earlier project phase)
├── scripts_figures/                         ← Earlier clinical figure scripts (legacy)
├── figures/                                 ← Earlier figure outputs
└── docs/                                    ← Methodology memos
```

The canonical working folder is **`blood_submission/`**. Everything else is earlier project context.

---

## How a reader can verify the work

The package in `blood_submission/` is **autonomous**: it carries its own README, `requirements.txt`, and a `_paths` resolver. The only thing not in the repo is the patient-level source data (kept on the AP-HP NAS).

### Browse the manuscript

Open `blood_submission/output/Blood_article_v8_9.docx` — the Blood-formatted main text (Intro→Discussion ≈ 4,365 words, Abstract 248/250, 31 references in citation order). The supplemental `Blood_article_v8_9_supplemental.docx` contains **19 SuppTables and 13 SuppFigures**. The cover letter is `Blood_cover_letter_v8_9.docx`.

### Trace any headline number to its script

| Claim in the manuscript | Script | Output |
|---|---|---|
| HR EFS 15.1, C-index 0.81 | `04_cox_univariate.py` | `output/tables/cox_univariate_metrics.csv` |
| HR OS 8.4 | `04_cox_univariate.py` | idem |
| Multivariable adjusted HR EFS 14.9; apparent C-index 0.86 EFS / 0.82 OS | `05_cox_multivariate_v2.py` + `30_fig_supp_bootstrap_cindex.py` | `output/tables/cox_multivariate_v2_metrics.csv`, `SuppTable_bootstrap_cindex.csv` |
| ctDNA-JLCM vs MTV-JLCM κ = 0.32 | `24_fig5_ctdna_vs_mtv.py` | `output/tables/SuppTable_concordance.csv` |
| External validation HR EFS 8.32 (Henri-Mondor) | `11_validation_lea.R` | Figure 4 + manuscript text |
| 18/22 + 3/22 = 21 lymphoma EFS events (n = 44) | `04_cox_univariate.py` + `master_dataset.csv` | computed from CRF merge (lymphoma-specific definition) |

### Reproduce the whole pipeline

With the patient source data placed in `blood_submission/input/`:

```bash
cd blood_submission/scripts
bash run_all.sh        # Linux/macOS
.\run_all.ps1          # Windows PowerShell
```

Phase 0 (data prep, optional) → 1 (modeling) → 1bis (benchmarks) → 2 (figures) → 3 (supplemental figures) → 4 (reviewer sensitivity analyses) → 5 (build .docx). Run from anywhere by exporting `BLOOD_PKG_ROOT=/abs/path/to/blood_submission`.

---

## The cross-pipeline finding (why validation is day-14 only)

The Henri-Mondor validation cohort was deliberately processed through the **routine clinical** variant-calling pipeline — analyst-supervised, no statistical phased-variants filtering — which is **different** from the trial-grade phased-variants pipeline used to train on ALYCANTE. This is a real-world deployment test, not a controlled re-analysis.

- **At day 14 the two pipelines converge**: the classifier holds (HR 8.32) even though the routine pipeline detects **zero** MRD-negative samples at D14 (vs 45% in ALYCANTE). The classifier works on *relative* ctDNA differences, not on an absolute clearance threshold.
- **Beyond day 14 the pipelines diverge sharply**: once patients enter remission, the routine pipeline can no longer separate residual tumor signal from clonal hematopoiesis and panel noise. The median residual ctDNA deviates by **> 6 log₁₀** from M1 onward in the low-risk class — a phase transition between D14 and M1, not a gradual drift (supplemental Figure S13).

**Conclusion:** day 14 is both the clinically actionable timepoint and the **deployment boundary** for the current classifier under a routine NGS pipeline. Extending later requires either pipeline harmonization or patient-specific variant tracking. The exploratory analyses behind this are in `blood_submission/explorations/` (not part of the submitted paper; candidate material for a methods follow-up).

---

## Key methodological choices (read before reviewing the code)

1. **`hEG` is already log10-transformed in the source CSV** — never re-transform. The model fits `log10(hEG)`, the natural scale of ctDNA dynamics.
2. **JLCM seed = 123, hard-coded.** `Jointlcmm()` with `random=~time` is initialization-sensitive. Seed 123 was selected from a pre-specified 20-seed sweep (`data_prep/00b_reseed_jlcm_rt.R`) on `predictClass` stability, with BIC as tie-breaker. Some seeds crash `predictClass()`; see SuppTable S14.
3. **`predictClass()` is the deployment operator.** Trained on the 57 patients with ≥1 exploitable timepoint (5 of 62 mFAS excluded: missing D14 sample or sequencing failure); deployed at D14 on the truncated trajectory. 44 of the 57 had complete IPI + baseline MTV and entered all Cox/KM analyses.
4. **EFS = lymphoma-specific.** Relapse, progression, or lymphoma-related death. Non-lymphoma deaths (toxicity, intercurrent illness) are **censored** — ctDNA tracks the lymphoma, not unrelated mortality. OS keeps the standard all-cause definition. The historical "Death without progression" regex bug (which mis-counted non-lymphoma deaths) is fixed in `data_prep/00a_prepare_data_lcmm.R`.
5. **R/R metrics filter follow-up.** For R/R12 / R/R24 (Se, Sp, PPV, NPV), patients censored before the horizon are excluded, not treated as "no R/R". `rr_strict_mapping.csv` codifies this.
6. **MAR-likelihood for missing timepoints.** `Jointlcmm()` handles missing-at-random natively — no imputation. Inputs: 48 paired (D0+D14), 6 baseline-only, 3 D14-only = 57.

---

## Environment

| Component | Version | Used for |
|---|---|---|
| R | 4.3.1 | JLCM (`lcmm`), survival (`survival`, `survminer`, `coxphf`, `pROC`) |
| Python | 3.11 | Cox (`lifelines`), figures (`matplotlib`), data prep (`pandas`, `openpyxl`) |
| Node.js | 24 | (legacy) literature-review Word generation (`docx`) |

```bash
pip install -r blood_submission/scripts/requirements.txt
# R:
# install.packages(c("lcmm","survival","survminer","coxphf","pROC"))
```

---

## Citation

1. **This biomarker substudy:**
   > Claudel A, Lemoine J, Delfau-Larue M-H, Houot R, on behalf of the ALYCANTE biomarker substudy investigators and the LYSARC. Day-14 ctDNA joint latent class modeling stratifies risk in transplant-ineligible R/R large B-cell lymphoma after axi-cel. *Blood*. 2026; submitted.
2. **Parent trial:**
   > Houot R, Bachy E, Cartron G, et al. Axicabtagene ciloleucel as second-line therapy in large B-cell lymphoma ineligible for autologous stem-cell transplantation: a phase 2 trial (ALYCANTE primary analysis). *Nat Med*. 2023;29(10):2593-2601.
   > Houot R, Lemoine J, Claudel A, et al. ALYCANTE final analysis. *J Clin Oncol*. 2026; in revision.

---

## License

Code: [MIT](LICENSE). Manuscript text and figures: © 2026 the authors (LYSARC + AP-HP), all rights reserved until publication.

---

## Authors

- **Alexis Claudel** — first author (Henri-Mondor Biological Immunology, AP-HP). GitHub: [@alessiocg](https://github.com/alessiocg).
- **Julien Lemoine** — clinical hematology lead (AP-HP, Université Paris Cité).
- **Marie-Hélène Delfau-Larue** — corresponding author, head of Biological Immunology, Henri-Mondor (AP-HP, UPEC, INSERM U955). `marie-helene.delfau@aphp.fr`
- **Roch Houot** — senior author, ALYCANTE principal investigator (CHU Rennes, INSERM UMR 1236, EFS).
- **+ ALYCANTE final-analysis core team** (alphabetical, see manuscript Title Page).

Statistical and code review with assistance from **Claude** (Anthropic).

---

*Last updated: 29 May 2026 (v8.9 submission-ready; repository public for open audit).*
