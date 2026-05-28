# =====================================================================
# 16_deauville_analyses.R
#
# Phase 2 of Blood v5 - Deauville (PET) covariate analyses.
#   1. JLCM trained on longitudinal Deauville (seed=123, 2 classes)
#   2. Cox univariate: EFS / OS ~ Deauville_D14 >=4, Deauville_M3, Lugano,
#      JLCM-Deauville (low/high-risk)
#   3. Cox bivariate: JLCM-ctDNA + Deauville_D14, JLCM-ctDNA + JLCM-Deauville
#   4. Concordance JLCM-ctDNA x JLCM-Deauville (Cohen's kappa, crosstab)
#   5. C-index: ctDNA, Deauville_D14, Lugano_D14, ctDNA+Deauville, ctDNA+Lugano
#
# Output (output/scripts_figures/data/):
#   data_deauville_long.csv
#   jlcm_deauville_model.rds
#   jlcm_deauville_predict_j14.csv
#   deauville_metrics.csv            (master metrics file)
#   deauville_cox_univariate.csv
#   deauville_cox_bivariate.csv
#   deauville_concordance.csv
#   deauville_concordance_crosstab.csv
#   deauville_cindex.csv
#
# Sources :
#   output/scripts_figures/data/data_pet_full_long.csv
#   output/scripts_figures/data/jlcm_predict_j14.csv      (ctDNA class)
#   output/scripts_figures/data/data_lcmm_long.csv        (survival fields)
#
# Author: A. Claudel, AP-HP - Blood v5 (May 21, 2026)
# =====================================================================

suppressPackageStartupMessages({
  library(lcmm)
  library(survival)
  library(survminer)
  library(dplyr)
  library(tidyr)
})

NAS  <- Sys.getenv("NAS_BASE",
                   OUTPUT_DIR)
DATA <- file.path(NAS, "output", "scripts_figures", "data")

SET_SEED <- 123

# ---------- Load data ------------------------------------------------------
cat("[load] reading PET long format\n")
pet <- read.csv(file.path(DATA, "data_pet_full_long.csv"),
                stringsAsFactors = FALSE)
pred_ct <- read.csv(file.path(DATA, "jlcm_predict_j14.csv"),
                    stringsAsFactors = FALSE)
surv <- read.csv(file.path(DATA, "data_lcmm_long.csv"),
                 stringsAsFactors = FALSE) |>
  select(ID, randomisation, efs_time, efs_event, os_time, os_event) |>
  group_by(ID) |>
  slice(1) |>
  ungroup()
cat(sprintf("[load] surv table: %d patient rows\n", nrow(surv)))

cat(sprintf("[load] %d patients in PET (%d rows)\n",
            length(unique(pet$ID)), nrow(pet)))

# ---------- Prepare Deauville long format ---------------------------------
# Map LYSARC timepoint -> internal label
pet$tp_int <- recode(pet$timepoint,
                     "PET_Baseline"      = "Baseline",
                     "PET_Pre_Treatment" = "Pre_Treatment",
                     "PET_D14"           = "D14",
                     "PET_M1"            = "M1",
                     "PET_M3"            = "M3",
                     "PET_M6"            = "M6",
                     "PET_M9"            = "M9",
                     "PET_M12"           = "M12",
                     "PET_Unscheduled"   = "Unscheduled")

# longitudinal Deauville with `time` in months from CAR-T (already in `time`)
deauville_long <- pet |>
  filter(!is.na(deauville), tp_int != "Unscheduled") |>
  select(ID, randomisation, time, timepoint = tp_int, deauville, lugano)

write.csv(deauville_long,
          file.path(DATA, "data_deauville_long.csv"),
          row.names = FALSE)
cat(sprintf("[save] data_deauville_long.csv (%d rows, %d patients)\n",
            nrow(deauville_long), length(unique(deauville_long$ID))))

# ---------- 1. JLCM trained on longitudinal Deauville ---------------------
cat("\n[JLCM] training on longitudinal Deauville (seed=123, 2 classes)\n")

# join survival for the joint model
df_dv <- deauville_long |>
  inner_join(surv |> select(ID, efs_time, efs_event, os_time, os_event),
             by = "ID")
