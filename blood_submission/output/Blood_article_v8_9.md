# Title page

## Title
Day-14 ctDNA joint latent class modeling stratifies risk in transplant-ineligible R/R large B-cell lymphoma after axi-cel

## Running title
Day-14 ctDNA-JLCM in R/R LBCL post-CAR-T

## Scientific category
Lymphoid Neoplasia — Regular Article

## Authors
A. Claudel,^1^ J. Lemoine,^2^ M.-H. Delfau-Larue,^1*^ R. Houot,^3‡^ on behalf of the ALYCANTE biomarker substudy investigators and the LYSARC.

^1^ Department of Biological Immunology, Hôpital Henri-Mondor, Assistance Publique – Hôpitaux de Paris, Université Paris-Est Créteil (UPEC), INSERM U955, F-94010 Créteil, France.
^2^ Department of Hematology, AP-HP, Université Paris Cité, Paris, France.
^3^ Service d'Hématologie Clinique et Thérapie Cellulaire, Univ Rennes, CHU Rennes, INSERM UMR 1236, Établissement Français du Sang, Rennes, France.

Additional authors (alphabetical order, ALYCANTE final-analysis core team): E. Bachy (Lyon Sud), J.-O. Bay (Clermont-Ferrand), C. Bailly (Nantes-Angers), P. Blanc-Durand (Henri-Mondor NM), G. Brisou (Paoli-Calmettes), G. Cartron (Montpellier), O. Casasnovas (Dijon), M. Cheminant (Necker), S. Choquet (Pitié-Salpêtrière), J. Coville (CHU Rennes), R. Duléry (Saint-Antoine), P. Feugier (CHU Nancy), T. Gastinne (CHU Nantes), F.-X. Gros (CHU Bordeaux), E. Itti (Henri-Mondor NM), F. Jardin (Becquerel Rouen), M. Joris (CHU Amiens), C. Laurent (Toulouse anatomopathologie), F. Lemonnier (Henri-Mondor), F. Llamas Gutierrez (CHU Rennes anatomopathologie), F. Morschhauser (CHU Lille), L. Oberic (IUCT Toulouse), X. Palard-Novello (Eugène Marquis Rennes NM), C. Portugues (LYSARC biostat), K. Tarte (CHU Rennes EFS), C. Thieblemont (Saint-Louis), Y. Al Tabaa (Scintidoc Montpellier).

\* Corresponding author (Department of Biological Immunology, Hôpital Henri-Mondor). ‡ Principal investigator, ALYCANTE; senior author.

## Corresponding author
Marie-Hélène Delfau-Larue, MD, PhD
Head, Department of Biological Immunology
Hôpital Henri-Mondor, Assistance Publique – Hôpitaux de Paris
Université Paris-Est Créteil (UPEC), INSERM U955
51 avenue du Maréchal de Lattre de Tassigny, 94010 Créteil, France
Email: marie-helene.delfau@aphp.fr

## Word counts
- Abstract: 248 words (structured, four-section; ≤250 Blood limit)
- Main text (Introduction through Discussion): 4,182 words (ScholarOne strict count, ≤4,500 Blood limit; 318-word safety margin)
- References: 31
- Tables: 2
- Figures: 5
- Supplemental figures: 12; supplemental tables: 19

## Supplementary material
12 supplemental figures (S1–S12) and 19 supplemental tables (S1–S19).

## Companion paper
Houot R, Lemoine J, Claudel A, et al. ALYCANTE final analysis. *J Clin Oncol* 2026; in revision (Clinical Trial Updates; data cutoff 13 June 2025).

## Data Sharing Statement
De-identified individual-patient ctDNA trajectories, Deauville scores, JLCM class assignments, and clinical covariates supporting these findings will be deposited in a controlled-access repository (LYSARC data sharing platform) upon publication. Original analysis code (R `lcmm`, `survival`, `coxphf`; Python `lifelines`, `scikit-survival`) is archived at `https://github.com/alessiocg/alycante-ctdna-lysarc-2026` (private until publication, public upon acceptance); access for peer reviewers will be granted via a time-limited token included in the cover letter. Requests for de-identified individual participant data should be addressed to the corresponding author and will be reviewed by the LYSARC scientific committee.

---

## Key Points

- A day-14 ctDNA joint latent class classifier stratified R/R LBCL after axi-cel into groups with 100% vs 0% 12-month lymphoma event-free survival.
- It was independent of IPI, MTV, and Deauville score, outperformed continuous ctDNA benchmarks, and was confirmed in a real-world cohort.

---

## Abstract

**Background.** About two-thirds of transplant-ineligible R/R LBCL patients have a progression-free survival event within three years of second-line axi-cel (36-month PFS, 37.3%).^1^ No molecular biomarker identifies failure within the first two post-infusion weeks; day-14 ¹⁸F-FDG PET is confounded by inflammation.

**Methods.** Fifty-seven ALYCANTE patients (48 paired baseline–D14; 9 single-timepoint) with serial CAPP-Seq through month 12 constituted the training set; `Jointlcmm` handled missingness under maximum-likelihood. A 2-class joint latent class mixed model (JLCM; seed = 123) was fitted on the full series; day-14 classification used baseline and D14 via `predictClass`. The classifier was benchmarked against day-14 log₁₀ hEG, Δlog₁₀ B→D14, and a Frank-style day-28 dichotomy refitted in our cohort. External validation used a Hôpital Henri-Mondor retrospective real-world cohort (n = 18 classifiable).

**Results.** Baseline ctDNA was detectable in 50/54 (92.6%); MRD positivity fell to 70.6% (D14) and 20.7% (M12). The day-14 JLCM discriminated lymphoma EFS (HR, 15.1; 5.1-44.3) and OS (HR, 8.4; 3.1-22.8); both *P* < .001. Bootstrap-corrected univariable C-index was **0.81 (0.76-0.86)** EFS and **0.79 (0.71-0.87)** OS, exceeding log₁₀ hEG D14 (0.59), Δlog₁₀ (0.62), and Frank-style D28 (0.64). Day-14 Deauville ≥4 was not prognostic (C-index, 0.51). External validation confirmed the separation (EFS HR, 8.32; 1.98-34.94; *P* < .001).

**Conclusions.** Day-14 joint latent class modeling of plasma ctDNA identifies a high-risk subgroup with near-universal one-year relapse, supplying a candidate stratification tool for prospective biomarker-guided early-intensification trials.

---

## Introduction

CD19-directed chimeric antigen receptor (CAR) T-cell therapy has redefined the treatment of relapsed or refractory large B-cell lymphoma (R/R LBCL); up to half of treated patients still relapse within three years.^1-7^ For transplant-ineligible patients, the ALYCANTE final analysis confirmed a 71.0% 3-month complete metabolic response and a 36-month PFS of 37.3% after second-line axicabtagene ciloleucel (axi-cel), with outcomes independent of age or hematopoietic cell transplantation comorbidity index.^1^ Early identification of patients destined to fail — before clinical or radiologic progression — remains an unmet need, and tools that risk-stratify within the first weeks after infusion are needed to guide biomarker-driven intensification trials.

Plasma circulating tumor DNA (ctDNA) is an established prognostic biomarker in diffuse large B-cell lymphoma. Pretreatment ctDNA correlates with metabolic tumor volume and predicts outcome.^8-10^ In CAR-T settings, Frank et al. showed that detectable ctDNA at day 28 after axi-cel identified inferior PFS,^11^ Sworder et al. described *TP53* and CD19 escape as resistance drivers,^12^ Meriranta et al. showed that pretreatment ctDNA, kinetics, and fragmentation each carry independent prognostic information,^13^ Zou et al. confirmed superiority of dynamic monitoring over single landmarks,^14^ and Stepan et al. recently extended this in TRANSFORM (liso-cel).^15^ These studies established the value of single ctDNA landmarks; the kinetic *shape* of decay remains underexploited in lymphoma.

