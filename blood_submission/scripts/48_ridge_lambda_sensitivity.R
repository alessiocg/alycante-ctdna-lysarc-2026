# =============================================================================
# 48_ridge_lambda_sensitivity.R
# -----------------------------------------------------------------------------
# Reviewer Blood rang A : "Votre HR EFS multivariable etait 17.7 sous ridge
# lambda=0.1. Sensible au choix de lambda ?"
# Strategie :
#   1) Cox ridge avec lambda dans {0.01, 0.05, 0.1, 0.2, 0.5, 1.0}, en
#      univariable (class_jlcm seul) et multivariable (class_jlcm + ipi + mtv_log10)
#   2) Cox Firth via coxphf (penalisation Jeffreys, gere la separation)
#   3) Resume HR, IC 95%, p, C-index dans une supplementary table.
#
# Convention temps : master_dataset.csv est en JOURS (efs_days, os_days).
# On convertit en mois (/30.4375) pour coherence avec la conf rest of paper
# mais l'unite ne change pas les HR (seulement les temps).
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
  library(coxphf)
})

set.seed(123)

NET <- normalizePath(file.path(OUTPUT_DIR, ".."), mustWork = FALSE)  # legacy NAS root, now portable
OUT_DIR <- file.path(NET, 'output/blood_article_package/output/tables')
dir.create(OUT_DIR, recursive=TRUE, showWarnings=FALSE)

# ---- Donnees master_dataset (contient IPI, MTV) ---------------------------
MASTER <- file.path(INPUT_DIR, "master_dataset.csv")
df <- read.csv(MASTER)
df <- df[df$group %in% c('BON','MAUVAIS'), ]
df <- df[!is.na(df$MTV_BL_log10) & !is.na(df$IPI_HIGH), ]
df$class_jlcm <- factor(df$group, levels=c('BON','MAUVAIS'))
df$IPI_HIGH <- as.numeric(df$IPI_HIGH)
df$MTV_BL_log10 <- as.numeric(df$MTV_BL_log10)
df$efs_time <- df$efs_days / 30.4375
df$os_time  <- df$os_days  / 30.4375
cat('=== Cohorte multivariable : n =', nrow(df), ' ===\n')
cat('Distribution JLCM :\n'); print(table(df$class_jlcm))
cat('Events EFS / OS par group :\n')
print(aggregate(cbind(efs_event, os_event) ~ class_jlcm, data=df, FUN=sum))

# ---- Fonctions -------------------------------------------------------------
fit_ridge <- function(formula_, data, lambda, covariate_label, ep_label,
                       set_label) {
  # Ridge cox : on ajoute ridge(x, theta=lambda) directement sur class_jlcm
  # Forme : Surv(...) ~ ridge(class_jlcm, ipi, mtv, theta=lambda)
  rhs <- gsub('~', '~', deparse(formula_[[3]]))
  # Construire la formule penalisee
  vars <- all.vars(formula_)[-(1:2)]  # exclure time, event
  rhs_ridge <- sprintf('ridge(%s, theta=%g)', paste(vars, collapse=','), lambda)
  fm <- as.formula(sprintf('%s ~ %s', deparse(formula_[[2]]), rhs_ridge))
  m <- tryCatch(coxph(fm, data=data),
                error=function(e) { cat('  ERROR ridge:', e$message,'\n'); NULL })
  if (is.null(m)) {
    return(data.frame(method=sprintf('ridge_lambda=%g', lambda), endpoint=ep_label,
                      covariate_set=set_label, covariate=covariate_label,
                      n=nrow(data), hr=NA, hr_lo=NA, hr_hi=NA, p=NA, c_index=NA,
                      stringsAsFactors=FALSE))
  }
  # coxph avec ridge ne fournit pas summary() conventionnel pour les coefs
  # On extrait coef et se via $coefficients et $var
  cf <- m$coefficients
  se <- sqrt(diag(m$var))
  # Trouver l'indice du covariate JLCM (toujours le 1er)
  idx <- 1
  hr   <- exp(cf[idx])
  hrlo <- exp(cf[idx] - 1.96 * se[idx])
  hrhi <- exp(cf[idx] + 1.96 * se[idx])
  # p-value = 2 * pnorm(-|z|)
  z <- cf[idx] / se[idx]
  p <- 2 * pnorm(-abs(z))
  cidx <- tryCatch(concordance(m)$concordance, error=function(e) NA)
  data.frame(method=sprintf('ridge_lambda=%g', lambda), endpoint=ep_label,
             covariate_set=set_label, covariate=covariate_label,
             n=m$n, hr=hr, hr_lo=hrlo, hr_hi=hrhi, p=p, c_index=cidx,
             stringsAsFactors=FALSE)
}

