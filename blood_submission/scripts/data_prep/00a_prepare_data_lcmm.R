################################################################################
# prepare_data_lcmm.R
# Reconstruit data_lcmm_long.csv et rr_strict_mapping.csv
# Référence temporelle : J0 = infusion Axi-cel (CAR-T)
#
# Sources :
#   - Donnees.xlsx        : ctDNA, time_from_J0 exact par patient/visite
#   - ALYCANTE_RNASeq_21OCT2025.xlsx : EFS/OS depuis leucaphérèse + dates leuca/J0
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

library(readxl)
library(dplyr)

setwd(.script_dir)

network <- INPUT_DIR  # portable: was NAS root
    ))
  ))
}

rna$date_leuca <- parse_date_mixte_v(rna[["Start of leukapheresis"]])
rna$date_J0    <- parse_date_mixte_v(rna[["Date of Axi-cel infusion (numeric)"]])

rna$delay_leuca_J0_months <- as.numeric(rna$date_J0 - rna$date_leuca) / 30.44

cat("=== Délais leucaphérèse → J0 ===\n")
cat("Min / Médiane / Max (mois):",
    round(min(rna$delay_leuca_J0_months, na.rm=TRUE), 2), "/",
    round(median(rna$delay_leuca_J0_months, na.rm=TRUE), 2), "/",
    round(max(rna$delay_leuca_J0_months, na.rm=TRUE), 2), "\n")
cat("NA delay:", sum(is.na(rna$delay_leuca_J0_months)), "\n\n")

# ── EFS et OS depuis J0 ───────────────────────────────────────────────────────
rna$efs_time_leuca <- as.numeric(rna[["EFS from leukapheresis (months)"]])
rna$os_time_leuca  <- as.numeric(rna[["OS (months)"]])

# Event EFS : R/R strict (Progression ou Relapse uniquement, pas décès)
efs_cols <- grep("^Event for EFS", names(rna), value = TRUE)
cat("Colonnes EFS event:", paste(efs_cols, collapse=", "), "\n")
# Col ...23 = type d'événement (texte), col ...24 = Yes/No
rna$is_rr   <- grepl("Progression|Relapse", rna[[efs_cols[1]]], ignore.case=TRUE)
rna$has_evt <- tolower(trimws(as.character(rna[[efs_cols[2]]]))) == "yes"
rna$efs_event_rr <- as.integer(rna$has_evt & rna$is_rr)

# OS event
rna$os_event_bin <- as.integer(tolower(trimws(as.character(rna[["OS event"]]))) == "yes")

# Conversion vers J0
rna$efs_time_J0 <- rna$efs_time_leuca - rna$delay_leuca_J0_months
rna$os_time_J0  <- rna$os_time_leuca  - rna$delay_leuca_J0_months

cat("\n=== EFS depuis J0 ===\n")
cat("Min / Médiane / Max (mois):",
    round(min(rna$efs_time_J0, na.rm=TRUE), 2), "/",
    round(median(rna$efs_time_J0, na.rm=TRUE), 2), "/",
    round(max(rna$efs_time_J0, na.rm=TRUE), 2), "\n")
cat("Evts R/R:", sum(rna$efs_event_rr, na.rm=TRUE), "\n\n")

# ── rr_strict_mapping.csv ─────────────────────────────────────────────────────
cat("=== Calcul rr_strict_mapping ===\n")
rr_map <- rna %>%
  select(randomisation, efs_time_J0, efs_event_rr) %>%
  mutate(
    rr_12    = as.integer(efs_event_rr == 1 & efs_time_J0 <= 12),
    rr_24    = as.integer(efs_event_rr == 1 & efs_time_J0 <= 24),
    rr_12_24 = as.integer(rr_24 == 1 & rr_12 == 0)
  ) %>%
  select(randomisation, rr_12, rr_24, rr_12_24)

cat("rr_12:", sum(rr_map$rr_12), "| rr_24:", sum(rr_map$rr_24),
    "| rr_12-24:", sum(rr_map$rr_12_24), "\n\n")

