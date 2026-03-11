---
name: musigma-html-report-generator
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

**Canonical DS TOC (adapt as needed — include all steps that apply):**

```
Introduction
Quick Peek of Notebook
Installing Necessary Packages
Import Dataset
Data Understanding
Data Wrangling
User Input Section
Categorical Transformation
Feature Preprocessing
Training-Validation Split
Dependent Variable Transformation
Numeric Transformation
Feature Selection
  └─ Selecting Important Features
Analysis Models
  └─ Model Comparison
  └─ Ensemble Averaging
  └─ Ensemble Stacking
Final Prediction
Downloads
Executive Summary
```

**Rules for DS Mode TOC:**
- Each pipeline step → its own `<div class="section level2">` with `<h2>`
- Variants / sub-steps (e.g., Ensemble Averaging, Ensemble Stacking under Analysis Models) → `<div class="section level3">` with `<h3>`
- Executive Summary always appears **last** in DS reports (it's the capstone, not the intro)
- Omit steps that don't apply (e.g., skip "Ensemble Stacking" if only one model was used)
- Add steps that are missing but relevant (e.g., "Hyperparameter Tuning", "Cross-Validation", "SHAP Analysis")
- "Downloads" section should contain links or placeholders for model artifacts, processed datasets, or prediction CSVs
- "Quick Peek of Notebook" should show a brief table or summary of all major steps with their purpose — like a pipeline map

**DS Mode chart guidance:**
- Data Understanding → distribution plots, correlation heatmap
- Feature Selection → feature importance bar chart
- Model Comparison → grouped bar chart of model metrics (accuracy, F1, AUC, RMSE, etc.)
- Ensemble Averaging / Stacking → performance lift chart vs. base models
- Final Prediction → prediction distribution, confusion matrix, or residual plot

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
