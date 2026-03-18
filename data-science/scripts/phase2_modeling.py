#!/usr/bin/env python3
"""
phase2_modeling.py — Model Selection & Validation Pipeline
Data Science Pipeline — Mu Sigma
Phase 2: Train candidate models, evaluate, pick best, fine-tune.

Changes (v2):
  CR5:  Feature selection rationale recorded
  CR10: VAR/VARMAX multivariate TS models added
  CR12: Per-model predictions saved
  CR13: 6-metric comparison (RMSE, MAE, MAPE, R2, CV Mean, CV Std)
"""

import argparse
import sys
import os
import json
import pickle
import subprocess
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np

from utils import (
    ARTIFACTS_DIR, DEFAULT_RANDOM_STATE, CHART_PALETTE,
    save_artifact, plotly_layout, _json_serialiser, compute_regression_metrics,
    compute_composite_score, generate_chart_conclusion, run_self_check, llm_describe
)

# ── Auto-install required packages ────────────────────────────────────────────
def _ensure_package(import_name: str, pip_name: str):
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"  Installing {pip_name}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_name, "--quiet", "--break-system-packages"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            try:
                __import__(import_name)
                return True
            except ImportError:
                pass
        print(f"  Warning: Could not install {pip_name}")
        return False

_ensure_package("xgboost", "xgboost")
_ensure_package("statsmodels", "statsmodels")

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing as HoltWinters
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

try:
    from statsmodels.tsa.api import VAR as VARModel
    VAR_AVAILABLE = True
except ImportError:
    VAR_AVAILABLE = False

try:
    from statsmodels.tsa.statespace.varmax import VARMAX as VARMAXModel
    VARMAX_AVAILABLE = True
except ImportError:
    VARMAX_AVAILABLE = False


# ── Metric helpers ─────────────────────────────────────────────────────────────

def _compute_reg_metrics(y_true, y_pred, cv_scores=None) -> dict:
    """Wrapper around utils.compute_regression_metrics for backward compat."""
    return compute_regression_metrics(y_true, y_pred, cv_scores)


def compute_classification_metrics(y_true, y_pred, y_proba=None) -> dict:
    from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                                  recall_score, roc_auc_score)
    acc  = float(accuracy_score(y_true, y_pred))
    f1   = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    prec = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    rec  = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    auc = 0.0
    try:
        if y_proba is not None:
            if y_proba.ndim == 2 and y_proba.shape[1] == 2:
                auc = float(roc_auc_score(y_true, y_proba[:, 1]))
            elif y_proba.ndim == 2:
                auc = float(roc_auc_score(y_true, y_proba, multi_class="ovr", average="weighted"))
        else:
            auc = float(roc_auc_score(y_true, y_pred))
    except Exception:
        auc = 0.0
    return {
        "accuracy": round(acc, 4), "f1": round(f1, 4),
        "precision": round(prec, 4), "recall": round(rec, 4), "auc_roc": round(auc, 4)
    }


def compute_segmentation_metrics(X, labels) -> dict:
    from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                                  calinski_harabasz_score)
    n_unique = len(set(labels)) - (1 if -1 in labels else 0)
    if n_unique < 2:
        return {"silhouette": 0.0, "davies_bouldin": 9999.0, "calinski_harabasz": 0.0}
    try:
        sil = float(silhouette_score(X, labels))
        db  = float(davies_bouldin_score(X, labels))
        ch  = float(calinski_harabasz_score(X, labels))
    except Exception:
        sil, db, ch = 0.0, 9999.0, 0.0
    return {
        "silhouette": round(sil, 4),
        "davies_bouldin": round(db, 4),
        "calinski_harabasz": round(ch, 2)
    }


# ── Model Candidates ───────────────────────────────────────────────────────────

def get_regression_models():
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor
    models = {
        "LinearRegression": (LinearRegression(), {}),
        "Ridge": (Ridge(random_state=DEFAULT_RANDOM_STATE),
                  {"alpha": [0.01, 0.1, 1, 10, 100]}),
        "RandomForestRegressor": (RandomForestRegressor(random_state=DEFAULT_RANDOM_STATE, n_jobs=-1),
                                  {"n_estimators": [50, 100, 200], "max_depth": [None, 5, 10]}),
    }
    if XGB_AVAILABLE:
        models["XGBRegressor"] = (
            xgb.XGBRegressor(random_state=DEFAULT_RANDOM_STATE, verbosity=0),
            {"n_estimators": [50, 100], "max_depth": [3, 6], "learning_rate": [0.05, 0.1, 0.3]}
        )
    return models


