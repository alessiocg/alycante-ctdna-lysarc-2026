################################################################################
# LOO-CV JLCM random=~time — Prediction out-of-sample
#
# Pour chaque fold i (1..54) :
#   1. Fit JLCM ng=1 (init) puis ng=2 sur 53 patients (random=~time)
#   2. predictClass() sur le patient laissé de côté
#   3. Comparer classe prédite vs vrai statut R/R
#
# Résultat : matrice de confusion, Se, Sp, PPV, NPV
# => ajouté comme 3ème panneau à la figure LOO validation
################################################################################
library(lcmm)
library(survival)
library(ggplot2)

SCRIPT_DIR <- tryCatch(
  dirname(normalizePath(sys.frame(1)$filename, mustWork = FALSE)),
  error = function(e) getwd()
)
setwd(SCRIPT_DIR)

network <- normalizePath(file.path(OUTPUT_DIR, ".."), mustWork = FALSE)  # legacy NAS root,
  "output"
)

# ── Donnees ──────────────────────────────────────────────────────────────────
dat  <- read.csv("data/data_lcmm_long.csv")
rr   <- read.csv("data/rr_strict_mapping.csv")
id_map <- unique(dat[, c("ID", "randomisation")])
rr2 <- merge(rr[, c("randomisation", "rr_12", "rr_24", "rr_12_24")], id_map, by = "randomisation")

surv <- unique(dat[, c("ID", "randomisation", "efs_event", "efs_time")])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
surv <- merge(surv, rr2[, c("ID", "rr_12", "rr_24", "rr_12_24")], by = "ID", all.x = TRUE)

dat_jlcm <- merge(dat, surv[, c("ID", "efs_event", "efs_time")],
                   by = "ID", suffixes = c("", ".s"))
dat_jlcm$Tevent <- dat_jlcm$efs_time.s
dat_jlcm$Event  <- dat_jlcm$efs_event.s

ids <- sort(unique(dat_jlcm$ID))
N   <- length(ids)
cat(sprintf("=== LOO-CV avec predictClass : %d patients ===\n", N))

# ── Cache ────────────────────────────────────────────────────────────────────
cache_file <- "data/jlcm_loo_predictclass.csv"

if (file.exists(cache_file)) {
  cat("Cache trouvé, chargement...\n")
  loo_res <- read.csv(cache_file)
} else {
  loo_res <- data.frame(
    fold           = integer(0),
    ID             = integer(0),
    predicted_class = integer(0),
    p_class1       = numeric(0),
    p_class2       = numeric(0),
    rr_12          = integer(0),
    rr_24          = integer(0),
    status         = character(0),
    stringsAsFactors = FALSE
  )

  for (i in seq_len(N)) {
    pat_id <- ids[i]
    cat(sprintf("  Fold %d/%d (ID=%d) ... ", i, N, pat_id))

    # Train/test split
    dat_train <- dat_jlcm[dat_jlcm$ID != pat_id, ]
    dat_test  <- dat_jlcm[dat_jlcm$ID == pat_id, ]

    tryCatch({
      # Fit ng=1 (init)
      set.seed(123)
      j1 <- Jointlcmm(
        heg ~ time + I(time^2),
        random   = ~ time,
        subject  = "ID",
        survival = Surv(Tevent, Event) ~ 1,
        hazard   = "Weibull",
        ng       = 1,
        data     = dat_train,
        verbose  = FALSE
      )

      # Fit ng=2
      set.seed(123)
      j2 <- Jointlcmm(
        heg ~ time + I(time^2),
        mixture  = ~ time + I(time^2),
        random   = ~ time,
        subject  = "ID",
        survival = Surv(Tevent, Event) ~ 1,
        hazard   = "Weibull",
        ng       = 2,
        B        = j1,
        data     = dat_train,
        verbose  = FALSE
      )

      # Identifier MAUVAIS dans le modèle k
      pp_k   <- j2$pprob
      surv_k <- surv[surv$ID %in% pp_k$ID, ]
      m_k    <- merge(pp_k, surv_k, by = "ID")
      r1k    <- mean(m_k$rr_12[m_k$class == 1], na.rm = TRUE)
      r2k    <- mean(m_k$rr_12[m_k$class == 2], na.rm = TRUE)
      mauv_k <- ifelse(r1k > r2k, 1, 2)

      # predictClass sur le patient exclu
      pred <- predictClass(j2, newdata = dat_test)

      p1 <- pred[1, "probYT1"]
      p2 <- pred[1, "probYT2"]
      pred_cl <- ifelse(p1 > p2, 1, 2)

      # R/R réel du patient
      pat_surv <- surv[surv$ID == pat_id, ]

      loo_res <- rbind(loo_res, data.frame(
        fold           = i,
        ID             = pat_id,
        predicted_class = pred_cl,
        mauv_class     = mauv_k,
        p_class1       = round(p1, 4),
        p_class2       = round(p2, 4),
        rr_12          = pat_surv$rr_12[1],
        rr_24          = pat_surv$rr_24[1],
        status         = "OK",
        stringsAsFactors = FALSE
      ))

      cat(sprintf("OK → cl=%d (p=%.2f/%.2f) | mauv=cl%d | rr12=%d\n",
                  pred_cl, p1, p2, mauv_k, pat_surv$rr_12[1]))

    }, error = function(e) {
      pat_surv <- surv[surv$ID == pat_id, ]
      loo_res <<- rbind(loo_res, data.frame(
        fold           = i,
        ID             = pat_id,
        predicted_class = NA,
        mauv_class     = NA,
        p_class1       = NA,
        p_class2       = NA,
        rr_12          = pat_surv$rr_12[1],
        rr_24          = pat_surv$rr_24[1],
        status         = gsub("\n", " ", as.character(e$message)),
        stringsAsFactors = FALSE
      ))
      cat(sprintf("ERREUR: %s\n", gsub("\n", " ", e$message)))
    })
  }

  dir.create("output/data", showWarnings = FALSE, recursive = TRUE)
  write.csv(loo_res, cache_file, row.names = FALSE)
  cat(sprintf("\nCache sauvegardé: %s\n", cache_file))
}

