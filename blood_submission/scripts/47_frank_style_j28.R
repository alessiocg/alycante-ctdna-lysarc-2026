# =============================================================================
# 47_frank_style_j28.R
# -----------------------------------------------------------------------------
# Reviewer Blood rang A : "Frank et al (Blood 2022) ont montre que la simple
# detectabilite de ctDNA a J28 separe les patients. Votre JLCM J14 fait-il mieux?"
# Strategie :
#   1) Pour chaque patient avec une mesure ctDNA dans la fenetre J21-J35
#      (0.69-1.15 mois = ~ timepoint M1 dans nos donnees), on definit
#      ctdna_d28_detectable = (heg > seuil).
#   2) Deux seuils testes pour robustesse :
#      a) heg > 0 strict (toute detection > LOQ assay)
#      b) heg > 0.5 hEG (= log10 > -0.301, seuil routine)
#   3) Cox EFS et OS ~ ctdna_d28_detectable (factor).
#   4) Comparer C-index, HR vs JLCM J14 (Analyse 1).
# Output : SuppTable_frank_style_j28.csv + recap.
#
# Convention temps : data_lcmm_long.csv en MOIS.
# Convention heg   : heg brut (hEG/mL non transforme) ; heg_log = log10(heg)
#                    avec heg=0 -> heg_log = -6.0 (artefact, donc on utilise heg>0).
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
})

set.seed(123)

NET <- normalizePath(file.path(OUTPUT_DIR, ".."), mustWork = FALSE)  # legacy NAS root, now portable
INPUT_DIR <- file.path(NET, 'output/blood_article_package/input')
OUT_DIR   <- file.path(NET, 'output/blood_article_package/output/tables')
dir.create(OUT_DIR, recursive=TRUE, showWarnings=FALSE)

# ---- Donnees ---------------------------------------------------------------
long <- read.csv(file.path(INPUT_DIR, 'data_lcmm_long.csv'))
pred <- read.csv(file.path(INPUT_DIR, 'jlcm_predict_j14.csv'))

# ---- Extraction J28 (fenetre J21-J35 = 0.69-1.15 mois, cible 0.92 ~ 28 jours)
# Note : dans nos donnees timepoint == 'M1' couvre [0.79, 1.64] mois.
# Pour rester strict avec J21-J35, on utilise lo=0.69 et hi=1.15.
get_per_pt <- function(d, target_time, lo, hi) {
  out <- data.frame(ID=integer(0), time=numeric(0), heg=numeric(0), heg_log=numeric(0))
  for (pid in unique(d$ID)) {
    sub <- d[d$ID == pid & d$time >= lo & d$time <= hi, ]
    if (nrow(sub) == 0) next
    idx <- which.min(abs(sub$time - target_time))
    out <- rbind(out, data.frame(ID=pid, time=sub$time[idx],
                                  heg=sub$heg[idx], heg_log=sub$heg_log[idx]))
  }
  out
}

d28 <- get_per_pt(long, target_time=0.92, lo=0.69, hi=1.15)
cat('Patients avec mesure J21-J35 :', nrow(d28), '\n')
cat('Distribution heg J28 :\n'); print(summary(d28$heg))

# ---- Survie + classe JLCM (pour comparaison) -------------------------------
surv <- unique(long[, c('ID','efs_time','efs_event','os_time','os_event')])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]

pred_class <- pred[pred$group %in% c('BON','MAUVAIS'), c('ID','group')]
colnames(pred_class)[2] <- 'class_jlcm'

# ---- Datasets pour analyses --------------------------------------------------
# (a) Cohorte ctDNA J28 : tous les patients avec une mesure J21-J35 ET survie
dat_frank <- merge(d28, surv, by='ID')
dat_frank$ctdna_d28_strict     <- factor(ifelse(dat_frank$heg > 0,    'POSITIVE', 'NEGATIVE'),
                                          levels=c('NEGATIVE','POSITIVE'))
dat_frank$ctdna_d28_routine    <- factor(ifelse(dat_frank$heg > 0.5,  'POSITIVE', 'NEGATIVE'),
                                          levels=c('NEGATIVE','POSITIVE'))
cat('\n=== Cohorte Frank-style : n =', nrow(dat_frank), ' ===\n')
cat('Strict (heg > 0)         :\n'); print(table(dat_frank$ctdna_d28_strict))
cat('Routine (heg > 0.5)      :\n'); print(table(dat_frank$ctdna_d28_routine))

