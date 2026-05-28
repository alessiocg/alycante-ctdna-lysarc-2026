library(lcmm)
library(survival)

SCRIPT_DIR <- tryCatch(
  dirname(normalizePath(sys.frame(1)$filename, mustWork = FALSE)),
  error = function(e) getwd()
)
setwd(SCRIPT_DIR)

dat <- read.csv("data/data_lcmm_long.csv")
surv <- unique(dat[, c("ID", "randomisation", "efs_event", "efs_time")])
surv <- surv[!is.na(surv$efs_time) & surv$efs_time > 0, ]

rr <- read.csv("data/rr_strict_mapping.csv")
id_map <- unique(dat[, c("ID", "randomisation")])
rr2 <- merge(rr[, c("randomisation", "rr_12")], id_map, by = "randomisation")
surv <- merge(surv, rr2, by = "ID")

dat_jlcm <- merge(dat, surv[, c("ID", "efs_event", "efs_time")], by = "ID", suffixes = c("", ".s"))
dat_jlcm$Tevent <- dat_jlcm$efs_time.s
dat_jlcm$Event <- dat_jlcm$efs_event.s

jrt <- readRDS("data/jlcm_heg_random_time_model.rds")
pp <- jrt$pprob
r1 <- mean(surv$rr_12[surv$ID %in% pp$ID[pp$class == 1]], na.rm = TRUE)
r2 <- mean(surv$rr_12[surv$ID %in% pp$ID[pp$class == 2]], na.rm = TRUE)
mauv_cl <- ifelse(r1 > r2, 1, 2)
prob_col <- paste0("probYT", mauv_cl)

ids <- sort(unique(dat_jlcm$ID))
results <- data.frame(ID = integer(), randomisation = character(),
                      p_mauvais = numeric(), group = character(),
                      stringsAsFactors = FALSE)

for (id in ids) {
  pat <- dat_jlcm[dat_jlcm$ID == id & dat_jlcm$time <= 0.46, ]
  rando_match <- unique(dat$randomisation[dat$ID == id])
  rando <- if (length(rando_match) > 0) rando_match[1] else NA
  if (nrow(pat) == 0) {
    results <- rbind(results, data.frame(ID = id, randomisation = rando,
                                         p_mauvais = NA, group = NA))
    next
  }
  tryCatch({
    pred <- predictClass(jrt, newdata = pat)
    p_m <- pred[1, prob_col]
    grp <- ifelse(p_m > 0.5, "MAUVAIS", "BON")
    results <- rbind(results, data.frame(ID = id, randomisation = rando,
                                         p_mauvais = round(p_m, 4), group = grp))
  }, error = function(e) {
    results <<- rbind(results, data.frame(ID = id, randomisation = rando,
                                          p_mauvais = NA, group = NA))
  })
}

write.csv(results, "data/jlcm_predict_j14.csv", row.names = FALSE)
cat(sprintf("OK: %d/%d classified | MAUVAIS=%d BON=%d NA=%d\n",
            sum(!is.na(results$group)), nrow(results),
            sum(results$group == "MAUVAIS", na.rm = TRUE),
            sum(results$group == "BON", na.rm = TRUE),
            sum(is.na(results$group))))
