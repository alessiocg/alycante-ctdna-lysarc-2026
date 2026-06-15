################################################################################
# V4 rebuild — Re-validation EXTERNE Lea : modele V4 (ALYCANTE rebuilt) FIGE ->
# predictClass sur la cohorte routine propre -> timeROC IPCW. Modele non touche par Lea.
# Entrees (input/, git-ignore) : data_lcmm_long_REBUILT_4WL.csv, data_lcmm_long.csv,
#                                rr_strict_mapping.csv, lea_all_jlcm_input.csv
# Sorties (input/, git-ignore) : model_V4_alycante.rds, lea_revalidation_V4_pred.csv
################################################################################
suppressMessages({library(lcmm); library(survival); library(timeROC)})
SCRIPT_DIR <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1]), mustWork = FALSE))
source(file.path(SCRIPT_DIR, "_paths.R"))
rr <- read.csv(input_path("rr_strict_mapping.csv"))
# --- 1. Fit V4 sur ALYCANTE rebuilt (FIGE) ---
d4  <- read.csv(input_path("data_lcmm_long_REBUILT_4WL.csv"))
old <- read.csv(input_path("data_lcmm_long.csv"))
d4$randomisation <- trimws(as.character(d4$randomisation)); old$randomisation <- trimws(as.character(old$randomisation)); rr$randomisation <- trimws(as.character(rr$randomisation))
efs <- unique(old[, c("randomisation", "efs_time", "efs_event")]); efs <- efs[!is.na(efs$efs_time) & efs$efs_time > 0, ]
d <- merge(d4, efs, by = "randomisation"); d$heg <- as.numeric(d$heg_V4); d <- d[!is.na(d$heg), ]
d$ID <- as.integer(factor(d$randomisation)); d$Tevent <- d$efs_time; d$Event <- d$efs_event
set.seed(123); j1 <- Jointlcmm(heg ~ time + I(time^2), random = ~time, subject = "ID", survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull", ng = 1, data = d, verbose = FALSE)
set.seed(123); jV4 <- Jointlcmm(heg ~ time + I(time^2), mixture = ~time + I(time^2), random = ~time, subject = "ID", survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull", ng = 2, B = j1, data = d, verbose = FALSE)
saveRDS(jV4, input_path("model_V4_alycante.rds"))
idmap <- unique(d[, c("ID", "randomisation")]); rr2 <- merge(rr[, c("randomisation", "rr_12")], idmap, by = "randomisation"); rr2 <- rr2[!duplicated(rr2$ID), ]
pp <- as.data.frame(jV4$pprob); m <- merge(data.frame(ID = pp$ID, class = pp$class), rr2, by = "ID")
r1 <- mean(m$rr_12[m$class == 1], na.rm = T); r2 <- mean(m$rr_12[m$class == 2], na.rm = T); mauv <- ifelse(r1 > r2, 1, 2); pcol <- paste0("probYT", mauv)
cat(sprintf("Modele V4 fige : BIC=%.0f, classe MAUVAIS=cl%d\n", jV4$BIC, mauv))
cat(sprintf("ALYCANTE heg_V4 (train) mediane=%.2f ; ", median(d$heg)))
# --- 2. Lea cohorte propre ---
lea <- read.csv(input_path("lea_all_jlcm_input.csv")); lea$heg <- as.numeric(lea$heg)
lea$Tevent <- lea$efs_time; lea$Event <- lea$efs_event
cat(sprintf("Lea heg (clean) mediane positifs=%.2f\n", median(lea$heg[lea$mrd_pos == 1], na.rm = T)))
ids <- sort(unique(lea$ID)); pred <- data.frame()
for (id in ids) {
  pat <- lea[lea$ID == id, ]
  pc <- tryCatch(predictClass(jV4, newdata = pat), error = function(e) NULL)
  if (is.null(pc)) next
  ev <- pat[1, c("efs_time", "efs_event")]
  pred <- rbind(pred, data.frame(ID = id, p_bad = as.numeric(pc[1, pcol]), efs_time = ev$efs_time, efs_event = ev$efs_event))
}
write.csv(pred, input_path("lea_revalidation_V4_pred.csv"), row.names = FALSE)
cat(sprintf("\nLea classes : %d/%d patients\n", nrow(pred), length(ids)))
pred <- pred[!is.na(pred$efs_time) & pred$efs_time > 0, ]
cat(sprintf("Lea evaluables (EFS>0) : %d | events : %d | groupe MAUVAIS (p>0.5): %d\n", nrow(pred), sum(pred$efs_event), sum(pred$p_bad > 0.5)))
# --- 3. timeROC IPCW ---
ac <- function(t) {
  r <- tryCatch(timeROC(T = pred$efs_time, delta = pred$efs_event, marker = pred$p_bad, cause = 1, times = t, weighting = "marginal", iid = TRUE), error = function(e) NULL)
  if (is.null(r)) {cat("  timeROC err @", t[length(t)], "\n"); return()}
  i <- length(t); sd <- r$inference$vect_sd_1[i]
  ss <- SeSpPPVNPV(0.5, T = pred$efs_time, delta = pred$efs_event, marker = pred$p_bad, cause = 1, times = t, weighting = "marginal")
  cat(sprintf("  @%dm: AUC=%.3f [%.2f-%.2f] | Se=%d Sp=%d VPP=%d VPN=%d\n", t[i], r$AUC[i], max(0, r$AUC[i] - 1.96 * sd), min(1, r$AUC[i] + 1.96 * sd),
      round(100 * ss$TP[i]), round(100 * (1 - ss$FP[i])), round(100 * ss$PPV[i]), round(100 * ss$NPV[i])))
}
pred$grp <- as.integer(pred$p_bad > 0.5)
sd1 <- tryCatch(survdiff(Surv(efs_time, efs_event) ~ grp, data = pred), error = function(e) NULL)
cat("\n=== Re-validation Lea (modele V4 fige) ===\n")
ac(c(6, 12)); ac(c(6, 12, 24))
if (!is.null(sd1)) cat(sprintf("  logrank MAUVAIS vs BON: p=%.4f\n", 1 - pchisq(sd1$chisq, 1)))
cat("Done.\n")
