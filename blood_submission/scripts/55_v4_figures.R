################################################################################
# V4 rebuild — toutes les figures de validation (trajectoires +/- IC, KM ALYCANTE & Lea
# +/- effectifs a risque, timeROC, survie predite jointe, decalage d'echelle + transfert).
# Entrees (input/, git-ignore) : model_V4_alycante.rds, data_lcmm_long_REBUILT_4WL.csv,
#   data_lcmm_long.csv, lea_all_jlcm_input.csv, loo_landmark_V4_oos.csv, lea_revalidation_V4_pred.csv
# Sorties : output/figures/Fig_v4_*.png  (agregat, sans PHI -> commitees)
################################################################################
suppressMessages({library(lcmm); library(survival); library(timeROC); library(survminer); library(ggplot2)})
SCRIPT_DIR <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1]), mustWork = FALSE))
source(file.path(SCRIPT_DIR, "_paths.R"))
FP <- function(n) figure_path(n)
jV4 <- readRDS(input_path("model_V4_alycante.rds"))
d4  <- read.csv(input_path("data_lcmm_long_REBUILT_4WL.csv"))
old <- read.csv(input_path("data_lcmm_long.csv"))
d4$randomisation <- trimws(as.character(d4$randomisation)); old$randomisation <- trimws(as.character(old$randomisation))
efs <- unique(old[, c("randomisation", "efs_time", "efs_event")]); efs <- efs[!is.na(efs$efs_time) & efs$efs_time > 0, ]
d <- merge(d4, efs, by = "randomisation"); d$heg <- as.numeric(d$heg_V4); d <- d[!is.na(d$heg), ]
d$ID <- as.integer(factor(d$randomisation))
pp <- as.data.frame(jV4$pprob); cls <- data.frame(ID = pp$ID, class = pp$class)
dpat0 <- unique(d[, c("ID", "efs_time", "efs_event")]); tmp <- merge(cls, dpat0, by = "ID")
er <- tapply(tmp$efs_event, tmp$class, mean); mauv <- as.integer(names(which.max(er)))
cls$grp <- ifelse(cls$class == mauv, "MRD persistant (mauvais)", "Clairance (bon)"); d <- merge(d, cls, by = "ID")
COL <- c("Clairance (bon)" = "#1b7837", "MRD persistant (mauvais)" = "#b2182b")
col_by_class <- c(ifelse(1 == mauv, COL[2], COL[1]), ifelse(2 == mauv, COL[2], COL[1]))
lea <- read.csv(input_path("lea_all_jlcm_input.csv")); lea$heg <- as.numeric(lea$heg)
oos <- read.csv(input_path("loo_landmark_V4_oos.csv"))
lp <- read.csv(input_path("lea_revalidation_V4_pred.csv")); lp <- lp[!is.na(lp$efs_time) & lp$efs_time > 0, ]
lp$grp <- ifelse(lp$p_bad > 0.5, "MRD persistant (mauvais)", "Clairance (bon)")

# --- Fig_v4_trajectories : spaghetti + moyennes predites ---
png(FP("Fig_v4_trajectories.png"), width = 2000, height = 1400, res = 200); par(mar = c(4.5, 4.5, 3, 1))
plot(NA, xlim = c(-1.6, 12), ylim = range(d$heg), xlab = "Temps depuis injection (mois)", ylab = "heg = log10(hEG tumoral)",
     main = "JLCM V4 — trajectoires ctDNA par classe latente (ALYCANTE, n=57)")
for (id in unique(d$ID)) {s <- d[d$ID == id, ]; s <- s[order(s$time), ]; lines(s$time, s$heg, col = adjustcolor(COL[s$grp[1]], .35), lwd = 1)}
tt <- seq(-1.5, 12, .25); py <- tryCatch(predictY(jV4, newdata = data.frame(time = tt), draws = FALSE), error = function(e) NULL)
if (!is.null(py)) {yy <- py$pred; for (k in 1:2) {gname <- ifelse(k == mauv, "MRD persistant (mauvais)", "Clairance (bon)"); lines(tt, yy[, k], col = COL[gname], lwd = 4)}}
abline(v = 0.46, lty = 3, col = "grey40"); text(0.46, max(d$heg), "J14", pos = 4, cex = .8, col = "grey40")
legend("topright", legend = names(COL), col = COL, lwd = 3, bty = "n", cex = .95); dev.off()