# (b) Cohorte JLCM J14 (pour comparaison head-to-head, meme effectif)
dat_jlcm <- merge(pred_class, surv, by='ID')
dat_jlcm$class_jlcm <- factor(dat_jlcm$class_jlcm, levels=c('BON','MAUVAIS'))
cat('\nCohorte JLCM J14 (full) : n =', nrow(dat_jlcm), '\n')

# (c) Cohorte intersection : patients avec J28 ET JLCM J14
dat_both <- merge(d28[,c('ID','heg','heg_log','time')], pred_class, by='ID')
dat_both <- merge(dat_both, surv, by='ID')
dat_both$ctdna_d28_strict     <- factor(ifelse(dat_both$heg > 0,    'POSITIVE', 'NEGATIVE'),
                                         levels=c('NEGATIVE','POSITIVE'))
dat_both$ctdna_d28_routine    <- factor(ifelse(dat_both$heg > 0.5,  'POSITIVE', 'NEGATIVE'),
                                         levels=c('NEGATIVE','POSITIVE'))
dat_both$class_jlcm <- factor(dat_both$class_jlcm, levels=c('BON','MAUVAIS'))
cat('\nCohorte intersection (J28 + JLCM J14) : n =', nrow(dat_both), '\n')

# ---- Fonction Fit & extract -------------------------------------------------
fit_extract <- function(formula_, data, label_model, label_ep) {
  m <- coxph(formula_, data=data, ties='efron')
  s <- summary(m)
  hr   <- s$conf.int[1, 'exp(coef)']
  hrlo <- s$conf.int[1, 'lower .95']
  hrhi <- s$conf.int[1, 'upper .95']
  p    <- s$coefficients[1, ncol(s$coefficients)]
  cidx <- concordance(m)$concordance
  # Compte des positives
  rhs_term <- all.vars(formula_)[3]  # first covariate
  n_pos <- if (rhs_term %in% colnames(data) && is.factor(data[[rhs_term]])) {
    sum(data[[rhs_term]] == levels(data[[rhs_term]])[2], na.rm=TRUE)
  } else NA
  data.frame(
    model       = label_model,
    endpoint    = label_ep,
    n_d28       = m$n,
    n_detectable= n_pos,
    hr          = hr,
    hr_lo       = hrlo,
    hr_hi       = hrhi,
    p           = p,
    c_index     = cidx,
    stringsAsFactors = FALSE
  )
}

# ---- Fit toutes les variantes -----------------------------------------------
rows <- list()

# (a) Frank-style sur dat_frank (toute la cohorte avec J28, sans pre-filtrer par JLCM)
rows[[1]] <- fit_extract(Surv(efs_time, efs_event) ~ ctdna_d28_strict,  dat_frank, 'Frank_strict_heg>0',     'EFS')
rows[[2]] <- fit_extract(Surv(efs_time, efs_event) ~ ctdna_d28_routine, dat_frank, 'Frank_routine_heg>0.5',  'EFS')
rows[[3]] <- fit_extract(Surv(os_time,  os_event)  ~ ctdna_d28_strict,  dat_frank, 'Frank_strict_heg>0',     'OS')
rows[[4]] <- fit_extract(Surv(os_time,  os_event)  ~ ctdna_d28_routine, dat_frank, 'Frank_routine_heg>0.5',  'OS')

# (b) JLCM J14 cohorte full (n=44)
rows[[5]] <- fit_extract(Surv(efs_time, efs_event) ~ class_jlcm, dat_jlcm, 'JLCM_J14_full',  'EFS')
rows[[6]] <- fit_extract(Surv(os_time,  os_event)  ~ class_jlcm, dat_jlcm, 'JLCM_J14_full',  'OS')

# (c) Comparaison sur la cohorte intersection (Frank-style ET JLCM)
rows[[7]] <- fit_extract(Surv(efs_time, efs_event) ~ ctdna_d28_strict,  dat_both, 'Frank_strict_intersect',  'EFS')
rows[[8]] <- fit_extract(Surv(efs_time, efs_event) ~ ctdna_d28_routine, dat_both, 'Frank_routine_intersect', 'EFS')
rows[[9]] <- fit_extract(Surv(efs_time, efs_event) ~ class_jlcm,        dat_both, 'JLCM_J14_intersect',      'EFS')
rows[[10]]<- fit_extract(Surv(os_time,  os_event)  ~ ctdna_d28_strict,  dat_both, 'Frank_strict_intersect',  'OS')
rows[[11]]<- fit_extract(Surv(os_time,  os_event)  ~ ctdna_d28_routine, dat_both, 'Frank_routine_intersect', 'OS')
rows[[12]]<- fit_extract(Surv(os_time,  os_event)  ~ class_jlcm,        dat_both, 'JLCM_J14_intersect',      'OS')

