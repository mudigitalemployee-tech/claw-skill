# Phase 1 — EDA & Preprocessing
**Script:** `scripts/phase1_eda.py`  
**Output directory:** `artifacts/phase1/`

## Purpose

Ingest raw data, profile it thoroughly, detect quality issues, engineer features, and produce a clean train/test split with a fitted preprocessing pipeline — ready for Phase 2 modeling.

---

## Usage

```bash
python3 scripts/phase1_eda.py \
  --data <path>          # CSV, Excel (.xlsx), JSON, or Parquet
  --target <col>         # Target column name
  --task_type <type>     # regression | classification | forecasting | segmentation | auto
  [--test_size 0.2]      # Train/test split ratio (default: 0.2)
  [--output_dir artifacts/phase1]
```

---

## Pipeline Steps

### 1. Data Loading
- Supports: CSV (`.csv`), Excel (`.xlsx`, `.xls`), JSON (`.json`), Parquet (`.parquet`)
- Prints shape, dtypes preview

### 2. Schema Inference
- Column types: numeric, categorical, datetime, boolean
- Cardinality per column (unique value count)
- Missing value % per column
- Date column detection (parse + extract year/month/day/dow features)

### 3. Outlier Detection
- **IQR method:** flag values outside [Q1 - 1.5×IQR, Q3 + 1.5×IQR]
- **Z-score method:** flag |z| > 3 for numeric columns
- Outlier counts saved in `phase1_results.json`

### 4. Distribution Analysis
- Per-column histograms for numeric features
- Value-count bar charts for categorical features (top 20 values)
- Normality test proxy: skewness + kurtosis

### 5. Correlation Analysis
- **Pearson** correlation matrix for numeric features
- **Spearman** for columns with |skew| > 1 (non-normal)
- Heatmap chart spec saved in `eda_charts.json`

### 6. Feature Selection
- **Correlation filter:** drop features with pairwise |corr| > 0.95
- **Variance threshold:** drop near-zero variance features (threshold=0.01)
- **Mutual information ranking:** top-N features by MI score vs. target
- Selected feature list saved in `phase1_results.json`

### 7. Train/Test Split
- Default: 80/20
- **Stratified** split for classification (on target column)
- **Time-aware** split for forecasting (no shuffle, sort by date col first)
- Split info (n_train, n_test, split_ratio) saved in `phase1_results.json`

### 8. Preprocessing Pipeline (scikit-learn Pipeline)
- **Numeric:** median imputation → StandardScaler
- **Categorical:** most-frequent imputation → OneHotEncoder (handle_unknown='ignore')
- **Boolean:** passthrough
- Fitted pipeline saved as `preprocessing_pipeline.pkl`
- Transformed train/test saved as `clean_train.csv`, `clean_test.csv`

---

## Outputs — `artifacts/phase1/`

| File | Description |
|---|---|
| `phase1_results.json` | Schema, missing %, outliers, selected features, split info |
| `clean_train.csv` | Preprocessed training set |
| `clean_test.csv` | Preprocessed test set |
| `feature_importance_phase1.json` | Mutual information scores per feature |
| `eda_charts.json` | List of Plotly chart specs `[{title, data, layout}]` |
| `preprocessing_pipeline.pkl` | Fitted scikit-learn pipeline (for inference) |

---

## Chart Specs Format

`eda_charts.json` is a JSON array:
```json
[
  {
    "chart_id": "dist_col1",
    "title": "Distribution: col1",
    "data": [ {...plotly trace...} ],
    "layout": { "xaxis": {"title": "col1"}, ... }
  },
  ...
]
```
All charts use the MuSigma palette: `["#4E79A7","#59A14F","#F28E2B","#E15759","#BAB0AC"]`

---

## Progress Output

```
✓ Data loaded: 5000 rows × 12 cols
✓ Schema inferred: 8 numeric, 3 categorical, 1 datetime
✓ Outliers detected: 47 IQR flags, 12 Z-score flags
✓ Distributions analyzed: 8 histograms, 3 bar charts
✓ Correlations computed: Pearson (8×8 matrix)
✓ Features selected: 7 of 11 features retained
✓ Train/test split: 4000 train, 1000 test (stratified)
✓ Preprocessing pipeline fitted and saved
✓ Phase 1 complete — artifacts/phase1/ ready
```
