#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ΔctDNA waterfall plot (Leuca → M3) — 3 groupes R/R"""
import os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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
# Correction J0
def _parse_dt(v):
    s = str(v).strip()
    try:
        n = float(s.replace(',', '.'))
        return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(n))
    except Exception:
        for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d']:
            try: return pd.to_datetime(s, format=fmt)
            except: pass
    return pd.NaT
df_surv['_dl'] = df_surv['Start of leukapheresis'].apply(_parse_dt)
df_surv['_dj'] = df_surv['Date of Axi-cel infusion (numeric)'].apply(_parse_dt)
df_surv['efs_time'] = df_surv['efs_time'] - (df_surv['_dj'] - df_surv['_dl']).dt.days / 30.44

df_surv["efs_event"] = (df_surv["efs_event_bin"] == "Yes").astype(int)
df_surv["rr_12"] = (
    (df_surv["efs_event"] == 1)
    & (df_surv["efs_time"] <= 12)
    & df_surv["efs_type"].str.contains("Progression|Relapse", na=False)
)
df_surv["rr_24"] = (
    (df_surv["efs_event"] == 1)
    & (df_surv["efs_time"] <= 24)
    & df_surv["efs_type"].str.contains("Progression|Relapse", na=False)
)
surv_cols = df_surv[["randomisation", "rr_12", "rr_24"]].copy()

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
df = df.merge(surv_cols, on="randomisation", how="left")
df["rr_12"] = df["rr_12"].fillna(False)
df["rr_24"] = df["rr_24"].fillna(False)

# --- Style ---
plt.rcParams.update({
    "font.size": 11, "axes.facecolor": "white", "axes.edgecolor": "#333333",
    "axes.grid": True, "grid.color": "#dddddd", "grid.linestyle": "--",
    "grid.linewidth": 0.6, "legend.fontsize": 10, "axes.titlesize": 13,
    "axes.labelsize": 11,
})

# --- Waterfall ---
leuca_data = df[df["visite_label"] == "Leuca"][["randomisation", "MRD_quanti_heg", "rr_12", "rr_24"]].copy()
leuca_data.columns = ["randomisation", "heg_leuca", "rr_12", "rr_24"]
leuca_data = leuca_data.dropna(subset=["heg_leuca"])
leuca_data = leuca_data[leuca_data["heg_leuca"] > 0]

m1_data = df[df["visite_label"] == "M1"][["randomisation", "MRD_quanti_heg"]].copy()
m1_data.columns = ["randomisation", "heg_m1"]
m1_data = m1_data.dropna(subset=["heg_m1"])

waterfall = leuca_data.merge(m1_data, on="randomisation", how="inner")
waterfall["delta"] = waterfall["heg_m1"] - waterfall["heg_leuca"]

def rr_group(row):
    if row["rr_12"]:
        return "R/R 0\u201312m"
    elif row["rr_24"] and not row["rr_12"]:
        return "R/R 12\u201324m"
    else:
        return "Pas de R/R"

waterfall["rr_group"] = waterfall.apply(rr_group, axis=1)
waterfall = waterfall.sort_values("delta")

COLOR_RR_012 = "#DC2626"
COLOR_RR_1224 = "#FF8F00"
COLOR_NO_RR = "#1565C0"
color_map = {"R/R 0\u201312m": COLOR_RR_012, "R/R 12\u201324m": COLOR_RR_1224, "Pas de R/R": COLOR_NO_RR}

print(f"Patients in waterfall: {len(waterfall)}")
for grp in ["R/R 0\u201312m", "R/R 12\u201324m", "Pas de R/R"]:
    print(f"  {grp}: {(waterfall['rr_group'] == grp).sum()}")

fig, ax = plt.subplots(figsize=(14, 6))
bar_colors = waterfall["rr_group"].map(color_map).values

SEUIL = -3.0
# Separate BON (delta <= seuil) and MAUVAIS (delta > seuil) with a gap
bon_idx = waterfall[waterfall["delta"] <= SEUIL].index
mauv_idx = waterfall[waterfall["delta"] > SEUIL].index
n_bon = len(bon_idx)
n_mauv = len(mauv_idx)
GAP = 2  # gap between groups

# Positions: BON on left, gap, MAUVAIS on right
positions = list(range(n_bon)) + list(range(n_bon + GAP, n_bon + GAP + n_mauv))
all_deltas = list(waterfall.loc[bon_idx, "delta"].values) + list(waterfall.loc[mauv_idx, "delta"].values)
all_colors = list(waterfall.loc[bon_idx, "rr_group"].map(color_map).values) + \
             list(waterfall.loc[mauv_idx, "rr_group"].map(color_map).values)

ax.bar(positions, all_deltas, color=all_colors, edgecolor="white", linewidth=0.4, alpha=0.88)
ax.axhline(y=0, color="black", linewidth=1.2, zorder=5)

# Seuil horizontal
ax.axhline(y=SEUIL, color="black", linewidth=1.5, linestyle="--", zorder=4)
ax.text(len(waterfall) + GAP + 1, SEUIL + 0.1, f"Seuil = {SEUIL:.1f}", fontsize=9,
        fontweight="bold", va="bottom")

# Labels BON / MAUVAIS
ax.text(n_bon / 2, ax.get_ylim()[0] + 0.15, f"BON (n={n_bon})",
        ha="center", fontsize=10, fontweight="bold", color="#1565C0")
ax.text(n_bon + GAP + n_mauv / 2, ax.get_ylim()[0] + 0.15, f"MAUVAIS (n={n_mauv})",
        ha="center", fontsize=10, fontweight="bold", color="#C62828")

patch_012 = mpatches.Patch(color=COLOR_RR_012, label="R/R 0\u201312m")
patch_1224 = mpatches.Patch(color=COLOR_RR_1224, label="R/R 12\u201324m")
patch_no = mpatches.Patch(color=COLOR_NO_RR, label="Pas de R/R")
ax.legend(handles=[patch_012, patch_1224, patch_no], loc="upper left")

ax.set_xlabel("Patients (tri\u00e9s par \u0394ctDNA croissant)")
ax.set_ylabel("\u0394ctDNA = hEG(M1) \u2212 hEG(Leuca)")
ax.set_title(f"\u0394ctDNA (Leuca\u2192M1) \u2014 Waterfall plot (n={len(waterfall)}, seuil = m\u00e9diane = \u22123.0)")
ax.set_xticks([])

fig.tight_layout()
outfile = os.path.join(OUT_DIR, "fig_delta_ctdna_waterfall.png")
fig.savefig(outfile, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {outfile}")
copy_net(outfile)
print("Done.")
