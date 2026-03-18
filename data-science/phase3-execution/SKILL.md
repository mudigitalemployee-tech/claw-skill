# Phase 3 — Execution & Business Insights
**Script:** `scripts/phase3_execution.py`  
**Input directories:** `artifacts/phase1/`, `artifacts/phase2/`  
**Output directory:** `artifacts/phase3/`

## Purpose

Load the fine-tuned best model, run final inference on the held-out test set, compute validation metrics, generate task-specific diagnostic charts, and auto-generate 3–5 business insights in plain language.

---

## Usage

```bash
python3 scripts/phase3_execution.py \
  --task_type <type>              # regression | classification | forecasting | segmentation
  --target <col>                  # Target column name
  [--phase1_dir artifacts/phase1]
  [--phase2_dir artifacts/phase2]
  [--output_dir artifacts/phase3]
```

---

## Pipeline Steps

### 1. Load Artifacts
- Load `best_model.pkl` from `artifacts/phase2/`
- Load `clean_test.csv` from `artifacts/phase1/`
- Load `phase1_results.json` and `phase2_results.json` for context

### 2. Run Predictions
- Separate features (X_test) from target (y_test)
- Generate predictions (y_pred) using loaded model
- For classification: also generate prediction probabilities (y_proba) if available
- Save actual vs predicted to `actual_vs_predicted.csv`

### 3. Final Validation Metrics
- Recompute all task-specific metrics on test set
- Compare with Phase 2 fine-tuned metrics (detect any drift)
- Flag if test performance deviates > 5% from validation performance

### 4. Task-Specific Diagnostics

#### Regression
- **Actual vs Predicted scatter plot** with perfect-fit reference line
- **Residuals distribution** (histogram) — check for normality
- **Residuals vs Predicted** (scatter) — check for heteroscedasticity

#### Classification
- **Confusion Matrix** heatmap
- **ROC Curve** with AUC annotation
- **Precision-Recall Curve**
- **Feature Importances** bar chart (if model supports it)

#### Forecasting
- **Time-series forecast plot**: actual (line) vs predicted (dashed line) over time
- **Error distribution** histogram (actual − predicted)
- **Rolling MAPE** chart over time window

#### Segmentation
- **Cluster profiles** table: mean feature values per cluster
- **Cluster size** bar chart
- **PCA 2D scatter** of clusters (if >2 features)
- **Silhouette per cluster** bar chart

### 5. Business Insights Generation
Auto-generate **3–5 business insights** by translating model outputs into plain language.

Rules:
- Always quantify (use actual metric values, not "high" or "low")
- Each insight = **Observation → Implication → Action**
- Task-type specific templates (see below)

#### Regression templates:
- "The model explains {R²×100:.1f}% of variance in {target} — suitable for {use_case}"
- "Mean prediction error is {MAE:.2f} units — within {pct:.1f}% of the average {target}"
- "Top driver of {target}: {top_feature} (importance: {imp:.2f})"

#### Classification templates:
- "Model correctly identifies {accuracy×100:.1f}% of cases"
- "Precision {precision:.2f} / Recall {recall:.2f} — {interpretation}"
- "AUC-ROC of {auc:.3f} indicates {model_discrimination_quality}"

#### Forecasting templates:
- "MAPE of {mape:.1f}% — forecast is within {mape:.1f}% of actuals on average"
- "Forecast accuracy degrades beyond {N} periods — plan refresh cadence accordingly"

#### Segmentation templates:
- "Identified {k} customer segments with distinct profiles"
- "Largest segment ({pct:.1f}% of data): characterized by {profile}"
- "Actionable segment for {use_case}: Segment {n} (size: {n_samples})"

---

## Outputs — `artifacts/phase3/`

| File | Description |
|---|---|
| `phase3_results.json` | Final metrics, comparison vs Phase 2, diagnostic flags |
| `actual_vs_predicted.csv` | Row-level actual and predicted values |
| `execution_charts.json` | Plotly chart spec array for all diagnostics |
| `business_insights.json` | Structured insights: `[{title, observation, implication, action}]` |

---

## `business_insights.json` Structure

```json
[
  {
    "id": 1,
    "title": "Model explains 84% of revenue variance",
    "observation": "The model achieves R²=0.84 on held-out test data",
    "implication": "Predictions are reliable enough for operational use",
    "action": "Deploy model for monthly revenue forecasting with monthly retraining",
    "metric": "R²=0.84"
  }
]
```

---

## Progress Output

```
✓ Best model loaded: RandomForestClassifier
✓ Predictions generated: 1000 rows
✓ Final metrics: Accuracy=0.89 | F1=0.87 | AUC=0.93
✓ Diagnostics: confusion matrix, ROC curve, PR curve
✓ Business insights generated: 4 insights
✓ Phase 3 complete — artifacts/phase3/ ready
```