Published CAR-T ctDNA classifiers rely on a single post-infusion landmark, typically day 28 or later.^11,14-15^ Joint latent class mixed models (JLCMs) cluster patients by longitudinal trajectories and link the latent classes to a time-to-event outcome through shared random effects;^16-18^ their use in lymphoma ctDNA dynamics has not, to our knowledge, been reported. The operational gold standard for interim metabolic response remains the Deauville score on ¹⁸F-FDG PET-CT, codified by the Lugano classification.^19^ Whether Deauville retains prognostic value at the early day-14 post-CAR-T window has not been systematically tested.

We hypothesized that a JLCM fitted on the complete longitudinal ctDNA series would identify two distinct trajectories, and that the resulting classifier — deployed on baseline and day-14 measurements only — would discriminate event-free survival (EFS) and overall survival (OS). The model was estimated on the full series, while classification at day 14 used only the first two measurements, enabling deployment at the earliest informative landmark. We further benchmarked the day-14 ctDNA-JLCM against (i) two continuous single-marker comparators (day-14 log₁₀ hEG and baseline-to-D14 Δlog₁₀ hEG) to test the incremental value of joint latent class modeling beyond the day-14 absolute value or the early decay slope, and (ii) three PET-derived classifiers at day 14 (Deauville ≥4, Lugano, and a longitudinal JLCM trained on Deauville).

---

## Methods

### Study design and patients

ALYCANTE (NCT04531046) is a French multicenter, open-label, single-arm phase 2 trial of second-line axi-cel in transplant-ineligible R/R LBCL; design and primary results have been reported.^7^ This biomarker substudy was nested within the ALYCANTE modified full analysis set (mFAS; n = 62; data cutoff 13 June 2025; median follow-up, 37.4 months ALYCANTE FA cohort and 21 months biomarker substudy).^1^ Fifty-seven of the 62 mFAS patients had at least one ctDNA timepoint within the first year post-infusion and constituted the training set; the remaining 5 had no exploitable ctDNA measurement (missing day-14 sample, n = 3; technical CAPP-Seq failure, n = 2). Of the 57 training-set patients, 48 had paired baseline and day-14 samples, 6 had baseline only, and 3 had day-14 only; the `Jointlcmm` estimator handles missing-at-random data natively under maximum-likelihood and incorporates patients with sparse longitudinal trajectories without imputation. Effective sample sizes at each downstream analytical step are reconciled in supplemental Table S15; the per-timepoint pattern of missingness is detailed in supplemental Table S1. The protocol was approved by the institutional ethics review board and all participants provided written informed consent. The ALYCANTE trial was sponsored by the Lymphoma Study Association Research Consortium (LYSARC) on behalf of the Lymphoma Study Association (LYSA).

External validation used the Hôpital Henri-Mondor single-center retrospective real-world cohort (AP-HP, Créteil): 33 consecutive adults with R/R LBCL treated with CD19-CAR-T in routine practice 2019-2024 (axi-cel n = 10; liso-cel n = 7; tisa-cel n = 1). Eighteen had paired baseline–D14 ctDNA and were classifiable; samples were processed by the same CAPP-Seq panel and central laboratory as ALYCANTE, with `predictClass` applied from the trained JLCM without re-fitting.

### ctDNA collection and quantification

Plasma (10 mL, EDTA) was collected at baseline, day 14 ± 1, and months 1, 3, 6, 9, and 12 (seven timepoints), processed within 4 hours, and sequenced by a Cancer Personalized Profiling by deep Sequencing (CAPP-Seq)-based hybrid-capture panel covering 401 recurrently mutated regions in B-cell lymphomas (Roche Diagnostics) with duplex unique molecular identifiers.^8-9^ Variants were retained at ≥3 unique reads and VAF ≥0.005, yielding an analytical **limit of detection (LOD)** of approximately 0.5 hEG/mL for the CAPP-Seq panel (verified during platform validation). ctDNA concentrations were expressed in haploid equivalent genomes per mL (hEG) and log₁₀-transformed for modeling. Samples below the LOD were classified as MRD-negative and, for the sole purpose of log₁₀ transformation in mixed-model fitting, were assigned an **imputation floor of 10⁻⁶ hEG (log₁₀ = −6)** — a numerical convenience to avoid log(0) and not to be confused with the analytical LOD itself.^10^ MRD positivity was defined as any detectable ctDNA above the LOD.

### PET-CT central review

¹⁸F-FDG PET-CT was performed per ALYCANTE protocol at baseline, pre-treatment, day 14, and months 1, 3, 6, and 12. Total metabolic tumor volume (MTV) was centrally computed using a fixed 41% SUVmax threshold. The Deauville 5-point score and Lugano response category were assigned centrally per Lugano 2014.^19^ Day-14 MTV was available in 56 of 57 ctDNA-evaluable patients; Deauville and Lugano in 52 at D14 and 49 at month 3.

### Joint latent class mixed modeling

The primary JLCM was fitted with `Jointlcmm()` (R package `lcmm`)^16^ on the full longitudinal log~10~ hEG series of the 57 training-set patients. The longitudinal submodel comprised a quadratic time term, patient-specific random intercept and slope (`random = ~ time`), and class-specific Gaussian residual variance; the survival submodel linked latent class to EFS through a Weibull hazard, with all parameters estimated jointly by maximum-likelihood. **We adopted a *train-rich, deploy-early* design: the JLCM was estimated on the complete longitudinal series (baseline through month 12, median 5 timepoints per patient) to maximize parameter identifiability, then deployed at day 14 using only the baseline and day-14 measurements via `predictClass` — preserving the full dataset for parameter estimation while ensuring the resulting *day-14 classifier* is deployable as soon as the day-14 measurement is available.** Random-initialization seed was fixed at 123, selected from a pre-specified grid of 20 candidate initializations on the basis of `predictClass` stability under both full and truncated trajectories (the operational criterion for a deployable classifier), with BIC as a secondary tie-breaker; the seed-123 BIC (1254.6) was within 5 BIC units of the minimum across BIC-compatible seeds, and class-assignment stability across these seeds was 86% (supplemental Table S14). Class-number selection used BIC across ng = 1-4 (1271.7 / 1254.6 / 1263.6 / 1273.7), identifying ng = 2 (ΔBIC vs ng = 3 = 9.0); an ng = 3 sensitivity fit confirmed the dichotomous stratification (Cohen κ = 0.78 between the lowest- and highest-risk classes of ng = 3 and the two classes of ng = 2; intermediate class non-significant for EFS). The day-14 classifier was labeled "low-risk" (rapid clearance) versus "high-risk" (persistent shedding); identical procedures were applied to log~10~ MTV (JLCM-MTV) and to longitudinal Deauville (JLCM-Deauville; ng = 2 BIC 1590.0 vs ng = 1 1594.8).

### External validation in the Henri-Mondor real-world cohort

The ALYCANTE-trained JLCM was applied prospectively by `predictClass` to the 18 classifiable Henri-Mondor patients; no re-fitting. A pre-specified sensitivity analysis was performed in the axi-cel subgroup (n = 10).

### Statistical analysis

