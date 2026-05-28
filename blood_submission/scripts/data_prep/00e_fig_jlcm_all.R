################################################################################
# JLCM unifie
# 1. jlcm_ng_comparison.csv       : BIC + OR modele complet random=~time (ng=1..4)
# 2. fig_jlcm_comparaison_modeles.png : comparaison individuelle random=~1 vs random=~time
#
# NB : Les courbes theoriques comparatives (random=~1 ref vs random=~time)
#      sont dans fig_jlcm_courbes_theoriques_r1.R
################################################################################
library(lcmm)
library(survival)
library(ggplot2)

# Auto-detect script directory for portability
SCRIPT_DIR <- tryCatch(
  dirname(normalizePath(sys.frame(1)$filename, mustWork = FALSE)),
  error = function(e) getwd()
)
setwd(SCRIPT_DIR)

network <- normalizePath(file.path(OUTPUT_DIR, ".."), mustWork = FALSE)  # legacy NAS root,
  "output"
)

# ── Donnees ───────────────────────────────────────────────────────────────────
dat  <- read.csv("data/data_lcmm_long.csv")
rr   <- read.csv("data/rr_strict_mapping.csv")

# rr_strict_mapping a une colonne 'randomisation', pas 'ID' → joindre via dat
id_map <- unique(dat[, c("ID", "randomisation")])
rr2 <- merge(rr[, c("randomisation", "rr_12", "rr_24", "rr_12_24")], id_map, by = "randomisation")

surv <- unique(dat[, c("ID", "randomisation", "efs_event", "efs_time")])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
surv <- merge(surv, rr2[, c("ID", "rr_12", "rr_24", "rr_12_24")], by = "ID", all.x = TRUE)
surv$rr_12_24 <- as.integer(surv$rr_24 == 1 & surv$rr_12 == 0)

dat_jlcm         <- merge(dat, surv[, c("ID", "efs_event", "efs_time")],
                           by = "ID", suffixes = c("", ".s"))
dat_jlcm$Tevent  <- dat_jlcm$efs_time.s
dat_jlcm$Event   <- dat_jlcm$efs_event.s

# ── Ajout colonnes obligatoires pour Jointlcmm ───────────────────────────────
dat_jlcm$heg2 <- dat_jlcm$time^2   # terme quadratique

# ── Fit ou chargement des deux modeles ───────────────────────────────────────
# Modele 1 : random=~1 (utilise pour LOO-CV)
if (!file.exists("data/jlcm_heg_model.rds")) {
  cat("=== Fitting JLCM ng=1 (init) ===\n")
  set.seed(42)
  j1_r1 <- Jointlcmm(
    heg ~ time + I(time^2),
    random   = ~1,
    subject  = "ID",
    survival = Surv(Tevent, Event) ~ 1,
    hazard   = "Weibull",
    ng       = 1,
    data     = dat_jlcm
  )
  cat("=== Fitting JLCM random=~1 (ng=2) ===\n")
  set.seed(42)
  j2_r1 <- Jointlcmm(
    heg ~ time + I(time^2),
    mixture  = ~ time + I(time^2),
    random   = ~1,
    subject  = "ID",
    survival = Surv(Tevent, Event) ~ 1,
    hazard   = "Weibull",
    ng       = 2,
    B        = j1_r1,
    data     = dat_jlcm
  )
  saveRDS(j2_r1, "data/jlcm_heg_model.rds")
  cat("Sauvegarde: output/data/jlcm_heg_model.rds\n")
} else {
  cat("Chargement jlcm_heg_model.rds\n")
}
j2_r1 <- readRDS("data/jlcm_heg_model.rds")
pp_r1 <- j2_r1$pprob
m_r1  <- merge(pp_r1, surv, by = "ID")
r1a   <- mean(m_r1$rr_12[m_r1$class == 1]); r2a <- mean(m_r1$rr_12[m_r1$class == 2])
mauv_r1 <- ifelse(r1a > r2a, 1, 2); bon_r1 <- 3 - mauv_r1
cat(sprintf("random=~1  : MAUVAIS=cl%d (n=%d, R/R12=%.0f%%)\n",
            mauv_r1, sum(m_r1$class == mauv_r1),
            mean(m_r1$rr_12[m_r1$class == mauv_r1]) * 100))

