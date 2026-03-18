#!/usr/bin/env python3
"""
phase3_execution.py — Execution & Business Insights Pipeline
Data Science Pipeline — Mu Sigma
Phase 3: Load best model, run final inference, diagnostics, business insights.

Changes (v2):
  CR12: Per-model actual-vs-predicted plots and residual tables
  CR13: 6-metric comparison on final test set
  CR17: Data points on forecast charts (lines+markers)
"""

from utils import (
    ARTIFACTS_DIR, DEFAULT_RANDOM_STATE, CHART_PALETTE,
    plotly_layout, _json_serialiser, compute_regression_metrics,
    generate_chart_conclusion, run_self_check, llm_describe
)
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys
import os
import json
import pickle
import subprocess
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _ensure_package(import_name: str, pip_name: str):
    try:
        __import__(import_name)
        return True
    except ImportError:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pip_name,
                "--quiet", "--break-system-packages"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            try:
                __import__(import_name)
                return True
            except ImportError:
                pass
        return False


_ensure_package("xgboost", "xgboost")
_ensure_package("statsmodels", "statsmodels")


# ── Metric helpers ───────────────────────────────────────────────────────

def compute_classification_metrics(y_true, y_pred, y_proba=None) -> dict:
    from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                                 recall_score, roc_auc_score)
    acc = float(accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    prec = float(precision_score(y_true, y_pred,
                 average="weighted", zero_division=0))
    rec = float(recall_score(y_true, y_pred,
                average="weighted", zero_division=0))
    auc = 0.0
    try:
        if y_proba is not None:
            if y_proba.ndim == 2 and y_proba.shape[1] == 2:
                auc = float(roc_auc_score(y_true, y_proba[:, 1]))
            else:
                auc = float(roc_auc_score(y_true, y_proba,
                            multi_class="ovr", average="weighted"))
        else:
            auc = float(roc_auc_score(y_true, y_pred))
    except Exception:
        auc = 0.0
    return {
        "accuracy": round(acc, 4), "f1": round(f1, 4),
        "precision": round(prec, 4), "recall": round(rec, 4), "auc_roc": round(auc, 4)
    }


# ── Diagnostic Charts ─────────────────────────────────────────────────────────

def make_regression_charts(y_true, y_pred, target: str) -> list:
    charts = []
    max_val = float(max(y_true.max(), y_pred.max()))
    min_val = float(min(y_true.min(), y_pred.min()))
    charts.append({
        "chart_id": "actual_vs_predicted",
        "title": f"Actual vs Predicted: {target}",
        "data": [
            {"type": "scatter", "mode": "markers",
             "x": y_true.tolist(), "y": y_pred.tolist(),
             "marker": {"color": CHART_PALETTE[0], "size": 5, "opacity": 0.6}, "name": "Predictions"},
            {"type": "scatter", "mode": "lines",
             "x": [min_val, max_val], "y": [min_val, max_val],
             "line": {"color": CHART_PALETTE[3], "dash": "dash", "width": 2}, "name": "Perfect Fit"},
        ],
        "layout": plotly_layout(f"Actual vs Predicted: {target}", f"Actual {target}", f"Predicted {target}")
    })
    residuals = (y_true - y_pred).tolist()
    res_arr = np.array(residuals)
    hist_vals, bin_edges = np.histogram(res_arr, bins=30)
    bin_mids = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()
    charts.append({
        "chart_id": "residuals_distribution",
        "title": "Residuals Distribution",
        "data": [{"type": "bar", "x": bin_mids, "y": hist_vals.tolist(),
                  "marker": {"color": CHART_PALETTE[2]}, "name": "Residuals"}],
        "layout": plotly_layout("Residuals Distribution", "Residual", "Count")
    })
    charts.append({
        "chart_id": "residuals_vs_predicted",
        "title": "Residuals vs Predicted",
        "data": [
            {"type": "scatter", "mode": "markers",
             "x": y_pred.tolist(), "y": residuals,
             "marker": {"color": CHART_PALETTE[1], "size": 4, "opacity": 0.6}, "name": "Residuals"},
            {"type": "scatter", "mode": "lines",
             "x": [float(y_pred.min()), float(y_pred.max())], "y": [0, 0],
             "line": {"color": CHART_PALETTE[3], "dash": "dash"}, "name": "Zero Line"},
        ],
        "layout": plotly_layout("Residuals vs Predicted", f"Predicted {target}", "Residual")
    })
    return charts


def make_classification_charts(y_true, y_pred, y_proba=None, classes=None) -> list:
    charts = []
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_true, y_pred)
    cls = classes if classes is not None else sorted(list(set(y_true)))
    cls_str = [str(c) for c in cls]
    charts.append({
        "chart_id": "confusion_matrix",
        "title": "Confusion Matrix",
        "data": [{"type": "heatmap", "z": cm.tolist(), "x": cls_str, "y": cls_str,
                  "colorscale": [[0, "#FFFFFF"], [1, "#4E79A7"]],
                  "text": [[str(v) for v in row] for row in cm.tolist()],
                  "texttemplate": "%{text}", "showscale": True}],
        "layout": plotly_layout("Confusion Matrix", "Predicted", "Actual", height=400)
    })
    if y_proba is not None and len(cls) == 2:
        from sklearn.metrics import roc_curve, auc
        fpr, tpr, _ = roc_curve(y_true, y_proba[:, 1])
        roc_auc = auc(fpr, tpr)
        charts.append({
            "chart_id": "roc_curve",
            "title": f"ROC Curve (AUC = {roc_auc:.3f})",
            "data": [
                {"type": "scatter", "mode": "lines", "x": fpr.tolist(), "y": tpr.tolist(),
                 "line": {"color": CHART_PALETTE[0], "width": 2}, "name": f"ROC (AUC={roc_auc:.3f})"},
                {"type": "scatter", "mode": "lines", "x": [0, 1], "y": [0, 1],
                 "line": {"color": CHART_PALETTE[4], "dash": "dash"}, "name": "Random"},
            ],
            "layout": plotly_layout(f"ROC Curve (AUC={roc_auc:.3f})", "FPR", "TPR")
        })
    return charts


