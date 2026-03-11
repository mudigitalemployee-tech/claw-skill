---
name: report_generatror
description: >
  Generate structured, interactive HTML analytics reports using the MuSigma canonical template.
  Use when: user asks to generate a report, analytics report, data analysis report, HTML report,
  dashboard report, EDA report, or any dataset summary report. Also use when asked to "use the
  MuSigma template", "generate report from template", "create an analytics report", or "analyze
  this dataset and make a report". Covers: data science reports, executive summaries, decision
  science outputs, benchmarking reports, customer analytics, and any structured data reporting.
  NOT for: slide decks, PDFs, or non-HTML output unless explicitly converting afterward.

---

# MuSigma HTML Report Generator

Generate self-contained, interactive HTML reports with fixed sidebar TOC, Plotly.js charts, and MuSigma branding.

---

## Report Modes

Before building, identify the **report type** and apply the matching TOC structure:

| Mode | Use When | TOC Style |
|------|----------|-----------|
| **Insight / Analytics** | EDA, business analytics, customer insights, benchmarking, executive summary | 4–8 broad thematic sections |
| **Data Science / DS / Decision Science** | Full ML pipeline, modeling notebooks, feature engineering, prediction outputs | Detailed step-by-step pipeline TOC (see below) |

If the user's input includes terms like "data science report", "DS report", "decision science", "model comparison", "feature engineering", "prediction", "ensemble", or "training/validation" → use **DS Mode**.

---

## Workflow

### 1. Load the Template

Read `assets/template.html` from this skill directory. This is the canonical template — never generate from scratch.

### 2. Analyze the Dataset / Context

- Load and parse the dataset (CSV, Excel, JSON, etc.) if provided
- Compute summary statistics, distributions, correlations
- Identify key segments, trends, outliers, and patterns
- Map findings to the appropriate sections for the chosen mode

### 3. Build the Report

Copy the template structure exactly. Replace `{{PLACEHOLDER}}` values with actual content.

**Mandatory elements (both modes):**
- MuSigma header with logo, title, author, version, date
- Executive Summary with key metrics and critical findings
- Data tables with `<thead>/<tbody>` (auto-styled by template CSS)
- Plotly.js charts with the professional palette (see below)
- Recommendations table (Priority / Recommendation / Rationale / Impact) — or equivalent in DS mode
- Conclusion with Next Step
- TOC builder script (copy from template — auto-generates sidebar)

---

## TOC Structures by Mode

### Mode A — Insight / Analytics Report

Group findings into **4–8 thematic sections**. Example structure:

```
Executive Summary
Dataset Overview
Key Trends & Patterns
Segment Analysis
Recommendations
Conclusion
```

Adjust sections to fit the data. Keep it high-level and business-readable.

---

### Mode B — Data Science / DS / Decision Science Report

Use a **granular, notebook-style step-by-step TOC** that mirrors the analysis pipeline. Every major pipeline step is its own top-level `<h2>` section. Subsections (h3) are used for variants/sub-steps only.

---

#### ⚠️ DS Variant Detection (MANDATORY — read this first)

Before building the report, determine which DS variant applies:

| Condition | Variant | Key Difference |
|-----------|---------|----------------|
| User does NOT specify a model, OR says "try multiple models", "compare models", "find the best model" | **DS-Multi** | Includes per-model iteration summaries + Model Comparison section |
| User specifies a SINGLE model (e.g., "use XGBoost", "build a Random Forest", "run ARIMA") | **DS-Single** | No comparison section — deep-dives into ONE model's tuning, iterations, and results |
| User specifies 2+ named models (e.g., "compare RF and XGBoost") | **DS-Multi** | Same as multi, but only the named models |

**Rule:** Pick the variant BEFORE generating any HTML. The TOC is locked once chosen — do not mix headers from both variants.

---

#### DS-Multi — Multi-Model Report TOC (when no specific model OR multiple models requested)

Use when the task involves testing/comparing multiple models. Every model gets its own subsection, and a dedicated comparison section ties them together.