# Modele 2 : random=~time (modele de reference)
if (!file.exists("data/jlcm_heg_random_time_model.rds")) {
  cat("=== Fitting JLCM ng=1 random=~time (init) ===\n")
  set.seed(42)
  j1_rt <- Jointlcmm(
    heg ~ time + I(time^2),
    random   = ~ time,
    subject  = "ID",
    survival = Surv(Tevent, Event) ~ 1,
    hazard   = "Weibull",
    ng       = 1,
    data     = dat_jlcm
  )
  cat("=== Fitting JLCM random=~time (ng=2) ===\n")
  set.seed(42)
  j2_rt <- Jointlcmm(
    heg ~ time + I(time^2),
    mixture  = ~ time + I(time^2),
    random   = ~ time,
    subject  = "ID",
    survival = Surv(Tevent, Event) ~ 1,
    hazard   = "Weibull",
    ng       = 2,
    B        = j1_rt,
    data     = dat_jlcm
  )
  saveRDS(j2_rt, "data/jlcm_heg_random_time_model.rds")
  cat("Sauvegarde: output/data/jlcm_heg_random_time_model.rds\n")
} else {
  cat("Chargement jlcm_heg_random_time_model.rds\n")
}
j2_rt <- readRDS("data/jlcm_heg_random_time_model.rds")
pp_rt <- j2_rt$pprob
m_rt  <- merge(pp_rt, surv, by = "ID")
r1b   <- mean(m_rt$rr_12[m_rt$class == 1]); r2b <- mean(m_rt$rr_12[m_rt$class == 2])
mauv_rt <- ifelse(r1b > r2b, 1, 2); bon_rt <- 3 - mauv_rt
cat(sprintf("random=~time: MAUVAIS=cl%d (n=%d, R/R12=%.0f%%)\n",
            mauv_rt, sum(m_rt$class == mauv_rt),
            mean(m_rt$rr_12[m_rt$class == mauv_rt]) * 100))

# ── jlcm_ng_comparison.csv : BIC + OR du modele complet random=~time ──────────
cat("\n=== Fit ng=1,3,4 pour comparaison BIC ===\n")

or_fisher <- function(pred, obs) {
  tab <- table(pred, obs)
  if (nrow(tab) < 2 || ncol(tab) < 2) return(Inf)
  fisher.test(tab)$estimate
}

fit_jlcm_rt <- function(ng, B_init) {
  set.seed(42)
  tryCatch(
    Jointlcmm(
      heg ~ time + I(time^2),
      mixture  = if (ng > 1) ~ time + I(time^2) else NULL,
      random   = ~ time,
      subject  = "ID",
      survival = Surv(Tevent, Event) ~ 1,
      hazard   = "Weibull",
      ng       = ng,
      B        = B_init,
      data     = dat_jlcm
    ),
    error = function(e) { cat("ng=", ng, "erreur:", conditionMessage(e), "\n"); NULL }
  )
}

# ng=1 (pas de mixture, pas de B)
cat("ng=1...\n")
j_ng1 <- tryCatch(
  Jointlcmm(heg ~ time + I(time^2), random = ~time, subject = "ID",
             survival = Surv(Tevent, Event) ~ 1, hazard = "Weibull",
             ng = 1, data = dat_jlcm),
  error = function(e) NULL
)

# ng=3 et ng=4 depuis ng=1 comme init
cat("ng=3...\n"); j_ng3 <- fit_jlcm_rt(3, j_ng1)
cat("ng=4...\n"); j_ng4 <- fit_jlcm_rt(4, j_ng1)