cat(sprintf("[JLCM] training set: %d rows, %d patients, %d events\n",
            nrow(df_dv), length(unique(df_dv$ID)),
            sum(df_dv |> distinct(ID, efs_event) |> pull(efs_event))))

set.seed(SET_SEED)
m_dv1 <- tryCatch(
  Jointlcmm(fixed = deauville ~ time + I(time^2),
            random = ~ time,
            subject = "ID",
            ng = 1,
            data = df_dv,
            survival = Surv(efs_time, efs_event) ~ 1,
            hazard = "Weibull"),
  error = function(e) { message("ng=1 failed: ", conditionMessage(e)); NULL })

set.seed(SET_SEED)
m_dv2 <- tryCatch(
  Jointlcmm(fixed = deauville ~ time + I(time^2),
            mixture = ~ time + I(time^2),
            random = ~ time,
            subject = "ID",
            ng = 2,
            data = df_dv,
            survival = Surv(efs_time, efs_event) ~ 1,
            hazard = "Weibull",
            B = m_dv1),
  error = function(e) { message("ng=2 failed: ", conditionMessage(e)); NULL })

saveRDS(m_dv2, file.path(DATA, "jlcm_deauville_model.rds"))
cat(sprintf("[JLCM] BIC ng=1=%.1f, ng=2=%.1f\n",
            if (is.null(m_dv1)) NA else m_dv1$BIC,
            if (is.null(m_dv2)) NA else m_dv2$BIC))

# identify which class is the "MAUVAIS" using training pprob + EFS events
identify_bad_class <- function(model, df) {
  pp <- model$pprob
  df_first <- df |> distinct(ID, .keep_all = TRUE)
  merged <- merge(pp, df_first, by = "ID")
  m <- aggregate(efs_event ~ class, data = merged, FUN = mean)
  list(bad = m$class[which.max(m$efs_event)], summary = m)
}

cls_info <- identify_bad_class(m_dv2, df_dv)
cat("[JLCM] EFS event rate by class:\n"); print(cls_info$summary)
mauvais_class_idx <- cls_info$bad
prob_col <- paste0("probYT", mauvais_class_idx)
cat(sprintf("[JLCM] MAUVAIS class index = %d (will use column %s)\n",
            mauvais_class_idx, prob_col))

# predict J14 class for Deauville: use Baseline + D14 only (deploy-early analog
# of ctDNA-JLCM). Must inject Tevent/Event columns required by Jointlcmm.
predict_dv_class <- function(model, dv_long, surv_tbl, mauvais_idx) {
  if (is.null(model)) return(NULL)
  ids <- sort(unique(dv_long$ID))
  out <- list()
  prob_col <- paste0("probYT", mauvais_idx)
  for (pid in ids) {
    sub <- dv_long |>
      filter(ID == pid, timepoint %in% c("Baseline", "Pre_Treatment", "D14"))
    if (nrow(sub) < 1) next
    s <- surv_tbl[surv_tbl$ID == pid, ]
    if (nrow(s) == 0) next
    sub$Tevent <- s$efs_time[1]
    sub$Event  <- s$efs_event[1]
    sub$efs_time <- s$efs_time[1]
    sub$efs_event <- s$efs_event[1]
    pp <- tryCatch(predictClass(model, newdata = sub),
                   error = function(e) NULL)
    if (is.null(pp)) next
    p_m <- pp[1, prob_col]
    out[[as.character(pid)]] <- data.frame(
      ID = pid,
      p_mauvais_dv = round(p_m, 4),
      group_dv = ifelse(is.na(p_m), NA,
                        ifelse(p_m > 0.5, "MAUVAIS_dv", "BON_dv")),
      n_meas = nrow(sub))
  }
  do.call(rbind, out)
}

if (!is.null(m_dv2)) {
  pred_dv <- predict_dv_class(m_dv2, deauville_long, surv, mauvais_class_idx)
  write.csv(pred_dv, file.path(DATA, "jlcm_deauville_predict_j14.csv"),
            row.names = FALSE)
  cat(sprintf("[save] jlcm_deauville_predict_j14.csv (%d patients)\n",
              nrow(pred_dv)))
  cat("[JLCM-Dv] class distribution:\n"); print(table(pred_dv$group_dv))
} else {
  pred_dv <- NULL
}

