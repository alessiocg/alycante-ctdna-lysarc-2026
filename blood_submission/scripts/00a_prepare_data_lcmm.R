################################################################################
# 00a_prepare_data_lcmm.R
# Reconstruit data_lcmm_long.csv et rr_strict_mapping.csv depuis le CRF
# Référence temporelle : J0 = infusion Axi-cel (CAR-T)
#
# Sources :
#   - Donnees.xlsx                          : ctDNA, time_from_J0 exact par patient/visite
#   - ALYCANTE_RNASeq_21OCT2025.xlsx        : EFS/OS depuis leucaphérèse + dates leuca/J0
#
# Définitions :
#   - data_lcmm_long.csv : efs_event = "Yes" à "Event for EFS" (DEATH-ANY-CAUSE +
#                          progression/relapse + salvage), conforme au manuscript Blood §107
#                          (« EFS = time from CAR-T infusion to progression, relapse, salvage
#                          therapy, or death »).
#   - rr_strict_mapping.csv : rr_12, rr_24 utilisent R/R strict (Progression OR Relapse
#                          uniquement, PAS death), pour les métriques Se/Sp/PPV/NPV.
################################################################################

# === Path resolution (portable) ===
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

# ── Lecture Donnees.xlsx ──────────────────────────────────────────────────────
cat("=== Lecture Donnees.xlsx ===\n")
don <- read_excel(file.path(INPUT_DIR, "Donnees.xlsx"), sheet = 1)
don$randomisation  <- as.numeric(don$randomisation)
don$time_from_J0   <- as.numeric(don$time_from_J0)
don$MRD_quanti_heg <- suppressWarnings(as.numeric(don$MRD_quanti_heg))
don$MRD_quali      <- as.character(don$MRD_quali)
cat("Lignes:", nrow(don), "| Patients:", length(unique(don$randomisation)), "\n\n")

# ── Lecture ALYCANTE_RNASeq ───────────────────────────────────────────────────
cat("=== Lecture ALYCANTE_RNASeq_21OCT2025.xlsx ===\n")
rna <- read_excel(file.path(INPUT_DIR, "ALYCANTE_RNASeq_21OCT2025.xlsx"), sheet = 1)
names(rna)[names(rna) == "Subject Identifier for the Study"] <- "randomisation"
rna$randomisation <- as.numeric(rna$randomisation)
cat("Patients:", nrow(rna), "\n\n")