final <- do.call(rbind, rows)
cat('\n=== TABLE FINAL ===\n')
print(final, digits=3)

out_csv <- file.path(OUT_DIR, 'SuppTable_frank_style_j28.csv')
write.csv(final, out_csv, row.names=FALSE)
cat('\nSauve :', out_csv, '\n')

# ---- Recap pour manuscrit --------------------------------------------------
recap_path <- file.path(OUT_DIR, 'recap_47_frank_style.txt')
sink(recap_path)
cat('=== POINT B - Frank-style J28 ===\n\n')

n_d28 <- nrow(dat_frank)
n_pos_strict  <- sum(dat_frank$ctdna_d28_strict  == 'POSITIVE')
n_pos_routine <- sum(dat_frank$ctdna_d28_routine == 'POSITIVE')

cat(sprintf('Patients avec mesure ctDNA J21-J35 (fenetre J28 +/- 7) : n = %d\n', n_d28))
cat(sprintf('  Detectable strict (heg > 0)       : %d / %d (%.1f%%)\n',
            n_pos_strict, n_d28, 100*n_pos_strict/n_d28))
cat(sprintf('  Detectable routine (heg > 0.5)    : %d / %d (%.1f%%)\n',
            n_pos_routine, n_d28, 100*n_pos_routine/n_d28))

cat('\n--- Cox EFS sur cohorte J28 (n =', n_d28, ') ---\n')
fmt <- function(r) sprintf('HR = %.2f (%.2f-%.2f), p = %.3g, C-index = %.3f',
                            r$hr, r$hr_lo, r$hr_hi, r$p, r$c_index)
cat('Frank strict (heg > 0)    :', fmt(final[1,]), '\n')
cat('Frank routine (heg > 0.5) :', fmt(final[2,]), '\n')

cat('\n--- Cox OS sur cohorte J28 (n =', n_d28, ') ---\n')
cat('Frank strict (heg > 0)    :', fmt(final[3,]), '\n')
cat('Frank routine (heg > 0.5) :', fmt(final[4,]), '\n')

cat('\n--- JLCM J14 sur cohorte full (n =', dat_jlcm |> nrow(), ') ---\n')
cat('JLCM EFS :', fmt(final[5,]), '\n')
cat('JLCM OS  :', fmt(final[6,]), '\n')

cat('\n--- Comparaison head-to-head sur cohorte INTERSECTION (n =', nrow(dat_both), ') ---\n')
cat('-- EFS --\n')
cat('Frank strict  :', fmt(final[7,]), '\n')
cat('Frank routine :', fmt(final[8,]), '\n')
cat('JLCM J14      :', fmt(final[9,]), '\n')
cat('-- OS  --\n')
cat('Frank strict  :', fmt(final[10,]), '\n')
cat('Frank routine :', fmt(final[11,]), '\n')
cat('JLCM J14      :', fmt(final[12,]), '\n')

cat('\nVERDICT :\n')
delta_efs_strict  <- final$c_index[9] - final$c_index[7]
delta_efs_routine <- final$c_index[9] - final$c_index[8]
delta_os_strict   <- final$c_index[12] - final$c_index[10]
delta_os_routine  <- final$c_index[12] - final$c_index[11]
cat(sprintf('JLCM J14 vs Frank strict  EFS  : delta C-index = %+.3f  (J14 gagne %+.0f jours)\n',
            delta_efs_strict, 14))
cat(sprintf('JLCM J14 vs Frank routine EFS  : delta C-index = %+.3f\n', delta_efs_routine))
cat(sprintf('JLCM J14 vs Frank strict  OS   : delta C-index = %+.3f\n', delta_os_strict))
cat(sprintf('JLCM J14 vs Frank routine OS   : delta C-index = %+.3f\n', delta_os_routine))
sink()
cat('Recap manuscrit sauve :', recap_path, '\n')

cat('\n=== TERMINE 47 ===\n')