# ---------- 2. Build per-patient covariates table -------------------------
# Need Deauville_D14, Deauville_M3, Lugano_D14, Lugano_M3 per patient
make_covs <- function(pet) {
  pet |>
    filter(tp_int %in% c("D14", "M3")) |>
    select(ID, randomisation, tp_int, deauville, lugano) |>
    pivot_wider(id_cols = c(ID, randomisation),
                names_from = tp_int,
                values_from = c(deauville, lugano)) |>
    mutate(deauville_D14_ge4 = ifelse(is.na(deauville_D14), NA,
                                       as.integer(deauville_D14 >= 4)),
           deauville_M3_ge4  = ifelse(is.na(deauville_M3), NA,
                                       as.integer(deauville_M3 >= 4)),
           lugano_D14_nonCMR = ifelse(is.na(lugano_D14), NA,
                                       as.integer(!grepl("Complete", lugano_D14))),
           lugano_M3_nonCMR  = ifelse(is.na(lugano_M3), NA,
                                       as.integer(!grepl("Complete", lugano_M3))))
}

covs <- make_covs(pet)

# merge with ctDNA-JLCM and Deauville-JLCM classes and survival
master <- surv |>
  left_join(covs |> select(-randomisation), by = "ID") |>
  left_join(pred_ct |> mutate(ctdna_jlcm = group) |>
              select(ID, ctdna_jlcm), by = "ID")
cat(sprintf("[master] efs events = %d / %d\n", sum(master$efs_event), nrow(master)))
if (!is.null(pred_dv)) {
  master <- master |>
    left_join(pred_dv |> mutate(deauville_jlcm = group_dv) |>
                select(ID, deauville_jlcm, p_mauvais_dv),
              by = "ID")
}

cat(sprintf("\n[master] n=%d patients with covariates\n", nrow(master)))

# ---------- 3. Cox univariate ---------------------------------------------
fit_cox <- function(formula_str, df, label) {
  f <- as.formula(formula_str)
  fit <- tryCatch(coxph(f, data = df), error = function(e) NULL)
  if (is.null(fit)) {
    return(data.frame(label = label, n = NA, n_events = NA,
                      HR = NA, lower = NA, upper = NA, p = NA,
                      c_index = NA))
  }
  s <- summary(fit)
  ci <- s$conf.int[1, ]
  data.frame(
    label = label,
    n = fit$n,
    n_events = fit$nevent,
    HR = round(ci[1], 2),
    lower = round(ci[3], 2),
    upper = round(ci[4], 2),
    p = signif(s$coefficients[1, 5], 3),
    c_index = round(s$concordance[1], 3)
  )
}

cox_uni <- list(
  fit_cox("Surv(efs_time, efs_event) ~ deauville_D14_ge4", master, "Deauville_D14_>=4 EFS"),
  fit_cox("Surv(os_time,  os_event)  ~ deauville_D14_ge4", master, "Deauville_D14_>=4 OS"),
  fit_cox("Surv(efs_time, efs_event) ~ deauville_M3_ge4",  master, "Deauville_M3_>=4 EFS"),
  fit_cox("Surv(os_time,  os_event)  ~ deauville_M3_ge4",  master, "Deauville_M3_>=4 OS"),
  fit_cox("Surv(efs_time, efs_event) ~ lugano_D14_nonCMR",  master, "Lugano_D14_non-CMR EFS"),
  fit_cox("Surv(os_time,  os_event)  ~ lugano_D14_nonCMR",  master, "Lugano_D14_non-CMR OS"),
  fit_cox("Surv(efs_time, efs_event) ~ lugano_M3_nonCMR",   master, "Lugano_M3_non-CMR EFS"),
  fit_cox("Surv(os_time,  os_event)  ~ lugano_M3_nonCMR",   master, "Lugano_M3_non-CMR OS")
)
if (!is.null(pred_dv)) {
  cox_uni <- c(cox_uni, list(
    fit_cox("Surv(efs_time, efs_event) ~ I(deauville_jlcm=='MAUVAIS_dv')",
            master, "JLCM-Deauville (high vs low) EFS"),
    fit_cox("Surv(os_time,  os_event)  ~ I(deauville_jlcm=='MAUVAIS_dv')",
            master, "JLCM-Deauville (high vs low) OS")
  ))
}
# reference ctDNA-JLCM
cox_uni <- c(cox_uni, list(
  fit_cox("Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS')",
          master, "JLCM-ctDNA (high vs low) EFS [reference]"),
  fit_cox("Surv(os_time,  os_event)  ~ I(ctdna_jlcm=='MAUVAIS')",
          master, "JLCM-ctDNA (high vs low) OS [reference]")
))

