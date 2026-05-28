# =============================================================================
# 46_cox_continuous_benchmark.R
# -----------------------------------------------------------------------------
# Reviewer Blood rang A : "Prouvez que le JLCM bat des benchmarks triviaux."
# Trois modeles Cox EFS et OS :
#   M_a   : Surv(efs,event) ~ log10_heg_d14         (continu)
#   M_b   : Surv(efs,event) ~ delta_log10           (J14 - baseline, continu)
#   M_jlcm: Surv(efs,event) ~ class_jlcm            (BON/MAUVAIS, factor)
# Pour chaque : HR, IC 95%, p, C-index, AUC time-dependent 12m
# NRI 12m : JLCM vs M_a et JLCM vs M_b (sur risque predit a 12m).
#
# Patients eligibles : 44 patients classifies + baseline (J0) + J14 + survie.
# Convention temps : data_lcmm_long.csv -> time en MOIS, efs_time/os_time en MOIS.
# Convention heg   : heg_log DEJA en log10 (memoire utilisateur), donc on
# extrait log10_heg_d14 et log10_heg_baseline directement de la colonne heg_log.
# =============================================================================


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

suppressPackageStartupMessages({
  library(survival)
  library(timeROC)
})

set.seed(123)

NET <- normalizePath(file.path(OUTPUT_DIR, ".."), mustWork = FALSE)  # legacy NAS root, now portable
INPUT_DIR <- file.path(NET, 'output/blood_article_package/input')
OUT_DIR   <- file.path(NET, 'output/blood_article_package/output/tables')
dir.create(OUT_DIR, recursive=TRUE, showWarnings=FALSE)

# ---- Donnees ---------------------------------------------------------------
long <- read.csv(file.path(INPUT_DIR, 'data_lcmm_long.csv'))
pred <- read.csv(file.path(INPUT_DIR, 'jlcm_predict_j14.csv'))

cat('Long n rows =', nrow(long), ' (n unique IDs =', length(unique(long$ID)), ')\n')
cat('Pred classifies =', sum(pred$group %in% c('BON','MAUVAIS')), '/', nrow(pred), '\n')

# ---- Extraction baseline (J0, time le plus proche de 0) et J14 (time entre
# 0.2 et 0.8 mois, plus proche de 0.46) pour chaque patient ------------------
get_per_pt <- function(d, target_time, lo, hi) {
  out <- data.frame(ID=integer(0), time=numeric(0), heg_log=numeric(0))
  for (pid in unique(d$ID)) {
    sub <- d[d$ID == pid & d$time >= lo & d$time <= hi, ]
    if (nrow(sub) == 0) next
    idx <- which.min(abs(sub$time - target_time))
    out <- rbind(out, data.frame(ID=pid, time=sub$time[idx], heg_log=sub$heg_log[idx]))
  }
  out
}

# Baseline : time entre -0.3 et 0.1 mois (inclut J0 et eventuellement J-5)
baseline <- get_per_pt(long, target_time=0, lo=-0.3, hi=0.1)
colnames(baseline)[2:3] <- c('time_b','log10_heg_baseline')
cat('Baseline trouvee :', nrow(baseline), ' patients\n')

# J14 : entre 0.2 et 0.8 mois (~ 6-24 jours), cible 0.46 mois (14 jours)
d14 <- get_per_pt(long, target_time=0.46, lo=0.2, hi=0.8)
colnames(d14)[2:3] <- c('time_d14','log10_heg_d14')
cat('J14 trouvee     :', nrow(d14), ' patients\n')

# ---- Survie + classe JLCM --------------------------------------------------
surv <- unique(long[, c('ID','efs_time','efs_event','os_time','os_event')])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
cat('Survie n =', nrow(surv), '\n')

pred_class <- pred[pred$group %in% c('BON','MAUVAIS'), c('ID','group')]
colnames(pred_class)[2] <- 'class_jlcm'

# ---- Merge -----------------------------------------------------------------
dat <- merge(baseline, d14, by='ID')
dat <- merge(dat, pred_class, by='ID')
dat <- merge(dat, surv, by='ID')
dat$delta_log10 <- dat$log10_heg_d14 - dat$log10_heg_baseline
dat$class_jlcm <- factor(dat$class_jlcm, levels=c('BON','MAUVAIS'))
cat('\n=== Cohorte finale Cox continu : n =', nrow(dat), ' ===\n')
cat('Distribution JLCM :\n'); print(table(dat$class_jlcm))
cat('Events EFS / OS :\n')
print(aggregate(cbind(efs_event, os_event) ~ class_jlcm, data=dat, FUN=sum))