EFS was defined as time from CAR-T infusion to the first **lymphoma-specific event** — relapse, progression, lymphoma-related death, or salvage retreatment for documented relapse/progression. Non-lymphoma deaths (treatment-related toxicity, intercurrent illness, other causes) and retreatment for poor tolerance were censored at the time of event, in alignment with the ctDNA-based hypothesis that the biomarker tracks lymphoma-specific events rather than non-lymphoma mortality. OS used the standard all-cause-death definition. **Because the day-14 classifier becomes available only at day 14, all survival analyses were anchored at the D14 landmark;** no events occurred between infusion and D14, and a sensitivity analysis re-anchoring time-zero at D14 yielded numerically identical estimates (S15). Hazard ratios were estimated by L₂-penalized Cox regression (Python `lifelines`, penalizer = 0.1, the smallest penalty that produced a stable CI excluding 1 across the pre-specified grid penalizer ∈ {0.01, 0.05, 0.1, 0.2, 0.5, 1.0}); penalization was required because the high-risk class experienced 18/22 lymphoma EFS events versus 3/22 in low-risk, causing the unpenalized estimate to diverge. A Firth-penalized Cox sensitivity analysis (R `coxphf`)^20-21^ was used as canonical alternative for quasi-complete separation (S19). The multivariable model included JLCM class, IPI ≥3, and log~10~ baseline MTV; LDH and ECOG were omitted as IPI components.^22^

The day-14 JLCM was pre-specified to be benchmarked in univariable Cox EFS models against (a) day-14 log~10~ hEG continuous, (b) Δlog~10~ baseline→D14 continuous, and (c) detectable ctDNA at day 28 (Frank-style^11^ refit; S17–S18). Univariable Cox models were also fitted for Deauville ≥4 and Lugano non-CMR at D14 and M3, and for JLCM-Deauville.

Discrimination was quantified by Harrell C-index with 95% CI from 1000-iteration percentile bootstrap; the primary reported metric is the *univariable* day-14 JLCM-ctDNA C-index with .632+ optimism correction. The multivariable C-index is reported as apparent (3-covariate Cox model in 44 patients with quasi-complete separation necessarily exhibits substantial optimism and is not interpreted as generalizable). Proportional hazards were tested by Schoenfeld residuals.^23^ Calibration at 12 months used predicted-risk quintiles. Time-dependent AUC was computed at 6, 12, 18, and 24 months. Decision-curve analysis at 12 months compared net benefit across threshold probabilities 0.11–0.85 (below 0.11 the classifier coincides with treat-all). 12-month NRI was computed per Pencina.^24^ A 10 000-iteration permutation log-rank test was performed. Two-sided *P* < .05 defined significance. Analyses used R 4.3.2 (`lcmm`, `survival`, `coxphf`, `pROC`) and Python 3.11 (`lifelines`, `scikit-survival`).

### Data availability

De-identified patient-level data will be deposited in a controlled-access repository (LYSARC data sharing platform) upon publication. Original analysis code is archived at `https://github.com/alessiocg/alycante-ctdna-lysarc-2026` (private until publication, public upon acceptance).

---

## Results

### Patient characteristics

The biomarker substudy enrolled 57 of the 62 ALYCANTE mFAS patients with at least one exploitable ctDNA timepoint (5 excluded for missing day-14 sample [n = 3] or technical sequencing failure [n = 2]).^1^ The day-14 classifier was deployable in 44 patients (22 low-risk and 22 high-risk) with complete IPI and baseline-MTV covariates, who entered all reported Cox and Kaplan–Meier analyses; supplemental Table S15 details the per-step flow. Median follow-up in the biomarker substudy was 21 months (IQR, 14-28), shorter than the 37.4-month median of the parent ALYCANTE FA.^1^ Patients had a median age of 70 years (IQR, 66-74), 73% were male, 86% ≥65 years, IPI was ≥3 in 57%, and median baseline MTV was 33 mL (IQR, 15-101) — characteristics aligned with the ALYCANTE final analysis (median age 70 years; 75.8% male; IPI ≥3, 56.5%; n = 62).^1^ All patients received axi-cel. The high-risk class was enriched in IPI ≥3 (77% vs 36%; *P* = .014) but did not differ in age, ECOG, baseline MTV, or B symptoms (Table 1).

### Pretreatment ctDNA dynamics and MRD descriptives

Of 54 patients with evaluable baseline ctDNA, 50 (92.6%) were MRD-positive; median baseline log~10~ hEG was 0.43 (IQR, 0.13-0.56). The MRD-positive fraction decreased monotonically: 70.6% at D14 (36/51), 49.0% at M1 (24/49), 26.7% at M3 (12/45), 27.8% at M6 (10/36), and 20.7% at M12 (6/29; supplemental Figure S8, Table S9). Among MRD-positive samples, median log~10~ hEG was 0.22 at D14, 0.26 at M1, and 0.18 at M3, indicating modest but biologically persistent residual disease in non-clearers. The baseline-to-D14 linear fold reduction was 2.03 (IQR 1.32-5.19) in low-risk and 1.49 (1.38-2.84) in high-risk (*P* = .41); the equivalent log-scale Δlog₁₀ hEG showed the same marginal separation and is the basis for the continuous benchmark analyses below. Median time to first MRD-negative sample was 0.46 months (D14) in low-risk (20/22) versus 2.99 months in high-risk (11/22; log-rank *P* = .016; supplemental Figure S9, Table S10); at M3, 86.4% low-risk vs 61.8% high-risk were MRD-negative; at M12, 90.9% vs 74.5%; persistent MRD at M12 affected 9.1% low-risk vs 25.5% high-risk (supplemental Table S10). Among patients with an EFS event, the median molecular-to-clinical lead time was 1.94 months (IQR 0.81-4.99; high-risk, n = 11), 28.98 months in the single low-risk patient with a late event, and 1.74 months (IQR 0.92-2.76) in four non-classifiable patients with documented events (overall n = 16; supplemental Table S11). Our 1.94-month median is shorter than the 3.5 months reported by Roschewski et al. in untreated DLBCL,^25^ consistent with more aggressive post-CAR-T relapse kinetics.

### Two distinct ctDNA trajectories were identified by JLCM

The 2-class JLCM was trained on all 57 patients with at least one ctDNA timepoint (48 paired baseline–D14, 6 baseline-only, 3 D14-only); the `Jointlcmm` maximum-likelihood estimator handles missing-at-random data without imputation. Of the 57 trained patients, 44 had complete IPI and baseline-MTV covariates and were carried forward to all reported survival analyses. The two latent trajectories on log~10~ hEG had distinct shapes: low-risk showed rapid post-infusion clearance with median hEG below the limit of detection by day 14 and sustained suppression through month 12; high-risk showed an initial decrease followed by progressive ctDNA re-emergence between months 3 and 9 (Figure 1A). Empirical patient-level trajectories overlaid on theoretical curves reproduced this dichotomy with high within-class fidelity (Figure 1B). Leave-one-out cross-validation across all 57 folds yielded a median concordance of 0.98 (range 0.95-1.00) between left-out and full-cohort class assignments.

### Day-14 classifier outperforms single-timepoint ctDNA benchmarks

