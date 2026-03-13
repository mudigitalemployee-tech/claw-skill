---
name: connected-insights
description: >
  Analyze data (CSV, PDF, or dashboard screenshots/images) and deliver business
  insights. Always generates an HTML report using Mu Sigma branded format.
  Single input → Executive Summary + Findings & Insights + Recommendations.
  Multiple inputs → same per input, plus a Cross-Comparison section.
  Use when: user uploads data files or dashboard images and asks for analysis,
  insights, business intelligence, comparison, or recommendations.
  Triggers on "analyze this data", "compare these dashboards",
  "business insights", "what does this data tell me", "compare datasets".
  NOT for: chart generation, data visualization, or non-analytical tasks.
---

# BI Report Generator

Always generates an HTML report (`Business_Insight_Report.html`) using `assets/report_template.html`.

## Mode 1: Single Input → HTML Report

When user provides ONE dataset, dashboard, or image:

Generate `Business_Insight_Report.html` with three sections:

**1. Executive Summary**
- 3–5 sentence paragraph overview of the data at a glance
- Highlight the single most critical finding and its business impact
- Set context for the detailed findings below

**2. Findings & Insights (5–8 bullets)**
- Each: **bold headline** + one sentence with a specific number
- No category tags or colored labels — just clean bullets
- Max 2 lines per insight

**3. Recommendations (3–5 bullets)**
- Each: **bold action** + one sentence with expected impact
- No priority emojis or colored bullets — just clean text
- Most urgent first, max 2 lines each

Also provide a brief chat summary (Executive Summary + top 3 insights) alongside the file.

## Mode 2: Multiple Inputs → HTML Report

When user provides TWO OR MORE datasets, dashboards, or images:

Generate `Business_Insight_Report.html` using `assets/report_template.html`.

### Report Structure

For N inputs, the report has N+2 sections:

**First section — Executive Summary:**
1. **Executive Summary** — 3–5 sentence overview of all inputs combined. Highlight the most critical finding, set context, and preview key themes. Written as a paragraph, not bullets.

**Section per input (repeated for each):**
1. **Input title** — name/description of the dataset or dashboard
2. **Findings & Insights** — 5–8 bullet insights specific to this input
3. **Recommendations** — 3–5 recommendations specific to this input

**Final section — Cross-Comparison:**
1. **Comparative Insights** — 5–8 bullets highlighting differences, correlations, contradictions, and patterns ACROSS all inputs
2. **Comparative Recommendations** — 3–5 actions that only emerge from looking at the data together

### Cross-Comparison Lenses

When comparing multiple inputs, specifically look for:
- **Contradictions** — where one dataset says X but another says the opposite
- **Amplifications** — where multiple datasets reinforce the same signal
- **Gaps** — metrics present in one but missing in another
- **Temporal shifts** — same metric changing over time across datasets
- **Segment differences** — same metric varying across different cuts (region, product, channel)
- **Hidden correlations** — patterns only visible when datasets are combined

### HTML Format Rules
- Use the Mu Sigma branded header (logo + maroon title + author + date) from the template
- Light-mode professional theme
- Each input section has a clear heading with a colored left border
- Cross-comparison section has a distinct highlight background
- No category tags (Trend/Risk/Opportunity/Anomaly) on insights — just clean bullets
- No colored emoji bullets on recommendations — just clean text
- Keep insights crisp — same 2-line max rule as chat mode
- No charts, no graphs, no Plotly — pure text

## Workflow (both modes)

### Phase 1: Data Ingestion

1. **Identify inputs** — count how many files/images. Determines Mode 1 or Mode 2.
2. **For each input:**
   - **CSV**: Run `python3 scripts/analyze_data.py <input.csv> <output.json>`, then custom pandas queries.
   - **PDF**: Extract text/tables with `pdfplumber` or vision.
   - **Dashboard / Image**: Use vision to read every visible metric, trend, label, and signal.
3. **Deep exploration per input** — distributions, top-N, time trends, cross-tabs, correlations, data quality.
4. **Cross-input analysis (Mode 2 only)** — compare key metrics across inputs, look for the comparison lenses above.

### Phase 2: Insight Generation

For every finding:
- **So What?** — business meaning
- **Quantified Impact** — dollar or percentage
- **Action** — what to do

Distill into crisp bullets. No paragraphs.

### Phase 3: Delivery

- **Mode 1**: Save `Business_Insight_Report.html`, share path, and provide a brief chat summary (Executive Summary + top 3 insights).
- **Mode 2**: Save `Business_Insight_Report.html`, share path, and provide a brief chat summary (top 3 cross-comparison insights).

## File Reference

| File | Purpose | When to read |
|------|---------|-------------|
| `scripts/analyze_data.py` | Automated CSV analysis | Always for CSV inputs |
| `references/style-guide.md` | CSS theme specification | When building HTML |
| `assets/report_template.html` | HTML template with Mu Sigma header | When assembling report |
