# -*- coding: utf-8 -*-
"""
36_fig_supp_forest_subgroups.py
Supplemental Figure S7 — Forest plot of EFS hazard ratios for the day-14
JLCM-ctDNA class (MAUVAIS vs BON) within pre-specified subgroups: IPI <3
vs ≥3, MTV median split, age, sex, ECOG, bridging therapy, LDH >ULN.
Bonferroni-adjusted interaction p-values are shown.

Inputs:
  - output/scripts_figures/data/subgroup_metrics.csv  (per-subgroup HR, CI, p)
  - output/scripts_figures/data_v2/subgroup_interactions.csv  (interaction p
    with Bonferroni correction)

Output:
  - output/figures/blood_v2/fig_forest_subgroups.png
"""

# === Path resolution (added for package portability) ===
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _paths import INPUT_DIR, OUTPUT_DIR, TABLES_DIR, FIGURES_DIR, DATA_DIR
except Exception:
    _here = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR   = os.path.join(_here, '..', 'input')
    OUTPUT_DIR  = os.path.join(_here, '..', 'output')
    TABLES_DIR  = os.path.join(OUTPUT_DIR, 'tables')
    FIGURES_DIR = os.path.join(OUTPUT_DIR, 'figures')
    DATA_DIR    = INPUT_DIR
    for d in (TABLES_DIR, FIGURES_DIR): os.makedirs(d, exist_ok=True)
# === end path resolution ===

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAS = Path(os.path.dirname(OUTPUT_DIR))
SG = NAS / "output" / "scripts_figures" / "data" / "subgroup_metrics.csv"
INT = NAS / "output" / "scripts_figures" / "data_v2" / "subgroup_interactions.csv"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_forest_subgroups.png"


def main():
    df = pd.read_csv(SG)
    inter = pd.read_csv(INT) if INT.exists() else pd.DataFrame()
    # Filter EFS only and rows with HR + n
    if "endpoint" in df.columns:
        df = df[df["endpoint"].str.lower().str.startswith("efs")].copy()
    df = df.dropna(subset=["HR", "CI_low", "CI_up"]).copy()

    # Friendly labels
    label_col = None
    for c in ["subgroup_label", "label", "subgroup"]:
        if c in df.columns:
            label_col = c
            break
    if label_col is None:
        label_col = df.columns[0]
    df["label"] = df[label_col].astype(str)
    fr_to_en = {
        "Toute la cohorte": "Overall cohort",
        "MTV < mediane": "MTV < median",
        "MTV >= mediane": "MTV >= median",
        "Bridging Yes": "Bridging yes",
        "Bridging No": "Bridging no",
        "Sexe Masculin": "Male",
        "Sexe Feminin": "Female",
    }
    df["label"] = df["label"].replace(fr_to_en)

    # Plot
    fig, ax = plt.subplots(figsize=(11, max(4, 0.55 * len(df))))
    y = np.arange(len(df))[::-1]
    for yi, (_, row) in zip(y, df.iterrows()):
        hr = float(row["HR"])
        lo = float(row["CI_low"])
        hi = float(row["CI_up"])
        ax.plot([lo, hi], [yi, yi], color="black", lw=1.5)
        ax.plot(hr, yi, "s", color="#d62728", markersize=9)
        n_show = ""
        if "n" in row and not pd.isna(row["n"]):
            n_show = f"  n={int(row['n'])}"
        ax.text(60, yi, f"HR {hr:.1f}  [{lo:.1f}-{hi:.1f}]{n_show}",
                va="center", fontsize=9)
    ax.axvline(1.0, color="grey", ls="--", lw=1)
    ax.set_xscale("log")
    ax.set_xlim(0.3, 200)
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"])
    ax.set_xlabel("Hazard ratio for EFS (high-risk vs low-risk), 95% CI")
    ax.set_title("Subgroup forest plot - day-14 JLCM-ctDNA class (Bonferroni adj.)")
    ax.grid(True, axis="x", alpha=0.3)

    if not inter.empty:
        bullet = []
        for _, row in inter.iterrows():
            sg = row.get("subgroup", "")
            p_efs = row.get("p_int_efs", np.nan)
            p_adj = row.get("bonferroni_p_efs", np.nan)
            bullet.append(
                f"Interaction {sg}: p={p_efs:.3f} (Bonf p={p_adj:.3f})"
            )
        ax.text(0.02, 0.02, "\n".join(bullet), transform=ax.transAxes,
                fontsize=9, bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
