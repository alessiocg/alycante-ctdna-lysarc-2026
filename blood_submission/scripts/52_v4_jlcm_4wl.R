################################################################################
# V4 rebuild — JLCM (Jointlcmm) sur les 4 versions de WL (seed=123).
# Demontre que la classification latente est ROBUSTE a la definition de WL :
# les 4 versions donnent la meme separation R/R (n_bad=27, RR12 100%/0%).
# Entrees (input/, git-ignore) : data_lcmm_long_REBUILT_4WL.csv, data_lcmm_long.csv,
#                                rr_strict_mapping.csv
################################################################################
suppressMessages({library(lcmm); library(survival)})
SCRIPT_DIR <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1]), mustWork = FALSE))
source(file.path(SCRIPT_DIR, "_paths.R"))
rr  <- read.csv(input_path("rr_strict_mapping.csv"))
d4  <- read.csv(input_path("data_lcmm_long_REBUILT_4WL.csv"))
old <- read.csv(input_path("data_lcmm_long.csv"))
d4$randomisation <- trimws(as.character(d4$randomisation)); old$randomisation <- trimws(as.character(old$randomisation)); rr$randomisation <- trimws(as.character(rr$randomisation))
efs <- unique(old[, c("randomisation", "efs_time", "efs_event")]); efs <- efs[!is.na(efs$efs_time) & efs$efs_time > 0, ]
cat(sprintf("4WL patients=%d ; EFS dispo=%d ; intersection=%d\n", length(unique(d4$randomisation)), nrow(efs), length(intersect(unique(d4$randomisation), efs$randomisation))))
d <- merge(d4, efs, by = "randomisation"); d$ID <- as.integer(factor(d$randomisation)); d$Tevent <- d$efs_time; d$Event <- d$efs_event
idmap <- unique(d[, c("ID", "randomisation")]); rr2 <- merge(rr[, c("randomisation", "rr_12")], idmap, by = "randomisation"); rr2 <- rr2[!duplicated(rr2$ID), ]
fitV <- function(v) {
  dv <- d; dv$heg <- as.numeric(dv[[paste0("heg_", v)]]); dv <- dv[!is.na(dv$heg), ]
  out <- tryCatch({
    set.seed(123); j1 <- Jointlcmm(heg ~ time + I(time^2), random = ~time, subject = "ID", survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull", ng = 1, data = dv, verbose = FALSE)
    set.seed(123); j2 <- Jointlcmm(heg ~ time + I(time^2), mixture = ~time + I(time^2), random = ~time, subject = "ID", survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull", ng = 2, B = j1, data = dv, verbose = FALSE)
    pp <- as.data.frame(j2$pprob); m <- merge(data.frame(ID = pp$ID, class = pp$class), rr2, by = "ID")
    surv <- unique(dv[, c("ID", "efs_time", "efs_event")]); surv <- surv[!duplicated(surv$ID), ]; m <- merge(m, surv, by = "ID")
    r1 <- mean(m$rr_12[m$class == 1], na.rm = T); r2 <- mean(m$rr_12[m$class == 2], na.rm = T); mauv <- ifelse(r1 > r2, 1, 2); m$bad <- as.integer(m$class == mauv)
    hr <- tryCatch(as.numeric(exp(coef(coxph(Surv(efs_time, efs_event) ~ bad, data = m)))[1]), error = function(e) NA)
    list(BIC = j2$BIC, conv = j2$conv, n = nrow(m), nbad = sum(m$bad), rr12 = round(100 * max(r1, r2)), rr12bon = round(100 * min(r1, r2)), evbad = sum(m$efs_event[m$bad == 1]), hr = hr)
  }, error = function(e) {cat(v, "ERR:", conditionMessage(e), "\n"); NULL})
  out
}
cat("\n=== JLCM par WL (seed=123) ===\n")
cat(sprintf("%-4s %4s %7s %5s %5s %8s %8s %8s\n", "WL", "conv", "BIC", "Npat", "nbad", "RR12 b/g", "evbad", "HR"))
for (v in c("V1", "V2", "V3", "V4")) {
  x <- fitV(v); if (is.null(x)) next
  cat(sprintf("%-4s %4d %7.0f %5d %5d %4d/%-3d %8d %8.1f\n", v, x$conv, x$BIC, x$n, x$nbad, x$rr12, x$rr12bon, x$evbad, x$hr))
}
cat("(BIC NON comparable entre WL: outcome heg differe. Comparer separation R/R + HR + stabilite.)\nDone.\n")
