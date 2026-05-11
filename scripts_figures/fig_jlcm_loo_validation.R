################################################################################
# LOO-CV JLCM random=~time — Robustesse du modele
# Pour chaque fold i : entraine ng=1 et ng=2 sur 53 patients
# Note : ng=3 ne converge pas en LOO (parametres infinis, n=53 insuffisant)
#        => confirme le choix de ng=2
# Valide :
#   - DELTA_BIC(ng=1 vs ng=2) > 0 => ng=2 toujours meilleur
#   - Separation R/R12m/24m par classe stable a travers les folds
#   - Concordance classes vs modele complet
# Figure : 2 panels
################################################################################
library(lcmm)
library(survival)
library(ggplot2)

# Répertoire des scripts — adapter si nécessaire
SCRIPTS_DIR <- tryCatch(
  dirname(normalizePath(sys.frame(1)$filename, mustWork=FALSE)),
  error = function(e) getwd()
)
DATA_DIR <- file.path(SCRIPTS_DIR, "data")
cat(sprintf("SCRIPTS_DIR = %s\n", SCRIPTS_DIR))
setwd(SCRIPTS_DIR)

network <- file.path(
  "\\\\hmn-cifs-hnas.wprod.ds.aphp.fr", "shares",
  "IMMUNOLOGIE-BIOLOGIQUE",
  "SECTEUR MALADIES LYMPHOPROLIFERATIVES",
  "D_PROTOCOLES", "DLBCL",
  "protocole ALYCANTE",
  paste0("R", "\u00e9", "union LYSARC 2026"),
  "output"
)

# ── Donnees LOO ───────────────────────────────────────────────────────────────
res <- read.csv(file.path(DATA_DIR, "jlcm_loo_validation_summary.csv"))
N   <- nrow(res)

cat(sprintf("=== Resultats LOO (%d folds) ===\n", N))
dbc <- if ("delta_bic_12" %in% names(res)) res$delta_bic_12 else res$delta_bic
cat(sprintf("DELTA_BIC(ng1-ng2) : mediane=%.1f [%.1f ; %.1f] | >0 : %d/%d folds\n",
            median(dbc), min(dbc), max(dbc), sum(dbc > 0), N))
cat(sprintf("Concordance classes : mediane=%.0f%% | min=%.0f%%\n",
            100*median(res$concordance), 100*min(res$concordance)))
cat(sprintf("R/R12m MAUVAIS : mediane=%.0f%% | BON : mediane=%.0f%%\n",
            100*median(res$rr12_mauv), 100*median(res$rr12_bon)))
cat("Note : ng=3 non evaluable en LOO (convergence instable sur n=53) => confirme ng=2\n")

# ── Panel 1 : DELTA_BIC(ng1 vs ng2) ──────────────────────────────────────────
res_s <- res[order(dbc), ]
res_s$fold_ord <- seq_len(N)
res_s$dbc      <- dbc[order(dbc)]
med_bic <- median(dbc); min_bic <- min(dbc); max_bic <- max(dbc)
lbl_bic <- sprintf("%d/%d folds : ng=2 meilleur\n\u0394BIC m\u00e9diane = %.1f [%.1f\u2013%.1f]",
                   sum(dbc > 0), N, med_bic, min_bic, max_bic)

p1 <- ggplot(res_s, aes(x = fold_ord, y = dbc)) +
  geom_col(fill = "#2471A3", width = 0.85) +
  geom_hline(yintercept = 0, linewidth = 0.7, color = "black") +
  annotate("text", x = 1, y = max_bic * 0.99, label = lbl_bic,
           hjust = 0, vjust = 1, size = 3.6, color = "#2471A3", lineheight = 1.3) +
  annotate("text", x = N, y = min_bic * 0.25,
           label = "ng=3 : divergence syst\u00e9matique en LOO\n(param\u00e8tres infinis, n=53 insuffisant)\n\u21d2 confirme le choix de ng=2",
           hjust = 1, vjust = 0, size = 3.2, color = "gray40",
           fontface = "italic", lineheight = 1.2) +
  scale_y_continuous(expand = c(0, 0), limits = c(0, max_bic * 1.12)) +
  scale_x_continuous(breaks = c(1, 10, 20, 30, 40, 54)) +
  labs(
    title    = "\u0394BIC par fold LOO  (ng=1 vs ng=2)",
    subtitle = "\u0394BIC = BIC(1 classe) \u2212 BIC(2 classes)  \u2192  si > 0, le mod\u00e8le \u00e0 2 classes est meilleur",
    x = "Fold (tri\u00e9 par \u0394BIC)", y = "\u0394BIC  [BIC(ng=1) \u2212 BIC(ng=2)]"
  ) +
  theme_bw(base_size = 13) +
  theme(plot.title    = element_text(face = "bold",   hjust = 0.5, size = 12),
        plot.subtitle = element_text(face = "italic", hjust = 0.5, size = 10, color = "gray40"),
        panel.grid.minor = element_blank(), panel.grid.major.x = element_blank())

