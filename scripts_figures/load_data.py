#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module utilitaire : chargement des données ALYCANTE.

Logique :
  1. Cherche Donnees_brutes2.xlsx à la racine du projet (../../)
     → Si trouvé, lance nettoyage_donnees.R pour régénérer Donnees.xlsx dans data/
  2. Sinon, utilise data/Donnees.xlsx (version corrigée pré-calculée)

Usage dans un script figure :
    from load_data import load_donnees, load_surv
    df = load_donnees()
    valid = load_surv(df)
"""
import os
import subprocess
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

# Chemin racine projet (2 niveaux au-dessus de scripts_figures/)
ROOT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
INPUT_DIR = os.path.join(ROOT_DIR, "input")
BRUTES_PATH = os.path.join(INPUT_DIR, "Donnees_brutes2.xlsx")


def _try_regenerate():
    """Tente de régénérer Donnees.xlsx depuis Donnees_brutes2.xlsx via R."""
    nettoyage_r = os.path.join(SCRIPT_DIR, "nettoyage_donnees.R")
    donnees_out = os.path.join(DATA_DIR, "Donnees.xlsx")

    if not os.path.exists(BRUTES_PATH):
        return False
    if not os.path.exists(nettoyage_r):
        return False

    print(f"[load_data] Donnees_brutes2.xlsx trouv\u00e9 \u00e0 {BRUTES_PATH}")
    print(f"[load_data] R\u00e9g\u00e9n\u00e9ration de Donnees.xlsx via nettoyage_donnees.R...")

    try:
        # Copier brutes dans data/ temporairement pour que R le trouve
        import shutil
        brutes_tmp = os.path.join(DATA_DIR, "Donnees_brutes2.xlsx")
        shutil.copy2(BRUTES_PATH, brutes_tmp)

        result = subprocess.run(
            ["Rscript", nettoyage_r],
            cwd=DATA_DIR,
            capture_output=True, text=True, timeout=60
        )

        # Nettoyer la copie temp
        if os.path.exists(brutes_tmp):
            os.remove(brutes_tmp)

        if result.returncode == 0 and os.path.exists(donnees_out):
            print(f"[load_data] Donnees.xlsx r\u00e9g\u00e9n\u00e9r\u00e9 avec succ\u00e8s")
            return True
        else:
            print(f"[load_data] \u00c9chec R: {result.stderr[:200] if result.stderr else 'no error'}")
            return False
    except Exception as e:
        print(f"[load_data] Erreur: {e}")
        return False


def load_donnees():
    """Charge Donnees.xlsx (régénéré si possible, sinon fallback sur data/)."""
    donnees_path = os.path.join(DATA_DIR, "Donnees.xlsx")

    # Tenter la régénération
    _try_regenerate()

    # Charger (régénéré ou existant)
    if not os.path.exists(donnees_path):
        raise FileNotFoundError(f"Donnees.xlsx introuvable dans {DATA_DIR}")

    df = pd.read_excel(donnees_path)
    ni = df.loc[df['MRD_quali'] == 'NI', 'randomisation'].unique()
    df = df[~df['randomisation'].isin(ni)]
    df['MRD_quanti_heg'] = pd.to_numeric(df['MRD_quanti_heg'], errors='coerce')
    df.loc[df['MRD_quali'] == 'NEGATIF', 'MRD_quanti_heg'] = 0.0
    return df


def _parse_dt(v):
    s = str(v).strip()
    try:
        n = float(s.replace(',', '.'))
        return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(n))
    except Exception:
        for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d']:
            try:
                return pd.to_datetime(s, format=fmt)
            except Exception:
                pass
    return pd.NaT


def load_surv(df=None):
    """Charge les données de survie avec correction J0 et R/R strict."""
    surv = pd.read_excel(os.path.join(DATA_DIR, 'ALYCANTE_RNASeq_21OCT2025.xlsx'))
    surv.rename(columns={'Subject Identifier for the Study': 'randomisation'}, inplace=True)
    surv['efs_time'] = pd.to_numeric(surv['EFS from leukapheresis (months)'], errors='coerce')

    # Correction J0
    surv['_dl'] = surv['Start of leukapheresis'].apply(_parse_dt)
    surv['_dj'] = surv['Date of Axi-cel infusion (numeric)'].apply(_parse_dt)
    surv['efs_time'] = surv['efs_time'] - (surv['_dj'] - surv['_dl']).dt.days / 30.44

    is_rr = surv['Event for EFS'].str.contains('Progression|Relapse', na=False)
    surv['efs_event'] = ((surv['Event for EFS.1'] == 'Yes') & is_rr).astype(int)

    if df is not None:
        valid = surv[surv['randomisation'].isin(df['randomisation'].unique())].drop_duplicates('randomisation')
    else:
        valid = surv.drop_duplicates('randomisation')

    valid['rr_12'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 12)).astype(int)
    valid['rr_24'] = ((valid['efs_event'] == 1) & (valid['efs_time'] <= 24)).astype(int)
    valid['adeq_12'] = ((valid['efs_time'] >= 12) | (valid['efs_event'] == 1))
    valid['adeq_24'] = ((valid['efs_time'] >= 24) | (valid['efs_event'] == 1))

    return valid