```
Introduction
Quick Peek of Notebook
Import Dataset
Data Understanding
Data Wrangling
Feature Preprocessing
  └─ Categorical Transformation
  └─ Numeric Transformation
  └─ Dependent Variable Transformation
Training-Validation Split
Feature Selection
  └─ Selecting Important Features
Analysis Models
  └─ Model 1: [Name] — Iteration Summary    ← one h3 per model tested
  └─ Model 2: [Name] — Iteration Summary
  └─ Model N: [Name] — Iteration Summary
  └─ Ensemble Averaging                      ← optional, if applicable
  └─ Ensemble Stacking                       ← optional, if applicable
Model Comparison                              ← MANDATORY h2 section
  └─ Metrics Comparison Table                ← MANDATORY
  └─ Comparison Plot (grouped bar / radar)   ← MANDATORY chart
  └─ Best Model Selection Rationale          ← MANDATORY paragraph
Final Prediction
  └─ Actual vs. Predicted Table              ← MANDATORY
  └─ Actual vs. Predicted Plot               ← MANDATORY chart
  └─ Error Distribution
Downloads
Executive Summary
```

**DS-Multi mandatory sections (non-negotiable):**
- ✅ Per-model iteration summaries (all iterations, not just best)
- ✅ Model Comparison h2 with table + chart + rationale
- ✅ Actual vs. Predicted table + plot
- ✅ Executive Summary (last section — capstone)

---

#### DS-Single — Single-Model Report TOC (when a specific model is requested)

Use when the user names ONE model. No comparison section — instead, deep-dive into that model's hyperparameter tuning, learning behavior, and diagnostics.

```
Introduction
Quick Peek of Notebook
Import Dataset
Data Understanding
Data Wrangling
Feature Preprocessing
  └─ Categorical Transformation
  └─ Numeric Transformation
  └─ Dependent Variable Transformation
Training-Validation Split
Feature Selection
  └─ Selecting Important Features
Model: [Name]
  └─ Model Configuration & Rationale
  └─ Hyperparameter Tuning — Iteration Summary    ← ALL iterations, not just best
  └─ Training & Validation Metrics
  └─ Learning Curves / Convergence                ← optional but recommended
Model Diagnostics
  └─ Feature Importance / SHAP Analysis            ← recommended
  └─ Residual Analysis (regression) OR Confusion Matrix (classification)
  └─ Overfitting Assessment
Final Prediction
  └─ Actual vs. Predicted Table              ← MANDATORY
  └─ Actual vs. Predicted Plot               ← MANDATORY chart
  └─ Error Distribution
Model Summary & Performance Card             ← replaces "Model Comparison" — single model scorecard
Downloads
Executive Summary
```

**DS-Single mandatory sections (non-negotiable):**
- ✅ Hyperparameter Tuning — all iterations table (not just best run)
- ✅ Model Diagnostics h2 (feature importance, residuals/confusion matrix, overfitting check)
- ✅ Actual vs. Predicted table + plot
- ✅ Model Summary & Performance Card (final metrics scorecard for the one model)
- ✅ Executive Summary (last section — capstone)

**DS-Single does NOT include:**
- ❌ Model Comparison section (no other models to compare)
- ❌ Multiple model subsections under "Analysis Models"
- ❌ Ensemble Averaging / Stacking (single model — no ensemble)

---

#### Shared DS Rules (both variants)

- Each pipeline step → its own `<div class="section level2">` with `<h2>`
- Sub-steps → `<div class="section level3">` with `<h3>`
- Executive Summary always appears **last** in DS reports (capstone, not intro)
- Omit steps that don't apply (e.g., skip "Categorical Transformation" if no categoricals exist)
- Add steps that are missing but relevant (e.g., "Cross-Validation", "SHAP Analysis", "Outlier Treatment")
- "Downloads" → links/placeholders for model artifacts, processed datasets, prediction CSVs
- "Quick Peek of Notebook" → brief table of all major steps with their purpose (pipeline map)

**DS chart guidance (both variants):**
- Data Understanding → distribution plots, correlation heatmap
- Feature Selection → feature importance bar chart
- **DS-Multi only:** Model Comparison → grouped bar chart or radar of all models' metrics
- **DS-Single only:** Hyperparameter Tuning → iteration performance line chart; Learning Curves → train vs. val over epochs/iterations
- Final Prediction → prediction scatter/line, confusion matrix heatmap, or residual histogram

---

### DS Mode — Mandatory Model Reporting Requirements (NON-NEGOTIABLE)

These requirements apply to ALL Data Science, model analysis, and performance reports.
Applies to **both DS-Multi and DS-Single** variants — adapt as noted below.

#### A. Per-Model Iteration Summary

