# Assets

Sample CSV files for testing the data quality profiler.

| File | Purpose |
|------|---------|
| `employees_valid.csv` | Clean dataset — should produce a **PASS** result with no issues |
| `employees_messy.csv` | Messy dataset with multiple quality issues — should produce **FAIL** |

## Issues in `employees_messy.csv`

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
use the csv-data-quality-profiler skill on the following data
/path/to/your/file.csv
```

### Examples

```
use the csv-data-quality-profiler skill on the following data
/home/bandaru/Downloads/archive/Smartphone_Usage_Productivity_Dataset_50000.csv
```

### Direct script usage (optional)

```bash
# Basic run
bash scripts/run.sh --input /path/to/your/file.csv

# With custom HTML output path
bash scripts/run.sh --input /path/to/your/file.csv --output-html /path/to/report.html

# With key column uniqueness check
bash scripts/run.sh --input /path/to/your/file.csv --key-cols id,email
```
