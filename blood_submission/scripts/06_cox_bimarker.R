# Cox bi-marqueur ctDNA vs MTV vs combine + NRI + forest plot

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

library(survival)
library(survminer)
library(ggplot2)

NET <- normalizePath(file.path(OUTPUT_DIR, ".."), mustWork = FALSE)
OUT_DIR <- file.path(NET, 'output/figures/jlcm_pet')
DATA_DIR <- file.path(NET, 'output/scripts_figures/data')
dir.create(OUT_DIR, recursive=TRUE, showWarnings=FALSE)

# Charger predict ctDNA (deja existant : jlcm_predict_j14.csv) et MTV
pred_ctdna <- read.csv(file.path(DATA_DIR, 'jlcm_predict_j14.csv'))
pred_mtv <- read.csv(file.path(DATA_DIR, 'jlcm_mtv_predict_j14.csv'))
cat('ctDNA predict :', nrow(pred_ctdna), '\n')
cat('MTV predict   :', nrow(pred_mtv), '\n')
cat('Cols ctDNA :', paste(colnames(pred_ctdna), collapse=', '), '\n')
cat('Cols MTV   :', paste(colnames(pred_mtv), collapse=', '), '\n')

# Charger donnees survie
long <- read.csv(file.path(DATA_DIR, 'data_lcmm_long.csv'))
surv <- unique(long[, c('ID','randomisation','efs_time','efs_event','os_time','os_event')])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
cat('Survie n =', nrow(surv), '\n')

# Joindre les 3 sources
# pred_ctdna : ID + group (BON/MAUVAIS)
# pred_mtv   : ID ou randomisation + group
# Identifier la cle commune
cat('Echantillon ctDNA :\n'); print(head(pred_ctdna, 3))
cat('Echantillon MTV :\n'); print(head(pred_mtv, 3))

# Standardiser
# Use group column
ctdna <- pred_ctdna[, c('ID','group')]
colnames(ctdna)[2] <- 'class_ctdna'
mtv <- pred_mtv
# Identifier la colonne identifiant et group
if ('ID' %in% colnames(mtv)) {
  mtv_id <- 'ID'
} else if ('randomisation' %in% colnames(mtv)) {
  mtv_id <- 'randomisation'
} else {
  cat('Cherche col identifiant MTV...\n')
  print(colnames(mtv))
  stop('Pas de colonne identifiant trouvee')
}
if ('group' %in% colnames(mtv)) {
  mtv_grp <- 'group'
} else {
  print(colnames(mtv))
  stop('Pas de colonne group MTV')
}
mtv_sub <- data.frame(id_mtv=mtv[[mtv_id]], class_mtv=mtv[[mtv_grp]])

# Merge selon le type d'ID
if (mtv_id == 'ID') {
  dat <- merge(ctdna, mtv_sub, by.x='ID', by.y='id_mtv')
} else {
  # Lookup ID via long
  id_to_rando <- unique(long[, c('ID','randomisation')])
  mtv_sub_join <- merge(id_to_rando, mtv_sub, by.x='randomisation', by.y='id_mtv')
  dat <- merge(ctdna, mtv_sub_join[, c('ID','class_mtv')], by='ID')
}
dat <- merge(dat, surv, by='ID')
dat <- dat[!is.na(dat$class_ctdna) & !is.na(dat$class_mtv) & dat$class_ctdna %in% c('BON','MAUVAIS') & dat$class_mtv %in% c('BON','MAUVAIS'), ]
dat$class_ctdna <- factor(dat$class_ctdna, levels=c('BON','MAUVAIS'))
dat$class_mtv   <- factor(dat$class_mtv,   levels=c('BON','MAUVAIS'))
cat('\n=== Patients avec ctDNA + MTV + survie : n =', nrow(dat), ' ===\n')
print(table(dat$class_ctdna, dat$class_mtv, dnn=c('ctDNA','MTV')))

# === Cox uni et bi-marqueur EFS ===
cat('\n--- Cox EFS ---\n')
cox_c  <- coxph(Surv(efs_time, efs_event) ~ class_ctdna, data=dat)
cox_m  <- coxph(Surv(efs_time, efs_event) ~ class_mtv,   data=dat)
cox_cm <- coxph(Surv(efs_time, efs_event) ~ class_ctdna + class_mtv, data=dat)
print(summary(cox_c)$coefficients);  print(concordance(cox_c)$concordance)
print(summary(cox_m)$coefficients);  print(concordance(cox_m)$concordance)
print(summary(cox_cm)$coefficients); print(concordance(cox_cm)$concordance)
lrt_cm_vs_c <- anova(cox_c, cox_cm)
cat('LRT bi vs ctDNA seul :\n'); print(lrt_cm_vs_c)
lrt_cm_vs_m <- anova(cox_m, cox_cm)
cat('LRT bi vs MTV seul :\n'); print(lrt_cm_vs_m)

# === Cox uni et bi-marqueur OS ===
cat('\n--- Cox OS ---\n')
cox_c_os  <- coxph(Surv(os_time, os_event) ~ class_ctdna, data=dat)
cox_m_os  <- coxph(Surv(os_time, os_event) ~ class_mtv,   data=dat)
cox_cm_os <- coxph(Surv(os_time, os_event) ~ class_ctdna + class_mtv, data=dat)
print(summary(cox_c_os)$coefficients);  print(concordance(cox_c_os)$concordance)
print(summary(cox_m_os)$coefficients);  print(concordance(cox_m_os)$concordance)
print(summary(cox_cm_os)$coefficients); print(concordance(cox_cm_os)$concordance)
lrt_os <- anova(cox_c_os, cox_cm_os)
cat('LRT bi vs ctDNA OS :\n'); print(lrt_os)

