# Assets

Sample CSV files for testing the data quality checker.

| File | Purpose |
|------|---------|
| `sample_clean.csv` | A clean dataset — should produce a **PASS** result with no issues |
| `sample_dirty.csv` | A deliberately messy dataset with multiple quality issues for testing all checks |

## Issues in `sample_dirty.csv`

- **Trailing empty column** (unnamed header)
- **Leading whitespace** in column name (` department`)
- **Mixed types** in `age` column (`"twenty-eight"` among integers)
- **Missing values** across multiple columns
- **Duplicate row** (id=1, Alice Smith appears twice)
- **Numeric outliers** (`salary = -5000`, `age = 150`)
- **Completely empty row** (id=8)
- **Inconsistent date formats** (`"not-a-date"` in join_date)

## Usage

Just tell the agent in natural language:

```
use the csv-dq-checker skill on the following data
/path/to/your/file.csv
```

### Examples

```
use the csv-dq-checker skill on the following data
/home/bandaru/Downloads/archive/Smartphone_Usage_Productivity_Dataset_50000.csv
```

```
use the csv-dq-checker skill on the following data
assets/sample_clean.csv
```

```
use the csv-dq-checker skill on the following data
assets/sample_dirty.csv
```

### Direct script usage (optional)

```bash
# Basic run
python scripts/csv_dq_report.py --input /path/to/your/file.csv

# With custom HTML output path
python scripts/csv_dq_report.py --input /path/to/your/file.csv --output-html /path/to/report.html

# With key column uniqueness check
python scripts/csv_dq_report.py --input /path/to/your/file.csv --key-cols id,email
```