# ── Dates leuca et J0 depuis ALYCANTE_RNASeq ─────────────────────────────────
# "Start of leukapheresis" : texte dd/mm/YYYY
# "Date of Axi-cel infusion (numeric)" : numéro série Excel OU texte
parse_date_mixte_v <- function(x) {
  x_chr <- trimws(as.character(x))
  x_num <- suppressWarnings(as.numeric(gsub(",", ".", x_chr)))
  as.Date(ifelse(
    !is.na(x_num),
    as.character(as.Date(floor(x_num), origin = "1899-12-30")),
    as.character(suppressWarnings(
      coalesce(
        as.Date(x_chr, format = "%d/%m/%Y"),
        as.Date(x_chr, format = "%Y-%m-%d")
      )
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

# Définition EFS event = R/R lymphome strict :
#   Event for EFS == "Progression/Relapse" exactement (match exact, PAS regex "Progression|Relapse"
#   qui matche aussi "Death without progression"). Ce sont les events lymphome-spécifiques que
#   ctDNA est censé prédire. Les "Death without progression" (toxicité, concurrent illness, autre)
#   sont censurés à la date de décès.
#
# IMPORTANT : Le regex grepl("Progression|Relapse") du script historique avait un bug —
# il matchait aussi "Death without progression" parce que la phrase contient le mot
# "progression". Corrigé en match exact ci-dessous.
efs_cols <- grep("^Event for EFS", names(rna), value = TRUE)
cat("Colonnes EFS event:", paste(efs_cols, collapse=", "), "\n")
# Col ...23 = type d'événement (texte), col ...24 = Yes/No
rna$evt_type <- trimws(as.character(rna[[efs_cols[1]]]))
rna$has_evt  <- tolower(trimws(as.character(rna[[efs_cols[2]]]))) == "yes"
# Match exact : "Progression/Relapse" seulement (R/R lymphome strict)
rna$is_rr <- tolower(rna$evt_type) == "progression/relapse"
rna$efs_event_rr <- as.integer(rna$has_evt & rna$is_rr)        # R/R lymphome strict

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
cat("Evts R/R lymphome strict :", sum(rna$efs_event_rr, na.rm=TRUE), "\n\n")

# ── rr_strict_mapping.csv (utilise R/R strict) ──────────────────────────────
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

# ── Données ctDNA long format pour JLCM (J0 et post-J0 uniquement) ──────────
cat("=== Construction data_lcmm_long ===\n")

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

# Merger EFS broad (death-any-cause) + OS
surv_j0 <- rna %>%
  select(randomisation, efs_time_J0, efs_event_rr, os_time_J0, os_event_bin) %>%
  rename(efs_time = efs_time_J0, efs_event = efs_event_rr,
         os_time = os_time_J0, os_event = os_event_bin)

don_jlcm <- left_join(don_jlcm, surv_j0, by = "randomisation") %>%
  filter(!is.na(efs_time) & efs_time > 0) %>%
  arrange(ID, time_from_J0) %>%
  rename(time = time_from_J0) %>%
  mutate(heg_log = log10(pmax(heg, 1e-6))) %>%
  select(ID, randomisation, time, timepoint, heg, heg_log, mrd_pos,
         efs_time, efs_event, os_time, os_event)

cat("Patients JLCM :", length(unique(don_jlcm$ID)), "\n")
cat("Observations  :", nrow(don_jlcm), "\n")
cat("EFS events (broad def, patient-level):",
    sum(unique(don_jlcm[c("ID","efs_event")])$efs_event), "\n")
cat("EFS range     :", round(min(don_jlcm$efs_time),2), "-",
    round(max(don_jlcm$efs_time),2), "mois depuis J0\n")
cat("time range    :", round(min(don_jlcm$time),2), "-",
    round(max(don_jlcm$time),2), "mois depuis J0\n")

cat("\nMédiane time par timepoint :\n")
print(don_jlcm %>% group_by(timepoint) %>%
      summarise(t_med=round(median(time),2), n=n(), .groups="drop") %>%
      arrange(t_med))

# ── Sauvegarde ────────────────────────────────────────────────────────────────
# Write directly to INPUT_DIR (replace existing). Backup is made before overwrite.
out_long <- file.path(INPUT_DIR, "data_lcmm_long.csv")
out_rr   <- file.path(INPUT_DIR, "rr_strict_mapping.csv")
backup_long <- file.path(INPUT_DIR, "data_lcmm_long.csv.bak_pre_efs_broad")
backup_rr   <- file.path(INPUT_DIR, "rr_strict_mapping.csv.bak_pre_efs_broad")

if (file.exists(out_long) && !file.exists(backup_long)) {
  file.copy(out_long, backup_long)
  cat("Backup créé:", backup_long, "\n")
}
if (file.exists(out_rr) && !file.exists(backup_rr)) {
  file.copy(out_rr, backup_rr)
  cat("Backup créé:", backup_rr, "\n")
}

write.csv(don_jlcm, out_long, row.names = FALSE)
cat("\nÉcrit:", out_long, "(", nrow(don_jlcm), "lignes)\n")

write.csv(rr_map, out_rr, row.names = FALSE)
cat("Écrit:", out_rr, "(", nrow(rr_map), "lignes)\n")

cat("\n=== DONE ===\n")
cat("Convention EFS dans data_lcmm_long.csv : broad (toute cause, conforme manuscript Blood §107).\n")
cat("Convention R/R dans rr_strict_mapping.csv : strict (Progression OR Relapse, sans death).\n")
