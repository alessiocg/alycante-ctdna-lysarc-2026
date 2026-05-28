# -*- coding: utf-8 -*-
"""
37_fig_visual_abstract.py
Supplemental Figure S8 (also referenced as Figure 6 in body) — Visual abstract
illustrating the "train-rich, deploy-early" JLCM ctDNA classifier for the
Blood Article v2.

The figure has 3 panels:
  1. Training: JLCM trained on full J0-M12 trajectories (theoretical curves)
  2. Deployment: predictClass on baseline + day-14 only
  3. Outcome: 12-month EFS difference (86% BON vs 9% MAUVAIS)

Inputs:
  - output/scripts_figures/data/data_lcmm_long.csv  (trajectories visualization)
  - output/scripts_figures/data/jlcm_predict_j14.csv  (class assignment)

Output:
  - output/figures/blood_v2/fig_visual_abstract.png
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
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

NAS = Path(os.path.dirname(OUTPUT_DIR))
LONG = NAS / "output" / "scripts_figures" / "data" / "data_lcmm_long.csv"
J14 = NAS / "output" / "scripts_figures" / "data" / "jlcm_predict_j14.csv"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_visual_abstract.png"


def main():
    long_df = pd.read_csv(LONG)
    j14 = pd.read_csv(J14)
    long_df = long_df.merge(j14[["ID", "group"]], on="ID", how="left")
    long_df = long_df.dropna(subset=["group"])
    # Remap French BON/MAUVAIS to English low-risk/high-risk for plot labels
    long_df["group_en"] = long_df["group"].map({"BON": "low-risk", "MAUVAIS": "high-risk"})

    times = sorted(long_df["time"].unique())

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

    # Panel 1 - TRAIN-RICH: full trajectories D0-M12
    ax1 = axes[0]
    for grp, color in [("low-risk", "#1f77b4"), ("high-risk", "#d62728")]:
        sub = long_df[long_df["group_en"] == grp]
        med = sub.groupby("time")["heg_log"].median()
        q25 = sub.groupby("time")["heg_log"].quantile(0.25)
        q75 = sub.groupby("time")["heg_log"].quantile(0.75)
        ax1.fill_between(med.index, q25, q75, color=color, alpha=0.2)
        ax1.plot(med.index, med.values, "-o", color=color, lw=2.5, markersize=7,
                 label=f"{grp} (n={sub['ID'].nunique()})")
    ax1.set_title("1. TRAIN-RICH\nJLCM fitted on full D0-M12 series", fontsize=11)
    ax1.set_xlabel("Months from CAR-T infusion")
    ax1.set_ylabel("log10 hEG (median, IQR)")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Panel 2 - DEPLOY-EARLY: D0 + D14 highlighted
    ax2 = axes[1]
    for grp, color in [("low-risk", "#1f77b4"), ("high-risk", "#d62728")]:
        sub = long_df[(long_df["group_en"] == grp) & (long_df["timepoint"].isin(["J0", "J14"]))]
        for pid, sub_pat in sub.groupby("ID"):
            sub_pat = sub_pat.sort_values("time")
            ax2.plot(sub_pat["time"], sub_pat["heg_log"], "-", color=color,
                     alpha=0.4, lw=1)
        med = sub.groupby("time")["heg_log"].median()
        ax2.plot(med.index, med.values, "-o", color=color, lw=3, markersize=10,
                 markeredgecolor="black", label=f"{grp} median")
    ax2.axvspan(0, 0.6, color="gold", alpha=0.18, label="Deployment window")
    ax2.set_title("2. DEPLOY-EARLY\npredictClass on D0 + D14 only", fontsize=11)
    ax2.set_xlabel("Months from CAR-T infusion")
    ax2.set_ylabel("log10 hEG")
    ax2.set_xlim(-0.1, 1.2)
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.3)

    # Panel 3 - OUTCOME: 12-month EFS bar
    ax3 = axes[2]
    labels = ["low-risk\n(favorable)", "high-risk\n(unfavorable)"]
    efs_12m = [86, 9]
    colors = ["#1f77b4", "#d62728"]
    bars = ax3.bar(labels, efs_12m, color=colors, edgecolor="black", lw=1.5)
    for bar, val in zip(bars, efs_12m):
        ax3.text(bar.get_x() + bar.get_width() / 2, val + 2, f"{val}%",
                 ha="center", fontsize=14, fontweight="bold")
    ax3.set_ylabel("12-month EFS (%)")
    ax3.set_ylim(0, 105)
    ax3.set_title("3. OUTCOME\nDay-14 classifier discriminates 12-mo EFS",
                  fontsize=11)
    ax3.grid(True, axis="y", alpha=0.3)
    ax3.text(0.5, 0.45,
             "HR 17.7\n95% CI 6.3-50.0\np < 0.0001",
             transform=ax3.transAxes, ha="center", fontsize=11,
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))

    fig.suptitle("Day-14 JLCM ctDNA classifier in R/R LBCL post-CAR-T — "
                 "train-rich, deploy-early",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
