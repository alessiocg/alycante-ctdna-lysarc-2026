# REVIEW v9.0 — V4 rebuild: ctDNA MRD ground truth re-derived from FV reports + clean external validation

**Date**: 15 June 2026
**Scope**: independent re-derivation of the ctDNA MRD ground truth from the phased-variant (FV)
reports, replacing the historical `Donnees_brutes2` extract; refit of the JLCM; honest internal
LOO-landmark; and a clean external validation on the routine CAR-T cohort (Léa).

## Motivation
The v8.9 analysis rests on `data_lcmm_long.csv`, itself derived from a doublet/quota extract
(`Donnees_brutes2`) whose provenance became untrustworthy. We rebuilt the MRD truth **from the
source FV reports** and checked whether the published result survives a trusted re-derivation.

## Method (scripts `50–56`)
1. **`50_v4_rebuild_wl_from_fv.py`** — read each `<NIP>_report.xlsx` (`PV_Summary`); exclude any
   phased variant whose row is filled non-white (orange = low quality; grey/beige theme = expert
   artifact; blue = polymorphism). 425/9200 PV excluded. Build 4 whitelist (WL) versions by the
   **selection** criterion (met on ≥1 timepoint):
   - V1 `Common_UMI≥1` · V2 `≥10` · V3 `≥1 & VAF_ratio>0.3` · **V4 `≥10 & VAF_ratio>0.3` (reference)**
   WL sizes 5917 / 5103 / 5431 / 4842; V1→V4 loses 1075 PV (18%, median 7/patient).
2. **`51_v4_heg_compute.py`** — physical marker, no offset/anti-log:
   - MRD+ (≥2 WL doublets detected, `Common_UMI≥1`): `heg = log10(pooled_UMI_fraction × cfDNA_hEG)`
   - MRD− : floor B `heg = log10(cfDNA_hEG / (WL_size_V × Profondeur_UMI))` = LOD 1/PCU_V
   - `cfDNA_hEG = ADN_total_ng / 0.0033` (gold source: 'suivi cfDNA').
3. **`52_v4_jlcm_4wl.R`** — `Jointlcmm` (seed=123) per WL version.
4. **`53_v4_loo_landmark.R`** — leave-one-out, out-of-sample `predictClass` on ≤J14 data; timeROC IPCW.
5. **`54_v4_lea_revalidation.R`** — V4 model frozen → `predictClass` on the routine cohort → timeROC.
6. **`55_v4_figures.R`** — all `Fig_v4_*` figures.
7. **`56_v4_lea_clean_builder.py`** — routine cohort, clean recipe (mean filtered VAF: germline VAF>0.35,
   gnomAD>0.001, CHIP genes excluded), `heg = log10(VAF_filtered × Cell_Free_DNA)`, floor B for MRD−.
   Output anonymised (`LEA001…`); name↔ID map kept private (git-ignored).

## Results
- **JLCM is robust to the WL definition**: all 4 versions give the SAME split — **27 R/R patients,
  RR@12m 100% / 0%, 26 events**. The joint survival anchors the latent classes; the floor/PCU choice
  is immaterial to classification (≥96% concordance). **V4 fixed as reference** (cleanest WL, no loss
  of prognostic signal).
- **The rebuild reproduces the published prognostic effect** (n_bad ≈ 27, RR@12m 100%/0%) — now from a
  trusted source. Conclusions of v8.9 are confirmed, not changed.
- **LOO-landmark V4 (honest, out-of-sample)**: **57/57** patients classifiable at J14;
  **@12m Se/Sp/PPV/NPV = 100%**; @24m Se 84 / Sp 100 / NPV 83. (PCU-correct floor made all 57
  classifiable vs 33 previously.)
- **External validation (Léa, routine CAR-T)**: 46/54 classified, 25 events;
  **@12m Se/Sp/PPV/NPV = 100%**; @24m Se 86 / Sp 100 / NPV 86; **log-rank p<0.0001**.
- **Cross-platform scale offset ~1.7 log** between MRD+ distributions (ALYCANTE UMI-phased median 3.39
  vs Léa VAF-routine median 1.70) — yet the frozen model transfers **perfectly @12m**. The model
  classifies on **clearance dynamics**, not absolute level: model output (p persistent) separates
  outcome identically in both cohorts despite the input offset (see `Fig_v4_scale_offset_transfer.png`).

## Figures (`output/figures/`)
`Fig_v4_trajectories[_CI].png`, `Fig_v4_km_alycante[_atrisk].png`, `Fig_v4_km_lea_validation[_atrisk].png`,
`Fig_v4_timeROC_12m.png`, `Fig_v4_survival_predicted.png`, `Fig_v4_scale_offset_transfer.png`.

## PHI / reproducibility
All inputs (FV reports, cfDNA Excel, Base CART, derived CSVs, `.rds`, the private name map) live in
`input/` and are git-ignored. Scripts resolve paths via `_paths.{R,py}` (`BLOOD_PKG_ROOT`); no NAS or
user path is hard-coded. Only code + aggregate figures are committed.

## Status
Manuscript **refonte on V4 data in progress**: recompute Cox / discrimination on the V4 classes,
then update main text + figures + supplement to rest on the trusted FV-sourced ground truth and add
the clean external validation. v8.9 numbers are confirmed by this rebuild in the interim.