# ── Résultats ────────────────────────────────────────────────────────────────
ok <- loo_res[loo_res$status == "OK", ]
n_ok <- nrow(ok)
n_fail <- sum(loo_res$status != "OK")
cat(sprintf("\n=== Résultats : %d OK / %d échecs / %d total ===\n", n_ok, n_fail, N))

if (n_ok > 0) {
  # Classifier en BON/MAUVAIS
  ok$pred_group <- ifelse(ok$predicted_class == ok$mauv_class, "MAUVAIS", "BON")
  ok$true_rr12  <- ok$rr_12

  # Matrice de confusion pour R/R 12m
  # MAUVAIS prédit = positif, R/R=1 = vrai positif
  TP <- sum(ok$pred_group == "MAUVAIS" & ok$true_rr12 == 1)
  FP <- sum(ok$pred_group == "MAUVAIS" & ok$true_rr12 == 0)
  FN <- sum(ok$pred_group == "BON"     & ok$true_rr12 == 1)
  TN <- sum(ok$pred_group == "BON"     & ok$true_rr12 == 0)

  Se  <- TP / max(TP + FN, 1)
  Sp  <- TN / max(TN + FP, 1)
  PPV <- TP / max(TP + FP, 1)
  NPV <- TN / max(TN + FN, 1)
  Acc <- (TP + TN) / n_ok

  cat(sprintf("\n--- Matrice de confusion (R/R 12m) ---\n"))
  cat(sprintf("                  Vrai R/R+   Vrai R/R-\n"))
  cat(sprintf("Prédit MAUVAIS      %3d         %3d\n", TP, FP))
  cat(sprintf("Prédit BON          %3d         %3d\n", FN, TN))
  cat(sprintf("\nSensibilité  = %.1f%%\n", Se * 100))
  cat(sprintf("Spécificité  = %.1f%%\n", Sp * 100))
  cat(sprintf("PPV          = %.1f%%\n", PPV * 100))
  cat(sprintf("NPV          = %.1f%%\n", NPV * 100))
  cat(sprintf("Accuracy     = %.1f%%\n", Acc * 100))

  # Idem pour R/R 24m
  TP24 <- sum(ok$pred_group == "MAUVAIS" & ok$rr_24 == 1)
  FP24 <- sum(ok$pred_group == "MAUVAIS" & ok$rr_24 == 0)
  FN24 <- sum(ok$pred_group == "BON"     & ok$rr_24 == 1)
  TN24 <- sum(ok$pred_group == "BON"     & ok$rr_24 == 0)

  Se24  <- TP24 / max(TP24 + FN24, 1)
  Sp24  <- TN24 / max(TN24 + FP24, 1)
  PPV24 <- TP24 / max(TP24 + FP24, 1)
  NPV24 <- TN24 / max(TN24 + FN24, 1)

  cat(sprintf("\n--- R/R 24m ---\n"))
  cat(sprintf("Se=%.1f%% | Sp=%.1f%% | PPV=%.1f%% | NPV=%.1f%%\n",
              Se24*100, Sp24*100, PPV24*100, NPV24*100))

  # ── Sauvegarder les métriques ────────────────────────────────────────────
  metrics <- data.frame(
    endpoint = c("R/R 12m", "R/R 24m"),
    TP = c(TP, TP24), FP = c(FP, FP24), FN = c(FN, FN24), TN = c(TN, TN24),
    Se = c(Se, Se24), Sp = c(Sp, Sp24), PPV = c(PPV, PPV24), NPV = c(NPV, NPV24)
  )
  write.csv(metrics, "data/jlcm_loo_predictclass_metrics.csv", row.names = FALSE)
}

cat("\nDone. Lancer le script de figure ensuite pour intégrer le 3ème panneau.\n")