fit_firth <- function(formula_, data, covariate_label, ep_label, set_label) {
  m <- tryCatch(coxphf(formula_, data=data, maxit=200, maxstep=2.5),
                error=function(e) { cat('  ERROR firth:', e$message, '\n'); NULL })
  if (is.null(m)) {
    return(data.frame(method='firth', endpoint=ep_label, covariate_set=set_label,
                      covariate=covariate_label, n=nrow(data), hr=NA, hr_lo=NA,
                      hr_hi=NA, p=NA, c_index=NA, stringsAsFactors=FALSE))
  }
  # coxphf retourne coef nommes (incluant le nom du facteur)
  # Trouver le coef pour class_jlcm (1er coef si univariable, sinon nomme class_jlcmMAUVAIS)
  cf_names <- names(m$coefficients)
  idx <- grep('class_jlcm', cf_names)
  if (length(idx) == 0) idx <- 1
  idx <- idx[1]
  # NOTE coxphf::coxphf : ci.lower / ci.upper sont DEJA sur l'echelle HR (exponentiees)
  hr   <- exp(m$coefficients[idx])
  hrlo <- m$ci.lower[idx]
  hrhi <- m$ci.upper[idx]
  p    <- m$prob[idx]
  # C-index : refit coxph standard sur dataset pour estimer C (coxphf ne fournit pas C-index)
  # Note : c'est une approximation, c'est l'ordre des risques predits qui compte
  m_cox <- tryCatch(coxph(formula_, data=data), error=function(e) NULL)
  cidx <- if (!is.null(m_cox)) tryCatch(concordance(m_cox)$concordance, error=function(e) NA) else NA
  data.frame(method='firth', endpoint=ep_label, covariate_set=set_label,
             covariate=covariate_label, n=nrow(data), hr=hr, hr_lo=hrlo, hr_hi=hrhi,
             p=p, c_index=cidx, stringsAsFactors=FALSE)
}

# ---- Cox lifelines-equivalent : ridge in 'glmnet' style (per-coef normalisation)
# Le manuscrit utilise lifelines.CoxPHFitter(penalizer=lambda) qui penalise
# chaque coefficient via 0.5*lambda * sum(beta^2) avec covariables non
# standardisees. R::survival::ridge() penalise 0.5*theta * t(beta) X (X'X) beta
# La quantite resultante n est pas la meme.
# Pour comparabilite avec le HR=17.7 publie (penalizer=0.1 lifelines multivariable),
# on appelle Python en sous-process et on agrege les resultats.

run_lifelines_ridge <- function(lambdas, ep, set_vars, ep_time, ep_event) {
  py_script <- tempfile(fileext='.py')
  csv_in <- tempfile(fileext='.csv')
  csv_out <- tempfile(fileext='.csv')
  write.csv(df[, c('class_jlcm','IPI_HIGH','MTV_BL_log10',ep_time,ep_event)],
            csv_in, row.names=FALSE)
  py_code <- sprintf("
import pandas as pd, numpy as np
from lifelines import CoxPHFitter
df = pd.read_csv(r'%s')
df = df.dropna()
df['jlcm'] = (df['class_jlcm']=='MAUVAIS').astype(int)
lambdas = %s
sets = {'univariate':['jlcm'], 'multivariate':['jlcm','IPI_HIGH','MTV_BL_log10']}
rows = []
for lam in lambdas:
    for s_name, s_vars in sets.items():
        d = df[s_vars + ['%s','%s']].dropna()
        cph = CoxPHFitter(penalizer=lam)
        cph.fit(d, duration_col='%s', event_col='%s')
        try:
            c = cph.concordance_index_
        except Exception:
            c = float('nan')
        hr = float(np.exp(cph.params_['jlcm']))
        try:
            ci_l = float(np.exp(cph.confidence_intervals_.loc['jlcm'].iloc[0]))
            ci_u = float(np.exp(cph.confidence_intervals_.loc['jlcm'].iloc[1]))
        except Exception:
            ci_l, ci_u = np.nan, np.nan
        p = float(cph.summary.loc['jlcm','p'])
        rows.append({'method':f'lifelines_penalizer={lam}', 'endpoint':'%s',
                     'covariate_set':s_name, 'covariate':'class_jlcm',
                     'n':len(d), 'hr':hr,'hr_lo':ci_l,'hr_hi':ci_u,
                     'p':p,'c_index':c})
pd.DataFrame(rows).to_csv(r'%s', index=False)
", csv_in, paste0('[',paste(lambdas,collapse=','),']'), ep_time, ep_event,
   ep_time, ep_event, ep, csv_out)
  writeLines(py_code, py_script)
  py_exe <- 'C:/Program Files/Python311/python.exe'
  ok <- system2(py_exe, py_script, stdout=TRUE, stderr=TRUE)
  if (!file.exists(csv_out)) {
    cat('  lifelines failed:\n'); print(ok)
    return(NULL)
  }
  read.csv(csv_out, stringsAsFactors=FALSE)
}

