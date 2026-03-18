#!/usr/bin/env python3
"""
phase1_eda.py — EDA & Preprocessing Pipeline
Data Science Pipeline — Mu Sigma
Phase 1: Load data, profile, detect outliers, select features, split, preprocess.

Changes (v2):
  CR3:  Exclude date-derived columns from EDA visuals (keep in dataset for modeling)
  CR4:  Raw time-series plots + log-differenced plots
  CR7:  Dataset categorization (time_series vs cross_sectional)
  CR8:  Data preview table after train/test split
  CR11: Stationarity checks (ADF, KPSS, ACF, PACF)
  CR15: All TS charts use date on X-axis
"""

from utils import (
    ARTIFACTS_DIR, DEFAULT_RANDOM_STATE, CHART_PALETTE, PALETTE,
    DATE_DERIVED_SUFFIXES,
    save_artifact, get_task_type_auto, plotly_layout, _json_serialiser,
    drop_date_derived_cols, is_date_derived,
    llm_describe, run_self_check, compute_composite_score
)
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys
import os
import json
import pickle
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))


# ── Data Loaders ──────────────────────────────────────────────────────────────

def load_data(path: str) -> pd.DataFrame:
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        return pd.read_csv(path)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    elif ext == ".json":
        return pd.read_json(path)
    elif ext == ".parquet":
        return pd.read_parquet(path)
    else:
        return pd.read_csv(path)


# ── Schema Inference ──────────────────────────────────────────────────────────

def infer_schema(df: pd.DataFrame) -> dict:
    schema = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_unique = int(df[col].nunique())
        missing_pct = float(round(df[col].isna().mean() * 100, 2))
        col_type = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else \
                   "boolean" if df[col].dtype == bool else \
                   "datetime" if pd.api.types.is_datetime64_any_dtype(df[col]) else \
                   "categorical"

        # 3e: Mark date-derived columns as modeling_include: false
        modeling_include = not _is_date_derived(col)

        entry = {
            "dtype": dtype,
            "col_type": col_type,
            "n_unique": n_unique,
            "missing_pct": missing_pct,
            "modeling_include": modeling_include
        }

        # CR10/CR24: Add min/max/mean/std for numeric columns (needed by anomaly detection)
        if col_type == "numeric":
            series = df[col].dropna()
            if len(series) > 0:
                entry["min"] = float(series.min())
                entry["max"] = float(series.max())
                entry["mean"] = float(series.mean())
                entry["std"] = float(series.std())

        schema[col] = entry
    return schema


def parse_datetime_cols(df: pd.DataFrame) -> tuple:
    """Detect and parse datetime columns; extract temporal features.
    Returns (df_modified, date_cols_detected, date_series_dict).
    date_series_dict maps original col name -> pd.Series of datetime values (for TS plots).
    """
    date_cols = []
    date_series = {}
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif df[col].dtype == object:
            try:
                parsed = pd.to_datetime(
                    df[col], infer_datetime_format=True, errors="raise")
                df[col] = parsed
                date_cols.append(col)
            except Exception:
                pass
    for col in date_cols:
        # Save the datetime series before dropping (for TS plots, CR15)
        date_series[col] = df[col].copy()
        df[f"{col}_year"] = df[col].dt.year
        df[f"{col}_month"] = df[col].dt.month
        df[f"{col}_day"] = df[col].dt.day
        df[f"{col}_dow"] = df[col].dt.dayofweek
        df = df.drop(columns=[col])
    return df, date_cols, date_series


def _is_date_derived(col: str) -> bool:
    """Check if a column name ends with a date-derived suffix."""
    return any(col.endswith(s) for s in DATE_DERIVED_SUFFIXES)


# ── Outlier Detection ─────────────────────────────────────────────────────────

def detect_outliers(df: pd.DataFrame, numeric_cols: list) -> dict:
    outliers = {}
    for col in numeric_cols:
        series = df[col].dropna()
        Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
        IQR = Q3 - Q1
        iqr_flags = int(((series < Q1 - 1.5 * IQR) |
                        (series > Q3 + 1.5 * IQR)).sum())
        z = (series - series.mean()) / (series.std() + 1e-9)
        z_flags = int((z.abs() > 3).sum())
        outliers[col] = {"iqr_flags": iqr_flags, "zscore_flags": z_flags}
    return outliers


# ── Distribution Charts ───────────────────────────────────────────────────────

