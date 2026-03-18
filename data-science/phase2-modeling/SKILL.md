# Phase 2 — Model Selection & Validation
**Script:** `scripts/phase2_modeling.py`  
**Input directory:** `artifacts/phase1/`  
**Output directory:** `artifacts/phase2/`

## Purpose

Train 3–4 candidate models for the detected task type, evaluate all of them, pick the best, and fine-tune it with GridSearchCV. All iterations are logged for the comparison report.

---

## Usage

```bash
python3 scripts/phase2_modeling.py \
  --task_type <type>          # regression | classification | forecasting | segmentation
  --target <col>              # Target column name
  [--phase1_dir artifacts/phase1]
  [--output_dir artifacts/phase2]
```

---

## Model Candidates by Task Type

### Regression
| Model | Key Hyperparams |
|---|---|
| LinearRegression | — |
| Ridge | alpha=[0.01, 0.1, 1, 10] |
| RandomForestRegressor | n_estimators, max_depth |
| XGBRegressor | learning_rate, max_depth, n_estimators |

### Classification
| Model | Key Hyperparams |
|---|---|
| LogisticRegression | C=[0.01, 0.1, 1, 10], max_iter=1000 |
| RandomForestClassifier | n_estimators, max_depth |
| XGBClassifier | learning_rate, max_depth, n_estimators |
| SVC | C, kernel, gamma |

### Forecasting
| Model | Notes |
|---|---|
| ARIMA (p=1,d=1,q=1) | statsmodels; graceful fallback if unavailable |
| ExponentialSmoothing | statsmodels; trend+seasonal |
| RandomForestRegressor | Time-aware features (lag, rolling mean) |
| XGBRegressor | Time-aware features |

### Segmentation (unsupervised)
| Model | Key Hyperparams |
|---|---|
| KMeans | n_clusters=[2,3,4,5,6,8] |
| DBSCAN | eps, min_samples |
| AgglomerativeClustering | n_clusters, linkage |
| GaussianMixture | n_components |

---

## Evaluation Metrics

| Task Type | Metrics |
|---|---|
| Regression | RMSE, MAE, MAPE, R² |
| Classification | Accuracy, F1 (weighted), AUC-ROC, Precision, Recall |
| Forecasting | RMSE, MAE, MAPE |
| Segmentation | Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index |

---

## Training Process

1. Load `clean_train.csv` and `clean_test.csv` from `artifacts/phase1/`
2. For each model: train on train set, evaluate on test set
3. Log **every** training iteration (cross-val fold scores included)
4. Rank models by primary metric (RMSE for regression/forecasting, F1 for classification, Silhouette for segmentation)
5. Select best model
6. Fine-tune best model with extended GridSearchCV (cv=5, scoring=primary_metric)

**XGBoost** is imported with `try/except` — if unavailable, falls back to 3 models with a `⚠ XGBoost not available` warning.

---

## Outputs — `artifacts/phase2/`

| File | Description |
|---|---|
| `phase2_results.json` | All model scores, best model name, fine-tuned params, ranking |
| `best_model.pkl` | Fitted best model (after fine-tuning) |
| `model_comparison_chart.json` | Plotly grouped bar chart spec (all models × all metrics) |
| `per_model_iteration_tables.json` | Full CV iteration logs per model |

---

## `phase2_results.json` Structure

```json
{
  "task_type": "classification",
  "target": "churn",
  "models": [
    {
      "name": "RandomForestClassifier",
      "params": {"n_estimators": 100, "max_depth": 8},
      "metrics": {"accuracy": 0.87, "f1": 0.85, "auc_roc": 0.91},
      "cv_scores": [0.84, 0.86, 0.85, 0.87, 0.85],
      "rank": 1
    }
  ],
  "best_model": "RandomForestClassifier",
  "fine_tuned_params": {"n_estimators": 200, "max_depth": 10},
  "fine_tuned_metrics": {"accuracy": 0.89, "f1": 0.87, "auc_roc": 0.93}
}
```

---

## Progress Output

```
✓ Loaded train (4000 rows) and test (1000 rows) from artifacts/phase1/
Training LogisticRegression...        ✓ F1=0.81 | AUC=0.87
Training RandomForestClassifier...    ✓ F1=0.85 | AUC=0.91
Training XGBClassifier...             ✓ F1=0.84 | AUC=0.90
Training SVC...                       ✓ F1=0.82 | AUC=0.88
✓ Best model: RandomForestClassifier (F1=0.85)
Fine-tuning RandomForestClassifier... ✓ F1=0.87 | AUC=0.93
✓ Phase 2 complete — artifacts/phase2/ ready
```
