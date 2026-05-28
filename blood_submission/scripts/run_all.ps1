# run_all.ps1 - Pipeline ALYCANTE Blood (package autonome) sous Windows / PowerShell
# Equivalent de run_all.sh. Necessite R 4.3+ et Python 3.11+.
#
# Le package est entierement autonome : aucun chemin NAS ni Temp n'est requis.
# Tous les inputs sont dans ../input/, tous les outputs vont dans ../output/.
#
# Pour relancer dans un autre dossier, definir avant l'execution :
#     $env:BLOOD_PKG_ROOT = "C:\chemin\local\blood_article_package"

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "=== ALYCANTE Blood - pipeline complet (package autonome) ==="

$PY = if ($env:PY_BIN) { $env:PY_BIN } else { "python" }
$R  = if ($env:R_BIN) { $env:R_BIN } else { "Rscript" }

function Run-R($name) {
    Write-Host "--- $name (R) ---"
    & $R (Join-Path $here $name)
    if ($LASTEXITCODE -ne 0) { throw "FAILED: $name" }
}
function Run-Py($name) {
    Write-Host "--- $name (Python) ---"
    & $PY (Join-Path $here $name)
    if ($LASTEXITCODE -ne 0) { throw "FAILED: $name" }
}

# ============================================================================
# Phase 0 - Data preparation (optionnel : a relancer SEULEMENT si on veut
# regenerer master_dataset.csv / data_lcmm_long.csv / le modele JLCM depuis
# les xlsx source). Les outputs sont deja embarques dans input/.
# Dependances : 00a -> 00c -> 00e (cree jlcm_heg_random_time_model.rds)
#   -> 00b (seed sweep) -> 00d (LOO-CV) -> 00f/00g (figures dev)
# ============================================================================
# Decommenter pour regenerer les inputs intermediaires :
# Run-R  "data_prep/00a_prepare_data_lcmm.R"           # CRF -> data_lcmm_long.csv
# Run-Py "data_prep/00c_build_master.py"               # CRF -> master_dataset.csv
# Run-R  "data_prep/00e_fig_jlcm_all.R"                # Initial Jointlcmm fit + saveRDS
# Run-R  "data_prep/00b_reseed_jlcm_rt.R"              # 20-seed sweep (selection seed=123)
# Run-R  "data_prep/00d_gen_loo_data_57.R"             # LOO-CV data prep
# Run-R  "data_prep/00f_fig_jlcm_courbes_theoriques_r1.R"
# Run-R  "data_prep/00g_fig_jlcm_loo_predict.R"

# ============================================================================
# Phase 1 - Modelisation et stats (01-11)
# ============================================================================
Run-R  "01_train_jlcm_ctdna.R"
Run-R  "02_predict_j14.R"
Run-R  "03_train_jlcm_mtv.R"
Run-Py "04_cox_univariate.py"
Run-Py "05_cox_multivariate_v2.py"
Run-R  "06_cox_bimarker.R"
Run-Py "07_nri_12m.py"
Run-Py "08_subgroup_analysis.py"
Run-Py "09_toxicity_by_jlcm.py"
Run-Py "10_table1_jlcm.py"
Run-R  "11_validation_lea.R"

# Phase 1bis - Analyses Blood v2 + Deauville
Run-Py "15_blood_v2_analyses.py"
Run-R  "16_deauville_analyses.R"

# Phase 2 - Figures Main
Run-Py "20_fig1_trajectories.py"
Run-R  "21_fig2_km_efs_os.R"
Run-Py "22_fig3_forest_multivariate.py"
Run-R  "23_fig4_validation_lea.R"
Run-Py "24_fig5_ctdna_vs_mtv.py"

# Phase 3 - Figures Supplemental
Run-Py "30_fig_supp_bootstrap_cindex.py"
Run-Py "31_fig_supp_schoenfeld.py"
Run-Py "32_fig_supp_calibration_12m.py"
Run-Py "33_fig_supp_tdroc.py"
Run-Py "34_fig_supp_dca_12m.py"
Run-Py "35_fig_supp_heatmap_dynamics.py"
Run-Py "36_fig_supp_forest_subgroups.py"
Run-Py "37_fig_visual_abstract.py"

# Phase 4 - Reviewer rang A : benchmarks continus + Frank-style + ridge sensit.
Run-R  "46_cox_continuous_benchmark.R"
Run-R  "47_frank_style_j28.R"
Run-R  "48_ridge_lambda_sensitivity.R"

# Phase 5 - Build docx (version finale v8_9 — soumission Blood)
Run-Py "59_build_blood_article_v8_9.py"

Write-Host "`n=== Pipeline termine. ==="
Write-Host "Verifier : ..\output\Blood_article_v8_9.docx et ..\output\Blood_article_v8_9_supplemental.docx"