def make_distribution_charts(df: pd.DataFrame, numeric_cols: list, cat_cols: list,
                             target: str = None, cache_dir=None) -> list:
    charts = []
    for col in numeric_cols:  # 3a: no cap
        series = df[col].dropna()
        hist_vals, bin_edges = np.histogram(series, bins=30)
        bin_mids = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()

        # 3f: Generate chart conclusion for each distribution (v5: enriched stats + LLM)
        skew = float(series.skew())
        kurt = float(series.kurtosis())
        stats = {
            "col": col,
            "skewness": skew,
            "kurtosis": kurt,
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
            "n_obs": len(series),
            "pct_missing": float(df[col].isna().mean() * 100),
        }
        conclusion = llm_describe("distribution", stats, cache_dir=cache_dir)

        charts.append({
            "chart_id": f"dist_{col}",
            "title": f"Distribution: {col}",
            "data": [{
                "type": "bar",
                "x": bin_mids,
                "y": hist_vals.tolist(),
                "marker": {"color": CHART_PALETTE[0]},
                "name": col
            }],
            "layout": plotly_layout(f"Distribution: {col}", col, "Count"),
            "conclusion": conclusion
        })

    for col in cat_cols[:5]:
        vc = df[col].value_counts().head(20)
        charts.append({
            "chart_id": f"cat_{col}",
            "title": f"Value Counts: {col}",
            "data": [{
                "type": "bar",
                "x": vc.index.tolist(),
                "y": vc.values.tolist(),
                "marker": {"color": CHART_PALETTE[1]},
                "name": col
            }],
            "layout": plotly_layout(f"Value Counts: {col}", col, "Count")
        })

    return charts


# ── Correlation ───────────────────────────────────────────────────────────────

def compute_correlations(df: pd.DataFrame, numeric_cols: list) -> tuple:
    if len(numeric_cols) < 2:
        return {}, {}
    sub = df[numeric_cols].copy()
    pearson = sub.corr(method="pearson").round(3)
    spearman = sub.corr(method="spearman").round(3)
    return pearson.to_dict(), spearman.to_dict()


def _shorten_label(name: str, max_len: int = 22) -> str:
    """Shorten long column names for axis labels while keeping them recognizable."""
    if len(name) <= max_len:
        return name
    # Try exact match abbreviations first, then partial
    exact_abbrevs = {
        "CPI_U_All_Items_Less_Food_Energy": "Core_CPI",
        "Spot_Oil_Price_West_Texas_Intermediate": "WTI_Oil",
        "X10_Year_Treasury_Note_Yield": "10Y_Treasury",
        "Unemployment_Rate": "Unempl_Rate",
        "Coincident_Index": "Coincident_Idx",
    }
    if name in exact_abbrevs:
        return exact_abbrevs[name]
    if len(name) > max_len:
        name = name[:max_len - 2] + ".."
    return name


