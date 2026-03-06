#!/usr/bin/env python3
"""Strict, deterministic CSV data quality checker.

Outputs:
- Text report to stdout
- Optional standalone HTML report

Design goals:
- Deterministic thresholds
- No fancy dependencies beyond pandas/numpy
"""

from __future__ import annotations

import argparse
import html
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class Thresholds:
    fail_missing_pct: float = 50.0
    warn_missing_pct: float = 10.0


def _pct(n: int, denom: int) -> float:
    if denom <= 0:
        return 0.0
    return round((n / denom) * 100.0, 2)


def _safe_read_csv(path: Path) -> pd.DataFrame:
    # Keep defaults deterministic; don't infer thousands separators, etc.
    return pd.read_csv(path)


def _header_issues(columns: List[str]) -> Dict[str, object]:
    raw = list(columns)
    normalized = [c.strip() for c in raw]
    dup_raw = sorted({c for c in raw if raw.count(c) > 1})
    dup_norm = sorted({c for c in normalized if normalized.count(c) > 1})
    whitespace = [c for c in raw if c != c.strip()]
    empty_names = [c for c in raw if c.strip() == ""]

    return {
        "duplicate_column_names": dup_raw,
        "duplicate_column_names_after_strip": dup_norm,
        "columns_with_leading_trailing_whitespace": whitespace,
        "empty_column_names": empty_names,
    }


def _empty_columns(df: pd.DataFrame) -> List[str]:
    empties = []
    for c in df.columns:
        s = df[c]
        if s.isna().all():
            empties.append(c)
            continue
        if s.dtype == object:
            # Treat empty strings as missing-like
            if s.astype(str).str.strip().replace("nan", "").eq("").all():
                empties.append(c)
    return empties


def _mixed_type_signals(df: pd.DataFrame, sample_size: int = 2000) -> List[Dict[str, object]]:
    """Heuristic, but deterministic: checks object columns for numeric-like mixtures."""
    out = []
    n = len(df)
    for c in df.columns:
        s = df[c]
        if s.dtype != object:
            continue
        s2 = s.dropna().astype(str).str.strip()
        if s2.empty:
            continue
        s2 = s2.head(sample_size)

        # Numeric-like?
        numeric_like = s2.str.fullmatch(r"[-+]?\d+(\.\d+)?")
        pct_numeric_like = float(numeric_like.mean() * 100.0)

        # ISO date-like (very simple)
        date_like = s2.str.fullmatch(r"\d{4}-\d{2}-\d{2}")
        pct_date_like = float(date_like.mean() * 100.0)

        # If a column is partially numeric-like or date-like, flag as mixed.
        if 0.0 < pct_numeric_like < 95.0:
            out.append(
                {
                    "column": c,
                    "signal": "mixed_numeric_like_strings",
                    "pct_numeric_like": round(pct_numeric_like, 2),
                    "examples_non_numeric": s2[~numeric_like].head(8).tolist(),
                }
            )
        if 0.0 < pct_date_like < 95.0:
            out.append(
                {
                    "column": c,
                    "signal": "mixed_date_like_strings",
                    "pct_date_like": round(pct_date_like, 2),
                    "examples_non_date": s2[~date_like].head(8).tolist(),
                }
            )
    return out


def _numeric_outliers(df: pd.DataFrame) -> List[Dict[str, object]]:
    out = []
    num = df.select_dtypes(include=[np.number])
    for c in num.columns:
        s = num[c].dropna()
        if len(s) < 8:
            continue
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        if iqr == 0 or math.isnan(iqr):
            continue
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        mask = (s < low) | (s > high)
        cnt = int(mask.sum())
        if cnt > 0:
            out.append(
                {
                    "column": c,
                    "outlier_count": cnt,
                    "outlier_pct": _pct(cnt, len(s)),
                    "low": low,
                    "high": high,
                    "examples": s[mask].head(10).tolist(),
                }
            )
    return out