cox_uni_df <- do.call(rbind, cox_uni)
write.csv(cox_uni_df,
          file.path(DATA, "deauville_cox_univariate.csv"),
          row.names = FALSE)
cat("\n[univariate Cox]\n"); print(cox_uni_df)

# ---------- 4. Cox bivariate ----------------------------------------------
fit_cox_multi <- function(formula_str, df, label) {
  f <- as.formula(formula_str)
  fit <- tryCatch(coxph(f, data = df), error = function(e) NULL)
  if (is.null(fit)) return(NULL)
  s <- summary(fit)
  ci <- s$conf.int
  rows <- vector("list", nrow(ci))
  for (i in seq_len(nrow(ci))) {
    rows[[i]] <- data.frame(
      model = label,
      covariate = rownames(ci)[i],
      n = fit$n,
      n_events = fit$nevent,
      HR = round(ci[i, 1], 2),
      lower = round(ci[i, 3], 2),
      upper = round(ci[i, 4], 2),
      p = signif(s$coefficients[i, 5], 3),
      c_index = round(s$concordance[1], 3)
    )
  }
  do.call(rbind, rows)
}

bivariate_list <- list(
  fit_cox_multi(
    "Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS') + deauville_D14_ge4",
    master, "ctDNA-JLCM + Deauville_D14 (EFS)"),
  fit_cox_multi(
    "Surv(os_time,  os_event)  ~ I(ctdna_jlcm=='MAUVAIS') + deauville_D14_ge4",
    master, "ctDNA-JLCM + Deauville_D14 (OS)"),
  fit_cox_multi(
    "Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS') + lugano_D14_nonCMR",
    master, "ctDNA-JLCM + Lugano_D14 (EFS)"),
  fit_cox_multi(
    "Surv(os_time,  os_event)  ~ I(ctdna_jlcm=='MAUVAIS') + lugano_D14_nonCMR",
    master, "ctDNA-JLCM + Lugano_D14 (OS)")
)
if (!is.null(pred_dv)) {
  bivariate_list <- c(bivariate_list, list(
    fit_cox_multi(
      "Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS') + I(deauville_jlcm=='MAUVAIS_dv')",
      master, "ctDNA-JLCM + Deauville-JLCM (EFS)"),
    fit_cox_multi(
      "Surv(os_time,  os_event)  ~ I(ctdna_jlcm=='MAUVAIS') + I(deauville_jlcm=='MAUVAIS_dv')",
      master, "ctDNA-JLCM + Deauville-JLCM (OS)")
  ))
}

biv_df <- do.call(rbind, bivariate_list)
write.csv(biv_df, file.path(DATA, "deauville_cox_bivariate.csv"),
          row.names = FALSE)
cat("\n[bivariate Cox]\n"); print(biv_df)

# ---------- 5. Concordance: JLCM-ctDNA x JLCM-Deauville -------------------
if (!is.null(pred_dv)) {
  cc <- master |>
    filter(!is.na(ctdna_jlcm), !is.na(deauville_jlcm))
  tbl <- table(ctdna = cc$ctdna_jlcm, deauville = cc$deauville_jlcm)
  agreement <- sum(diag(tbl)) / sum(tbl)
  # Cohen's kappa
  po <- agreement
  rowsum <- rowSums(tbl) / sum(tbl)
  colsum <- colSums(tbl) / sum(tbl)
  pe <- sum(rowsum * colsum)
  kappa <- (po - pe) / (1 - pe)

  conc_df <- data.frame(
    metric = c("n", "agreement_pct", "cohen_kappa"),
    value = c(sum(tbl), round(100 * agreement, 1), round(kappa, 3))
  )
  write.csv(conc_df, file.path(DATA, "deauville_concordance.csv"),
            row.names = FALSE)
  write.csv(as.data.frame.matrix(tbl),
            file.path(DATA, "deauville_concordance_crosstab.csv"),
            row.names = TRUE)
  cat(sprintf("\n[concordance] n=%d, agreement=%.1f%%, kappa=%.3f\n",
              sum(tbl), 100 * agreement, kappa))
  print(tbl)
}

