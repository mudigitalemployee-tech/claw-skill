#!/usr/bin/env python3
"""
Test Report Generator — Produces an HTML report from analysis + test results JSON.

Usage:
    python3 scripts/generate_report.py --analysis analysis.json --results results.json [--sonar sonar.json] [--output report.html]
"""

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text())


def pct(num: int, denom: int) -> str:
    if denom == 0:
        return "N/A"
    return f"{(num / denom) * 100:.1f}%"


def status_badge(status: str) -> str:
    colors = {"PASSED": "#22c55e", "FAILED": "#ef4444", "WARNING": "#f59e0b", "INFO": "#3b82f6"}
    color = colors.get(status, "#6b7280")
    return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:4px;font-size:0.85em;font-weight:600">{status}</span>'


def generate_report(analysis: dict, results: dict, sonar: dict | None = None) -> str:
    """Generate full HTML test report."""
    project_name = Path(analysis["project_path"]).name
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lang = analysis.get("language", "unknown")
    framework = analysis.get("framework") or "—"
    test_fw = analysis.get("test_framework", "unknown")

    total = results.get("total", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    skipped = results.get("skipped", 0)
    errors = results.get("errors", 0)
    duration = results.get("duration_seconds", 0)
    overall = "PASSED" if failed == 0 and errors == 0 else "FAILED"

    # Source file summary
    top_files = sorted(analysis.get("source_files", []), key=lambda f: len(f.get("functions", [])), reverse=True)[:20]

    report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AutoTest Report — {html.escape(project_name)}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
:root {{ --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #94a3b8; --accent: #3b82f6; --green: #22c55e; --red: #ef4444; --yellow: #f59e0b; --border: #334155; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
h2 {{ font-size: 1.3rem; margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }}
h3 {{ font-size: 1.05rem; margin: 1.2rem 0 0.5rem; color: var(--accent); }}
.subtitle {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 2rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1.2rem; }}
.card .label {{ font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
.card .value {{ font-size: 1.8rem; font-weight: 700; margin-top: 0.3rem; }}
.card .value.green {{ color: var(--green); }}
.card .value.red {{ color: var(--red); }}
.card .value.yellow {{ color: var(--yellow); }}
.card .value.blue {{ color: var(--accent); }}
table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }}
th, td {{ padding: 0.6rem 0.8rem; text-align: left; border-bottom: 1px solid var(--border); }}
th {{ color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }}
tr:hover {{ background: rgba(59,130,246,0.05); }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }}
.tag-pass {{ background: rgba(34,197,94,0.15); color: var(--green); }}
.tag-fail {{ background: rgba(239,68,68,0.15); color: var(--red); }}
.tag-skip {{ background: rgba(245,158,11,0.15); color: var(--yellow); }}
pre {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; overflow-x: auto; font-size: 0.85rem; color: var(--muted); max-height: 400px; overflow-y: auto; }}
.failure-block {{ background: rgba(239,68,68,0.08); border-left: 3px solid var(--red); padding: 0.8rem 1rem; margin: 0.5rem 0; border-radius: 0 6px 6px 0; }}
.failure-block .test-name {{ font-weight: 600; color: var(--red); }}
.failure-block .test-msg {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.3rem; }}
.chart-container {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin: 1rem 0; }}
footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.8rem; text-align: center; }}
</style>
</head>
<body>
<div class="container">

<h1>🧪 AutoTest Report — {html.escape(project_name)}</h1>
<p class="subtitle">Generated {now} &nbsp;|&nbsp; {status_badge(overall)}</p>

<h2>📋 Project Overview</h2>
<div class="grid">
  <div class="card"><div class="label">Language</div><div class="value blue">{html.escape(lang.title())}</div></div>
  <div class="card"><div class="label">Framework</div><div class="value">{html.escape(framework)}</div></div>
  <div class="card"><div class="label">Test Framework</div><div class="value">{html.escape(test_fw)}</div></div>
  <div class="card"><div class="label">Source Files</div><div class="value">{analysis.get('total_source_files', 0)}</div></div>
  <div class="card"><div class="label">Total Lines</div><div class="value">{analysis.get('total_lines', 0):,}</div></div>
  <div class="card"><div class="label">Functions</div><div class="value">{analysis.get('total_functions', 0)}</div></div>
  <div class="card"><div class="label">Classes</div><div class="value">{analysis.get('total_classes', 0)}</div></div>
  <div class="card"><div class="label">Existing Tests</div><div class="value">{len(analysis.get('existing_tests', []))}</div></div>
</div>