def _key_uniqueness(df: pd.DataFrame, key_cols: List[str]) -> Dict[str, object]:
    missing_cols = [c for c in key_cols if c not in df.columns]
    if missing_cols:
        return {
            "provided": key_cols,
            "status": "ERROR",
            "error": f"Key columns not found: {missing_cols}",
        }

    key_df = df[key_cols]
    null_in_key = key_df.isna().any(axis=1).sum()
    dup_keys = key_df.duplicated().sum()

    return {
        "provided": key_cols,
        "status": "OK",
        "rows_with_null_in_key": int(null_in_key),
        "duplicate_key_rows": int(dup_keys),
    }


def _status(summary: Dict[str, object], thresholds: Thresholds) -> Tuple[str, List[str], List[str]]:
    fails = []
    warns = []

    header = summary["header"]
    empties = summary["empty_columns"]
    missing_tbl = summary["missing_by_column"]

    if header["duplicate_column_names"] or header["duplicate_column_names_after_strip"]:
        fails.append("Duplicate column names")
    if header["empty_column_names"]:
        fails.append("Empty column name(s)")
    if empties:
        fails.append("Completely empty column(s)")

    # Missingness severity
    for col, metrics in missing_tbl.items():
        pct = metrics["missing_pct"]
        if pct > thresholds.fail_missing_pct:
            fails.append(f"High missingness >{thresholds.fail_missing_pct}% in column '{col}' ({pct}%)")
        elif pct >= thresholds.warn_missing_pct:
            warns.append(f"Missingness {thresholds.warn_missing_pct}-{thresholds.fail_missing_pct}% in column '{col}' ({pct}%)")

    if summary["duplicate_rows"]["count"] > 0:
        warns.append("Duplicate rows present")

    if summary["mixed_type_signals"]:
        warns.append("Mixed-type signals detected")

    if summary["numeric_outliers"]:
        warns.append("Numeric outliers detected (IQR rule)")

    key = summary.get("key_uniqueness")
    if key and key.get("status") == "OK":
        if key.get("duplicate_key_rows", 0) > 0:
            fails.append("Key uniqueness violated")
        if key.get("rows_with_null_in_key", 0) > 0:
            fails.append("Nulls present in key columns")
    elif key and key.get("status") == "ERROR":
        fails.append("Invalid key columns provided")

    if fails:
        return "FAIL", fails, warns
    if warns:
        return "WARNING", fails, warns
    return "PASS", fails, warns


def build_summary(df: pd.DataFrame, key_cols: Optional[List[str]], thresholds: Thresholds) -> Dict[str, object]:
    rows, cols = df.shape

    header = _header_issues(list(df.columns))

    dtypes = {c: str(df[c].dtype) for c in df.columns}

    missing = {}
    for c in df.columns:
        miss_cnt = int(df[c].isna().sum())
        missing[c] = {
            "missing_count": miss_cnt,
            "missing_pct": _pct(miss_cnt, rows),
        }

    dup_rows = int(df.duplicated().sum())

    empty_cols = _empty_columns(df)
    mixed = _mixed_type_signals(df)
    outliers = _numeric_outliers(df)

    summary: Dict[str, object] = {
        "dataset": {
            "rows": int(rows),
            "columns": int(cols),
            "column_names": list(df.columns),
        },
        "dtypes": dtypes,
        "header": header,
        "missing_by_column": missing,
        "duplicate_rows": {
            "count": dup_rows,
            "pct": _pct(dup_rows, rows),
        },
        "empty_columns": empty_cols,
        "mixed_type_signals": mixed,
        "numeric_outliers": outliers,
    }

    if key_cols:
        summary["key_uniqueness"] = _key_uniqueness(df, key_cols)

    status, fails, warns = _status(summary, thresholds)
    summary["overall_status"] = status
    summary["fail_reasons"] = fails
    summary["warning_reasons"] = warns

    return summary