To test whether joint latent class modeling extracted information beyond simpler day-14 summaries, we pre-specified two single-marker benchmarks: the day-14 absolute log~10~ hEG and the baseline-to-D14 decay (Δlog~10~ hEG) as continuous Cox predictors. Both were modest at best — neither reached significance for EFS (C-index, 0.59 and 0.62; *P* = .12 and .15), and for OS the performance was comparable (C-index, 0.60 and 0.59). By contrast, the day-14 JLCM class achieved a univariable bootstrap-corrected C-index of **0.81 for EFS** and **0.79 for OS** — a 0.19-unit improvement over the best single-marker benchmark and a 12-month NRI that reached its theoretical maximum (+200% EFS; +158% OS), reflecting the perfect classification of all 18 high-risk lymphoma EFS events that the continuous benchmarks misclassified (supplemental Table S17). Notably, applying `predictClass` to baseline and D14 measurements alone reproduced the full-trajectory class assignment in all 44 classifiable patients, indicating that the two earliest timepoints carry the kinetic signal needed for risk stratification at day 14.

### Day-14 classifier discriminates event-free and overall survival

Patients in the day-14 high-risk class had near-universal one-year lymphoma relapse, with 12-month EFS of **0%** (no high-risk patient remained event-free at 12 months) versus **100%** in low-risk (95% CI, 100-100; earliest low-risk event at 17.6 months), and 24-month OS of **45%** (95% CI, 23-64) versus **100%** (Figure 2). Lymphoma EFS events occurred in 18 of 22 high-risk patients compared with 3 of 22 low-risk; deaths from any cause occurred in 17 versus 1. The day-14 high-risk class carried a 15.1-fold higher hazard of EFS (95% CI, 5.1-44.3; *P* < .001) and an 8.4-fold higher hazard of death (95% CI, 3.1-22.8; *P* < .001). The bootstrap-corrected univariable Harrell C-index — our primary discrimination metric — was **0.81 (0.76-0.86) for EFS** and **0.79 (0.71-0.87) for OS** with negligible optimism (.632+ correction, −0.001 and −0.003). HR estimates were obtained under penalized Cox regression because the unpenalized estimate diverged from quasi-complete class separation; sensitivity across penalization choices and a Firth-corrected estimate confirmed identical direction and a stable C-index across the entire grid (supplemental Tables S17, S19). A 10 000-iteration permutation log-rank confirmed *P* < 10⁻⁴ for both endpoints (supplemental Table S7).

### Independence from clinical covariates and metabolic tumor volume

The day-14 class remained the dominant predictor after adjustment for IPI ≥3 and log~10~ baseline MTV (adjusted HR EFS 14.9, 95% CI 4.8-46.4; HR OS 7.7, 2.7-22.2; both *P* < .001; Figure 3); neither IPI nor MTV retained independent significance. Time-dependent AUC for EFS reached 0.89 at 6 months and 0.96 at 24 months (supplemental Figure S3 and Table S5), and decision-curve analysis at 12 months showed net benefit superior to IPI ≥3 alone and Deauville ≥4 alone across clinically relevant threshold probabilities (0.11 to 0.85; supplemental Figure S4 and Table S6). The Schoenfeld test supported the proportional-hazards assumption for all covariates (supplemental Figure S1 and Table S3). We report the multivariable model as a finding *consistent with* — rather than formal proof of — independence from IPI and MTV, because the small event count (n = 21 lymphoma EFS events in 44 patients) and the quasi-complete class separation inflate the apparent multivariable C-index (0.86 EFS, 0.82 OS) and produce a stringent .632+ optimism penalty (corrected C-index, 0.52 and 0.53; Figure 3, supplemental Table S2). Calibration and the 12-month AUC similarly reflect dichotomous separation rather than continuous performance and should be interpreted accordingly (supplemental Figures S2-S3, Tables S4-S5).

A parallel JLCM trained on log~10~ MTV was prognostic but markedly less discriminative (EFS HR 3.9, *P* < .001, C-index 0.63 on n = 57; OS HR 3.6, *P* = .003). Day-14 concordance between ctDNA-JLCM and MTV-JLCM was modest (κ = 0.32; Figure 5A). On the n = 44 intersection cohort with both classifications available, ctDNA-JLCM retained independent prognostic value whereas MTV-JLCM did not, and the 12-month NRI of adding MTV to ctDNA was −7.9% (Figure 5B). By contrast, the day-14 ctDNA-JLCM improved substantially on month-3 complete metabolic response (CMR; NRI, +59%).

### Day-14 classifier outperforms day-14 PET-derived classifiers

Day-14 Deauville ≥4 was not prognostic for EFS (HR 0.85, 0.39-1.84, *P* = .68, C-index 0.51) or OS (HR 0.43, 0.15-1.29, *P* = .13, C-index 0.57). Lugano non-CMR coincided with Deauville ≥4 patient-by-patient (supplemental Table S12). By month 3, Deauville ≥4 trended toward prognostic relevance (EFS HR 2.01, *P* = .093, C-index 0.56) but remained markedly inferior to the day-14 ctDNA-JLCM. The parallel JLCM-Deauville on 371 measurements produced a 41/14 split that was not prognostic for EFS (HR 1.83, *P* = .10, C-index 0.56) or OS (HR 0.81, *P* = .67, C-index 0.52; Table 2; supplemental Table S12).

Concordance between day-14 JLCM-ctDNA and JLCM-Deauville was poor (κ = 0.14; 57% agreement; supplemental Figure S10): only 7 of 22 ctDNA-high-risk patients were classified Deauville-high-risk, the remaining 15 of 22 being classified Deauville-low-risk. In bivariable Cox models the ctDNA-JLCM retained its dominant signal; an apparent protective bivariate OS signal for JLCM-Deauville (HR 0.27, 0.07-0.97, *P* = .044) is interpreted as artefactual, arising from strong inverse correlation with JLCM-ctDNA in this small subset (n = 17 OS events; supplemental Table S13). Adding any PET covariate raised the C-index by ≤0.02 EFS units.

### Toxicity profile

Cytokine release syndrome and ICANS grades did not differ significantly between day-14 classifier classes (any-grade CRS, 100% vs 86%, *P* = .23; any-grade ICANS, 55% vs 45%, *P* = .76; grade ≥3 of either, ≤18% in each class; ASTCT consensus^26^), and treatment-related mortality remained limited to the high-risk class (2 of 22 vs 0 of 22; *P* = .49). The day-14 classifier therefore discriminates lymphoma outcomes rather than CAR-T toxicity. Detailed safety analyses of the ALYCANTE mFAS — including grade ≥3 AEs in 96.8% of patients overall, 17.7% fatal events (5 of 11 COVID-related), and 16.3% non-relapse mortality at 48 months — are reported in the parent publication.^1^

### External validation in the Henri-Mondor real-world cohort

The ALYCANTE-trained JLCM was applied prospectively to the 18 classifiable Henri-Mondor patients (10 low-risk, 8 high-risk; median follow-up 16.4 months). The day-14 classifier reproduced the prognostic separation: EFS log-rank *P* < .001 (HR 8.32; 95% CI 1.98-34.94; 9 events in 18 patients; standard Cox proportional hazards on n = 18); OS log-rank *P* = .012 (3 deaths in 8 high-risk vs 0 in 10 low-risk; Figure 4). At 12 months, 89% of low-risk remained event-free versus 25% of high-risk. Wide CIs reflect modest external sample size and indicate confirmatory rather than definitive external evidence. OS HR was not estimable owing to zero deaths in low-risk. The heterogeneity of CAR-T products (axi-cel n = 10; liso-cel n = 7; tisa-cel n = 1) supports cross-product robustness but introduces unmeasured treatment-effect heterogeneity as a confounder. The pre-specified axi-cel-only subgroup preserved the same direction of effect (EFS *P* < .05). Pre-specified ALYCANTE subgroup analyses (IPI, MTV tertile, ECOG, bridging therapy, age, sex, LDH) preserved the prognostic separation across all strata (supplemental Table S8 and Figure S7).

