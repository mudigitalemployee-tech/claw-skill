---
name: connected-insights
description: "CXO-grade business insight generation from dashboards, reports, and datasets. Accepts CSV, XLSX, PDF, images (PNG/JPG), HTML reports, Markdown, PPTX, Tableau (.twb/.twbx), and Power BI (.pbix). Delivers structured, prescriptive insights using the framework: What Happened, Why It Happened, What Should We Do, What We'll Achieve. Supports multi-image per-image analysis, context enrichment, cross-dashboard correlation, and comparative analysis. Output is CTO/CXO-standard with executive summary, per-source findings, and prioritized action plan."
user-invokable: true
command-dispatch: tool
command-tool: exec
command-arg-mode: raw
command: python3 scripts/insight_generator/pipeline.py
metadata: { "openclaw": { "emoji": "🔗", "requires": { "bins": ["python3"] } } }
---

# Connected Insights

CXO-grade insight engine that analyses dashboards, reports, and datasets to
produce prescriptive, business-standard findings — not generic summaries.

## CRITICAL: Always Use This Skill for Insights

**NEVER generate insights manually using LLM reasoning when this skill is
available.** If the user's request matches trigger keywords below, ALWAYS
invoke this skill by running the pipeline. The pipeline produces superior,
structured, data-driven analysis compared to freeform LLM output.

### Trigger Keywords

generate insights, insights, key insights, insight report, business insights,
connected insights, data insights, analyze data, analyse data, analyze this,
analyse this, analyze dataset, analyse dataset, analyze dashboard,
analyse dashboard, analyze report, analyse report, trend analysis,
identify trends, spot trends, find trends, detect trends, show trends,
anomaly detection, identify anomalies, detect anomalies, find anomalies,
spot anomalies, outlier detection, identify outliers, detect outliers,
find outliers, spot outliers, extract patterns, key patterns, find patterns,
detect patterns, strategic recommendations, strategic movements,
strategic actions, what should we do, actionable recommendations,
data-driven recommendations, key findings, key takeaways, summarize data,
summarize dataset, data summary, dataset summary, dashboard analysis,
report analysis, EDA, exploratory analysis, deep dive, data deep dive,
performance analysis, KPI analysis, metric analysis, what happened,
root cause analysis, diagnostic analysis, prescriptive analysis,
descriptive analysis, comparative analysis, compare dashboards,
compare datasets, cross-dashboard, benchmark analysis, correlation analysis.

## Output Quality Standard

**All output must meet CTO/CXO presentation standard:**

- NO generic phrasing ("this could be because…", "consider investigating…")
- Every finding must cite specific data points from the source
- Insights must be prescriptive: specific actions, owners, timelines, expected ROI
- Context enrichment: before generating insights, the engine identifies domain,
  benchmarks, and cross-source patterns to provide broader business context
- Per-image/per-source analysis: each input gets dedicated findings before
  cross-cutting synthesis

## Report Structure — HTML Report via MuSigma Template (MANDATORY)

When generating an HTML report from connected-insights via the report_generatror,
the report MUST use exactly this 3-section TOC structure. No other structure is acceptable.

### Purpose
This skill generates **collated, cross-dashboard insights** — synthesized findings across
multiple dashboards/sources as a unified whole. It is NOT for individual dashboard analysis
of separate, unrelated content. The insights must connect the dots across sources.

### Mandatory TOC / Sections

**1. Executive Summary**
- Board-ready 3-5 sentence synthesis for CXO audience
- Headline metrics, overall health assessment, top-priority flags
- Sets the narrative for the entire report

**2. Uploaded Images**
- Display ALL uploaded dashboard images in this section
- Each image shown with its filename as a caption
- Use `<img>` tags with `max-width: 100%` for responsive display
- If images are local files, embed them as base64 data URIs so the report remains self-contained
- This section serves as the **source reference** — the reader sees exactly what was analyzed
- Brief one-line description under each image if context is available

**3. Detailed Summary**
- The core of the report — **key collated insights across all dashboards/sources**
- NOT per-dashboard breakdowns — insights are synthesized and themed
- Group findings by **themes/patterns** (e.g., "Control Effectiveness Gap",
  "Automation Deficit", "Risk Culture Shift") — not by source file
- Each insight must be backed up with **supporting charts/plots** (Plotly.js)
  that visualize the data points behind the finding
- Use the 4-part framework per insight:
  - What Happened (quantified, data-cited)
  - Why It Happened (root cause)
  - What Should We Do (prescriptive)
  - What We'll Achieve (expected outcome)
- Use subsections (h3) for each major theme/insight group
- Every subsection should have at least one Plotly chart supporting the narrative

