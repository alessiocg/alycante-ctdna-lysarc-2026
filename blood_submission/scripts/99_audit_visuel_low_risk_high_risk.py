# -*- coding: utf-8 -*-
"""
99_fix_blood_figures_v3.py

Auditeur visuel ALYCANTE-Blood : régénère toutes les figures contenant des
résidus BON/MAUVAIS hérités du développement, en les remplaçant par low-risk/
high-risk + autres expressions anglaises. Cible le package Blood v3.

Stratégie : ne touche PAS aux CSV sources (ils contiennent encore BON/MAUVAIS
comme labels d'origine du modèle JLCM). Remappe à la volée dans chaque script.

Figures régénérées :
  - Fig1A_trajectories_theoretical.png  (courbes théoriques JLCM)
  - Fig1B_trajectories_observed.png     (trajectoires observées par R/R)
  - Fig2_km_efs_os.png                  (KM landmark par horizon)
  - Fig3_forest_multivariate.png        (Cox multivariate forest)
  - Fig5A_ctdna_vs_mtv_kappa.png        (heatmap concordance)
  - Fig5B_bimarker_forest.png           (bi-marker forest)
  - SuppFig1_schoenfeld.png             (S1)
  - SuppFig6_heatmap_dynamics.png       (S6)
  - SuppFig7_forest_subgroups.png       (S7)

Ensuite recombine Fig1 et Fig5 (les 2 panels combinés) via 50_rebuild logic.
"""

from __future__ import annotations

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

import io
import os
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ----------------------------------------------------------------------
# PATHS — autonomous (uses _paths.INPUT_DIR / FIGURES_DIR)
# ----------------------------------------------------------------------
FIG_DIR = Path(FIGURES_DIR)
DATA_DIR = Path(INPUT_DIR)       # all derived CSVs live alongside raw inputs
DATA_V2_DIR = Path(INPUT_DIR)    # idem (no separate data_v2 in autonomous package)

# Optional NAS fallback for development on PI's machine
_nas_root = os.environ.get("BLOOD_NAS_ROOT", "")
if _nas_root:
    _nas = Path(_nas_root)
    _nas_data = _nas / "output" / "scripts_figures" / "data"
    _nas_data_v2 = _nas / "output" / "scripts_figures" / "data_v2"
    # Use NAS if a key file is missing locally
    if not (DATA_DIR / "data_lcmm_long.csv").exists() and _nas_data.exists():
        DATA_DIR = _nas_data
    if not (DATA_V2_DIR / "schoenfeld.csv").exists() and _nas_data_v2.exists():
        DATA_V2_DIR = _nas_data_v2

LABEL_MAP = {"BON": "low-risk", "MAUVAIS": "high-risk"}
COLOR_LOW = "#1f77b4"   # bleu
COLOR_HIGH = "#d62728"  # rouge

plt.rcParams.update({
    "savefig.dpi": 180,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "DejaVu Sans",
    "font.size": 10,
})