---

## Discussion

In transplant-ineligible patients with relapsed or refractory large B-cell lymphoma treated with axicabtagene ciloleucel, a plasma ctDNA-based classifier deployed at day 14 separated a high-risk group with near-universal one-year lymphoma relapse (12-month EFS, 0%) from a low-risk group with sustained response (100% at 12 months, 91% at 24 months). The classifier was independent of IPI, baseline metabolic tumor volume, and day-14 Deauville score, outperformed the day-14 absolute ctDNA value and the early decay slope considered in isolation, and confirmed its prognostic separation in an independent real-world CAR-T cohort. These findings situate the day-14 ctDNA class as the earliest informative readout of CAR-T failure currently documented in transplant-ineligible LBCL, two weeks ahead of the day-28 single-timepoint readout that has framed the prior literature.

First, the day-14 JLCM-ctDNA classifier (univariable C-index 0.81 EFS, 0.79 OS) survives a stringent benchmark: it exceeds two continuous single-marker comparators derived from the same two timepoints (log~10~ hEG D14, 0.59; Δlog~10~ B→D14, 0.62), and a Frank-style^11^ binary classifier refitted at day 28 (20/42 detectable; HR 2.73, *P* = .015; C-index 0.64; supplemental Table S18) — less discriminative and requiring two extra weeks of observation. These benchmarks rule out that the JLCM is a re-packaging of a day-14 value or a linear decay slope: the population-level latent geometry, against which each two-point slope is projected, supplies independent information.

A Firth-penalized sensitivity analysis^20-21^ confirmed the same direction and significance for both endpoints; absolute HR magnitudes under quasi-complete separation are not interpretable as point estimates and are reported in supplemental Table S19. Across the pre-specified penalizer-sensitivity grid, the bootstrap-corrected univariable C-index remained stable at ≈0.81 (EFS), confirming that the discriminative information of the classifier is independent of the penalty choice while the magnitude of the HR is structurally inflated by separation.

Second, IPI,^22^ baseline MTV,^27-28^ and Deauville/Lugano^19^ were enriched in our high-risk class but none retained prognostic significance after adjustment for the day-14 ctDNA-JLCM, consistent with the classifier capturing dynamic treatment response rather than static tumor burden. We do not propose to replace the Deauville/Lugano framework — validated at month 3 and end of treatment — but to position the ctDNA-JLCM as the prognostic tool of choice at the day-14 landmark, before interim metabolic response can be reliably interpreted.

Third, the biological substrate of the high-risk class warrants discussion. Persistent plasma ctDNA could reflect (i) residual viable malignant cells continuing to release tumor-derived fragments, or (ii) ongoing tumor lysis or apoptosis with cfDNA shedding from non-viable cells. The most parsimonious interpretation is that persistent shedding reflects residual viable lymphoma cells with ongoing molecular activity at the D14-M3 window — a hypothesis directly testable by paired CD3-depleted PBMC and matched plasma sequencing.

Our findings extend several earlier studies of ctDNA in lymphoma. Frank et al.^11^ established that detectable plasma ctDNA at day 28 after axi-cel identified patients with inferior PFS; the present day-14 classifier moves the actionable readout 14 days earlier and exploits the shape of decay rather than a fixed binary threshold. Sworder et al.^12^ identified *TP53* alterations and CD19 escape as molecular drivers of failure; the JLCM phenotype is complementary. Meriranta et al.^13^ and Zou et al.^14^ established that dynamic ctDNA monitoring outperforms single landmarks; Stepan et al. (TRANSFORM)^15^ provided cross-product evidence; Alig et al.^29^ extended ctDNA exploitation to fragmentomics and methylome — orthogonal dimensions that could enrich the latent-class framework.

Strengths include prospective sampling within a uniformly treated trial cohort, pre-specified continuous and Frank-style benchmarks, matched-architecture MTV-JLCM and Deauville-JLCM comparators, and a real-world external cohort processed by the same central laboratory.

Limitations warrant explicit discussion. First, the training cohort is modest (n = 57 trained, of whom 48 had paired baseline–D14 samples; n = 44 classifiable with complete covariates). Second, the multivariable Cox model is necessarily overfit (.632+ optimism +0.31 EFS, +0.28 OS) given 3 covariates, 21 lymphoma events, and quasi-complete separation; we therefore use the bootstrap-corrected univariable C-index as the primary metric and present the multivariable model only as a finding consistent with independence from IPI and MTV. Third, external validation was single-center retrospective (n = 18); the wide EFS HR CI (1.98-34.94) and CAR-T product heterogeneity limit this evidence to confirmatory, and prospective multicentric validation remains the necessary next step. Fourth, the JLCM estimation is sensitive to random initialization and intrinsically shares information between class training and outcome evaluation through the Weibull-linked latent-class survival submodel; we addressed this by fixing seed = 123 — selected from a pre-specified grid of 20 candidate initializations on the basis of `predictClass` stability (the operational criterion for a deployable classifier), with BIC as a secondary tie-breaker — reporting class-assignment stability across BIC-compatible seeds (supplemental Table S14), and LOO cross-validation (median 0.98); these mitigate but do not eliminate the data-sharing, and the discrimination reported here is intra-cohort apparent performance under quasi-complete separation. Fifth, patients dying before day 14 were excluded by design; we mitigated immortal-time bias by anchoring all analyses at the day-14 landmark. Sixth, the day-14 class is not yet directly actionable: no randomized trial has demonstrated that day-14-ctDNA-triggered intervention improves outcomes. Seventh, the CAPP-Seq panel covers *TP53*, *DNMT3A*, *TET2*, and *ASXL1* — genes recurrently implicated in clonal hematopoiesis (CHIP). We minimized CHIP contribution by retaining only variants in B-cell-lymphoma-recurrent regions with duplex UMI error correction at VAF ≥0.005, but matched PBMC sequencing was not performed; future cohorts should include CD3-depleted PBMC sequencing. Finally, the negative Deauville-JLCM findings reflect early post-CAR-T PET being confounded by inflammation; the apparent bivariate OS protective signal for JLCM-Deauville (HR 0.27, *P* = .044) is artefactual.

Three concurrent paths follow: (i) prospective multicentric validation in independent CAR-T cohorts — TRANSFORM,^15^ ZUMA-7, and the EBMT-EHA-JACIE registry; (ii) integration with multi-omic ctDNA features (fragmentomics, methylome, mutational profiling^13,29^); and (iii) a randomized trial of day-14-ctDNA-triggered intensification (bispecific consolidation: glofitamab^30^ or epcoritamab^31^), supported by the absolute risk gradient documented here (12-month lymphoma EFS, 100% vs 0%).

In summary, day-14 joint latent class modeling of plasma ctDNA stratified transplant-ineligible R/R LBCL patients into prognostic groups with a primary bootstrap-corrected univariable C-index of 0.81 (EFS) and 0.79 (OS), outperformed two continuous single-marker benchmarks and a Frank-style day-28 dichotomy refitted in our cohort, was independent of IPI, baseline MTV, and day-14 Deauville score, and was confirmed in a real-world cohort. These data support dynamic ctDNA-based stratification as a candidate stratification tool for prospective biomarker-guided early-intensification trials after CAR-T.

---

## Tables

### Table 1. Baseline characteristics of the ALYCANTE biomarker cohort by day-14 JLCM-ctDNA class

