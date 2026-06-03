#### Apply ALYCANTE JLCM via predictClass to Lea EXTENDED data (all timepoints)
suppressMessages({ library(lcmm); library(survival) })

NAS <- "//Hmn-cifs-hnas.wprod.ds.aphp.fr/shares/IMMUNOLOGIE-BIOLOGIQUE/SECTEUR MALADIES LYMPHOPROLIFERATIVES/D_PROTOCOLES/DLBCL/protocole ALYCANTE/Réunion LYSARC 2026"
MODEL <- file.path(NAS, "output/blood_article_package/input/jlcm_heg_random_time_model.rds")
INP <- file.path(NAS, "output/blood_article_package/output/tables/lea_extended_jlcm_input.csv")
OUT <- file.path(NAS, "output/blood_article_package/output/tables/lea_extended_jlcm_predict.csv")
ALY <- file.path(NAS, "output/blood_article_package/input/data_lcmm_long.csv")

jrt <- readRDS(MODEL)

aly <- read.csv(ALY)
surv <- unique(aly[, c("ID","efs_event","efs_time")])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time>0,]
pp <- jrt$pprob
classes <- sort(unique(pp$class))
rates <- sapply(classes, function(cl) {
  ids <- pp$ID[pp$class==cl]
  s <- surv[surv$ID %in% ids,]
  sum(s$efs_event==1 & s$efs_time<=12) / nrow(s)
})
mauv_cl <- classes[which.max(rates)]
prob_col <- paste0("probYT", mauv_cl)
cat(sprintf("MAUVAIS class = %d (event rate 12m = %.0f%%)\n", mauv_cl, 100*rates[mauv_cl]))

lea <- read.csv(INP)
lea$Tevent <- as.numeric(lea$efs_time); lea$Event <- as.numeric(lea$efs_event)
lea$time <- as.numeric(lea$time); lea$heg <- as.numeric(lea$heg); lea$heg_log <- as.numeric(lea$heg_log)
lea$ID <- as.integer(lea$ID)
cat(sprintf("\nLea extended: %d rows, %d patients\n", nrow(lea), length(unique(lea$ID))))

results <- data.frame()
for (id in sort(unique(lea$ID))) {
  pat_all <- lea[lea$ID==id,]
  nom <- unique(pat_all$randomisation)[1]
  pat_j0j14 <- pat_all[pat_all$timepoint %in% c("J0","J14"),]
  p_m_j14 <- NA; n_tp_j14 <- nrow(pat_j0j14)
  if (n_tp_j14 >= 1) {
    tryCatch({ p_m_j14 <- predictClass(jrt, newdata=pat_j0j14)[1, prob_col] }, error=function(e) {})
  }
  p_m_all <- NA; n_tp_all <- nrow(pat_all)
  tryCatch({ p_m_all <- predictClass(jrt, newdata=pat_all)[1, prob_col] }, error=function(e) {})
  tps <- paste(sort(unique(pat_all$timepoint)), collapse=",")
  results <- rbind(results, data.frame(
    ID=id, nom=nom, n_tp_all=n_tp_all, tps=tps,
    n_tp_j14=n_tp_j14, p_mauvais_j14=round(p_m_j14, 4),
    group_j14=ifelse(is.na(p_m_j14), NA, ifelse(p_m_j14>0.5,"MAUVAIS","BON")),
    p_mauvais_all=round(p_m_all, 4),
    group_all=ifelse(is.na(p_m_all), NA, ifelse(p_m_all>0.5,"MAUVAIS","BON")),
    efs_event=unique(pat_all$efs_event)[1], efs_time=round(unique(pat_all$efs_time)[1], 2)
  ))
}

results$same_class <- with(results, ifelse(is.na(group_j14)|is.na(group_all), NA, group_j14==group_all))
results$change_dp <- with(results, p_mauvais_all - p_mauvais_j14)

cat(sprintf("\n=== Summary (n=%d) ===\n", nrow(results)))
both <- results[!is.na(results$group_j14) & !is.na(results$group_all),]
cat(sprintf("Classifiable J0+J14: %d/%d\n", sum(!is.na(results$group_j14)), nrow(results)))
cat(sprintf("Classifiable all-tp: %d/%d\n", sum(!is.na(results$group_all)), nrow(results)))
cat(sprintf("Both predicted: %d\n", nrow(both)))
cat(sprintf("Class CONCORDANT (J14 vs all): %d/%d (%.0f%%)\n",
            sum(both$same_class, na.rm=TRUE), nrow(both),
            100*mean(both$same_class, na.rm=TRUE)))

disc <- both[!both$same_class & !is.na(both$same_class),]
if (nrow(disc) > 0) {
  cat(sprintf("\n=== %d patients with CLASS CHANGE under extended trajectory ===\n", nrow(disc)))
  print(disc[, c("ID","nom","tps","p_mauvais_j14","group_j14","p_mauvais_all","group_all","efs_event","efs_time")])
}

shift <- both[!is.na(both$change_dp) & abs(both$change_dp) > 0.20,]
if (nrow(shift) > 0) {
  cat(sprintf("\n=== %d patients with |Δp_mauvais|>0.20 ===\n", nrow(shift)))
  print(shift[order(-abs(shift$change_dp)), c("nom","tps","p_mauvais_j14","p_mauvais_all","change_dp","group_j14","group_all","efs_event")])
}

write.csv(results, OUT, row.names=FALSE)
cat(sprintf("\nWritten: %s\n", OUT))