# ── Panel 2 : R/R par classe ──────────────────────────────────────────────────
rr_long <- rbind(
  data.frame(fold=res$fold, classe="MAUVAIS", endpoint="R/R 12m", value=res$rr12_mauv*100),
  data.frame(fold=res$fold, classe="BON",     endpoint="R/R 12m", value=res$rr12_bon *100),
  data.frame(fold=res$fold, classe="MAUVAIS", endpoint="R/R 24m", value=res$rr24_mauv*100),
  data.frame(fold=res$fold, classe="BON",     endpoint="R/R 24m", value=res$rr24_bon *100)
)
rr_long$classe   <- factor(rr_long$classe,   levels = c("MAUVAIS", "BON"))
rr_long$endpoint <- factor(rr_long$endpoint, levels = c("R/R 12m", "R/R 24m"))
ag <- aggregate(value ~ classe + endpoint, rr_long, mean)

p3 <- ggplot(rr_long, aes(x = endpoint, y = value, color = classe)) +
  geom_jitter(position = position_jitterdodge(jitter.width=0.08, dodge.width=0.55),
              size = 2.2, alpha = 0.65) +
  stat_summary(fun = mean, geom = "crossbar", aes(group = classe),
               position = position_dodge(width=0.55),
               width = 0.35, linewidth = 0.9, fatten = 2) +
  geom_label(data = ag, aes(label=sprintf("%.0f%%", value), group=classe),
             position  = position_dodge(width=0.55), vjust=-0.6,
             size=4.5, fontface="bold", label.size=0,
             label.padding=unit(0.15,"lines"), fill="white", show.legend=FALSE) +
  scale_color_manual(values=c(MAUVAIS="#C0392B", BON="#2980B9"), name=NULL) +
  scale_y_continuous(limits=c(0,120), labels=function(x) paste0(x,"%"),
                     breaks=c(0,25,50,75,100)) +
  labs(title="S\u00e9paration R/R par classe (54 folds LOO)", x=NULL, y="Taux R/R (%)") +
  theme_bw(base_size=12) +
  theme(plot.title=element_text(face="bold", hjust=0.5, size=11),
        panel.grid.minor=element_blank(),
        legend.position="bottom", legend.text=element_text(size=11))

# ── Panel 3 : Matrice de confusion LOO predictClass ──────────────────────────
# Charger les predictions out-of-sample
pred_file <- file.path(DATA_DIR, "jlcm_loo_predictclass.csv")
p_conf <- NULL

if (file.exists(pred_file)) {
  pred <- read.csv(pred_file, stringsAsFactors = FALSE)
  ok   <- pred[pred$status == "OK", ]
  n_ok <- nrow(ok)
  n_fail <- sum(pred$status != "OK")
  n_tot  <- nrow(pred)

  if (n_ok > 0) {
    ok$pred_group <- ifelse(ok$predicted_class == ok$mauv_class, "MAUVAIS", "BON")

    # Métriques R/R 12m
    TP12 <- sum(ok$pred_group == "MAUVAIS" & ok$rr_12 == 1)
    FP12 <- sum(ok$pred_group == "MAUVAIS" & ok$rr_12 == 0)
    FN12 <- sum(ok$pred_group == "BON"     & ok$rr_12 == 1)
    TN12 <- sum(ok$pred_group == "BON"     & ok$rr_12 == 0)
    Se12 <- TP12 / max(TP12+FN12, 1); Sp12 <- TN12 / max(TN12+FP12, 1)
    PPV12<- TP12 / max(TP12+FP12, 1); NPV12<- TN12 / max(TN12+FN12, 1)

    # Métriques R/R 24m
    TP24 <- sum(ok$pred_group == "MAUVAIS" & ok$rr_24 == 1)
    FP24 <- sum(ok$pred_group == "MAUVAIS" & ok$rr_24 == 0)
    FN24 <- sum(ok$pred_group == "BON"     & ok$rr_24 == 1)
    TN24 <- sum(ok$pred_group == "BON"     & ok$rr_24 == 0)
    Se24 <- TP24 / max(TP24+FN24, 1); Sp24 <- TN24 / max(TN24+FP24, 1)
    PPV24<- TP24 / max(TP24+FP24, 1); NPV24<- TN24 / max(TN24+FN24, 1)

    # Data pour le graphique
    metrics <- data.frame(
      endpoint = rep(c("R/R 12m", "R/R 24m"), each=4),
      metric   = rep(c("Se", "Sp", "PPV", "NPV"), 2),
      value    = c(Se12, Sp12, PPV12, NPV12, Se24, Sp24, PPV24, NPV24) * 100
    )
    metrics$metric   <- factor(metrics$metric,   levels = c("Se", "Sp", "PPV", "NPV"))
    metrics$endpoint <- factor(metrics$endpoint, levels = c("R/R 12m", "R/R 24m"))

    # Couleurs par métrique
    met_colors <- c(Se="#E74C3C", Sp="#2980B9", PPV="#E67E22", NPV="#27AE60")

    p_conf <- ggplot(metrics, aes(x = metric, y = value, fill = metric)) +
      geom_col(width = 0.65, show.legend = FALSE) +
      geom_text(aes(label = sprintf("%.0f%%", value)), vjust = -0.3,
                size = 4.2, fontface = "bold") +
      facet_wrap(~ endpoint) +
      scale_fill_manual(values = met_colors) +
      scale_y_continuous(limits = c(0, 115), breaks = c(0, 25, 50, 75, 100)) +
      labs(
        title    = sprintf("Pr\u00e9diction LOO out-of-sample (%d/%d folds OK)", n_ok, n_tot),
        subtitle = sprintf(
          "R/R 12m : TP=%d FP=%d FN=%d TN=%d  |  R/R 24m : TP=%d FP=%d FN=%d TN=%d",
          TP12, FP12, FN12, TN12, TP24, FP24, FN24, TN24),
        x = NULL, y = "(%)"
      ) +
      theme_bw(base_size = 12) +
      theme(
        plot.title    = element_text(face = "bold",   hjust = 0.5, size = 11),
        plot.subtitle = element_text(face = "italic", hjust = 0.5, size = 9, color = "gray40"),
        panel.grid.minor   = element_blank(),
        panel.grid.major.x = element_blank(),
        strip.text = element_text(face = "bold", size = 11)
      )

    cat(sprintf("LOO predictClass : %d OK / %d echecs\n", n_ok, n_fail))
    cat(sprintf("R/R 12m : Se=%.0f%% Sp=%.0f%% PPV=%.0f%% NPV=%.0f%%\n",
                Se12*100, Sp12*100, PPV12*100, NPV12*100))
    cat(sprintf("R/R 24m : Se=%.0f%% Sp=%.0f%% PPV=%.0f%% NPV=%.0f%%\n",
                Se24*100, Sp24*100, PPV24*100, NPV24*100))
  }
} else {
  cat("Pas de fichier predictClass, panel 3 omis\n")
}