cat('\nSummary log10_heg_d14   :\n'); print(summary(dat$log10_heg_d14))
cat('Summary delta_log10       :\n'); print(summary(dat$delta_log10))

# ---- Fonctions utilitaires -------------------------------------------------
fit_extract <- function(formula_, data, label_model, label_ep) {
  m <- coxph(formula_, data=data, ties='efron')
  s <- summary(m)
  hr   <- s$conf.int[1, 'exp(coef)']
  hrlo <- s$conf.int[1, 'lower .95']
  hrhi <- s$conf.int[1, 'upper .95']
  p    <- s$coefficients[1, ncol(s$coefficients)]
  cidx <- concordance(m)$concordance
  data.frame(
    model    = label_model,
    endpoint = label_ep,
    n        = m$n,
    hr       = hr,
    hr_lo    = hrlo,
    hr_hi    = hrhi,
    p        = p,
    c_index  = cidx,
    auc_12m  = NA_real_,
    nri_vs_jlcm = NA_real_,
    stringsAsFactors = FALSE
  )
}

# AUC time-dependent a 12 mois via timeROC (covariable continue ou risque predit)
get_auc12 <- function(m, data, ep_time, ep_event) {
  # On utilise le risque predit relatif (lp) pour ranger les patients
  marker <- predict(m, newdata=data, type='lp')
  if (any(!is.finite(marker))) return(NA)
  tr <- tryCatch(
    timeROC(T=data[[ep_time]], delta=data[[ep_event]], marker=marker,
            cause=1, times=12, iid=FALSE),
    error=function(e) NULL
  )
  if (is.null(tr)) return(NA)
  as.numeric(tr$AUC['t=12'])
}

# NRI 12m a la facon cox_bimarker.R
# m_new est le modele JLCM, m_ref est M_a ou M_b
compute_nri_12m <- function(m_new, m_ref, data, ep_time, ep_event, horizon=12) {
  sf_new <- survfit(m_new, newdata=data)
  sf_ref <- survfit(m_ref, newdata=data)
  idx_new <- which.min(abs(sf_new$time - horizon))
  idx_ref <- which.min(abs(sf_ref$time - horizon))
  p_new <- 1 - sf_new$surv[idx_new, ]
  p_ref <- 1 - sf_ref$surv[idx_ref, ]
  events     <- data[[ep_event]] == 1 & data[[ep_time]] <= horizon
  non_events <- data[[ep_event]] == 0 & data[[ep_time]] >= horizon
  delta <- p_new - p_ref
  nri_e  <- mean(delta[events] > 0, na.rm=TRUE)   - mean(delta[events] < 0, na.rm=TRUE)
  nri_ne <- mean(delta[non_events] < 0, na.rm=TRUE) - mean(delta[non_events] > 0, na.rm=TRUE)
  list(
    nri_total = nri_e + nri_ne,
    nri_events = nri_e,
    nri_nonevents = nri_ne,
    n_events = sum(events, na.rm=TRUE),
    n_nonevents = sum(non_events, na.rm=TRUE)
  )
}

# ---- Fit les 6 modeles -----------------------------------------------------
res <- list()

cat('\n--- EFS ---\n')
m_a_efs   <- coxph(Surv(efs_time, efs_event) ~ log10_heg_d14, data=dat)
m_b_efs   <- coxph(Surv(efs_time, efs_event) ~ delta_log10,    data=dat)
m_jlcm_efs <- coxph(Surv(efs_time, efs_event) ~ class_jlcm,    data=dat)
print(summary(m_a_efs)$coefficients); cat('C-index =', concordance(m_a_efs)$concordance, '\n')
print(summary(m_b_efs)$coefficients); cat('C-index =', concordance(m_b_efs)$concordance, '\n')
print(summary(m_jlcm_efs)$coefficients); cat('C-index =', concordance(m_jlcm_efs)$concordance, '\n')

