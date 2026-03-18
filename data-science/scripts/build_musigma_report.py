#!/usr/bin/env python3
"""
build_musigma_report.py — Generates HTML report using the MuSigma canonical template.
Data Science Pipeline — Mu Sigma

THE SOLE CANONICAL REPORT GENERATOR. All report generation routes here.
Reads template from musigma-html-report-generator/assets/template.html,
extracts CSS and TOC builder JS, builds self-contained HTML from phase artifacts.

Section order (12 sections, matching R sample report pattern):
  1. Introduction
  2. Data Overview
  3. Data Wrangling
  4. Exploratory Data Analysis
  5. Time Series EDA (conditional)
  6. Feature Engineering & Selection
  7. Model Training & Results
  8. Model Comparison
  9. Validation & Drift
 10. Business Insights
 11. Executive Summary (near end, compact, no overlap with §7)
 12. Appendix: Formulas
"""

from utils import (
    ARTIFACTS_DIR, REPORTS_DIR, CHART_PALETTE, REPORT_AUTHOR,
    get_report_version, get_template_path, _json_serialiser, cleanup_artifacts,
    FALLBACK_STYLE_BLOCK, FALLBACK_TOC_SCRIPT,
    KATEX_CSS_CDN, KATEX_JS_CDN, KATEX_AUTO_CDN,
    DATATABLES_CSS_CDN, DATATABLES_JS_CDN,
    ABBREVIATION_GLOSSARY, SCROLLABLE_TABLE_CSS,
    plotly_layout,
    llm_describe, is_date_derived,
)
import argparse
import sys
import json
import datetime
import re
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


# ── Template extraction ────────────────────────────────────────────────────────

def _extract_template_parts(template_path: Path):
    """Extract <style> block and TOC builder <script> from canonical template."""
    text = template_path.read_text(encoding="utf-8")
    style_match = re.search(
        r'(<style type="text/css">.*?</style>)', text, re.DOTALL)
    if not style_match:
        raise RuntimeError("Could not extract <style> block from template")
    style_block = style_match.group(1)

    # Extract inline script blocks: TOC builder, DataTables init, KaTeX auto-render
    all_scripts = re.findall(
        r'(<script>.*?</script>)', text, re.DOTALL)
    # Keep only functional scripts (TOC, DataTables, KaTeX) — skip Plotly var defs
    inline_scripts = [
        s for s in all_scripts
        if 'src=' not in s and (
            '#TOC' in s or 'DataTable' in s or 'renderMathInElement' in s
        )
    ]
    toc_script = "\n".join(inline_scripts)
    if not toc_script:
        raise RuntimeError(
            "Could not extract inline scripts from template")

    return style_block, toc_script


def _load_template():
    """Load template parts with fallback to embedded constants. Injects custom CSS."""
    tpath = get_template_path()
    try:
        if tpath.exists():
            style_block, toc_script = _extract_template_parts(tpath)
            # Inject SCROLLABLE_TABLE_CSS before </style>
            style_block = style_block.replace(
                "</style>", f"{SCROLLABLE_TABLE_CSS}</style>")
            return style_block, toc_script
    except Exception as e:
        print(f"  Warning: Template extraction failed ({e}), using fallback")
    style_block = FALLBACK_STYLE_BLOCK.replace(
        "</style>", f"{SCROLLABLE_TABLE_CSS}</style>")
    return style_block, FALLBACK_TOC_SCRIPT


# ── Helpers ────────────────────────────────────────────────────────────────────

def to_js(obj) -> str:
    return json.dumps(obj, default=_json_serialiser)


def _fmt(name: str) -> str:
    return name.replace("_", " ")


def _slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def render_chart(chart_dict: dict, chart_id: str, style: str = "width:100%;min-height:370px;") -> str:
    if not chart_dict:
        return ""
    data_js = to_js(chart_dict.get("data", []))
    layout_js = to_js(chart_dict.get("layout", {}))
    return (
        f'<div class="chart-container" id="{chart_id}" style="{style}"></div>\n'
        f"<script>Plotly.newPlot('{chart_id}',{data_js},"
        f"$.extend(true,{{}},L,{layout_js}),{{responsive:true}});</script>\n"
    )


def _table(headers, rows, bold_test=None, add_sno=False, extra_class=""):
    """
    Generate HTML table.
    add_sno: If True, prepend S.No. column automatically
    extra_class: Additional CSS class for the table
    """
    if add_sno:
        headers = ["S.No."] + list(headers)

    thead = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    tbody = ""
    for i, row in enumerate(rows):
        do_bold = bold_test and bold_test(i, row)
        cells = ""
        if add_sno:
            cells += f"<td>{i+1}</td>"
        for c in row:
            inner = f"<strong>{c}</strong>" if do_bold else str(c)
            cells += f"<td>{inner}</td>"
        tbody += f"<tr>{cells}</tr>\n"

    class_attr = f' class="{extra_class}"' if extra_class else ""
    return f"<table{class_attr}>\n<thead>{thead}</thead>\n<tbody>\n{tbody}</tbody>\n</table>\n"


def _table_scrollable(headers, rows, bold_test=None, add_sno=False, extra_class=""):
    """Wrap table in scrollable div."""
    table_html = _table(headers, rows, bold_test=bold_test,
                        add_sno=add_sno, extra_class=extra_class)
    return f'<div class="table-scroll-wrapper">\n{table_html}</div>\n'


def _fv(v, fmt=".4f"):
    if isinstance(v, (int, float)):
        return f"{v:{fmt}}"
    return str(v) if v is not None else "N/A"