<h2>🧪 Test Execution Summary</h2>
<div class="grid">
  <div class="card"><div class="label">Total Tests</div><div class="value blue">{total}</div></div>
  <div class="card"><div class="label">Passed</div><div class="value green">{passed}</div></div>
  <div class="card"><div class="label">Failed</div><div class="value red">{failed}</div></div>
  <div class="card"><div class="label">Skipped</div><div class="value yellow">{skipped}</div></div>
  <div class="card"><div class="label">Errors</div><div class="value red">{errors}</div></div>
  <div class="card"><div class="label">Pass Rate</div><div class="value {'green' if failed == 0 else 'red'}">{pct(passed, total)}</div></div>
  <div class="card"><div class="label">Duration</div><div class="value">{duration:.1f}s</div></div>
</div>

<div class="chart-container">
  <div id="results-chart" style="height:320px"></div>
</div>
<script>
Plotly.newPlot('results-chart', [{{
  values: [{passed}, {failed}, {skipped}, {errors}],
  labels: ['Passed', 'Failed', 'Skipped', 'Errors'],
  type: 'pie',
  hole: 0.5,
  marker: {{ colors: ['#22c55e', '#ef4444', '#f59e0b', '#6b7280'] }},
  textinfo: 'label+value',
  textfont: {{ color: '#e2e8f0', size: 13 }}
}}], {{
  paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
  font: {{ color: '#94a3b8' }},
  margin: {{ t: 30, b: 30, l: 30, r: 30 }},
  title: {{ text: 'Test Results Distribution', font: {{ size: 15, color: '#e2e8f0' }} }},
  showlegend: true, legend: {{ font: {{ color: '#94a3b8' }} }}
}}, {{ responsive: true }});
</script>
"""

    # Failures section
    failures = results.get("failures", [])
    if failures:
        report += "\n<h2>❌ Failed Tests — Detailed Analysis</h2>\n"
        for f in failures:
            test_name = html.escape(f.get("test", "Unknown"))
            msg = html.escape(f.get("message", "No details captured"))
            report += f"""<div class="failure-block">
  <div class="test-name">{test_name}</div>
  <div class="test-msg">{msg}</div>
</div>\n"""

    # Source files table
    if top_files:
        report += "\n<h2>📂 Key Source Files</h2>\n<table><tr><th>File</th><th>Language</th><th>Lines</th><th>Functions</th><th>Classes</th></tr>\n"
        for sf in top_files:
            fns = len(sf.get("functions", []))
            cls = len(sf.get("classes", []))
            report += f'<tr><td>{html.escape(sf["path"])}</td><td>{html.escape(sf["language"])}</td><td>{sf["lines"]}</td><td>{fns}</td><td>{cls}</td></tr>\n'
        report += "</table>\n"

    # SonarQube section
    if sonar:
        report += "\n<h2>🔍 SonarQube Code Quality Analysis</h2>\n"
        report += '<div class="grid">\n'
        metrics = [
            ("Bugs", sonar.get("bugs", "—"), "red" if sonar.get("bugs", 0) > 0 else "green"),
            ("Code Smells", sonar.get("code_smells", "—"), "yellow" if sonar.get("code_smells", 0) > 10 else "green"),
            ("Vulnerabilities", sonar.get("vulnerabilities", "—"), "red" if sonar.get("vulnerabilities", 0) > 0 else "green"),
            ("Coverage", sonar.get("coverage", "—"), "green"),
            ("Duplications", sonar.get("duplicated_lines_density", "—"), "yellow"),
            ("Maintainability", sonar.get("sqale_rating", "—"), "blue"),
            ("Reliability", sonar.get("reliability_rating", "—"), "blue"),
            ("Security", sonar.get("security_rating", "—"), "blue"),
            ("Tech Debt", sonar.get("sqale_debt_ratio", "—"), "yellow"),
        ]
        for label, value, color in metrics:
            report += f'  <div class="card"><div class="label">{label}</div><div class="value {color}">{value}</div></div>\n'
        report += "</div>\n"

    # Execution log
    stdout = results.get("stdout", "").strip()
    if stdout:
        report += f"\n<h2>📜 Execution Log</h2>\n<pre>{html.escape(stdout[-3000:])}</pre>\n"

    # Footer
    report += f"""
<footer>
  AutoTest Engineer Report &nbsp;|&nbsp; Generated {now} &nbsp;|&nbsp; Command: <code>{html.escape(results.get('command', '—'))}</code>
</footer>

</div>
</body>
</html>"""

    return report


def main():
    parser = argparse.ArgumentParser(description="Generate HTML test report")
    parser.add_argument("--analysis", "-a", required=True, help="Analysis JSON file")
    parser.add_argument("--results", "-r", required=True, help="Test results JSON file")
    parser.add_argument("--sonar", "-s", help="SonarQube results JSON file (optional)")
    parser.add_argument("--output", "-o", default="autotest-report.html", help="Output HTML file")
    args = parser.parse_args()

    analysis = load_json(args.analysis)
    results = load_json(args.results)
    sonar = load_json(args.sonar) if args.sonar else None

    report_html = generate_report(analysis, results, sonar)
    Path(args.output).write_text(report_html)
    print(f"Report generated: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