# --- Fig_v4_trajectories_CI : moyennes predites + IC95% ---
P <- as.data.frame(predictY(jV4, newdata = data.frame(time = tt), draws = TRUE)$pred)
g <- function(pre, k) {j <- grep(paste0("^", pre, ".*class", k, "$"), colnames(P)); if (length(j)) P[[j[1]]] else rep(NA, nrow(P))}
png(FP("Fig_v4_trajectories_CI.png"), width = 2000, height = 1400, res = 200); par(mar = c(4.5, 4.5, 3, 1))
plot(NA, xlim = c(-1.6, 12), ylim = range(d$heg), xlab = "Temps depuis injection (mois)", ylab = "heg = log10(hEG tumoral)",
     main = "JLCM V4 — trajectoires moyennes predites + IC95% par classe")
for (k in 1:2) {gname <- ifelse(k == mauv, "MRD persistant (mauvais)", "Clairance (bon)"); cc <- COL[gname]
  lo <- g("lower", k); hi <- g("upper", k); me <- g("Ypred", k)
  if (all(!is.na(lo))) polygon(c(tt, rev(tt)), c(lo, rev(hi)), col = adjustcolor(cc, .18), border = NA)
  lines(tt, me, col = cc, lwd = 4)}
abline(v = 0.46, lty = 3, col = "grey40"); text(0.46, max(d$heg), "J14", pos = 4, cex = .8, col = "grey40")
legend("topright", legend = names(COL), col = COL, lwd = 3, bty = "n", cex = .95); dev.off()

# --- Fig_v4_km_alycante (+ version effectifs a risque) ---
dpat <- unique(d[, c("ID", "grp", "efs_time", "efs_event")])
sf <- survfit(Surv(efs_time, efs_event) ~ grp, data = dpat); sdd <- survdiff(Surv(efs_time, efs_event) ~ grp, data = dpat); pv <- 1 - pchisq(sdd$chisq, 1)
png(FP("Fig_v4_km_alycante.png"), width = 1800, height = 1400, res = 200); par(mar = c(4.5, 4.5, 3, 1))
plot(sf, col = COL[c("Clairance (bon)", "MRD persistant (mauvais)")], lwd = 3, xlab = "Mois depuis injection", ylab = "Survie sans evenement (EFS)",
     main = sprintf("ALYCANTE — EFS par classe JLCM V4 (logrank p<%s)", ifelse(pv < 0.0001, "0.0001", sprintf("%.3f", pv))), mark.time = TRUE)
legend("bottomleft", legend = names(COL), col = COL, lwd = 3, bty = "n", cex = .95); dev.off()
g2 <- ggsurvplot(sf, data = dpat, risk.table = TRUE, pval = TRUE, palette = as.character(COL), legend.labs = names(COL),
     legend.title = "Classe JLCM V4", xlab = "Mois depuis injection", ylab = "EFS", title = "ALYCANTE — EFS par classe (n=57)",
     risk.table.height = 0.26, break.time.by = 12, risk.table.title = "Effectifs a risque")
ggsave(FP("Fig_v4_km_alycante_atrisk.png"), plot = print(g2), width = 8, height = 7, dpi = 200)

# --- Fig_v4_km_lea_validation (+ effectifs) ---
sfl <- survfit(Surv(efs_time, efs_event) ~ grp, data = lp); sdl <- survdiff(Surv(efs_time, efs_event) ~ grp, data = lp); pvl <- 1 - pchisq(sdl$chisq, 1)
png(FP("Fig_v4_km_lea_validation.png"), width = 1800, height = 1400, res = 200); par(mar = c(4.5, 4.5, 3, 1))
plot(sfl, col = COL[c("Clairance (bon)", "MRD persistant (mauvais)")], lwd = 3, xlab = "Mois depuis injection", ylab = "Survie sans evenement (EFS)",
     main = sprintf("Validation externe Lea (routine CAR-T, n=%d) — logrank p<%s", nrow(lp), ifelse(pvl < 0.0001, "0.0001", sprintf("%.3f", pvl))), mark.time = TRUE)
legend("bottomleft", legend = names(COL), col = COL, lwd = 3, bty = "n", cex = .95); dev.off()
g3 <- ggsurvplot(sfl, data = lp, risk.table = TRUE, pval = TRUE, palette = as.character(COL), legend.labs = names(COL),
     legend.title = "Classe predite (V4 fige)", xlab = "Mois depuis injection", ylab = "EFS", title = sprintf("Validation externe Lea (routine CAR-T, n=%d)", nrow(lp)),
     risk.table.height = 0.26, break.time.by = 12, risk.table.title = "Effectifs a risque")
ggsave(FP("Fig_v4_km_lea_validation_atrisk.png"), plot = print(g3), width = 8, height = 7, dpi = 200)

