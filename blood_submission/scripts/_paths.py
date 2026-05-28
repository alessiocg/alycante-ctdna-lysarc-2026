# -*- coding: utf-8 -*-
"""
_paths.py - Resolution unifiee des chemins pour le package Blood ALYCANTE.

Permet aux scripts d'etre 100% portables (NAS / poste local / cluster).
A importer en debut de chaque script Python du package :

    from _paths import INPUT_DIR, TABLES_DIR, FIGURES_DIR, DATA_DIR

Override possible via variables d'environnement :
    BLOOD_PKG_ROOT     = chemin absolu vers blood_article_package/
    BLOOD_INPUT_DIR    = chemin absolu vers input/   (defaut : <ROOT>/input)
    BLOOD_OUTPUT_DIR   = chemin absolu vers output/  (defaut : <ROOT>/output)

Si rien n'est defini, on remonte d'un cran depuis le repertoire du script
(scripts/ -> blood_article_package/).
"""
import os
import sys

# 1. Resolution de PKG_ROOT
PKG_ROOT = os.environ.get("BLOOD_PKG_ROOT")
if not PKG_ROOT:
    here = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(here)
    # Detection : si on est dans scripts/data_prep/, remonter 2 niveaux
    if os.path.basename(here) == "data_prep":
        PKG_ROOT = os.path.dirname(parent)
    else:
        PKG_ROOT = parent

# 2. Sous-repertoires
INPUT_DIR  = os.environ.get("BLOOD_INPUT_DIR",  os.path.join(PKG_ROOT, "input"))
OUTPUT_DIR = os.environ.get("BLOOD_OUTPUT_DIR", os.path.join(PKG_ROOT, "output"))
TABLES_DIR  = os.path.join(OUTPUT_DIR, "tables")
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")
DATA_DIR = INPUT_DIR  # alias historique
DATA_V2_DIR = os.path.join(OUTPUT_DIR, "data_v2")

# 3. Creation defensive
for d in (TABLES_DIR, FIGURES_DIR, DATA_V2_DIR):
    os.makedirs(d, exist_ok=True)

# 4. Helpers
def input_path(*parts):
    return os.path.join(INPUT_DIR, *parts)

def output_path(*parts):
    return os.path.join(OUTPUT_DIR, *parts)

def table_path(name):
    return os.path.join(TABLES_DIR, name)

def figure_path(name):
    return os.path.join(FIGURES_DIR, name)

if __name__ == "__main__":
    print("PKG_ROOT   :", PKG_ROOT)
    print("INPUT_DIR  :", INPUT_DIR)
    print("OUTPUT_DIR :", OUTPUT_DIR)
    print("TABLES_DIR :", TABLES_DIR)
    print("FIGURES_DIR:", FIGURES_DIR)
    print("DATA_DIR   :", DATA_DIR, "(alias = INPUT_DIR)")
