"""
utils.py — Shared config, constants, and artifact I/O helpers
Data Science Pipeline — Mu Sigma
"""

import os
import json
import pickle
import datetime
import re
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Reports go to skills/data-science/reports/
REPORTS_DIR = BASE_DIR / "reports"

DEFAULT_RANDOM_STATE = 42

# MuSigma chart palette (matches template spec)
CHART_PALETTE = ["#4E79A7", "#59A14F", "#F28E2B", "#E15759", "#BAB0AC"]
PALETTE = CHART_PALETTE

# Report author constant (matches SOUL.md identity)
REPORT_AUTHOR = "Ved"

# Date-derived column suffixes to exclude from EDA and modeling
DATE_DERIVED_SUFFIXES = ("_year", "_month", "_day", "_dow")

# ── CDN Constants (CR21, CR13) ────────────────────────────────────────────────
KATEX_CSS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css"
KATEX_JS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"
KATEX_AUTO_CDN = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"
DATATABLES_CSS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/datatables/1.10.21/css/jquery.dataTables.min.css"
DATATABLES_JS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/datatables/1.10.21/js/jquery.dataTables.min.js"

# ── Abbreviation Glossary (CR17) ──────────────────────────────────────────────
ABBREVIATION_GLOSSARY = {
    "RMSE": "Root Mean Squared Error",
    "MAE": "Mean Absolute Error",
    "MAPE": "Mean Absolute Percentage Error (%)",
    "R2": "Coefficient of Determination",
    "CV": "Cross-Validation",
    "ADF": "Augmented Dickey-Fuller Test",
    "KPSS": "Kwiatkowski-Phillips-Schmidt-Shin Test",
    "ACF": "Autocorrelation Function",
    "PACF": "Partial Autocorrelation Function",
    "IQR": "Interquartile Range",
    "VAR": "Vector Autoregression",
    "VARMAX": "VAR with Exogenous Variables",
    "ARIMA": "Autoregressive Integrated Moving Average",
    "XGB": "eXtreme Gradient Boosting",
    "RF": "Random Forest",
    "CPI": "Consumer Price Index",
    "ETF": "Exchange-Traded Fund",
    "TS": "Time Series",
    "EDA": "Exploratory Data Analysis",
}

# ── Extra CSS for tables (CR8) ────────────────────────────────────────────────
SCROLLABLE_TABLE_CSS = """
.table-scroll-wrapper { overflow-x: auto; max-width: 100%; margin: 12px 0; }
.chart-conclusion { font-style: italic; font-size: 13px; color: #555;
  border-left: 3px solid #4E79A7; padding: 6px 12px; margin: 8px 0 16px; }
tbody { counter-reset: rownum; }
.sno-table tbody tr td:first-child::before { counter-increment: rownum; content: counter(rownum); }
"""

# ── Template Resolution ───────────────────────────────────────────────────────


def get_template_path() -> Path:
    """Resolve the canonical template.html path. Tries multiple locations."""
    candidates = [
        Path.home() / ".openclaw" / "workspace" / "skills" /
        "musigma-html-report-generator" / "assets" / "template.html",
        Path(__file__).resolve().parent.parent.parent /
        "musigma-html-report-generator" / "assets" / "template.html",
    ]
    env_home = os.environ.get("OPENCLAW_HOME")
    if env_home:
        candidates.append(Path(env_home) / "workspace" / "skills" /
                          "musigma-html-report-generator" / "assets" / "template.html")
    for p in candidates:
        try:
            if p.resolve().exists():
                return p.resolve()
        except OSError:
            continue
    return candidates[0]


# ── Fallback Template CSS/JS ─────────────────────────────────────────────────