cat('\n--- OS ---\n')
m_a_os   <- coxph(Surv(os_time, os_event) ~ log10_heg_d14, data=dat)
m_b_os   <- coxph(Surv(os_time, os_event) ~ delta_log10,    data=dat)
m_jlcm_os <- coxph(Surv(os_time, os_event) ~ class_jlcm,    data=dat)
print(summary(m_a_os)$coefficients);  cat('C-index =', concordance(m_a_os)$concordance, '\n')
print(summary(m_b_os)$coefficients);  cat('C-index =', concordance(m_b_os)$concordance, '\n')
print(summary(m_jlcm_os)$coefficients); cat('C-index =', concordance(m_jlcm_os)$concordance, '\n')

# ---- Extraire les metriques -----------------------------------------------
rows <- list()
rows[[1]] <- fit_extract(Surv(efs_time, efs_event) ~ log10_heg_d14, dat, 'M_a_log10_heg_d14', 'EFS')
rows[[2]] <- fit_extract(Surv(efs_time, efs_event) ~ delta_log10,    dat, 'M_b_delta_log10',   'EFS')
rows[[3]] <- fit_extract(Surv(efs_time, efs_event) ~ class_jlcm,     dat, 'M_jlcm',            'EFS')
rows[[4]] <- fit_extract(Surv(os_time, os_event)  ~ log10_heg_d14,  dat, 'M_a_log10_heg_d14', 'OS')
rows[[5]] <- fit_extract(Surv(os_time, os_event)  ~ delta_log10,     dat, 'M_b_delta_log10',   'OS')
rows[[6]] <- fit_extract(Surv(os_time, os_event)  ~ class_jlcm,      dat, 'M_jlcm',            'OS')

# AUC 12m
rows[[1]]$auc_12m <- get_auc12(m_a_efs,   dat, 'efs_time', 'efs_event')
rows[[2]]$auc_12m <- get_auc12(m_b_efs,   dat, 'efs_time', 'efs_event')
rows[[3]]$auc_12m <- get_auc12(m_jlcm_efs,dat, 'efs_time', 'efs_event')
rows[[4]]$auc_12m <- get_auc12(m_a_os,    dat, 'os_time',  'os_event')
rows[[5]]$auc_12m <- get_auc12(m_b_os,    dat, 'os_time',  'os_event')
rows[[6]]$auc_12m <- get_auc12(m_jlcm_os, dat, 'os_time',  'os_event')

# NRI : JLCM vs M_a et JLCM vs M_b (12 mois)
cat('\n--- NRI 12m EFS ---\n')
nri_jlcm_vs_a_efs <- compute_nri_12m(m_jlcm_efs, m_a_efs, dat, 'efs_time', 'efs_event', 12)
nri_jlcm_vs_b_efs <- compute_nri_12m(m_jlcm_efs, m_b_efs, dat, 'efs_time', 'efs_event', 12)
cat('JLCM vs M_a EFS : NRI_total =', sprintf('%.3f', nri_jlcm_vs_a_efs$nri_total),
    '  (events=', nri_jlcm_vs_a_efs$n_events, ', non-events=', nri_jlcm_vs_a_efs$n_nonevents,')\n')
cat('JLCM vs M_b EFS : NRI_total =', sprintf('%.3f', nri_jlcm_vs_b_efs$nri_total),
    '  (events=', nri_jlcm_vs_b_efs$n_events, ', non-events=', nri_jlcm_vs_b_efs$n_nonevents,')\n')

cat('\n--- NRI 12m OS ---\n')
nri_jlcm_vs_a_os <- compute_nri_12m(m_jlcm_os, m_a_os, dat, 'os_time', 'os_event', 12)
nri_jlcm_vs_b_os <- compute_nri_12m(m_jlcm_os, m_b_os, dat, 'os_time', 'os_event', 12)
cat('JLCM vs M_a OS  : NRI_total =', sprintf('%.3f', nri_jlcm_vs_a_os$nri_total),
    '  (events=', nri_jlcm_vs_a_os$n_events, ', non-events=', nri_jlcm_vs_a_os$n_nonevents,')\n')
cat('JLCM vs M_b OS  : NRI_total =', sprintf('%.3f', nri_jlcm_vs_b_os$nri_total),
    '  (events=', nri_jlcm_vs_b_os$n_events, ', non-events=', nri_jlcm_vs_b_os$n_nonevents,')\n')

# Reporter le NRI sur la ligne M_a et M_b (sens : "vs JLCM"), pour le JLCM, NRI = NA (reference)
rows[[1]]$nri_vs_jlcm <- nri_jlcm_vs_a_efs$nri_total  # NRI de JLCM par rapport a M_a
rows[[2]]$nri_vs_jlcm <- nri_jlcm_vs_b_efs$nri_total
rows[[4]]$nri_vs_jlcm <- nri_jlcm_vs_a_os$nri_total
rows[[5]]$nri_vs_jlcm <- nri_jlcm_vs_b_os$nri_total

