################################################################################
# Génération des données LOO pour les figures (57 patients)
# 1. jlcm_loo_predictions.csv — predictClass par horizon (modèle complet)
# 2. jlcm_loo_validation_summary.csv — ΔBIC + concordance par fold LOO
################################################################################

# === Path resolution (added for package portability) ===
.script_dir <- tryCatch({
  args <- commandArgs(trailingOnly = FALSE)
  fa <- grep("^--file=", args, value = TRUE)
  if (length(fa) > 0) dirname(normalizePath(sub("^--file=", "", fa[1]), mustWork = FALSE))
  else dirname(sys.frame(1)$ofile)
}, error = function(e) getwd())
if (file.exists(file.path(.script_dir, "_paths.R"))) {
  source(file.path(.script_dir, "_paths.R"))
} else if (file.exists(file.path(.script_dir, "..", "_paths.R"))) {
  source(file.path(.script_dir, "..", "_paths.R"))
} else {
  PKG_ROOT    <- normalizePath(file.path(.script_dir, ".."), mustWork = FALSE)
  INPUT_DIR   <- file.path(PKG_ROOT, "input")
  OUTPUT_DIR  <- file.path(PKG_ROOT, "output")
  TABLES_DIR  <- file.path(OUTPUT_DIR, "tables")
  FIGURES_DIR <- file.path(OUTPUT_DIR, "figures")
  DATA_DIR    <- INPUT_DIR
  for (d in c(TABLES_DIR, FIGURES_DIR)) if (!dir.exists(d)) dir.create(d, recursive=TRUE)
}
# === end path resolution ===

library(lcmm)
library(survival)

setwd(.script_dir)

# ── Données ──────────────────────────────────────────────────────────────────
dat  <- read.csv("data_lcmm_long.csv")
rr   <- read.csv("rr_strict_mapping.csv")
id_map <- unique(dat[, c("ID", "randomisation")])
rr2 <- merge(rr[, c("randomisation", "rr_12", "rr_24", "rr_12_24")], id_map, by = "randomisation")

surv <- unique(dat[, c("ID", "randomisation", "efs_event", "efs_time")])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
surv <- merge(surv, rr2[, c("ID", "rr_12", "rr_24", "rr_12_24")], by = "ID", all.x = TRUE)
surv$rr_12_24 <- as.integer(surv$rr_24 == 1 & surv$rr_12 == 0)

dat_jlcm <- merge(dat, surv[, c("ID", "efs_event", "efs_time")],
                   by = "ID", suffixes = c("", ".s"))
dat_jlcm$Tevent <- dat_jlcm$efs_time.s
dat_jlcm$Event  <- dat_jlcm$efs_event.s

ids <- sort(unique(dat_jlcm$ID))
N   <- length(ids)

# ── Modèle complet ──────────────────────────────────────────────────────────
jrt <- readRDS("output/data/jlcm_heg_random_time_model.rds")
pp_full <- jrt$pprob
r1 <- mean(surv$rr_12[surv$ID %in% pp_full$ID[pp_full$class == 1]], na.rm = TRUE)
r2 <- mean(surv$rr_12[surv$ID %in% pp_full$ID[pp_full$class == 2]], na.rm = TRUE)
mauv_full <- ifelse(r1 > r2, 1, 2); bon_full <- 3 - mauv_full
prob_col <- paste0("probYT", mauv_full)
cat(sprintf("Modèle complet : MAUVAIS=cl%d | BON=cl%d (N=%d)\n", mauv_full, bon_full, N))

# ── PARTIE 1 : Predictions par horizon (modèle complet, truncated data) ────
horizons <- c(J14 = 0.46, M1 = 1.02, M3 = 2.99, M6 = 6.03, M9 = 9.05, M12 = 11.99)

cat(sprintf("\n=== Predictions par horizon : %d patients x %d horizons ===\n", N, length(horizons)))
pred_list <- list()
n_ok <- 0; n_echec <- 0

for (i in seq_along(ids)) {
  pat_id <- ids[i]
  pat_dat <- dat_jlcm[dat_jlcm$ID == pat_id, ]

  for (h_name in names(horizons)) {
    h_time <- horizons[h_name]
    dat_trunc <- pat_dat[pat_dat$time <= h_time, ]
    if (nrow(dat_trunc) == 0) next

    tryCatch({
      pred <- predictClass(jrt, newdata = dat_trunc)
      p_mauv <- pred[1, prob_col]
      group <- ifelse(p_mauv > 0.5, "MAUVAIS", "BON")
      pred_list[[length(pred_list) + 1]] <- data.frame(
        ID = pat_id, horizon = h_name, hz_time = h_time,
        p_mauvais = p_mauv, group = group)
      n_ok <- n_ok + 1
    }, error = function(e) { n_echec <<- n_echec + 1 })
  }
}