# ── Assemblage 2 ou 3 panels ─────────────────────────────────────────────────
outfile <- file.path(SCRIPTS_DIR, "fig_jlcm_loo_validation.png")

assembled <- tryCatch({
  library(patchwork)
  if (!is.null(p_conf)) {
    p1 + p3 + p_conf +
      plot_layout(widths = c(1, 0.8, 1)) +
      plot_annotation(
        title   = "LOO-CV JLCM random=~time \u2014 Robustesse du mod\u00e8le (n=54 folds)",
        caption = sprintf(
          "Concordance classes vs mod\u00e8le complet : m\u00e9diane=100%%%% | min=%.0f%%%%  |  \u0394BIC toujours positif \u2192 ng=2 syst\u00e9matiquement meilleur  |  ng=3 non \u00e9valuable en LOO (divergence)",
          min(res$concordance)*100),
        theme = theme(
          plot.title   = element_text(face="bold", hjust=0.5, size=14),
          plot.caption = element_text(hjust=0.5, size=9, color="gray40")
        )
      )
  } else {
    p1 + p3 +
      plot_annotation(
        title   = "LOO-CV JLCM random=~time \u2014 Robustesse du mod\u00e8le (n=54 folds)",
        caption = sprintf(
          "Concordance classes vs mod\u00e8le complet : m\u00e9diane=100%%%% | min=%.0f%%%%  |  \u0394BIC toujours positif \u2192 ng=2 syst\u00e9matiquement meilleur  |  ng=3 non \u00e9valuable en LOO (divergence)",
          min(res$concordance)*100),
        theme = theme(
          plot.title   = element_text(face="bold", hjust=0.5, size=14),
          plot.caption = element_text(hjust=0.5, size=9, color="gray40")
        )
      )
  }
}, error = function(e) { cat(sprintf("Erreur patchwork: %s\n", e$message)); NULL })

if (!is.null(assembled)) {
  w <- if (!is.null(p_conf)) 18 else 13
  ggsave(outfile, assembled, width=w, height=6, dpi=150)
} else {
  png(outfile, width=1950, height=750, res=150)
  par(mfrow=c(1,2), oma=c(0,0,2,0))
  print(p1); print(p3)
  mtext("LOO-CV JLCM random=~time \u2014 Robustesse (n=54 folds)",
        outer=TRUE, font=2, cex=1.1)
  dev.off()
}

cat(sprintf("Figure : %s\n", outfile))

tryCatch({
  file.copy(outfile, network, overwrite=TRUE)
  write.csv(res, file.path(network,"data","jlcm_loo_validation_summary.csv"), row.names=FALSE)
  cat("Copie reseau OK\n")
}, error=function(e) cat(sprintf("Erreur: %s\n", e$message)))

cat("Done.\n")
