# -*- coding: utf-8 -*-
"""
33_fig_supp_tdroc.py
Supplemental Figure S3 — Time-dependent (cumulative/dynamic) AUC for the
day-14 JLCM-ctDNA classifier on EFS, evaluated at 6, 12, 18 and 24 months.

Input (precomputed):
  - output/scripts_figures/data_v2/tdroc.csv

Output:
  - output/figures/blood_v2/fig_tdroc.png
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
import pandas as pd

NAS = Path(os.path.dirname(OUTPUT_DIR))
DATA = NAS / "output" / "scripts_figures" / "data_v2" / "tdroc.csv"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_tdroc.png"


def main():
    df = pd.read_csv(DATA)
    df = df.sort_values("horizon_months")
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(df["horizon_months"], df["auc"], "o-", color="#d62728", lw=2.5,
            markersize=11, label="Day-14 JLCM-ctDNA (EFS)")
    for _, row in df.iterrows():
        ax.annotate(f"{row['auc']:.2f}",
                    (row["horizon_months"], row["auc"]),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=10, fontweight="bold")
    ax.axhline(0.5, color="grey", ls="--", lw=1, label="Chance (AUC=0.5)")
    ax.set_xlabel("Time horizon (months from day 14)")
    ax.set_ylabel("Time-dependent AUC (cumulative/dynamic)")
    ax.set_title("Time-dependent AUC — day-14 JLCM-ctDNA classifier, EFS")
    ax.set_xticks(df["horizon_months"].values)
    ax.set_ylim(0.4, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
