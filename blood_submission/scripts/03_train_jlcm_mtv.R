################################################################################
# ALYCANTE LYSARC 2026 - JLCM sur MTV log10 (PET-CT longitudinal)
#
# Structure analogue au JLCM ctDNA :
#   Jointlcmm(mtv_log ~ time + I(time^2),
#             mixture  = ~ time + I(time^2),
#             random   = ~ time,
#             survival = Surv(Tevent, Event) ~ 1,
#             hazard   = "Weibull",
#             ng       = 2,
#             seed     = 123)
#
# Cohorte = 57 patients ALYCANTE (intersection ctDNA x PET MTV)
# 132 mesures MTV exploitables (Pre_Treatment + D14 + M1 + M3)
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

suppressPackageStartupMessages({
  library(lcmm)
  library(survival)
})

NET <- normalizePath(file.path(OUTPUT_DIR, ".."), mustWork = FALSE)
DATA_DIR <- file.path(NET, 'output', 'scripts_figures', 'data')
INPUT    <- file.path(DATA_DIR, 'data_lcmm_mtv_long.csv')
MODEL    <- file.path(DATA_DIR, 'jlcm_mtv_model.rds')
MODEL_NG1 <- file.path(DATA_DIR, 'jlcm_mtv_ng1_model.rds')

set.seed(123)

dat <- read.csv(INPUT)
cat(sprintf("Donnees MTV : %d lignes, %d patients, %d events EFS\n",
            nrow(dat), length(unique(dat$ID)),
            length(unique(dat$ID[dat$efs_event==1]))))
cat("Distribution time :\n"); print(round(quantile(dat$time, na.rm=TRUE), 2))

# Variables JLCM
dat$Tevent <- dat$efs_time
dat$Event  <- dat$efs_event
# Filtrer time NA et time <0 (PET_Baseline)
dat <- dat[!is.na(dat$time) & dat$time >= 0 & !is.na(dat$mtv_log), ]
cat(sprintf("\nApres filtrage (time>=0, mtv_log!=NA) : %d lignes, %d patients\n",
            nrow(dat), length(unique(dat$ID))))

# 1. Initialisation ng=1 (random=~time)
cat("\n=== Fit ng=1 (init) seed=123 ===\n")
set.seed(123)
j1 <- Jointlcmm(
  mtv_log ~ time + I(time^2),
  random   = ~ time,
  subject  = "ID",
  survival = Surv(Tevent, Event) ~ 1,
  hazard   = "Weibull",
  ng       = 1,
  data     = dat
)
saveRDS(j1, MODEL_NG1)
cat(sprintf("BIC ng=1 : %.2f\n", j1$BIC))

# 2. ng=2 avec mixture
cat("\n=== Fit ng=2 random=~time seed=123 ===\n")
set.seed(123)
j2 <- Jointlcmm(
  mtv_log ~ time + I(time^2),
  mixture  = ~ time + I(time^2),
  random   = ~ time,
  subject  = "ID",
  survival = Surv(Tevent, Event) ~ 1,
  hazard   = "Weibull",
  ng       = 2,
  B        = j1,
  data     = dat
)
cat(sprintf("\nBIC ng=2 : %.2f\n", j2$BIC))
cat(sprintf("Delta BIC vs ng=1 : %.2f (negatif = ng=2 meilleur)\n", j2$BIC - j1$BIC))
cat("\nDistribution classes:\n"); print(table(j2$pprob$class))

# 3. ng=3 et ng=4 (verification)
cat("\n=== ng=3 et ng=4 (verification BIC) ===\n")
set.seed(123)
j3 <- tryCatch(Jointlcmm(
  mtv_log ~ time + I(time^2),
  mixture  = ~ time + I(time^2),
  random   = ~ time,
  subject  = "ID",
  survival = Surv(Tevent, Event) ~ 1,
  hazard   = "Weibull",
  ng       = 3,
  B        = j1,
  data     = dat
), error=function(e) {cat("ng=3 erreur:", conditionMessage(e),"\n"); NULL})
set.seed(123)
j4 <- tryCatch(Jointlcmm(
  mtv_log ~ time + I(time^2),
  mixture  = ~ time + I(time^2),
  random   = ~ time,
  subject  = "ID",
  survival = Surv(Tevent, Event) ~ 1,
  hazard   = "Weibull",
  ng       = 4,
  B        = j1,
  data     = dat
), error=function(e) NULL)

bic_summary <- data.frame(
  ng = 1:4,
  bic = c(j1$BIC, j2$BIC,
          if (!is.null(j3)) j3$BIC else NA,
          if (!is.null(j4)) j4$BIC else NA),
  n   = c(j1$ns, j2$ns,
          if (!is.null(j3)) j3$ns else NA,
          if (!is.null(j4)) j4$ns else NA)
)
cat("BIC comparison :\n"); print(bic_summary)

# 4. Saver modele ng=2 (modele principal)
saveRDS(j2, MODEL)
cat(sprintf("\nModele sauve : %s\n", MODEL))

# 5. Diagnostic ng=2 : event rate par classe
pp <- j2$pprob
surv_pat <- unique(dat[, c('ID','randomisation','efs_event','efs_time','os_event','os_time')])
m <- merge(pp, surv_pat, by='ID')

event_rate_12m <- function(cl) {
  sub <- m[m$class==cl, ]
  sum(sub$efs_event==1 & sub$efs_time<=12) / nrow(sub)
}
er1 <- event_rate_12m(1); er2 <- event_rate_12m(2)
mauv_cl <- ifelse(er1 > er2, 1, 2)
bon_cl  <- 3 - mauv_cl

cat(sprintf("\nClasse 1: n=%d, event rate 12m = %.1f%%\n", sum(pp$class==1), 100*er1))
cat(sprintf("Classe 2: n=%d, event rate 12m = %.1f%%\n", sum(pp$class==2), 100*er2))
cat(sprintf("=> MAUVAIS = classe %d, BON = classe %d\n", mauv_cl, bon_cl))

# 6. Save BIC comparison
write.csv(bic_summary,
          file.path(DATA_DIR, 'jlcm_mtv_ng_comparison.csv'),
          row.names = FALSE)

# 7. Save trajectoires moyennes par classe (pour figure spaghetti future)
new_data <- data.frame(time = seq(0, 12, by = 0.25))
new_data$ID <- 1
new_data$Tevent <- 12; new_data$Event <- 0
pred <- predictY(j2, newdata=new_data, var.time='time')
class_curves <- data.frame(
  time = new_data$time,
  class1 = pred$pred[, 1],
  class2 = pred$pred[, 2]
)
write.csv(class_curves, file.path(DATA_DIR, 'jlcm_mtv_curves.csv'), row.names = FALSE)

cat("\nDone.\n")