FALLBACK_STYLE_BLOCK = """<style type="text/css">
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px; line-height: 1.42857; color: #333; background: #fff;
  counter-reset: h2counter;
}
div.container-fluid.main-container { max-width: 1200px; margin: 0 auto; }
#TOC { position: fixed; top: 60px; left: 0; width: 22%; max-height: calc(100vh - 80px);
       overflow-y: auto; padding: 10px 15px; font-size: 12px; }
#TOC ul { list-style: none; padding-left: 0; }
#TOC ul ul { padding-left: 14px; }
#TOC li { margin: 2px 0; }
#TOC a { color: #4E79A7; text-decoration: none; }
#TOC a:hover { text-decoration: underline; }
.toc-content { margin-left: 24%; }
h2 { counter-increment: h2counter; counter-reset: h3counter; font-size: 22px;
     font-weight: 700; margin: 30px 0 12px; color: #222; }
h2::before { content: counter(h2counter) ". "; color: #4E79A7; }
h3 { counter-increment: h3counter; font-size: 17px; font-weight: 600;
     margin: 20px 0 8px; color: #333; }
h3::before { content: counter(h2counter) "." counter(h3counter) " "; color: #4E79A7; }
table { width: 100%; border-collapse: collapse; margin: 12px 0 18px; font-size: 13px; }
thead tr { background: #4E79A7; color: #fff; }
th, td { padding: 7px 10px; border: 1px solid #ddd; text-align: left; }
tbody tr:nth-child(even) { background: #f8f9fa; }
.report-header { display: flex; align-items: center; padding: 18px 0; margin-bottom: 15px; }
.report-header .logo img { height: 48px; margin-right: 18px; }
.report-header .title-text { font-size: 24px; font-weight: 700; color: #222; }
.report-header .author-date { font-size: 13px; color: #666; margin-top: 2px; }
.report-header .spacer { flex: 1; }
.chart-container { margin: 10px 0 18px; }
.table-scroll-wrapper { overflow-x: auto; max-width: 100%; margin: 12px 0; }
.chart-conclusion { font-style: italic; font-size: 13px; color: #555;
  border-left: 3px solid #4E79A7; padding: 6px 12px; margin: 8px 0 16px; }
@media (max-width: 768px) { #TOC { display: none; } .toc-content { margin-left: 0; } }
</style>"""

FALLBACK_TOC_SCRIPT = """<script>
$(document).ready(function(){
  var toc=$('#TOC'), ul=$('<ul/>'), h2c=0, h3c=0;
  $('h2,h3').each(function(){
    var $h=$(this), tag=this.tagName.toLowerCase(), id=$h.closest('.section').attr('id')||'';
    if(!id) return;
    if(tag==='h2'){ h2c++; h3c=0; var li=$('<li/>').append($('<a/>').attr('href','#'+id).text(h2c+'. '+$h.text().replace(/^[\\d.]+\\s*/,''))); ul.append(li); li.data('sub',$('<ul/>')); li.append(li.data('sub')); }
    else if(tag==='h3'){ h3c++; var sub=ul.children('li:last').data('sub'); if(sub) sub.append($('<li/>').append($('<a/>').attr('href','#'+id).text(h2c+'.'+h3c+' '+$h.text().replace(/^[\\d.]+\\s*/,'')))); }
  });
  toc.empty().append(ul);
});
</script>"""


# ── Composite Scoring (CR11) ──────────────────────────────────────────────────

def compute_composite_score(metrics: dict) -> float:
    """
    Weighted composite model score: higher is better.
    Weights: 35% RMSE, 25% MAPE, 25% R2, 15% CV stability.
    All components normalized to [0, 1].
    """
    rmse = metrics.get("rmse", 999)
    mape = metrics.get("mape", 999)
    r2 = metrics.get("r2", -1)
    cv_std = metrics.get("cv_std", 999)

    rmse_norm = 1.0 / (1.0 + rmse)
    mape_norm = 1.0 / (1.0 + mape / 100.0)
    r2_norm = max(0.0, r2)
    cv_stability = 1.0 / (1.0 + cv_std)

    composite = (0.35 * rmse_norm + 0.25 * mape_norm +
                 0.25 * r2_norm + 0.15 * cv_stability)
    return round(composite, 6)


# ── Self-Check Framework (CR22) ───────────────────────────────────────────────