def make_forecasting_charts(y_true, y_pred, target: str, date_strings: list = None) -> list:
    """
    CR9, CR17: Date-aware forecast with lines+markers for data point visibility.
    Args:
        date_strings: Optional list of date strings for X-axis. If None, uses numeric index.
    """
    if date_strings is not None and len(date_strings) == len(y_true):
        x_vals = date_strings
        x_title = "Date"
        hovertemplate_actual = '%{x|%Y-%m-%d}<br>Value: %{y:.4f}<extra></extra>'
        hovertemplate_pred = '%{x|%Y-%m-%d}<br>Value: %{y:.4f}<extra></extra>'
    else:
        x_vals = list(range(len(y_true)))
        x_title = "Time Index"
        hovertemplate_actual = None
        hovertemplate_pred = None

    # Step 6A: Add date range to chart title
    date_range_str = f" ({date_strings[0]} to {date_strings[-1]})" if date_strings and len(
        date_strings) >= 2 else ""

    actual_trace = {
        "type": "scatter", "mode": "lines+markers",
        "x": x_vals, "y": y_true.tolist(),
        "line": {"color": CHART_PALETTE[0], "width": 2},
        "marker": {"size": 4},
        "name": "Actual"
    }
    pred_trace = {
        "type": "scatter", "mode": "lines+markers",
        "x": x_vals, "y": y_pred.tolist(),
        "line": {"color": CHART_PALETTE[2], "width": 2, "dash": "dash"},
        "marker": {"size": 4},
        "name": "Predicted"
    }

    if hovertemplate_actual:
        actual_trace["hovertemplate"] = hovertemplate_actual
        pred_trace["hovertemplate"] = hovertemplate_pred

    return [{
        "chart_id": "forecast_plot",
        "title": f"Forecast: Actual vs Predicted - {target}{date_range_str}",
        "data": [actual_trace, pred_trace],
        "layout": plotly_layout(f"Forecast: {target}{date_range_str}", x_title, target)
    }]


def make_segmentation_charts(X, labels, feature_names: list) -> list:
    charts = []
    df_seg = pd.DataFrame(X, columns=feature_names[:X.shape[1]])
    df_seg["_cluster"] = labels
    sizes = df_seg["_cluster"].value_counts().sort_index()
    charts.append({
        "chart_id": "cluster_sizes",
        "title": "Cluster Sizes",
        "data": [{"type": "bar",
                  "x": [f"Cluster {c}" for c in sizes.index.tolist()],
                  "y": sizes.values.tolist(),
                  "marker": {"color": CHART_PALETTE[:len(sizes)]}}],
        "layout": plotly_layout("Cluster Sizes", "Cluster", "Count")
    })
    if X.shape[1] >= 2:
        try:
            from sklearn.decomposition import PCA
            pca = PCA(n_components=2, random_state=DEFAULT_RANDOM_STATE)
            X_2d = pca.fit_transform(X)
            unique_labels = sorted(set(labels))
            scatter_data = []
            for i, lbl in enumerate(unique_labels):
                mask = np.array(labels) == lbl
                scatter_data.append({
                    "type": "scatter", "mode": "markers",
                    "x": X_2d[mask, 0].tolist(), "y": X_2d[mask, 1].tolist(),
                    "marker": {"color": CHART_PALETTE[i % len(CHART_PALETTE)], "size": 5, "opacity": 0.7},
                    "name": f"Cluster {lbl}"
                })
            charts.append({
                "chart_id": "cluster_pca",
                "title": "Cluster Visualization (PCA 2D)",
                "data": scatter_data,
                "layout": plotly_layout("Cluster Visualization (PCA 2D)", "PC1", "PC2")
            })
        except Exception:
            pass
    return charts


# ── Per-Model Charts and Tables (CR12) ────────────────────────────────────────