# === Sauver metrics complet ===
extract_metrics <- function(cox, label, endpoint) {
  s <- summary(cox)$coefficients
  ci <- summary(cox)$conf.int
  c_idx <- concordance(cox)$concordance
  if (nrow(s) == 1) {
    return(data.frame(model=label, endpoint=endpoint, var=rownames(s),
                      hr=ci[,'exp(coef)'], hr_lo=ci[,'lower .95'], hr_hi=ci[,'upper .95'],
                      p=s[,'Pr(>|z|)'], c_index=c_idx))
  }
  do.call(rbind, lapply(1:nrow(s), function(i) data.frame(
    model=label, endpoint=endpoint, var=rownames(s)[i],
    hr=ci[i,'exp(coef)'], hr_lo=ci[i,'lower .95'], hr_hi=ci[i,'upper .95'],
    p=s[i,'Pr(>|z|)'], c_index=c_idx)))
}

metrics_full <- rbind(
  extract_metrics(cox_c,  'ctDNA seul',         'EFS'),
  extract_metrics(cox_m,  'MTV seul',           'EFS'),
  extract_metrics(cox_cm, 'ctDNA + MTV',        'EFS'),
  extract_metrics(cox_c_os,  'ctDNA seul',      'OS'),
  extract_metrics(cox_m_os,  'MTV seul',        'OS'),
  extract_metrics(cox_cm_os, 'ctDNA + MTV',     'OS')
)
write.csv(metrics_full, file.path(DATA_DIR, 'cox_bimarker_metrics.csv'), row.names=FALSE)
cat('\nMetrics sauvegardes\n')
print(metrics_full)

# === Forest plot des HR ===
metrics_full$label <- paste0(metrics_full$model, ' [', metrics_full$var, ']')
metrics_full$logHR <- log(metrics_full$hr)
metrics_full$logLo <- log(metrics_full$hr_lo)
metrics_full$logHi <- log(metrics_full$hr_hi)
# Filtrer HR aberrants (> 100) pour readability
metrics_full$hr_disp <- pmin(metrics_full$hr, 50)
metrics_full$hr_lo_disp <- pmin(metrics_full$hr_lo, 50)
metrics_full$hr_hi_disp <- pmin(metrics_full$hr_hi, 100)

png(file.path(OUT_DIR, 'fig_forest_bimarker.png'), width=1300, height=750, res=130)
par(mar=c(5,16,3,2))
ep_colors <- c('EFS'='#2F5496','OS'='#cf222e')
y_pos <- 1:nrow(metrics_full)
plot(metrics_full$hr_disp, y_pos, log='x', xlim=c(0.1, 100),
     xlab='Hazard Ratio [IC 95%]', ylab='', yaxt='n', pch=15,
     col=ep_colors[metrics_full$endpoint], cex=1.4,
     main='Cox uni et bi-marqueur : ctDNA et MTV (ALYCANTE)')
abline(v=1, lty=2, col='gray50')
# Add intervals
for (i in y_pos) {
  segments(metrics_full$hr_lo_disp[i], i, metrics_full$hr_hi_disp[i], i,
            col=ep_colors[metrics_full$endpoint[i]], lwd=2)
}
axis(2, at=y_pos, labels=paste0(metrics_full$endpoint, ' | ', metrics_full$label), las=2, cex.axis=0.85)
# Add p-values on right
text(80, y_pos, sprintf('p=%.3g', metrics_full$p), pos=4, cex=0.8, xpd=NA)
legend('topright', legend=c('EFS','OS'), col=ep_colors, pch=15, bty='n', cex=0.9)
dev.off()
cat('Forest plot :', file.path(OUT_DIR, 'fig_forest_bimarker.png'), '\n')

# === NRI a 12 mois (Net Reclassification Improvement) ===
# Comparer modele simple (ctDNA seul) vs combine (ctDNA + MTV)
# Risque predit a 12 mois EFS
horizon <- 12
risk_c  <- 1 - survfit(cox_c,  newdata=dat)$surv[, ]
# Pour Cox, predict type='risk' donne le risque relatif, pas la prob. Calculer survie a 12m :
sf_c  <- survfit(cox_c,  newdata=dat); idx <- which.min(abs(sf_c$time  - horizon))
sf_cm <- survfit(cox_cm, newdata=dat); idx2 <- which.min(abs(sf_cm$time - horizon))
p_c  <- 1 - sf_c$surv[idx, ]
p_cm <- 1 - sf_cm$surv[idx2, ]
# NRI continu
events <- dat$efs_event == 1 & dat$efs_time <= horizon
non_events <- dat$efs_event == 0 & dat$efs_time >= horizon
delta <- p_cm - p_c
nri_e   <- mean(delta[events]    > 0, na.rm=TRUE) - mean(delta[events]    < 0, na.rm=TRUE)
nri_ne  <- mean(delta[non_events] < 0, na.rm=TRUE) - mean(delta[non_events] > 0, na.rm=TRUE)
nri_tot <- nri_e + nri_ne
cat(sprintf('\nNRI 12m (ctDNA+MTV vs ctDNA seul) :\n  NRI events     = %.3f\n  NRI non-events = %.3f\n  NRI total      = %.3f\n', nri_e, nri_ne, nri_tot))
write.csv(data.frame(nri_events=nri_e, nri_nonevents=nri_ne, nri_total=nri_tot, n_events=sum(events), n_nonevents=sum(non_events)),
          file.path(DATA_DIR, 'nri_12m_ctdna_plus_mtv.csv'), row.names=FALSE)

cat('\n=== TERMINE ===\n')
