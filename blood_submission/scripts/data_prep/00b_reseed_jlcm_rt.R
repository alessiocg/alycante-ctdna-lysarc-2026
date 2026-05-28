################################################################################
# Re-seed JLCM random=~time sur 57 patients
# Teste plusieurs seeds pour trouver un modèle où predictClass() fonctionne
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

dat  <- read.csv("data_lcmm_long.csv")
rr   <- read.csv("rr_strict_mapping.csv")
id_map <- unique(dat[, c("ID", "randomisation")])
rr2 <- merge(rr[, c("randomisation", "rr_12", "rr_24")], id_map, by = "randomisation")

surv <- unique(dat[, c("ID", "randomisation", "efs_event", "efs_time")])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
surv <- merge(surv, rr2[, c("ID", "rr_12", "rr_24")], by = "ID", all.x = TRUE)

dat_jlcm <- merge(dat, surv[, c("ID", "efs_event", "efs_time")],
                   by = "ID", suffixes = c("", ".s"))
dat_jlcm$Tevent <- dat_jlcm$efs_time.s
dat_jlcm$Event  <- dat_jlcm$efs_event.s

ids <- sort(unique(dat_jlcm$ID))
N <- length(ids)
cat(sprintf("N = %d patients\n", N))

# Test predictClass on 10 patients (full + truncated M6)
test_predict <- function(model, dat_jlcm, ids_test) {
  n_ok_full <- 0; n_ok_trunc <- 0; n_test <- length(ids_test)
  for (id in ids_test) {
    pat_full <- dat_jlcm[dat_jlcm$ID == id, ]
    pat_trunc <- dat_jlcm[dat_jlcm$ID == id & dat_jlcm$time <= 6.03, ]
    tryCatch({ predictClass(model, newdata = pat_full); n_ok_full <- n_ok_full + 1 },
             error = function(e) {})
    if (nrow(pat_trunc) > 0) {
      tryCatch({ predictClass(model, newdata = pat_trunc); n_ok_trunc <- n_ok_trunc + 1 },
               error = function(e) {})
    }
  }
  c(full = n_ok_full, trunc = n_ok_trunc, n = n_test)
}

# Seeds to try
seeds <- c(42, 123, 456, 789, 1000, 2024, 3141, 5000, 7777, 9999,
           11, 22, 33, 44, 55, 66, 77, 88, 99, 100)
ids_test <- ids[1:15]

best_seed <- NA; best_bic <- Inf; best_predict_score <- 0

results <- data.frame(seed=integer(), bic=numeric(), conv=integer(),
                      n_cl1=integer(), n_cl2=integer(),
                      rr12_mauv=numeric(), predict_full=integer(),
                      predict_trunc=integer(), stringsAsFactors=FALSE)

for (s in seeds) {
  cat(sprintf("\n=== Seed %d ===\n", s))

  tryCatch({
    set.seed(s)
    j1 <- Jointlcmm(heg ~ time + I(time^2), random = ~time, subject = "ID",
                     survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull",
                     ng = 1, data = dat_jlcm, verbose = FALSE)

    set.seed(s)
    j2 <- Jointlcmm(heg ~ time + I(time^2), mixture = ~time + I(time^2),
                     random = ~time, subject = "ID",
                     survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull",
                     ng = 2, B = j1, data = dat_jlcm, verbose = FALSE)

    pp <- j2$pprob
    r1 <- mean(surv$rr_12[surv$ID %in% pp$ID[pp$class == 1]], na.rm = TRUE)
    r2 <- mean(surv$rr_12[surv$ID %in% pp$ID[pp$class == 2]], na.rm = TRUE)
    mauv <- ifelse(r1 > r2, 1, 2)
    rr12_mauv <- max(r1, r2) * 100

    cat(sprintf("  BIC=%.1f | conv=%d | cl1=%d cl2=%d | MAUVAIS=cl%d (R/R12=%.0f%%)\n",
                j2$BIC, j2$conv, sum(pp$class==1), sum(pp$class==2), mauv, rr12_mauv))

    # Test predictClass
    tp <- test_predict(j2, dat_jlcm, ids_test)
    cat(sprintf("  predictClass: full=%d/%d | trunc_M6=%d/%d\n",
                tp["full"], tp["n"], tp["trunc"], tp["n"]))

    results <- rbind(results, data.frame(
      seed = s, bic = j2$BIC, conv = j2$conv,
      n_cl1 = sum(pp$class==1), n_cl2 = sum(pp$class==2),
      rr12_mauv = rr12_mauv,
      predict_full = tp["full"], predict_trunc = tp["trunc"]))

    # Best = highest predict score, then lowest BIC
    score <- tp["full"] + tp["trunc"]
    if (score > best_predict_score || (score == best_predict_score && j2$BIC < best_bic)) {
      best_seed <- s; best_bic <- j2$BIC; best_predict_score <- score
      saveRDS(j2, "output/data/jlcm_heg_random_time_model_best.rds")
      cat(sprintf("  >>> NEW BEST (score=%d, BIC=%.1f)\n", score, j2$BIC))
    }

  }, error = function(e) {
    cat(sprintf("  ERREUR: %s\n", e$message))
  })
}

cat("\n\n=== RESULTATS ===\n")
print(results[order(-results$predict_full, -results$predict_trunc, results$bic), ])
cat(sprintf("\nMeilleur seed: %d (BIC=%.1f, predict_score=%d)\n",
            best_seed, best_bic, best_predict_score))

cat("Done.\n")