# ----------------------------------------------------------------------
# Fig2 : KM EFS landmark par horizon (JLCM random=~time)
# ----------------------------------------------------------------------
def fig2_km_landmark():
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test

    loo = pd.read_csv(DATA_DIR / "jlcm_loo_predictions.csv")
    rr = pd.read_csv(DATA_DIR / "rr_strict_mapping.csv")
    long = pd.read_csv(DATA_DIR / "data_lcmm_long.csv")

    # Map ID -> randomisation
    id_map = long[["ID", "randomisation"]].drop_duplicates()
    surv = long[["ID", "efs_time", "efs_event"]].drop_duplicates()
    rr2 = rr.merge(id_map, on="randomisation")
    surv = surv.merge(rr2[["ID", "rr_12", "rr_24"]], on="ID", how="left")
    surv["rr_event"] = surv["rr_24"]  # tout R/R sur horizon long

    horizons = [("D14", 0.46), ("M1", 1.02), ("M3", 2.99),
                ("M6", 6.03), ("M9", 9.05), ("M12", 11.99)]

    fig, axes = plt.subplots(2, 3, figsize=(13, 8), sharey=True)
    axes = axes.flatten()
    max_followup = surv["efs_time"].max()

    for ax, (h_name, h_time) in zip(axes, horizons):
        loo_h = loo[loo["horizon"] == ("J14" if h_name == "D14" else h_name)][["ID", "group"]]
        if len(loo_h) == 0:
            ax.set_title(f"Horizon {h_name} (no data)")
            continue
        pred_m = loo_h.merge(surv, on="ID", how="inner")
        # landmark : exclure ceux avec event avant l'horizon
        pred_lm = pred_m[~((pred_m["rr_event"] == 1) & (pred_m["efs_time"] < h_time))].copy()
        pred_lm["surv_time"] = np.maximum(pred_lm["efs_time"] - h_time, 0.01)
        pred_lm["group_en"] = pred_lm["group"].map(LABEL_MAP)

        kmf = KaplanMeierFitter()
        for grp, color in [("low-risk", COLOR_LOW), ("high-risk", COLOR_HIGH)]:
            sub = pred_lm[pred_lm["group_en"] == grp]
            if len(sub) == 0:
                continue
            kmf.fit(sub["surv_time"], sub["rr_event"], label=f"{grp} (n={len(sub)})")
            kmf.plot_survival_function(ax=ax, ci_show=False, color=color, lw=2)

        # p-value log-rank
        sub_lr_low = pred_lm[pred_lm["group_en"] == "low-risk"]
        sub_lr_high = pred_lm[pred_lm["group_en"] == "high-risk"]
        if len(sub_lr_low) > 0 and len(sub_lr_high) > 0:
            lr = logrank_test(
                sub_lr_low["surv_time"], sub_lr_high["surv_time"],
                sub_lr_low["rr_event"], sub_lr_high["rr_event"]
            )
            p = lr.p_value
            ptxt = "<0.001" if p < 0.001 else f"{p:.3f}"
        else:
            ptxt = "NA"

        # Barres 12m / 24m
        v12 = 12 - h_time
        v24 = 24 - h_time
        xlim_val = int(np.ceil((max_followup - h_time) / 5) * 5)
        if 0 < v12 <= xlim_val:
            ax.axvline(v12, ls="--", color="gray", lw=0.8)
            ax.text(v12, 1.02, "12m", fontsize=7, color="gray", ha="center")
        if 0 < v24 <= xlim_val:
            ax.axvline(v24, ls="--", color="gray", lw=0.8)
            ax.text(v24, 1.02, "24m", fontsize=7, color="gray", ha="center")

        ax.set_title(f"Horizon {h_name}", fontsize=11, fontweight="bold")
        ax.set_xlabel(f"Time from {h_name} (months)", fontsize=9)
        ax.set_ylabel("Event-free survival (R/R)", fontsize=9)
        ax.set_ylim(0, 1.05)
        ax.set_xlim(0, xlim_val)
        ax.text(0.98, 0.95, f"p = {ptxt}", transform=ax.transAxes,
                fontsize=9, ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85))
        ax.legend(loc="lower left", fontsize=8, frameon=True)
        ax.grid(True, alpha=0.3)

    fig.suptitle(
        "Kaplan-Meier EFS by truncation horizon - JLCM random=~time (landmark analysis)",
        fontsize=12.5, fontweight="bold", y=1.00,
    )
    plt.tight_layout()
    out = FIG_DIR / "Fig2_km_efs_os.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# Fig5A : heatmap concordance ctDNA-JLCM vs MTV-JLCM