loo_pred <- do.call(rbind, pred_list)
write.csv(loo_pred, "output/data/jlcm_loo_predictions.csv", row.names = FALSE)
cat(sprintf("Predictions horizon : %d OK | %d échecs\n", n_ok, n_echec))

# ── PARTIE 2 : LOO ΔBIC + concordance (57 folds) ──────────────────────────
cat(sprintf("\n=== LOO ΔBIC : %d folds ===\n", N))

full_classes <- pp_full[, c("ID", "class")]
names(full_classes)[2] <- "full_class"

loo_summary <- data.frame(
  fold = integer(0), ID_left_out = integer(0),
  bic_ng1 = numeric(0), bic_ng2 = numeric(0), delta_bic = numeric(0),
  concordance = numeric(0),
  rr12_mauv = numeric(0), rr12_bon = numeric(0),
  rr24_mauv = numeric(0), rr24_bon = numeric(0),
  status = character(0), stringsAsFactors = FALSE
)

for (i in seq_len(N)) {
  pat_id <- ids[i]
  cat(sprintf("  Fold %d/%d (ID=%d) ... ", i, N, pat_id))

  dat_train <- dat_jlcm[dat_jlcm$ID != pat_id, ]

  tryCatch({
    set.seed(42)
    j1 <- Jointlcmm(heg ~ time + I(time^2), random = ~time, subject = "ID",
                     survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull",
                     ng = 1, data = dat_train, verbose = FALSE)

    set.seed(42)
    j2 <- Jointlcmm(heg ~ time + I(time^2), mixture = ~time + I(time^2),
                     random = ~time, subject = "ID",
                     survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull",
                     ng = 2, B = j1, data = dat_train, verbose = FALSE)

    dbic <- j1$BIC - j2$BIC

    # Concordance with full model
    pp_k <- j2$pprob
    m_k <- merge(pp_k, surv, by = "ID")
    r1k <- mean(m_k$rr_12[m_k$class == 1], na.rm = TRUE)
    r2k <- mean(m_k$rr_12[m_k$class == 2], na.rm = TRUE)
    mauv_k <- ifelse(r1k > r2k, 1, 2)

    pp_k$group_k <- ifelse(pp_k$class == mauv_k, "MAUVAIS", "BON")
    comp <- merge(pp_k[, c("ID", "group_k")], full_classes, by = "ID")
    comp$group_full <- ifelse(comp$full_class == mauv_full, "MAUVAIS", "BON")
    conc <- mean(comp$group_k == comp$group_full)

    rr12m <- mean(m_k$rr_12[m_k$class == mauv_k], na.rm = TRUE)
    rr12b <- mean(m_k$rr_12[m_k$class != mauv_k], na.rm = TRUE)
    rr24m <- mean(m_k$rr_24[m_k$class == mauv_k], na.rm = TRUE)
    rr24b <- mean(m_k$rr_24[m_k$class != mauv_k], na.rm = TRUE)

    loo_summary <- rbind(loo_summary, data.frame(
      fold = i, ID_left_out = pat_id,
      bic_ng1 = j1$BIC, bic_ng2 = j2$BIC, delta_bic = dbic,
      concordance = conc, rr12_mauv = rr12m, rr12_bon = rr12b,
      rr24_mauv = rr24m, rr24_bon = rr24b, status = "OK"))

    cat(sprintf("OK | ΔBIC=%.1f | conc=%.0f%%\n", dbic, conc * 100))

  }, error = function(e) {
    loo_summary <<- rbind(loo_summary, data.frame(
      fold = i, ID_left_out = pat_id,
      bic_ng1 = NA, bic_ng2 = NA, delta_bic = NA,
      concordance = NA, rr12_mauv = NA, rr12_bon = NA,
      rr24_mauv = NA, rr24_bon = NA, status = gsub("\n", " ", e$message)))
    cat(sprintf("ERREUR\n"))
  })
}

write.csv(loo_summary, "output/data/jlcm_loo_validation_summary.csv", row.names = FALSE)

ok <- loo_summary[loo_summary$status == "OK", ]
cat(sprintf("\n=== %d/%d folds OK ===\n", nrow(ok), N))
if (nrow(ok) > 0) {
  cat(sprintf("ΔBIC : médiane=%.1f [%.1f ; %.1f] | >0: %d/%d\n",
              median(ok$delta_bic), min(ok$delta_bic), max(ok$delta_bic),
              sum(ok$delta_bic > 0), nrow(ok)))
  cat(sprintf("Concordance : médiane=%.0f%% | min=%.0f%%\n",
              100*median(ok$concordance), 100*min(ok$concordance)))
}

cat("\nDone.\n")