def run_self_check(phase: str, data_dict: dict, original_stats: dict = None) -> dict:
    """
    Lenient self-check: warns and flags, never halts.
    Returns {"passed": bool, "warnings": [...], "errors": [...]}.
    Warnings are dicts: {"text": "...", "severity": "major"|"minor"}.
    """
    import numpy as np
    warnings_list = []
    errors_list = []

    def _warn(text, severity="minor"):
        warnings_list.append({"text": text, "severity": severity})

    if phase == "phase1":
        schema = data_dict.get("schema", {})
        n_train = data_dict.get("split_info", {}).get("n_train", 0)
        n_test = data_dict.get("split_info", {}).get("n_test", 0)
        n_rows = data_dict.get("n_rows", 0)
        if n_train + n_test != n_rows:
            _warn(f"Train+test ({n_train}+{n_test}={n_train+n_test}) != original rows ({n_rows})", "major")
        if not schema:
            errors_list.append("Schema is empty")

    elif phase == "phase2":
        models = data_dict.get("models", [])
        if len(models) < 3:
            _warn(f"Only {len(models)} models produced valid metrics (expected >=3)", "minor")
        for m in models:
            name = m.get("name", "?")
            mx = m.get("metrics", {})
            mape = mx.get("mape", 0)
            r2 = mx.get("r2", 0)
            if mape > 200:
                _warn(f"{name}: MAPE={mape:.1f}% is very high (>200%)", "minor")
            if r2 < 0:
                _warn(f"{name}: Negative R2={r2:.4f} (worse than mean baseline)", "minor")
            # Check for NaN — major severity
            for k, v in mx.items():
                if v is not None and isinstance(v, float) and np.isnan(v):
                    _warn(f"{name}: metric {k} is NaN", "major")
                    errors_list.append(f"{name}: metric {k} is NaN")
        # Check for empty predictions — major
        if len(models) == 0:
            _warn("No models produced valid predictions", "major")

    elif phase == "phase3":
        fm = data_dict.get("final_metrics", {})
        mape = fm.get("mape", 0)
        r2 = fm.get("r2", 0)
        if mape > 200:
            _warn(f"Final MAPE={mape:.1f}% very high", "minor")
        if r2 < 0:
            _warn(f"Final R2={r2:.4f} negative", "minor")
        # Check drift
        drift = data_dict.get("drift_analysis", {})
        for metric, info in drift.items():
            drift_pct = info.get("drift_pct", 0)
            if drift_pct > 50:
                _warn(f"Metric {metric} drifted by {drift_pct:.1f}% (>50%)", "minor")
        # Check for empty predictions — major
        n_preds = data_dict.get("n_predictions", 0)
        if n_preds == 0:
            _warn("Empty predictions — no test samples produced", "major")

    passed = len(errors_list) == 0
    return {"passed": passed, "warnings": warnings_list, "errors": errors_list}


# ── Chart Conclusion Generator (CR5, CR6, CR23) ──────────────────────────────

