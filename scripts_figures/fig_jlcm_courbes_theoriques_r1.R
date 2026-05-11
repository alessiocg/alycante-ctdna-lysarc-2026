################################################################################
# JLCM — Courbes theoriques : comparaison random=~1 vs random=~time
# Courbes pleines  : random=~1  (modele de reference, avec equations)
# Courbes pointillees : random=~time (comparaison, avec equations)
# Aucun LOO-CV dans cette figure — modeles complets
################################################################################
library(lcmm)
library(ggplot2)

SCRIPT_DIR <- tryCatch(
  dirname(normalizePath(sys.frame(1)$filename, mustWork = FALSE)),
  error = function(e) getwd()
)
setwd(SCRIPT_DIR)

network <- file.path(
  "\\\\hmn-cifs-hnas.wprod.ds.aphp.fr", "shares",
  "IMMUNOLOGIE-BIOLOGIQUE",
  "SECTEUR MALADIES LYMPHOPROLIFERATIVES",
  "D_PROTOCOLES", "DLBCL",
  "protocole ALYCANTE",
  paste0("R", "\u00e9", "union LYSARC 2026"),
  "output"
)

# ── Donnees ───────────────────────────────────────────────────────────────────
dat  <- read.csv("data/data_lcmm_long.csv")
rr   <- read.csv("data/rr_strict_mapping.csv")
# rr_strict_mapping a 'randomisation', pas 'ID' → joindre via dat
id_map <- unique(dat[, c("ID", "randomisation")])
rr2 <- merge(rr[, c("randomisation", "rr_12", "rr_24", "rr_12_24")], id_map, by = "randomisation")
surv <- unique(dat[, c("ID", "efs_event", "efs_time")])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]
surv <- merge(surv, rr2[, c("ID", "rr_12", "rr_24", "rr_12_24")], by = "ID", all.x = TRUE)
surv$rr_12_24 <- as.integer(surv$rr_24 == 1 & surv$rr_12 == 0)

fmt_sign <- function(x) ifelse(x >= 0, sprintf("+ %.3f", x), sprintf("- %.3f", abs(x)))

# ── Modele random=~1 (reference, trait plein) ─────────────────────────────────
j1 <- readRDS("data/jlcm_heg_model.rds")
pp1 <- j1$pprob
m1  <- merge(pp1, surv, by = "ID")
r1_1 <- mean(m1$rr_12[m1$class == 1]); r1_2 <- mean(m1$rr_12[m1$class == 2])
mauv_1 <- ifelse(r1_1 > r1_2, 1, 2); bon_1 <- 3 - mauv_1

n_mauv_1    <- sum(m1$class == mauv_1)
n_bon_1     <- sum(m1$class == bon_1)
rr12_mauv_1 <- round(mean(m1$rr_12[m1$class == mauv_1]) * 100)
rr12_bon_1  <- round(mean(m1$rr_12[m1$class == bon_1])  * 100)
rr24_mauv_1 <- round(mean(m1$rr_24[m1$class == mauv_1]) * 100)
rr24_bon_1  <- round(mean(m1$rr_24[m1$class == bon_1])  * 100)
rr1224_mauv_1 <- round(mean(m1$rr_12_24[m1$class == mauv_1]) * 100)
rr1224_bon_1  <- round(mean(m1$rr_12_24[m1$class == bon_1])  * 100)

cat(sprintf("random=~1 : MAUVAIS=cl%d (n=%d, R/R12=%d%%) | BON=cl%d (n=%d, R/R12=%d%%)\n",
            mauv_1, n_mauv_1, rr12_mauv_1, bon_1, n_bon_1, rr12_bon_1))

# Courbes theoriques random=~1
t_grid <- seq(0, 12.5, by = 0.1)
fake   <- data.frame(ID = rep(9999, length(t_grid)), time = t_grid,
                     heg = 0, Tevent = 40, Event = 0)

py1 <- predictY(j1, newdata = fake, var.time = "time")
y_mauv_1 <- py1$pred[, paste0("Ypred_class", mauv_1)]
y_bon_1  <- py1$pred[, paste0("Ypred_class", bon_1)]