# ── Assemblage CSV ─────────────────────────────────────────────────────────────
bic_get <- function(m) if (!is.null(m)) m$BIC else NA

results <- data.frame(
  ng       = 1:4,
  bic      = c(bic_get(j_ng1), j2_rt$BIC, bic_get(j_ng3), bic_get(j_ng4)),
  or_12    = NA_real_,
  or_24    = NA_real_,
  or_12_24 = NA_real_
)

# OR pour chaque ng >= 2
compute_or <- function(jm, ng_val) {
  if (is.null(jm) || ng_val < 2) return(c(NA, NA, NA))
  pp  <- jm$pprob
  m   <- merge(pp, surv, by = "ID")
  rr1 <- mean(m$rr_12[m$class == 1], na.rm = TRUE)
  rr2 <- mean(m$rr_12[m$class == 2], na.rm = TRUE)
  mauv <- ifelse(rr1 > rr2, 1, 2)
  m$pred_mauv <- as.integer(m$class == mauv)
  c(or_fisher(m$pred_mauv, m$rr_12),
    or_fisher(m$pred_mauv, m$rr_24),
    or_fisher(m$pred_mauv, m$rr_12_24))
}

or2 <- compute_or(j2_rt, 2)
or3 <- compute_or(j_ng3, 3)
or4 <- compute_or(j_ng4, 4)

results[results$ng == 2, c("or_12","or_24","or_12_24")] <- or2
results[results$ng == 3, c("or_12","or_24","or_12_24")] <- or3
results[results$ng == 4, c("or_12","or_24","or_12_24")] <- or4

cat("\n=== jlcm_ng_comparison ===\n")
print(results)

write.csv(results, "data/jlcm_ng_comparison.csv", row.names = FALSE)
file.copy("data/jlcm_ng_comparison.csv",
          file.path(network, "data"), overwrite = TRUE)
cat("CSV mis a jour\n")

# ── Log equations pour reference ──────────────────────────────────────────────
fmt_coef <- function(x, first = FALSE) {
  if (first) sprintf("%.3f", x)
  else ifelse(x >= 0, sprintf("+ %.3f", x), sprintf("%.3f", x))
}
make_eq <- function(a0, a1, a2) {
  sprintf("hEG = %s %s\u00B7t %s\u00B7t\u00B2",
          fmt_coef(a0, TRUE), fmt_coef(a1), fmt_coef(a2))
}
b1 <- j2_r1$best
if (mauv_r1 == 1) {
  eq_mauv_r1 <- make_eq(b1[5], b1[7], b1[9])
  eq_bon_r1  <- make_eq(b1[6], b1[8], b1[10])
} else {
  eq_mauv_r1 <- make_eq(b1[6], b1[8], b1[10])
  eq_bon_r1  <- make_eq(b1[5], b1[7], b1[9])
}
b2 <- j2_rt$best
if (mauv_rt == 1) {
  eq_mauv_rt <- make_eq(b2[5], b2[7], b2[9])
  eq_bon_rt  <- make_eq(b2[6], b2[8], b2[10])
} else {
  eq_mauv_rt <- make_eq(b2[6], b2[8], b2[10])
  eq_bon_rt  <- make_eq(b2[5], b2[7], b2[9])
}
cat(sprintf("\nEquations random=~1  : MAUVAIS: %s\n", eq_mauv_r1))
cat(sprintf("                       BON    : %s\n", eq_bon_r1))
cat(sprintf("Equations random=~time: MAUVAIS: %s\n", eq_mauv_rt))
cat(sprintf("                       BON    : %s\n", eq_bon_rt))

# ── Copies reseau ─────────────────────────────────────────────────────────────
tryCatch({
  scripts_dir <- file.path(network, "scripts_figures")
  file.copy("fig_jlcm_all.R", scripts_dir, overwrite = TRUE)
}, error = function(e) NULL)

cat("Done.\n")