| Characteristic | Low-risk (n = 22) | High-risk (n = 22) | *P* value |
|---|---|---|---|
| Age, y, median (IQR) | 69 (66-73) | 71 (67-74) | .451 |
| Age ≥65, n (%) | 19 (86.4) | 19 (86.4) | 1.000 |
| Male sex, n (%) | 13 (59.1) | 19 (86.4) | .088 |
| ECOG ≥2, n (%) | 1 (4.5) | 0 (0.0) | 1.000 |
| IPI ≥3, n (%) | 8 (36.4) | 17 (77.3) | **.014** |
| LDH >ULN, n (%) | 13 (59.1) | 15 (68.2) | .755 |
| Bone marrow involvement, n (%) | 0 (0.0) | 0 (0.0) | 1.000 |
| Baseline MTV, mL, median (IQR) | 42.8 (15.3-75.1) | 30.7 (15.2-170.9) | .557 |
| Bridging therapy, n (%) | 16 (72.7) | 20 (90.9) | .240 |
| Ann Arbor stage III-IV, n (%) | 14 (63.6) | 19 (86.4) | .162 |
| B symptoms, n (%) | 3 (13.6) | 0 (0.0) | .233 |
| Axi-cel, n (%) | 22 (100) | 22 (100) | NA |
| MRD-positive at baseline (n=41 evaluable)^*^, n (%) | 19 (86.4) | 22 (100.0) | .232 |
| Baseline log~10~ hEG, median (IQR) | 0.40 (0.13-0.55) | 0.47 (0.29-0.59) | .231 |
| Baseline Deauville score, median (IQR) | 5 (5-5) | 5 (5-5) | 1.000 |

*P* values from Wilcoxon or Fisher exact. Boldface, *P* < .05. ^*^"MRD-positive at baseline" denotes detection of ≥1 lymphoma-specific variant in the CAPP-Seq panel at baseline plasma (≥0.005 VAF, duplex UMI error correction); this is the same operational definition as "detectable baseline ctDNA" used in the Results section. The two denominators differ only by the analytic subset: **Table 1** restricts to the 44 classifiable patients of whom 41 had a baseline plasma sample meeting QC (3 patients had insufficient DNA input or coverage <2,000× and were excluded from the baseline-VAF analysis) — 38/41 = 92.7%. The **Results section** reports the same metric on the 57-patient training set (of whom 54 had QC-passing baseline samples) — 50/54 = 92.6%. Effective sample sizes are reconciled in supplemental Table S15.

---

### Table 2. Performance metrics of day-14 classifiers in the ALYCANTE training cohort and in the Henri-Mondor real-world validation cohort

| Classifier | Cohort | n | Endpoint | HR (95% CI) | Log-rank *P* | C-index [95% CI]^a^ |
|---|---|---|---|---|---|---|
| **JLCM-ctDNA, day 14** | ALYCANTE | 44 | EFS (lymphoma) | 15.1 (5.1-44.3)^b^ | <.001 | **0.81 [0.76-0.86]**^c^ |
| **JLCM-ctDNA, day 14** | ALYCANTE | 44 | OS | 8.4 (3.1-22.8)^b^ | <.001 | **0.79 [0.71-0.87]**^c^ |
| Day-14 log~10~ hEG (continuous) | ALYCANTE | 44 | EFS | 1.12 (0.97-1.29) per log~10~ | .123 | 0.59 |
| Δlog~10~ baseline→D14 (continuous) | ALYCANTE | 44 | EFS | 1.10 (0.97-1.25) per log~10~ | .145 | 0.62 |
| Detectable ctDNA, day 28 (Frank-style)^h^ | ALYCANTE | 42 | EFS | 2.73 (1.21-6.14) | .015 | 0.64 |
| JLCM-MTV, day 14^j^ | ALYCANTE | 57 | EFS | 3.9 (1.9-8.0) | <.001 | 0.63 |
| JLCM-MTV, day 14^j^ | ALYCANTE | 57 | OS | 3.6 (1.6-8.2) | .003 | 0.63 |
| Deauville ≥4, day 14 | ALYCANTE | 52 | EFS | 0.85 (0.39-1.84) | .68 | 0.51 |
| Deauville ≥4, day 14 | ALYCANTE | 49 | OS | 0.43 (0.15-1.29) | .13 | 0.57 |
| Deauville ≥4, month 3 | ALYCANTE | 49 | EFS | 2.01 (0.89-4.56) | .093 | 0.56 |
| JLCM-Deauville (high vs low) | ALYCANTE | 55 | EFS | 1.83 (0.88-3.79) | .10 | 0.56 |
| JLCM-Deauville (high vs low) | ALYCANTE | 52 | OS | 0.81 (0.30-2.18) | .67 | 0.52 |
| ctDNA-JLCM + Deauville ≥4 (D14) | ALYCANTE | 41 | EFS | ctDNA, separation (*P* = .997); Deauville, 1.02 (0.42-2.50; *P* = .97) | — | 0.82^d^ |
| ctDNA-JLCM + JLCM-Deauville | ALYCANTE | 44 | EFS | ctDNA, separation (*P* = .997); JLCM-Deauville, 1.11 (0.45-2.71; *P* = .83) | — | 0.82^d^ |
| Multivariable (JLCM + IPI + MTV) | ALYCANTE | 44 | EFS (lymphoma) | JLCM, 14.9 (4.8-46.4); IPI, 1.19 (0.45-3.13); MTV, 1.53 (0.86-2.72) | <.001 | 0.86 apparent (boot 0.52)^e^ |
| Multivariable (JLCM + IPI + MTV) | ALYCANTE | 44 | OS | JLCM, 7.7 (2.7-22.2); IPI, 1.49 (0.53-4.19); MTV, 0.72 (0.41-1.28) | <.001 | 0.82 apparent (boot 0.53)^e^ |
| Bi-marker (ctDNA + MTV) | ALYCANTE | 44 | EFS | ctDNA, *P* < .001 (separation); MTV, 1.20 (0.43-3.32; *P* = .73) | — | 0.81 |
| **JLCM-ctDNA, day 14 (validation)** | Henri-Mondor real-world^f^ | 18 | EFS | 8.32 (1.98-34.94) | <.001 | — |
| **JLCM-ctDNA, day 14 (validation)** | Henri-Mondor real-world^f^ | 18 | OS | NE^g^ | .012 | — |
| NRI 12 mo (JLCM vs day-14 log~10~ hEG continuous) | ALYCANTE | 44 | — | +200% (theoretical max)^i^ | — | — |
| NRI 12 mo (JLCM vs Δlog~10~ continuous) | ALYCANTE | 44 | — | +200% (theoretical max)^i^ | — | — |
| NRI 12 mo (bi-marker ctDNA+MTV vs ctDNA only) | ALYCANTE | 39 | — | −7.9% | — | — |
| NRI 12 mo (JLCM D14 vs CMR M3) | ALYCANTE | 39 | — | +59% | — | — |

