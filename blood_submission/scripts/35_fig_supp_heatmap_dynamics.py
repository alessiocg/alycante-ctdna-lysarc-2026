# -*- coding: utf-8 -*-
"""
35_fig_supp_heatmap_dynamics.py
Supplemental Figure S6 — Heatmap of individual ctDNA log10 hEG dynamics in
ALYCANTE, rows = patients ordered by JLCM class then by event status,
columns = ctDNA timepoints (J0, J14, M1, M3, M6, M9, M12).

Inputs:
  - output/scripts_figures/data/data_lcmm_long.csv  (long format hEG)
  - output/scripts_figures/data/jlcm_predict_j14.csv  (JLCM J14 group)

Output:
  - output/figures/blood_v2/fig_heatmap_dynamics.png
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
LONG = NAS / "output" / "scripts_figures" / "data" / "data_lcmm_long.csv"
J14 = NAS / "output" / "scripts_figures" / "data" / "jlcm_predict_j14.csv"
OUT_PNG = NAS / "output" / "figures" / "blood_v2" / "fig_heatmap_dynamics.png"

TIMEPOINTS = ["J0", "J14", "M1", "M3", "M6", "M9", "M12"]


def main():
    long_df = pd.read_csv(LONG)
    j14 = pd.read_csv(J14)

    # Pivot to wide hEG_log
    wide = long_df.pivot_table(index="ID", columns="timepoint",
                               values="heg_log", aggfunc="mean")
    wide = wide.reindex(columns=TIMEPOINTS)

    # Attach JLCM group
    j14_map = j14.set_index("ID")["group"].to_dict()
    efs_event = long_df.groupby("ID")["efs_event"].first().to_dict()
    wide["group"] = wide.index.map(j14_map)
    wide["event"] = wide.index.map(efs_event).astype("Int64")
    wide = wide[wide["group"].isin(["BON", "MAUVAIS"])]

    # Order rows: BON first, then MAUVAIS; within each, ordered by event then by baseline
    order = (
        wide.assign(
            grp_order=lambda d: d["group"].map({"BON": 0, "MAUVAIS": 1}),
            event_order=lambda d: d["event"].fillna(-1).astype(int),
        )
        .sort_values(["grp_order", "event_order", "J0"],
                     ascending=[True, False, True])
        .index
    )
    wide = wide.loc[order]
    mat = wide[TIMEPOINTS].values

    fig, ax = plt.subplots(figsize=(9, 9))
    im = ax.imshow(mat, aspect="auto", cmap="RdYlBu_r", vmin=-6, vmax=4,
                   interpolation="nearest")
    ax.set_xticks(range(len(TIMEPOINTS)))
    ax.set_xticklabels(TIMEPOINTS)
    ax.set_xlabel("Timepoint")
    ax.set_ylabel(f"Patients (n={len(wide)}) - low-risk top, high-risk bottom")
    ax.set_title("Individual ctDNA dynamics (log10 hEG) by JLCM class")

    # Mark low-risk/high-risk boundary
    n_bon = (wide["group"] == "BON").sum()
    ax.axhline(n_bon - 0.5, color="black", lw=2)
    ax.text(-0.6, n_bon / 2, "low-risk\n(n={})".format(n_bon), rotation=90,
            va="center", ha="right", fontsize=11, fontweight="bold", color="#1f77b4")
    ax.text(-0.6, n_bon + (len(wide) - n_bon) / 2,
            "high-risk\n(n={})".format(len(wide) - n_bon), rotation=90,
            va="center", ha="right", fontsize=11, fontweight="bold", color="#d62728")

    cbar = plt.colorbar(im, ax=ax, shrink=0.6)
    cbar.set_label("log10 hEG (floor = -6)")
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