# ---- Execution -------------------------------------------------------------
lambdas <- c(0.01, 0.05, 0.1, 0.2, 0.5, 1.0)
all_results <- list()
k <- 1

for (ep in c('EFS','OS')) {
  ep_time <- if (ep=='EFS') 'efs_time' else 'os_time'
  ep_ev   <- if (ep=='EFS') 'efs_event' else 'os_event'
  d <- df[!is.na(df[[ep_time]]) & df[[ep_time]] > 0, ]

  cat(sprintf('\n========== %s (n = %d) ==========\n', ep, nrow(d)))

  # Univariable
  fm_uni  <- as.formula(sprintf('Surv(%s, %s) ~ class_jlcm', ep_time, ep_ev))
  # Multivariable
  fm_multi <- as.formula(sprintf('Surv(%s, %s) ~ class_jlcm + IPI_HIGH + MTV_BL_log10', ep_time, ep_ev))

  # Ridge univariable et multivariable pour chaque lambda
  for (lam in lambdas) {
    cat(sprintf('Ridge lambda=%g univariable...\n', lam))
    all_results[[k]] <- fit_ridge(fm_uni, d, lam, 'class_jlcm', ep, 'univariate'); k <- k + 1
    cat(sprintf('Ridge lambda=%g multivariable...\n', lam))
    all_results[[k]] <- fit_ridge(fm_multi, d, lam, 'class_jlcm', ep, 'multivariate'); k <- k + 1
  }

  # Firth univariable et multivariable
  cat('Firth univariable...\n')
  all_results[[k]] <- fit_firth(fm_uni, d, 'class_jlcm', ep, 'univariate'); k <- k + 1
  cat('Firth multivariable...\n')
  all_results[[k]] <- fit_firth(fm_multi, d, 'class_jlcm', ep, 'multivariate'); k <- k + 1
}

# ---- Run lifelines comparison (matches manuscript HR=17.7 estimator) -------
cat('\n========== Lifelines penalizer (Python) ==========\n')
ll_efs <- run_lifelines_ridge(lambdas, 'EFS', NULL, 'efs_time', 'efs_event')
ll_os  <- run_lifelines_ridge(lambdas, 'OS',  NULL, 'os_time',  'os_event')
if (!is.null(ll_efs)) {
  for (i in 1:nrow(ll_efs)) { all_results[[k]] <- ll_efs[i,]; k <- k + 1 }
}
if (!is.null(ll_os)) {
  for (i in 1:nrow(ll_os)) { all_results[[k]] <- ll_os[i,]; k <- k + 1 }
}

final <- do.call(rbind, all_results)
cat('\n=== TABLE FINAL ===\n')
print(final, digits=3)

out_csv <- file.path(OUT_DIR, 'SuppTable_ridge_lambda_sensitivity.csv')
write.csv(final, out_csv, row.names=FALSE)
cat('\nSauve :', out_csv, '\n')

# ---- Recap pour manuscrit --------------------------------------------------
recap_path <- file.path(OUT_DIR, 'recap_48_ridge_lambda.txt')
sink(recap_path)
cat('=== POINT C - Sensibilite ridge lambda + Firth ===\n\n')
cat(sprintf('Cohorte multivariable (apres dropna IPI + MTV) : n = %d\n', nrow(df)))
cat('-> Ridge avec theta = lambda dans {0.01, 0.05, 0.1, 0.2, 0.5, 1.0}\n')
cat('-> Firth (coxphf) sans tuning parameter\n\n')

for (ep in c('EFS','OS')) {
  for (set in c('univariate','multivariate')) {
    sub <- final[final$endpoint == ep & final$covariate_set == set, ]
    cat(sprintf('--- %s | %s ---\n', ep, set))
    for (i in 1:nrow(sub)) {
      r <- sub[i,]
      if (is.na(r$hr)) {
        cat(sprintf('  %-22s : pas d estimation\n', r$method))
      } else if (is.infinite(r$hr_hi) || r$hr_hi > 1000) {
        cat(sprintf('  %-22s : HR = %.2f (%.2f - inf), p = %.3g, C = %.3f\n',
                    r$method, r$hr, r$hr_lo, r$p, r$c_index))
      } else {
        cat(sprintf('  %-22s : HR = %.2f (%.2f - %.2f), p = %.3g, C = %.3f\n',
                    r$method, r$hr, r$hr_lo, r$hr_hi, r$p, r$c_index))
      }
    }
    cat('\n')
  }
}

# Decision
cat('DECISION (Reviewer Blood) :\n')
cat('  Ridge lambda=0.1 (notre choix initial) bracket entre lambda=0.01 et lambda=1.0\n')
cat('  Firth fournit une alternative robuste sans tuning subjectif.\n')
cat('  Voir SuppTable_ridge_lambda_sensitivity.csv pour analyses completes.\n')
sink()

cat('Recap manuscrit sauve :', recap_path, '\n')
cat('\n=== TERMINE 48 ===\n')
