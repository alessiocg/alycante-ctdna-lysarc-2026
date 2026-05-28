################################################################################
# _paths.R - Resolution unifiee des chemins pour le package Blood ALYCANTE.
#
# A sourcer en debut de chaque script R du package :
#     source("_paths.R")
# Ou si execute depuis Rscript :
#     SCRIPT_DIR <- dirname(normalizePath(sub("^--file=", "",
#       grep("^--file=", commandArgs(trailingOnly=FALSE), value=TRUE)[1])))
#     source(file.path(SCRIPT_DIR, "_paths.R"))
#
# Definit : PKG_ROOT, INPUT_DIR, OUTPUT_DIR, TABLES_DIR, FIGURES_DIR, DATA_DIR
#
# Override possible via variables d'environnement :
#     BLOOD_PKG_ROOT   = chemin absolu vers blood_article_package/
#     BLOOD_INPUT_DIR  = chemin absolu vers input/
#     BLOOD_OUTPUT_DIR = chemin absolu vers output/
################################################################################

.get_script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  fa <- grep("^--file=", args, value = TRUE)
  if (length(fa) > 0) {
    return(dirname(normalizePath(sub("^--file=", "", fa[1]), mustWork = FALSE)))
  }
  for (i in rev(seq_along(sys.frames()))) {
    f <- tryCatch(sys.frame(i)$ofile, error = function(e) NULL)
    if (!is.null(f) && nzchar(f)) {
      return(dirname(normalizePath(f, mustWork = FALSE)))
    }
  }
  return(getwd())
}

# 1. PKG_ROOT
PKG_ROOT <- Sys.getenv("BLOOD_PKG_ROOT", unset = NA)
if (is.na(PKG_ROOT) || !nzchar(PKG_ROOT)) {
  .here   <- .get_script_dir()
  .parent <- dirname(.here)
  if (basename(.here) == "data_prep") {
    PKG_ROOT <- dirname(.parent)
  } else {
    PKG_ROOT <- .parent
  }
}

# 2. Sous-repertoires
INPUT_DIR  <- Sys.getenv("BLOOD_INPUT_DIR",
                          unset = file.path(PKG_ROOT, "input"))
OUTPUT_DIR <- Sys.getenv("BLOOD_OUTPUT_DIR",
                          unset = file.path(PKG_ROOT, "output"))
TABLES_DIR  <- file.path(OUTPUT_DIR, "tables")
FIGURES_DIR <- file.path(OUTPUT_DIR, "figures")
DATA_DIR    <- INPUT_DIR  # alias historique
DATA_V2_DIR <- file.path(OUTPUT_DIR, "data_v2")

# 3. Creation defensive
for (.d in c(TABLES_DIR, FIGURES_DIR, DATA_V2_DIR)) {
  if (!dir.exists(.d)) dir.create(.d, recursive = TRUE, showWarnings = FALSE)
}

# 4. Helpers
input_path  <- function(...) file.path(INPUT_DIR,  ...)
output_path <- function(...) file.path(OUTPUT_DIR, ...)
table_path  <- function(name) file.path(TABLES_DIR, name)
figure_path <- function(name) file.path(FIGURES_DIR, name)