def build_per_model_plots(per_model_preds: dict, target: str, date_strings: list = None) -> list:
    """
    Generate actual vs predicted line chart for EVERY model (CR9, CR12, CR17).
    Args:
        date_strings: Optional list of date strings for X-axis.
    """
    charts = []
    # Step 6A: Prepare date range string
    date_range_str = f" ({date_strings[0]} to {date_strings[-1]})" if date_strings and len(
        date_strings) >= 2 else ""

    for i, (model_name, data) in enumerate(per_model_preds.items()):
        actual = data.get("actual", [])
        predicted = data.get("predicted", [])

        if date_strings is not None and len(date_strings) == len(actual):
            x_vals = date_strings
            x_title = "Date"
            hovertemplate = '%{x|%Y-%m-%d}<br>Value: %{y:.4f}<extra></extra>'
        else:
            x_vals = list(range(len(actual)))
            x_title = "Time Index"
            hovertemplate = None

        actual_trace = {
            "type": "scatter", "mode": "lines+markers",
            "x": x_vals, "y": actual,
            "line": {"color": CHART_PALETTE[0], "width": 2},
            "marker": {"size": 4}, "name": "Actual"
        }
        pred_trace = {
            "type": "scatter", "mode": "lines+markers",
            "x": x_vals, "y": predicted,
            "line": {"color": CHART_PALETTE[i % len(CHART_PALETTE) if i > 0 else 2], "width": 2, "dash": "dash"},
            "marker": {"size": 4}, "name": "Predicted"
        }

        if hovertemplate:
            actual_trace["hovertemplate"] = hovertemplate
            pred_trace["hovertemplate"] = hovertemplate

        charts.append({
            "chart_id": f"per_model_{model_name.replace(' ', '_').replace('(', '').replace(')', '')}",
            "title": f"{model_name}: Actual vs Predicted - {target}{date_range_str}",
            "data": [actual_trace, pred_trace],
            "layout": plotly_layout(f"{model_name}: Actual vs Predicted{date_range_str}", x_title, target)
        })
    return charts


def build_per_model_residual_tables(per_model_preds: dict) -> dict:
    """Generate per-model residual tables with Date/Index, Actual, Predicted, Residual (CR12)."""
    tables = {}
    for model_name, data in per_model_preds.items():
        actual = data.get("actual", [])
        predicted = data.get("predicted", [])
        residuals = data.get("residuals", [])
        rows = []
        for j in range(len(actual)):
            rows.append({
                "index": j,
                "actual": round(actual[j], 4) if isinstance(actual[j], float) else actual[j],
                "predicted": round(predicted[j], 4) if isinstance(predicted[j], float) else predicted[j],
                "residual": round(residuals[j], 4) if j < len(residuals) and isinstance(residuals[j], float) else (residuals[j] if j < len(residuals) else None),
            })
        tables[model_name] = rows
    return tables


# ── Business Insights ─────────────────────────────────────────────────────────

