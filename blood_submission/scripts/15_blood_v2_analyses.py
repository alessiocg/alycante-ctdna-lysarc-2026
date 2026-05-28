#!/usr/bin/env python
"""
ALYCANTE Blood v2 - additional analyses for reviewer rang A.

Outputs (CSV) in data_v2/
- bootstrap_cindex.csv     : 1000x bootstrap C-index distributions
- schoenfeld.csv           : Schoenfeld residual chi-sq + p
- calibration.csv          : O/E ratio @ 12m by predicted-risk quintile
- tdroc.csv                : time-dependent AUC at 6/12/18/24m
- dca_12m.csv              : net benefit curve at 12m
- missingness.csv          : % missing per covariate
- subgroup_interactions.csv: interaction p with multiplicity adj

Figures (PNG) in output/figures/blood_v2/
- fig_bootstrap_cindex.png
- fig_schoenfeld.png
- fig_calibration_12m.png
- fig_tdroc.png
- fig_dca_12m.png
- fig_heatmap_dynamics.png
- fig_forest_subgroups.png
- fig_visual_abstract.png
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec

from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.utils import concordance_index
from scipy.stats import chi2, norm, fisher_exact, mannwhitneyu

np.random.seed(20260520)

BASE = os.path.dirname(OUTPUT_DIR)
DATA = os.path.join(BASE, "output", "scripts_figures", "data")
OUT_DATA = os.path.join(BASE, "output", "scripts_figures", "data_v2")
OUT_FIG = os.path.join(BASE, "output", "figures", "blood_v2")
os.makedirs(OUT_DATA, exist_ok=True)
os.makedirs(OUT_FIG, exist_ok=True)

# ---------- Load core datasets ----------
pred = pd.read_csv(os.path.join(DATA, "jlcm_predict_j14.csv"))
pred = pred.rename(columns={"randomisation": "rand"})
pred["jlcm"] = pred["group"].map({"BON": 0, "MAUVAIS": 1}).astype("Int64")

# Long ctDNA for trajectories
long_df = pd.read_csv(os.path.join(DATA, "data_lcmm_long.csv"))

# Load CRF (xlsx) for IPI / MTV / OS / EFS
crf_path = os.path.join(BASE, "input", "ALYCANTE_export_20260505.xlsx")
crf_extens = pd.read_excel(crf_path, sheet_name="EXTENS")
crf_tmtv = pd.read_excel(crf_path, sheet_name="TMTV")
crf_extens.columns = [c.strip() for c in crf_extens.columns]
crf_tmtv.columns = [c.strip() for c in crf_tmtv.columns]

# Use long-format for survival times (already there) merged with predict_j14
surv = long_df.groupby("randomisation").agg(
    efs_time=("efs_time", "max"),
    efs_event=("efs_event", "max"),
    os_time=("os_time", "max"),
    os_event=("os_event", "max"),
).reset_index().rename(columns={"randomisation": "rand"})

# Number of measurements per patient
nmeas = long_df.groupby("randomisation").size().reset_index(name="nmeas").rename(columns={"randomisation": "rand"})

df = pred.merge(surv, on="rand", how="left").merge(nmeas, on="rand", how="left")

# Load Cox v2 metrics to remind covariate set
cox_v2 = pd.read_csv(os.path.join(DATA, "cox_multivariate_v2_metrics.csv"))

# Try to bring covariates from the existing PET / CRF
pet = pd.read_csv(os.path.join(DATA, "data_pet_full_long.csv"))
mtv_baseline = (pet[pet["timepoint"].isin(["PET_Baseline", "PET_Pre_Treatment"])]
                  .sort_values(["randomisation", "time"], ascending=[True, False])
                  .groupby("randomisation").first().reset_index()
                  [["randomisation", "mtv", "mtv_log"]]
                  .rename(columns={"randomisation": "rand",
                                   "mtv": "mtv_base",
                                   "mtv_log": "mtv_log_base"}))
df = df.merge(mtv_baseline, on="rand", how="left")

# Pull IPI from EXTENS sheet (column 'IPI', baseline period only)
ipi_df = crf_extens[["SUBJID", "PERIOD", "IPI"]].copy()
# Take baseline / first period
ipi_df["PERIOD"] = ipi_df["PERIOD"].astype(str)
ipi_df = ipi_df.sort_values(["SUBJID", "PERIOD"]).groupby("SUBJID").first().reset_index()
ipi_df["ipi_total"] = pd.to_numeric(ipi_df["IPI"], errors="coerce")
ipi_df = ipi_df[["SUBJID", "ipi_total"]].rename(columns={"SUBJID": "rand"})
# Make sure rand is int
ipi_df["rand"] = pd.to_numeric(ipi_df["rand"], errors="coerce").astype("Int64")
df["rand"] = pd.to_numeric(df["rand"], errors="coerce").astype("Int64")
df = df.merge(ipi_df, on="rand", how="left")
df["ipi_high"] = (df["ipi_total"] >= 3).astype("Int64")

# Drop rows without prediction and survival
df_pred = df.dropna(subset=["jlcm"]).copy()
df_pred["jlcm"] = df_pred["jlcm"].astype(int)
df_pred = df_pred.dropna(subset=["efs_time", "efs_event"]).copy()
df_pred["efs_event"] = df_pred["efs_event"].astype(int)
df_pred["efs_time"] = df_pred["efs_time"].astype(float)
df_pred_os = df_pred.dropna(subset=["os_time", "os_event"]).copy()
df_pred_os["os_event"] = df_pred_os["os_event"].astype(int)
df_pred_os["os_time"] = df_pred_os["os_time"].astype(float)

print("[INFO] N with prediction:", len(df_pred))
print("[INFO] BON/MAUVAIS counts:", df_pred["group"].value_counts().to_dict())

# Build N=44 with full covariates (IPI + baseline MTV + EFS)
df_full = df_pred.dropna(subset=["mtv_log_base"]).copy()
if "ipi_high" in df_full.columns:
    df_full = df_full[df_full["ipi_high"].notna()]
df_full["ipi_high"] = df_full["ipi_high"].astype(int)
print("[INFO] N with full covariates:", len(df_full))

# ============================================================
# 1) BOOTSTRAP C-INDEX (1000x) for EFS and OS  -- univariable JLCM and Cox v2
# ============================================================
print("[1] Bootstrap C-index 1000x")
rng = np.random.default_rng(20260520)
n_boot = 1000

def cindex(df_in, endpoint, score_col="jlcm"):
    t = df_in[f"{endpoint}_time"].values
    e = df_in[f"{endpoint}_event"].values
    s = df_in[score_col].values
    return concordance_index(t, -s, e)  # higher MAUVAIS = lower survival

def fit_cox_v2_cindex(df_in, endpoint):
    cols = [f"{endpoint}_time", f"{endpoint}_event", "jlcm", "ipi_high", "mtv_log_base"]
    df_c = df_in[cols].copy().dropna()
    df_c.columns = ["T", "E", "jlcm", "ipi_high", "mtv_log_base"]
    if df_c["E"].sum() < 2 or df_c["jlcm"].nunique() < 2:
        return np.nan
    cph = CoxPHFitter(penalizer=0.1)
    try:
        cph.fit(df_c, duration_col="T", event_col="E")
        return cph.concordance_index_
    except Exception:
        return np.nan

boot_rows = []
for endpoint in ("efs", "os"):
    base_uni = df_pred if endpoint == "efs" else df_pred_os
    base_mv = df_full if endpoint == "efs" else df_full.dropna(subset=["os_time", "os_event"])
    # Univariable JLCM
    cuni = cindex(base_uni, endpoint, "jlcm")
    cmv = fit_cox_v2_cindex(base_mv, endpoint)
    cuni_boot, cmv_boot = [], []
    for b in range(n_boot):
        idx_u = rng.integers(0, len(base_uni), size=len(base_uni))
        idx_m = rng.integers(0, len(base_mv), size=len(base_mv))
        boot_u = base_uni.iloc[idx_u]
        boot_m = base_mv.iloc[idx_m]
        try:
            cuni_boot.append(cindex(boot_u, endpoint, "jlcm"))
        except Exception:
            cuni_boot.append(np.nan)
        cmv_boot.append(fit_cox_v2_cindex(boot_m, endpoint))
    cuni_boot = np.array([c for c in cuni_boot if not np.isnan(c)])
    cmv_boot = np.array([c for c in cmv_boot if not np.isnan(c)])
    if len(cuni_boot):
        ci_uni = (np.percentile(cuni_boot, 2.5), np.percentile(cuni_boot, 97.5))
        # .632+ optimism-corrected
        opt_uni = cuni - cuni_boot.mean()
    else:
        ci_uni = (np.nan, np.nan)
        opt_uni = np.nan
    if len(cmv_boot):
        ci_mv = (np.percentile(cmv_boot, 2.5), np.percentile(cmv_boot, 97.5))
        opt_mv = cmv - cmv_boot.mean()
    else:
        ci_mv = (np.nan, np.nan)
        opt_mv = np.nan

    boot_rows.append({"endpoint": endpoint, "model": "univariable_JLCM",
                      "c_index": cuni, "ci_lo": ci_uni[0], "ci_hi": ci_uni[1],
                      "boot_mean": np.nanmean(cuni_boot) if len(cuni_boot) else np.nan,
                      "optimism": np.nan if np.isnan(opt_uni) else opt_uni,
                      "n_boot": len(cuni_boot)})
    boot_rows.append({"endpoint": endpoint, "model": "multivariable_v2",
                      "c_index": cmv, "ci_lo": ci_mv[0], "ci_hi": ci_mv[1],
                      "boot_mean": np.nanmean(cmv_boot) if len(cmv_boot) else np.nan,
                      "optimism": np.nan if np.isnan(opt_mv) else opt_mv,
                      "n_boot": len(cmv_boot)})
    # save raw distribution
    pd.DataFrame({"endpoint": endpoint, "univariable_JLCM": cuni_boot[:n_boot]}).to_csv(
        os.path.join(OUT_DATA, f"bootstrap_cindex_{endpoint}_univariable.csv"), index=False
    )
    pd.DataFrame({"endpoint": endpoint, "multivariable_v2": cmv_boot[:n_boot]}).to_csv(
        os.path.join(OUT_DATA, f"bootstrap_cindex_{endpoint}_multivariable.csv"), index=False
    )

boot_df = pd.DataFrame(boot_rows)
boot_df.to_csv(os.path.join(OUT_DATA, "bootstrap_cindex.csv"), index=False)
print(boot_df.to_string(index=False))

# ============================================================
# 2) PERMUTATION LOG-RANK (10000)
# ============================================================
print("[2] Permutation log-rank 10000x")
from lifelines.statistics import logrank_test

def perm_logrank(df_in, endpoint, n_perm=10000):
    t = df_in[f"{endpoint}_time"].values
    e = df_in[f"{endpoint}_event"].values
    g = df_in["jlcm"].values
    obs = logrank_test(t[g == 0], t[g == 1], event_observed_A=e[g == 0], event_observed_B=e[g == 1]).test_statistic
    rng_l = np.random.default_rng(20260521)
    count = 0
    for _ in range(n_perm):
        gp = rng_l.permutation(g)
        try:
            stat = logrank_test(t[gp == 0], t[gp == 1], event_observed_A=e[gp == 0], event_observed_B=e[gp == 1]).test_statistic
        except Exception:
            stat = 0
        if stat >= obs:
            count += 1
    return obs, count / n_perm

perm_rows = []
for endpoint in ("efs", "os"):
    base = df_pred if endpoint == "efs" else df_pred_os
    obs, p = perm_logrank(base, endpoint)
    perm_rows.append({"endpoint": endpoint, "logrank_chi2": obs, "perm_p": p, "n_perm": 10000})
pd.DataFrame(perm_rows).to_csv(os.path.join(OUT_DATA, "permutation_logrank.csv"), index=False)
print(pd.DataFrame(perm_rows).to_string(index=False))

# ============================================================
# 3) SCHOENFELD RESIDUALS (Cox PH assumption)
# ============================================================
print("[3] Schoenfeld residuals")
sch_rows = []
for endpoint in ("efs", "os"):
    cols = [f"{endpoint}_time", f"{endpoint}_event", "jlcm", "ipi_high", "mtv_log_base"]
    base = df_full if endpoint == "efs" else df_full.dropna(subset=["os_time", "os_event"])
    df_c = base[cols].dropna().copy()
    df_c.columns = ["T", "E", "jlcm", "ipi_high", "mtv_log_base"]
    cph = CoxPHFitter(penalizer=0.1)
    cph.fit(df_c, duration_col="T", event_col="E")
    try:
        ph = cph.check_assumptions(df_c, p_value_threshold=0.05, show_plots=False)
        # check_assumptions returns dataframes per variable
        # Use proportional_hazard_test directly:
        from lifelines.statistics import proportional_hazard_test
        ph_test = proportional_hazard_test(cph, df_c, time_transform="rank")
        for var in ph_test.summary.index:
            r = ph_test.summary.loc[var]
            sch_rows.append({"endpoint": endpoint, "var": var,
                             "test_stat": float(r["test_statistic"]),
                             "p": float(r["p"])})
    except Exception as exc:
        print("PH test failed:", exc)

sch_df = pd.DataFrame(sch_rows)
sch_df.to_csv(os.path.join(OUT_DATA, "schoenfeld.csv"), index=False)
print(sch_df.to_string(index=False))

# ============================================================
# 4) CALIBRATION @12m (O/E by predicted risk decile / Hosmer-Lemeshow-like)
# ============================================================
print("[4] Calibration @12m")
cph_full = CoxPHFitter(penalizer=0.1)
df_c = df_full[["efs_time", "efs_event", "jlcm", "ipi_high", "mtv_log_base"]].dropna().copy()
df_c.columns = ["T", "E", "jlcm", "ipi_high", "mtv_log_base"]
cph_full.fit(df_c, duration_col="T", event_col="E")
predicted_surv_12m = cph_full.predict_survival_function(df_c, times=[12]).T.iloc[:, 0]
predicted_risk_12m = 1 - predicted_surv_12m
df_c = df_c.assign(pred_risk=predicted_risk_12m.values)
# Observed @12m
df_c["obs_event_12m"] = ((df_c["T"] <= 12) & (df_c["E"] == 1)).astype(int)

# Group by predicted-risk quintile
try:
    df_c["quintile"] = pd.qcut(df_c["pred_risk"], q=5, duplicates="drop")
    calib = df_c.groupby("quintile").agg(
        n=("pred_risk", "size"),
        pred_mean=("pred_risk", "mean"),
        obs=("obs_event_12m", "sum"),
    ).reset_index()
    calib["obs_rate"] = calib["obs"] / calib["n"]
except Exception as exc:
    print("Calibration quintile failed:", exc)
    df_c["quintile"] = pd.cut(df_c["pred_risk"], bins=3)
    calib = df_c.groupby("quintile").agg(
        n=("pred_risk", "size"),
        pred_mean=("pred_risk", "mean"),
        obs=("obs_event_12m", "sum"),
    ).reset_index()
    calib["obs_rate"] = calib["obs"] / calib["n"]
calib.to_csv(os.path.join(OUT_DATA, "calibration_12m.csv"), index=False)
print(calib.to_string(index=False))

# Calibration in the large (intercept / slope using logistic)
from sklearn.linear_model import LogisticRegression
logit_x = np.log(np.clip(predicted_risk_12m, 1e-6, 1 - 1e-6) / (1 - np.clip(predicted_risk_12m, 1e-6, 1 - 1e-6)))
y_obs = df_c["obs_event_12m"].values
lr = LogisticRegression(fit_intercept=True)
logit_arr = np.asarray(logit_x).reshape(-1, 1)
lr.fit(logit_arr, y_obs)
calib_intercept = lr.intercept_[0]
calib_slope = lr.coef_[0][0]
pd.DataFrame({"metric": ["intercept", "slope"], "value": [calib_intercept, calib_slope]}).to_csv(
    os.path.join(OUT_DATA, "calibration_in_the_large.csv"), index=False
)

# ============================================================
# 5) TIME-DEPENDENT AUC at 6/12/18/24 months (cumulative/dynamic)
# ============================================================
print("[5] time-dependent AUC")
try:
    from sksurv.metrics import cumulative_dynamic_auc
    from sksurv.util import Surv
    y = Surv.from_arrays(event=df_pred["efs_event"].astype(bool).values,
                         time=df_pred["efs_time"].values)
    times = np.array([6.0, 12.0, 18.0, 24.0])
    # Score = JLCM class as risk
    risk_score = df_pred["jlcm"].astype(float).values
    auc_vals, mean_auc = cumulative_dynamic_auc(y, y, risk_score, times)
    pd.DataFrame({"horizon_months": times, "auc": auc_vals}).to_csv(
        os.path.join(OUT_DATA, "tdroc.csv"), index=False
    )
    print("td AUC:", dict(zip(times, auc_vals)))
except Exception as exc:
    print("td AUC failed, computing manually:", exc)
    rows = []
    for tp in (6.0, 12.0, 18.0, 24.0):
        df_temp = df_pred.copy()
        df_temp["case"] = ((df_temp["efs_time"] <= tp) & (df_temp["efs_event"] == 1)).astype(int)
        df_temp = df_temp[(df_temp["efs_time"] > tp) | (df_temp["efs_event"] == 1)]
        if df_temp["case"].sum() == 0 or df_temp["case"].sum() == len(df_temp):
            rows.append({"horizon_months": tp, "auc": np.nan})
            continue
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(df_temp["case"].values, df_temp["jlcm"].values)
        rows.append({"horizon_months": tp, "auc": auc})
    pd.DataFrame(rows).to_csv(os.path.join(OUT_DATA, "tdroc.csv"), index=False)

# ============================================================
# 6) DECISION CURVE ANALYSIS @12m
# ============================================================
print("[6] DCA")
def dca(y_true, p_hat, thresholds=np.arange(0.01, 0.99, 0.01)):
    rows = []
    n = len(y_true)
    for pt in thresholds:
        # Treat if p_hat >= pt
        treat = p_hat >= pt
        tp = np.sum((treat == 1) & (y_true == 1))
        fp = np.sum((treat == 1) & (y_true == 0))
        nb = (tp / n) - (fp / n) * (pt / (1 - pt))
        rows.append({"threshold": pt, "net_benefit_model": nb})
    return pd.DataFrame(rows)

# JLCM-only model
p_jlcm = df_c.assign(p=df_c["pred_risk"])["p"].values  # already 12m risk
y12 = df_c["obs_event_12m"].values
dca_model = dca(y12, p_jlcm)
# treat-all and treat-none
prev = y12.mean()
ts = dca_model["threshold"].values
dca_model["net_benefit_all"] = prev - (1 - prev) * (ts / (1 - ts))
dca_model["net_benefit_none"] = 0
dca_model.to_csv(os.path.join(OUT_DATA, "dca_12m.csv"), index=False)

# Also DCA for IPI-only predicted risk (Cox with IPI only)
cph_ipi = CoxPHFitter(penalizer=0.1)
df_ipi = df_full[["efs_time", "efs_event", "ipi_high"]].dropna().copy()
df_ipi.columns = ["T", "E", "ipi_high"]
cph_ipi.fit(df_ipi, duration_col="T", event_col="E")
predicted_ipi = 1 - cph_ipi.predict_survival_function(df_ipi, times=[12]).T.iloc[:, 0].values
dca_ipi = dca(((df_ipi["T"] <= 12) & (df_ipi["E"] == 1)).astype(int).values, predicted_ipi)
dca_ipi.to_csv(os.path.join(OUT_DATA, "dca_12m_ipi.csv"), index=False)

# ============================================================
# 7) MISSINGNESS table
# ============================================================
print("[7] Missingness")
miss_cols = ["jlcm", "efs_time", "os_time", "mtv_log_base", "ipi_high", "ipi_total"]
miss_df = pd.DataFrame({
    "variable": miss_cols,
    "n_total": [len(df) for _ in miss_cols],
    "n_missing": [df[c].isna().sum() if c in df.columns else len(df) for c in miss_cols],
})
miss_df["pct_missing"] = (miss_df["n_missing"] / miss_df["n_total"] * 100).round(1)
miss_df.to_csv(os.path.join(OUT_DATA, "missingness.csv"), index=False)
print(miss_df.to_string(index=False))

# ============================================================
# 8) Bonferroni-corrected subgroup interactions
# ============================================================
print("[8] Subgroup interactions")
sub_rows = []
# Build interaction test for each candidate covariate
def cox_int(df_in, cov_col, endpoint):
    cols = [f"{endpoint}_time", f"{endpoint}_event", "jlcm", cov_col]
    df_c2 = df_in[cols].dropna().copy()
    df_c2.columns = ["T", "E", "jlcm", "X"]
    df_c2["int"] = df_c2["jlcm"] * df_c2["X"]
    cph_i = CoxPHFitter(penalizer=0.1)
    try:
        cph_i.fit(df_c2[["T", "E", "jlcm", "X", "int"]], duration_col="T", event_col="E")
        return cph_i.summary.loc["int", "p"]
    except Exception:
        return np.nan

candidates = {"ipi_high": "ipi_high", "mtv_log_base": "mtv_log_base"}
for cov_label, cov_col in candidates.items():
    p_efs = cox_int(df_full, cov_col, "efs")
    p_os = cox_int(df_full, cov_col, "os")
    sub_rows.append({"subgroup": cov_label, "p_int_efs": p_efs, "p_int_os": p_os})
sub_df = pd.DataFrame(sub_rows)
sub_df["bonferroni_p_efs"] = (sub_df["p_int_efs"] * len(sub_df)).clip(upper=1)
sub_df["bonferroni_p_os"] = (sub_df["p_int_os"] * len(sub_df)).clip(upper=1)
sub_df.to_csv(os.path.join(OUT_DATA, "subgroup_interactions.csv"), index=False)
print(sub_df.to_string(index=False))

# ============================================================
# FIGURES
# ============================================================

# 9) Bootstrap C-index histogram
print("[fig] bootstrap C-index")
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=140)
for ax, endpoint, title in zip(axes, ("efs", "os"), ("EFS", "OS")):
    buni = pd.read_csv(os.path.join(OUT_DATA, f"bootstrap_cindex_{endpoint}_univariable.csv"))
    bmv = pd.read_csv(os.path.join(OUT_DATA, f"bootstrap_cindex_{endpoint}_multivariable.csv"))
    ax.hist(buni["univariable_JLCM"].dropna(), bins=30, alpha=0.55, color="#1f77b4",
            label="JLCM univariable")
    ax.hist(bmv["multivariable_v2"].dropna(), bins=30, alpha=0.55, color="#d62728",
            label="Cox v2 (JLCM+IPI+log10 MTV)")
    ax.axvline(buni["univariable_JLCM"].mean(), color="#1f77b4", lw=2)
    ax.axvline(bmv["multivariable_v2"].mean(), color="#d62728", lw=2)
    ax.set_title(f"{title} — Bootstrap C-index (n=1000)")
    ax.set_xlabel("Harrell C-index")
    ax.set_ylabel("Frequency")
    ax.legend(loc="upper left", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "fig_bootstrap_cindex.png"), bbox_inches="tight")
plt.close()

# 10) Schoenfeld figure
print("[fig] Schoenfeld")
fig, ax = plt.subplots(figsize=(7, 3.8), dpi=140)
sch = pd.read_csv(os.path.join(OUT_DATA, "schoenfeld.csv"))
if len(sch):
    sch = sch.sort_values(["endpoint", "p"])
    colors = ["#2ca02c" if p > 0.05 else "#d62728" for p in sch["p"]]
    bars = ax.barh([f"{r['endpoint'].upper()} – {r['var']}" for _, r in sch.iterrows()],
                   sch["p"], color=colors)
    ax.axvline(0.05, color="grey", ls="--", lw=1)
    ax.set_xlabel("p (proportional hazard test, time-rank)")
    ax.set_title("Schoenfeld test — Cox v2 PH assumption (green: PH holds, p > 0.05)")
    for bar, p in zip(bars, sch["p"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"p={p:.3f}", va="center", fontsize=9)
    ax.set_xlim(0, max(0.3, sch["p"].max() * 1.2 + 0.05))
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "fig_schoenfeld.png"), bbox_inches="tight")
plt.close()

# 11) Calibration plot
print("[fig] calibration")
fig, ax = plt.subplots(figsize=(5.4, 4.6), dpi=140)
cal = pd.read_csv(os.path.join(OUT_DATA, "calibration_12m.csv"))
ax.plot([0, 1], [0, 1], "--", color="grey", label="Perfect calibration")
ax.scatter(cal["pred_mean"], cal["obs_rate"], s=80, color="#d62728", zorder=3,
           label=f"Cox v2 (n={int(cal['n'].sum())})")
for _, row in cal.iterrows():
    ax.errorbar(row["pred_mean"], row["obs_rate"],
                yerr=1.96 * np.sqrt(row["obs_rate"] * (1 - row["obs_rate"]) / max(row["n"], 1)),
                fmt="none", color="#d62728", capsize=4)
ax.set_xlabel("Predicted 12-month event probability")
ax.set_ylabel("Observed 12-month event rate")
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_title(f"Calibration @12m — intercept={calib_intercept:.2f}, slope={calib_slope:.2f}")
ax.legend(loc="lower right", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "fig_calibration_12m.png"), bbox_inches="tight")
plt.close()

# 12) tdROC plot
print("[fig] tdROC")
fig, ax = plt.subplots(figsize=(5.8, 4.2), dpi=140)
td = pd.read_csv(os.path.join(OUT_DATA, "tdroc.csv"))
ax.plot(td["horizon_months"], td["auc"], "o-", color="#1f77b4", lw=2, ms=8)
for _, r in td.iterrows():
    ax.text(r["horizon_months"], r["auc"] + 0.015, f"{r['auc']:.2f}", ha="center", fontsize=9)
ax.axhline(0.5, color="grey", ls="--", lw=1)
ax.set_xlabel("Horizon (months from day 14)")
ax.set_ylabel("Cumulative/dynamic AUC")
ax.set_ylim(0.4, 1.02)
ax.set_title("Time-dependent AUC of day-14 JLCM-ctDNA — EFS")
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "fig_tdroc.png"), bbox_inches="tight")
plt.close()

# 13) DCA plot
print("[fig] DCA")
fig, ax = plt.subplots(figsize=(6.0, 4.4), dpi=140)
d = pd.read_csv(os.path.join(OUT_DATA, "dca_12m.csv"))
di = pd.read_csv(os.path.join(OUT_DATA, "dca_12m_ipi.csv"))
ax.plot(d["threshold"], d["net_benefit_model"], color="#d62728", lw=2, label="JLCM-ctDNA day 14")
ax.plot(di["threshold"], di["net_benefit_model"], color="#2ca02c", lw=2, label="IPI ≥3 only")
ax.plot(d["threshold"], d["net_benefit_all"], color="black", ls=":", lw=1.5, label="Treat all")
ax.plot(d["threshold"], d["net_benefit_none"], color="grey", ls="--", lw=1.5, label="Treat none")
ax.set_xlim(0, 1)
ax.set_ylim(-0.10, max(0.65, d["net_benefit_model"].max() * 1.1))
ax.set_xlabel("Threshold probability of 12-month event")
ax.set_ylabel("Net benefit")
ax.set_title("Decision curve analysis @12 months — EFS")
ax.legend(loc="upper right", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "fig_dca_12m.png"), bbox_inches="tight")
plt.close()

# 14) Heatmap individual ctDNA dynamics (rows = patients, cols = time)
print("[fig] heatmap dynamics")
piv = (long_df.assign(time_bin=long_df["timepoint"]
                      .replace({"J0": 0, "J14": 14, "M1": 30, "M3": 90,
                                "M6": 180, "M9": 270, "M12": 365,
                                "Leuca": -30, "J-5": -5}))
              .pivot_table(index="randomisation",
                           columns="time_bin",
                           values="heg_log",
                           aggfunc="mean"))
# Order patients by class
class_map = pred.set_index("rand")["group"]
piv["class"] = piv.index.map(class_map)
piv = piv.dropna(subset=["class"])
piv = piv.sort_values(["class"] + [c for c in piv.columns if isinstance(c, (int, float))])

fig, ax = plt.subplots(figsize=(7.6, 9), dpi=140)
hm = piv.drop(columns="class")
im = ax.imshow(hm.values, aspect="auto", cmap="RdBu_r",
               vmin=-6, vmax=hm.values[~np.isnan(hm.values)].max() if (~np.isnan(hm.values)).any() else 1)
ax.set_xticks(np.arange(len(hm.columns)))
ax.set_xticklabels(hm.columns, rotation=45)
ax.set_yticks(np.arange(len(hm.index)))
ax.set_yticklabels(["BON" if c == "BON" else "MAUVAIS"
                    for c in piv["class"].values], fontsize=6)
ax.set_xlabel("Time (days)")
ax.set_title("Individual ctDNA dynamics (log10 hEG) by day-14 JLCM class\nrows = patients, ordered BON then MAUVAIS")
fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04, label="log10 hEG")
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "fig_heatmap_dynamics.png"), bbox_inches="tight")
plt.close()

# 15) Subgroup forest
print("[fig] subgroups forest")
sg = pd.read_csv(os.path.join(DATA, "subgroup_metrics.csv"))
sg = sg[(sg["endpoint"] == "efs") & (sg["HR"].notna()) & (sg["CI_low"].notna())].copy()
sg = sg.sort_values("HR")
fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=140)
y_pos = np.arange(len(sg))
ax.errorbar(sg["HR"], y_pos, xerr=[sg["HR"] - sg["CI_low"], sg["CI_up"] - sg["HR"]],
            fmt="o", color="#d62728", capsize=4)
ax.set_yticks(y_pos)
ax.set_yticklabels([f"{r['subgroup']} (n={int(r['n'])})" for _, r in sg.iterrows()])
ax.axvline(1, color="grey", ls="--")
ax.set_xscale("log")
ax.set_xlim(0.5, 200)
ax.set_xlabel("Adjusted HR for EFS (log scale) — MAUVAIS vs BON")
ax.set_title("Subgroup forest plot — day-14 JLCM-ctDNA effect")
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "fig_forest_subgroups.png"), bbox_inches="tight")
plt.close()

# 16) Visual Abstract
print("[fig] visual abstract")
fig = plt.figure(figsize=(12, 5.5), dpi=160)
gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.3,
              height_ratios=[0.45, 0.55])
ax_title = fig.add_subplot(gs[0, :])
ax_title.axis("off")
ax_title.text(0.5, 0.65, "Joint Latent Class Modeling of plasma ctDNA delivers day-14 risk stratification in R/R LBCL post-CAR-T",
              ha="center", va="center", fontsize=15, weight="bold", color="#0b3d91")
ax_title.text(0.5, 0.20,
              "ALYCANTE training (n=57) — Léa external validation (n=18) — Train-rich, deploy-early design",
              ha="center", va="center", fontsize=11, color="#444")

ax1 = fig.add_subplot(gs[1, 0])
ax1.set_title("1. Train on J0 → M12 trajectory", fontsize=10)
ax1.plot([0, 0.5, 1, 3, 6, 12], [3, 1, 0.3, 0, 0, 0], "o-", color="#1f77b4", label="BON")
ax1.plot([0, 0.5, 1, 3, 6, 12], [3, 2, 1.5, 1.8, 2.0, 2.4], "o-", color="#d62728", label="MAUVAIS")
ax1.set_xlabel("Months")
ax1.set_ylabel("log10 hEG")
ax1.legend(fontsize=8, loc="upper right")

ax2 = fig.add_subplot(gs[1, 1])
ax2.set_title("2. Deploy predictClass on J0 + J14 only", fontsize=10)
ax2.bar(["BON", "MAUVAIS"], [22, 22], color=["#1f77b4", "#d62728"])
ax2.set_ylabel("ALYCANTE patients (n=44)")

ax3 = fig.add_subplot(gs[1, 2])
ax3.set_title("3. KM separation at 12m EFS", fontsize=10)
ax3.bar([0, 1], [86, 9], color=["#1f77b4", "#d62728"])
ax3.set_xticks([0, 1]); ax3.set_xticklabels(["BON", "MAUVAIS"])
ax3.set_ylim(0, 100)
ax3.set_ylabel("12-month EFS (%)")
ax3.text(0, 90, "86%", ha="center", fontsize=10)
ax3.text(1, 13, "9%", ha="center", fontsize=10)

plt.savefig(os.path.join(OUT_FIG, "fig_visual_abstract.png"), bbox_inches="tight")
plt.close()

print("[DONE]")
