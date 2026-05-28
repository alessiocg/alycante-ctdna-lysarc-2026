#!/usr/bin/env bash
# run_all.sh - Pipeline ALYCANTE Blood (package autonome) sous Linux / macOS
#
# Le package est entierement autonome : aucun chemin NAS ni Temp requis.
# Tous les inputs sont dans ../input/, tous les outputs vont dans ../output/.
#
# Pour relancer dans un autre dossier, exporter avant :
#     export BLOOD_PKG_ROOT=/chemin/local/blood_article_package

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PY="${PY_BIN:-python}"
R="${R_BIN:-Rscript}"

echo "=== ALYCANTE Blood - pipeline complet (package autonome) ==="
echo "Scripts : $SCRIPT_DIR"
echo

run_r()  { echo "--- $1 (R) ---";  "$R"  "$SCRIPT_DIR/$1"; }
run_py() { echo "--- $1 (Python) ---"; "$PY" "$SCRIPT_DIR/$1"; }

# =============================================================================
# Phase 0 - data preparation (preparation des inputs depuis CRF brut)
# ATTENTION : decommente seulement si tu regeneres les inputs from scratch.
# Les inputs pre-traites sont deja dans ../input/ - sauter par defaut.
# Sequence de dependances : 00a -> 00c -> 00e (cree jlcm_heg_random_time_model.rds)
#   -> 00b (seed sweep optionnel) -> 00d (LOO-CV) -> 00f/00g (figures dev)
# =============================================================================
# run_r  data_prep/00a_prepare_data_lcmm.R          # CRF -> data_lcmm_long.csv
# run_py data_prep/00c_build_master.py              # CRF -> master_dataset.csv
# run_r  data_prep/00e_fig_jlcm_all.R               # Initial Jointlcmm fit + saveRDS
# run_r  data_prep/00b_reseed_jlcm_rt.R             # 20-seed sweep (selection seed=123)
# run_r  data_prep/00d_gen_loo_data_57.R            # LOO-CV data prep
# run_r  data_prep/00f_fig_jlcm_courbes_theoriques_r1.R
# run_r  data_prep/00g_fig_jlcm_loo_predict.R

# =============================================================================
# Phase 1 - modelisation (assume inputs pre-traites dans ../input/)
# =============================================================================
run_r  01_train_jlcm_ctdna.R
run_r  02_predict_j14.R
run_r  03_train_jlcm_mtv.R
run_py 04_cox_univariate.py
run_py 05_cox_multivariate_v2.py
run_r  06_cox_bimarker.R
run_py 07_nri_12m.py
run_py 08_subgroup_analysis.py
run_py 09_toxicity_by_jlcm.py
run_py 10_table1_jlcm.py
run_r  11_validation_lea.R

# Phase 1bis - Blood v2 + Deauville
run_py 15_blood_v2_analyses.py
run_r  16_deauville_analyses.R

# Phase 2 - figures Main
run_py 20_fig1_trajectories.py
run_r  21_fig2_km_efs_os.R
run_py 22_fig3_forest_multivariate.py
run_r  23_fig4_validation_lea.R
run_py 24_fig5_ctdna_vs_mtv.py

# Phase 3 - figures Supplemental
run_py 30_fig_supp_bootstrap_cindex.py
run_py 31_fig_supp_schoenfeld.py
run_py 32_fig_supp_calibration_12m.py
run_py 33_fig_supp_tdroc.py
run_py 34_fig_supp_dca_12m.py
run_py 35_fig_supp_heatmap_dynamics.py
run_py 36_fig_supp_forest_subgroups.py
run_py 37_fig_visual_abstract.py

# Phase 4 - Reviewer rang A
run_r  46_cox_continuous_benchmark.R
run_r  47_frank_style_j28.R
run_r  48_ridge_lambda_sensitivity.R

# Phase 5 - build docx v8.9 (manuscrit final, version soumission Blood)
run_py 59_build_blood_article_v8_9.py

echo
echo "=== Pipeline termine. ==="
echo "Verifier : ../output/Blood_article_v8_9.docx et ../output/Blood_article_v8_9_supplemental.docx"