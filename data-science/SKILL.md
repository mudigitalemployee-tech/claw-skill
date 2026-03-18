---
name: data-science
description: >
  Structured tabular data analysis pipeline for regression, classification, segmentation,
  and time-series forecasting tasks. Handles EDA, feature engineering, model training
  (including multivariate TS models like VAR/VARMAX), and generates HTML reports using
  the musigma-html-report-generator template. Features: weighted composite model selection
  (35% RMSE + 25% MAPE + 25% R² + 15% CV stability), rule-based chart conclusions for
  all visualizations, self-check validation in all 3 phases (lenient mode), individual
  per-variable outlier detection, KaTeX formula rendering, DataTables sortable tables,
  CXO-grade business insights, MAPE edge-case handling with warning flags, 6 per-metric
  comparison charts, CV-vs-test drift analysis, and abbreviated correlation heatmap labels.
---

# Data Science Pipeline - Master Orchestrator

> ⚠️ **MANDATORY DISCLOSURE:** At the very end of every response using this skill, append:
> `_I used the data-science skill to answer this._ 🛠️`
> This is non-negotiable — applies on ALL channels including WhatsApp, webchat, Discord, Telegram.

**Location:** `skills/data-science/` (relative to workspace root)

## Overview

Modular 3-phase Data Science pipeline. Regression, classification, forecasting, segmentation — raw data to self-contained HTML report.

Phases communicate via `artifacts/` folder. Final step assembles everything into a MuSigma-branded HTML report using the canonical template from `musigma-html-report-generator`.

---

## Report Generation

- **`build_musigma_report.py`** — the ONLY canonical report script
- **`assemble_report.py`** — DEPRECATED forwarding shim (routes to build_musigma_report)
- **`generate_report.py`** — REMOVED (was hardcoded single-dataset script)

All reports use the musigma-html-report-generator template (CSS, TOC sidebar, Plotly palette).

### Template Integration
The report builder extracts 3 inline scripts from the MuSigma template:
1. **TOC builder** — auto-populates sidebar from h2/h3 headings with collapsible subheaders and scroll tracking
2. **DataTables init** — enables column sorting on `.sortable` tables
3. **KaTeX auto-render** — renders LaTeX formulas in the appendix

> **Important:** The builder must NOT emit duplicate DataTables init or KaTeX scripts — the template scripts are the single source.

---

## Inputs Required from User

| Parameter | Values | Description |
|---|---|---|
| `--data` | `<path>` | Path to input dataset (CSV, Excel, JSON, Parquet) |
| `--target` | `<col>` | Target column name for supervised tasks |
| `--task_type` | `regression`, `classification`, `forecasting`, `segmentation`, `auto` | ML task type |
| `--project_name` | `<name>` | Used for artifact folders and report filename |

---

## Execution Flow

### Step 1 — EDA & Preprocessing
```bash
python3 scripts/phase1_eda.py \
  --data <path> --target <col> --task_type <type> --test_size 0.2
```
Outputs: `artifacts/phase1/` — clean data, EDA charts (distributions + outlier boxplots for **all** numeric columns including target), TS diagnostics, feature list, split preview, self-check results

> **Multi-target note:** The target column is included in EDA distributions and outlier boxplots. This ensures all columns are visualized when running multi-target (`target=all`).

### Step 2 — Model Selection & Validation
```bash
python3 scripts/phase2_modeling.py \
  --task_type <type> --target <col> --phase1_dir artifacts/phase1
```
Outputs: `artifacts/phase2/<target>/` — best model (`.pkl`), per-model predictions, 6 per-metric comparison charts, iteration tables, cv_baseline_metrics, self-check results

### Step 3 — Execution & Business Insights
```bash
python3 scripts/phase3_execution.py \
  --task_type <type> --target <col> --phase1_dir artifacts/phase1 --phase2_dir artifacts/phase2/<target>
```
Outputs: `artifacts/phase3/<target>/` — predictions, per-model actual-vs-predicted plots (7 per target), diagnostics, business insights (5-7 per target), drift matrix (CV vs test), self-check results