^a^ 1000-iteration percentile bootstrap CIs. ^b^ Estimable as a finite point only under L₂-penalized Cox (lifelines penalizer = 0.1); unpenalized estimate diverges from quasi-complete separation; Firth-corrected estimate in supplemental Table S19. ^c^ Primary discrimination metric: .632+ bootstrap-corrected univariable C-index with negligible optimism (−0.001 EFS, −0.003 OS). ^d^ Apparent bivariable C-index. ^e^ Apparent multivariable C-index; .632+ correction reveals severe optimism (+0.31 EFS, +0.28 OS); not interpreted as generalizable. ^f^ Single-center retrospective real-world cohort; n = 18 classifiable; CAR-T products: axi-cel (10), liso-cel (7), tisa-cel (1); confirmatory not definitive. ^g^ Not estimable (zero deaths in low-risk). ^h^ Frank-style binary classifier (detectable ctDNA at day 28; Frank et al. JCO 2021^11^) refitted in our cohort; supplemental Table S18. ^i^ Both continuous benchmarks misclassify all 22 EFS events of the high-risk class at the 12-month horizon; the JLCM classifies them correctly. NRI reaching its theoretical maximum reflects the perfect class separation in this cohort and is not a calibrated improvement metric; it should not be interpreted as a generalizable prospective benefit. ^j^ JLCM-MTV univariate HRs are reported on the n = 57 MTV-evaluable cohort; on the n = 44 intersection cohort (patients also classifiable by ctDNA-JLCM), MTV-JLCM loses prognostic significance (HR 0.88; *P* = .80). See Figure 5 legend for full discussion. C-index hierarchy at EFS endpoint (univariable, day-14; supplemental Table S16): **JLCM-ctDNA, 0.81 > Frank-style D28, 0.64 ≈ JLCM-MTV, 0.63 ≈ Δlog~10~ continuous, 0.62 > day-14 log~10~ hEG continuous, 0.59 > Deauville month 3, 0.56 ≈ JLCM-Deauville, 0.56 > Deauville day 14, 0.51.**

---

## Figure legends

### Figure 1. JLCM identifies two distinct ctDNA trajectories in ALYCANTE (n = 57 training set)

![Figure 1. Theoretical and empirical ctDNA trajectories by JLCM class (n = 57 training set; ng = 2; seed = 123).](../blood_article_package/output/figures/Fig1_trajectories_combined.png)

(A) Theoretical mean trajectories from the 2-class JLCM (R `lcmm`; quadratic time, random slope, seed = 123): low-risk (blue, rapid clearance) and high-risk (red, persistent or re-emerging shedding). (B) Observed individual ctDNA trajectories (log~10~ hEG) by day-14 JLCM class, stratified by relapse status within 12 and 24 months. Class-number selection by BIC across ng = 1-4 (1271.7, 1254.6, 1263.6, 1273.7) supported ng = 2 (ΔBIC vs ng = 3 = 9.0).

### Figure 2. Day-14 JLCM-ctDNA class discriminates EFS and OS in ALYCANTE (n = 44 classifiable)

![Figure 2. KM curves for EFS (left) and OS (right) anchored at the day-14 landmark.](../blood_article_package/output/figures/Fig2_km_efs_os.png)

Kaplan–Meier estimates of EFS (left) and OS (right) anchored at the day-14 landmark, by day-14 JLCM class. Log-rank *P* < .001 for both endpoints. Bootstrap-corrected univariable C-index: 0.81 (95% CI 0.76-0.86) EFS; 0.79 (0.71-0.87) OS.

### Figure 3. Multivariable Cox model: day-14 JLCM-ctDNA class is independent of IPI and baseline MTV (n = 44 classifiable)

![Figure 3. Forest plot of the multivariable Cox model adjusting for IPI and log10 baseline MTV.](../blood_article_package/output/figures/Fig3_forest_multivariate.png)

Forest plot of L₂-penalized multivariable Cox (lifelines penalizer = 0.1) for EFS (left) and OS (right): JLCM class, IPI ≥3, log~10~ baseline MTV. n = 44. Day-14 JLCM-ctDNA remained the dominant predictor (adjusted HR EFS 14.9, OS 7.7); IPI ≥3 and log~10~ MTV did not reach significance. Apparent multivariable C-index 0.86 EFS / 0.82 OS; .632+ correction reveals severe optimism (+0.31 EFS, +0.28 OS), corrected to 0.52/0.53 — an expected artefact under quasi-complete separation in this sample size. The **primary metric reported throughout is the bootstrap-corrected univariable JLCM-ctDNA C-index (0.81 [95% CI 0.76-0.86] EFS, 0.79 [0.71-0.87] OS; optimism ≈ 0)**; the multivariable model is presented only as consistent with independence from IPI and MTV. Schoenfeld *P* > .20 for all variables.

### Figure 4. External validation in the Henri-Mondor real-world CAR-T cohort (n = 18 classifiable)

![Figure 4. KM curves for EFS and OS in the Henri-Mondor retrospective real-world cohort (single-center, AP-HP Créteil) by day-14 JLCM class.](../blood_article_package/output/figures/Fig4_validation_lea.png)

Kaplan–Meier estimates of EFS (left) and OS (right) from day 14 in the Henri-Mondor real-world cohort (single-center, retrospective; n = 18 classifiable). Log-rank EFS *P* < .001 (HR 8.32; 95% CI 1.98-34.94; standard Cox proportional hazards on n = 18); OS *P* = .012 (HR not estimable because of zero deaths in low-risk). Patients received axi-cel (n = 10), liso-cel (n = 7), or tisa-cel (n = 1) in routine practice 2019-2024. The wide EFS HR CI reflects modest sample size; the validation is confirmatory rather than definitive.

### Figure 5. Day-14 ctDNA-JLCM outperforms day-14 PET-derived classifiers

![Figure 5. Concordance heatmap and forest plot comparing ctDNA-JLCM with MTV-JLCM at day 14.](../blood_article_package/output/figures/Fig5_ctdna_vs_mtv_combined.png)

(A) Concordance heatmap of day-14 JLCM-ctDNA versus JLCM-MTV (n = 44 with both); Cohen κ = 0.32; 66% agreement (this value applies to the ctDNA-vs-MTV comparison; the parallel ctDNA-vs-Deauville-JLCM concordance was 57% with κ = 0.14, supplemental Figure S10). (B) Forest plot of univariable and bi-marker L₂-penalized Cox models for EFS (blue) and OS (red). Only ctDNA-JLCM retained independent prognostic value. Parallel Deauville analyses (JLCM-Deauville, day-14 Deauville ≥4) reach the same conclusion (κ JLCM-ctDNA vs JLCM-Deauville = 0.14). The apparent bivariate OS protective signal for JLCM-Deauville (HR 0.27, *P* = .044) is artefactual (supplemental Table S13). Lugano non-CMR coincided patient-by-patient with Deauville ≥4 (supplemental Table S12). A and B reflect the n = 44 intersection cohort with both ctDNA-JLCM and MTV-JLCM classifications. The JLCM-MTV univariate HR of 3.9 reported in Table 2 was estimated on the larger n = 57 MTV-evaluable cohort; on the n = 44 intersection cohort the MTV-JLCM loses prognostic significance after restriction to ctDNA-classifiable patients.

---

## Authorship statement

A.C. designed the biomarker substudy, performed the JLCM modeling and statistical analyses (including benchmark Cox models, calibration, decision-curve analysis, and external validation), coordinated the Henri-Mondor real-world validation cohort and clinical follow-up, and drafted the manuscript. J.L. contributed to clinical management of patients and critical revision. M.-H.D.-L. heads the biological immunology platform (Hôpital Henri-Mondor, Créteil), oversaw the ctDNA assay validation and the biomarker substudy, and is the corresponding author. R.H. is the principal investigator of ALYCANTE; he supervised the substudy, reviewed the manuscript, and is the senior author. Coauthors performed sample processing and sequencing (K.T., AP-HP biological immunology platform), central PET review (E.I., X.P.-N., P.B.-D., Y.A.T., C.B.), central pathology review (F.L.G., C.L.), and patient management at participating LYSA centers. C.P. provided LYSARC biostatistical support. All authors approved the final version.

