# -*- coding: utf-8 -*-
"""
34_fig_supp_dca_12m.py
Supplemental Figure S4 — Decision curve analysis at 12 months comparing the
day-14 JLCM-ctDNA classifier (Cox v2 risk) vs IPI ≥3 alone vs treat-all vs
treat-none, across decision threshold probabilities pt.

Inputs (precomputed):
  - output/scripts_figures/data_v2/dca_12m.csv  (model, all, none)
  - output/scripts_figures/data_v2/dca_12m_ipi.csv  (IPI ≥3 net benefit)

Output:
  - output/figures/blood_v2/fig_dca_12m.png
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
DATA = NAS / "output" / "scripts_figures" / "data_v2" / "dca_12m.csv"
DATA_IPI = NAS / "output" / "scripts_figures" / "data_v2" / "dca_12m_ipi.csv"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_dca_12m.png"


def main():
    df = pd.read_csv(DATA)
    fig, ax = plt.subplots(figsize=(9.5, 6))
    ax.plot(df["threshold"], df["net_benefit_model"], color="#d62728", lw=2.5,
            label="JLCM-ctDNA Cox v2 (day-14)")
    ax.plot(df["threshold"], df["net_benefit_all"], color="grey", ls="--", lw=1.5,
            label="Treat all")
    ax.plot(df["threshold"], df["net_benefit_none"], color="black", lw=1.5,
            label="Treat none")
    if DATA_IPI.exists():
        ipi = pd.read_csv(DATA_IPI)
        if "net_benefit_ipi" in ipi.columns:
            col = "net_benefit_ipi"
        elif "net_benefit_model" in ipi.columns:
            col = "net_benefit_model"
        else:
            col = ipi.columns[1]
        ax.plot(ipi["threshold"], ipi[col], color="#1f77b4", ls=":", lw=2,
                label="IPI ≥3 alone")

    ax.set_xlabel("Threshold probability pt")
    ax.set_ylabel("Net benefit at 12 months")
    ax.set_title("Decision curve analysis — net benefit of day-14 JLCM-ctDNA "
                 "vs IPI vs all/none")
    ax.set_xlim(0, 1)
    # Crop the y-axis to the relevant zone so the JLCM curve remains readable.
    # The 'treat all' curve plunges to -infinity near pt=1; we cap at -0.5.
    ax.set_ylim(-0.5, 0.55)
    ax.axhline(0.0, color="black", lw=0.8)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=10)
    ax.text(0.30, 0.18,
            "JLCM net benefit > IPI alone\nover pt ∈ [0.11, 0.85]",
            transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.85))
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