final <- do.call(rbind, rows)
cat('\n=== TABLE FINAL ===\n')
print(final, digits=3)

out_csv <- file.path(OUT_DIR, 'SuppTable_continuous_benchmarks.csv')
write.csv(final, out_csv, row.names=FALSE)
cat('\nSauve :', out_csv, '\n')

# ---- Recap pour manuscrit --------------------------------------------------
recap_path <- file.path(OUT_DIR, 'recap_46_continuous.txt')
sink(recap_path)
cat('=== POINT A - Benchmark vs Cox continu ===\n')
fmt <- function(r) sprintf('HR per unit = %.2f (%.2f-%.2f), p = %.3g, C-index = %.3f, AUC12m = %.3f',
                            r$hr, r$hr_lo, r$hr_hi, r$p, r$c_index, r$auc_12m)
cat('\n--- EFS (n =', nrow(dat), ') ---\n')
cat('M_a (log10 hEG J14)        :', fmt(final[1,]), '\n')
cat('M_b (Delta log10 B -> J14) :', fmt(final[2,]), '\n')
cat('M_jlcm (BON/MAUVAIS)       :', fmt(final[3,]), '\n')
cat('NRI 12m JLCM vs M_a (continu) =', sprintf('%.3f', nri_jlcm_vs_a_efs$nri_total),
    '  (events:', sprintf('%.3f', nri_jlcm_vs_a_efs$nri_events),
    ', non-events:', sprintf('%.3f', nri_jlcm_vs_a_efs$nri_nonevents),')\n')
cat('NRI 12m JLCM vs M_b (delta)   =', sprintf('%.3f', nri_jlcm_vs_b_efs$nri_total),
    '  (events:', sprintf('%.3f', nri_jlcm_vs_b_efs$nri_events),
    ', non-events:', sprintf('%.3f', nri_jlcm_vs_b_efs$nri_nonevents),')\n')

cat('\n--- OS (n =', nrow(dat), ') ---\n')
cat('M_a (log10 hEG J14)        :', fmt(final[4,]), '\n')
cat('M_b (Delta log10 B -> J14) :', fmt(final[5,]), '\n')
cat('M_jlcm (BON/MAUVAIS)       :', fmt(final[6,]), '\n')
cat('NRI 12m JLCM vs M_a (continu) =', sprintf('%.3f', nri_jlcm_vs_a_os$nri_total),
    '  (events:', sprintf('%.3f', nri_jlcm_vs_a_os$nri_events),
    ', non-events:', sprintf('%.3f', nri_jlcm_vs_a_os$nri_nonevents),')\n')
cat('NRI 12m JLCM vs M_b (delta)   =', sprintf('%.3f', nri_jlcm_vs_b_os$nri_total),
    '  (events:', sprintf('%.3f', nri_jlcm_vs_b_os$nri_events),
    ', non-events:', sprintf('%.3f', nri_jlcm_vs_b_os$nri_nonevents),')\n')

# Verdict automatique
verdict <- function(c_jlcm, c_bench, name_bench) {
  diff <- c_jlcm - c_bench
  if (diff > 0.02) return(sprintf('JLCM BAT %s (+%.3f C-index)', name_bench, diff))
  if (diff > -0.02) return(sprintf('JLCM EGALE %s (delta C = %+.3f)', name_bench, diff))
  return(sprintf('JLCM PERD vs %s (-%.3f C-index)', name_bench, abs(diff)))
}
cat('\nVerdict EFS  - JLCM vs M_a :', verdict(final$c_index[3], final$c_index[1], 'M_a'), '\n')
cat('Verdict EFS  - JLCM vs M_b :', verdict(final$c_index[3], final$c_index[2], 'M_b'), '\n')
cat('Verdict OS   - JLCM vs M_a :', verdict(final$c_index[6], final$c_index[4], 'M_a'), '\n')
cat('Verdict OS   - JLCM vs M_b :', verdict(final$c_index[6], final$c_index[5], 'M_b'), '\n')
sink()
cat('Recap manuscrit sauve :', recap_path, '\n')

cat('\n=== TERMINE 46 ===\n')
