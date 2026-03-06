# References

Background material on the data quality methods and thresholds used by this skill.

## Core Concepts

### 1. Data Quality Dimensions

The checks in this skill map to standard data quality dimensions from the [DAMA Body of Knowledge](https://www.dama.org/cpages/body-of-knowledge):

| Dimension | What We Check |
|-----------|--------------|
| **Completeness** | Missing values per column, completely empty columns |
| **Uniqueness** | Duplicate rows, key column uniqueness violations |
| **Consistency** | Mixed-type signals (numeric-like strings in object columns), header whitespace |
| **Validity** | Numeric outliers (IQR), schema/dtype inference |

### 2. IQR Outlier Detection

We use the **Interquartile Range (IQR) method** to flag numeric outliers:

```
Q1 = 25th percentile
Q3 = 75th percentile
IQR = Q3 - Q1

Lower bound = Q1 - 1.5 × IQR
Upper bound = Q3 + 1.5 × IQR

Any value outside [Lower, Upper] is flagged as an outlier.
```

**Why 1.5×IQR?**
- Proposed by John Tukey (1977) in *Exploratory Data Analysis*
- Robust to non-normal distributions (unlike z-score methods)
- 1.5× is the standard "mild outlier" threshold; 3× would flag only "extreme outliers"

**Limitations:**
- Not appropriate for heavily skewed distributions without transformation
- Columns with < 8 non-null values are skipped (insufficient data)
- IQR = 0 columns are skipped (constant values)

### 3. Missingness Thresholds

| Missing % | Severity | Rationale |
|-----------|----------|-----------|
| 0% | PASS | Complete data |
| 0.01–9.99% | PASS | Minor — typical in real datasets |
| 10–50% | WARNING | Significant gaps — investigate upstream |
| >50% | FAIL | Column is more absent than present — likely broken extraction or wrong schema |

These thresholds are configurable via the `Thresholds` dataclass in the script but default to the values above.

### 4. Mixed-Type Detection

Object-typed columns are sampled (up to 2000 rows) and tested for:
- **Numeric-like patterns**: regex `[-+]?\d+(\.\d+)?` — if 0–95% match, the column has mixed types
- **Date-like patterns**: regex `\d{4}-\d{2}-\d{2}` (ISO format) — same threshold

A column that's 100% numeric-like would have been parsed as numeric by pandas, so we only flag the ambiguous middle ground.

## Further Reading

- Tukey, J.W. (1977). *Exploratory Data Analysis*. Addison-Wesley. — Origin of the IQR/box-plot outlier rule
- [pandas `read_csv` documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) — How dtypes are inferred during CSV parsing
- [Great Expectations](https://greatexpectations.io/) — Open-source data quality framework; inspiration for threshold-based validation
- [Deequ (AWS)](https://github.com/awslabs/deequ) — Unit tests for data; similar philosophy of deterministic, declarative checks
- [TDWI Data Quality Benchmark](https://tdwi.org/) — Industry benchmarks on data quality costs and best practices