# Equations random=~1
b1 <- j1$best
if (mauv_1 == 1) {
  a0m1 <- b1[5]; a1m1 <- b1[7]; a2m1 <- b1[9]
  a0b1 <- b1[6]; a1b1 <- b1[8]; a2b1 <- b1[10]
} else {
  a0m1 <- b1[6]; a1m1 <- b1[8]; a2m1 <- b1[10]
  a0b1 <- b1[5]; a1b1 <- b1[7]; a2b1 <- b1[9]
}
eq_mauv_1 <- sprintf("MAUVAIS: y = %.3f %s t %s t\u00B2", a0m1, fmt_sign(a1m1), fmt_sign(a2m1))
eq_bon_1  <- sprintf("BON:         y = %.3f %s t %s t\u00B2", a0b1, fmt_sign(a1b1), fmt_sign(a2b1))
cat(sprintf("\nEquations random=~1:\n%s\n%s\n", eq_mauv_1, eq_bon_1))

# ── Modele random=~time (comparaison, pointille) ──────────────────────────────
jrt <- readRDS("data/jlcm_heg_random_time_model.rds")
pprt <- jrt$pprob
mrt  <- merge(pprt, surv, by = "ID")
r1_rt <- mean(mrt$rr_12[mrt$class == 1]); r2_rt <- mean(mrt$rr_12[mrt$class == 2])
mauv_rt <- ifelse(r1_rt > r2_rt, 1, 2); bon_rt <- 3 - mauv_rt

n_mauv_rt    <- sum(mrt$class == mauv_rt)
n_bon_rt     <- sum(mrt$class == bon_rt)
rr12_mauv_rt <- round(mean(mrt$rr_12[mrt$class == mauv_rt]) * 100)
rr12_bon_rt  <- round(mean(mrt$rr_12[mrt$class == bon_rt])  * 100)
rr24_mauv_rt <- round(mean(mrt$rr_24[mrt$class == mauv_rt]) * 100)
rr24_bon_rt  <- round(mean(mrt$rr_24[mrt$class == bon_rt])  * 100)
rr1224_mauv_rt <- round(mean(mrt$rr_12_24[mrt$class == mauv_rt]) * 100)
rr1224_bon_rt  <- round(mean(mrt$rr_12_24[mrt$class == bon_rt])  * 100)

cat(sprintf("random=~time : MAUVAIS=cl%d (n=%d, R/R12=%d%%) | BON=cl%d (n=%d, R/R12=%d%%)\n",
            mauv_rt, n_mauv_rt, rr12_mauv_rt, bon_rt, n_bon_rt, rr12_bon_rt))

# Courbes theoriques random=~time
pyrt <- predictY(jrt, newdata = fake, var.time = "time")
y_mauv_rt <- pyrt$pred[, paste0("Ypred_class", mauv_rt)]
y_bon_rt  <- pyrt$pred[, paste0("Ypred_class", bon_rt)]

# Equations random=~time
brt <- jrt$best
if (mauv_rt == 1) {
  a0mrt <- brt[5]; a1mrt <- brt[7]; a2mrt <- brt[9]
  a0brt <- brt[6]; a1brt <- brt[8]; a2brt <- brt[10]
} else {
  a0mrt <- brt[6]; a1mrt <- brt[8]; a2mrt <- brt[10]
  a0brt <- brt[5]; a1brt <- brt[7]; a2brt <- brt[9]
}
eq_mauv_rt <- sprintf("MAUVAIS: y = %.3f %s t %s t\u00B2", a0mrt, fmt_sign(a1mrt), fmt_sign(a2mrt))
eq_bon_rt  <- sprintf("BON:         y = %.3f %s t %s t\u00B2", a0brt, fmt_sign(a1brt), fmt_sign(a2brt))
cat(sprintf("\nEquations random=~time:\n%s\n%s\n", eq_mauv_rt, eq_bon_rt))

# ── Data frame figure ─────────────────────────────────────────────────────────
df_all <- rbind(
  data.frame(time = t_grid, y = y_mauv_1,  grp = "M1"),
  data.frame(time = t_grid, y = y_bon_1,   grp = "B1"),
  data.frame(time = t_grid, y = y_mauv_rt, grp = "Mt"),
  data.frame(time = t_grid, y = y_bon_rt,  grp = "Bt")
)
df_all$grp <- factor(df_all$grp, levels = c("M1", "B1", "Mt", "Bt"))

