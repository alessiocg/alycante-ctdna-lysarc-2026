################################################################################
# KM EFS landmark JLCM — modele complet random=~time, donnees tronquees
# Un seul modele fitte sur tous les patients
# Pour chaque horizon H : predictClass sur trajectoire tronquee a H
# Puis KM landmark
################################################################################
library(lcmm)
library(survival)

SCRIPT_DIR <- tryCatch(
  dirname(normalizePath(sys.frame(1)$filename, mustWork = FALSE)),
  error = function(e) getwd()
)
setwd(SCRIPT_DIR)

network <- file.path(
  "\\\\hmn-cifs-hnas.wprod.ds.aphp.fr", "shares",
  "IMMUNOLOGIE-BIOLOGIQUE",
  "SECTEUR MALADIES LYMPHOPROLIFERATIVES",
  "D_PROTOCOLES", "DLBCL",
  "protocole ALYCANTE",
  paste0("R", "\u00e9", "union LYSARC 2026"),
  "output"
)

# ── Donnees ──────────────────────────────────────────────────────────────────
dat   <- read.csv("data/data_lcmm_long.csv")
rr    <- read.csv("data/rr_strict_mapping.csv")
# rr_strict_mapping a 'randomisation', pas 'ID' → joindre via dat
id_map <- unique(dat[, c("ID", "randomisation")])
rr2 <- merge(rr[, c("randomisation", "rr_12", "rr_24", "rr_12_24")], id_map, by = "randomisation")
surv  <- unique(dat[, c("ID", "efs_event", "efs_time")])
surv  <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
surv  <- merge(surv, rr2[, c("ID", "rr_12", "rr_24")], by = "ID", all.x = TRUE)
surv$rr_event <- surv$rr_24   # event KM = tout R/R

dat_jlcm <- merge(dat, surv[, c("ID", "efs_event", "efs_time")], by = "ID",
                  suffixes = c("", ".s"))
dat_jlcm$Tevent <- dat_jlcm$efs_time.s
dat_jlcm$Event  <- dat_jlcm$efs_event.s

horizons  <- c(J14 = 0.46, M1 = 1.02, M3 = 2.99, M6 = 6.03, M9 = 9.05, M12 = 11.99)
ids       <- sort(unique(dat_jlcm$ID))
pred_cache <- "data/jlcm_loo_predictions.csv"

# ── Chargement modele complet random=~time (seed=123, predictClass stable) ─────
jrt <- readRDS("data/jlcm_heg_random_time_model.rds")
pp  <- jrt$pprob
r1  <- mean(surv$rr_12[surv$ID %in% pp$ID[pp$class == 1]], na.rm = TRUE)
r2  <- mean(surv$rr_12[surv$ID %in% pp$ID[pp$class == 2]], na.rm = TRUE)
mauv_cl  <- ifelse(r1 > r2, 1, 2)
prob_col <- paste0("probYT", mauv_cl)
cat(sprintf("Modele complet random=~1 : MAUVAIS=cl%d (R/R12=%.0f%%) | BON=cl%d (R/R12=%.0f%%)\n",
            mauv_cl, max(r1,r2)*100, 3-mauv_cl, min(r1,r2)*100))

# ── Classification par horizon (donnees tronquees, modele complet) ─────────────
if (file.exists(pred_cache)) {
  cat("=== Chargement predictions depuis cache ===\n")
  loo_pred <- read.csv(pred_cache)
} else {
  cat(sprintf("=== Classification horizon : %d patients x %d horizons ===\n",
              length(ids), length(horizons)))

  pred_list <- list()
  n_ok <- 0; n_echec <- 0

  for (i in seq_along(ids)) {
    pat_id    <- ids[i]
    pat_dat   <- dat_jlcm[dat_jlcm$ID == pat_id, ]
    cat(sprintf("  Patient %d/%d (ID=%d)\r", i, length(ids), pat_id))

    for (h_name in names(horizons)) {
      h_time    <- horizons[h_name]
      dat_trunc <- pat_dat[pat_dat$time <= h_time, ]
      if (nrow(dat_trunc) == 0) next

      tryCatch({
        pred   <- predictClass(jrt, newdata = dat_trunc)
        p_mauv <- pred[1, prob_col]
        group  <- ifelse(p_mauv > 0.5, "MAUVAIS", "BON")
        pred_list[[length(pred_list) + 1]] <- data.frame(
          ID        = pat_id,
          horizon   = h_name,
          hz_time   = h_time,
          p_mauvais = p_mauv,
          group     = group
        )
        n_ok <- n_ok + 1
      }, error = function(e) {
        n_echec <<- n_echec + 1
      })
    }
  }

  cat("\n")
  loo_pred <- do.call(rbind, pred_list)
  write.csv(loo_pred, pred_cache, row.names = FALSE)
  cat(sprintf("Predictions : %d OK | %d echecs\n", n_ok, n_echec))
}