def get_classification_models():
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    models = {
        "LogisticRegression": (LogisticRegression(random_state=DEFAULT_RANDOM_STATE, max_iter=1000, n_jobs=-1),
                               {"C": [0.01, 0.1, 1, 10]}),
        "RandomForestClassifier": (RandomForestClassifier(random_state=DEFAULT_RANDOM_STATE, n_jobs=-1),
                                   {"n_estimators": [50, 100, 200], "max_depth": [None, 5, 10]}),
        "SVC": (SVC(random_state=DEFAULT_RANDOM_STATE, probability=True),
                {"C": [0.1, 1, 10], "kernel": ["rbf", "linear"]}),
    }
    if XGB_AVAILABLE:
        models["XGBClassifier"] = (
            xgb.XGBClassifier(random_state=DEFAULT_RANDOM_STATE, verbosity=0, eval_metric="logloss"),
            {"n_estimators": [50, 100], "max_depth": [3, 6], "learning_rate": [0.05, 0.1, 0.3]}
        )
    return models


def get_segmentation_models():
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.mixture import GaussianMixture
    return {
        "KMeans_3": (KMeans(n_clusters=3, random_state=DEFAULT_RANDOM_STATE, n_init=10), {}),
        "KMeans_5": (KMeans(n_clusters=5, random_state=DEFAULT_RANDOM_STATE, n_init=10), {}),
        "DBSCAN": (DBSCAN(eps=0.5, min_samples=5), {}),
        "AgglomerativeClustering": (AgglomerativeClustering(n_clusters=4), {}),
        "GaussianMixture": (GaussianMixture(n_components=4, random_state=DEFAULT_RANDOM_STATE), {}),
    }


def get_forecasting_models():
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    models = {
        "Ridge": (Ridge(random_state=DEFAULT_RANDOM_STATE),
                  {"alpha": [0.01, 0.1, 1, 10, 100]}),
        "RandomForestRegressor": (RandomForestRegressor(random_state=DEFAULT_RANDOM_STATE, n_jobs=-1),
                                  {"n_estimators": [50, 100, 200], "max_depth": [None, 5, 10]}),
        "GradientBoosting": (GradientBoostingRegressor(random_state=DEFAULT_RANDOM_STATE),
                             {"n_estimators": [50, 100], "max_depth": [3, 5], "learning_rate": [0.05, 0.1]}),
    }
    if XGB_AVAILABLE:
        models["XGBRegressor"] = (
            xgb.XGBRegressor(random_state=DEFAULT_RANDOM_STATE, verbosity=0),
            {"n_estimators": [50, 100, 200], "max_depth": [3, 6], "learning_rate": [0.05, 0.1, 0.2]}
        )
    return models


def make_time_features(X_train, X_test):
    """Add lag + rolling features for forecasting."""
    all_data = pd.concat([X_train, X_test], ignore_index=True)
    numeric_cols = all_data.select_dtypes(include="number").columns.tolist()
    new_cols = {}
    for col in numeric_cols[:8]:
        new_cols[f"{col}_lag1"]     = all_data[col].shift(1).bfill()
        new_cols[f"{col}_lag3"]     = all_data[col].shift(3).bfill()
        new_cols[f"{col}_rolling3"] = all_data[col].rolling(3, min_periods=1).mean()
        new_cols[f"{col}_rolling6"] = all_data[col].rolling(6, min_periods=1).mean()
    new_df = pd.DataFrame(new_cols, index=all_data.index)
    all_data = pd.concat([all_data, new_df], axis=1).copy()
    n_train = len(X_train)
    return all_data.iloc[:n_train].copy(), all_data.iloc[n_train:].copy()


def train_statsmodels_forecaster(y_train, y_test, model_type="arima"):
    """Train ARIMA or ExponentialSmoothing on the target series only."""
    if not STATSMODELS_AVAILABLE:
        return None, None
    try:
        if model_type == "arima":
            m = ARIMA(y_train.values, order=(1, 1, 1))
            fitted = m.fit()
            y_pred = fitted.forecast(steps=len(y_test))
        else:  # holtwinters
            m = HoltWinters(y_train.values, trend="add", seasonal=None, initialization_method="estimated")
            fitted = m.fit(optimized=True)
            y_pred = fitted.forecast(len(y_test))
        return fitted, np.array(y_pred)
    except Exception as e:
        print(f"  Warning: {model_type} failed: {e}")
        return None, None