# ---------- 6. C-index comparisons ----------------------------------------
get_cindex <- function(formula_str, df, label) {
  f <- as.formula(formula_str)
  fit <- tryCatch(coxph(f, data = df), error = function(e) NULL)
  if (is.null(fit)) {
    return(data.frame(model = label, n = NA_integer_,
                      c_index = NA_real_, c_index_se = NA_real_))
  }
  s <- summary(fit)
  data.frame(model = label,
             n = fit$n,
             c_index = round(s$concordance[1], 3),
             c_index_se = round(s$concordance[2], 3))
}

cindex_efs <- list(
  get_cindex("Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS')",
             master, "ctDNA-JLCM only (EFS)"),
  get_cindex("Surv(efs_time, efs_event) ~ deauville_D14_ge4",
             master, "Deauville_D14 only (EFS)"),
  get_cindex("Surv(efs_time, efs_event) ~ lugano_D14_nonCMR",
             master, "Lugano_D14 only (EFS)"),
  get_cindex("Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS') + deauville_D14_ge4",
             master, "ctDNA-JLCM + Deauville_D14 (EFS)"),
  get_cindex("Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS') + lugano_D14_nonCMR",
             master, "ctDNA-JLCM + Lugano_D14 (EFS)")
)
if (!is.null(pred_dv)) {
  cindex_efs <- c(cindex_efs, list(
    get_cindex("Surv(efs_time, efs_event) ~ I(deauville_jlcm=='MAUVAIS_dv')",
               master, "Deauville-JLCM only (EFS)"),
    get_cindex("Surv(efs_time, efs_event) ~ I(ctdna_jlcm=='MAUVAIS') + I(deauville_jlcm=='MAUVAIS_dv')",
               master, "ctDNA-JLCM + Deauville-JLCM (EFS)")
  ))
}
cindex_efs_df <- do.call(rbind, cindex_efs)

cindex_os <- list(
  get_cindex("Surv(os_time, os_event) ~ I(ctdna_jlcm=='MAUVAIS')",
             master, "ctDNA-JLCM only (OS)"),
  get_cindex("Surv(os_time, os_event) ~ deauville_D14_ge4",
             master, "Deauville_D14 only (OS)"),
  get_cindex("Surv(os_time, os_event) ~ lugano_D14_nonCMR",
             master, "Lugano_D14 only (OS)"),
  get_cindex("Surv(os_time, os_event) ~ I(ctdna_jlcm=='MAUVAIS') + deauville_D14_ge4",
             master, "ctDNA-JLCM + Deauville_D14 (OS)"),
  get_cindex("Surv(os_time, os_event) ~ I(ctdna_jlcm=='MAUVAIS') + lugano_D14_nonCMR",
             master, "ctDNA-JLCM + Lugano_D14 (OS)")
)
if (!is.null(pred_dv)) {
  cindex_os <- c(cindex_os, list(
    get_cindex("Surv(os_time, os_event) ~ I(deauville_jlcm=='MAUVAIS_dv')",
               master, "Deauville-JLCM only (OS)"),
    get_cindex("Surv(os_time, os_event) ~ I(ctdna_jlcm=='MAUVAIS') + I(deauville_jlcm=='MAUVAIS_dv')",
               master, "ctDNA-JLCM + Deauville-JLCM (OS)")
  ))
}
cindex_os_df <- do.call(rbind, cindex_os)
cindex_df <- rbind(cindex_efs_df, cindex_os_df)
write.csv(cindex_df, file.path(DATA, "deauville_cindex.csv"), row.names = FALSE)
cat("\n[C-index]\n"); print(cindex_df)

# ---------- 7. Master metrics file ----------------------------------------
# Single consolidated CSV
metrics <- cox_uni_df |> mutate(analysis = "univariate")
master_df <- cox_uni_df
write.csv(master_df, file.path(DATA, "deauville_metrics.csv"), row.names = FALSE)
cat("\n[save] deauville_metrics.csv (univariate Cox master)\n")

cat("\n[done] Phase 2 Deauville analyses complete.\n")