# ── Figure KM landmark avec predictions LOO ───────────────────────────────────
max_followup <- max(surv$efs_time, na.rm = TRUE)

outfile <- "fig_km_landmark_jlcm.png"
png(outfile, width = 1800, height = 1200, res = 150)
par(mfrow = c(2, 3), mar = c(4, 4, 3, 1), oma = c(0, 0, 2, 0))

for (h_name in names(horizons)) {
  h_time <- horizons[h_name]

  # Predictions LOO a cet horizon
  loo_h <- loo_pred[loo_pred$horizon == h_name, c("ID", "group")]
  if (nrow(loo_h) == 0) next

  # Merge avec survie
  pred_m  <- merge(loo_h, surv, by = "ID")

  # Landmark : exclure patients avec R/R avant l'horizon
  pred_lm <- pred_m[!(pred_m$rr_event == 1 & pred_m$efs_time < h_time), ]
  pred_lm$surv_time <- pmax(pred_lm$efs_time - h_time, 0.01)

  n_bon   <- sum(pred_lm$group == "BON")
  n_mauv  <- sum(pred_lm$group == "MAUVAIS")
  ev_bon  <- sum(pred_lm$rr_event[pred_lm$group == "BON"])
  ev_mauv <- sum(pred_lm$rr_event[pred_lm$group == "MAUVAIS"])

  cat(sprintf("%s: n=%d | BON=%d (ev=%d) | MAUVAIS=%d (ev=%d)\n",
              h_name, nrow(pred_lm), n_bon, ev_bon, n_mauv, ev_mauv))

  pred_lm$group <- droplevels(factor(pred_lm$group, levels = c("BON", "MAUVAIS")))
  fit <- survfit(Surv(surv_time, rr_event) ~ group, data = pred_lm)

  pval <- tryCatch({
    lr <- survdiff(Surv(surv_time, rr_event) ~ group, data = pred_lm)
    1 - pchisq(lr$chisq, 1)
  }, error = function(e) NA)
  pval_txt <- if (is.na(pval)) "NA" else if (pval < 0.001) "<0.001" else sprintf("%.3f", pval)

  xlim_val <- ceiling((max_followup - h_time) / 5) * 5

  grps_present <- levels(pred_lm$group)
  col_map <- c(BON = "blue", MAUVAIS = "red")
  col_use <- col_map[grps_present]

  plot(fit, col = col_use, lwd = 2, conf.int = FALSE,
       mark.time = TRUE, mark = 3, cex = 0.6,
       xlab = paste0("Temps depuis ", h_name, " (mois)"),
       ylab = "Probabilite EFS (survie sans R/R)",
       main = paste0("Horizon ", h_name),
       xlim = c(0, xlim_val), ylim = c(0, 1), xaxt = "n")
  axis(1, at = seq(0, xlim_val, by = 5))

  # Barres verticales a 12m et 24m post-infusion (J0=t=1 => M12=t=13, M24=t=25)
  v12 <- 12 - h_time
  v24 <- 24 - h_time
  if (v12 > 0 && v12 <= xlim_val) {
    abline(v = v12, lty = 2, col = "gray50", lwd = 1.2)
    text(v12, 0.97, "12m", cex = 0.6, col = "gray40", adj = c(0.5, 1))
  }
  if (v24 > 0 && v24 <= xlim_val) {
    abline(v = v24, lty = 2, col = "gray50", lwd = 1.2)
    text(v24, 0.97, "24m", cex = 0.6, col = "gray40", adj = c(0.5, 1))
  }

  legend("bottomleft", legend = grps_present,
         col = col_use, lwd = 2, bty = "n", cex = 0.9)
  mtext(paste0("p=", pval_txt), side = 3, adj = 1, cex = 0.8, line = 0)
}

mtext("KM EFS par horizon de troncature — JLCM random=~time (analyse landmark)",
      outer = TRUE, cex = 1.2, font = 2)
dev.off()

cat(sprintf("\nFigure : %s\n", outfile))

tryCatch({
  dir.create(network, showWarnings = FALSE, recursive = TRUE)
  file.copy(outfile, network, overwrite = TRUE)
  file.copy(pred_cache, file.path(network, "data"), overwrite = TRUE)
  cat("Copie reseau OK\n")
}, error = function(e) cat(sprintf("Erreur copie: %s\n", e$message)))

tryCatch({
  scripts_dir <- file.path(network, "scripts_figures")
  dir.create(scripts_dir, showWarnings = FALSE, recursive = TRUE)
  file.copy("fig_km_landmark_jlcm_loo.R", scripts_dir, overwrite = TRUE)
  cat("Script copie OK\n")
}, error = function(e) NULL)

cat("Done.\n")