# ----------------------------------------------------------------------
def fig5a_heatmap_concordance():
    crosstab = pd.read_csv(DATA_DIR / "jlcm_ctdna_mtv_crosstab.csv", index_col=0)
    metrics = pd.read_csv(DATA_DIR / "jlcm_ctdna_mtv_concordance.csv")
    n = int(metrics.loc[metrics["metric"] == "n", "value"].iloc[0])
    kap = float(metrics.loc[metrics["metric"] == "cohen_kappa", "value"].iloc[0])
    agree = float(metrics.loc[metrics["metric"] == "agreement_pct", "value"].iloc[0])

    # Reorder rows/cols low-risk first then high-risk
    crosstab = crosstab.reindex(index=["BON", "MAUVAIS"], columns=["BON", "MAUVAIS"])
    mat = crosstab.values.astype(int)

    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(mat, cmap="YlOrRd", aspect="auto", vmin=0, vmax=mat.max())
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{mat[i, j]}", ha="center", va="center",
                    fontsize=24, fontweight="bold",
                    color="black" if mat[i, j] < mat.max() * 0.6 else "white")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["low-risk", "high-risk"], fontsize=12)
    ax.set_yticks([0, 1]); ax.set_yticklabels(["low-risk", "high-risk"], fontsize=12)
    ax.set_xlabel("JLCM-MTV class (early PET D14)", fontsize=12, fontweight="bold")
    ax.set_ylabel("JLCM-ctDNA class (early ctDNA D14)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Concordance JLCM-ctDNA vs JLCM-MTV\n"
        f"ALYCANTE (n={n}) | kappa = {kap:.2f} | agreement = {agree:.0f}%",
        fontsize=12.5, fontweight="bold")
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("N patients")
    plt.tight_layout()
    out = FIG_DIR / "Fig5A_ctdna_vs_mtv_kappa.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# Fig5B : bi-marker Cox forest (ctDNA-JLCM + MTV-JLCM)
# ----------------------------------------------------------------------
def fig5b_bimarker_forest():
    df = pd.read_csv(DATA_DIR / "cox_bimarker_metrics.csv")
    df = df.dropna(subset=["hr"]).copy()

    # Remap noms variables BON/MAUVAIS -> high-risk
    def relabel(v):
        v = str(v).replace("class_ctdnaMAUVAIS", "ctDNA-JLCM high-risk")
        v = v.replace("class_mtvMAUVAIS", "MTV-JLCM high-risk")
        return v
    df["var_en"] = df["var"].map(relabel)
    df["model_en"] = df["model"].replace({
        "ctDNA seul": "ctDNA alone",
        "MTV seul": "MTV alone",
        "ctDNA + MTV": "ctDNA + MTV",
    })
    df["row_label"] = df["endpoint"].str.upper() + " | " + df["model_en"] + " [" + df["var_en"] + "]"

    # Cap CI for display
    df["hr_cap"] = df["hr"].clip(upper=200)
    df["hi_cap"] = df["hr_hi"].clip(upper=200)
    df["lo_cap"] = df["hr_lo"].clip(lower=0.1)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    y = np.arange(len(df))[::-1]
    for yi, (_, row) in zip(y, df.iterrows()):
        ep = row["endpoint"].upper()
        color = COLOR_HIGH if ep == "OS" else COLOR_LOW
        marker = "s" if ep == "OS" else "o"
        ax.plot([row["lo_cap"], row["hi_cap"]], [yi, yi], color=color, lw=1.8)
        ax.plot(row["hr_cap"], yi, marker=marker, color=color, markersize=10,
                markeredgecolor="black", markeredgewidth=0.5)
        pstr = "<0.0001" if row["p"] < 0.0001 else f"={row['p']:.3f}"
        ax.text(220, yi, f"HR={row['hr']:.2g}  p{pstr}",
                va="center", fontsize=9)

    ax.set_yticks(y)
    ax.set_yticklabels(df["row_label"], fontsize=9)
    ax.axvline(1.0, color="gray", ls="--", lw=1)
    ax.set_xscale("log")
    ax.set_xlim(0.05, 200)
    ax.set_xlabel("Hazard ratio (95% CI)", fontsize=11)
    ax.set_title("Cox univariable and bi-marker (ctDNA + MTV) - ALYCANTE",
                 fontsize=11.5, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3, which="both")
    from matplotlib.lines import Line2D
    legend = [
        Line2D([0], [0], color=COLOR_HIGH, marker="s", label="OS", lw=1.8),
        Line2D([0], [0], color=COLOR_LOW, marker="o", label="EFS", lw=1.8),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=9)
    plt.tight_layout()
    out = FIG_DIR / "Fig5B_bimarker_forest.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# Fig1A : courbes JLCM théoriques par classe (reconstruites depuis pprob du
