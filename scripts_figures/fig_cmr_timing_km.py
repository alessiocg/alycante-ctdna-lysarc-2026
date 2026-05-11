#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EFS KM par timing de la première CMR (précoce J14/M1, tardive M3-M12, jamais)"""
import os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import multivariate_logrank_test
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lifelines", "-q"])
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import multivariate_logrank_test

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUT_DIR  = BASE_DIR

NETWORK = (
    r"\\hmn-cifs-hnas.wprod.ds.aphp.fr\shares\IMMUNOLOGIE-BIOLOGIQUE"
    r"\SECTEUR MALADIES LYMPHOPROLIFERATIVES\D_PROTOCOLES\DLBCL"
    r"\protocole ALYCANTE\Réunion LYSARC 2026\output"
)

def copy_net(fname):
    try:
        import shutil
        shutil.copy2(fname, NETWORK)
    except Exception:
        pass

# --- Load data ---
df_main = pd.read_excel(os.path.join(DATA_DIR, "Donnees.xlsx"))
df_surv = pd.read_excel(os.path.join(DATA_DIR, "ALYCANTE_RNASeq_21OCT2025.xlsx"))

df_surv = df_surv.rename(columns={
    "Subject Identifier for the Study": "randomisation",
    "EFS from leukapheresis (months)":  "efs_time",
    "Event for EFS.1":                  "efs_event_bin",
    "Event for EFS":                    "efs_type",
})
df_surv["efs_event"] = (df_surv["efs_event_bin"] == "Yes").astype(int)
surv_cols = df_surv[["randomisation", "efs_time", "efs_event"]].copy()

# Exclude NI
ni_ids = df_main.loc[df_main["MRD_quali"] == "NI", "randomisation"].unique()
df = df_main[~df_main["randomisation"].isin(ni_ids)].copy()
df["MRD_quanti_heg"] = pd.to_numeric(df["MRD_quanti_heg"], errors="coerce")
df.loc[df["MRD_quali"] == "NEGATIF", "MRD_quanti_heg"] = 0.0

visite_map = {
    "Leucaph\u00e9r\u00e8se": "Leuca", "Leucaphérèse": "Leuca",
    "D-5": "J-5", "D0": "J0", "D14": "J14",
    "M1": "M1", "M3": "M3", "M6": "M6", "M9": "M9", "M12": "M12",
}
df["visite_label"] = df["visite"].map(visite_map).fillna(df["visite"])
df["is_cmr"] = df["MRD_quali"] == "NEGATIF"

# --- Style ---
plt.rcParams.update({
    "font.size": 11, "axes.facecolor": "white", "axes.edgecolor": "#333333",
    "axes.grid": True, "grid.color": "#dddddd", "grid.linestyle": "--",
    "grid.linewidth": 0.6, "legend.fontsize": 10, "axes.titlesize": 13,
    "axes.labelsize": 11,
})

# --- CMR timing groups ---
ALL_POST = ["J14", "M1", "M3", "M6", "M9", "M12"]
EARLY_TPS = {"J14", "M1"}

df_all_tp = df[df["visite_label"].isin(ALL_POST)].copy()

def cmr_timing_group(pid):
    pdata = df_all_tp[df_all_tp["randomisation"] == pid]
    for tp in ALL_POST:
        row = pdata[pdata["visite_label"] == tp]
        if len(row) > 0 and row["is_cmr"].iloc[0]:
            if tp in EARLY_TPS:
                return "CMR précoce"
            else:
                return "CMR tardive"
    return "Jamais CMR"

pat_surv = surv_cols.copy()
pat_surv = pat_surv[pat_surv["randomisation"].isin(df["randomisation"].unique())]
pat_surv["cmr_group"] = pat_surv["randomisation"].apply(cmr_timing_group)

group_counts = pat_surv["cmr_group"].value_counts()
print("CMR timing groups:\n", group_counts)

# --- KM curves ---
fig, (ax_km, ax_rt) = plt.subplots(
    2, 1, figsize=(10, 7),
    gridspec_kw={"height_ratios": [4, 1]},
    sharex=False
)

group_styles = {
    "CMR précoce":  {"color": "#1f77b4", "ls": "-"},
    "CMR tardive":  {"color": "#FF7F0E", "ls": "--"},
    "Jamais CMR":   {"color": "#DC2626", "ls": "-."},
}

kmfs = {}
for grp, style in group_styles.items():
    gdata = pat_surv[pat_surv["cmr_group"] == grp]
    if len(gdata) == 0:
        continue
    kmf = KaplanMeierFitter()
    kmf.fit(gdata["efs_time"], event_observed=gdata["efs_event"],
            label=f"{grp} (n={len(gdata)})")
    kmf.plot_survival_function(ax=ax_km, color=style["color"],
                                linestyle=style["ls"], linewidth=2,
                                ci_show=True, ci_alpha=0.12)
    kmfs[grp] = (kmf, gdata)

# Log-rank
groups_present = [g for g in group_styles if g in pat_surv["cmr_group"].values]
if len(groups_present) >= 2:
    results = multivariate_logrank_test(
        pat_surv["efs_time"], pat_surv["cmr_group"], pat_surv["efs_event"])
    p_val = results.p_value
    ax_km.text(0.98, 0.98,
               f"Log-rank p = {p_val:.4f}" if p_val >= 0.0001 else "Log-rank p < 0.0001",
               transform=ax_km.transAxes, ha="right", va="top", fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow",
                         edgecolor="#999", alpha=0.8))

ax_km.set_xlabel("Mois depuis leucaphérèse")
ax_km.set_ylabel("EFS probability")
ax_km.set_title("EFS selon le timing de la premi\u00e8re CMR (non landmark)\n(Pr\u00e9coce = CMR \u00e0 J14 ou M1 ; Tardive = CMR \u00e0 M3\u2013M12)")
ax_km.set_ylim(0, 1.05)
ax_km.set_xlim(0, 42)
ax_km.set_xticks(np.arange(0, 43, 6))
ax_km.set_xticklabels([f"{int(x)}" for x in np.arange(0, 43, 6)])

# Risk table
time_points_rt = np.arange(0, 45, 6)
y_positions = {"CMR précoce": 0.7, "CMR tardive": 0.35, "Jamais CMR": 0.0}
ax_rt.set_xlim(ax_km.get_xlim())
ax_rt.set_ylim(-0.2, 1.0)
ax_rt.spines['top'].set_visible(False)
ax_rt.spines['right'].set_visible(False)
ax_rt.spines['left'].set_visible(False)
ax_rt.spines['bottom'].set_visible(False)
ax_rt.set_yticks([])

for grp, style in group_styles.items():
    if grp not in kmfs:
        continue
    kmf, gdata = kmfs[grp]
    y_pos = y_positions[grp]
    ax_rt.text(-0.5, y_pos + 0.15, grp,
               transform=ax_rt.get_yaxis_transform(),
               ha="right", va="center", fontsize=8.5,
               color=style["color"], fontweight="bold")
    for t in time_points_rt:
        at_risk = (gdata["efs_time"] >= t).sum()
        ax_rt.text(t, y_pos + 0.15, str(at_risk),
                   ha="center", va="center", fontsize=8.5,
                   color=style["color"])

ax_rt.set_xticks([])
ax_rt.set_xlabel("")

fig.tight_layout()
outfile = os.path.join(OUT_DIR, "fig_cmr_timing_km.png")
fig.savefig(outfile, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {outfile}")
copy_net(outfile)
print("Done.")
