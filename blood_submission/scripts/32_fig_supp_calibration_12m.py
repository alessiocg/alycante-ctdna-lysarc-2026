# -*- coding: utf-8 -*-
"""
32_fig_supp_calibration_12m.py
Supplemental Figure S2 — Calibration plot at 12 months for the multivariable
Cox v2 (predicted EFS event probability vs observed event rate, by quintile of
predicted risk).

Inputs (precomputed):
  - output/scripts_figures/data_v2/calibration_12m.csv  (per-quintile)
  - output/scripts_figures/data_v2/calibration_in_the_large.csv  (intercept/slope)

Output:
  - output/figures/blood_v2/fig_calibration_12m.png
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
DATA = NAS / "output" / "scripts_figures" / "data_v2" / "calibration_12m.csv"
DATA_LARGE = NAS / "output" / "scripts_figures" / "data_v2" / "calibration_in_the_large.csv"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_calibration_12m.png"


def main():
    df = pd.read_csv(DATA)
    # calibration_in_the_large may have intercept/slope rows
    intercept = slope = np.nan
    if DATA_LARGE.exists():
        large = pd.read_csv(DATA_LARGE)
        if "metric" in large.columns and "value" in large.columns:
            for _, row in large.iterrows():
                if str(row["metric"]).lower().startswith("interc"):
                    intercept = float(row["value"])
                elif str(row["metric"]).lower().startswith("slop"):
                    slope = float(row["value"])
        else:
            try:
                intercept = float(large.iloc[0, 0])
                slope = float(large.iloc[0, 1])
            except Exception:
                pass

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.plot([0, 1], [0, 1], color="grey", ls="--", lw=1.5, label="Ideal calibration")
    ax.plot(df["pred_mean"], df["obs_rate"], "o-", color="#1f77b4", lw=2,
            markersize=10, label="JLCM Cox v2 (per-quintile)")
    for _, row in df.iterrows():
        ax.annotate(f"n={int(row['n'])}",
                    (row["pred_mean"], row["obs_rate"]),
                    textcoords="offset points", xytext=(10, -10),
                    fontsize=9)
    ax.set_xlabel("Predicted 12-month event probability")
    ax.set_ylabel("Observed 12-month event rate")
    ax.set_title("Calibration plot at 12 months — multivariable Cox v2 (n=44)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    if not np.isnan(intercept) and not np.isnan(slope):
        ax.text(0.02, 0.92,
                f"Calibration-in-the-large\nIntercept = {intercept:+.2f}\nSlope = {slope:.2f}",
                transform=ax.transAxes, fontsize=10,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    ax.legend(loc="lower right")
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