def make_correlation_chart(corr_dict: dict, title: str = "Correlation Heatmap", cache_dir=None) -> dict:
    cols = list(corr_dict.keys())
    if not cols:
        return {}
    z = [[corr_dict[r].get(c, 0) for c in cols] for r in cols]

    # Shortened labels for axes
    short_cols = [_shorten_label(c) for c in cols]

    # 3c: Adaptive sizing — compute based on longest label
    n = len(cols)
    max_label_len = max(len(s) for s in short_cols) if short_cols else 10
    height = max(500, n * 50)
    width = max(650, n * 55)

    # Adaptive tickfont size and margins based on label length
    tickfont_size = max(9, min(12, 220 // n))
    margin_l = max(100, min(220, max_label_len * 8))
    margin_b = max(100, min(220, max_label_len * 7))

    # 3f: Generate chart conclusion
    # Find top correlation
    top_r = 0
    top_pair = ("", "")
    n_high = 0
    for i, r in enumerate(cols):
        for j, c in enumerate(cols):
            if i < j:
                val = abs(corr_dict[r].get(c, 0))
                if val > abs(top_r):
                    top_r = corr_dict[r].get(c, 0)
                    top_pair = (r, c)
                if val > 0.8:
                    n_high += 1

    # v5: Find bottom (weakest) correlation pair and average
    bottom_r = 1.0
    bottom_pair = ("", "")
    all_corrs = []
    for i, r in enumerate(cols):
        for j, c in enumerate(cols):
            if i < j:
                val = corr_dict[r].get(c, 0)
                all_corrs.append(abs(val))
                if abs(val) < abs(bottom_r):
                    bottom_r = val
                    bottom_pair = (r, c)
    avg_corr = float(np.mean(all_corrs)) if all_corrs else 0

    stats = {"top_pair": top_pair, "top_r": top_r, "n_high_corr": n_high,
             "bottom_pair": bottom_pair, "bottom_r": bottom_r,
             "avg_corr": avg_corr, "n_variables": len(cols)}
    conclusion = llm_describe("correlation", stats, cache_dir=cache_dir)

    return {
        "chart_id": "correlation_heatmap",
        "title": title,
        "data": [{
            "type": "heatmap",
            "z": z, "x": short_cols, "y": short_cols,
            "colorscale": "RdBu", "zmid": 0, "zmin": -1, "zmax": 1,
            "text": [[f"{v:.2f}" for v in row] for row in z],
            "texttemplate": "%{text}", "showscale": True
        }],
        "layout": {
            **plotly_layout(title, height=height),
            "width": width,
            "xaxis": {"title": "", "gridcolor": "#E5E5E5", "tickangle": -45,
                      "tickfont": {"size": tickfont_size}, "automargin": True},
            "yaxis": {"title": "", "gridcolor": "#E5E5E5",
                      "tickfont": {"size": tickfont_size}, "automargin": True},
            "margin": {"t": 50, "b": margin_b, "l": margin_l, "r": 30}
        },
        "conclusion": conclusion
    }


# ── Time Series EDA (CR4, CR11, CR15) ────────────────────────────────────────

def make_raw_ts_plots(df: pd.DataFrame, date_series: dict, numeric_cols: list, cache_dir=None) -> list:
    """Generate one line chart per numeric variable with X=date, Y=value (CR4, CR15)."""
    if not date_series:
        return []
    # Use the first detected date column
    date_col_name = list(date_series.keys())[0]
    dates = date_series[date_col_name]
    date_str = dates.dt.strftime("%Y-%m-%d").tolist()

    charts = []
    for i, col in enumerate(numeric_cols):
        if col not in df.columns:
            continue
        vals = df[col].fillna(method="ffill").fillna(method="bfill").tolist()

        # 3f: Generate chart conclusion
        series = df[col].dropna()
        # Simple trend detection
        if len(series) > 2:
            first_half_mean = series.iloc[:len(series)//2].mean()
            second_half_mean = series.iloc[len(series)//2:].mean()
            if second_half_mean > first_half_mean * 1.1:
                trend = "upward"
            elif second_half_mean < first_half_mean * 0.9:
                trend = "downward"
            else:
                trend = "flat"
        else:
            trend = "unknown"

        volatility = "high" if series.std() > series.mean(
        ) * 0.5 else "moderate" if series.std() > series.mean() * 0.2 else "low"
        pct_change = ((series.iloc[-1] - series.iloc[0]) /
                      (abs(series.iloc[0]) + 1e-9)) * 100 if len(series) > 1 else 0
        stats = {"col": col, "trend": trend, "volatility": volatility,
                 "n_obs": len(series), "start_val": float(series.iloc[0]),
                 "end_val": float(series.iloc[-1]), "pct_change_overall": float(pct_change)}
        conclusion = llm_describe("ts_raw", stats, cache_dir=cache_dir)

        charts.append({
            "chart_id": f"raw_ts_{col}",
            "title": f"Time Series: {col}",
            "data": [{
                "type": "scatter", "mode": "lines+markers",  # 3d: lines+markers
                "x": date_str, "y": vals,
                "line": {"color": CHART_PALETTE[i % len(CHART_PALETTE)], "width": 1.5},
                "marker": {"size": 4},  # 3d: marker size 4
                # 3d: custom hovertemplate
                "hovertemplate": "%{x|%Y-%m-%d}<br>%{y:.4f}<extra></extra>",
                "name": col
            }],
            "layout": plotly_layout(f"Time Series: {col}", date_col_name, col),
            "conclusion": conclusion
        })
    return charts


def make_log_diff_plots(df: pd.DataFrame, date_series: dict, numeric_cols: list, cache_dir=None) -> list:
    """Compute log(x_t) - log(x_{t-lag}) and generate line charts (CR4)."""
    if not date_series:
        return []
    date_col_name = list(date_series.keys())[0]
    dates = date_series[date_col_name]
    date_str = dates.dt.strftime("%Y-%m-%d").tolist()
    lag = 12 if len(df) >= 24 else 1

    charts = []
    for i, col in enumerate(numeric_cols):
        if col not in df.columns:
            continue
        series = df[col].fillna(method="ffill").fillna(method="bfill")
        # Avoid log of zero/negative
        if (series <= 0).any():
            # Use first-difference instead
            diff = series.diff(lag).fillna(0)
            title_suffix = f"(Diff lag={lag})"
        else:
            diff = np.log(series) - np.log(series.shift(lag))
            diff = diff.fillna(0)
            title_suffix = f"(Log-Diff lag={lag})"

        # 3f: Generate chart conclusion (v5: enriched + LLM)
        mean_val = float(diff.mean())
        std_val = float(diff.std())
        stats = {"col": col, "mean": mean_val, "std": std_val,
                 "n_obs": len(diff), "min": float(diff.min()), "max": float(diff.max())}
        conclusion = llm_describe("log_diff", stats, cache_dir=cache_dir)

        charts.append({
            "chart_id": f"log_diff_{col}",
            "title": f"{col} {title_suffix}",
            "data": [{
                "type": "scatter", "mode": "lines+markers",  # 3d: lines+markers
                "x": date_str, "y": diff.tolist(),
                "line": {"color": CHART_PALETTE[(i + 2) % len(CHART_PALETTE)], "width": 1.5},
                "marker": {"size": 4},  # 3d: marker size 4
                # 3d: custom hovertemplate
                "hovertemplate": "%{x|%Y-%m-%d}<br>%{y:.4f}<extra></extra>",
                "name": col
            }],
            "layout": plotly_layout(f"{col} {title_suffix}", date_col_name, "Differenced Value"),
            "conclusion": conclusion
        })
    return charts


def run_stationarity_checks(df: pd.DataFrame, numeric_cols: list) -> dict:
    """Run ADF, KPSS, ACF, PACF for each numeric variable (CR11)."""
    results = {}
    try:
        from statsmodels.tsa.stattools import adfuller, kpss, acf, pacf
    except ImportError:
        print("  Warning: statsmodels not available for stationarity checks")
        return results

    for col in numeric_cols:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) < 20:
            continue

        col_result = {}

        # ADF test
        try:
            adf_result = adfuller(series, autolag="AIC")
            col_result["adf"] = {
                "test_statistic": round(float(adf_result[0]), 4),
                "p_value": round(float(adf_result[1]), 6),
                "lags_used": int(adf_result[2]),
                "n_obs": int(adf_result[3]),
                "critical_values": {k: round(float(v), 4) for k, v in adf_result[4].items()},
                "stationary": float(adf_result[1]) < 0.05,
            }
        except Exception as e:
            col_result["adf"] = {"error": str(e)}

        # KPSS test
        try:
            kpss_result = kpss(series, regression="c", nlags="auto")
            col_result["kpss"] = {
                "test_statistic": round(float(kpss_result[0]), 4),
                "p_value": round(float(kpss_result[1]), 6),
                "critical_values": {k: round(float(v), 4) for k, v in kpss_result[3].items()},
                "stationary": float(kpss_result[1]) > 0.05,
            }
        except Exception as e:
            col_result["kpss"] = {"error": str(e)}

        # ACF and PACF values + chart data
        try:
            n_lags = min(40, len(series) // 2 - 1)
            if n_lags < 5:
                n_lags = 5
            acf_vals = acf(series, nlags=n_lags, fft=True)
            col_result["acf"] = {
                "values": [round(float(v), 4) for v in acf_vals],
                "n_lags": n_lags,
            }
        except Exception as e:
            col_result["acf"] = {"error": str(e)}

        try:
            n_lags_pacf = min(40, len(series) // 2 - 1)
            if n_lags_pacf < 5:
                n_lags_pacf = 5
            pacf_vals = pacf(series, nlags=n_lags_pacf)
            col_result["pacf"] = {
                "values": [round(float(v), 4) for v in pacf_vals],
                "n_lags": n_lags_pacf,
            }
        except Exception as e:
            col_result["pacf"] = {"error": str(e)}

        results[col] = col_result

    return results


def make_acf_pacf_charts(ts_diagnostics: dict, cache_dir=None) -> list:
    """Generate ACF and PACF bar charts with significance bands (CR11)."""
    charts = []
    for col, diag in ts_diagnostics.items():
        acf_data = diag.get("acf", {})
        pacf_data = diag.get("pacf", {})

        if "values" in acf_data:
            n = acf_data.get("n_lags", len(acf_data["values"]))
            sig_band = 1.96 / np.sqrt(n + 1)
            lags = list(range(len(acf_data["values"])))

            # 3f: Generate ACF conclusion (v5: enriched + LLM)
            significant_lags = sum(
                1 for v in acf_data["values"][1:] if abs(v) > sig_band)
            stats = {"col": col, "significant_lags": significant_lags,
                     "total_lags": len(acf_data["values"]) - 1, "n_obs": n}
            acf_conclusion = llm_describe("acf", stats, cache_dir=cache_dir)

            charts.append({
                "chart_id": f"acf_{col}",
                "title": f"ACF: {col}",
                "data": [
                    {"type": "bar", "x": lags, "y": acf_data["values"],
                     "marker": {"color": CHART_PALETTE[0]}, "name": "ACF"},
                    {"type": "scatter", "mode": "lines", "x": [0, max(lags)],
                     "y": [sig_band, sig_band], "line": {"color": CHART_PALETTE[3], "dash": "dash", "width": 1},
                     "name": "+95% CI", "showlegend": True},
                    {"type": "scatter", "mode": "lines", "x": [0, max(lags)],
                     "y": [-sig_band, -sig_band], "line": {"color": CHART_PALETTE[3], "dash": "dash", "width": 1},
                     "name": "-95% CI", "showlegend": False},
                ],
                "layout": plotly_layout(f"ACF: {col}", "Lag", "Autocorrelation", height=300),
                "conclusion": acf_conclusion
            })

        if "values" in pacf_data:
            n = pacf_data.get("n_lags", len(pacf_data["values"]))
            sig_band = 1.96 / np.sqrt(n + 1)
            lags = list(range(len(pacf_data["values"])))

            # 3f: Generate PACF conclusion (v5: enriched + LLM)
            significant_lags = sum(
                1 for v in pacf_data["values"][1:] if abs(v) > sig_band)
            stats = {"col": col, "significant_lags": significant_lags,
                     "total_lags": len(pacf_data["values"]) - 1, "n_obs": n}
            pacf_conclusion = llm_describe("pacf", stats, cache_dir=cache_dir)

            charts.append({
                "chart_id": f"pacf_{col}",
                "title": f"PACF: {col}",
                "data": [
                    {"type": "bar", "x": lags, "y": pacf_data["values"],
                     "marker": {"color": CHART_PALETTE[1]}, "name": "PACF"},
                    {"type": "scatter", "mode": "lines", "x": [0, max(lags)],
                     "y": [sig_band, sig_band], "line": {"color": CHART_PALETTE[3], "dash": "dash", "width": 1},
                     "name": "+95% CI", "showlegend": True},
                    {"type": "scatter", "mode": "lines", "x": [0, max(lags)],
                     "y": [-sig_band, -sig_band], "line": {"color": CHART_PALETTE[3], "dash": "dash", "width": 1},
                     "name": "-95% CI", "showlegend": False},
                ],
                "layout": plotly_layout(f"PACF: {col}", "Lag", "Partial Autocorrelation", height=300),
                "conclusion": pacf_conclusion
            })

    return charts


# ── Feature Selection ─────────────────────────────────────────────────────────

def select_features(df: pd.DataFrame, target: str, task_type: str,
                    numeric_cols: list, cat_cols: list) -> dict:
    """CR5: Record per-variable drop reasons in feature_selection_rationale."""
    feature_cols = [c for c in numeric_cols + cat_cols if c != target]
    if not feature_cols:
        return {"selected": feature_cols, "mi_scores": {}, "dropped_high_corr": [],
                "dropped_low_var": [], "rationale": []}

    from sklearn.feature_selection import VarianceThreshold
    num_feats = [c for c in numeric_cols if c != target]
    dropped_low_var = []
    rationale = []

    # 1. Variance threshold
    if num_feats:
        vt = VarianceThreshold(threshold=0.01)
        try:
            sub = df[num_feats].fillna(df[num_feats].median())
            vt.fit(sub)
            variances = vt.variances_
            for c, s, var in zip(num_feats, vt.get_support(), variances):
                if not s:
                    dropped_low_var.append(c)
                    rationale.append({
                        "column": c, "reason": f"Low variance (var={var:.4f} < 0.01)"
                    })
            num_feats = [c for c in num_feats if c not in dropped_low_var]
        except Exception:
            pass

    # 2. Correlation filter
    dropped_high_corr = []
    if len(num_feats) > 1:
        sub = df[num_feats].fillna(df[num_feats].median())
        corr_m = sub.corr().abs()
        upper = corr_m.where(np.triu(np.ones(corr_m.shape), k=1).astype(bool))
        for col in upper.columns:
            high_corr_pairs = upper.index[upper[col] > 0.95].tolist()
            if high_corr_pairs:
                dropped_high_corr.append(col)
                best_pair = high_corr_pairs[0]
                corr_val = corr_m.loc[best_pair, col]
                rationale.append({
                    "column": col,
                    "reason": f"High correlation with {best_pair} (r={corr_val:.3f} > 0.95)"
                })
        num_feats = [c for c in num_feats if c not in dropped_high_corr]

    selected = num_feats + [c for c in cat_cols if c != target]

    # 3. Mutual information
    mi_scores = {}
    if target in df.columns and task_type in ("regression", "classification", "forecasting"):
        try:
            from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
            X_sub = df[selected].copy()
            y_sub = df[target].copy()
            for col in X_sub.select_dtypes(include="number").columns:
                X_sub[col] = X_sub[col].fillna(X_sub[col].median())
            for col in X_sub.select_dtypes(exclude="number").columns:
                X_sub[col] = X_sub[col].astype("category").cat.codes
            fn = mutual_info_classif if task_type == "classification" else mutual_info_regression
            scores = fn(X_sub.fillna(0), y_sub.fillna(
                y_sub.median()), random_state=DEFAULT_RANDOM_STATE)
            mi_scores = {c: float(round(s, 4))
                         for c, s in zip(selected, scores)}
        except Exception as e:
            print(f"  Warning: MI scoring failed: {e}")

    return {
        "selected": selected,
        "mi_scores": mi_scores,
        "dropped_high_corr": dropped_high_corr,
        "dropped_low_var": dropped_low_var,
        "rationale": rationale,
    }


# ── Preprocessing Pipeline ────────────────────────────────────────────────────

def build_preprocessing_pipeline(df: pd.DataFrame, feature_cols: list):
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.impute import SimpleImputer

    num_cols = [
        c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [
        c for c in feature_cols if not pd.api.types.is_numeric_dtype(df[c])]

    transformers = []
    if num_cols:
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])
        transformers.append(("num", num_pipe, num_cols))
    if cat_cols:
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])
        transformers.append(("cat", cat_pipe, cat_cols))

    if not transformers:
        from sklearn.preprocessing import FunctionTransformer
        return Pipeline([("passthrough", FunctionTransformer())])

    return ColumnTransformer(transformers=transformers, remainder="drop")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1 - EDA & Preprocessing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--data",       required=True,
                        help="Path to input dataset")
    parser.add_argument("--target",     required=True,
                        help="Target column name")
    parser.add_argument("--task_type",  required=True,
                        choices=["regression", "classification", "forecasting", "segmentation", "auto"])
    parser.add_argument("--test_size",  type=float, default=0.2)
    parser.add_argument("--output_dir", default=None)
    args = parser.parse_args()

    out_dir = Path(
        args.output_dir) if args.output_dir else ARTIFACTS_DIR / "phase1"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\nPhase 1 - EDA & Preprocessing")
    print("=" * 50)

    # ── Load ──
    print(f"  Loading data from: {args.data}")
    df_raw = load_data(args.data)
    print(f"  Data loaded: {df_raw.shape[0]} rows x {df_raw.shape[1]} cols")

    # ── Auto task type ──
    task_type = args.task_type
    if task_type == "auto":
        task_type = get_task_type_auto(df_raw, args.target)
        print(f"  Task type auto-detected: {task_type}")
    else:
        print(f"  Task type: {task_type}")

    # ── Parse datetime and extract features ──
    df, date_cols, date_series = parse_datetime_cols(df_raw)

    # ── Dataset categorization (CR7) ──
    has_datetime = len(date_cols) > 0
    if args.target.lower() == "all":
        # When target=all, check if any numeric column exists
        has_numeric_target = any(
            pd.api.types.is_numeric_dtype(df[c]) for c in df.columns)
    else:
        has_numeric_target = args.target in df.columns and pd.api.types.is_numeric_dtype(
            df[args.target])
    dataset_category = "time_series" if (
        has_datetime and has_numeric_target) else "cross_sectional"
    print(f"  Dataset category: {dataset_category}")

    # ── Schema ──
    schema = infer_schema(df)
    numeric_cols = [c for c, v in schema.items() if v["col_type"] == "numeric"]
    cat_cols = [c for c, v in schema.items() if v["col_type"] == "categorical"]
    print(
        f"  Schema: {len(numeric_cols)} numeric, {len(cat_cols)} categorical, {len(date_cols)} datetime")

    # ── CR3: Filter out date-derived columns for EDA visuals ──
    # Note: target column is INCLUDED in EDA distributions (important for multi-target runs)
    eda_numeric_cols = [
        c for c in numeric_cols if not _is_date_derived(c)]
    eda_cat_cols = [c for c in cat_cols if c != args.target]
    print(
        f"  EDA columns (excluding date-derived): {len(eda_numeric_cols)} numeric")
    # 3a: log
    print(f"  Including {len(eda_numeric_cols)} numeric columns in EDA")

    # ── Outliers (on EDA columns only, CR3) ──
    outliers = detect_outliers(df, eda_numeric_cols)
    total_iqr = sum(v["iqr_flags"] for v in outliers.values())
    total_zscore = sum(v["zscore_flags"] for v in outliers.values())
    print(f"  Outliers: {total_iqr} IQR flags, {total_zscore} Z-score flags")

    # ── Distributions (EDA cols only, CR3) ──
    dist_charts = make_distribution_charts(
        df, eda_numeric_cols, eda_cat_cols, cache_dir=out_dir)
    print(f"  Distributions: {len(dist_charts)} charts")

    # ── Correlations (EDA cols only, CR3) ──
    pearson_corr, spearman_corr = compute_correlations(df, eda_numeric_cols)
    corr_chart = make_correlation_chart(
        pearson_corr, "Pearson Correlation Heatmap", cache_dir=out_dir)
    print(
        f"  Correlations computed: {len(eda_numeric_cols)}x{len(eda_numeric_cols)} matrix")

    # ── Time Series EDA (CR4, CR11, CR15) ──
    raw_ts_plots = []
    log_diff_plots = []
    ts_diagnostics = {}
    acf_pacf_charts = []

    if dataset_category == "time_series":
        print("  Running time-series EDA...")
        # All numeric cols (including target) for TS plots
        ts_numeric_cols = [c for c in numeric_cols if not _is_date_derived(c)]

        raw_ts_plots = make_raw_ts_plots(
            df, date_series, ts_numeric_cols, cache_dir=out_dir)
        print(f"    Raw TS plots: {len(raw_ts_plots)}")

        log_diff_plots = make_log_diff_plots(
            df, date_series, ts_numeric_cols, cache_dir=out_dir)
        print(f"    Log-diff plots: {len(log_diff_plots)}")

        ts_diagnostics = run_stationarity_checks(df, ts_numeric_cols)
        print(f"    Stationarity checks: {len(ts_diagnostics)} variables")

        acf_pacf_charts = make_acf_pacf_charts(
            ts_diagnostics, cache_dir=out_dir)
        print(f"    ACF/PACF charts: {len(acf_pacf_charts)}")

    # ── Feature Selection (v5: filter date-derived BEFORE selection) ──
    # Filter date-derived columns BEFORE feature selection
    modeling_numeric_cols = [c for c in numeric_cols if not is_date_derived(c)]
    feat_result = select_features(
        df, args.target, task_type, modeling_numeric_cols, cat_cols)
    # v5: Add rationale entries for excluded date-derived columns
    for col in numeric_cols:
        if is_date_derived(col):
            feat_result.setdefault("rationale", []).append(
                {"column": col, "reason": "Date-derived feature - excluded from modeling pipeline (informational only in §3)"})
    selected = feat_result["selected"]
    print(f"  Features selected: {len(selected)} retained")

    # ── Train/Test Split ──
    from sklearn.model_selection import train_test_split

    if args.target in df.columns:
        X = df[selected].copy()
        y = df[args.target].copy()
    else:
        X = df[selected].copy()
        y = None

    if task_type == "forecasting":
        # CR7: Chronological split for time-series — NO shuffle, index-based.
        # This preserves temporal ordering which is critical for TS validation.
        split_idx = int(len(df) * (1 - args.test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        if y is not None:
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        else:
            y_train, y_test = None, None
    elif task_type == "classification" and y is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size,
            random_state=DEFAULT_RANDOM_STATE, stratify=y
        )
    elif y is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=DEFAULT_RANDOM_STATE
        )
    else:
        X_train, X_test = train_test_split(
            X, test_size=args.test_size, random_state=DEFAULT_RANDOM_STATE)
        y_train, y_test = None, None

    print(f"  Train/test split: {len(X_train)} train, {len(X_test)} test")

    # ── Preprocessing ──
    preprocessor = build_preprocessing_pipeline(X_train, selected)
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)

    try:
        ohe_cols = []
        for name, trans, cols in preprocessor.transformers_:
            if name == "num":
                ohe_cols += cols
            elif name == "cat":
                ohe = trans.named_steps["encoder"]
                ohe_cols += list(ohe.get_feature_names_out(cols))
        transformed_cols = ohe_cols
    except Exception:
        transformed_cols = [f"f_{i}" for i in range(X_train_t.shape[1])]

    train_df = pd.DataFrame(X_train_t, columns=transformed_cols)
    test_df = pd.DataFrame(X_test_t,  columns=transformed_cols)

    if y_train is not None:
        train_df[args.target] = y_train.values
    if y_test is not None:
        test_df[args.target] = y_test.values

    # 3e: Drop date-derived columns from clean_train/clean_test before saving
    train_df = drop_date_derived_cols(train_df)
    test_df = drop_date_derived_cols(test_df)

    print(f"  Preprocessing pipeline fitted")

    # ── 3b: Individual outlier box charts ──
    box_charts = []
    for i, col in enumerate(eda_numeric_cols):  # 3a: no cap
        series = df[col].dropna()
        Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
        IQR = Q3 - Q1
        iqr_flags = int(((series < Q1 - 1.5 * IQR) |
                        (series > Q3 + 1.5 * IQR)).sum())
        z = (series - series.mean()) / (series.std() + 1e-9)
        z_flags = int((z.abs() > 3).sum())
        outlier_pct = (iqr_flags / len(series) * 100) if len(series) > 0 else 0

        # Generate conclusion (v5: enriched with IQR/Z-score detail + LLM)
        stats = {"col": col, "outlier_pct": outlier_pct,
                 "iqr_flags": iqr_flags, "zscore_flags": z_flags,
                 "q1": float(Q1), "q3": float(Q3), "iqr": float(IQR),
                 "median": float(series.median()),
                 "min": float(series.min()), "max": float(series.max())}
        conclusion = llm_describe("boxplot", stats, cache_dir=out_dir)

        box_charts.append({
            "chart_id": f"outlier_{col}",
            "title": f"Outliers: {col}",
            "data": [{
                "type": "box",
                "y": series.tolist(),
                "name": col,
                "marker": {"color": CHART_PALETTE[i % len(CHART_PALETTE)]},
                "boxmean": True
            }],
            "layout": plotly_layout(
                f"Outliers: {col}<br><sub>IQR flags: {iqr_flags}, Z-score flags: {z_flags} ({outlier_pct:.1f}%)</sub>",
                "", "Value", height=350
            ),
            "conclusion": conclusion
        })

    all_charts = dist_charts + [corr_chart] + box_charts

    # ── CR8: Split preview ──
    split_preview = {
        "train_preview": train_df.head(10).round(4).to_dict("records"),
        "test_preview": test_df.head(5).round(4).to_dict("records"),
    }

    # ── Save Artifacts ──
    phase1_results = {
        "task_type": task_type,
        "target": args.target,
        "dataset_category": dataset_category,  # CR7
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "schema": schema,
        "date_cols_detected": date_cols,
        "outliers": outliers,
        "pearson_corr": pearson_corr,
        "spearman_corr": spearman_corr,
        "feature_selection": feat_result,
        "selected_features": selected,
        "split_info": {
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "test_size": args.test_size,
            "split_type": "stratified" if task_type == "classification" else
                          "time_aware" if task_type == "forecasting" else "random"
        },
        "preprocessed_shape": {
            "train": list(X_train_t.shape),
            "test":  list(X_test_t.shape)
        }
    }

    with open(out_dir / "phase1_results.json", "w") as f:
        json.dump(phase1_results, f, indent=2, default=_json_serialiser)

    train_df.to_csv(out_dir / "clean_train.csv", index=False)
    test_df.to_csv(out_dir / "clean_test.csv", index=False)

    # Save date index for Phase 3 chart titles and drift headers (v5 Step 6)
    if date_series:
        date_col_name = list(date_series.keys())[0]
        full_dates = date_series[date_col_name]
        # Split the dates the same way as the data (time-aware = last N rows for test)
        n_test = len(test_df)
        test_dates = full_dates.iloc[-n_test:].astype(str).tolist()
        train_dates = full_dates.iloc[:-n_test].astype(str).tolist()
        with open(out_dir / "date_index.json", "w") as f:
            json.dump({"date_col": date_col_name,
                       "train_dates": train_dates,
                       "test_dates": test_dates}, f, indent=2)

    mi_sorted = dict(
        sorted(feat_result["mi_scores"].items(), key=lambda x: x[1], reverse=True))
    with open(out_dir / "feature_importance_phase1.json", "w") as f:
        json.dump(mi_sorted, f, indent=2)

    with open(out_dir / "eda_charts.json", "w") as f:
        json.dump(all_charts, f, indent=2, default=_json_serialiser)

    with open(out_dir / "preprocessing_pipeline.pkl", "wb") as f:
        pickle.dump(preprocessor, f)

    # CR5: Feature selection rationale
    with open(out_dir / "feature_selection_rationale.json", "w") as f:
        json.dump(feat_result.get("rationale", []), f, indent=2)

    # CR8: Split preview
    with open(out_dir / "split_preview.json", "w") as f:
        json.dump(split_preview, f, indent=2, default=_json_serialiser)

    # Time-series specific artifacts (CR4, CR11)
    if dataset_category == "time_series":
        with open(out_dir / "raw_ts_plots.json", "w") as f:
            json.dump(raw_ts_plots, f, indent=2, default=_json_serialiser)

        with open(out_dir / "log_diff_plots.json", "w") as f:
            json.dump(log_diff_plots, f, indent=2, default=_json_serialiser)

        with open(out_dir / "ts_diagnostics.json", "w") as f:
            json.dump(ts_diagnostics, f, indent=2, default=_json_serialiser)

        with open(out_dir / "acf_pacf_charts.json", "w") as f:
            json.dump(acf_pacf_charts, f, indent=2, default=_json_serialiser)

        # 3f: Add stationarity conclusions (v5: enriched + LLM)
        stationarity_conclusions = {}
        for col, diag in ts_diagnostics.items():
            adf_info = diag.get("adf", {})
            kpss_info = diag.get("kpss", {})
            adf_stat = adf_info.get("stationary", False)
            kpss_stat = kpss_info.get("stationary", False)
            stats = {"col": col, "adf_stationary": adf_stat,
                     "kpss_stationary": kpss_stat,
                     "adf_pvalue": adf_info.get("p_value"),
                     "kpss_pvalue": kpss_info.get("p_value"),
                     "adf_statistic": adf_info.get("test_statistic"),
                     "kpss_statistic": kpss_info.get("test_statistic")}
            stationarity_conclusions[col] = llm_describe(
                "stationarity", stats, cache_dir=out_dir)

        with open(out_dir / "stationarity_conclusions.json", "w") as f:
            json.dump(stationarity_conclusions, f,
                      indent=2, default=_json_serialiser)

    # 3f: Save all chart conclusions
    chart_conclusions = {}
    for chart in all_charts:
        if "conclusion" in chart:
            chart_conclusions[chart["chart_id"]] = chart["conclusion"]
    for chart in raw_ts_plots:
        if "conclusion" in chart:
            chart_conclusions[chart["chart_id"]] = chart["conclusion"]
    for chart in log_diff_plots:
        if "conclusion" in chart:
            chart_conclusions[chart["chart_id"]] = chart["conclusion"]
    for chart in acf_pacf_charts:
        if "conclusion" in chart:
            chart_conclusions[chart["chart_id"]] = chart["conclusion"]

    # v5: Merge stationarity conclusions into main chart_conclusions.json
    if dataset_category == "time_series" and stationarity_conclusions:
        for col, conclusion_text in stationarity_conclusions.items():
            chart_conclusions[f"stationarity_{col}"] = conclusion_text

    with open(out_dir / "chart_conclusions.json", "w") as f:
        json.dump(chart_conclusions, f, indent=2, default=_json_serialiser)

    # 3g: Phase 1 self-check
    self_check_results = run_self_check("phase1", phase1_results)
    with open(out_dir / "self_check_results.json", "w") as f:
        json.dump(self_check_results, f, indent=2, default=_json_serialiser)

    if not self_check_results.get("passed", True):
        print(f"  Self-check errors: {self_check_results.get('errors', [])}")
    if self_check_results.get("warnings"):
        print(
            f"  Self-check warnings: {self_check_results.get('warnings', [])}")

    print(f"  Artifacts saved to: {out_dir}")
    print(f"\n  Phase 1 complete - {out_dir}/ ready\n")


if __name__ == "__main__":
    main()