def generate_chart_conclusion(chart_type: str, stats: dict) -> str:
    """
    Rule-based chart conclusion generator. Returns 2-3 sentence text.
    chart_type: distribution, correlation, boxplot, ts_raw, log_diff, acf, pacf,
                stationarity, forecast, comparison, residual
    """
    if chart_type == "distribution":
        col = stats.get("col", "variable")
        skew = stats.get("skewness", 0)
        kurt = stats.get("kurtosis", 0)
        mn, mx = stats.get("min", 0), stats.get("max", 0)
        mean = stats.get("mean")
        median = stats.get("median")
        std = stats.get("std")
        n_obs = stats.get("n_obs")
        pct_missing = stats.get("pct_missing", 0)
        if abs(skew) > 1:
            shape = "positively skewed" if skew > 0 else "negatively skewed"
        elif abs(skew) > 0.5:
            shape = "moderately skewed"
        else:
            shape = "approximately symmetric"
        tail = "heavy-tailed (leptokurtic)" if kurt > 3 else "light-tailed (platykurtic)" if kurt < 2 else "normal-tailed"
        summary_parts = [f"The distribution of {col} is {shape} (skewness={skew:.2f}) with {tail} behaviour (kurtosis={kurt:.2f})"]
        if n_obs is not None:
            summary_parts[0] += f" across {n_obs} observations"
        summary_parts[0] += f", ranging from {mn:.2f} to {mx:.2f}."
        if mean is not None and std is not None:
            summary_parts.append(f"Mean={mean:.2f}, median={median:.2f if median is not None else 'N/A'}, std={std:.2f}.")
        if pct_missing > 0:
            summary_parts.append(f"{pct_missing:.1f}% missing values detected.")
        if abs(skew) > 1:
            summary_parts.append("The pronounced skew suggests outlier-robust models (tree-based) may be preferred over linear methods.")
        else:
            summary_parts.append("The approximately symmetric shape is suitable for both linear and tree-based modeling approaches.")
        return " ".join(summary_parts)

    elif chart_type == "correlation":
        top_pair = stats.get("top_pair", ("", ""))
        top_r = stats.get("top_r", 0)
        n_high = stats.get("n_high_corr", 0)
        if top_r > 0.8:
            return (f"Strong positive correlation ({top_r:.2f}) between {top_pair[0]} and {top_pair[1]}. "
                    f"{n_high} variable pair{'s' if n_high != 1 else ''} exceed |r|>0.8, indicating potential multicollinearity. "
                    f"Feature selection addresses this by dropping redundant predictors.")
        elif top_r > 0.5:
            return (f"Moderate correlations detected (max {top_r:.2f}). "
                    f"No severe multicollinearity concerns.")
        return "Correlations are generally weak, suggesting independent features suitable for linear models."

    elif chart_type == "boxplot":
        col = stats.get("col", "variable")
        outlier_pct = stats.get("outlier_pct", 0)
        iqr_flags = stats.get("iqr_flags", 0)
        z_flags = stats.get("zscore_flags", 0)
        q1 = stats.get("q1")
        q3 = stats.get("q3")
        iqr_val = stats.get("iqr")
        median_val = stats.get("median")
        min_val = stats.get("min")
        max_val = stats.get("max")
        # Build IQR/Z-score explanation with actual values when available
        iqr_detail = ""
        if q1 is not None and q3 is not None and iqr_val is not None:
            lower_bound = q1 - 1.5 * iqr_val
            upper_bound = q3 + 1.5 * iqr_val
            iqr_detail = (f" Using the IQR method (values outside Q1({q1:.2f}) − 1.5×IQR to Q3({q3:.2f}) + 1.5×IQR, "
                          f"i.e. below {lower_bound:.2f} or above {upper_bound:.2f}), {iqr_flags} values were flagged. "
                          f"The Z-score method (values beyond 3 standard deviations from the mean) flagged {z_flags} values.")
        range_detail = ""
        if min_val is not None and max_val is not None and median_val is not None:
            range_detail = f" Values range from {min_val:.2f} to {max_val:.2f} with median {median_val:.2f}."
        if outlier_pct > 5:
            return (f"{col} has {outlier_pct:.1f}% outlier observations.{iqr_detail}{range_detail} "
                    f"These extreme values may influence linear models but tree-based methods are inherently robust to them.")
        elif outlier_pct > 1:
            return (f"{col} shows moderate outlier presence ({outlier_pct:.1f}%).{iqr_detail}{range_detail} "
                    f"Outliers are retained for modeling — tree-based algorithms handle them naturally.")
        return (f"{col} has minimal outliers ({outlier_pct:.1f}%).{iqr_detail}{range_detail} "
                f"Clean data distribution suitable for all model types.")

    elif chart_type == "ts_raw":
        col = stats.get("col", "variable")
        trend = stats.get("trend", "unknown")
        volatility = stats.get("volatility", "unknown")
        return (f"{col} shows a {trend} trend over the observation period with {volatility} volatility. "
                f"{'Differencing or detrending may be needed before modeling.' if trend != 'flat' else 'Series appears relatively stable.'}")

    elif chart_type == "log_diff":
        col = stats.get("col", "variable")
        mean_val = stats.get("mean", 0)
        std_val = stats.get("std", 0)
        return (f"Log-differenced {col} has mean {mean_val:.4f} and std {std_val:.4f}. "
                f"{'Values centered near zero suggest approximate stationarity after differencing.' if abs(mean_val) < 0.1 else 'Non-zero mean indicates residual trend.'}")

    elif chart_type == "stationarity":
        col = stats.get("col", "variable")
        adf_stat = stats.get("adf_stationary", False)
        kpss_stat = stats.get("kpss_stationary", False)
        if adf_stat and kpss_stat:
            return f"{col} is stationary (confirmed by both ADF and KPSS tests). Direct modeling is appropriate."
        elif adf_stat and not kpss_stat:
            return f"{col}: ADF indicates stationarity but KPSS suggests trend-stationarity. Consider detrending."
        elif not adf_stat and kpss_stat:
            return f"{col}: ADF fails to reject unit root but KPSS suggests stationarity. May need differencing."
        return f"{col} is non-stationary (both ADF and KPSS). Differencing or transformation required before modeling."

    elif chart_type == "acf":
        col = stats.get("col", "variable")
        significant_lags = stats.get("significant_lags", 0)
        if significant_lags > 5:
            return f"{col} shows {significant_lags} significant autocorrelation lags, indicating strong serial dependence. ARIMA or VAR models are well-suited."
        elif significant_lags > 0:
            return f"{col} has {significant_lags} significant lag{'s' if significant_lags != 1 else ''}, suggesting moderate temporal dependence."
        return f"{col} shows no significant autocorrelation, suggesting the series may be white noise."

    elif chart_type == "pacf":
        col = stats.get("col", "variable")
        significant_lags = stats.get("significant_lags", 0)
        if significant_lags >= 3:
            return f"PACF for {col} suggests AR order >= {significant_lags}. Consider ARIMA(p,d,q) with p >= {min(significant_lags, 5)}."
        elif significant_lags > 0:
            return f"PACF indicates AR({significant_lags}) may be sufficient for {col}."
        return f"No significant partial autocorrelation for {col}."

    elif chart_type == "forecast":
        target = stats.get("target", "variable")
        r2 = stats.get("r2", 0)
        rmse = stats.get("rmse", 0)
        model = stats.get("model", "model")
        if r2 > 0.8:
            quality = "closely tracks"
        elif r2 > 0.5:
            quality = "captures the general trend of"
        elif r2 > 0:
            quality = "partially captures"
        else:
            quality = "struggles to predict"
        return (f"{model} {quality} actual {target} values (R2={r2:.3f}, RMSE={rmse:.3f}). "
                f"{'The model is production-ready for this variable.' if r2 > 0.8 else 'Additional feature engineering or alternative models may improve accuracy.'}")

    elif chart_type == "comparison":
        metric = stats.get("metric", "metric")
        best = stats.get("best_model", "model")
        best_val = stats.get("best_value", 0)
        worst_val = stats.get("worst_value", 0)
        spread = abs(best_val - worst_val)
        return (f"For {metric}, {best} leads with {best_val:.4f}. "
                f"The spread across models is {spread:.4f}, "
                f"{'indicating substantial model differentiation.' if spread > 0.1 else 'suggesting similar performance across candidates.'}")

    elif chart_type == "residual":
        model = stats.get("model", "model")
        mean_res = stats.get("mean_residual", 0)
        std_res = stats.get("std_residual", 0)
        if abs(mean_res) < 0.01 * std_res:
            return f"{model} residuals are centered near zero (mean={mean_res:.4f}), indicating no systematic bias."
        return f"{model} residuals have mean={mean_res:.4f} (std={std_res:.4f}), suggesting {'positive' if mean_res > 0 else 'negative'} prediction bias."

    elif chart_type == "feature_selection":
        n_ret = stats.get("n_retained", 0)
        n_orig = stats.get("n_original", 0)
        n_var = stats.get("n_dropped_var", 0)
        n_corr = stats.get("n_dropped_corr", 0)
        pct = round(n_ret / n_orig * 100, 1) if n_orig else 0
        return (f"{n_ret} of {n_orig} features ({pct}%) retained after 3-step filtering. "
                f"Variance threshold removed {n_var} near-constant feature{'s' if n_var != 1 else ''}, "
                f"correlation filter removed {n_corr} redundant predictor{'s' if n_corr != 1 else ''}. "
                f"The retained feature set balances dimensionality reduction with information preservation.")

    elif chart_type == "train_test_split":
        split_type = stats.get("split_type", "random")
        n_train = stats.get("n_train", 0)
        n_test = stats.get("n_test", 0)
        test_pct = stats.get("test_pct", 20)
        is_temporal = stats.get("is_temporal", False)
        return (f"{'Time-aware chronological' if is_temporal else 'Random'} split: "
                f"{n_train} training samples ({100 - test_pct}%), {n_test} test samples ({test_pct}%). "
                f"{'Chronological ordering preserved to prevent temporal data leakage — no future data leaks into training.' if is_temporal else 'Stratified random split applied to maintain class distribution.'} "
                f"This split ratio provides sufficient test data for robust evaluation while maximising training signal.")

    elif chart_type == "model_metrics":
        target = stats.get("target", "variable")
        best = stats.get("best_model", "model")
        r2 = stats.get("r2", 0)
        rmse = stats.get("rmse", 0)
        mape = stats.get("mape", 0)
        n_models = stats.get("n_models", 0)
        quality = "excellent" if mape < 10 else "good" if mape < 20 else "moderate" if mape < 50 else "limited"
        return (f"{best} achieved R²={r2:.3f} on {target}, explaining {r2*100:.1f}% of variance across the test set. "
                f"RMSE of {rmse:.3f} and MAPE of {mape:.1f}% indicate {quality} forecast accuracy. "
                f"Selected from {n_models} candidate models using weighted composite scoring (35% RMSE, 25% MAPE, 25% R², 15% CV stability).")

    elif chart_type == "drift":
        target = stats.get("target", "variable")
        n_flagged = stats.get("n_flagged", 0)
        biggest = stats.get("biggest_metric", "")
        biggest_pct = float(stats.get("biggest_pct", 0))
        if n_flagged > 0:
            return (f"Drift analysis for {target}: {n_flagged} of 4 metrics showed drift >5% between training CV and test evaluation. "
                    f"Largest drift in {biggest.upper()} at {biggest_pct:.1f}%, suggesting potential distribution shift between training and test periods. "
                    f"This target requires close monitoring in production and may benefit from periodic retraining.")
        return (f"Drift analysis for {target}: all metrics stable between training CV and test evaluation. "
                f"No metric exceeded the 5% drift threshold, confirming robust model generalisation to unseen data.")

    elif chart_type == "comparison_table":
        n_targets = stats.get("n_targets", 0)
        avg_r2 = stats.get("avg_r2", 0)
        best_target = stats.get("best_target", "")
        worst_target = stats.get("worst_target", "")
        quality = "strong" if avg_r2 > 0.8 else "moderate" if avg_r2 > 0.5 else "limited"
        return (f"Across {n_targets} target variables, average R²={avg_r2:.3f} indicates {quality} overall predictive capability. "
                f"{best_target} achieved the strongest fit while {worst_target} proved most challenging. "
                f"{'Overall pipeline demonstrates production-ready accuracy.' if avg_r2 > 0.8 else 'Targets with lower R² may benefit from additional feature engineering or domain-specific transformations.'}")

    elif chart_type == "executive_summary":
        project = stats.get("project", "Project")
        n_targets = stats.get("n_targets", 0)
        avg_r2 = stats.get("avg_r2", 0)
        dominant = stats.get("dominant_model", "")
        problem_targets = stats.get("problem_targets", "")
        # problem_targets can be int (count) or str (comma-separated names)
        if isinstance(problem_targets, str):
            problem_count = len([p.strip() for p in problem_targets.split(",") if p.strip()]) if problem_targets else 0
            problem_label = problem_targets
        else:
            problem_count = int(problem_targets)
            problem_label = f"{problem_count} target{'s' if problem_count != 1 else ''}"
        if problem_count > 0:
            return (f"{project}: {n_targets} target variable{'s' if n_targets != 1 else ''} analysed with {dominant} emerging as the dominant model. "
                    f"Average R²={avg_r2:.3f} across all targets. "
                    f"Low-confidence targets: {problem_label} — flagged for production monitoring.")
        return (f"{project}: {n_targets} target variable{'s' if n_targets != 1 else ''} analysed with {dominant} emerging as the dominant model. "
                f"Average R²={avg_r2:.3f} across all targets. All models passed validation with acceptable drift levels.")

    elif chart_type == "model_summary":
        model_type = stats.get("model_type", "")
        target = stats.get("target", "variable")
        if model_type == "tree":
            top_feat = stats.get("top_feature", "")
            top_imp = stats.get("top_importance", 0)
            return (f"The best model for {target} is tree-based. Top predictive feature: {top_feat} "
                    f"(importance={top_imp:.4f}). Feature importances indicate the relative contribution "
                    f"of each predictor to the model's split decisions and overall prediction quality.")
        elif model_type == "linear":
            return (f"The best model for {target} is linear (Ridge/OLS). "
                    f"Coefficients represent the marginal effect of each standardised feature on the target, "
                    f"holding other features constant. Larger absolute values indicate stronger predictive influence.")
        elif model_type == "statsmodels":
            aic = stats.get("aic", "N/A")
            bic = stats.get("bic", "N/A")
            return (f"The best model for {target} is a statsmodels time-series model (AIC={aic}, BIC={bic}). "
                    f"Lower AIC/BIC values indicate better model fit with parsimony penalty. "
                    f"The model summary below provides coefficient estimates and diagnostic statistics.")
        return f"Model summary for {target}."

    elif chart_type == "per_model_forecast":
        model = stats.get("model", "model")
        target = stats.get("target", "variable")
        r2 = stats.get("r2", 0)
        rmse = stats.get("rmse", 0)
        quality = "strong" if r2 > 0.8 else "moderate" if r2 > 0.5 else "weak" if r2 > 0 else "poor"
        return (f"{model} shows {quality} predictive performance on {target} (R2={r2:.3f}, RMSE={rmse:.3f}). "
                f"{'This model is competitive for production deployment.' if r2 > 0.8 else 'Performance gap versus the best model suggests this architecture may not be optimal for this target.'}")

    return ""