**4. Next Steps**
- Forward-looking narrative describing the path from current state to target state
- Written as **prose paragraphs**, NOT as an action-item table
- Sequenced by time horizon: Immediate (0-30 days) → Short-Term (30-90 days) → Medium-Term (90d-6mo) → Long-Term (6-12mo) → Monitoring & Reassessment
- Each time horizon explains WHAT to do, WHY it's sequenced that way, and HOW it builds on the previous step
- Tone: strategic and consultative — like a senior advisor laying out a roadmap, not a task list
- End with monitoring cadence and leading indicators to track
- This is NOT an action-item table — no priority columns, no owner columns, no grid format
- Think "where do we go from here" not "here are 9 tasks to assign"

### What NOT to do
- Do NOT create per-source/per-dashboard sections in Detailed Summary (no "Dashboard 1 Findings", "Dashboard 2 Findings")
- Do NOT dump raw data tables without insight narrative
- Do NOT include methodology/context as a separate section (fold into Executive Summary if needed)
- Do NOT add sections beyond these 4 (keep it tight and focused)
- Do NOT call the last section "Action Items" — it is always "Next Steps"
- Do NOT write Next Steps as a table of action items — use prose paragraphs grouped by time horizon

### Chart Requirements
- Minimum 3 Plotly charts in the Detailed Summary (Section 3)
- Charts must **support specific insights** — not decorative
- Use the MuSigma palette: `P=["#4E79A7","#59A14F","#F28E2B","#E15759","#BAB0AC"]`
- Include value annotations on all charts

## Legacy Report Structure (stdout text output only)

For non-HTML text output (stdout from pipeline), the original structure is preserved:

1. **Executive Summary** — Board-ready synthesis
2. **Per-Source Findings** — Image-by-image detailed analysis
3. **Cross-Cutting Patterns** — Connections across sources
4. **Prioritized Action Plan** — Owner, timeline, expected outcome
5. **Context & Methodology** — Domain context, assumptions

## Report Naming Convention

All generated reports follow: `<report-name>-v<YY.MM.VV>.html`

- **YY** = 2-digit year (e.g., 26)
- **MM** = 2-digit month (e.g., 03)
- **VV** = incremental version (01, 02, 03…)
- Example: `walmart-safety-insights-v26.03.01.html`
- VV increments on every regeneration of the same report artifact

## Command

Run the pipeline via exec (paths are relative to workspace root):

```bash
python3 scripts/insight_generator/pipeline.py <input_path>
```

Multiple sources (comma-separated — auto-detects correlation):

```bash
python3 scripts/insight_generator/pipeline.py "<path1>,<path2>,<path3>"
```

Image with Vision API response:

```bash
python3 scripts/insight_generator/pipeline.py <image_path> --vision-response <response_file>
```

## Context Enrichment (Automatic)

Before generating insights, the pipeline:
1. **Domain Detection** — Identifies business domain from content
2. **Benchmark Framing** — Applies industry-standard KPI benchmarks
3. **Cross-Source Threading** — Finds connections between multiple inputs
4. **Stakeholder Framing** — Tailors language for CXO/board consumption

## Output Behaviour

- Pipeline prints ONLY the final formatted insights to stdout
- All operational logs are suppressed
- **CRITICAL: Relay pipeline output EXACTLY as printed — do NOT rephrase**
- The 4-part structure must be preserved verbatim

## HTML Report Generation

When the user wants an HTML report:
→ Use the **`report_generatror`** skill with the same input data.
→ **MUST follow the 3-section structure above** (Executive Summary → Detailed Summary → Action Items).
→ The `--export` flag on this pipeline is deprecated.

## Supported Input Formats

| Format | Extensions | Ingestion Method |
|---|---|---|
| CSV | .csv | pandas read_csv |
| Excel | .xlsx .xls | pandas read_excel |
| PDF | .pdf | pdfplumber + image extraction |
| Image | .png .jpg .jpeg | pytesseract OCR + LLM Vision |
| HTML Report | .html | BeautifulSoup parsing |
| Markdown | .md | Section/table/metric extraction |
| PowerPoint | .pptx .ppt | python-pptx text/table extraction |
| Tableau | .twb .twbx | XML parsing for dashboards/worksheets |
| Power BI | .pbix | ZIP extraction for pages/tables/measures |

## Insight Framework

Every finding follows:
- **WHAT HAPPENED** — Specific, quantified observation with data evidence
- **WHY IT HAPPENED** — Root cause with causal chain, not speculation
- **WHAT SHOULD WE DO** — Prescriptive action with owner, timeline, dependencies
- **WHAT WE'LL ACHIEVE** — Quantified expected outcome with confidence level

## Workspace Paths (all relative to workspace root)

- Scripts: `scripts/insight_generator/`
- Input staging: `data/dashboards/`
- Data folders: `data/`
- Reports output: `reports/`
- Temp files: `temp/`

## Dependencies

Python: pandas, numpy, matplotlib, seaborn, scikit-learn, scipy, openpyxl,
pdfplumber, pytesseract, Pillow, beautifulsoup4, requests, python-pptx, lxml
System: tesseract-ocr