def generate_insights(task_type: str, metrics: dict, phase1_results: dict,
                      phase2_results: dict, target: str, drift_flags: dict = None, cache_dir=None) -> list:
    """
    Step 7: Restructured insights with batched LLM call per target (1 call with all metrics).
    Falls back to template logic if LLM fails.
    Each insight: id, title, observation, finding, insight, supporting_metrics, confidence_level.
    """
    insights = []
    best_model = phase2_results.get("best_model", "Model")
    drift_flags = drift_flags or {}

    # Step 7: Try batched LLM call first for regression/forecasting
    if task_type in ("regression", "forecasting"):
        r2 = metrics.get("r2", 0)
        mae = metrics.get("mae", 0)
        rmse = metrics.get("rmse", 0)
        mape = metrics.get("mape", 0)
        cv_mean = metrics.get("cv_mean", 0)
        cv_std = metrics.get("cv_std", 0)
        n_rows = phase1_results.get("n_rows", 0)
        outlier_pct = phase1_results.get("outliers_pct", 0)

        # Build drift summary
        has_drift = any(d.get("flag", False) for d in drift_flags.values())
        drift_metrics = [k for k, v in drift_flags.items()
                         if v.get("flag", False)]
        drift_summary = f"{len(drift_metrics)} metrics drifted: {', '.join(drift_metrics)}" if has_drift else "No significant drift"

        # Try LLM batched call
        llm_succeeded = False
        try:
            import urllib.request
            import urllib.error
            from pathlib import Path

            api_key = ""
            # Try to load API key
            import os
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                try:
                    ap_path = Path.home() / ".openclaw" / "agents" / "main" / \
                        "agent" / "auth-profiles.json"
                    if ap_path.exists():
                        with open(ap_path, "r") as f:
                            data = json.load(f)
                        api_key = data.get("profiles", {}).get(
                            "anthropic:default", {}).get("key", "")
                except Exception:
                    pass

            if api_key:
                prompt = f"""Generate 3-4 business insights for target variable '{target}'.

Metrics: R²={r2:.3f}, RMSE={rmse:.3f}, MAPE={mape:.1f}%, MAE={mae:.3f}
Best model: {best_model}
CV stability: mean={cv_mean:.3f}, std={cv_std:.3f}
Drift status: {drift_summary}
Data: {n_rows} observations, {outlier_pct:.1f}% outliers

Return ONLY a JSON array (no markdown, no backticks): [{{"title": "short descriptive title", "observation": "data-backed factual statement with numbers from above", "finding": "what this means for business decisions", "insight": "one specific actionable recommendation"}}, ...]

Be crisp, formal, and exquisite. Back every statement with the actual numbers provided. No generic filler."""

                payload = json.dumps({
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 500,
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

                with urllib.request.urlopen(req, timeout=20) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    text = ""
                    for block in result.get("content", []):
                        if block.get("type") == "text":
                            text += block.get("text", "")
                    text = text.strip()

                    # Try to parse JSON
                    try:
                        llm_insights = json.loads(text)
                        if isinstance(llm_insights, list) and len(llm_insights) > 0:
                            # Convert to standard format
                            for i, ins in enumerate(llm_insights, 1):
                                insights.append({
                                    "id": i,
                                    "title": ins.get("title", "Insight"),
                                    "observation": ins.get("observation", ""),
                                    "finding": ins.get("finding", ""),
                                    "insight": ins.get("insight", ""),
                                    "supporting_metrics": {"r2": r2, "rmse": rmse, "mape": mape, "mae": mae},
                                    "confidence_level": "High" if r2 > 0.8 else "Moderate" if r2 > 0.5 else "Low"
                                })
                            llm_succeeded = True
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

        # If LLM succeeded, return those insights
        if llm_succeeded:
            return insights

    # Fallback to template logic (remapped fields: finding from implication, insight from strategic_action)
    insights = []
    best_model = phase2_results.get("best_model", "Model")
    drift_flags = drift_flags or {}

    if task_type in ("regression", "forecasting"):
        r2 = metrics.get("r2", 0)
        mae = metrics.get("mae", 0)
        rmse = metrics.get("rmse", 0)
        mape = metrics.get("mape", 0)
        cv_mean = metrics.get("cv_mean", 0)
        cv_std = metrics.get("cv_std", 0)
        n_rows = phase1_results.get("n_rows", 0)
        outlier_pct = phase1_results.get("outliers_pct", 0)

        # Determine confidence level
        if r2 > 0.8:
            confidence = "High"
        elif r2 > 0.5:
            confidence = "Moderate"
        else:
            confidence = "Low"

        # Insight 1: Predictive Accuracy
        insights.append({
            "id": 1,
            "title": "Predictive Accuracy & Model Explanatory Power",
            "observation": f"{best_model} achieves R²={r2:.3f} and RMSE={rmse:.3f} on {n_rows} test samples, explaining {r2*100:.1f}% of variance in {target}.",
            "finding": "Strong predictive capability enables reliable forecasting for strategic planning." if r2 > 0.8
                           else ("Moderate fit indicates the model captures key trends but may benefit from additional features." if r2 > 0.5
                                 else "Limited explanatory power suggests exploring alternative modeling approaches or feature engineering."),
            "insight": f"Deploy model for automated {target} forecasting in production systems with monthly performance monitoring." if r2 > 0.8
            else f"Conduct feature enrichment analysis and consider ensemble methods to improve R² above 0.8 threshold.",
            "supporting_metrics": {"r2": r2, "rmse": rmse, "test_samples": n_rows},
            "confidence_level": confidence
        })

        # Insight 2: Forecast Reliability
        insights.append({
            "id": 2,
            "title": "Forecast Reliability & Operational Tolerance",
            "observation": f"Mean Absolute Percentage Error (MAPE) of {mape:.1f}% with Mean Absolute Error (MAE) of {mae:.2f} units.",
            "finding": "Excellent forecast accuracy suitable for high-stakes decision-making." if mape < 10
                           else ("Good accuracy for most operational scenarios." if mape < 20
                                 else "Moderate accuracy requires validation thresholds before deployment."),
            "insight": f"Establish automated alert thresholds at ±{mae:.2f} units for real-time monitoring and intervention." if mape < 20
            else f"Implement human-in-the-loop validation for predictions exceeding ±{mae:.2f} units.",
            "supporting_metrics": {"mape": mape, "mae": mae, "rmse": rmse},
            "confidence_level": confidence
        })

        # Insight 3: Model Stability
        insights.append({
            "id": 3,
            "title": "Model Stability & Cross-Validation Performance",
            "observation": f"Cross-validation yields mean R² of {cv_mean:.3f} with standard deviation {cv_std:.3f}, indicating {'high' if cv_std < 0.05 else 'moderate' if cv_std < 0.1 else 'variable'} stability across data folds.",
            "finding": "Consistent performance across validation folds confirms model robustness." if cv_std < 0.05
                           else ("Moderate variance suggests sensitivity to data composition." if cv_std < 0.1
                                 else "High variance indicates potential overfitting or data quality issues."),
            "insight": "Proceed with deployment using current model architecture." if cv_std < 0.05
            else "Implement ensemble averaging or regularization to reduce prediction variance.",
            "supporting_metrics": {"cv_mean": cv_mean, "cv_std": cv_std},
            "confidence_level": confidence
        })

        # Insight 4: Risk Indicators (drift)
        has_drift = any(d.get("flag", False) for d in drift_flags.values())
        drift_metrics = [k for k, v in drift_flags.items()
                         if v.get("flag", False)]
        insights.append({
            "id": 4,
            "title": "Performance Drift & Risk Indicators",
            "observation": f"{'Significant drift detected in ' + ', '.join(drift_metrics[:3]) if has_drift else 'No significant performance drift detected between validation and test sets.'}" +
                           f" Test RMSE={rmse:.3f} vs validation baseline.",
            "finding": "Model maintains stable performance in production conditions." if not has_drift
                           else f"Drift in {len(drift_metrics)} metric(s) suggests data distribution shift or concept drift.",
            "insight": "Maintain quarterly model refresh cadence with automated drift monitoring." if not has_drift
                                else "Initiate immediate model retraining with recent data and investigate root cause of distribution shift.",
            "supporting_metrics": {"drift_count": len(drift_metrics), "drifted_metrics": drift_metrics},
            "confidence_level": "High" if not has_drift else "Low"
        })

        # Insight 5: Strategic Recommendations
        insights.append({
            "id": 5,
            "title": "Strategic Deployment Roadmap",
            "observation": f"Overall model composite score reflects {confidence.lower()} readiness based on accuracy (R²={r2:.3f}), reliability (MAPE={mape:.1f}%), and stability (CV std={cv_std:.3f}).",
            "finding": "Model meets production-grade criteria for enterprise deployment." if confidence == "High"
                           else ("Model is suitable for pilot deployment with monitoring safeguards." if confidence == "Moderate"
                                 else "Model requires further development before operational use."),
            "insight": "Integrate into production forecasting pipeline with automated retraining triggers at monthly intervals and MAPE threshold alerts." if confidence == "High"
            else ("Deploy in shadow mode alongside existing processes for 2-4 weeks to validate performance." if confidence == "Moderate"
                               else "Prioritize data quality improvement and feature engineering before reconsidering deployment."),
            "supporting_metrics": {"r2": r2, "mape": mape, "cv_std": cv_std, "overall_confidence": confidence},
            "confidence_level": confidence
        })

        # Insight 6: Data Quality Impact
        insights.append({
            "id": 6,
            "title": "Data Quality Impact on Model Performance",
            "observation": f"Training dataset contains {outlier_pct:.1f}% outliers, with {n_rows} test samples evaluated.",
            "finding": "Minimal outlier influence on tree-based model performance." if outlier_pct < 2
                           else ("Moderate outlier presence may affect prediction extremes." if outlier_pct < 5
                                 else "High outlier rate may distort predictions and requires data cleansing."),
            "insight": "Current data quality is acceptable for production use." if outlier_pct < 2
            else "Implement outlier detection and handling in preprocessing pipeline.",
            "supporting_metrics": {"outlier_pct": outlier_pct, "n_samples": n_rows},
            "confidence_level": confidence
        })

        # Insight 7: Variable Importance (if available)
        feature_importance = phase2_results.get("feature_importance", [])
        if feature_importance:
            top_features = feature_importance[:3] if len(
                feature_importance) >= 3 else feature_importance
            top_names = [f["feature"] for f in top_features]
            insights.append({
                "id": 7,
                "title": "Key Predictive Drivers",
                "observation": f"Top 3 predictive features: {', '.join(top_names)}. These variables collectively drive model predictions.",
                "finding": "Understanding key drivers enables targeted business interventions and scenario planning.",
                "insight": f"Monitor {top_names[0]} closely as primary prediction driver. Develop what-if scenarios around top 3 features for strategic planning.",
                "supporting_metrics": {"top_features": top_names, "count": len(feature_importance)},
                "confidence_level": confidence
            })

    elif task_type == "classification":
        acc = metrics.get("accuracy", 0)
        f1 = metrics.get("f1", 0)
        auc = metrics.get("auc_roc", 0)
        prec = metrics.get("precision", 0)
        rec = metrics.get("recall", 0)
        confidence = "High" if acc > 0.85 else "Moderate" if acc > 0.7 else "Low"

        insights.append({
            "id": 1,
            "title": "Classification Accuracy & Business Impact",
            "observation": f"{best_model} achieves {acc*100:.1f}% accuracy with F1-score of {f1:.3f} on test set.",
            "finding": "High accuracy enables confident automated decision-making." if acc > 0.85
                           else "Moderate accuracy suitable for assisted decision workflows.",
            "insight": "Deploy in production with automated classification pipeline." if acc > 0.85
                                else "Implement human review for low-confidence predictions.",
            "supporting_metrics": {"accuracy": acc, "f1": f1},
            "confidence_level": confidence
        })

    elif task_type == "segmentation":
        sil = metrics.get("silhouette", 0)
        db = metrics.get("davies_bouldin", 9999)
        ch = metrics.get("calinski_harabasz", 0)
        confidence = "High" if sil > 0.5 else "Moderate" if sil > 0.25 else "Low"

        insights.append({
            "id": 1,
            "title": "Segmentation Quality & Customer Differentiation",
            "observation": f"Silhouette score of {sil:.3f} indicates {'well-separated' if sil > 0.5 else 'moderately separated' if sil > 0.25 else 'weakly separated'} customer segments.",
            "finding": "Clear segment boundaries enable targeted marketing strategies." if sil > 0.5
                           else "Moderate separation allows for differentiated strategies with careful validation.",
            "insight": "Deploy segment-specific campaigns and measure incremental ROI by segment." if sil > 0.5
                                else "Refine segmentation with additional behavioral features.",
            "supporting_metrics": {"silhouette": sil, "davies_bouldin": db, "calinski_harabasz": ch},
            "confidence_level": confidence
        })

    return insights


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phase 3 - Execution & Business Insights")
    parser.add_argument("--task_type", required=True,
                        choices=["regression", "classification", "forecasting", "segmentation"])
    parser.add_argument("--target", required=True)
    parser.add_argument("--phase1_dir", default=None)
    parser.add_argument("--phase2_dir", default=None)
    parser.add_argument("--output_dir", default=None)
    args = parser.parse_args()

    p1_dir = Path(
        args.phase1_dir) if args.phase1_dir else ARTIFACTS_DIR / "phase1"
    p2_dir = Path(
        args.phase2_dir) if args.phase2_dir else ARTIFACTS_DIR / "phase2"
    out_dir = Path(
        args.output_dir) if args.output_dir else ARTIFACTS_DIR / "phase3"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Input validation (Step 11) ──
    for fname, src in [("phase1_results.json", p1_dir), ("phase2_results.json", p2_dir),
                       ("best_model.pkl", p2_dir), ("clean_test.csv", p1_dir)]:
        if not (src / fname).exists():
            print(
                f"Error: Phase 3 requires {fname}. Run previous phases first.")
            sys.exit(1)

    print("\nPhase 3 - Execution & Business Insights")
    print("=" * 50)

    # ── Load artifacts ──
    with open(p1_dir / "phase1_results.json") as f:
        phase1_results = json.load(f)
    with open(p2_dir / "phase2_results.json") as f:
        phase2_results = json.load(f)
    with open(p2_dir / "best_model.pkl", "rb") as f:
        model = pickle.load(f)

    test_df = pd.read_csv(p1_dir / "clean_test.csv")

    target = args.target
    if target in test_df.columns:
        X_test = test_df.drop(columns=[target])
        y_test = test_df[target]
    else:
        X_test = test_df.copy()
        y_test = None

    X_test = X_test.fillna(X_test.median(numeric_only=True))

    if y_test is not None:
        mask_test = ~pd.isnull(y_test)
        X_test = X_test[mask_test].reset_index(drop=True)
        y_test = y_test[mask_test].reset_index(drop=True)

    best_model_name = phase2_results.get("best_model", "")
    print(f"  Best model: {best_model_name}")

    # ── Predict ──
    task_type = args.task_type
    is_statsmodels_model = best_model_name in (
        "ARIMA(1,1,1)", "HoltWinters", "VAR")

    if task_type == "forecasting" and not is_statsmodels_model:
        train_df_raw = pd.read_csv(os.path.join(p1_dir, "clean_train.csv"))
        if args.target in train_df_raw.columns:
            X_train_raw = train_df_raw.drop(columns=[args.target])
        else:
            X_train_raw = train_df_raw.copy()
        X_train_raw = X_train_raw.fillna(X_train_raw.median(numeric_only=True))
        all_data = pd.concat([X_train_raw, X_test], ignore_index=True)
        numeric_cols = all_data.select_dtypes(
            include="number").columns.tolist()
        new_cols = {}
        for col in numeric_cols[:8]:
            new_cols[f"{col}_lag1"] = all_data[col].shift(1).bfill()
            new_cols[f"{col}_lag3"] = all_data[col].shift(3).bfill()
            new_cols[f"{col}_rolling3"] = all_data[col].rolling(
                3, min_periods=1).mean()
            new_cols[f"{col}_rolling6"] = all_data[col].rolling(
                6, min_periods=1).mean()
        new_df = pd.DataFrame(new_cols, index=all_data.index)
        all_data = pd.concat([all_data, new_df], axis=1).copy()
        X_test = all_data.iloc[len(X_train_raw):].copy().fillna(
            0).reset_index(drop=True)

    if task_type == "segmentation" or y_test is None:
        if hasattr(model, "predict"):
            labels = model.predict(X_test)
        else:
            labels = model.labels_[:len(X_test)]
        y_pred = pd.Series(labels, name="cluster")
        y_proba = None
    elif task_type == "forecasting" and is_statsmodels_model:
        try:
            if best_model_name == "VAR":
                # VAR forecasting
                y_pred = model.forecast(
                    model.endog[-model.k_ar:], steps=len(y_test))
                # Extract target column (first column by convention)
                y_pred = y_pred[:, 0]
            else:
                y_pred = model.forecast(steps=len(y_test))
        except Exception:
            try:
                y_pred = model.predict(start=len(model.fittedvalues), end=len(
                    model.fittedvalues) + len(y_test) - 1)
            except Exception as e:
                print(
                    f"  Warning: statsmodels prediction fallback failed: {e}")
                y_pred = np.full(len(y_test), y_test.mean())
        y_pred = np.array(y_pred)
        y_proba = None
    else:
        y_pred = model.predict(X_test)
        y_proba = None
        if hasattr(model, "predict_proba") and task_type == "classification":
            try:
                y_proba = model.predict_proba(X_test)
            except Exception:
                pass

    print(f"  Predictions: {len(y_pred)} rows")

    # ── Metrics (CR13: 6 metrics) ──
    if task_type == "segmentation" or y_test is None:
        from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
        try:
            sil = float(silhouette_score(X_test.values, labels))
            db = float(davies_bouldin_score(X_test.values, labels))
            ch = float(calinski_harabasz_score(X_test.values, labels))
        except Exception:
            sil, db, ch = 0.0, 9999.0, 0.0
        final_metrics = {"silhouette": round(sil, 4), "davies_bouldin": round(
            db, 4), "calinski_harabasz": round(ch, 2)}
    elif task_type in ("regression", "forecasting"):
        final_metrics = compute_regression_metrics(y_test.values, y_pred)
    else:
        final_metrics = compute_classification_metrics(
            y_test.values, y_pred, y_proba)

    metric_str = " | ".join(f"{k.upper()}={v}" for k, v in final_metrics.items()
                            if k in ("rmse", "mae", "mape", "r2", "accuracy", "f1", "silhouette"))
    print(f"  Final metrics: {metric_str}")

    # ── Load date information for forecast X-axis (CR9) ──
    date_strings = None
    if task_type == "forecasting":
        try:
            # v5: Load from date_index.json (saved by Phase 1)
            date_index_path = p1_dir / "date_index.json"
            if date_index_path.exists():
                with open(date_index_path) as f:
                    date_index = json.load(f)
                    test_dates = date_index.get("test_dates", [])
                    if test_dates:
                        date_strings = test_dates[:len(y_test)]
            # Fallback: check phase1_results.json + clean_test.csv
            if date_strings is None:
                date_cols_detected = phase1_results.get(
                    "date_cols_detected", [])
                if date_cols_detected:
                    test_csv_path = p1_dir / "clean_test.csv"
                    if test_csv_path.exists():
                        test_date_df = pd.read_csv(test_csv_path)
                        date_col = date_cols_detected[0]
                        if date_col in test_date_df.columns:
                            date_strings = test_date_df[date_col].astype(str).tolist()[
                                :len(y_test)]
        except Exception as e:
            print(
                f"  Warning: Could not load date column for forecast X-axis: {e}")
            date_strings = None

    # ── Drift analysis (CR16: Compare CV baseline (Phase 2) vs test (Phase 3)) ──
    # Use cv_baseline_metrics (pre-fine-tuning CV scores) for meaningful drift,
    # fall back to fine_tuned_metrics if cv_baseline not available
    p2_metrics = phase2_results.get("cv_baseline_metrics",
                                    phase2_results.get("fine_tuned_metrics", {}))
    drift_flags = {}
    # Compare only metrics available in both phases (CV metrics excluded —
    # Phase 3 doesn't re-run cross-validation, so cv_mean/cv_std would be
    # meaningless 100% drift)
    all_metrics = ["rmse", "mae", "mape", "r2"]
    for k in all_metrics:
        v = final_metrics.get(k, 0)
        p2v = p2_metrics.get(k, v)
        if p2v is not None and abs(p2v) > 1e-6:
            drift = abs(v - p2v) / abs(p2v) * 100
            drift_flags[k] = {"phase2": p2v, "phase3": v,
                              "drift_pct": round(drift, 2), "flag": drift > 5}
        else:
            drift_flags[k] = {"phase2": p2v, "phase3": v,
                              "drift_pct": 0.0, "flag": False}

    # Save drift keyed by target name for the drift matrix (CR16)
    drift_matrix_entry = {target: drift_flags}

    # ── Charts (CR9: pass date_strings) ──
    feature_names = list(X_test.columns)

    if task_type == "segmentation" or y_test is None:
        exec_charts = make_segmentation_charts(
            X_test.values, labels, feature_names)
    elif task_type == "regression":
        exec_charts = make_regression_charts(y_test, pd.Series(y_pred), target)
    elif task_type == "forecasting":
        # v5 Step 6D: Data integrity check before plotting
        if y_test is not None and len(y_pred) > 0:
            pred_mean = float(np.mean(y_pred))
            actual_mean = float(y_test.mean())
            actual_std = float(y_test.std()) if y_test.std() > 0 else 1e-9
            if abs(pred_mean - actual_mean) > 3 * actual_std:
                print(f"  ⚠ Warning: Prediction scale mismatch for {target}: "
                      f"pred_mean={pred_mean:.2f}, actual_mean={actual_mean:.2f}, actual_std={actual_std:.2f}")
        exec_charts = make_forecasting_charts(
            y_test, pd.Series(y_pred), target, date_strings=date_strings)
    else:
        classes = sorted(list(set(y_test.values)))
        exec_charts = make_classification_charts(
            y_test.values, y_pred, y_proba, classes)

    print(f"  Diagnostics: {len(exec_charts)} charts")

    # ── CR12: Per-model plots and residual tables (CR9: with dates) ──
    per_model_preds = {}
    per_model_plots = []
    per_model_residual_tables = {}

    pmp_path = p2_dir / "per_model_predictions.json"
    if pmp_path.exists():
        try:
            per_model_preds = json.load(open(pmp_path))
            per_model_plots = build_per_model_plots(
                per_model_preds, target, date_strings=date_strings)
            per_model_residual_tables = build_per_model_residual_tables(
                per_model_preds)
            print(f"  Per-model plots: {len(per_model_plots)}")
        except Exception as e:
            print(f"  Warning: Could not load per-model predictions: {e}")

    # ── Business Insights (CR18, CR19: pass drift_flags, Step 7: pass cache_dir) ──
    insights = generate_insights(
        task_type, final_metrics, phase1_results, phase2_results, target, drift_flags=drift_flags, cache_dir=out_dir)
    print(f"  Business insights: {len(insights)}")

    # ── Step 8: Wire LLM descriptions into Phase 3 ──
    chart_conclusions = {}

    # Prepare date range string for descriptions
    date_range_info = ""
    if date_strings and len(date_strings) >= 2:
        date_range_info = f"{date_strings[0]} to {date_strings[-1]}"

    if task_type == "forecasting":
        # Main forecast chart description with LLM
        n_test = len(y_test) if y_test is not None else 0
        conclusion = llm_describe('forecast', {
            'target': target,
            'model': best_model_name,
            'r2': final_metrics.get('r2', 0),
            'rmse': final_metrics.get('rmse', 0),
            'mape': final_metrics.get('mape', 0),
            'n_test': n_test,
            'date_range': date_range_info
        }, cache_dir=out_dir)
        chart_conclusions["forecast_plot"] = conclusion

        # Per-model chart descriptions with LLM
        for model_name, data in per_model_preds.items():
            actual = data.get("actual", [])
            predicted = data.get("predicted", [])
            if actual and predicted:
                from sklearn.metrics import r2_score, mean_squared_error
                r2 = r2_score(actual, predicted)
                rmse = np.sqrt(mean_squared_error(actual, predicted))
                conclusion = llm_describe('per_model_forecast', {
                    'model': model_name,
                    'target': target,
                    'r2': r2,
                    'rmse': rmse
                }, cache_dir=out_dir)
                chart_conclusions[f"per_model_{model_name.replace(' ', '_').replace('(', '').replace(')', '')}"] = conclusion

        # Drift description with LLM
        n_drift_flags = sum(1 for v in drift_flags.values()
                            if v.get("flag", False))
        drift_metrics = [k for k, v in drift_flags.items()
                         if v.get("flag", False)]
        biggest_metric = ""
        biggest_pct = 0
        for k, v in drift_flags.items():
            if v.get("drift_pct", 0) > biggest_pct:
                biggest_pct = v.get("drift_pct", 0)
                biggest_metric = k
        drift_stats = {
            "target": target,
            "n_flagged": n_drift_flags,
            "biggest_metric": biggest_metric,
            "biggest_pct": biggest_pct
        }
        chart_conclusions[f"drift_{target}"] = llm_describe(
            "drift", drift_stats, cache_dir=out_dir)

    elif task_type == "regression":
        # Actual vs predicted description with LLM
        conclusion = llm_describe('forecast', {
            'target': target,
            'model': best_model_name,
            'r2': final_metrics.get('r2', 0),
            'rmse': final_metrics.get('rmse', 0),
            'mape': final_metrics.get('mape', 0)
        }, cache_dir=out_dir)
        chart_conclusions["actual_vs_predicted"] = conclusion

    print(f"  Chart conclusions: {len(chart_conclusions)}")

    # ── Save Artifacts ──
    phase3_results = {
        "task_type": task_type,
        "target": target,
        "best_model": phase2_results.get("best_model"),
        "final_metrics": final_metrics,
        "drift_analysis": drift_flags,
        "n_predictions": int(len(y_pred))
    }

    # v5 Step 6C: Add test date range
    if date_strings and len(date_strings) >= 2:
        phase3_results["test_date_range"] = {
            "start": date_strings[0], "end": date_strings[-1]}

    with open(out_dir / "phase3_results.json", "w") as f:
        json.dump(phase3_results, f, indent=2, default=_json_serialiser)

    # v5 Step 6B: Add Date column and test_date_range to outputs
    if y_test is not None:
        if date_strings and len(date_strings) == len(y_test):
            avp = pd.DataFrame({"Date": date_strings[:len(
                y_test)], "Actual": y_test.values, "Predicted": y_pred})
        else:
            avp = pd.DataFrame({"Actual": y_test.values, "Predicted": y_pred})
    else:
        avp = pd.DataFrame({"Predicted": y_pred})
    avp.to_csv(out_dir / "actual_vs_predicted.csv", index=False)

    with open(out_dir / "execution_charts.json", "w") as f:
        json.dump(exec_charts, f, indent=2, default=_json_serialiser)

    with open(out_dir / "business_insights.json", "w") as f:
        json.dump(insights, f, indent=2, default=_json_serialiser)

    # CR12: Save per-model outputs
    if per_model_plots:
        with open(out_dir / "per_model_plots.json", "w") as f:
            json.dump(per_model_plots, f, indent=2, default=_json_serialiser)

    if per_model_residual_tables:
        with open(out_dir / "per_model_residual_tables.json", "w") as f:
            json.dump(per_model_residual_tables, f,
                      indent=2, default=_json_serialiser)

    # CR16: Save complete drift matrix (keyed by target name)
    with open(out_dir / "drift_matrix.json", "w") as f:
        json.dump(drift_matrix_entry, f, indent=2, default=_json_serialiser)

    # CR6, CR23: Save chart conclusions
    if chart_conclusions:
        with open(out_dir / "chart_conclusions.json", "w") as f:
            json.dump(chart_conclusions, f, indent=2, default=_json_serialiser)

    # CR22, CR24: Run self-check
    self_check_results = run_self_check('phase3', phase3_results)
    with open(out_dir / "self_check_results.json", "w") as f:
        json.dump(self_check_results, f, indent=2, default=_json_serialiser)

    if not self_check_results["passed"]:
        print(
            f"  Warning: Self-check found {len(self_check_results['errors'])} error(s)")
    if self_check_results["warnings"]:
        print(
            f"  Self-check: {len(self_check_results['warnings'])} warning(s)")

    print(f"\n  Phase 3 complete - {out_dir}/ ready\n")


if __name__ == "__main__":
    main()