# ── LLM Description Generator (v5) ───────────────────────────────────────────

_ANTHROPIC_API_KEY_CACHE = None


def _load_api_key() -> str:
    """Load Anthropic API key: env var first, then auth-profiles.json fallback."""
    global _ANTHROPIC_API_KEY_CACHE
    if _ANTHROPIC_API_KEY_CACHE is not None:
        return _ANTHROPIC_API_KEY_CACHE

    # 1. Environment variable
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        _ANTHROPIC_API_KEY_CACHE = key
        return key

    # 2. auth-profiles.json fallback
    try:
        ap_path = Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json"
        if ap_path.exists():
            with open(ap_path, "r") as f:
                data = json.load(f)
            key = data.get("profiles", {}).get("anthropic:default", {}).get("key", "")
            if key:
                _ANTHROPIC_API_KEY_CACHE = key
                return key
    except Exception:
        pass

    _ANTHROPIC_API_KEY_CACHE = ""
    return ""


def _load_description_cache(cache_dir: Path) -> dict:
    """Load description cache from a directory."""
    if cache_dir is None:
        return {}
    cache_path = cache_dir / "description_cache.json"
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_description_cache(cache_dir: Path, cache: dict):
    """Save description cache to a directory."""
    if cache_dir is None:
        return
    cache_path = cache_dir / "description_cache.json"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def llm_describe(context_type: str, stats: dict, cache_dir: Path = None) -> str:
    """
    Generate a rich, data-specific description using Anthropic Sonnet API.
    Falls back to generate_chart_conclusion() if API is unavailable.

    Args:
        context_type: Type of chart/table (distribution, correlation, model_metrics, etc.)
        stats: Dict of data values to reference in the description
        cache_dir: Directory for caching descriptions (description_cache.json)

    Returns:
        2-4 sentence description referencing actual data values.
    """
    import hashlib

    # 1. Cache lookup
    stats_str = json.dumps(stats, sort_keys=True, default=str)
    cache_key = f"{context_type}_{hashlib.md5(stats_str.encode()).hexdigest()}"

    cache = _load_description_cache(cache_dir)
    if cache_key in cache:
        return cache[cache_key]

    # 2. Try Anthropic Sonnet API
    api_key = _load_api_key()
    if api_key:
        try:
            import urllib.request
            prompt = (
                f"You are a senior data scientist writing a report description.\n"
                f"Context: {context_type}\n"
                f"Data: {stats_str}\n\n"
                f"Write 2-4 sentences. Reference actual numbers from the data provided. "
                f"Structure: What it shows → What it means → Modeling/business implication. "
                f"Output ONLY the description text, nothing else."
            )
            payload = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = ""
                for block in result.get("content", []):
                    if block.get("type") == "text":
                        text += block.get("text", "")
                text = text.strip()
                if text and len(text) > 20:
                    # Cache and return
                    cache[cache_key] = text
                    _save_description_cache(cache_dir, cache)
                    return text
        except Exception as e:
            print(f"    LLM describe fallback ({context_type}): {e}")

    # 3. Fallback to rule-based
    fallback = generate_chart_conclusion(context_type, stats)
    if fallback:
        cache[cache_key] = fallback
        _save_description_cache(cache_dir, cache)
    return fallback