**DS-Multi:** For **every model tested**, include a dedicated subsection (h3) under "Analysis Models" that records:
**DS-Single:** Include a single subsection under "Model: [Name]" → "Hyperparameter Tuning — Iteration Summary" that records:

- **Model name and type** (e.g., Random Forest, XGBoost, ARIMA, Prophet, Logistic Regression)
- **Hyperparameters used** for each iteration/run (table format)
- **Training metrics** for each iteration (accuracy, RMSE, MAE, F1, AUC, R², etc. — whichever apply)
- **Validation metrics** for each iteration
- **Iteration history** — if multiple hyperparameter runs were performed, show ALL iterations in a table, not just the best one

Example table per model:
```
| Iteration | Key Hyperparameters          | Train Metric | Val Metric | Notes         |
|-----------|------------------------------|--------------|------------|---------------|
| 1         | n_estimators=100, depth=5    | 0.92         | 0.88       | Baseline      |
| 2         | n_estimators=200, depth=8    | 0.95         | 0.89       | Improved      |
| 3         | n_estimators=300, depth=10   | 0.97         | 0.87       | Overfitting   |
```

**Key rule:** Record ALL iterations, not just the best. The report is a full audit trail of what was tried and what worked.

#### B. Model Comparison — DS-Multi ONLY (MANDATORY for multi-model reports)

**Applies to DS-Multi only.** DS-Single replaces this with "Model Summary & Performance Card" (see below).

A dedicated `<h2>` section titled **"Model Comparison"** that includes:

1. **Comparison table** — All models side by side with their best metrics:
   ```
   | Model              | Accuracy | F1 Score | AUC   | RMSE  | MAE   | Best Iteration |
   |--------------------|----------|----------|-------|-------|-------|----------------|
   | Random Forest      | 0.89     | 0.87     | 0.93  | —     | —     | #2             |
   | XGBoost            | 0.91     | 0.90     | 0.95  | —     | —     | #4             |
   | Logistic Regression| 0.84     | 0.82     | 0.88  | —     | —     | #1             |
   ```

2. **Comparison plot (MANDATORY)** — A Plotly grouped bar chart or radar chart showing all models' key metrics side by side. This chart is non-negotiable — every DS-Multi report must have it.
   - Use grouped bar chart for up to 5 models
   - Use radar/spider chart for 3+ metrics across 3+ models
   - Include value annotations on the chart
   - Highlight the winning model visually (e.g., different color or annotation)

3. **Best model selection rationale** — Brief paragraph explaining why the final model was chosen (not just "highest accuracy" — consider overfitting, interpretability, inference speed, business constraints)

#### B-alt. Model Summary & Performance Card — DS-Single ONLY (MANDATORY for single-model reports)

**Applies to DS-Single only.** Replaces "Model Comparison" when only one model is used.

A dedicated `<h2>` section titled **"Model Summary & Performance Card"** that includes:

1. **Final metrics scorecard** — A clean summary table of the best iteration's performance:
   ```
   | Metric     | Train   | Validation | Test (if available) |
   |------------|---------|------------|---------------------|
   | Accuracy   | 0.94    | 0.91       | 0.90                |
   | F1 Score   | 0.92    | 0.89       | 0.88                |
   | AUC        | 0.97    | 0.94       | 0.93                |
   ```

2. **Performance gauge or bar chart (MANDATORY)** — A Plotly gauge chart or horizontal bar chart showing key metrics vs. target/baseline thresholds. Visually communicates "how good is this model at a glance."

3. **Model strengths & limitations** — Brief paragraph covering what the model handles well, known weaknesses, and deployment considerations (interpretability, latency, data drift sensitivity)

#### C. Actual vs. Predicted Values (MANDATORY section)

A dedicated section (h2 or h3 under "Final Prediction") that includes:

1. **Actual vs. Predicted table** — Show a sample of actual vs. predicted values:
   - For regression: at least 15-20 rows showing actual, predicted, and residual (error)
   - For classification: confusion matrix + sample predictions with actual label, predicted label, and confidence score
   - For time series: actual vs. forecasted values for the test/validation period

2. **Actual vs. Predicted plot (MANDATORY)** — A Plotly chart visualizing the comparison:
   - Regression → scatter plot (actual vs. predicted) with 45° reference line, or line chart showing both series over time
   - Classification → confusion matrix heatmap + ROC curve
   - Time series → overlay line chart (actual line + predicted/forecast line with confidence band)

