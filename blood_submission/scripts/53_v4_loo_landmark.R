################################################################################
# V4 rebuild — LOO-landmark J14 HONNETE sur la WL V4 (reference).
# Pour chaque patient : refit JLCM sur les 56 autres (seed=123), puis predictClass
# sur ses donnees <=J14 (out-of-sample). Puis timeROC IPCW @12/24m.
# Entrees (input/, git-ignore) : data_lcmm_long_REBUILT_4WL.csv, data_lcmm_long.csv,
#                                rr_strict_mapping.csv
################################################################################
suppressMessages({library(lcmm); library(survival); library(timeROC)})
SCRIPT_DIR <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1]), mustWork = FALSE))
source(file.path(SCRIPT_DIR, "_paths.R"))
rr  <- read.csv(input_path("rr_strict_mapping.csv"))
d4  <- read.csv(input_path("data_lcmm_long_REBUILT_4WL.csv"))
old <- read.csv(input_path("data_lcmm_long.csv"))
d4$randomisation <- trimws(as.character(d4$randomisation)); old$randomisation <- trimws(as.character(old$randomisation)); rr$randomisation <- trimws(as.character(rr$randomisation))
efs <- unique(old[, c("randomisation", "efs_time", "efs_event")]); efs <- efs[!is.na(efs$efs_time) & efs$efs_time > 0, ]
d <- merge(d4, efs, by = "randomisation"); d$heg <- as.numeric(d$heg_V4); d <- d[!is.na(d$heg), ]
d$ID <- as.integer(factor(d$randomisation)); d$Tevent <- d$efs_time; d$Event <- d$efs_event
idmap <- unique(d[, c("ID", "randomisation")]); rr2 <- merge(rr[, c("randomisation", "rr_12", "rr_24")], idmap, by = "randomisation"); rr2 <- rr2[!duplicated(rr2$ID), ]
ids <- sort(unique(d$ID)); N <- length(ids)
cat(sprintf("V4 LOO-landmark : %d patients\n", N))
oos <- data.frame()
for (i in seq_along(ids)) {
  pid <- ids[i]; train <- d[d$ID != pid, ]
  val <- tryCatch({
    set.seed(123); j1 <- Jointlcmm(heg ~ time + I(time^2), random = ~time, subject = "ID", survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull", ng = 1, data = train, verbose = FALSE)
    set.seed(123); j2 <- Jointlcmm(heg ~ time + I(time^2), mixture = ~time + I(time^2), random = ~time, subject = "ID", survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull", ng = 2, B = j1, data = train, verbose = FALSE)
    pp <- as.data.frame(j2$pprob); m <- merge(data.frame(ID = pp$ID, class = pp$class), rr2, by = "ID")
    r1 <- mean(m$rr_12[m$class == 1], na.rm = T); r2 <- mean(m$rr_12[m$class == 2], na.rm = T); pcol <- paste0("probYT", ifelse(r1 > r2, 1, 2))
    patd <- d[d$ID == pid & d$time <= 0.46, ]
    if (nrow(patd) == 0) NA else as.numeric(predictClass(j2, newdata = patd)[1, pcol])
  }, error = function(e) NA)
  if (!is.na(val)) {
    ev <- unique(d[d$ID == pid, c("efs_time", "efs_event")])[1, ]; rv <- rr2[rr2$ID == pid, ]
    oos <- rbind(oos, data.frame(ID = pid, p_bad = val, efs_time = ev$efs_time, efs_event = ev$efs_event,
                 rr_12 = ifelse(nrow(rv) > 0, rv$rr_12, NA), rr_24 = ifelse(nrow(rv) > 0, rv$rr_24, NA)))
  }
  cat(sprintf("fold %d/%d ID=%d -> %s\n", i, N, pid, ifelse(is.na(val), "NA", sprintf("%.3f", val))))
}
write.csv(oos, input_path("loo_landmark_V4_oos.csv"), row.names = FALSE)
cat(sprintf("\nOOS: %d/%d patients classes a J14\n", nrow(oos), N))
ac <- function(t) {
  r <- timeROC(T = oos$efs_time, delta = oos$efs_event, marker = oos$p_bad, cause = 1, times = t, weighting = "marginal", iid = TRUE)
  i <- length(t); sd <- r$inference$vect_sd_1[i]; ss <- SeSpPPVNPV(0.5, T = oos$efs_time, delta = oos$efs_event, marker = oos$p_bad, cause = 1, times = t, weighting = "marginal")
  cat(sprintf("  @%dm: AUC=%.3f [%.2f-%.2f] | Se=%d Sp=%d VPP=%d VPN=%d\n", t[i], r$AUC[i], max(0, r$AUC[i] - 1.96 * sd), min(1, r$AUC[i] + 1.96 * sd),
      round(100 * ss$TP[i]), round(100 * (1 - ss$FP[i])), round(100 * ss$PPV[i]), round(100 * ss$NPV[i])))
}
nv <- function(tr) {
  z <- oos[!is.na(oos[[tr]]), ]; pb <- as.integer(z$p_bad > 0.5)
  TP <- sum(pb & z[[tr]] == 1); FP <- sum(pb & z[[tr]] == 0); FN <- sum(!pb & z[[tr]] == 1); TN <- sum(!pb & z[[tr]] == 0)
  cat(sprintf("  naif %s: N=%d Se=%d Sp=%d VPP=%d VPN=%d\n", tr, nrow(z), round(100 * TP / max(TP + FN, 1)), round(100 * TN / max(TN + FP, 1)), round(100 * TP / max(TP + FP, 1)), round(100 * TN / max(TN + FN, 1))))
}
cat("\n=== V4 LOO-landmark HONNETE (out-of-sample) ===\n")
ac(c(6, 12)); ac(c(6, 12, 24)); nv("rr_12"); nv("rr_24")
cat("Done.\n")