# ── Date-Derived Column Helper (CR7) ──────────────────────────────────────────

def drop_date_derived_cols(df):
    """Drop date-derived columns from a DataFrame for modeling."""
    cols_to_drop = [c for c in df.columns if any(
        c.endswith(s) for s in DATE_DERIVED_SUFFIXES)]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop, errors="ignore")
    return df


def is_date_derived(col: str) -> bool:
    """Check if a column name ends with a date-derived suffix."""
    return any(col.endswith(s) for s in DATE_DERIVED_SUFFIXES)


# ── Artifact I/O ─────────────────────────────────────────────────────────────

def save_artifact(phase: str, filename: str, data, mode: str = "auto") -> Path:
    out_dir = ARTIFACTS_DIR / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    ext = Path(filename).suffix.lower()
    if ext == ".json" or (mode == "json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=_json_serialiser)
    elif ext == ".pkl" or (mode == "pkl"):
        with open(path, "wb") as f:
            pickle.dump(data, f)
    elif ext == ".csv" or (mode == "csv"):
        data.to_csv(path, index=False)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(data))
    return path


def load_artifact(phase: str, filename: str, mode: str = "auto"):
    path = ARTIFACTS_DIR / phase / filename
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    ext = Path(filename).suffix.lower()
    if ext == ".json" or (mode == "json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif ext == ".pkl" or (mode == "pkl"):
        with open(path, "rb") as f:
            return pickle.load(f)
    elif ext == ".csv" or (mode == "csv"):
        import pandas as pd
        return pd.read_csv(path)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


# ── Task Type Auto-Detection ──────────────────────────────────────────────────

def get_task_type_auto(df, target_col: str) -> str:
    import pandas as pd
    import numpy as np
    if target_col is None or target_col not in df.columns:
        return "segmentation"
    y = df[target_col].dropna()
    n_unique = y.nunique()
    dtype = y.dtype
    has_datetime = any(
        pd.api.types.is_datetime64_any_dtype(df[c]) or
        (df[c].dtype == object and _looks_like_date(df[c]))
        for c in df.columns if c != target_col
    )
    if pd.api.types.is_numeric_dtype(dtype):
        if n_unique <= 20:
            return "classification"
        if has_datetime and n_unique > 20:
            return "forecasting"
        return "regression"
    else:
        if n_unique <= 20:
            return "classification"
        return "segmentation"


def _looks_like_date(series) -> bool:
    import pandas as pd
    sample = series.dropna().head(10)
    try:
        pd.to_datetime(sample, infer_datetime_format=True, errors="raise")
        return True
    except Exception:
        return False


# ── Report Versioning ─────────────────────────────────────────────────────────

def get_report_version(project_name: str) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    yy = now.strftime("%y")
    mm = now.strftime("%m")
    pattern = re.compile(
        rf"^{re.escape(project_name)}-ds-v{yy}\.{mm}\.(\d{{2}})\.html$")
    max_vv = 0
    for f in REPORTS_DIR.iterdir():
        m = pattern.match(f.name)
        if m:
            max_vv = max(max_vv, int(m.group(1)))
    vv = str(max_vv + 1).zfill(2)
    return f"{yy}.{mm}.{vv}"


def get_report_path(project_name: str) -> Path:
    version = get_report_version(project_name)
    filename = f"{project_name}-ds-v{version}.html"
    return REPORTS_DIR / filename, version


# ── Date Helper ───────────────────────────────────────────────────────────────

def get_today_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ── JSON Serialiser ───────────────────────────────────────────────────────────

def _json_serialiser(obj):
    import numpy as np
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serialisable")


# ── Artifact Cleanup ──────────────────────────────────────────────────────────

def cleanup_artifacts(delay_seconds: int = 0, artifacts_dir: Path = None) -> bool:
    import shutil
    import time
    target_dir = Path(artifacts_dir) if artifacts_dir else ARTIFACTS_DIR
    try:
        target_dir = target_dir.resolve()
    except OSError:
        pass
    if not target_dir.exists():
        print("info: Artifacts directory does not exist - nothing to clean.")
        return False
    try:
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        total_bytes = sum(
            f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
        total_mb = total_bytes / (1024 * 1024)
        shutil.rmtree(target_dir)
        print(f"Cleaned artifacts/ - freed {total_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"Warning: Artifact cleanup failed: {e}")
        return False


# ── Plotly Layout Defaults ────────────────────────────────────────────────────

def plotly_layout(title: str = "", xaxis_title: str = "", yaxis_title: str = "",
                  height: int = 370) -> dict:
    return {
        "title": {"text": title, "font": {"size": 14}},
        "height": height,
        "font": {"family": '"Helvetica Neue",Helvetica,Arial,sans-serif', "size": 11},
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor": "#FFFFFF",
        "margin": {"t": 50, "b": 60, "l": 60, "r": 30},
        "xaxis": {"title": xaxis_title, "gridcolor": "#E5E5E5"},
        "yaxis": {"title": yaxis_title, "gridcolor": "#E5E5E5"},
    }


# ── Shared Metric Computation ────────────────────────────────────────────────

def compute_regression_metrics(y_true, y_pred, cv_scores=None) -> dict:
    """Compute all 6 regression metrics + MAPE warning flags (CR14, CR15)."""
    import numpy as np
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # Replace NaN with 0 for safety
    y_pred = np.nan_to_num(y_pred, nan=0.0, posinf=0.0, neginf=0.0)

    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_true, y_pred))
    mask = y_true != 0
    mape = float(np.mean(np.abs(
        (y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.any() else 0.0
    r2 = float(r2_score(y_true, y_pred))

    cv_mean = 0.0
    cv_std = 0.0
    if cv_scores is not None and len(cv_scores) > 0:
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))

    result = {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
        "cv_mean": round(cv_mean, 4),
        "cv_std": round(cv_std, 4),
    }

    # MAPE warning flags (CR14, CR15)
    if mape > 200:
        result["mape_flag"] = "extreme"
        result["mape_note"] = "Near-zero actual values inflate MAPE"
    elif mape > 100:
        result["mape_flag"] = "high"
        result["mape_note"] = "MAPE > 100% may indicate near-zero actuals"
    else:
        result["mape_flag"] = "normal"

    # R2 warning
    result["r2_warning"] = r2 < 0

    return result
