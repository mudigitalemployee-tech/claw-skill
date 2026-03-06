# Threshold Reference

Quick reference for all configurable thresholds and rules used by the checker.

## Severity Matrix

| Check | PASS | WARNING | FAIL |
|-------|------|---------|------|
| Missing values (per column) | < 10% | 10–50% | > 50% |
| Duplicate rows | 0 | > 0 | — |
| Duplicate column names | No | — | Yes |
| Empty column names | No | — | Yes |
| Completely empty columns | No | — | Yes |
| Mixed-type signals | None | Detected | — |
| Numeric outliers (IQR) | None | Detected | — |
| Key uniqueness (if `--key-cols`) | Unique, no NULLs | — | Duplicates or NULLs in key |

## Overall Status Logic

```
if any FAIL condition → FAIL
else if any WARNING condition → WARNING
else → PASS
```

## Defaults (Thresholds dataclass)

```python
fail_missing_pct = 50.0   # Column > 50% missing → FAIL
warn_missing_pct = 10.0   # Column 10-50% missing → WARNING
```

## IQR Parameters

```python
iqr_multiplier = 1.5      # Standard Tukey fence
min_sample_size = 8        # Skip columns with fewer non-null values
```