# --- Fig_v4_timeROC_12m : LOO ALYCANTE + Lea ---
rA <- timeROC(T = oos$efs_time, delta = oos$efs_event, marker = oos$p_bad, cause = 1, times = c(6, 12), weighting = "marginal", iid = TRUE)
rL <- timeROC(T = lp$efs_time, delta = lp$efs_event, marker = lp$p_bad, cause = 1, times = c(6, 12), weighting = "marginal", iid = TRUE)
png(FP("Fig_v4_timeROC_12m.png"), width = 1600, height = 1500, res = 200); par(mar = c(4.5, 4.5, 3, 1))
plot(rA$FP[, 2], rA$TP[, 2], type = "l", lwd = 3, col = "#2166ac", xlab = "1 - Specificite", ylab = "Sensibilite", main = "ROC dependant du temps @12 mois (J14 landmark)", xlim = c(0, 1), ylim = c(0, 1))
lines(rL$FP[, 2], rL$TP[, 2], lwd = 3, col = "#b2182b"); abline(0, 1, lty = 3, col = "grey")
legend("bottomright", legend = c(sprintf("ALYCANTE LOO out-of-sample (AUC=%.2f)", rA$AUC[2]), sprintf("Lea validation externe (AUC=%.2f)", rL$AUC[2])), col = c("#2166ac", "#b2182b"), lwd = 3, bty = "n", cex = .9); dev.off()

# --- Fig_v4_survival_predicted : survie sans evenement PREDITE par le modele joint ---
png(FP("Fig_v4_survival_predicted.png"), width = 1800, height = 1400, res = 200); par(mar = c(4.5, 4.5, 3, 1))
ok <- tryCatch({plot(jV4, which = "survival", col = col_by_class, lwd = 3, xlab = "Mois depuis injection", ylab = "EFS predite (modele joint)", main = "ALYCANTE — survie sans evenement PREDITE par classe (JLCM V4)"); TRUE}, error = function(e) FALSE)
if (ok) legend("bottomleft", legend = names(COL), col = COL, lwd = 3, bty = "n", cex = .95); dev.off()

# --- Fig_v4_scale_offset_transfer : decalage d'echelle (A) + transfert par la dynamique (B) ---
aly_pos <- d$heg[d$mrd_V4 == 1]; lea_pos <- lea$heg[lea$mrd_pos == 1]
pb <- rbind(data.frame(p = oos$p_bad, ev = oos$efs_event, coh = "ALYCANTE (LOO)"),
            data.frame(p = lp$p_bad, ev = lp$efs_event, coh = "Lea (externe)"))
bl <- c("ALYCANTE (LOO)\nSans evt", "ALYCANTE (LOO)\nEvt", "Lea (externe)\nSans evt", "Lea (externe)\nEvt")
pb$box <- factor(paste(pb$coh, ifelse(pb$ev == 1, "Evt", "Sans evt"), sep = "\n"), levels = bl)
png(FP("Fig_v4_scale_offset_transfer.png"), width = 2200, height = 1100, res = 200); par(mfrow = c(1, 2), mar = c(4, 4.5, 3.2, 1))
dn1 <- density(aly_pos); dn2 <- density(lea_pos)
plot(dn1, col = "#2166ac", lwd = 3, xlim = range(c(aly_pos, lea_pos)), ylim = c(0, max(dn1$y, dn2$y) * 1.05), xlab = "heg+ = log10(hEG tumoral), MRD+", ylab = "densite", main = "A. Decalage d'echelle des heg+")
lines(dn2, col = "#d6604d", lwd = 3); abline(v = median(aly_pos), col = "#2166ac", lty = 2); abline(v = median(lea_pos), col = "#d6604d", lty = 2)
legend("topright", legend = c(sprintf("ALYCANTE (UMI phases, med=%.2f)", median(aly_pos)), sprintf("Lea (VAF routine, med=%.2f)", median(lea_pos))), col = c("#2166ac", "#d6604d"), lwd = 3, bty = "n", cex = .8)
text(mean(c(median(aly_pos), median(lea_pos))), max(dn1$y, dn2$y), sprintf("~%.1f log", median(aly_pos) - median(lea_pos)), cex = .85, col = "grey30")
bp <- split(pb$p, pb$box)
boxplot(bp, col = c("#1b7837", "#b2182b", "#1b7837", "#b2182b"), ylab = "p(classe MRD persistant) — sortie modele", main = "B. Sortie du modele par devenir (transfert)", cex.axis = .62, las = 1, ylim = c(0, 1)); dev.off()
cat("Figures V4 ecrites dans:", FIGURES_DIR, "\n")