3. **Error distribution** — Histogram or summary of residuals/errors to show prediction quality

**Key rule:** Never present a model without showing how it actually performed on real data. The table + plot combination is the proof that the model works.

---

## Shared Build Rules

**Version Numbering (MANDATORY — YY.MM.VV format):**
- Format: `YY.MM.VV` where:
  - `YY` = last 2 digits of the current year (e.g., `26` for 2026)
  - `MM` = current month, zero-padded (e.g., `03` for March)
  - `VV` = version number for this specific report artifact, zero-padded, starting at `01`
- Version increments: if regenerating/recreating the same report, increment `VV` by 1 (e.g., `26.03.01` → `26.03.02`)
- To determine the correct `VV`: check `reports/` for existing files with the same base name and pick the next version number

**File Naming Convention (MANDATORY):**
- Include the version in the filename: `<report-name>-v<YY.MM.VV>.html`
- Examples:
  - `cirrhosis-clinical-trial-ds-v26.03.01.html`
  - `churn-prediction-report-v26.03.02.html`
- Always save to `reports/`

**Date Handling (MANDATORY):**
- Every date field representing "today" or "report generation date" MUST use the **actual system date** at time of generation
- Never hardcode dates — always fetch from system context or session
- Applies to: report header date, executive summary references, any "as of" timestamps

**Section structure:**
- Each section: `<div id="unique-id" class="section level2">` with `<h2>`
- Subsections: `<div id="unique-id" class="section level3">` with `<h3>`
- Headings are auto-numbered via CSS counters: h2 → 1, 2, 3… / h3 → 1.1, 1.2, 2.1…
- TOC sidebar mirrors the same numbering automatically
- Charts: `<div class="chart-container" id="chart-name"></div>`

**Callouts — NO alert boxes:**
- Do NOT use `<div class="alert ...">` for critical findings, notes, or next steps
- Use plain `<p><strong>Label:</strong> content text</p>`
- Example: `<p><strong>Critical Finding:</strong> Return rate of 24.8% is eroding margins.</p>`
- Example: `<p><strong>Next Step:</strong> Schedule deep-dive with product team.</p>`

**Chart palette — Professional colors (mandatory):**
```javascript
var P=["#4E79A7","#59A14F","#F28E2B","#E15759","#BAB0AC"], H=370;
// Primary (Blue), Secondary (Green), Highlight (Orange), Negative (Red), Neutral (Gray)
```
Always add value annotations (`text` + `textposition`) on charts. Use colors from `P` array — cycle through them for multiple series/bars. Layout defaults include `gridcolor:'#E5E5E5'` for clean axis grids.

**Chart layout defaults:**
```javascript
var L={font:{family:'"Helvetica Neue",Helvetica,Arial,sans-serif',size:11},
       paper_bgcolor:'#fff',plot_bgcolor:'#fff',margin:{t:50,b:60,l:60,r:30}};
```

### 4. Deliver the Report

- Save as self-contained `.html` file in `reports/`
- On WhatsApp: compress to `.zip` before sending (see TOOLS.md)
- Open in browser for the user when on webchat/local

---

## Template Reference

For detailed HTML patterns, element examples, and constraints: read `references/template-guide.md`.

For a complete working example: see `references/example-report.html`.

---

## Constraints

- **Never deviate from template structure** unless user explicitly requests a different format
- **No alert boxes** — use plain `<p><strong>` for all callouts (critical findings, notes, next steps)
- **Auto-numbered headings** — CSS counters handle numbering; never hardcode numbers in heading text
- **Professional chart palette** — always use `P=["#4E79A7","#59A14F","#F28E2B","#E15759","#BAB0AC"]`
- **No KPI cards, no footer, no box-shadow** — clean continuous page
- **Self-contained:** inline CSS, JS via CDN only (Bootstrap 3.3.5, jQuery 1.12.4, Plotly 2.27.0)
- **TOC auto-generates** from h2/h3 headings — never hardcode TOC
- **Every `.section` div must have a unique `id`**
- **Minimum 3 Plotly charts** per report (more for DS mode — aim for one per major analytical step)
- **Always include an Executive Summary** — first section in Insight mode, last section in DS mode
- **DS mode:** Executive Summary is the capstone — place it after Final Prediction, before Downloads or at the very end
