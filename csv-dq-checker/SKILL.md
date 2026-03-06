---
name: csv-dq-checker
description: "Strict, deterministic data quality checking for CSV datasets. Use when a user uploads a .csv (or provides a local path) and asks for profiling/validation (row/column counts, schema inference, null and duplicate detection, empty columns, header consistency, mixed/inconsistent types, abnormal numeric values). Generates a structured PASS/WARNING/FAIL report and always outputs a standalone HTML report."
---

# CSV Data Quality Checker

Use this skill to produce a **strict, repeatable** data quality report for a CSV.

## Workflow

### 1) Acquire the CSV

- If the CSV is uploaded: use the uploaded file.
- If the user provides a local path: read it **only if** local filesystem tools are available; otherwise ask for upload/paste.

### 2) Run the deterministic checker

Run the bundled script:

- Script: `scripts/csv_dq_report.py`
- Inputs:
  - `--input <path-to-csv>` (required)
  - `--output-html <path>` to control where the HTML report is written (optional — defaults to `<input>.dq_report.html` alongside the CSV)
  - `--key-cols col1,col2` to check key uniqueness (optional)

**The script always generates an HTML report.** If `--output-html` is not specified, the report is written next to the input CSV as `<filename>.dq_report.html`.

### 3) Return the report

Return a clear report with:

- **Dataset summary** (rows, columns, column list, inferred dtypes)
- **Critical issues first**
- **Validation results** (nulls, duplicates, empty cols, header problems, mixed types, numeric outliers)
- **Suggested fixes** (specific, minimal, deterministic)
- **Overall status**: PASS / WARNING / FAIL
- **HTML report path** — always tell the user where the HTML file was saved

## Deterministic rules (do not improvise)

Use these severities (unless the user supplies different thresholds):

- **FAIL** if any of:
  - duplicate column names
  - any completely empty column
  - any key uniqueness violation when `--key-cols` provided
  - any column has >50% missing values
- **WARNING** if any of:
  - duplicate rows > 0
  - any column has 10–50% missing values
  - mixed-type signals detected (e.g., numeric-like strings mixed with non-numeric)
  - numeric outliers detected (IQR rule) in numeric columns
- **PASS** otherwise.

## Assets

| Asset | Path | Description |
|-------|------|-------------|
| DQ checker script | `scripts/csv_dq_report.py` | Main Python script — runs all deterministic checks and generates text + HTML reports |

### Dependencies

- **Python 3.8+**
- **pandas** — CSV parsing, dtype inference, duplicate detection
- **numpy** — numeric outlier detection (IQR)

No other dependencies required. Standard library modules used: `argparse`, `html`, `json`, `math`, `dataclasses`, `pathlib`, `typing`.

## References

- [Pandas DataFrame documentation](https://pandas.pydata.org/docs/reference/frame.html) — core data structure used for all checks
- [IQR outlier detection method](https://en.wikipedia.org/wiki/Interquartile_range#Outliers) — the statistical method used for numeric outlier flagging (1.5×IQR rule)
- [Data Quality Dimensions (DAMA)](https://www.dama.org/cpages/body-of-knowledge) — industry framework for data quality dimensions (completeness, uniqueness, consistency, validity)
- [Great Expectations](https://greatexpectations.io/) — open-source DQ framework (inspiration for threshold-based validation approach)

## Notes

- Be strict and deterministic.
- Don't ask the user extra questions unless required to access the file or a key column list is necessary for a uniqueness check.
- **Always provide the HTML report** — no need for the user to request it separately.
