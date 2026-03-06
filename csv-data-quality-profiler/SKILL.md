---
name: csv-data-quality-profiler
description: "Strict, deterministic data quality profiling for CSV datasets. Use when a user uploads a .csv (or provides a local path) and asks for profiling/validation (row/column counts, schema inference, null and duplicate detection, empty columns, header consistency, mixed/inconsistent types, abnormal numeric values). Generates a structured PASS/WARNING/FAIL report and always outputs a standalone HTML report."
---

# CSV Data Quality Profiler

Produces a **strict, repeatable** data quality profile for any CSV dataset.

## Workflow

### 1) Acquire the CSV

- If the CSV is uploaded: use the uploaded file.
- If the user provides a local path: read it **only if** local filesystem tools are available; otherwise ask for upload/paste.

### 2) Run the profiler

**Always use the smart runner:**

```bash
bash <skill_dir>/scripts/run.sh --input <path-to-csv> [--output-html <path>] [--key-cols col1,col2]
```

**What `run.sh` does:**
1. Finds Python 3.8+ on the system
2. Checks if `pandas` and `numpy` are importable
3. If packages are missing → runs `setup.sh` to auto-install them
4. Runs `csv_dq_report.py` for full analysis
5. If Python can't be found or deps fail to install → exits with clear instructions

**Always call `run.sh`** — never call `csv_dq_report.py` directly.

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--input <path>` | Yes | Path to the input CSV file |
| `--output-html <path>` | No | Where to write HTML report. Default: `<input>.dq_report.html` alongside the CSV |
| `--key-cols col1,col2` | No | Comma-separated key columns for uniqueness check |

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
  - numeric outliers detected via IQR rule in numeric columns
- **PASS** otherwise.

## Assets

| Asset | Path | Description |
|-------|------|-------------|
| **Smart runner** | `scripts/run.sh` | Entry point — finds Python, installs deps if needed, runs profiler |
| **Setup script** | `scripts/setup.sh` | Finds/installs Python3, pip, pandas, numpy. Called by `run.sh` automatically |
| **Python profiler** | `scripts/csv_dq_report.py` | Full DQ profiler — all checks, text + HTML output |
| **Valid sample CSV** | `assets/employees_valid.csv` | Clean test dataset — should produce PASS |
| **Messy sample CSV** | `assets/employees_messy.csv` | Test dataset with multiple DQ issues — should produce FAIL |

### Dependencies

- **Python 3.8+**
- **pandas** — CSV parsing, dtype inference, duplicate detection
- **numpy** — numeric outlier detection (IQR)
- Standard library: `argparse`, `html`, `json`, `math`, `dataclasses`, `pathlib`, `typing`

## Error Handling

| Scenario | What happens |
|----------|-------------|
| Python not installed | Clear error with install instructions per OS |
| Python found but pandas/numpy missing | `setup.sh` auto-installs via pip |
| pip not available | Tries `ensurepip`, then `get-pip.py` |
| No sudo access | Tries `pip install --user` |
| Setup fails entirely | Clear error: "Install manually: pip install pandas numpy" |
| CSV file not found | Error message, exit 1 |
| CSV is empty (0 rows) | Reports 0 rows, all checks still run |
| Very large CSV (>1M rows) | Handles it (may be slower on huge files) |

## References

- [Pandas DataFrame documentation](https://pandas.pydata.org/docs/reference/frame.html) — core data structure for all checks
- [IQR outlier detection method](https://en.wikipedia.org/wiki/Interquartile_range#Outliers) — 1.5×IQR rule for numeric outlier flagging
- [Data Quality Dimensions (DAMA)](https://www.dama.org/cpages/body-of-knowledge) — industry framework: completeness, uniqueness, consistency, validity
- [Great Expectations](https://greatexpectations.io/) — open-source DQ framework (inspiration for threshold-based validation)

## Notes

- Be strict and deterministic.
- Don't ask the user extra questions unless required to access the file or a key column list is necessary for a uniqueness check.
- **Always provide the HTML report** — no need for the user to request it separately.
- **Always use `scripts/run.sh`** — never call the Python script directly.