# Comparaison avec ancien rr_strict_mapping
old_rr <- read.csv("rr_strict_mapping.csv")
if ("randomisation" %in% names(old_rr)) {
  old_rr$randomisation <- as.numeric(old_rr$randomisation)
  comp <- merge(rr_map, old_rr[, c("randomisation","rr_12","rr_24")],
                by="randomisation", suffixes=c("_new","_old"))
  cat("Différences rr_12 (new vs old):", sum(comp$rr_12_new != comp$rr_12_old, na.rm=TRUE), "\n")
  cat("Différences rr_24 (new vs old):", sum(comp$rr_24_new != comp$rr_24_old, na.rm=TRUE), "\n\n")
}

# ── Données ctDNA long format pour JLCM (J0 et post-J0 uniquement) ──────────
cat("=== Construction data_lcmm_long ===\n")

# Visites incluses dans le JLCM (J0 et post)
visits_jlcm <- c("D0", "D14", "M1", "M3", "M6", "M9", "M12")
tp_labels   <- c("J0", "J14", "M1", "M3", "M6", "M9", "M12")
tp_map      <- setNames(tp_labels, visits_jlcm)

don_jlcm <- don %>%
  filter(visite %in% visits_jlcm) %>%
  filter(!is.na(time_from_J0)) %>%
  filter(MRD_quali %in% c("POSITIF", "NEGATIF") | is.na(MRD_quali)) %>%
  mutate(
    timepoint = tp_map[visite],
    heg       = case_when(
      MRD_quali == "NEGATIF" & is.na(MRD_quanti_heg) ~ 0,
      MRD_quali == "POSITIF" & is.na(MRD_quanti_heg) ~ 0,  # #NOMBRE! → log(0) → 0
      TRUE ~ MRD_quanti_heg
    ),
    mrd_pos = as.integer(MRD_quali == "POSITIF")
  ) %>%
  filter(!is.na(heg)) %>%
  select(randomisation, time_from_J0, timepoint, heg, mrd_pos)

# Numéro patient séquentiel (ID 1..n)
pat_ids <- data.frame(
  randomisation = sort(unique(don_jlcm$randomisation)),
  ID = seq_len(length(unique(don_jlcm$randomisation)))
)
don_jlcm <- left_join(don_jlcm, pat_ids, by = "randomisation")

# Merger EFS/OS
surv_j0 <- rna %>%
  select(randomisation, efs_time_J0, efs_event_rr, os_time_J0, os_event_bin) %>%
  rename(efs_time = efs_time_J0, efs_event = efs_event_rr,
         os_time = os_time_J0, os_event = os_event_bin)

don_jlcm <- left_join(don_jlcm, surv_j0, by = "randomisation") %>%
  filter(!is.na(efs_time) & efs_time > 0) %>%
  arrange(ID, time_from_J0) %>%
  rename(time = time_from_J0) %>%
  mutate(heg_log = log10(pmax(heg, 1e-6))) %>%  # log10, heg déjà log → heg_log=log10(heg)?
  select(ID, randomisation, time, timepoint, heg, heg_log, mrd_pos,
         efs_time, efs_event, os_time, os_event)

cat("Patients JLCM :", length(unique(don_jlcm$ID)), "\n")
cat("Observations  :", nrow(don_jlcm), "\n")
cat("EFS range     :", round(min(don_jlcm$efs_time),2), "-",
    round(max(don_jlcm$efs_time),2), "mois depuis J0\n")
cat("time range    :", round(min(don_jlcm$time),2), "-",
    round(max(don_jlcm$time),2), "mois depuis J0\n")

cat("\nMédiane time par timepoint :\n")
print(don_jlcm %>% group_by(timepoint) %>%
      summarise(t_med=round(median(time),2), n=n(), .groups="drop") %>%
      arrange(t_med))

# ── Sauvegarde ────────────────────────────────────────────────────────────────
write.csv(don_jlcm, "data_lcmm_long_J0.csv", row.names = FALSE)
cat("\ndata_lcmm_long_J0.csv écrit :", nrow(don_jlcm), "lignes\n")

write.csv(rr_map, "rr_strict_mapping_J0.csv", row.names = FALSE)
cat("rr_strict_mapping_J0.csv écrit :", nrow(rr_map), "lignes\n")

cat("\n=== ATTENTION : vérifier les sorties avant de remplacer les fichiers actuels ===\n")
cat("  data_lcmm_long.csv     (actuel, depuis leuca)\n")
cat("  data_lcmm_long_J0.csv  (nouveau, depuis J0) <- à valider\n")
cat("  rr_strict_mapping.csv     (actuel)\n")
cat("  rr_strict_mapping_J0.csv  (nouveau) <- à valider\n")