# modèle complet random=~time : moyenne de heg_log par classe x timepoint)
# ----------------------------------------------------------------------
def fig1a_theoretical_curves():
    long = pd.read_csv(DATA_DIR / "data_lcmm_long.csv")
    j14 = pd.read_csv(DATA_DIR / "jlcm_predict_j14.csv")

    # group BON/MAUVAIS du jlcm_predict_j14
    long["randomisation"] = long["randomisation"].astype(str)
    j14["randomisation"] = j14["randomisation"].astype(str)
    merged = long.merge(j14[["randomisation", "group"]], on="randomisation", how="left")
    merged = merged[merged["group"].isin(["BON", "MAUVAIS"])]
    merged["group_en"] = merged["group"].map(LABEL_MAP)

    # Moyenne par groupe x timepoint pour la courbe représentative
    # Si manquant, on enlève
    timepoints_order = ["J0", "J14", "M1", "M3", "M6", "M9", "M12"]
    time_num = {"J0": 0, "J14": 0.46, "M1": 1.02, "M3": 2.99,
                "M6": 6.03, "M9": 9.05, "M12": 11.99}

    fig, ax = plt.subplots(figsize=(11, 5.5))
    # tracé moyenne ± SE par classe
    for grp, color in [("low-risk", COLOR_LOW), ("high-risk", COLOR_HIGH)]:
        sub = merged[merged["group_en"] == grp]
        # courbe moyenne
        agg = sub.groupby("timepoint")["heg_log"].agg(["mean", "sem"]).reset_index()
        agg = agg.set_index("timepoint").reindex(timepoints_order).dropna().reset_index()
        agg["time_num"] = agg["timepoint"].map(time_num)
        n_pat = sub["randomisation"].nunique()
        ev = sub.drop_duplicates("randomisation")["efs_event"].sum()
        ax.plot(agg["time_num"], agg["mean"],
                color=color, lw=3.0,
                label=f"{grp} (n={n_pat}, events={int(ev)})")
        ax.fill_between(agg["time_num"], agg["mean"] - agg["sem"],
                        agg["mean"] + agg["sem"], color=color, alpha=0.20)

    ax.axhline(0, color="grey", ls=":", lw=0.7)
    ax.set_xlabel("Time since CAR-T infusion (months)", fontsize=11)
    ax.set_ylabel("Mean log10 hEG (per mL plasma)", fontsize=11)
    ax.set_title("JLCM 2 classes - mean theoretical-class trajectories",
                 fontsize=12, fontweight="bold")
    ax.set_xticks([time_num[t] for t in timepoints_order])
    ax.set_xticklabels([{'J0':'D0','J14':'D14'}.get(t,t) for t in timepoints_order])
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=10, frameon=True)
    plt.tight_layout()
    out = FIG_DIR / "Fig1A_trajectories_theoretical.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# Fig1B : trajectoires observées individuelles, 4 facets par R/R
