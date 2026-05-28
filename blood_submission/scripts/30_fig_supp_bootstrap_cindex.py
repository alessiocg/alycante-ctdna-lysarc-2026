# -*- coding: utf-8 -*-
"""
30_fig_supp_bootstrap_cindex.py
Supplemental Figure S5 — Bootstrap (1000x) C-index distributions for the
univariable JLCM-ctDNA and multivariable Cox v2 models, EFS and OS.

Inputs (resolved relative to NAS):
  - output/scripts_figures/data_v2/bootstrap_cindex_efs_univariable.csv
  - output/scripts_figures/data_v2/bootstrap_cindex_efs_multivariable.csv
  - output/scripts_figures/data_v2/bootstrap_cindex_os_univariable.csv
  - output/scripts_figures/data_v2/bootstrap_cindex_os_multivariable.csv
  - output/scripts_figures/data_v2/bootstrap_cindex.csv  (summary with point estimates)

Output:
  - output/figures/blood_v2/fig_bootstrap_cindex.png

Reproducibility: relies on already-computed bootstrap CSVs (1000 iterations,
seed used in analysis pipeline; this script only plots).
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
DATA_DIR = NAS / "output" / "scripts_figures" / "data_v2"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_bootstrap_cindex.png"


def main():
    efs_uni = pd.read_csv(DATA_DIR / "bootstrap_cindex_efs_univariable.csv")
    efs_mul = pd.read_csv(DATA_DIR / "bootstrap_cindex_efs_multivariable.csv")
    os_uni = pd.read_csv(DATA_DIR / "bootstrap_cindex_os_univariable.csv")
    os_mul = pd.read_csv(DATA_DIR / "bootstrap_cindex_os_multivariable.csv")
    summary = pd.read_csv(DATA_DIR / "bootstrap_cindex.csv").set_index(["endpoint", "model"])

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, endpoint, (uni_df, mul_df) in zip(
            axes, ["efs", "os"], [(efs_uni, efs_mul), (os_uni, os_mul)]):
        uni = uni_df.iloc[:, -1].dropna().values
        mul = mul_df.iloc[:, -1].dropna().values
        ax.hist(uni, bins=40, alpha=0.6, color="#1f77b4",
                label=f"Univariable JLCM (n={len(uni)})", density=True)
        ax.hist(mul, bins=40, alpha=0.55, color="#d62728",
                label=f"Multivariable Cox v2 (n={len(mul)})", density=True)
        uni_pt = summary.loc[(endpoint, "univariable_JLCM"), "c_index"]
        mul_pt = summary.loc[(endpoint, "multivariable_v2"), "c_index"]
        uni_lo = summary.loc[(endpoint, "univariable_JLCM"), "ci_lo"]
        uni_hi = summary.loc[(endpoint, "univariable_JLCM"), "ci_hi"]
        mul_lo = summary.loc[(endpoint, "multivariable_v2"), "ci_lo"]
        mul_hi = summary.loc[(endpoint, "multivariable_v2"), "ci_hi"]
        ax.axvline(uni_pt, color="#1f77b4", lw=2, ls="--")
        ax.axvline(mul_pt, color="#d62728", lw=2, ls="--")
        ax.set_title(f"{endpoint.upper()} — Bootstrap (1000x) Harrell C-index")
        ax.set_xlabel("C-index")
        if endpoint == "efs":
            ax.set_ylabel("Density")
        ax.set_xlim(0.3, 1.0)
        ax.grid(True, alpha=0.3)
        legend_text = (
            f"Univariable: {uni_pt:.3f}  95% CI [{uni_lo:.2f}-{uni_hi:.2f}]\n"
            f"Multivariable: {mul_pt:.3f}  95% CI [{mul_lo:.2f}-{mul_hi:.2f}]"
        )
        ax.legend(loc="upper left", fontsize=8.5, frameon=True)
        ax.text(0.02, 0.55, legend_text, transform=ax.transAxes, fontsize=8.5,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    plt.suptitle("Bootstrap 1,000-iteration C-index distributions — Blood v2 sensitivity",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