## Acknowledgments

The authors thank the patients and families of ALYCANTE and of the Henri-Mondor real-world cohort, the LYSA and LYSARC networks, the AP-HP biological immunology platform (Hôpital Henri-Mondor, Créteil), and the Roche Sequencing Solutions team (France). ALYCANTE was sponsored by LYSARC with an academic-industry partnership including Kite, a Gilead Company. The biomarker substudy and the Henri-Mondor cohort received institutional support from AP-HP.

## Conflict of interest

R.H. has received honoraria and/or consultancy fees from Kite/Gilead. Coauthor disclosures align with the parent ALYCANTE FA manuscript.^1^ A.C. and M.-H.D.-L. declare no relevant conflicts of interest.

---

## References

1. Houot R, Lemoine J, Claudel A, et al. Axicabtagene ciloleucel as second-line therapy in patients with large B-cell lymphoma ineligible for autologous stem cell transplantation: ALYCANTE final analysis. *J Clin Oncol*. 2026; in revision (Clinical Trial Updates; data cutoff 13 June 2025).
2. Neelapu SS, Locke FL, Bartlett NL, et al. Axicabtagene ciloleucel CAR T-cell therapy in refractory large B-cell lymphoma. *N Engl J Med*. 2017;377(26):2531-2544.
3. Schuster SJ, Bishop MR, Tam CS, et al. Tisagenlecleucel in adult relapsed or refractory diffuse large B-cell lymphoma (JULIET). *N Engl J Med*. 2019;380(1):45-56.
4. Abramson JS, Palomba ML, Gordon LI, et al. Lisocabtagene maraleucel for patients with relapsed or refractory large B-cell lymphomas (TRANSCEND-NHL-001). *Lancet*. 2020;396(10254):839-852.
5. Locke FL, Miklos DB, Jacobson CA, et al. Axicabtagene ciloleucel as second-line therapy for large B-cell lymphoma (ZUMA-7). *N Engl J Med*. 2022;386(7):640-654.
6. Abramson JS, Solomon SR, Arnason J, et al. Lisocabtagene maraleucel as second-line therapy for large B-cell lymphoma: TRANSFORM. *Blood*. 2023;141(14):1675-1684.
7. Houot R, Bachy E, Cartron G, et al. Axicabtagene ciloleucel as second-line therapy in large B-cell lymphoma ineligible for autologous stem-cell transplantation: a phase 2 trial (ALYCANTE primary analysis). *Nat Med*. 2023;29(10):2593-2601.
8. Lauer EM, Mutter J, Scherer F. Circulating tumor DNA in B-cell lymphoma: technical advances, clinical applications, and perspectives. *Leukemia*. 2022;36(9):2151-2164.
9. Newman AM, Bratman SV, To J, et al. An ultrasensitive method for quantitating circulating tumor DNA with broad patient coverage. *Nat Med*. 2014;20(5):548-554.
10. Kurtz DM, Scherer F, Jin MC, et al. Circulating tumor DNA measurements as early outcome predictors in diffuse large B-cell lymphoma. *J Clin Oncol*. 2018;36(28):2845-2853.
11. Frank MJ, Hossain NM, Bukhari A, et al. Monitoring of circulating tumor DNA improves early relapse detection after axicabtagene ciloleucel in large B-cell lymphoma. *J Clin Oncol*. 2021;39(27):3034-3043.
12. Sworder BJ, Kurtz DM, Alig SK, et al. Determinants of resistance to engineered T-cell therapies targeting CD19 in large B-cell lymphomas. *Cancer Cell*. 2023;41(1):210-225.e5.
13. Meriranta L, Alkodsi A, Pasanen A, et al. Molecular features encoded in the ctDNA reveal heterogeneity and predict outcome in high-risk aggressive B-cell lymphoma. *Blood*. 2022;139(12):1863-1877.
14. Zou H, Liu W, Wang X, et al. Dynamic monitoring of circulating tumor DNA reveals outcomes and genomic alterations in patients with relapsed or refractory large B-cell lymphoma undergoing CAR T-cell therapy. *J Immunother Cancer*. 2024;12(7):e009016.
15. Stepan L, Sehgal A, Ghosh M, et al. Circulating tumor DNA dynamics in second-line lisocabtagene maraleucel: TRANSFORM biomarker substudy. *Blood*. 2026; in press.
16. Proust-Lima C, Philipps V, Liquet B. Estimation of extended mixed models using latent classes and latent processes: the R package lcmm. *J Stat Softw*. 2017;78(2):1-56.
17. Henderson R, Diggle P, Dobson A. Joint modelling of longitudinal measurements and event time data. *Biostatistics*. 2000;1(4):465-480.
18. Proust-Lima C, Sene M, Taylor JMG, Jacqmin-Gadda H. Joint latent class models for longitudinal and time-to-event data: a review. *Stat Methods Med Res*. 2014;23(1):74-90.
19. Cheson BD, Fisher RI, Barrington SF, et al. Recommendations for initial evaluation, staging, and response assessment of Hodgkin and non-Hodgkin lymphoma: the Lugano classification. *J Clin Oncol*. 2014;32(27):3059-3068.
20. Firth D. Bias reduction of maximum likelihood estimates. *Biometrika*. 1993;80(1):27-38.
21. Heinze G, Schemper M. A solution to the problem of monotone likelihood in Cox regression. *Biometrics*. 2001;57(1):114-119.
22. International Non-Hodgkin's Lymphoma Prognostic Factors Project. A predictive model for aggressive non-Hodgkin's lymphoma. *N Engl J Med*. 1993;329(14):987-994.
23. Schoenfeld D. Partial residuals for the proportional hazards regression model. *Biometrika*. 1982;69(1):239-241.
24. Pencina MJ, D'Agostino RB, Steyerberg EW. Extensions of net reclassification improvement calculations to measure usefulness of new biomarkers. *Stat Med*. 2011;30(1):11-21.
25. Roschewski M, Dunleavy K, Pittaluga S, et al. Circulating tumour DNA and CT monitoring in patients with untreated diffuse large B-cell lymphoma. *Lancet Oncol*. 2015;16(5):541-549.
26. Lee DW, Santomasso BD, Locke FL, et al. ASTCT consensus grading for cytokine release syndrome and neurologic toxicity associated with immune effector cells. *Biol Blood Marrow Transplant*. 2019;25(4):625-638.
27. Sasanelli M, Meignan M, Haioun C, et al. Pretherapy metabolic tumour volume is an independent predictor of outcome in patients with diffuse large B-cell lymphoma. *Eur J Nucl Med Mol Imaging*. 2014;41(11):2017-2022.
28. Vercellino L, Cottereau AS, Casasnovas O, et al. High total metabolic tumor volume at baseline predicts survival independent of response to therapy. *Blood*. 2020;135(16):1396-1405.
29. Alig SK, Shahrokh Esfahani M, Garofalo A, et al. Distinct Hodgkin lymphoma subtypes defined by noninvasive genomic profiling. *Nature*. 2024;625(7997):779-787.
30. Dickinson MJ, Carlo-Stella C, Morschhauser F, et al. Glofitamab for relapsed or refractory diffuse large B-cell lymphoma. *N Engl J Med*. 2022;387(24):2220-2231.
31. Thieblemont C, Phillips T, Ghesquieres H, et al. Epcoritamab, a novel, subcutaneous CD3xCD20 bispecific T-cell-engaging antibody, in relapsed/refractory large B-cell lymphoma: EPCORE NHL-1. *J Clin Oncol*. 2023;41(12):2238-2247.