# ----------------------------------------------------------------------
def fig1b_observed_individual():
    long = pd.read_csv(DATA_DIR / "data_lcmm_long.csv")
    rr = pd.read_csv(DATA_DIR / "rr_strict_mapping.csv")
    long["randomisation"] = long["randomisation"].astype(str)
    rr["randomisation"] = rr["randomisation"].astype(str)

    merged = long.merge(rr, on="randomisation", how="left")
    timepoints_order = ["J0", "J14", "M1", "M3", "M6", "M9", "M12"]
    time_num = {"J0": 0, "J14": 0.46, "M1": 1.02, "M3": 2.99,
                "M6": 6.03, "M9": 9.05, "M12": 11.99}

    # 4 groupes : pas de R/R, R/R 12m, R/R 12-24m, R/R 24m (cumulatif)
    no_rr = merged.drop_duplicates("randomisation").query("rr_24 == 0 and rr_12 == 0")
    rr12 = merged.drop_duplicates("randomisation").query("rr_12 == 1")
    rr12_24 = merged.drop_duplicates("randomisation").query("rr_12 == 0 and rr_24 == 1")
    rr24 = merged.drop_duplicates("randomisation").query("rr_24 == 1")

    groups = [
        ("No R/R", no_rr, "#6699CC", "#003366"),
        ("R/R <= 12 months", rr12, "#CC6666", "#660000"),
        ("R/R 12-24 months", rr12_24, "#CC9966", "#663300"),
        ("R/R <= 24 months (any)", rr24, "#CC4444", "#880000"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharey=True, sharex=True)
    axes = axes.flatten()
    fig.suptitle("Longitudinal ctDNA kinetics (log10 hEG)",
                 fontsize=13.5, fontweight="bold", y=1.00)
    for ax, (title, sub, c_line, c_med) in zip(axes, groups):
        ids = sub["randomisation"].unique()
        sub_long = merged[merged["randomisation"].isin(ids)]
        for pat in ids:
            pat_data = sub_long[sub_long["randomisation"] == pat].sort_values("time")
            pat_data = pat_data[pat_data["timepoint"].isin(timepoints_order)]
            if len(pat_data) > 1:
                ax.plot(pat_data["time"], pat_data["heg_log"],
                        color=c_line, alpha=0.25, lw=0.8)
        # médiane par timepoint
        med = sub_long[sub_long["timepoint"].isin(timepoints_order)].groupby("timepoint")["heg_log"].median()
        med_x = [time_num[t] for t in timepoints_order if t in med.index]
        med_y = [med[t] for t in timepoints_order if t in med.index]
        ax.plot(med_x, med_y, color=c_med, marker="o", markersize=6,
                linestyle="none", zorder=4)
        ax.axhline(0, color="grey", ls=":", lw=0.5)
        ax.set_title(f"{title} (n={len(ids)})", fontsize=11, fontweight="bold")
        ax.set_xlabel("Months since CAR-T infusion")
        ax.set_ylabel("log10 hEG")
        ax.set_xticks([time_num[t] for t in timepoints_order])
        ax.set_xticklabels([{'J0':'D0','J14':'D14'}.get(t,t) for t in timepoints_order], rotation=45, ha="right", fontsize=9)
        ax.set_ylim(-6.5, 5.5)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.02, 1, 0.97])
    fig.text(0.5, 0.005,
             "Thin lines: individual trajectories | Dots: median per timepoint | "
             "R/R = relapse/progression only",
             ha="center", fontsize=8, color="#666666", style="italic")
    out = FIG_DIR / "Fig1B_trajectories_observed.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# Fig3 : forest multivarié v2 (JLCM + IPI + log10 MTV)