def _load(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _load_list(path):
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    return []


def _render_avp(avp_path, max_rows=10):
    try:
        import pandas as pd
        if not avp_path.exists():
            return "<p>Actual vs Predicted file not found.</p>"
        df = pd.read_csv(avp_path).head(max_rows)
        headers = list(df.columns)
        rows = []
        for _, row in df.iterrows():
            rows.append([f"{v:.4f}" if isinstance(
                v, float) else str(v) for v in row])
        return _table(headers, rows) + f"<p><em>Showing first {max_rows} rows</em></p>"
    except Exception as e:
        return f"<p>Could not load predictions table: {e}</p>"


def _render_chart_conclusion(chart_id: str, conclusions_dict: dict) -> str:
    """Render chart conclusion from conclusions dict by chart_id."""
    if not conclusions_dict:
        return ""
    conclusion_text = conclusions_dict.get(chart_id, "")
    if conclusion_text:
        return f'<p class="chart-conclusion"><em>{conclusion_text}</em></p>\n'
    return ""


def _metric_footnote(keys):
    """Render inline abbreviation footnote for specific keys."""
    items = [(k, ABBREVIATION_GLOSSARY[k])
             for k in keys if k in ABBREVIATION_GLOSSARY]
    if not items:
        return ""
    text = " | ".join(f"<strong>{k}</strong>: {v}" for k, v in items)
    return f'<p style="font-size:11px;color:#888;margin-top:4px;">{text}</p>\n'


def _validate_html(html: str) -> list:
    """Validate HTML output before writing. Returns list of issue strings."""
    issues = []
    # 1. DataTable init count
    dt_count = html.count("DataTable(") - html.count("// DataTable")
    if dt_count != 1:
        issues.append(f"DataTable() init count: {dt_count} (expected 1)")
    # 2. TOC builder
    if "$('#TOC')" not in html and '$("#TOC")' not in html:
        issues.append("TOC builder script not found")
    # 3. KaTeX auto-render
    if html.count("renderMathInElement") < 1:
        issues.append("KaTeX auto-render not found")
    # 4. Date-derived cols outside S3, S4 EDA note, and S6 rationale
    # Allow mentions in §3 (data wrangling), §4 EDA exclusion note, and §6 rationale table
    outside_s3 = html.split('id="data-wrangling"')
    if len(outside_s3) > 1:
        after_s3 = outside_s3[1].split(
            'id="eda"')[1] if 'id="eda"' in outside_s3[1] else ""
        for col in ["Date_year", "Date_month", "Date_day", "Date_dow"]:
            import re as _re
            cleaned = after_s3
            # Strip §6 rationale table mentions
            cleaned = _re.sub(
                r'<td>' + col + r'</td><td>Date-derived feature[^<]*</td>', '', cleaned)
            # Strip §4 EDA exclusion note (e.g. "Date_year/month/day/dow")
            cleaned = _re.sub(
                r'Date-derived features \([^)]*\) are excluded from these visualizations', '', cleaned)
            if col in cleaned:
                issues.append(
                    f"Date-derived column '{col}' found outside S3/S6 rationale")
    # 5. Sortable class coverage
    sortable_count = html.count('class="sortable"')
    if sortable_count < 8:
        issues.append(f"Only {sortable_count} sortable tables (expected >=8)")
    # 6. Chart conclusions coverage
    chart_count = html.count('class="chart-container"')
    conclusion_count = html.count('class="chart-conclusion"')
    if chart_count > 0 and conclusion_count < chart_count * 0.5:
        issues.append(
            f"Only {conclusion_count} conclusions for {chart_count} charts (<50%)")
    # 7. Duplicate script blocks
    ready_count = html.count("$(document).ready")
    if ready_count > 3:
        issues.append(f"$(document).ready count: {ready_count} (expected <=3)")
    return issues


def _format_mape(mape_val, metrics_dict=None):
    """Format MAPE value with warning flag if high/extreme (CR8, CR14, CR15)."""
    if mape_val is None:
        return "N/A"
    if not isinstance(mape_val, (int, float)):
        return str(mape_val)

    mape_str = f"{mape_val:.2f}%"
    flag = metrics_dict.get(
        "mape_flag", "normal") if metrics_dict else "normal"

    if flag == "extreme":
        return f'{mape_str} <span style="color:#E15759;font-size:11px;" title="Near-zero actual values inflate MAPE">&#9888;</span>'
    elif flag == "high":
        return f'{mape_str} <span style="color:#F28E2B;font-size:11px;" title="MAPE > 100% may indicate near-zero actuals">&#9888;</span>'
    else:
        return mape_str


# ── Main build function ───────────────────────────────────────────────────────

def build_report(project_name, task_type, p1_dir, p2_dir, p3_dir, output_path, version):
    run_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    style_block, toc_script = _load_template()

    # Load all artifacts
    p1 = _load(p1_dir / "phase1_results.json")
    p2 = _load(p2_dir / "phase2_results.json")
    p3 = _load(p3_dir / "phase3_results.json")

    eda_charts = _load_list(p1_dir / "eda_charts.json")
    raw_ts_plots = _load_list(p1_dir / "raw_ts_plots.json")
    log_diff_plots = _load_list(p1_dir / "log_diff_plots.json")
    ts_diagnostics = _load(p1_dir / "ts_diagnostics.json")
    acf_pacf_charts = _load_list(p1_dir / "acf_pacf_charts.json")
    split_preview = _load(p1_dir / "split_preview.json")
    feat_rationale = _load_list(p1_dir / "feature_selection_rationale.json")

    # Load chart conclusions (CR5, CR6, CR23)
    chart_conclusions_p1 = _load(p1_dir / "chart_conclusions.json")
    chart_conclusions_p3 = _load(p3_dir / "chart_conclusions.json")

    # Load Phase 2 chart conclusions (v5-final — previously missing)
    chart_conclusions_p2 = {}
    if p2_dir.exists():
        # Check root level first
        p2_cc_root = p2_dir / "chart_conclusions.json"
        if p2_cc_root.exists():
            chart_conclusions_p2.update(_load(p2_cc_root))
        # Then aggregate from per-target subdirs
        for subdir in sorted(p2_dir.iterdir()) if p2_dir.exists() else []:
            if subdir.is_dir():
                p2_cc_path = subdir / "chart_conclusions.json"
                if p2_cc_path.exists():
                    chart_conclusions_p2.update(_load(p2_cc_path))

    # Combined conclusions dict — phases generate, report renders
    all_conclusions = {}
    all_conclusions.update(chart_conclusions_p1)
    all_conclusions.update(chart_conclusions_p2)
    all_conclusions.update(chart_conclusions_p3)

    # Load drift matrix (CR16) — aggregate from per-target subdirs if multi-target
    drift_matrix = _load(p3_dir / "drift_matrix.json")
    if not drift_matrix and p3_dir.exists():
        drift_matrix = {}
        for subdir in sorted(p3_dir.iterdir()):
            dm_path = subdir / "drift_matrix.json"
            if dm_path.exists():
                dm = _load(dm_path)
                if dm and isinstance(dm, dict):
                    drift_matrix.update(dm)

    # Load self-check results (CR22)
    # Phase 1: always at root level
    self_check_p1 = _load(p1_dir / "self_check_results.json")

    # Phase 2 & 3: check root level first, then aggregate from per-target subdirs
    def _aggregate_self_checks(base_dir):
        """Aggregate per-target self-check results into a single summary."""
        root_sc = _load(base_dir / "self_check_results.json")
        if root_sc:
            return root_sc
        # Multi-target: aggregate from subdirectories
        all_warnings = []
        all_errors = []
        found = False
        if base_dir.exists():
            for subdir in sorted(base_dir.iterdir()):
                sc_path = subdir / "self_check_results.json"
                if sc_path.exists():
                    found = True
                    sc = _load(sc_path)
                    if sc:
                        target_name = subdir.name
                        for w in sc.get("warnings", []):
                            # Handle both string and dict warning formats
                            if isinstance(w, dict):
                                all_warnings.append(
                                    {"text": f"[{target_name}] {w['text']}", "severity": w.get("severity", "minor")})
                            else:
                                all_warnings.append(f"[{target_name}] {w}")
                        for e in sc.get("errors", []):
                            all_errors.append(f"[{target_name}] {e}")
        if not found:
            return {}
        return {
            "passed": len(all_errors) == 0,
            "warnings": all_warnings,
            "errors": all_errors
        }

    self_check_p2 = _aggregate_self_checks(p2_dir)
    self_check_p3 = _aggregate_self_checks(p3_dir)

    cmp_chart = _load(p2_dir / "model_comparison_chart.json")
    # CR12: 6 separate per-metric comparison charts
    comparison_charts = _load_list(p2_dir / "comparison_charts.json")
    exec_charts = _load_list(p3_dir / "execution_charts.json")
    insights_raw = _load_list(p3_dir / "business_insights.json")
    iter_tables = _load(p2_dir / "per_model_iteration_tables.json")
    mi_scores = _load(p1_dir / "feature_importance_phase1.json")

    # Per-model data (CR12)
    per_model_preds_all = _load(p2_dir / "per_model_predictions.json")
    per_model_plots_all = {}
    per_model_res_tables_all = {}
    for tname_key in (list(per_model_preds_all.keys()) if isinstance(per_model_preds_all, dict) else []):
        pmp_path = p3_dir / tname_key / "per_model_plots.json"
        pmr_path = p3_dir / tname_key / "per_model_residual_tables.json"
        if pmp_path.exists():
            per_model_plots_all[tname_key] = _load_list(pmp_path)
        if pmr_path.exists():
            per_model_res_tables_all[tname_key] = _load(pmr_path)

    is_multi = (p2.get("target") == "all")
    dataset_category = p1.get("dataset_category", "cross_sectional")
    is_ts = dataset_category == "time_series"

    # Shared phase1 fields
    n_rows = p1.get("n_rows", "N/A")
    n_cols = p1.get("n_cols", "N/A")
    schema = p1.get("schema", {})
    split = p1.get("split_info", {})
    sel_feats = p1.get("selected_features", [])
    feat_sel = p1.get("feature_selection", {})
    outliers = p1.get("outliers", {})
    date_cols = p1.get("date_cols_detected", [])

    p2_per_target = p2.get("per_target_results", {})
    p3_per_target = p3.get("per_target_results", {})
    best_models_summary = p2.get("best_models_summary", [])
    target_names = list(p2_per_target.keys()) if is_multi else [
        p1.get("target", p2.get("target", "target"))]

    # ── All model names ──
    all_model_names = set()
    if is_multi:
        for tname in target_names:
            t_p2 = p2_per_target.get(tname, {})
            for m in t_p2.get("models", []):
                all_model_names.add(m.get("name", ""))
            for mname in iter_tables.get(tname, {}).keys():
                all_model_names.add(mname)
    else:
        for m in p2.get("models", []):
            all_model_names.add(m.get("name", ""))

    # Win counts
    win_counts = {}
    for entry in best_models_summary:
        bm = entry.get("best_model", "")
        win_counts[bm] = win_counts.get(bm, 0) + 1
    dominant_model = max(
        win_counts, key=win_counts.get) if win_counts else "N/A"
    dominant_wins = win_counts.get(dominant_model, 0)

    title = f"{project_name} - Data Science Report"

    # ================================================================
    # HTML HEAD
    # ================================================================
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta http-equiv="X-UA-Compatible" content="IE=edge"/>
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.5/css/bootstrap.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.11.4/jquery-ui.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.5/js/bootstrap.min.js"></script>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<link rel="stylesheet" href="{KATEX_CSS_CDN}"/>
<script src="{KATEX_JS_CDN}"></script>
<script src="{KATEX_AUTO_CDN}"></script>
<link rel="stylesheet" href="{DATATABLES_CSS_CDN}"/>
<script src="{DATATABLES_JS_CDN}"></script>

{style_block}
</head>

<body>
<div class="container-fluid main-container">
<div class="row">

<div class="col-xs-12 col-sm-4 col-md-3">
  <div id="TOC"></div>
</div>

<div class="toc-content col-xs-12 col-sm-8 col-md-9">

<div class="report-header">
  <div class="logo">
    <img src="http://upload.wikimedia.org/wikipedia/en/0/0c/Mu_Sigma_Logo.jpg" alt="Mu Sigma"/>
  </div>
  <div class="title-block">
    <div class="title-text">{title}</div>
    <div class="author-date"><b>Author:</b> {REPORT_AUTHOR} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Version:</b> {version} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date:</b> {run_dt}</div>
  </div>
  <div class="spacer"></div>
</div>

<script>
var P={to_js(CHART_PALETTE)}, H=370;
var L={{font:{{family:'"Helvetica Neue",Helvetica,Arial,sans-serif',size:11}},paper_bgcolor:'#fff',plot_bgcolor:'#fff',margin:{{t:50,b:60,l:60,r:30}},xaxis:{{gridcolor:'#E5E5E5'}},yaxis:{{gridcolor:'#E5E5E5'}}}};
</script>

"""

    # ================================================================
    # SECTION 1: Introduction
    # ================================================================
    targets_list_html = "".join(f"<li>{_fmt(t)}</li>\n" for t in target_names)

    html += f"""
<div id="introduction" class="section level2">
<h2>Introduction</h2>
<p>This report presents the results of a comprehensive <strong>{task_type}</strong> analysis
for the <strong>{project_name}</strong> project, conducted using the Mu Sigma modular
Data Science pipeline. The analysis covers <strong>{len(target_names)} target variable{'s' if len(target_names) > 1 else ''}</strong>
{'simultaneously' if is_multi else ''}, applying machine learning and
statistical models to generate actionable forecasts.</p>

{f'<p><strong>Target variables analysed:</strong></p><ol>{targets_list_html}</ol>' if is_multi else ''}

<div id="intro-methodology" class="section level3">
<h3>Methodology</h3>
<ol><li><strong>Phase 1 - EDA &amp; Preprocessing:</strong> Data profiling, feature engineering, outlier detection, train/test split</li><li><strong>Phase 2 - Model Selection &amp; Validation:</strong> Multi-model training, cross-validation, hyperparameter tuning</li><li><strong>Phase 3 - Execution &amp; Insights:</strong> Final inference on held-out test set, drift analysis, business insight generation</li></ol>
</div>
</div>
"""

    # ================================================================
    # SECTION 2: Data Overview
    # ================================================================
    # Filter date-derived columns from schema display (v5-final Step 10D)
    display_schema = {k: v for k,
                      v in schema.items() if not is_date_derived(k)}
    schema_rows = []
    for col, info in list(display_schema.items())[:30]:
        schema_rows.append([
            col, info.get("dtype", ""), info.get("col_type", ""),
            info.get("n_unique", ""), f"{info.get('missing_pct', 0):.1f}%",
        ])

    missing_rows = []
    for col, info in sorted(schema.items(), key=lambda x: x[1].get("missing_pct", 0), reverse=True):
        mp = info.get("missing_pct", 0)
        if mp > 0:
            missing_rows.append([col, f"{mp:.1f}%"])

    n_missing_cols = len(missing_rows)

    html += f"""
<div id="data-overview" class="section level2">
<h2>Data Overview</h2>
<p>The dataset comprises <strong>{n_rows} observations</strong> across <strong>{n_cols} columns</strong>.
{'Data quality is excellent - no missing values detected.' if n_missing_cols == 0 else f'{n_missing_cols} column{"s" if n_missing_cols != 1 else ""} have missing values.'}</p>

<div id="column-schema" class="section level3">
<h3>Column Schema</h3>
{_table(["Column", "Dtype", "Type", "Unique", "Missing %"], schema_rows, extra_class="sortable")}
<p class="chart-conclusion"><em>The dataset contains {len(display_schema)} features ({sum(1 for v in display_schema.values() if v.get("col_type") == "numeric")} numeric, {sum(1 for v in display_schema.values() if v.get("col_type") == "categorical")} categorical{", " + str(len(date_cols)) + " datetime" if date_cols else ""}). {"Date-derived columns are excluded from this schema display." if date_cols else ""}</em></p>
</div>

<div id="missing-values" class="section level3">
<h3>Missing Values</h3>
{_table(["Column", "Missing %"], missing_rows) if missing_rows else '<p>No missing values detected.</p>'}
<p class="chart-conclusion"><em>{'No missing values detected across any column - the dataset is complete and ready for modeling without imputation.' if n_missing_cols == 0 else f'{n_missing_cols} column{"s" if n_missing_cols != 1 else ""} contain missing values. Missing data will be handled during preprocessing via forward-fill/backward-fill for time series or median imputation for cross-sectional data.'}</em></p>
</div>
</div>
"""

    # ================================================================
    # SECTION 3: Data Wrangling
    # ================================================================
    date_derived = [
        f"{dc}_year, {dc}_month, {dc}_day, {dc}_dow" for dc in date_cols]
    derived_html = "".join(
        f"<li>{d}</li>" for d in date_derived) if date_derived else "<li>None</li>"

    html += f"""
<div id="data-wrangling" class="section level2">
<h2>Data Wrangling</h2>

<div id="datetime-conversion" class="section level3">
<h3>DateTime Conversion</h3>
<p>{f'Detected and parsed <strong>{len(date_cols)} datetime column{"s" if len(date_cols) != 1 else ""}</strong>: {", ".join(date_cols)}.' if date_cols else 'No datetime columns detected.'}</p>
</div>

<div id="derived-features" class="section level3">
<h3>Derived Features</h3>
<p>Temporal features extracted from datetime columns:</p>
<ul>{derived_html}</ul>
<p>These derived features are used for modeling but excluded from EDA visualizations to avoid redundancy.</p>
</div>

<div id="cleaning-steps" class="section level3">
<h3>Cleaning Steps Applied</h3>
<ul>
<li>Numeric missing values imputed with column median</li>
<li>Categorical missing values imputed with most frequent value</li>
<li>Numeric features standardized (zero mean, unit variance)</li>
<li>Categorical features one-hot encoded</li>
</ul>
</div>
</div>
"""

    # ================================================================
    # SECTION 4: Exploratory Data Analysis
    # ================================================================
    eda_chart_html = ""
    dist_charts = [c for c in eda_charts if c.get("chart_id", "").startswith(
        "dist_") or c.get("chart_id", "").startswith("cat_")]
    for i, ch in enumerate(dist_charts[:20]):
        chart_id_val = ch.get("chart_id", "")
        eda_chart_html += render_chart(ch, f"eda-chart-{i}")
        eda_chart_html += _render_chart_conclusion(
            chart_id_val, chart_conclusions_p1)

    corr_chart = next(
        (c for c in eda_charts if "correlation" in c.get("chart_id", "").lower()), None)
    outlier_charts = [c for c in eda_charts if c.get(
        "chart_id", "").startswith("outlier_")]

    outlier_rows = []
    for col, v in list(outliers.items())[:20]:
        outlier_rows.append(
            [col, v.get("iqr_flags", 0), v.get("zscore_flags", 0)])

    total_iqr = sum(v.get("iqr_flags", 0) for v in outliers.values())
    total_z = sum(v.get("zscore_flags", 0) for v in outliers.values())

    # Build individual outlier subsections (CR4)
    outlier_subsections_html = ""
    for i, ch in enumerate(outlier_charts[:20]):
        chart_id_val = ch.get("chart_id", "")
        col_name = chart_id_val.replace(
            "outlier_", "").replace("_", " ").title()
        sub_chart_html = render_chart(ch, f"outlier-{i}")
        conclusion_html = _render_chart_conclusion(
            chart_id_val, chart_conclusions_p1)
        outlier_subsections_html += f"""
<div id="outlier-{_slug(col_name)}" class="section level4">
<h4>{col_name}</h4>
{sub_chart_html}
{conclusion_html}
</div>
"""

    html += f"""
<div id="eda" class="section level2">
<h2>Exploratory Data Analysis</h2>
<p>This section explores the dataset through distribution analysis, correlations, and outlier detection.
Date-derived features ({', '.join(f'{dc}_year/month/day/dow' for dc in date_cols) if date_cols else 'none'}) are excluded from these visualizations.</p>

<div id="feature-distributions" class="section level3">
<h3>Feature Distributions</h3>
{eda_chart_html if eda_chart_html else '<p>No distribution charts available.</p>'}
</div>

<div id="correlation-analysis" class="section level3">
<h3>Correlation Analysis</h3>
{render_chart(corr_chart, "corr-heatmap", style="min-height:500px;width:100%;") if corr_chart else '<p>Correlation chart not available.</p>'}
{_render_chart_conclusion("correlation_heatmap", chart_conclusions_p1)}
</div>

<div id="outlier-detection" class="section level3">
<h3>Outlier Detection</h3>
<p><strong>Methodology:</strong> Outlier detection uses two complementary methods:
<strong>(1) IQR Method</strong> - values below Q1 - 1.5xIQR or above Q3 + 1.5xIQR are flagged.
This is robust to non-normal distributions as it relies on quartiles rather than mean/standard deviation.
<strong>(2) Z-Score Method</strong> - values more than 3 standard deviations from the mean are flagged.
This assumes approximate normality and is sensitive to extreme values.
Using both methods together provides comprehensive outlier identification. Flagged values are
retained for modeling - tree-based algorithms (Random Forest, XGBoost, Gradient Boosting) are
inherently robust to outliers due to their split-based decision boundaries.</p>
<p><strong>{total_iqr} IQR flags</strong> and <strong>{total_z} Z-score flags</strong> detected.</p>
{_table(["Column", "IQR Flags", "Z-Score Flags"], outlier_rows, extra_class="sortable") if outlier_rows else ''}
<p class="chart-conclusion"><em>{'Minimal outlier presence across features - data quality is high for modeling.' if (total_iqr + total_z) < 20 else f'A total of {total_iqr} IQR-flagged and {total_z} Z-score-flagged observations were detected. These are retained for tree-based models which are robust to outliers, but may impact linear model performance.'}</em></p>
{outlier_subsections_html}
</div>
</div>
"""

    # ================================================================
    # SECTION 5: Time Series EDA (conditional)
    # ================================================================
    if is_ts:
        # Raw TS plots
        raw_ts_html = ""
        for i, ch in enumerate(raw_ts_plots[:15]):
            chart_id_val = ch.get("chart_id", "")
            raw_ts_html += render_chart(ch, f"raw-ts-{i}")
            raw_ts_html += _render_chart_conclusion(
                chart_id_val, chart_conclusions_p1)

        # Log-diff plots
        log_diff_html = ""
        for i, ch in enumerate(log_diff_plots[:15]):
            chart_id_val = ch.get("chart_id", "")
            log_diff_html += render_chart(ch, f"log-diff-{i}")
            log_diff_html += _render_chart_conclusion(
                chart_id_val, chart_conclusions_p1)

        # Stationarity tables (ADF + KPSS)
        adf_rows = []
        kpss_rows = []
        for col, diag in ts_diagnostics.items():
            adf = diag.get("adf", {})
            if "error" not in adf:
                stat_label = "Stationary" if adf.get(
                    "stationary") else "Non-stationary"
                adf_rows.append([
                    col, _fv(adf.get("test_statistic")),
                    _fv(adf.get("p_value"), ".6f"),
                    adf.get("lags_used", "N/A"), stat_label
                ])
            kp = diag.get("kpss", {})
            if "error" not in kp:
                stat_label = "Stationary" if kp.get(
                    "stationary") else "Non-stationary"
                kpss_rows.append([
                    col, _fv(kp.get("test_statistic")),
                    _fv(kp.get("p_value"), ".6f"), stat_label
                ])

        # ACF/PACF charts
        acf_pacf_html = ""
        for i, ch in enumerate(acf_pacf_charts[:20]):
            chart_id_val = ch.get("chart_id", "")
            acf_pacf_html += render_chart(ch, f"acf-pacf-{i}")
            acf_pacf_html += _render_chart_conclusion(
                chart_id_val, chart_conclusions_p1)

        html += f"""
<div id="ts-eda" class="section level2">
<h2>Time Series EDA</h2>
<p>Time-series-specific diagnostics for all numeric variables. All charts use the date column as X-axis.</p>

<div id="raw-ts-plots" class="section level3">
<h3>Raw Time Series Plots</h3>
<p>One line chart per variable showing the raw values over time.</p>
{raw_ts_html if raw_ts_html else '<p>No time series plots available.</p>'}
</div>

<div id="log-diff-plots" class="section level3">
<h3>Log-Differenced Plots</h3>
<p>Log-differenced (or first-differenced for non-positive series) values to visualize stationarity.</p>
{log_diff_html if log_diff_html else '<p>No log-diff plots available.</p>'}
</div>

<div id="stationarity-checks" class="section level3">
<h3>Stationarity Checks</h3>
<p><strong>Methodology:</strong> Two complementary stationarity tests are applied:
<strong>ADF (Augmented Dickey-Fuller)</strong> tests the null hypothesis that a unit root is present
(i.e., the series is non-stationary). A p-value &lt; 0.05 rejects the null, confirming stationarity.
<strong>KPSS (Kwiatkowski-Phillips-Schmidt-Shin)</strong> reverses the null hypothesis - it tests whether
the series IS stationary. A p-value &gt; 0.05 fails to reject stationarity. Using both tests
together addresses their individual limitations: ADF has low power for near-unit-root processes,
while KPSS can falsely reject stationarity for long-memory processes. The ideal result is
ADF stationary + KPSS stationary (both agree the series is stable).</p>
{_table(["Variable", "Test Statistic", "p-value", "Lags", "Result"], adf_rows, extra_class="sortable") if adf_rows else '<p>ADF results not available.</p>'}
{_table(["Variable", "Test Statistic", "p-value", "Result"], kpss_rows, extra_class="sortable") if kpss_rows else '<p>KPSS results not available.</p>'}
{_metric_footnote(["ADF", "KPSS"])}
</div>

<div id="acf-pacf" class="section level3">
<h3>ACF &amp; PACF</h3>
<p><strong>Methodology:</strong> <strong>ACF (Autocorrelation Function)</strong> measures the correlation between
a time series and its lagged values at various lag orders - it reveals the overall memory structure
of the series including indirect effects through intermediate lags.
<strong>PACF (Partial Autocorrelation Function)</strong> isolates the direct effect of each lag by
controlling for all intermediate lags. The dashed lines represent 95% confidence intervals
(+/-1.96/sqrt(n)) - lags beyond these bands are statistically significant. ACF helps determine the
MA(q) order in ARIMA modeling (significant lags before cutoff), while PACF guides the AR(p) order
(significant partial correlations before cutoff). Together they inform ARIMA(p,d,q) model specification.</p>
{acf_pacf_html if acf_pacf_html else '<p>ACF/PACF charts not available.</p>'}
</div>
</div>
"""

    # ================================================================
    # SECTION 6: Feature Engineering & Selection
    # ================================================================
    sel_rows = [
        ["1", "Variance Threshold (0.01)", "Drop near-zero variance",
         f"{len(feat_sel.get('dropped_low_var', []))} dropped"],
        ["2", "Correlation Filter (>0.95)", "Drop highly correlated",
         f"{len(feat_sel.get('dropped_high_corr', []))} dropped"],
        ["3", "Mutual Information", "Rank by MI score",
         f"{len(sel_feats)} retained"],
    ]

    # Feature selection rationale table with S.No. (CR8)
    rationale_rows = []
    for r in feat_rationale:
        rationale_rows.append([r.get("column", ""), r.get("reason", "")])

    split_type = split.get("split_type", "random")
    test_size = split.get("test_size", 0.2)

    # Split preview tables with scrollable wrapper (CR8)
    train_preview = split_preview.get("train_preview", [])
    test_preview = split_preview.get("test_preview", [])
    preview_html = ""
    if train_preview:
        tp_headers = list(train_preview[0].keys()) if train_preview else []
        tp_rows = [[_fv(row.get(h, ""), ".3f") if isinstance(row.get(h), float) else str(row.get(h, ""))
                    for h in tp_headers] for row in train_preview[:8]]
        preview_html += "<p><strong>Training Set Preview (first 8 rows):</strong></p>\n"
        preview_html += _table_scrollable(tp_headers,
                                          tp_rows, add_sno=True) if tp_headers else ""
    if test_preview:
        te_headers = list(test_preview[0].keys()) if test_preview else []
        te_rows = [[_fv(row.get(h, ""), ".3f") if isinstance(row.get(h), float) else str(row.get(h, ""))
                    for h in te_headers] for row in test_preview[:5]]
        preview_html += "<p><strong>Test Set Preview (first 5 rows):</strong></p>\n"
        preview_html += _table_scrollable(te_headers,
                                          te_rows, add_sno=True) if te_headers else ""

    html += f"""
<div id="feature-engineering" class="section level2">
<h2>Feature Engineering &amp; Selection</h2>
<p>Feature selection applied in three steps to reduce dimensionality. <strong>{len(sel_feats)} features</strong> retained for modeling.</p>

<div id="selection-summary" class="section level3">
<h3>Selection Summary</h3>
{_table(["Step", "Method", "Action", "Result"], sel_rows)}
{_render_chart_conclusion("feature_selection_summary", all_conclusions) or
 ('<p class="chart-conclusion"><em>' + llm_describe("feature_selection", {
     "n_retained": len(sel_feats), "n_original": len(schema),
     "n_dropped_var": sum(1 for r in feat_rationale if 'variance' in r.get('reason', '').lower() or 'near-constant' in r.get('reason', '').lower()),
     "n_dropped_corr": sum(1 for r in feat_rationale if 'correlation' in r.get('reason', '').lower())
 }) + '</em></p>' if sel_feats else '')}
</div>

{'<div id="drop-rationale" class="section level3"><h3>Dropped Variables Rationale</h3>' + _table(["Column", "Reason"], rationale_rows, add_sno=True) + '<p class="chart-conclusion"><em>' + str(len(rationale_rows)) + (' features were' if len(rationale_rows) != 1 else ' feature was') + ' removed during feature selection. Date-derived columns, low-variance features, and highly correlated pairs are filtered to reduce multicollinearity and improve model generalization.</em></p></div>' if rationale_rows else ''}

<div id="train-test-split" class="section level3">
<h3>Train/Test Split</h3>
<p>Split strategy: <strong>{split_type}</strong>{'  (chronological - no shuffle, preserving temporal order)' if split_type == 'time_aware' else ''}.</p>
{_table(["Set", "Rows", "Split %"], [
    ["Training", split.get("n_train", "N/A"), f"{int((1 - test_size) * 100)}%"],
    ["Test", split.get("n_test", "N/A"), f"{int(test_size * 100)}%"],
])}
{_render_chart_conclusion("train_test_split", all_conclusions) or
 ('<p class="chart-conclusion"><em>' + llm_describe("train_test_split", {
     "split_type": split_type, "n_train": split.get("n_train", 0),
     "n_test": split.get("n_test", 0), "test_pct": int(test_size * 100),
     "is_temporal": split_type == "time_aware"
 }) + '</em></p>')}
</div>

<div id="split-preview" class="section level3">
<h3>Data Preview After Split</h3>
{preview_html if preview_html else '<p>Data preview not available.</p>'}
</div>
</div>
"""

    # ================================================================
    # SECTION 7: Model Training & Results
    # ================================================================
    model_descs = {
        "ARIMA(1,1,1)": "Classical univariate TS model (autoregressive + moving average with differencing)",
        "HoltWinters": "Triple exponential smoothing for trend and seasonality",
        "VAR": "Vector AutoRegression - multivariate TS model fitting all series jointly",
        "XGBRegressor": "Gradient-boosted decision tree ensemble (best for structured data)",
        "XGBClassifier": "Gradient-boosted decision tree ensemble for classification",
        "GradientBoosting": "Sequential tree ensemble correcting residuals",
        "RandomForestRegressor": "Bagged ensemble of decision trees",
        "RandomForestClassifier": "Bagged decision tree ensemble for classification",
        "Ridge": "L2-regularized linear regression",
        "LinearRegression": "Ordinary least squares baseline",
        "LogisticRegression": "Linear classification via logistic function",
        "SVC": "Support vector classifier with kernel functions",
    }

    models_rows = []
    for mname in sorted(all_model_names):
        models_rows.append([mname, model_descs.get(mname, mname)])

    html += f"""
<div id="model-training" class="section level2">
<h2>Model Training &amp; Results</h2>
<p>{len(all_model_names)} candidate models evaluated per target. <strong>{dominant_model}</strong> won {dominant_wins} of {len(target_names)} targets.</p>

<div id="models-considered" class="section level3">
<h3>Models Considered</h3>
{_table(["Model", "Description"], models_rows)}
<p class="chart-conclusion"><em>{len(models_rows)} models were evaluated. Best model selection uses composite scoring: 35% RMSE + 25% MAPE + 25% R-Squared + 15% CV stability, ensuring robust performance across multiple criteria rather than optimizing a single metric.</em></p>
</div>
"""

    # Per-target results with per-model plots (CR12, CR17)
    if is_multi:
        for tname in target_names:
            t_slug = _slug(tname)
            t_display = _fmt(tname)
            t_iter = iter_tables.get(tname, {})
            t_p2 = p2_per_target.get(tname, {})
            t_best_model = t_p2.get("best_model", "")
            t_models = t_p2.get("models", [])

            model_headers = ["Model", "RMSE", "MAE",
                             "MAPE", "R2", "CV Mean", "CV Std"]
            model_rows = []
            best_names = {t_best_model}

            if t_iter:
                for mname, mdata in t_iter.items():
                    tm = mdata.get("test_metrics", {})
                    model_rows.append([
                        mname, _fv(tm.get("rmse")), _fv(tm.get("mae")),
                        _fv(tm.get("mape"), ".2f"), _fv(tm.get("r2")),
                        _fv(mdata.get("cv_mean")), _fv(mdata.get("cv_std")),
                    ])
            elif t_models:
                for m in t_models:
                    mm = m.get("metrics", {})
                    model_rows.append([
                        m.get("name", ""), _fv(
                            mm.get("rmse")), _fv(mm.get("mae")),
                        _fv(mm.get("mape"), ".2f"), _fv(mm.get("r2")),
                        _fv(mm.get("cv_mean")), _fv(mm.get("cv_std")),
                    ])

            def bold_best(idx, row):
                return row[0] in best_names

            # Per-model plots for this target (CR12)
            per_model_chart_html = ""
            t_pm_plots = per_model_plots_all.get(tname, [])
            for ci, ch in enumerate(t_pm_plots[:10]):
                per_model_chart_html += render_chart(ch, f"pm-{t_slug}-{ci}")
                pm_cid = ch.get("chart_id", "")
                per_model_chart_html += _render_chart_conclusion(pm_cid, all_conclusions)

            # Per-model residual tables (CR12)
            per_model_res_html = ""
            t_pm_res = per_model_res_tables_all.get(tname, {})
            for mname, rows_data in list(t_pm_res.items())[:6]:
                if rows_data:
                    res_headers = ["Index", "Actual", "Predicted", "Residual"]
                    res_rows = [[str(r.get("index", "")), _fv(r.get("actual")),
                                 _fv(r.get("predicted")), _fv(r.get("residual"))]
                                for r in rows_data[:10]]
                    per_model_res_html += f"<p><strong>{mname}</strong></p>\n"
                    per_model_res_html += _table(res_headers, res_rows)
                    per_model_res_html += "<p><em>Showing first 10 rows</em></p>\n"

            # Low-confidence badge (v5-final Step 12C)
            low_conf = t_p2.get("low_confidence", False)
            low_conf_badge = ' <span style="background:#FFF3CD;padding:2px 6px;border-radius:3px;font-size:11px;">Low Confidence</span>' if low_conf else ""

            # Model summary rendering (v5-final Step 10F)
            model_summary_html = ""
            model_summaries = t_p2.get("model_summaries", {})
            best_summary = model_summaries.get(t_best_model, {})
            if best_summary:
                summary_type = best_summary.get("type", "")
                if summary_type == "statsmodels":
                    summary_text = best_summary.get("summary_text", "")
                    aic = best_summary.get("aic", "N/A")
                    bic = best_summary.get("bic", "N/A")
                    model_summary_html += f'<p><strong>{t_best_model} Model Summary</strong> (AIC: {aic}, BIC: {bic})</p>\n'
                    model_summary_html += f'<pre><code>{summary_text}</code></pre>\n'
                elif summary_type == "tree":
                    fi = best_summary.get("feature_importances", [])
                    fi_rows = [
                        [item["feature"], f'{item["importance"]:.4f}'] for item in fi[:10]]
                    model_summary_html += f'<p><strong>{t_best_model} - Top 10 Feature Importances</strong></p>\n'
                    model_summary_html += _table(["Feature", "Importance"],
                                                 fi_rows, extra_class="sortable")
                elif summary_type == "linear":
                    coefs = best_summary.get("coefficients", [])
                    coef_rows = [
                        [item["feature"], f'{item["coef"]:.4f}'] for item in coefs]
                    intercept = best_summary.get("intercept")
                    model_summary_html += f'<p><strong>{t_best_model} - Coefficients</strong>{f" (Intercept: {intercept})" if intercept else ""}</p>\n'
                    model_summary_html += _table(["Feature", "Coefficient"],
                                                 coef_rows, extra_class="sortable")
            model_summary_html += _render_chart_conclusion(
                f"model_summary_{tname}", all_conclusions)

            # Anomaly flag rendering (v5-final Step 10H)
            anomaly_html = ""
            anomaly_path = p2_dir / tname / "anomaly_flags.json"
            if anomaly_path.exists():
                anomaly_data = _load(anomaly_path)
                for amodel_name, flags in anomaly_data.items():
                    oor = flags.get("out_of_range_count", 0)
                    dips = flags.get("sudden_dips_count", 0)
                    if oor > 0 or dips > 0:
                        anomaly_html += f"""
<div style="border-left:3px solid #E15759;padding:8px;margin:8px 0;background:#fff5f5;">
  <p><strong>Prediction Anomaly ({amodel_name}):</strong> {oor} out-of-range predictions, {dips} sudden dips detected.</p>
</div>
"""

            html += f"""
<div id="training-{t_slug}" class="section level3">
<h3>{t_display}{low_conf_badge}</h3>
<p>Best model: <strong>{t_best_model}</strong></p>
{_table(model_headers, model_rows, bold_test=bold_best, extra_class="sortable") if model_rows else '<p>No model data.</p>'}
{_metric_footnote(["RMSE", "MAE", "MAPE", "R2", "CV"])}
{_render_chart_conclusion(f"model_metrics_{tname}", all_conclusions)}
{model_summary_html}
{anomaly_html}
{per_model_chart_html}
{per_model_res_html}
</div>
"""
    else:
        models = p2.get("models", [])
        best_model = p2.get("best_model", "")
        model_headers = ["Model", "RMSE", "MAE",
                         "MAPE", "R2", "CV Mean", "CV Std"]
        model_rows = []
        for m in models:
            mm = m.get("metrics", {})
            model_rows.append([
                m.get("name", ""), _fv(mm.get("rmse")), _fv(mm.get("mae")),
                _fv(mm.get("mape"), ".2f"), _fv(mm.get("r2")),
                _fv(mm.get("cv_mean")), _fv(mm.get("cv_std")),
            ])

        def bold_best_single(idx, row):
            return row[0] == best_model
        html += _table(model_headers, model_rows,
                       bold_test=bold_best_single, extra_class="sortable") if model_rows else ''
        html += _metric_footnote(["RMSE", "MAE", "MAPE", "R2", "CV"])

    html += "</div>\n"

    # ================================================================
    # SECTION 8: Model Comparison
    # ================================================================
    bms_headers = ["Variable", "Best Model", "RMSE", "MAE", "MAPE", "R2"]
    bms_rows = []
    for entry in best_models_summary:
        m = entry.get("metrics", {})
        mape_val = m.get("mape")
        mape_str = f"{mape_val:.2f}%" if isinstance(
            mape_val, (int, float)) else str(mape_val or "N/A")
        bms_rows.append([
            _fmt(entry.get("target", "")), entry.get("best_model", ""),
            _fv(m.get("rmse")), _fv(m.get("mae")), mape_str, _fv(m.get("r2")),
        ])

    # Comparison charts
    comp_chart_html = render_chart(
        cmp_chart, "model-cmp-main") if cmp_chart else ""

    # Build cross-model comparison table (CR13: 6 metrics, CR8: MAPE warnings)
    comp_full_headers = ["Variable", "Best Model",
                         "RMSE", "MAE", "MAPE", "R2", "CV Mean", "CV Std"]
    comp_full_rows = []
    for tname in target_names:
        t_display = _fmt(tname)
        t_p2 = p2_per_target.get(tname, {}) if is_multi else p2
        t_best = t_p2.get("best_model", "N/A")
        ft_metrics = t_p2.get("fine_tuned_metrics", {})
        t_iter = iter_tables.get(tname, {})

        best_metrics = ft_metrics if ft_metrics else {}
        if not best_metrics:
            for m in t_p2.get("models", []):
                if m.get("name") == t_best:
                    best_metrics = m.get("metrics", {})
                    break

        cv_mean, cv_std = "N/A", "N/A"
        if t_best in t_iter:
            cv_mean = _fv(t_iter[t_best].get("cv_mean", "N/A"))
            cv_std = _fv(t_iter[t_best].get("cv_std", "N/A"))

        mape_val = best_metrics.get("mape")
        mape_str = _format_mape(mape_val, best_metrics)

        comp_full_rows.append([
            t_display, t_best,
            _fv(best_metrics.get("rmse")), _fv(best_metrics.get("mae")),
            mape_str, _fv(best_metrics.get("r2")),
            cv_mean, cv_std,
        ])

    avg_r2_all = [e.get("metrics", {}).get("r2", 0)
                  for e in best_models_summary]
    avg_r2_val = sum(avg_r2_all) / len(avg_r2_all) if avg_r2_all else 0

    html += f"""
<div id="model-comparison" class="section level2">
<h2>Model Comparison</h2>
<p>Average R2 across all targets: <strong>{avg_r2_val:.3f}</strong>.</p>

<div id="six-metric-comparison" class="section level3">
<h3>6-Metric Comparison Table</h3>
{_table(comp_full_headers, comp_full_rows, extra_class="sortable")}
</div>

<div id="best-models-summary" class="section level3">
<h3>Best Models Summary</h3>
{_table(bms_headers, bms_rows, extra_class="sortable")}
{_metric_footnote(["RMSE", "MAE", "MAPE", "R2"])}
{('<p class="chart-conclusion"><em>' + llm_describe("comparison_table", {
     "n_targets": len(best_models_summary),
     "avg_r2": round(avg_r2_val, 3),
     "best_target": best_models_summary[0]["target"] if best_models_summary else "",
     "worst_target": best_models_summary[-1]["target"] if best_models_summary else ""
 }) + '</em></p>') if best_models_summary else ''}
</div>

<div id="comparison-charts" class="section level3">
<h3>Comparison Charts</h3>"""

    # CR12: Render 6 separate per-metric comparison charts
    if comparison_charts and len(comparison_charts) > 0:
        metric_keys_for_chart = ["rmse", "mae",
                                 "mape", "r2", "cv_mean", "cv_std"]
        for ci, ch in enumerate(comparison_charts[:6]):
            chart_title = ch.get("layout", {}).get(
                "title", {}).get("text", f"Comparison {ci+1}")
            mkey = metric_keys_for_chart[ci] if ci < len(
                metric_keys_for_chart) else f"chart_{ci}"
            html += f"""
<div id="comp-chart-{ci}" class="section level4">
<h4>{chart_title}</h4>
{render_chart(ch, f"cmp-sep-{ci}")}
{_render_chart_conclusion(f"comparison_{mkey}", all_conclusions)}
</div>
"""
    elif is_multi and best_models_summary:
        # Build 6 cross-target per-metric charts from best_models_summary
        metrics_info = [
            ("rmse", "RMSE (Best Model per Target)", False),
            ("mae", "MAE (Best Model per Target)", False),
            ("mape", "MAPE % (Best Model per Target)", False),
            ("r2", "R-Squared (Best Model per Target)", True),
            ("cv_mean", "CV Mean (Best Model per Target)", True),
            ("cv_std", "CV Std Dev (Best Model per Target)", False),
        ]
        for mi, (mkey, mlabel, higher_better) in enumerate(metrics_info):
            t_names = []
            t_values = []
            t_models = []
            for entry in best_models_summary:
                tname = entry.get("target", "?")
                bm = entry.get("best_model", "?")
                val = entry.get("metrics", {}).get(mkey, 0)
                if val is None:
                    val = 0
                t_names.append(_fmt(tname))
                t_values.append(round(val, 4))
                t_models.append(bm)

            color = CHART_PALETTE[mi % len(CHART_PALETTE)]
            chart_obj = {
                "data": [{
                    "type": "bar",
                    "orientation": "h",
                    "y": t_names,
                    "x": t_values,
                    "text": t_models,
                    "textposition": "auto",
                    "marker": {"color": color},
                    "name": mlabel,
                    "hovertemplate": "%{y}<br>" + mlabel + ": %{x:.4f}<br>Model: %{text}<extra></extra>"
                }],
                "layout": {
                    **plotly_layout(mlabel, height=max(350, len(t_names) * 35)),
                    "xaxis": {"title": mlabel, "gridcolor": "#E5E5E5"},
                    "yaxis": {"title": "", "gridcolor": "#E5E5E5", "automargin": True},
                    "margin": {"t": 50, "b": 50, "l": 180, "r": 30}
                }
            }
            html += f"""
<div id="comp-chart-{mi}" class="section level4">
<h4>{mlabel}</h4>
{render_chart(chart_obj, f"cmp-sep-{mi}")}
{_render_chart_conclusion(f"comparison_{mkey}", all_conclusions)}
</div>
"""
    elif comp_chart_html:
        html += comp_chart_html
    else:
        html += '<p>No comparison charts available.</p>'

    html += """
</div>
</div>
"""

    # ================================================================
    # SECTION 9: Validation & Drift
    # ================================================================
    drift_flagged_targets = []
    for tname in target_names:
        t_p3 = p3_per_target.get(tname, {}) if is_multi else p3
        t_drift = t_p3.get("drift_analysis", {})
        if any(v.get("flag") for v in t_drift.values()):
            drift_flagged_targets.append(_fmt(tname))

    html += f"""
<div id="validation-drift" class="section level2">
<h2>Validation &amp; Drift</h2>
<p>Comparing Phase 2 (CV on training) vs Phase 3 (test set) metrics.
{f'{len(drift_flagged_targets)} target{"s" if len(drift_flagged_targets) != 1 else ""} showed drift.' if drift_flagged_targets else 'No significant drift detected.'}</p>
"""

    # CR16: Full drift matrix with red flagging (if available)
    if drift_matrix and isinstance(drift_matrix, dict):
        metrics_list = ["rmse", "mae", "mape", "r2"]
        drift_full_headers = ["Target"] + [m.upper() for m in metrics_list]
        drift_full_rows_html = ""
        for tname in target_names:
            t_display = _fmt(tname)
            t_drift_data = drift_matrix.get(tname, {})
            row_html = f"<tr><td>{t_display}</td>"
            for metric in metrics_list:
                info = t_drift_data.get(metric, {})
                drift_pct = info.get("drift_pct", 0)
                drift_str = f"{drift_pct:.2f}%"
                # Red flag if drift > 5%
                if abs(drift_pct) > 5:
                    row_html += f'<td style="color:#E15759;font-weight:bold;">{drift_str}</td>'
                else:
                    row_html += f"<td>{drift_str}</td>"
            row_html += "</tr>\n"
            drift_full_rows_html += row_html
        html += f"""
<div id="drift-matrix" class="section level3">
<h3>Full Drift Matrix</h3>
<table class="sortable">
<thead><tr>{''.join(f'<th>{h}</th>' for h in drift_full_headers)}</tr></thead>
<tbody>
{drift_full_rows_html}
</tbody>
</table>
</div>
"""

    # Per-target detailed drift tables
    drift_footnote = '<p style="font-size:11px;color:#888;margin-top:4px;">Drift % = |Phase2 - Phase3| / Phase2 x 100</p>\n'
    if is_multi:
        for tname in target_names:
            t_slug = _slug(tname)
            t_display = _fmt(tname)
            t_p3 = p3_per_target.get(tname, {})
            t_drift = t_p3.get("drift_analysis", {})
            # Date range for drift header (v5-final Step 10E)
            test_range = t_p3.get("test_date_range", {})
            date_label = f" (Test Period: {test_range.get('start', '?')} - {test_range.get('end', '?')})" if test_range else ""
            drift_rows = []
            for metric, info in t_drift.items():
                flag = "Warning: Yes" if info.get("flag") else "OK"
                drift_rows.append([
                    metric.upper(), _fv(info.get("phase2", 0)),
                    _fv(info.get("phase3", 0)),
                    f"{info.get('drift_pct', 0):.2f}%", flag,
                ])
            html += f"""
<div id="drift-{t_slug}" class="section level3">
<h3>{t_display}{date_label}</h3>
{_table(["Metric", "Phase 2", "Phase 3", "Drift %", "Flag"], drift_rows, extra_class="sortable") if drift_rows else '<p>No drift data.</p>'}
{drift_footnote}
{_render_chart_conclusion(f"drift_{tname}", all_conclusions)}
</div>
"""
    else:
        drift = p3.get("drift_analysis", {})
        drift_rows = []
        for metric, info in drift.items():
            flag = "Warning: Yes" if info.get("flag") else "OK"
            drift_rows.append([
                metric.upper(), _fv(info.get("phase2", 0)),
                _fv(info.get("phase3", 0)),
                f"{info.get('drift_pct', 0):.2f}%", flag,
            ])
        html += _table(["Metric", "Phase 2", "Phase 3", "Drift %",
                       "Flag"], drift_rows, extra_class="sortable") if drift_rows else ''
        html += drift_footnote

    html += "</div>\n"

    # ================================================================
    # SECTION 10: Business Insights
    # ================================================================
    insights_by_target = {}
    for ins in insights_raw:
        tv = ins.get("target_variable", "General")
        insights_by_target.setdefault(tv, []).append(ins)

    html += f"""
<div id="business-insights" class="section level2">
<h2>Business Insights</h2>
<p>{len(insights_raw)} insights generated across {len(target_names)} target variables.</p>
"""

    # v5-final: Insight card format with backward compat (Observation/Finding/Insight)
    def _render_insight_card(ins):
        """Render insight with backward-compatible field mapping."""
        title = ins.get("title", "Insight")
        observation = ins.get("observation", "")
        finding = ins.get("finding", ins.get(
            "implication", ""))  # backward compat
        insight = ins.get("insight", ins.get(
            "strategic_action", ins.get("action", "")))  # backward compat
        return f"""
<div style="border-left:3px solid #4E79A7;padding:12px;margin:12px 0;background:#f8f9fa;">
  <p><strong>{title}</strong></p>
  <p><strong>Observation:</strong> {observation}</p>
  <p><strong>Finding:</strong> {finding}</p>
  <p><strong>Insight:</strong> {insight}</p>
</div>
"""

    for tname in target_names:
        t_insights = insights_by_target.get(tname, [])
        if t_insights:
            t_slug = _slug(tname)
            html += f"""
<div id="insights-{t_slug}" class="section level3">
<h3>{_fmt(tname)}</h3>
"""
            for ins in t_insights:
                html += _render_insight_card(ins)
            html += "</div>\n"

    general = insights_by_target.get("General", [])
    if general:
        html += """
<div id="insights-general" class="section level3">
<h3>General Insights</h3>
"""
        for ins in general:
            html += _render_insight_card(ins)
        html += "</div>\n"

    html += "</div>\n"

    # ================================================================
    # SECTION 11: Executive Summary (CR20: 4 paragraphs, all 6 metrics)
    # ================================================================
    total_preds = sum(p3_per_target.get(t, {}).get("n_predictions", 0)
                      for t in target_names) if is_multi else p3.get("n_predictions", 0)
    high_r2_count = sum(1 for e in best_models_summary if e.get(
        "metrics", {}).get("r2", 0) > 0.95)

    # Build table with all 6 metrics
    exec_summary_headers = ["Variable", "Best Model",
                            "RMSE", "MAE", "MAPE", "R2", "CV Mean", "CV Std"]
    exec_summary_rows = []
    for tname in target_names:
        t_p2 = p2_per_target.get(tname, {}) if is_multi else p2
        t_p3 = p3_per_target.get(tname, {}) if is_multi else p3
        t_best = t_p2.get("best_model", "N/A")
        t_fm = t_p3.get("final_metrics", t_p2.get("fine_tuned_metrics", {}))
        t_iter = iter_tables.get(tname, {})

        cv_mean, cv_std = "N/A", "N/A"
        if t_best in t_iter:
            cv_mean = _fv(t_iter[t_best].get("cv_mean", "N/A"))
            cv_std = _fv(t_iter[t_best].get("cv_std", "N/A"))

        mape_val = t_fm.get("mape")
        mape_str = _format_mape(mape_val, t_fm)

        exec_summary_rows.append([
            _fmt(tname), t_best, _fv(t_fm.get("rmse")), _fv(t_fm.get("mae")),
            mape_str, _fv(t_fm.get("r2")), cv_mean, cv_std,
        ])

    critical_findings = []
    if drift_flagged_targets:
        critical_findings.append(
            f"{len(drift_flagged_targets)} target{'s' if len(drift_flagged_targets) != 1 else ''} showed metric drift between training and test phases.")
    if high_r2_count > 0:
        critical_findings.append(
            f"{high_r2_count} of {len(target_names)} targets achieved excellent accuracy (R2 > 0.95).")
    if not critical_findings:
        critical_findings.append(
            "All models trained and validated successfully with acceptable drift levels.")

    findings_html = "".join(f"<li>{f}</li>" for f in critical_findings[:3])

    html += f"""
<div id="executive-summary" class="section level2">
<h2>Executive Summary</h2>

<div id="exec-scope" class="section level3">
<h3>Scope &amp; Methodology</h3>
<p>The <strong>{project_name}</strong> {task_type} pipeline was executed using the Mu Sigma 3-phase modular approach.
Phase 1 performed data profiling, feature engineering, and train/test splitting across <strong>{n_rows} observations</strong> and <strong>{n_cols} features</strong>.
Phase 2 trained and validated <strong>{len(all_model_names)} candidate models</strong> across <strong>{len(target_names)} target variable{"s" if len(target_names) != 1 else ""}</strong> using 5-fold cross-validation.
Phase 3 executed final predictions on the held-out test set, generating <strong>{total_preds} predictions</strong>, and performed drift analysis and business insight extraction.</p>
</div>

<div id="exec-findings" class="section level3">
<h3>Key Findings</h3>
<p>{f'<strong>{dominant_model}</strong> emerged as the dominant performer, winning {dominant_wins} of {len(target_names)} targets.' if dominant_wins > 1 else f'Best models were selected per target based on composite scoring across 6 metrics.'}
The average R2 across all targets is <strong>{avg_r2_val:.3f}</strong>, indicating {'strong' if avg_r2_val > 0.8 else 'moderate' if avg_r2_val > 0.5 else 'baseline'} predictive power.
{f'{high_r2_count} target{"s" if high_r2_count != 1 else ""} achieved R2 > 0.95, demonstrating production-ready accuracy.' if high_r2_count > 0 else 'No targets achieved R2 > 0.95; additional feature engineering may be beneficial.'}</p>
</div>

<div id="exec-risk" class="section level3">
<h3>Risk &amp; Monitoring</h3>
<p>{f'{len(drift_flagged_targets)} target{"s" if len(drift_flagged_targets) != 1 else ""} showed metric drift exceeding 5% between Phase 2 (cross-validation) and Phase 3 (test set): {", ".join(drift_flagged_targets)}. These require close monitoring in production.' if drift_flagged_targets else 'No significant drift detected between training and test phases, indicating stable model generalization.'}
{f'{len(insights_raw)} business insights have been generated, highlighting key drivers and actionable recommendations for stakeholders.' if insights_raw else ''}</p>
</div>

<div id="exec-recommendation" class="section level3">
<h3>Strategic Recommendation</h3>
<p>The pipeline is ready for deployment. {'All targets demonstrate acceptable accuracy and drift levels.' if not drift_flagged_targets and high_r2_count > 0 else 'Targets with drift or low R2 should be prioritized for re-training or feature enhancement before production use.'}
Establish a monitoring framework to track prediction accuracy, data drift, and feature importance shifts over time.
Re-train models {'quarterly' if is_ts else 'when new data accumulates or performance degrades below thresholds'}.</p>
</div>

<div id="exec-perf" class="section level3">
<h3>Best Model per Target (All 6 Metrics)</h3>
{_table(exec_summary_headers, exec_summary_rows, extra_class="sortable")}
{_metric_footnote(["RMSE", "MAE", "MAPE", "R2", "CV", "ADF", "KPSS"])}
{('<p class="chart-conclusion"><em>' + llm_describe("executive_summary", {
     "project": project_name,
     "n_targets": len(target_names),
     "avg_r2": round(avg_r2_val, 3),
     "dominant_model": dominant_model,
     "problem_targets": len([t for t in target_names if p2_per_target.get(t, {}).get("low_confidence", False)])
 }) + '</em></p>') if exec_summary_rows else ''}
</div>
</div>
"""

    # ================================================================
    # SECTION 12: Appendix - Formulas & Glossary
    # ================================================================
    html += """
<div id="appendix-formulas" class="section level2">
<h2>Appendix: Formulas &amp; Glossary</h2>

<div id="metric-formulas" class="section level3">
<h3>Metric Definitions</h3>
<table>
<thead><tr><th>Metric</th><th>Formula</th><th>Interpretation</th></tr></thead>
<tbody>
<tr><td>RMSE</td><td>$$\\text{RMSE} = \\sqrt{\\frac{1}{n}\\sum_{i=1}^{n}(y_i - \\hat{y}_i)^2}$$</td><td>Root Mean Squared Error - penalizes large errors more heavily. Lower is better.</td></tr>
<tr><td>MAE</td><td>$$\\text{MAE} = \\frac{1}{n}\\sum_{i=1}^{n}|y_i - \\hat{y}_i|$$</td><td>Mean Absolute Error - average magnitude of errors. Lower is better.</td></tr>
<tr><td>MAPE</td><td>$$\\text{MAPE} = \\frac{100}{n}\\sum_{i=1}^{n}\\left|\\frac{y_i - \\hat{y}_i}{y_i}\\right|$$</td><td>Mean Absolute Percentage Error - scale-independent accuracy measure. Lower is better.</td></tr>
<tr><td>R2</td><td>$$R^2 = 1 - \\frac{\\sum(y_i - \\hat{y}_i)^2}{\\sum(y_i - \\bar{y})^2}$$</td><td>Coefficient of Determination - proportion of variance explained. Higher is better (max 1.0).</td></tr>
<tr><td>CV Mean</td><td>$$\\text{CV Mean} = \\frac{1}{k}\\sum_{j=1}^{k}s_j$$</td><td>Mean cross-validation score across k folds. Indicates average generalization performance.</td></tr>
<tr><td>CV Std</td><td>$$\\text{CV Std} = \\sqrt{\\frac{1}{k}\\sum_{j=1}^{k}(s_j - \\bar{s})^2}$$</td><td>Standard deviation of CV scores. Lower indicates more stable model performance across folds.</td></tr>
</tbody>
</table>
</div>

<div id="abbreviation-glossary" class="section level3">
<h3>Abbreviation Glossary</h3>
<table>
<thead><tr><th>Abbreviation</th><th>Full Form</th></tr></thead>
<tbody>
"""
    for abbr, full in sorted(ABBREVIATION_GLOSSARY.items()):
        html += f"<tr><td><strong>{abbr}</strong></td><td>{full}</td></tr>\n"
    html += """
</tbody>
</table>
</div>

"""
    # NOTE: Pipeline Validation (§12.3) is intentionally excluded from the report.
    # Self-check validation still runs internally (artifacts contain self_check_results.json)
    # but is not rendered in the client-facing report — it stays agent-side only.

    html += """
</div>
"""

    # ── Footer ──
    html += """
<!-- ===== FOOTER ===== -->
<div class="report-footer">
  <div class="footer-subtitle" id="footer-dynamic-text"></div>
</div>
<script>
(function() {
  var months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var now = new Date();
  var monthYear = months[now.getMonth()] + " " + now.getFullYear();
  document.getElementById("footer-dynamic-text").textContent = "Confidential \u2014 Mu Sigma, Inc. \u2014 " + monthYear;
})();
</script>
"""

    # ── Close content area ──
    html += """
</div><!-- /toc-content -->
</div><!-- /row -->
</div><!-- /main-container -->
"""

    html += toc_script + "\n"

    html += """
</body>
</html>"""

    # ── CR1: Remove em-dashes ──
    html = html.replace("\u2014", "-").replace("&mdash;", "-")

    # ── HTML validation (v5-final Step 13) ──
    validation_issues = _validate_html(html)
    if validation_issues:
        print(f"  HTML validation warnings ({len(validation_issues)}):")
        for issue in validation_issues:
            print(f"    - {issue}")

    # ── Write output ──
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build MuSigma HTML report from DS pipeline artifacts")
    parser.add_argument("--project_name", required=True)
    parser.add_argument("--task_type", required=True,
                        choices=["regression", "classification", "forecasting", "segmentation"])
    parser.add_argument("--phase1_dir", default=None)
    parser.add_argument("--phase2_dir", default=None)
    parser.add_argument("--phase3_dir", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--cleanup", action="store_true", default=True)
    parser.add_argument("--no-cleanup", action="store_false", dest="cleanup")
    parser.add_argument("--cleanup-delay", type=int, default=0)
    args = parser.parse_args()

    p1_dir = Path(
        args.phase1_dir) if args.phase1_dir else ARTIFACTS_DIR / "phase1"
    p2_dir = Path(
        args.phase2_dir) if args.phase2_dir else ARTIFACTS_DIR / "phase2"
    p3_dir = Path(
        args.phase3_dir) if args.phase3_dir else ARTIFACTS_DIR / "phase3"

    # Input validation
    if not (p1_dir / "phase1_results.json").exists():
        print(
            f"Error: Phase 1 results not found at {p1_dir}. Run Phase 1 first.")
        sys.exit(1)

    version = get_report_version(args.project_name)

    if args.output:
        output_path = Path(args.output)
    else:
        filename = f"{args.project_name}-ds-v{version}.html"
        output_path = REPORTS_DIR / filename

    print(f"\nBuilding MuSigma Report: {output_path.name}")
    print("=" * 50)
    print(f"  Project:   {args.project_name}")
    print(f"  Task type: {args.task_type}")
    print(f"  Version:   {version}")
    print(f"  Template:  {get_template_path()}")

    try:
        build_report(args.project_name, args.task_type,
                     p1_dir, p2_dir, p3_dir, output_path, version)
        size_kb = output_path.stat().st_size / 1024
        print(f"\n  Report ready: {output_path}  ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"\n  Error building report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Post-report cleanup
    if args.cleanup:
        print("\n  Cleaning up artifacts...")
        cleanup_artifacts(delay_seconds=args.cleanup_delay)
    else:
        print("\n  Artifacts retained (--no-cleanup).")
    print()


if __name__ == "__main__":
    main()