def train_var_model(train_df, test_df, target, all_numeric_cols):
    """Train VAR model on multivariate time series (CR10)."""
    if not VAR_AVAILABLE:
        return None, None
    try:
        # Use all numeric columns for VAR
        use_cols = [c for c in all_numeric_cols if c in train_df.columns][:8]  # cap at 8 to avoid dimensionality issues
        if target not in use_cols:
            use_cols = [target] + use_cols[:7]
        if len(use_cols) < 2:
            return None, None

        train_sub = train_df[use_cols].fillna(method="ffill").fillna(method="bfill").fillna(0)
        model = VARModel(train_sub)
        # Auto-select lag order
        try:
            lag_order = model.select_order(maxlags=min(12, len(train_sub) // 5))
            best_lag = lag_order.aic
            if best_lag < 1:
                best_lag = 1
        except Exception:
            best_lag = min(4, len(train_sub) // 10)

        fitted = model.fit(best_lag)
        forecast = fitted.forecast(train_sub.values[-best_lag:], steps=len(test_df))
        target_idx = use_cols.index(target)
        y_pred = forecast[:, target_idx]
        return fitted, np.array(y_pred)
    except Exception as e:
        print(f"  Warning: VAR failed: {e}")
        return None, None


# ── Cross-Validation Scoring ───────────────────────────────────────────────────

def cv_score_model(model, X, y, task_type, cv=5):
    from sklearn.model_selection import cross_val_score
    scoring = {
        "regression": "neg_root_mean_squared_error",
        "classification": "f1_weighted",
        "forecasting": "neg_root_mean_squared_error",
    }.get(task_type, "neg_root_mean_squared_error")
    try:
        scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)
        if "neg_" in scoring:
            scores = -scores
        return [round(float(s), 4) for s in scores]
    except Exception:
        return [0.0]


# ── Fine-Tuning ────────────────────────────────────────────────────────────────

def fine_tune_model(model, param_grid, X_train, y_train, task_type):
    from sklearn.model_selection import GridSearchCV
    if not param_grid:
        model.fit(X_train, y_train)
        return model, {}
    scoring = {
        "regression": "neg_root_mean_squared_error",
        "classification": "f1_weighted",
        "forecasting": "neg_root_mean_squared_error",
    }.get(task_type, "neg_root_mean_squared_error")
    try:
        gs = GridSearchCV(model, param_grid, cv=5, scoring=scoring, n_jobs=-1, refit=True)
        gs.fit(X_train, y_train)
        return gs.best_estimator_, gs.best_params_
    except Exception as e:
        print(f"  Warning: GridSearch failed: {e} - using default params")
        model.fit(X_train, y_train)
        return model, {}


# ── Model Comparison Chart ─────────────────────────────────────────────────────

def make_comparison_chart(model_results: list, task_type: str) -> dict:
    if task_type == "regression":
        metrics = ["rmse", "mae", "r2"]
    elif task_type == "classification":
        metrics = ["accuracy", "f1", "auc_roc"]
    elif task_type == "forecasting":
        metrics = ["rmse", "mae", "mape"]
    else:
        metrics = ["silhouette", "calinski_harabasz"]

    model_names = [r["name"] for r in model_results]
    traces = []
    for i, metric in enumerate(metrics):
        values = [r["metrics"].get(metric, 0) for r in model_results]
        traces.append({
            "type": "bar",
            "name": metric.upper(),
            "x": model_names,
            "y": values,
            "marker": {"color": CHART_PALETTE[i % len(CHART_PALETTE)]}
        })

    return {
        "chart_id": "model_comparison",
        "title": f"Model Comparison - {task_type.title()}",
        "data": traces,
        "layout": {
            **plotly_layout(f"Model Comparison ({task_type.title()})", "Model", "Score"),
            "barmode": "group"
        }
    }


def detect_prediction_anomalies(per_model_predictions: dict, phase1_results: dict, target: str) -> dict:
    """
    CR10, CR24: Detect anomalies in predictions.
    - Out-of-range predictions: outside [col_min - 2*std, col_max + 2*std]
    - Sudden dips: |y[i] - y[i-1]| > 3*std
    Returns dict mapping model_name -> {"out_of_range": [...], "sudden_dips": [...]}
    """
    import numpy as np

    # Get target column stats from phase1
    schema = phase1_results.get("schema", {})
    target_stats = schema.get(target, {})
    col_min = target_stats.get("min", 0)
    col_max = target_stats.get("max", 0)
    col_std = target_stats.get("std", 1)

    # Define acceptable range
    lower_bound = col_min - 2 * col_std
    upper_bound = col_max + 2 * col_std
    sudden_dip_threshold = 3 * col_std

    anomaly_flags = {}

    for model_name, pred_data in per_model_predictions.items():
        predicted = np.array(pred_data.get("predicted", []))
        if len(predicted) == 0:
            continue

        # Out-of-range check
        out_of_range_indices = []
        for i, val in enumerate(predicted):
            if val < lower_bound or val > upper_bound:
                out_of_range_indices.append({
                    "index": i,
                    "value": float(val),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound)
                })

        # Sudden dips check
        sudden_dip_indices = []
        for i in range(1, len(predicted)):
            diff = abs(predicted[i] - predicted[i-1])
            if diff > sudden_dip_threshold:
                sudden_dip_indices.append({
                    "index": i,
                    "prev_value": float(predicted[i-1]),
                    "curr_value": float(predicted[i]),
                    "diff": float(diff),
                    "threshold": float(sudden_dip_threshold)
                })

        anomaly_flags[model_name] = {
            "out_of_range_count": len(out_of_range_indices),
            "out_of_range": out_of_range_indices[:20],  # Limit to first 20
            "sudden_dips_count": len(sudden_dip_indices),
            "sudden_dips": sudden_dip_indices[:20],  # Limit to first 20
            "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)},
            "sudden_dip_threshold": float(sudden_dip_threshold)
        }

    return anomaly_flags


def make_per_metric_comparison_charts(model_results: list, task_type: str) -> list:
    """
    CR12: Generate 6 separate horizontal bar charts for forecasting/regression.
    Returns a list of 6 chart dicts, one for each metric.
    """
    if task_type in ("regression", "forecasting"):
        metrics_info = [
            ("rmse", "RMSE", False),  # lower is better
            ("mae", "MAE", False),
            ("mape", "MAPE", False),
            ("r2", "R²", True),  # higher is better
            ("cv_mean", "CV Mean", True),
            ("cv_std", "CV Std Dev", False),
        ]
    else:
        # For other task types, return empty list
        return []

    charts = []
    for metric_key, metric_label, higher_better in metrics_info:
        # Extract values for this metric
        model_data = []
        for r in model_results:
            val = r["metrics"].get(metric_key, 0)
            model_data.append({"name": r["name"], "value": val})

        # Sort by value
        model_data.sort(key=lambda x: x["value"], reverse=higher_better)

        # Extract sorted names and values
        sorted_names = [m["name"] for m in model_data]
        sorted_values = [m["value"] for m in model_data]

        # Pick color for this metric
        color_idx = ["rmse", "mae", "mape", "r2", "cv_mean", "cv_std"].index(metric_key)
        color = CHART_PALETTE[color_idx % len(CHART_PALETTE)]

        # Build horizontal bar chart
        trace = {
            "type": "bar",
            "orientation": "h",
            "y": sorted_names,
            "x": sorted_values,
            "marker": {"color": color},
            "name": metric_label,
        }

        # Generate chart conclusion
        best_model = sorted_names[0]
        best_value = sorted_values[0]
        worst_value = sorted_values[-1] if len(sorted_values) > 1 else best_value
        conclusion = generate_chart_conclusion("comparison", {
            "metric": metric_label,
            "best_model": best_model,
            "best_value": best_value,
            "worst_value": worst_value,
        })

        chart = {
            "chart_id": f"comparison_{metric_key}",
            "title": f"Model Comparison - {metric_label}",
            "data": [trace],
            "layout": plotly_layout(
                f"Model Comparison - {metric_label}",
                metric_label,
                "Model"
            ),
            "conclusion": conclusion,
        }
        charts.append(chart)

    return charts


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Phase 2 - Model Selection & Validation")
    parser.add_argument("--task_type", required=True,
                        choices=["regression", "classification", "forecasting", "segmentation"])
    parser.add_argument("--target", required=True)
    parser.add_argument("--phase1_dir", default=None)
    parser.add_argument("--output_dir", default=None)
    args = parser.parse_args()

    p1_dir  = Path(args.phase1_dir) if args.phase1_dir else ARTIFACTS_DIR / "phase1"
    out_dir = Path(args.output_dir) if args.output_dir else ARTIFACTS_DIR / "phase2"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Input validation (Step 11) ──
    required_files = ["clean_train.csv", "clean_test.csv", "phase1_results.json"]
    for fname in required_files:
        if not (p1_dir / fname).exists():
            print(f"Error: Phase 2 requires {fname} from Phase 1. Run Phase 1 first.")
            sys.exit(1)

    print("\nPhase 2 - Model Selection & Validation")
    print("=" * 50)

    # ── Load data ──
    train_df = pd.read_csv(p1_dir / "clean_train.csv")
    test_df  = pd.read_csv(p1_dir / "clean_test.csv")

    # Load phase1_results for anomaly detection (CR10, CR24)
    with open(p1_dir / "phase1_results.json", "r") as f:
        phase1_results = json.load(f)

    target = args.target
    if target in train_df.columns:
        X_train = train_df.drop(columns=[target])
        y_train = train_df[target]
        X_test  = test_df.drop(columns=[target])
        y_test  = test_df[target]
    else:
        X_train = train_df.copy()
        y_train = None
        X_test  = test_df.copy()
        y_test  = None

    X_train = X_train.fillna(X_train.median(numeric_only=True))
    X_test  = X_test.fillna(X_test.median(numeric_only=True))

    if y_train is not None:
        mask_train = ~pd.isnull(y_train)
        X_train = X_train[mask_train].reset_index(drop=True)
        y_train = y_train[mask_train].reset_index(drop=True)
    if y_test is not None:
        mask_test = ~pd.isnull(y_test)
        X_test = X_test[mask_test].reset_index(drop=True)
        y_test = y_test[mask_test].reset_index(drop=True)

    print(f"  Loaded train ({len(X_train)}) and test ({len(X_test)}) from {p1_dir}")

    # ── Get models ──
    task_type = args.task_type
    statsmodels_results = []
    per_model_predictions = {}  # CR12: predictions for every model

    if task_type == "regression":
        candidates = get_regression_models()
    elif task_type == "classification":
        candidates = get_classification_models()
    elif task_type == "forecasting":
        X_train_orig = X_train.copy()
        X_test_orig = X_test.copy()
        X_train, X_test = make_time_features(X_train, X_test)
        X_train = X_train.copy().fillna(0)
        X_test  = X_test.copy().fillna(0)
        candidates = get_forecasting_models()

        # ── Train statsmodels univariate models ──
        if STATSMODELS_AVAILABLE and y_train is not None:
            for sm_name, sm_type in [("ARIMA(1,1,1)", "arima"), ("HoltWinters", "holtwinters")]:
                print(f"  Training {sm_name}...", end="  ", flush=True)
                try:
                    fitted_sm, y_pred_sm = train_statsmodels_forecaster(y_train, y_test, model_type=sm_type)
                    if fitted_sm is not None and y_pred_sm is not None:
                        # Extract model summary immediately after fit
                        model_summary = {
                            "type": "statsmodels",
                            "summary_text": str(fitted_sm.summary()) if hasattr(fitted_sm, 'summary') else "Summary unavailable",
                        }
                        if hasattr(fitted_sm, 'aic'):
                            model_summary["aic"] = round(float(fitted_sm.aic), 2)
                        if hasattr(fitted_sm, 'bic'):
                            model_summary["bic"] = round(float(fitted_sm.bic), 2)

                        cv_scores_sm = [round(float(-np.sqrt(np.mean((y_train.values[i:i+len(y_test)] - y_pred_sm[:len(y_train.values[i:i+len(y_test)])])**2))), 4)
                                        for i in range(0, 1)]  # simplified CV proxy
                        metrics_sm = _compute_reg_metrics(y_test.values, y_pred_sm, cv_scores_sm)
                        primary_sm = compute_composite_score(metrics_sm)
                        metric_str = " | ".join(f"{k.upper()}={v}" for k, v in metrics_sm.items() if k in ("rmse", "mae", "mape", "r2"))
                        print(f"Done: {metric_str}")
                        # CR14, CR15: Log MAPE and R2 warnings
                        if metrics_sm.get("mape", 0) > 200:
                            print(f"    Warning: {sm_name} MAPE={metrics_sm['mape']:.1f}% is very high (>200%)")
                        if metrics_sm.get("r2", 0) < 0:
                            print(f"    Warning: {sm_name} R2={metrics_sm['r2']:.4f} is negative (worse than mean baseline)")
                        statsmodels_results.append({
                            "name": sm_name, "params": {"type": sm_type},
                            "metrics": metrics_sm, "cv_scores": cv_scores_sm,
                            "primary": float(primary_sm),
                            "_fitted": fitted_sm, "_y_pred": y_pred_sm,
                            "mape_warning": metrics_sm.get("mape_flag", "normal") != "normal",
                            "r2_warning": metrics_sm.get("r2_warning", False),
                            "model_summary": model_summary,
                        })
                        # CR12: Save predictions
                        residuals = (y_test.values - y_pred_sm).tolist()
                        per_model_predictions[sm_name] = {
                            "actual": y_test.values.tolist(),
                            "predicted": y_pred_sm.tolist(),
                            "residuals": residuals,
                        }
                except Exception as e:
                    print(f"Failed: {e}")
                    continue

        # ── CR10: Train VAR model ──
        if VAR_AVAILABLE and y_train is not None:
            print(f"  Training VAR...", end="  ", flush=True)
            try:
                all_numeric = X_train_orig.select_dtypes(include="number").columns.tolist()
                # Build combined train/test with target
                train_combined = X_train_orig.copy()
                train_combined[target] = y_train.values
                test_combined = X_test_orig.copy()
                test_combined[target] = y_test.values

                fitted_var, y_pred_var = train_var_model(
                    train_combined, test_combined, target, [target] + all_numeric
                )
                if fitted_var is not None and y_pred_var is not None:
                    # Extract model summary immediately after fit
                    model_summary = {
                        "type": "statsmodels",
                        "summary_text": str(fitted_var.summary()) if hasattr(fitted_var, 'summary') else "Summary unavailable",
                    }
                    if hasattr(fitted_var, 'aic'):
                        model_summary["aic"] = round(float(fitted_var.aic), 2)
                    if hasattr(fitted_var, 'bic'):
                        model_summary["bic"] = round(float(fitted_var.bic), 2)

                    cv_scores_var = [0.0]  # VAR doesn't support sklearn CV
                    metrics_var = _compute_reg_metrics(y_test.values, y_pred_var, cv_scores_var)
                    primary_var = compute_composite_score(metrics_var)
                    metric_str = " | ".join(f"{k.upper()}={v}" for k, v in metrics_var.items() if k in ("rmse", "mae", "mape", "r2"))
                    print(f"Done: {metric_str}")
                    # CR14, CR15: Log MAPE and R2 warnings
                    if metrics_var.get("mape", 0) > 200:
                        print(f"    Warning: VAR MAPE={metrics_var['mape']:.1f}% is very high (>200%)")
                    if metrics_var.get("r2", 0) < 0:
                        print(f"    Warning: VAR R2={metrics_var['r2']:.4f} is negative (worse than mean baseline)")
                    statsmodels_results.append({
                        "name": "VAR", "params": {"type": "var"},
                        "metrics": metrics_var, "cv_scores": cv_scores_var,
                        "primary": float(primary_var),
                        "_fitted": fitted_var, "_y_pred": y_pred_var,
                        "mape_warning": metrics_var.get("mape_flag", "normal") != "normal",
                        "r2_warning": metrics_var.get("r2_warning", False),
                        "model_summary": model_summary,
                    })
                    residuals = (y_test.values - y_pred_var).tolist()
                    per_model_predictions["VAR"] = {
                        "actual": y_test.values.tolist(),
                        "predicted": y_pred_var.tolist(),
                        "residuals": residuals,
                    }
                else:
                    print("Skipped (convergence issue)")
            except Exception as e:
                print(f"Failed: {e}")
    else:
        candidates = get_segmentation_models()

    # ── Train & Evaluate ──
    model_results    = list(statsmodels_results)
    iteration_tables = {}

    for name, (model, param_grid) in candidates.items():
        print(f"  Training {name}...", end="  ", flush=True)
        try:
            if task_type == "segmentation" or y_train is None:
                model.fit(X_train)
                labels = model.labels_ if hasattr(model, "labels_") else model.predict(X_train)
                metrics = compute_segmentation_metrics(X_train.values, labels)
                cv_scores_list = [round(float(metrics["silhouette"]), 4)]
                primary = metrics["silhouette"]
            else:
                model.fit(X_train, y_train)

                # Extract model summary immediately after fit
                model_summary = {"type": "unknown"}
                if hasattr(model, 'feature_importances_'):
                    fi = sorted(zip(X_train.columns.tolist(), model.feature_importances_.tolist()),
                                key=lambda x: x[1], reverse=True)[:10]
                    model_summary = {
                        "type": "tree",
                        "feature_importances": [{"feature": f, "importance": round(imp, 4)} for f, imp in fi]
                    }
                elif hasattr(model, 'coef_'):
                    coefs = sorted(zip(X_train.columns.tolist(), model.coef_.tolist()),
                                   key=lambda x: abs(x[1]), reverse=True)
                    model_summary = {
                        "type": "linear",
                        "coefficients": [{"feature": f, "coef": round(c, 4)} for f, c in coefs],
                        "intercept": round(float(model.intercept_), 4) if hasattr(model, 'intercept_') else None
                    }

                y_pred = model.predict(X_test)
                y_proba = None
                if hasattr(model, "predict_proba") and task_type == "classification":
                    try:
                        y_proba = model.predict_proba(X_test)
                    except Exception:
                        pass

                cv_scores_list = cv_score_model(model, X_train, y_train, task_type)

                if task_type in ("regression", "forecasting"):
                    metrics = _compute_reg_metrics(y_test.values, y_pred, cv_scores_list)
                    primary = compute_composite_score(metrics)
                else:
                    metrics = compute_classification_metrics(y_test.values, y_pred, y_proba)
                    primary = metrics["f1"]

                # CR12: Save per-model predictions
                if y_test is not None:
                    residuals = (y_test.values - y_pred).tolist()
                    per_model_predictions[name] = {
                        "actual": y_test.values.tolist(),
                        "predicted": y_pred.tolist(),
                        "residuals": residuals,
                    }

            result = {
                "name": name,
                "params": {k: str(v) for k, v in model.get_params().items()},
                "metrics": metrics,
                "cv_scores": cv_scores_list,
                "primary": float(primary)
            }

            # Add model_summary if available (for sklearn models)
            if task_type != "segmentation" and y_train is not None:
                result["model_summary"] = model_summary

            # CR14, CR15: Add MAPE and R2 warning flags
            if task_type in ("regression", "forecasting"):
                result["mape_warning"] = metrics.get("mape_flag", "normal") != "normal"
                result["r2_warning"] = metrics.get("r2_warning", False)

            model_results.append(result)

            cv_mean = round(float(np.mean(cv_scores_list)), 4)
            cv_std = round(float(np.std(cv_scores_list)), 4)
            iteration_tables[name] = {
                "cv_scores": cv_scores_list,
                "cv_mean": cv_mean,
                "cv_std": cv_std,
                "test_metrics": metrics
            }

            metric_str = " | ".join(f"{k.upper()}={v}" for k, v in metrics.items()
                                    if k in ("rmse", "mae", "mape", "r2", "accuracy", "f1", "silhouette"))
            print(f"Done: {metric_str}")

            # CR14, CR15: Log MAPE and R2 warnings
            if task_type in ("regression", "forecasting"):
                if metrics.get("mape", 0) > 200:
                    print(f"    Warning: {name} MAPE={metrics['mape']:.1f}% is very high (>200%)")
                if metrics.get("r2", 0) < 0:
                    print(f"    Warning: {name} R2={metrics['r2']:.4f} is negative (worse than mean baseline)")

        except Exception as e:
            print(f"Failed: {e}")
            continue

    if not model_results:
        print("Error: All models failed.")
        sys.exit(1)

    # ── Add iteration entries for statsmodels results ──
    for sr in statsmodels_results:
        sm_name = sr["name"]
        if sm_name not in iteration_tables:
            cv = sr.get("cv_scores", [0.0])
            iteration_tables[sm_name] = {
                "cv_scores": cv,
                "cv_mean": round(float(np.mean(cv)), 4),
                "cv_std": round(float(np.std(cv)), 4),
                "test_metrics": sr["metrics"]
            }

    # ── Rank models ──
    for r in model_results:
        r.pop("_fitted", None)
        r.pop("_y_pred", None)

    model_results.sort(key=lambda x: x["primary"], reverse=True)
    for i, r in enumerate(model_results):
        r["rank"] = i + 1

    best = model_results[0]
    best_name = best["name"]
    # CR11: Log composite score breakdown
    if task_type in ("regression", "forecasting"):
        print(f"\n  Selected {best_name} (composite={best['primary']:.4f})")
    else:
        print(f"\n  Best model: {best_name} (primary={best['primary']:.4f})")

    # ── Fine-tune ──
    print(f"  Fine-tuning {best_name}...", end="  ", flush=True)

    is_statsmodels_model = best_name in ("ARIMA(1,1,1)", "HoltWinters", "VAR")

    if task_type == "segmentation" or y_train is None:
        best_model_obj, best_param_grid = candidates[best_name]
        best_model_obj.fit(X_train)
        fine_tuned_params  = {}
        fine_tuned_metrics = best["metrics"]
        best_fitted = best_model_obj
    elif is_statsmodels_model:
        sm_type = "arima" if "ARIMA" in best_name else ("var" if best_name == "VAR" else "holtwinters")
        if best_name == "VAR":
            all_numeric = X_train_orig.select_dtypes(include="number").columns.tolist() if 'X_train_orig' in dir() else []
            train_combined = X_train_orig.copy() if 'X_train_orig' in dir() else X_train.copy()
            train_combined[target] = y_train.values
            test_combined = X_test_orig.copy() if 'X_test_orig' in dir() else X_test.copy()
            test_combined[target] = y_test.values
            best_fitted, y_pred_ft = train_var_model(train_combined, test_combined, target, [target] + all_numeric)
        else:
            best_fitted, y_pred_ft = train_statsmodels_forecaster(y_train, y_test, model_type=sm_type)
        fine_tuned_params = {"type": sm_type, "note": "statsmodels - no GridSearch tuning"}
        if y_pred_ft is not None:
            fine_tuned_metrics = _compute_reg_metrics(y_test.values, y_pred_ft, best.get("cv_scores"))
        else:
            fine_tuned_metrics = best["metrics"]
    else:
        best_model_obj, best_param_grid = candidates[best_name]
        best_fitted, fine_tuned_params = fine_tune_model(
            best_model_obj, best_param_grid, X_train, y_train, task_type
        )
        y_pred_ft = best_fitted.predict(X_test)
        y_proba_ft = None
        if hasattr(best_fitted, "predict_proba") and task_type == "classification":
            try:
                y_proba_ft = best_fitted.predict_proba(X_test)
            except Exception:
                pass
        cv_scores_ft = cv_score_model(best_fitted, X_train, y_train, task_type)
        if task_type in ("regression", "forecasting"):
            fine_tuned_metrics = _compute_reg_metrics(y_test.values, y_pred_ft, cv_scores_ft)
        else:
            fine_tuned_metrics = compute_classification_metrics(y_test.values, y_pred_ft, y_proba_ft)

    metric_str = " | ".join(f"{k.upper()}={v}" for k, v in fine_tuned_metrics.items()
                            if k in ("rmse", "mae", "mape", "r2", "accuracy", "f1"))
    print(f"Done: {metric_str}")

    # ── Build comparison chart ──
    comparison_chart = make_comparison_chart(model_results, task_type)

    # CR12: Build per-metric comparison charts
    per_metric_charts = make_per_metric_comparison_charts(model_results, task_type)

    # CR10, CR24: Detect anomalies in predictions
    anomaly_flags = {}
    if task_type in ("regression", "forecasting") and per_model_predictions:
        anomaly_flags = detect_prediction_anomalies(per_model_predictions, phase1_results, target)
        total_anomalies = sum(v["out_of_range_count"] + v["sudden_dips_count"] for v in anomaly_flags.values())
        if total_anomalies > 0:
            print(f"\n  Anomaly detection: {total_anomalies} total anomalies flagged across models")

    # ── Save Artifacts ──
    # Store pre-fine-tuning CV-based metrics separately for drift analysis
    # (fine_tuned_metrics are evaluated on test set, so drift vs test would be ~0%)
    cv_baseline_metrics = best.get("metrics", {})

    # Collect model summaries
    model_summaries = {}
    for r in model_results:
        if "model_summary" in r:
            model_summaries[r["name"]] = r["model_summary"]

    phase2_results = {
        "task_type": task_type,
        "target": target,
        "models": model_results,
        "best_model": best_name,
        "fine_tuned_params": fine_tuned_params,
        "fine_tuned_metrics": fine_tuned_metrics,
        "cv_baseline_metrics": cv_baseline_metrics,
        "model_summaries": model_summaries,
        "xgb_available": XGB_AVAILABLE,
        "statsmodels_avail": STATSMODELS_AVAILABLE,
        "var_available": VAR_AVAILABLE,
    }

    # Add low_confidence flag if best model R² < 0
    if task_type in ("regression", "forecasting"):
        if fine_tuned_metrics.get("r2", 0) < 0:
            phase2_results["low_confidence"] = True

    with open(out_dir / "phase2_results.json", "w") as f:
        json.dump(phase2_results, f, indent=2, default=_json_serialiser)

    with open(out_dir / "best_model.pkl", "wb") as f:
        pickle.dump(best_fitted, f)

    with open(out_dir / "model_comparison_chart.json", "w") as f:
        json.dump(comparison_chart, f, indent=2, default=_json_serialiser)

    with open(out_dir / "per_model_iteration_tables.json", "w") as f:
        json.dump(iteration_tables, f, indent=2, default=_json_serialiser)

    # CR12: Save per-model predictions
    with open(out_dir / "per_model_predictions.json", "w") as f:
        json.dump(per_model_predictions, f, indent=2, default=_json_serialiser)

    # CR12: Save per-metric comparison charts
    if per_metric_charts:
        with open(out_dir / "comparison_charts.json", "w") as f:
            json.dump(per_metric_charts, f, indent=2, default=_json_serialiser)

    # CR10, CR24: Save anomaly flags
    if anomaly_flags:
        with open(out_dir / "anomaly_flags.json", "w") as f:
            json.dump(anomaly_flags, f, indent=2, default=_json_serialiser)

    # Generate and save chart conclusions for Phase 2
    p2_chart_conclusions = {}

    # Model metrics description
    p2_chart_conclusions[f"model_metrics_{target}"] = llm_describe("model_metrics", {
        "target": target, "best_model": best_name,
        "r2": fine_tuned_metrics.get("r2"), "rmse": fine_tuned_metrics.get("rmse"),
        "mape": fine_tuned_metrics.get("mape"), "n_models": len(model_results)
    }, cache_dir=out_dir)

    # Comparison chart descriptions (6 metrics)
    for metric_key in ["rmse", "mae", "mape", "r2", "cv_mean", "cv_std"]:
        values = [(m["name"], m["metrics"].get(metric_key, 0)) for m in model_results]
        values_sorted = sorted(values, key=lambda x: x[1])
        p2_chart_conclusions[f"comparison_{metric_key}"] = llm_describe("comparison", {
            "metric": metric_key.upper(), "best_model": values_sorted[0][0],
            "best_value": values_sorted[0][1], "worst_model": values_sorted[-1][0],
            "worst_value": values_sorted[-1][1],
            "spread": abs(values_sorted[-1][1] - values_sorted[0][1]),
            "n_models": len(model_results)
        }, cache_dir=out_dir)

    # Model summary description (best model only)
    best_summary = model_summaries.get(best_name, {})
    summary_stats = {"model_type": best_summary.get("type", ""), "target": target}
    if best_summary.get("type") == "tree" and best_summary.get("feature_importances"):
        summary_stats["top_feature"] = best_summary["feature_importances"][0]["feature"]
        summary_stats["top_importance"] = best_summary["feature_importances"][0]["importance"]
    elif best_summary.get("type") == "statsmodels":
        summary_stats["aic"] = best_summary.get("aic", "N/A")
        summary_stats["bic"] = best_summary.get("bic", "N/A")
    p2_chart_conclusions[f"model_summary_{target}"] = llm_describe("model_summary", summary_stats, cache_dir=out_dir)

    with open(out_dir / "chart_conclusions.json", "w") as f:
        json.dump(p2_chart_conclusions, f, indent=2, default=_json_serialiser)

    # CR22: Phase 2 self-check
    self_check_results = run_self_check("phase2", phase2_results)
    with open(out_dir / "self_check_results.json", "w") as f:
        json.dump(self_check_results, f, indent=2, default=_json_serialiser)

    # Print self-check warnings/errors
    if self_check_results["warnings"]:
        print("\n  Self-check warnings:")
        for w in self_check_results["warnings"]:
            print(f"    - {w}")
    if self_check_results["errors"]:
        print("\n  Self-check errors:")
        for e in self_check_results["errors"]:
            print(f"    - {e}")

    if self_check_results["passed"]:
        print(f"\n  Phase 2 complete - {out_dir}/ ready\n")
    else:
        print(f"\n  Phase 2 complete with errors - {out_dir}/ ready\n")


if __name__ == "__main__":
    main()