# ── Labels et styles ──────────────────────────────────────────────────────────
n_events <- sum(surv$efs_event)

col_mauv <- "#C0392B"
col_bon  <- "#2980B9"

col_grp <- c(M1 = col_mauv, B1 = col_bon, Mt = col_mauv, Bt = col_bon)
lty_grp <- c(M1 = "solid",  B1 = "solid",  Mt = "dotted", Bt = "dotted")
lwd_grp <- c(M1 = 1.6,      B1 = 1.6,      Mt = 1.0,      Bt = 1.0)

fmt_eq <- function(a0, a1, a2)
  sprintf("y = %.3f %s t %s t\u00B2", a0, fmt_sign(a1), fmt_sign(a2))

lab_grp <- c(
  M1 = sprintf("Classe MAUVAIS \u2014 random=~1   (n=%d, R/R 12m=%d%%, R/R 24m=%d%%)    %s",
               n_mauv_1, rr12_mauv_1, rr24_mauv_1, fmt_eq(a0m1, a1m1, a2m1)),
  B1 = sprintf("Classe BON     \u2014 random=~1   (n=%d, R/R 12m=%d%%, R/R 24m=%d%%)    %s",
               n_bon_1,  rr12_bon_1,  rr24_bon_1,  fmt_eq(a0b1, a1b1, a2b1)),
  Mt = sprintf("Classe MAUVAIS \u2014 random=~time (BIC=%.1f)    %s",
               jrt$BIC, fmt_eq(a0mrt, a1mrt, a2mrt)),
  Bt = sprintf("Classe BON     \u2014 random=~time    %s",
               fmt_eq(a0brt, a1brt, a2brt))
)

caption_txt <- sprintf(
  "%d evenements EFS (R/R uniquement) | random=~1 : BIC=%.1f (r\u00e9f\u00e9rence) | random=~time : BIC=%.1f",
  n_events, j1$BIC, jrt$BIC)

# ── Figure ────────────────────────────────────────────────────────────────────
x_breaks <- c(0, 0.46, 1.02, 2.99, 6.03, 9.05, 11.99)
x_labels <- c("J0", "J14", "M1", "M3", "M6", "M9", "M12")

p <- ggplot(df_all, aes(x = time, y = y, color = grp, linetype = grp,
                        linewidth = grp)) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray50",
             linewidth = 0.4) +
  geom_line() +
  # color et linetype sur la meme variable => legende unifiee automatiquement
  scale_color_manual(values = col_grp, labels = lab_grp, name = NULL) +
  scale_linetype_manual(values = lty_grp, labels = lab_grp, name = NULL) +
  scale_discrete_manual(aesthetics = "linewidth", values = lwd_grp, guide = "none") +
  scale_x_continuous(
    breaks = x_breaks, labels = x_labels,
    expand = c(0.02, 0),
    limits = c(0, 13.5)
  ) +
  labs(
    title   = "JLCM 2 classes \u2014 Courbes th\u00e9oriques",
    x       = "Temps depuis J0 CAR-T (mois)",
    y       = "hEG (log\u2081\u2080)",
    caption = caption_txt
  ) +
  theme_bw(base_size = 13) +
  theme(
    legend.position      = c(0.99, 0.99),
    legend.justification = c(1, 1),
    legend.background    = element_blank(),
    legend.key           = element_blank(),
    legend.text          = element_text(size = 10),
    plot.caption         = element_text(hjust = 0.5, size = 9, color = "gray40"),
    plot.title           = element_text(face = "bold", hjust = 0.5),
    panel.grid.minor     = element_blank()
  )

outfile <- "fig_jlcm_courbes_theoriques_r1.png"
ggsave(outfile, p, width = 11, height = 7, dpi = 150)
cat(sprintf("\nFigure : %s\n", outfile))

# ── Copies reseau ─────────────────────────────────────────────────────────────
tryCatch({
  file.copy(outfile, network, overwrite = TRUE)
  cat("Copie reseau OK\n")
}, error = function(e) cat(sprintf("Erreur: %s\n", e$message)))

tryCatch({
  scripts_dir <- file.path(network, "scripts_figures")
  file.copy("fig_jlcm_courbes_theoriques_r1.R", scripts_dir, overwrite = TRUE)
}, error = function(e) NULL)

cat("Done.\n")