### Step 4 — Build Report
```bash
python3 scripts/build_musigma_report.py \
  --project_name <name> --task_type <type>
```
Output: `reports/<project-name>-ds-v<YY.MM.VV>.html`

### Multi-Target (target=all)
```bash
# Phase 1 must be run first with any target column
python3 scripts/phase1_eda.py --data <path> --target <first_col> --task_type forecasting --test_size 0.2

# Then run the multi-target wrapper
python3 scripts/run_all_targets.py --project_name <name> --task_type forecasting
```
Auto-detects all numeric target columns from Phase 1 results. Runs Phase 2 + Phase 3 for each, then assembles a unified report.

#### Multi-Target Pipeline Order
1. Self-check aggregation (before report — artifacts must exist)
2. Report assembly (with `--cleanup` to free artifacts after)

---

## Model Hierarchy by Task Type

### Forecasting (preferred order)
1. **VAR** — Vector AutoRegression (multivariate, fits all series jointly)
2. **XGBRegressor** — best for complex time series with lag+rolling features
3. **ARIMA(1,1,1)** — classical univariate time series model
4. **HoltWinters** — additive trend smoothing
5. **GradientBoosting** — sklearn ensemble
6. **RandomForestRegressor** — robust baseline
7. **Ridge** — regularized linear baseline

### Regression (preferred order)
1. **XGBRegressor**
2. **RandomForestRegressor**
3. **Ridge**
4. **LinearRegression**

### Classification (preferred order)
1. **XGBClassifier**
2. **RandomForestClassifier**
3. **LogisticRegression**
4. **SVC**

### Segmentation
KMeans (k=3,5), GaussianMixture, DBSCAN, AgglomerativeClustering — selected by Silhouette Score.

### Model Selection — Composite Scoring
Best model is selected by weighted composite score (not just RMSE):
- **35%** RMSE (normalized, lower is better)
- **25%** MAPE (normalized, lower is better)
- **25%** R² (higher is better)
- **15%** CV stability (lower std is better)

---

## Report Section Order (12 sections)

1. Introduction
2. Data Overview
3. Data Wrangling
4. Exploratory Data Analysis (distributions + individual outlier boxplots for all columns)
5. Time Series EDA (conditional: raw TS plots, log-diff, stationarity, ACF/PACF)
6. Feature Engineering & Selection
7. Model Training & Results (per-model actual-vs-predicted plots + residual tables)
8. Model Comparison (6 per-metric charts: RMSE, MAE, MAPE, R², CV Mean, CV Std + summary table)
9. Validation & Drift (4-metric drift matrix: RMSE, MAE, MAPE, R² — CV baseline vs test)
10. Business Insights (CXO-grade, 5-7 per target with confidence levels)
11. Executive Summary (compact, near end)
12. Appendix: Formulas (KaTeX-rendered) & Abbreviation Glossary (19 entries)
13. ~~Pipeline Validation~~ — removed from report (self-checks still run internally in artifacts, agent-side only)

---

## Key Design Principles

1. **Best model always wins** — pipeline auto-installs xgboost + statsmodels
2. **Generic by design** — `task_type` adapts all phases
3. **Auto-install, never block** — missing packages installed at runtime
4. **Artifact-based handoff** — phases communicate only via `artifacts/`
5. **Self-contained HTML** — report has no external file dependencies beyond CDNs
6. **Repeatable** — `random_state=42` everywhere
7. **Version-aware** — report filenames auto-increment (`v<YY.MM.VV>`)
8. **Error-resilient** — single model failure doesn't crash the pipeline
9. **Template-driven** — all reports use musigma-html-report-generator template
10. **Self-validating** — 3-phase self-check (lenient: warn + flag, never halt)
11. **Composite scoring** — weighted model selection (35/25/25/15)
12. **Rule-based conclusions** — every chart gets a threshold-driven text conclusion (no LLM dependency)
13. **MAPE-aware** — flags extreme MAPE (>200%) with tooltip notes about near-zero actuals
14. **KaTeX formulas** — 6 metric formulas rendered via KaTeX 0.16.x in appendix
15. **Sortable tables** — DataTables 1.10.x on comparison tables (sorting only, no paging)
16. **Individual outliers** — per-variable boxplots with IQR/Z-score flags
17. **CXO insights** — 5-7 business insights per target with confidence levels
18. **Abbreviation glossary** — all abbreviations defined in appendix (19 entries)

