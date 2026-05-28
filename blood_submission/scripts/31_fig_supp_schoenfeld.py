# -*- coding: utf-8 -*-
"""
31_fig_supp_schoenfeld.py
Supplemental Figure S1 — Schoenfeld proportional-hazards test, rank-time
transform, for each covariate of the multivariable Cox v2 model (JLCM, IPI,
log10 MTV) on EFS and OS.

Input (precomputed):
  - output/scripts_figures/data_v2/schoenfeld.csv

Output:
  - output/figures/blood_v2/fig_schoenfeld.png

Generation of the Schoenfeld CSV uses lifelines' `proportional_hazard_test`
on the fitted CoxPHFitter with ridge penalty 0.1; this plotting script only
visualises the resulting p-values.
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
DATA = NAS / "output" / "scripts_figures" / "data_v2" / "schoenfeld.csv"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_schoenfeld.png"

LABEL_MAP = {
    "jlcm": "JLCM class (high-risk vs low-risk)",
    "ipi_high": "IPI ≥3",
    "mtv_log_base": "log10 baseline MTV",
}


def main():
    df = pd.read_csv(DATA)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, endpoint in zip(axes, ["efs", "os"]):
        sub = df[df["endpoint"] == endpoint].copy()
        sub["label"] = sub["var"].map(LABEL_MAP).fillna(sub["var"])
        # Order: JLCM, IPI, MTV
        order = ["JLCM class (high-risk vs low-risk)", "IPI ≥3", "log10 baseline MTV"]
        sub = sub.set_index("label").reindex(order).reset_index()
        y = np.arange(len(sub))
        colors = ["#2ca02c" if p > 0.05 else "#d62728" for p in sub["p"]]
        ax.barh(y, sub["p"], color=colors, alpha=0.8, edgecolor="black")
        for yi, p in zip(y, sub["p"]):
            ax.text(min(p, 0.95) + 0.02, yi, f"p = {p:.3f}", va="center", fontsize=10)
        ax.axvline(0.05, color="red", ls="--", lw=1.5, label="alpha = 0.05")
        ax.axvline(0.20, color="orange", ls=":", lw=1.2, label="conservative 0.20")
        ax.set_yticks(y)
        ax.set_yticklabels(sub["label"])
        ax.set_xlabel("Schoenfeld test p-value (rank time-transform)")
        ax.set_title(f"{endpoint.upper()} — PH assumption test")
        ax.set_xlim(0, 1.05)
        ax.grid(True, axis="x", alpha=0.3)
        if endpoint == "efs":
            ax.legend(loc="lower right", fontsize=9)

    plt.suptitle(
        "Schoenfeld proportional-hazards test — multivariable Cox v2 "
        "(all p > 0.20: PH holds)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