def summary_to_text(summary: Dict[str, object]) -> str:
    lines = []
    status = summary["overall_status"]

    lines.append("DATA QUALITY REPORT")
    lines.append("=" * 80)
    lines.append(f"Overall status: {status}")

    if summary.get("fail_reasons"):
        lines.append("\nCRITICAL ISSUES (FAIL)")
        for r in summary["fail_reasons"]:
            lines.append(f"- {r}")

    if summary.get("warning_reasons"):
        lines.append("\nWARNINGS")
        for r in summary["warning_reasons"]:
            lines.append(f"- {r}")

    ds = summary["dataset"]
    lines.append("\nDATASET SUMMARY")
    lines.append(f"- Rows: {ds['rows']}")
    lines.append(f"- Columns: {ds['columns']}")
    lines.append(f"- Column names: {', '.join(ds['column_names'])}")

    lines.append("\nSCHEMA (INFERRED DTYPES)")
    for c, t in summary["dtypes"].items():
        lines.append(f"- {c}: {t}")

    lines.append("\nMISSING VALUES")
    # Sort by missing_count desc
    miss_items = sorted(summary["missing_by_column"].items(), key=lambda kv: kv[1]["missing_count"], reverse=True)
    for c, m in miss_items:
        if m["missing_count"] > 0:
            lines.append(f"- {c}: {m['missing_count']} ({m['missing_pct']}%)")

    if all(m["missing_count"] == 0 for _, m in miss_items):
        lines.append("- None")

    lines.append("\nDUPLICATES")
    lines.append(f"- Duplicate rows: {summary['duplicate_rows']['count']} ({summary['duplicate_rows']['pct']}%)")

    lines.append("\nHEADER CONSISTENCY")
    header = summary["header"]
    lines.append(f"- Duplicate column names: {header['duplicate_column_names']}")
    lines.append(f"- Duplicate after strip: {header['duplicate_column_names_after_strip']}")
    lines.append(f"- Columns with whitespace: {header['columns_with_leading_trailing_whitespace']}")
    lines.append(f"- Empty column names: {header['empty_column_names']}")

    lines.append("\nEMPTY COLUMNS")
    lines.append(f"- Empty columns: {summary['empty_columns']}")

    lines.append("\nMIXED/INCONSISTENT TYPE SIGNALS")
    if summary["mixed_type_signals"]:
        for s in summary["mixed_type_signals"]:
            col = s["column"]
            if s["signal"] == "mixed_numeric_like_strings":
                lines.append(f"- {col}: mixed numeric-like strings ({s['pct_numeric_like']}% numeric-like). Examples non-numeric: {s['examples_non_numeric']}")
            else:
                lines.append(f"- {col}: mixed date-like strings ({s['pct_date_like']}% date-like). Examples non-date: {s['examples_non_date']}")
    else:
        lines.append("- None")

    lines.append("\nABNORMAL NUMERIC VALUES (IQR OUTLIERS)")
    if summary["numeric_outliers"]:
        for o in summary["numeric_outliers"]:
            lines.append(
                f"- {o['column']}: {o['outlier_count']} outliers ({o['outlier_pct']}%), bounds=[{o['low']:.6g}, {o['high']:.6g}], examples={o['examples']}"
            )
    else:
        lines.append("- None")

    if "key_uniqueness" in summary:
        k = summary["key_uniqueness"]
        lines.append("\nKEY UNIQUENESS")
        if k.get("status") == "OK":
            lines.append(f"- Key columns: {k['provided']}")
            lines.append(f"- Rows with NULL in key: {k['rows_with_null_in_key']}")
            lines.append(f"- Duplicate key rows: {k['duplicate_key_rows']}")
        else:
            lines.append(f"- ERROR: {k.get('error')}")

    lines.append("\nSUGGESTED FIXES (DETERMINISTIC)")
    fixes = []
    if summary["header"]["columns_with_leading_trailing_whitespace"]:
        fixes.append("Strip whitespace from header names (e.g., rename columns with leading/trailing spaces).")
    if summary["header"]["duplicate_column_names"] or summary["header"]["duplicate_column_names_after_strip"]:
        fixes.append("Rename duplicate columns to unique names; avoid collisions after trimming whitespace.")
    if summary["empty_columns"]:
        fixes.append("Drop empty columns or backfill them from source; empty columns should not be shipped.")
    if summary["duplicate_rows"]["count"] > 0:
        fixes.append("Deduplicate rows: define a key (or full-row hash) and keep the latest/first deterministically.")
    if summary["mixed_type_signals"]:
        fixes.append("Standardize types: coerce numeric-like columns to numeric; treat invalid strings as NULL; document parsing rules.")
    if summary["numeric_outliers"]:
        fixes.append("Validate outliers against domain rules; cap/winsorize only if business-approved; otherwise correct source values.")

    # Missingness fixes
    high_missing_cols = [c for c, m in summary["missing_by_column"].items() if m["missing_pct"] > 10.0]
    if high_missing_cols:
        fixes.append(f"Investigate missingness in columns: {high_missing_cols}. Consider making them nullable explicitly or fixing upstream extraction.")

    if "key_uniqueness" in summary and summary["key_uniqueness"].get("status") == "OK":
        k = summary["key_uniqueness"]
        if k.get("rows_with_null_in_key", 0) > 0 or k.get("duplicate_key_rows", 0) > 0:
            fixes.append("Enforce key constraints upstream (NOT NULL + UNIQUE) and reject/repair violating rows.")

    if not fixes:
        fixes.append("No fixes suggested; dataset passed the configured checks.")

    for f in fixes:
        lines.append(f"- {f}")

    return "\n".join(lines) + "\n"