---

## Multi-Target Specifics

When running `target=all` via `run_all_targets.py`:

### Artifact Layout
```
artifacts/
  phase1/              <- Shared (one EDA run)
  phase2/
    <target_1>/        <- Per-target model selection
    <target_2>/
    ...
  phase3/
    <target_1>/        <- Per-target execution
    <target_2>/
    ...
```

### Report Builder — Multi-Target Aggregation
The report builder handles multi-target mode by:
- **Self-check:** Aggregates per-target self-check results from subdirectories into unified Phase 2 / Phase 3 summaries
- **Drift matrix:** Loads per-target `drift_matrix.json` from Phase 3 subdirectories and merges into a single cross-target table
- **Comparison charts:** When no root-level `comparison_charts.json` exists, builds 6 horizontal bar charts dynamically from `best_models_summary` (one per metric, showing all targets)
- **Per-model plots:** Loaded per-target from `phase3/<target>/per_model_plots.json`

### Correlation Heatmap — Label Abbreviations
Long column names are automatically shortened for readability on heatmap axes:
- `CPI_U_All_Items_Less_Food_Energy` → `Core_CPI`
- `Spot_Oil_Price_West_Texas_Intermediate` → `WTI_Oil`
- `X10_Year_Treasury_Note_Yield` → `10Y_Treasury`
- Names > 22 chars are truncated with `..`

Margins and font sizes adapt to label count and length. `automargin: true` is set on both axes.

### Drift Analysis
Drift compares **Phase 2 CV baseline metrics** vs **Phase 3 test metrics** (4 metrics: RMSE, MAE, MAPE, R²).
- CV metrics (`cv_mean`, `cv_std`) are excluded from drift — Phase 3 doesn't re-run cross-validation.
- Phase 2 stores `cv_baseline_metrics` separately from `fine_tuned_metrics` (which are test-evaluated).
- Drift > 5% is flagged red in the report table.

---

## Known Constraints

- **numpy scoping:** Never use `import numpy as np` inside function bodies if `np` is already imported at module level — Python treats it as a local variable, breaking earlier references.
- **DataTables double-init:** The template already includes DataTables init — the report builder must NOT add another.
- **TOC script extraction:** The builder extracts inline scripts from the template by filtering for `#TOC`, `DataTable`, and `renderMathInElement` — Plotly var definitions (P, L) are excluded to avoid redefinition.
- **MAPE near-zero:** When actual values are near zero, MAPE can be >1000%. These are flagged with ⚠️ tooltips rather than excluded.
- **Artifact cleanup timing:** Self-check aggregation must run BEFORE report assembly (which triggers cleanup).

---

## Directory Structure

```
data-science/
  SKILL.md                     <- This file
  scripts/
    utils.py                   <- Shared helpers, constants, CDN URLs, composite scoring, self-check, chart conclusions
    phase1_eda.py              <- EDA & preprocessing (distributions, outliers, TS diagnostics, stationarity)
    phase2_modeling.py          <- Model selection, composite scoring, per-metric comparison charts
    phase3_execution.py         <- Final inference, per-model plots, drift analysis, business insights
    build_musigma_report.py     <- CANONICAL report generator (template integration, multi-target aggregation)
    run_all_targets.py          <- Multi-target wrapper (Phase 2 + Phase 3 for each target, self-check aggregation, report assembly)
    assemble_report.py          <- DEPRECATED forwarding shim
  artifacts/                   <- Phase outputs (cleaned after report build)
  reports/                     <- Final HTML reports
```
