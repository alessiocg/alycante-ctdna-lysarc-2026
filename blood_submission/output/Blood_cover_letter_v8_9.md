**Marie-Hélène Delfau-Larue, MD, PhD**
Head, Department of Biological Immunology
Hôpital Henri-Mondor, AP-HP
Université Paris-Est Créteil (UPEC), INSERM U955
51 avenue du Maréchal de Lattre de Tassigny
94010 Créteil, France
marie-helene.delfau@aphp.fr | +33 1 49 81 28 33

29 May 2026

**The Editor-in-Chief**
*Blood*
American Society of Hematology
2021 L Street NW, Suite 900
Washington, DC 20036, USA

**Re:** Submission of Regular Article *"Day-14 ctDNA joint latent class modeling stratifies risk in transplant-ineligible R/R large B-cell lymphoma after axi-cel"* (Lymphoid Neoplasia)

Dear Editor,

We are pleased to submit for your consideration the enclosed Regular Article reporting the biomarker substudy of ALYCANTE (ClinicalTrials.gov NCT04531046), the LYSARC-sponsored academic phase 2 trial that evaluated axicabtagene ciloleucel (axi-cel) as second-line therapy in transplant-ineligible patients with relapsed/refractory large B-cell lymphoma (R/R LBCL). This manuscript is the **biomarker companion** to the trial's final analysis (Houot et al., *Journal of Clinical Oncology* 2026; currently in revision), itself the update of the primary report (Houot et al., *Nat Med* 2023, doi:10.1038/s41591-023-02572-5).

**The clinical question we address is well-defined**: among the ~40% of CAR T-cell recipients who will eventually relapse, can we identify them within two weeks of infusion — well before the day-90 PET-CT — to enable risk-adapted intervention? We report that a **joint latent class mixed model (JLCM)** trained on serial ctDNA dynamics (CAPP-Seq, seven post-infusion timepoints D0 → M12) and deployed at day 14 via `predictClass` stratifies relapse risk with an EFS hazard ratio of **15.1** (95% CI 5.1–44.3) and a bootstrap-corrected Harrell C-index of **0.81** — outperforming day-14 continuous ctDNA, day-28 Frank-style detection, day-14 PET (Deauville ≥4), and month-3 complete metabolic response. The signal generalized in a single-center real-world cohort (Hôpital Henri-Mondor, n = 18; EFS HR 8.32, 95% CI 1.98–34.94). EFS in this substudy is defined as time to lymphoma-specific events (relapse, progression, lymphoma-related death) — a definition aligned with the biological hypothesis that ctDNA tracks lymphoma rather than non-lymphoma mortality.

**We believe this work fits *Blood* for three reasons.** First, the methodological contribution is distinct: rather than thresholding a single ctDNA timepoint, we explicitly model the longitudinal trajectory jointly with the survival outcome, which makes the resulting class deployable at day 14 from a sparse longitudinal prior — the *train-rich, deploy-early* design. Second, the day-14 readout fills the actionable gap repeatedly identified by the field (Frank et al., *J Clin Oncol* 2021; Sworder et al., *Cancer Cell* 2023; Meriranta et al., *Blood* 2022) between infusion and month-3 imaging, when no other biomarker is yet interpretable. Third, the manuscript is supported by a fully reproducible analytic package hosted at `https://github.com/alessiocg/alycante-ctdna-lysarc-2026` (public, MIT-licensed) containing the 50+ analysis scripts, the trained JLCM model, the aggregate metrics CSVs (Tables 1–2, SuppTables S1–S19), and the 16 figures (Figs 1–5 + SuppFigs S1–S12 + Visual abstract). Patient-level data remain on the AP-HP secure NAS and will be deposited in the LYSARC controlled-access repository upon publication.

**Manuscript metadata**. Abstract: 247 words (limit 250). Body (Introduction → Discussion): 4 378 words (limit 4 500). References: 31 (citation-order, AMA format). Tables: 2 main + 19 supplemental. Figures: 5 main + 12 supplemental + 1 visual abstract. Key Points: 2 (each ≤ 140 characters).

**Declarations**. This manuscript has not been published previously and is not under consideration at any other journal; all coauthors have read and approved the present submission. All patient data were collected under the ALYCANTE trial protocol, approved by Comité de Protection des Personnes Sud-Est II (CPP); the substudy was conducted under the same ethics framework. Coauthor disclosures align with those of the parent ALYCANTE paper; no additional conflicts of interest pertain to the biomarker analysis. The work was supported by LYSARC and the AP-HP Department of Biological Immunology.

We would be honored to have this work considered for *Blood* and stand ready to address any clarification the editorial office or peer reviewers may require.

Sincerely,

**Marie-Hélène Delfau-Larue**, MD, PhD
Corresponding author
Head, Department of Biological Immunology, Hôpital Henri-Mondor, AP-HP

on behalf of all coauthors, including:
**Alexis Claudel** (first author; Henri-Mondor Biological Immunology)
**Julien Lemoine** (clinical hematology, AP-HP, Université Paris Cité)
**Roch Houot** (senior author; ALYCANTE principal investigator; CHU Rennes, INSERM UMR 1236, EFS)
and the ALYCANTE biomarker substudy investigators and the LYSARC.