def summary_to_html(summary: Dict[str, object]) -> str:
    """Clean, report-style, self-contained HTML (print-friendly)."""

    def esc(x):
        return html.escape(str(x))

    ds = summary["dataset"]
    status = summary["overall_status"]
    fail_reasons = summary.get("fail_reasons", [])
    warn_reasons = summary.get("warning_reasons", [])

    # Build column overview table
    miss = summary["missing_by_column"]
    dtype = summary["dtypes"]
    cols = ds["column_names"]

    col_rows = []
    for c in cols:
        m = miss.get(c, {"missing_count": 0, "missing_pct": 0.0})
        col_rows.append(
            f"<tr><td class='mono'>{esc(c)}</td><td class='mono'>{esc(dtype.get(c))}</td><td class='num'>{esc(m['missing_count'])}</td><td class='num'>{esc(m['missing_pct'])}%</td></tr>"
        )

    header = summary["header"]

    # Mixed type table
    mixed = summary.get("mixed_type_signals", [])
    if mixed:
        mixed_rows = []
        for s in mixed:
            pct = s.get("pct_numeric_like", s.get("pct_date_like", ""))
            examples = s.get("examples_non_numeric", s.get("examples_non_date", []))
            mixed_rows.append(
                f"<tr><td class='mono'>{esc(s.get('column'))}</td><td>{esc(s.get('signal'))}</td><td class='num'>{esc(pct)}</td><td><code>{esc(json.dumps(examples)[:600])}</code></td></tr>"
            )
        mixed_block = f"""
        <table>
          <thead><tr><th>Column</th><th>Signal</th><th class='num'>%</th><th>Examples</th></tr></thead>
          <tbody>{''.join(mixed_rows)}</tbody>
        </table>
        """
    else:
        mixed_block = "<p class='muted'>None.</p>"

    # Outliers table
    outliers = summary.get("numeric_outliers", [])
    if outliers:
        out_rows = []
        for o in outliers:
            out_rows.append(
                "<tr>"
                f"<td class='mono'>{esc(o['column'])}</td>"
                f"<td class='num'>{esc(o['outlier_count'])}</td>"
                f"<td class='num'>{esc(o['outlier_pct'])}%</td>"
                f"<td class='num'>{esc(o['low'])}</td>"
                f"<td class='num'>{esc(o['high'])}</td>"
                f"<td><code>{esc(json.dumps(o['examples'])[:600])}</code></td>"
                "</tr>"
            )
        outlier_block = f"""
        <table>
          <thead><tr><th>Column</th><th class='num'>Outliers</th><th class='num'>Outlier %</th><th class='num'>Low</th><th class='num'>High</th><th>Examples</th></tr></thead>
          <tbody>{''.join(out_rows)}</tbody>
        </table>
        """
    else:
        outlier_block = "<p class='muted'>None.</p>"

    def bullet_list(items):
        if not items:
            return "<p class='muted'>None.</p>"
        return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"

    # Suggested fixes (deterministic)
    fixes = []
    if header["columns_with_leading_trailing_whitespace"]:
        fixes.append("Strip whitespace from header names.")
    if header["duplicate_column_names"] or header["duplicate_column_names_after_strip"]:
        fixes.append("Rename duplicate columns to unique names.")
    if summary.get("empty_columns"):
        fixes.append("Drop empty columns or backfill them from source.")
    if summary["duplicate_rows"]["count"] > 0:
        fixes.append("Deduplicate rows deterministically (define a key or full-row hash).")
    if mixed:
        fixes.append("Standardize types and document coercion rules.")
    if outliers:
        fixes.append("Validate outliers against business rules; correct upstream values if invalid.")

    high_missing_cols = [c for c, m in miss.items() if m.get("missing_pct", 0) > 10.0]
    if high_missing_cols:
        fixes.append(f"Investigate missingness in columns: {high_missing_cols}.")

    if not fixes:
        fixes.append("No fixes suggested; dataset passed the configured checks.")

    status_class = status

    doc = f"""<!doctype html>
<html>
<head>
  <meta charset='utf-8'/>
  <meta name='viewport' content='width=device-width, initial-scale=1'/>
  <title>CSV Data Quality Report</title>
  <style>
    :root {{
      --text: #111827;
      --muted: #6b7280;
      --border: #e5e7eb;
      --bg: #ffffff;
      --pass: #065f46;
      --warn: #92400e;
      --fail: #991b1b;
      --passbg: #ecfdf5;
      --warnbg: #fffbeb;
      --failbg: #fef2f2;
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
    }}

    html, body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
    .page {{ max-width: 980px; margin: 0 auto; padding: 28px 18px 56px; }}

    h1 {{ font-size: 26px; margin: 0 0 6px; }}
    h2 {{ font-size: 16px; margin: 22px 0 10px; padding-top: 8px; border-top: 1px solid var(--border); }}
    p {{ margin: 8px 0; }}
    .muted {{ color: var(--muted); }}
    .mono {{ font-family: var(--mono); }}
    code {{ font-family: var(--mono); font-size: 12px; }}

    .banner {{ border: 1px solid var(--border); border-left-width: 6px; border-radius: 10px; padding: 12px 14px; margin-top: 14px; }}
    .banner.PASS {{ border-left-color: var(--pass); background: var(--passbg); }}
    .banner.WARNING {{ border-left-color: var(--warn); background: var(--warnbg); }}
    .banner.FAIL {{ border-left-color: var(--fail); background: var(--failbg); }}
    .banner .k {{ font-weight: 800; }}

    .kpis {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }}
    .kpi {{ border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; }}
    .kpi .k {{ font-size: 18px; font-weight: 800; }}
    .kpi .v {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}

    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
    th, td {{ border: 1px solid var(--border); padding: 8px 10px; font-size: 13px; vertical-align: top; }}
    th {{ background: #f9fafb; text-align: left; }}
    td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}

    pre {{ background: #f9fafb; border: 1px solid var(--border); border-radius: 10px; padding: 12px; overflow-x: auto; }}

    @media print {{
      .page {{ max-width: none; }}
      a {{ color: inherit; text-decoration: none; }}
    }}
    @media (max-width: 900px) {{
      .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <div class='page'>
    <h1>CSV Data Quality Report</h1>
    <p class='muted'>Deterministic checks: header consistency, missing values, duplicates, empty columns, mixed-type signals, numeric outliers (IQR).</p>

    <div class='banner {esc(status_class)}'>
      <div class='k'>Overall status: {esc(status)}</div>
      <div class='muted'>Fails: {len(fail_reasons)} · Warnings: {len(warn_reasons)}</div>
    </div>

    <div class='kpis'>
      <div class='kpi'><div class='k'>{ds['rows']}</div><div class='v'>Rows</div></div>
      <div class='kpi'><div class='k'>{ds['columns']}</div><div class='v'>Columns</div></div>
      <div class='kpi'><div class='k'>{esc(summary['duplicate_rows']['count'])}</div><div class='v'>Duplicate rows</div></div>
      <div class='kpi'><div class='k'>{len(summary.get('empty_columns', []))}</div><div class='v'>Empty columns</div></div>
    </div>

    <h2>1) Critical issues (FAIL)</h2>
    {bullet_list(fail_reasons)}

    <h2>2) Warnings</h2>
    {bullet_list(warn_reasons)}

    <h2>3) Dataset summary</h2>
    <ul>
      <li><b>Rows</b>: {ds['rows']}</li>
      <li><b>Columns</b>: {ds['columns']}</li>
      <li><b>Column names</b>: <span class='mono'>{esc(', '.join(cols))}</span></li>
    </ul>

    <h2>4) Column overview (dtype + missingness)</h2>
    <table>
      <thead>
        <tr><th>Column</th><th>Dtype</th><th class='num'>Missing</th><th class='num'>Missing %</th></tr>
      </thead>
      <tbody>
        {''.join(col_rows)}
      </tbody>
    </table>

    <h2>5) Duplicates</h2>
    <ul>
      <li><b>Duplicate rows</b>: {esc(summary['duplicate_rows']['count'])} ({esc(summary['duplicate_rows']['pct'])}%)</li>
    </ul>

    <h2>6) Header consistency</h2>
    <ul>
      <li><b>Duplicate column names</b>: <code>{esc(header['duplicate_column_names'])}</code></li>
      <li><b>Duplicate after strip</b>: <code>{esc(header['duplicate_column_names_after_strip'])}</code></li>
      <li><b>Columns with whitespace</b>: <code>{esc(header['columns_with_leading_trailing_whitespace'])}</code></li>
      <li><b>Empty column names</b>: <code>{esc(header['empty_column_names'])}</code></li>
    </ul>

    <h2>7) Empty columns</h2>
    <p class='mono'>{esc(summary.get('empty_columns', []))}</p>

    <h2>8) Mixed / inconsistent type signals</h2>
    {mixed_block}

    <h2>9) Abnormal numeric values (IQR outliers)</h2>
    {outlier_block}

    <h2>10) Suggested fixes (deterministic)</h2>
    {bullet_list(fixes)}

  </div>
</body>
</html>
"""

    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to input CSV")
    ap.add_argument("--output-html", default=None, help="Optional: write standalone HTML report")
    ap.add_argument("--key-cols", default=None, help="Optional: comma-separated key columns for uniqueness checks")
    args = ap.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    df = _safe_read_csv(in_path)

    key_cols = None
    if args.key_cols:
        key_cols = [c.strip() for c in args.key_cols.split(",") if c.strip()]

    thresholds = Thresholds()
    summary = build_summary(df, key_cols=key_cols, thresholds=thresholds)

    print(summary_to_text(summary))

    # Always generate HTML report
    if args.output_html:
        html_path = Path(args.output_html).expanduser().resolve()
    else:
        # Default: write HTML alongside input file
        html_path = in_path.with_suffix(".dq_report.html")
    html_path.write_text(summary_to_html(summary), encoding="utf-8")
    print(f"\nHTML report written to: {html_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