# ----------------------------------------------------------------------
def fig3_forest_multivariate():
    csv_local = Path(os.path.join(INPUT_DIR, "cox_multivariate_v2_metrics.csv"))
    if not csv_local.exists() and _nas_root:
        # fallback NAS via env var
        csv_local = Path(_nas_root) / "output" / "scripts_figures" / "data" / "cox_multivariate_v2_metrics.csv"
    if not csv_local.exists():
        # Hard fallback: search package output for the file
        cands = list(Path(OUTPUT_DIR).rglob("cox_multivariate_v2_metrics.csv"))
        if cands:
            csv_local = cands[0]
    df = pd.read_csv(csv_local)
    final = df[df["model"] == "multivarie_v2"].copy()
    var_order = ["jlcm", "IPI_HIGH", "MTV_BL_log10"]
    labels = {
        "jlcm": "JLCM ctDNA D14\n(high-risk vs low-risk)",
        "IPI_HIGH": "IPI ≥3 vs <3",
        "MTV_BL_log10": "log10(MTV baseline)\n(per unit)",
    }

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.0), constrained_layout=True)
    for ax, ep, title in zip(axes, ["efs", "os"], ["Event-free survival", "Overall survival"]):
        sub = final[final["endpoint"] == ep].set_index("var").loc[var_order].reset_index()
        ypos = np.arange(len(sub))[::-1]
        cidx = sub["C_index"].iloc[0]
        nn = int(sub["n"].iloc[0])
        for i, row in sub.iterrows():
            y = ypos[i]
            hr, lo, hi, p = row["HR"], row["CI_low"], row["CI_up"], row["p"]
            color = COLOR_HIGH if row["var"] == "jlcm" else COLOR_LOW
            marker = "s" if row["var"] == "jlcm" else "o"
            hi_disp = min(hi, 80)
            ax.plot([max(lo, 0.05), hi_disp], [y, y], color=color, lw=2.4)
            ax.plot(hr, y, marker=marker, color=color, markersize=11, zorder=5,
                    markeredgecolor="black", markeredgewidth=0.6)
            pstr = "<0.0001" if p < 0.0001 else f"={p:.3f}"
            ax.text(110, y, f"HR={hr:.2f} [{lo:.2f}-{hi:.2f}]  p{pstr}",
                    va="center", fontsize=9.5)
        ax.set_yticks(ypos)
        ax.set_yticklabels([labels[v] for v in sub["var"]], fontsize=10)
        ax.axvline(1, color="gray", ls="--", lw=1.1)
        ax.set_xscale("log")
        ax.set_xlim(0.3, 80)
        ax.set_xlabel("Adjusted hazard ratio (95% CI)", fontsize=10)
        ax.set_title(f"{title} - C-index = {cidx:.3f} (n={nn})",
                     fontsize=11, weight="bold")
        ax.grid(axis="x", alpha=0.3, which="both")

    plt.suptitle(
        "Cox multivariable v2 : JLCM ctDNA day-14 class remains independent of "
        "IPI and baseline MTV\n(LDH and ECOG omitted because they are IPI components)",
        fontsize=11.5, weight="bold", y=1.06)

    out = FIG_DIR / "Fig3_forest_multivariate.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# SuppFig1 : Schoenfeld PH test
