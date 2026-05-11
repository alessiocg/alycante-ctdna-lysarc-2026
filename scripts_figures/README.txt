================================================================================
  ALYCANTE — Scripts des figures (ctDNA CAR-T DLBCL)
  Reunion LYSARC 2026
================================================================================

STRUCTURE
---------
scripts_figures/
  data/                     Donnees intermediaires (quasi auto-suffisant)
    Donnees.xlsx            Donnees ctDNA nettoyees (generees par nettoyage_donnees.R)
    ALYCANTE_RNASeq_21OCT2025.xlsx   Donnees cliniques/survie
    data_lcmm_long.csv      Format long pour JLCM (57 patients)
    rr_strict_mapping.csv   Mapping R/R strict par patient
    jlcm_heg_random_time_model.rds   Modele JLCM random=~time (seed=123)
    jlcm_heg_model.rds      Modele JLCM random=~1
    jlcm_*.csv               Resultats LOO, predictions, etc.
    baseline_variants_kept.*  Variants de reference
  load_data.py              Module utilitaire de chargement des donnees
  nettoyage_donnees.R       Nettoyage Donnees_brutes2.xlsx -> Donnees.xlsx
  *.py / *.R                Scripts des figures (1 script = 1 figure)

DONNEES SOURCES (dans input/, hors de ce dossier)
--------------------------------------------------
  ../../input/Donnees_brutes2.xlsx          Donnees ctDNA brutes (source)
  ../../input/ALYCANTE_RNASeq_21OCT2025.xlsx  Donnees cliniques
  ../../input/baseline_variants_kept.xlsx   Variants de reference

CHAINE DE DONNEES
-----------------
  Donnees_brutes2.xlsx --[nettoyage_donnees.R]--> data/Donnees.xlsx
  data/Donnees.xlsx + data/ALYCANTE_RNASeq_21OCT2025.xlsx --> figures

  Si Donnees_brutes2.xlsx est present dans input/, load_data.py
  tente de regenerer Donnees.xlsx automatiquement. Sinon, il utilise la
  version pre-calculee dans data/.

PARAMETRES CLES
---------------
  - JLCM : seed=123, random=~time, 57 patients, BIC=1254.6
  - Seuil delta hEG (Leuca->M1) : -3.0 (mediane = Youden optimal)
  - CMR ponctuelle : M3 (justifie par fig_cmr_timepoint_comparison)
  - Seuils baseline hEG : Leuca=3.5, J-5=3.5, J0=3.0 (medianes)
  - Temps : EFS depuis J0 (corrige du delai leucapherese -> J0)
  - R/R strict = Progression|Relapse uniquement (pas deces non-R/R)
  - Followup : toujours filtrer (efs_time >= seuil) | (efs_event == 1)

ENVIRONNEMENT
-------------
  - Python 3.11 (pandas, numpy, matplotlib, lifelines, scipy, sklearn, plotly)
  - R 4.3.1 (lcmm, survival, ggplot2, patchwork)

USAGE
-----
  Chaque script est autonome. Lancer depuis ce dossier :
    python fig_xxx.py       (Python)
    Rscript fig_xxx.R       (R)

  Les figures sont sauvegardees dans le dossier courant et copiees
  automatiquement sur le reseau si accessible.

LISTE DES FIGURES (ordre logique)
---------------------------------
  Bloc 1 - Population
    consort_v3.py                   CONSORT flowchart
    fig_distribution_ctdna.py       Taux positivite ctDNA par timepoint
    fig_cfdna_boxplot.py            Boxplot cfDNA total par timepoint
    fig_informativity.py            Informativity (regions couvertes, FN/VN)
    fig_km_baseline_heg.py          KM EFS par hEG baseline (Leuca, J-5, J0)
    fig_km_diversite.py             KM diversite clonale
    fig_correlation_ratio_heg.py    Correlation ctDNA ratio vs hEG

  Bloc 2 - Trajectoires
    fig_trajectoires_efs.py         Spaghetti plot trajectoires ctDNA
    fig_boxplot_heg_4grp.py         Boxplot hEG par groupe R/R
    fig_velocity_analysis.py        Velocite par segment (J-5->J0, J0->J14, J14->M1, M1->M3)

  Bloc 3 - CMR ponctuelle
    fig_taux_cmr_3grp.py            Taux CMR par timepoint (J0-M12)
    fig_cmr_cumule_3grp.py          CMR cumulee par timepoint (J0-M12)
    fig_cmr_timing_km.py            KM timing CMR (non landmark)
    fig_cmr_timepoint_comparison.py OR/logrank/cindex par timepoint (justifie M3)
    fig_km_cmr_m3.py                KM EFS CMR M3 (n=45)

  Bloc 4 - Delta hEG
    fig_delta_ctdna_waterfall.py    Waterfall delta (seuil -3.0, mediane)
    fig_heatmaps_unified.py         Heatmaps AUC + C-index
    fig_spline_delta_heg.py         Spline Cox delta (linearite)
    fig_spline_baseline_heg.py      Spline Cox baseline (Leuca, J-5, J0)
    fig_km_delta_v2.py              KM EFS delta Leuca->M1 (seuil -3.0)

  Bloc 5 - Classification V2
    sankey_classification_V2.py     Sankey classification experte
    fig_spaghetti_v2_horizons.py    Trajectoires par horizon (classif V2 tronquee)

  Bloc 6 - JLCM
    fig_jlcm_all.R                  BIC ng=1..4 + modeles
    fig_jlcm_bic_or.py              BIC + OR
    fig_jlcm_courbes_theoriques_r1.R  Courbes theoriques (random=~1 vs ~time)
    fig_jlcm_loo_validation.R       LOO DBIC + concordance + predictClass
    fig_jlcm_loo_predict.R          LOO predictClass (seed=123)
    fig_km_landmark_jlcm.R          KM landmark par horizon (J14-M12)
    jlcm_predict_j14.R              Predictions J14

  Bloc 7 - Comparaison 3 methodes (JLCM J14, CMR M3, delta hEG)
    fig_comparison_metrics.py       Se/Sp/PPV/NPV barplot
    fig_swimmer_leadtime.py         Swimmer plots lead time
    fig_dca_3methods.py             DCA 3 methodes lissees
    fig_nri_comparison.py           NRI (Net Reclassification Improvement)

  Utilitaires
    load_data.py                    Chargement donnees avec fallback brutes->nettoyees
    nettoyage_donnees.R             Brutes -> Donnees.xlsx
    prepare_data_lcmm.R            Preparation data_lcmm_long.csv
    gen_loo_data_57.R               Generation donnees LOO (DBIC + predictions)
    reseed_jlcm_rt.R               Grid search seeds JLCM