# ----------------------------------------------------------------------
def suppfig1_schoenfeld():
    df = pd.read_csv(DATA_V2_DIR / "schoenfeld.csv")
    LM = {
        "jlcm": "JLCM class (high-risk vs low-risk)",
        "ipi_high": "IPI ≥3",
        "mtv_log_base": "log10 baseline MTV",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, ep in zip(axes, ["efs", "os"]):
        sub = df[df["endpoint"] == ep].copy()
        sub["label"] = sub["var"].map(LM).fillna(sub["var"])
        order = ["JLCM class (high-risk vs low-risk)", "IPI ≥3", "log10 baseline MTV"]
        sub = sub.set_index("label").reindex(order).reset_index()
        y = np.arange(len(sub))
        colors = ["#2ca02c" if p > 0.05 else COLOR_HIGH for p in sub["p"]]
        ax.barh(y, sub["p"], color=colors, alpha=0.8, edgecolor="black")
        for yi, p in zip(y, sub["p"]):
            ax.text(min(p, 0.95) + 0.02, yi, f"p = {p:.3f}",
                    va="center", fontsize=10)
        ax.axvline(0.05, color=COLOR_HIGH, ls="--", lw=1.5, label="alpha = 0.05")
        ax.axvline(0.20, color="orange", ls=":", lw=1.2, label="conservative 0.20")
        ax.set_yticks(y)
        ax.set_yticklabels(sub["label"])
        ax.set_xlabel("Schoenfeld test p-value (rank time-transform)")
        ax.set_title(f"{ep.upper()} - PH assumption test")
        ax.set_xlim(0, 1.05)
        ax.grid(True, axis="x", alpha=0.3)
        if ep == "efs":
            ax.legend(loc="lower right", fontsize=9)

    plt.suptitle(
        "Schoenfeld proportional-hazards test - multivariable Cox v2 (all p > 0.20: PH holds)",
        fontsize=12, fontweight="bold")
    plt.tight_layout()
    out = FIG_DIR / "SuppFig1_schoenfeld.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# SuppFig6 : heatmap individual dynamics
# ----------------------------------------------------------------------
def suppfig6_heatmap_dynamics():
    long = pd.read_csv(DATA_DIR / "data_lcmm_long.csv")
    j14 = pd.read_csv(DATA_DIR / "jlcm_predict_j14.csv")
    TIMEPOINTS = ["J0", "J14", "M1", "M3", "M6", "M9", "M12"]
    wide = long.pivot_table(index="ID", columns="timepoint",
                            values="heg_log", aggfunc="mean").reindex(columns=TIMEPOINTS)
    j14_map = j14.set_index("ID")["group"].to_dict()
    efs_event = long.groupby("ID")["efs_event"].first().to_dict()
    wide["group"] = wide.index.map(j14_map)
    wide["event"] = wide.index.map(efs_event).astype("Int64")
    wide = wide[wide["group"].isin(["BON", "MAUVAIS"])]

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
    n_bon = (wide["group"] == "BON").sum()

    fig, ax = plt.subplots(figsize=(9, 9))
    im = ax.imshow(mat, aspect="auto", cmap="RdYlBu_r", vmin=-6, vmax=4,
                   interpolation="nearest")
    ax.set_xticks(range(len(TIMEPOINTS)))
    ax.set_xticklabels([{'J0':'D0','J14':'D14'}.get(t,t) for t in TIMEPOINTS])
    ax.set_xlabel("Timepoint")
    ax.set_ylabel(f"Patients (n={len(wide)}) - low-risk top, high-risk bottom")
    ax.set_title("Individual ctDNA dynamics (log10 hEG) by JLCM class")
    ax.axhline(n_bon - 0.5, color="black", lw=2)
    ax.text(-0.6, n_bon / 2, f"low-risk\n(n={n_bon})", rotation=90,
            va="center", ha="right", fontsize=11, fontweight="bold", color=COLOR_LOW)
    ax.text(-0.6, n_bon + (len(wide) - n_bon) / 2,
            f"high-risk\n(n={len(wide) - n_bon})", rotation=90,
            va="center", ha="right", fontsize=11, fontweight="bold", color=COLOR_HIGH)
    cbar = plt.colorbar(im, ax=ax, shrink=0.6)
    cbar.set_label("log10 hEG (floor = -6)")
    plt.tight_layout()
    out = FIG_DIR / "SuppFig6_heatmap_dynamics.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# SuppFig7 : forest subgroups
# ----------------------------------------------------------------------
def suppfig7_forest_subgroups():
    df = pd.read_csv(DATA_DIR / "subgroup_metrics.csv")
    int_csv = DATA_V2_DIR / "subgroup_interactions.csv"
    inter = pd.read_csv(int_csv) if int_csv.exists() else pd.DataFrame()
    if "endpoint" in df.columns:
        df = df[df["endpoint"].str.lower().str.startswith("efs")].copy()
    df = df.dropna(subset=["HR", "CI_low", "CI_up"]).copy()

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

    fig, ax = plt.subplots(figsize=(11, max(4, 0.55 * len(df))))
    y = np.arange(len(df))[::-1]
    for yi, (_, row) in zip(y, df.iterrows()):
        hr = float(row["HR"]); lo = float(row["CI_low"]); hi = float(row["CI_up"])
        ax.plot([lo, hi], [yi, yi], color="black", lw=1.5)
        ax.plot(hr, yi, "s", color=COLOR_HIGH, markersize=9)
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
            bullet.append(f"Interaction {sg}: p={p_efs:.3f} (Bonf p={p_adj:.3f})")
        ax.text(0.02, 0.02, "\n".join(bullet), transform=ax.transAxes,
                fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    plt.tight_layout()
    out = FIG_DIR / "SuppFig7_forest_subgroups.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {out.name}")


# ----------------------------------------------------------------------
# Combine Fig1 (1A + 1B) et Fig5 (5A + 5B)
# ----------------------------------------------------------------------
def combine_two_panels(panel_a_png, panel_b_png, out_stem,
                       title_a="", title_b=""):
    img_a = mpimg.imread(str(panel_a_png))
    img_b = mpimg.imread(str(panel_b_png))
    fig = plt.figure(figsize=(10, 12))
    gs = GridSpec(2, 1, figure=fig, hspace=0.08)
    ax_a = fig.add_subplot(gs[0]); ax_a.imshow(img_a); ax_a.axis("off")
    ax_a.set_title(title_a, loc="left", fontsize=12, fontweight="bold")
    ax_b = fig.add_subplot(gs[1]); ax_b.imshow(img_b); ax_b.axis("off")
    ax_b.set_title(title_b, loc="left", fontsize=12, fontweight="bold")
    fig.savefig(str(out_stem) + ".pdf", format="pdf", bbox_inches="tight")
    fig.savefig(str(out_stem) + ".png", format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"OK {Path(out_stem).name} (combined)")


def passthrough_pdf(src_png, out_stem, label=""):
    img = mpimg.imread(str(src_png))
    h, w = img.shape[:2]
    fig_w = 9
    fig_h = fig_w / (w / max(h, 1))
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img); ax.axis("off")
    if label:
        ax.text(0.01, 0.97, label, transform=ax.transAxes, fontsize=10,
                ha="left", va="top",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.85))
    fig.savefig(str(out_stem) + ".pdf", format="pdf", bbox_inches="tight")
    fig.savefig(str(out_stem) + ".png", format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"OK {Path(out_stem).name} (wrapped)")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    print(f"\n=== Regenerating ALYCANTE-Blood figures (low-risk/high-risk) ===")
    print(f"FIG_DIR : {FIG_DIR}\n")

    # === Régénération PNG sources ===
    fig1a_theoretical_curves()
    fig1b_observed_individual()
    fig2_km_landmark()
    fig3_forest_multivariate()
    fig5a_heatmap_concordance()
    fig5b_bimarker_forest()
    suppfig1_schoenfeld()
    suppfig6_heatmap_dynamics()
    suppfig7_forest_subgroups()

    # === Recombinaison ===
    combine_two_panels(
        FIG_DIR / "Fig1A_trajectories_theoretical.png",
        FIG_DIR / "Fig1B_trajectories_observed.png",
        FIG_DIR / "Fig1_trajectories_combined",
        title_a="A. Theoretical JLCM trajectories",
        title_b="B. Observed individual trajectories",
    )
    combine_two_panels(
        FIG_DIR / "Fig5A_ctdna_vs_mtv_kappa.png",
        FIG_DIR / "Fig5B_bimarker_forest.png",
        FIG_DIR / "Fig5_ctdna_vs_mtv_combined",
        title_a="A. ctDNA-JLCM vs MTV-JLCM concordance",
        title_b="B. Bi-marker Cox forest plot",
    )

    # === Wrap PDF des autres (sans label parasitique) ===
    for stem in ["Fig2_km_efs_os", "Fig3_forest_multivariate",
                 "Fig4_validation_lea",
                 "SuppFig1_schoenfeld", "SuppFig2_calibration_12m",
                 "SuppFig3_tdroc", "SuppFig4_dca_12m",
                 "SuppFig5_bootstrap_cindex",
                 "SuppFig6_heatmap_dynamics", "SuppFig7_forest_subgroups",
                 "SuppFig8_mrd_dynamics", "SuppFig9_time_to_mrd",
                 "SuppFig10_deauville_concordance"]:
        src = FIG_DIR / f"{stem}.png"
        if src.exists():
            passthrough_pdf(src, FIG_DIR / stem)

    print("\n[DONE] all figures regenerated")


if __name__ == "__main__":
    main()
