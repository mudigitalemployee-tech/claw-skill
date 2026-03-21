#!/usr/bin/env python3
"""
Automated CSV data analysis for BI Report Generator.

Usage: python3 analyze_data.py <input.csv> <output.json>

Outputs a JSON file with:
  - summary: per-column stats (count, mean, std, min, max, nulls, dtype)
  - growth_rates: period-over-period % change per numeric column
  - moving_averages: 3-period moving average per numeric column
  - correlations: correlation matrix (numeric columns only)
  - anomalies: rows where any numeric value deviates > 2 std from mean
  - significant_changes: items with absolute growth > 5%
  - categorical_breakdowns: top-N value counts for each non-numeric column
  - data_quality: null rates, duplicate counts, type inconsistencies
  - time_series: monthly/periodic aggregations if date column detected
"""

import sys
import json
import pandas as pd
import numpy as np


def detect_date_column(df):
    """Try to find and parse a date column."""
    date_col = None
    for col in df.columns:
        if df[col].dtype == 'object':
            sample = df[col].dropna().head(100)
            try:
                parsed = pd.to_datetime(sample, format='mixed', utc=True)
                if parsed.notna().sum() > len(sample) * 0.8:
                    date_col = col
                    break
            except Exception:
                continue
        # Also check column names
        if col.lower() in ('date', 'datetime', 'timestamp', 'saledate', 'sale_date',
                           'created_at', 'updated_at', 'order_date', 'transaction_date'):
            try:
                pd.to_datetime(df[col].dropna().head(20), format='mixed', utc=True)
                date_col = col
                break
            except Exception:
                continue
    return date_col


def analyze(input_path: str) -> dict:
    df = pd.read_csv(input_path)

    # --- Summary stats ---
    summary = {}
    for col in df.columns:
        info = {
            "dtype": str(df[col].dtype),
            "count": int(df[col].count()),
            "nulls": int(df[col].isna().sum()),
            "null_pct": round(float(df[col].isna().mean() * 100), 2),
            "unique": int(df[col].nunique()),
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            info.update({
                "mean": round(float(desc["mean"]), 4),
                "std": round(float(desc["std"]), 4) if "std" in desc else None,
                "min": round(float(desc["min"]), 4),
                "max": round(float(desc["max"]), 4),
                "median": round(float(df[col].median()), 4),
                "variance": round(float(df[col].var()), 4),
                "q25": round(float(desc["25%"]), 4) if "25%" in desc else None,
                "q75": round(float(desc["75%"]), 4) if "75%" in desc else None,
            })
        summary[col] = info

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

    # --- Growth rates (row-over-row % change) ---
    growth_rates = {}
    for col in numeric_cols:
        pct = df[col].pct_change(fill_method=None).dropna()
        growth_rates[col] = {
            "mean_growth": round(float(pct.mean()), 6) if len(pct) > 0 else None,
            "max_growth": round(float(pct.max()), 6) if len(pct) > 0 else None,
            "min_growth": round(float(pct.min()), 6) if len(pct) > 0 else None,
        }

    # --- Moving averages (window=3) ---
    window = min(3, len(df))
    moving_averages = {}
    for col in numeric_cols:
        ma = df[col].rolling(window=window).mean().dropna()
        moving_averages[col] = {
            "window": window,
            "last_3": [round(v, 4) for v in ma.tail(3).tolist()],
        }

    # --- Correlation matrix ---
    corr = {}
    if len(numeric_cols) >= 2:
        corr_df = df[numeric_cols].corr()
        corr = {
            "columns": numeric_cols,
            "matrix": corr_df.round(4).values.tolist(),
        }
        # Highlight strong correlations (|r| > 0.7, excluding self)
        strong = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                r = corr_df.iloc[i, j]
                if abs(r) > 0.7:
                    strong.append({
                        "col1": numeric_cols[i],
                        "col2": numeric_cols[j],
                        "r": round(float(r), 4),
                        "strength": "strong_positive" if r > 0 else "strong_negative",
                    })
        corr["strong_correlations"] = strong

    # --- Anomaly detection (z-score > 2) ---
    anomalies = []
    anomaly_summary = {}
    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        if std and std > 0:
            z = ((df[col] - mean) / std).abs()
            outlier_count = int((z > 2).sum())
            anomaly_summary[col] = {
                "outlier_count": outlier_count,
                "outlier_pct": round(outlier_count / len(df) * 100, 2),
            }
            # Sample up to 5 anomalies per column
            outlier_idx = z[z > 2].nlargest(5).index.tolist()
            for idx in outlier_idx:
                anomalies.append({
                    "row": int(idx),
                    "column": col,
                    "value": round(float(df[col].iloc[idx]), 4),
                    "z_score": round(float(z.iloc[idx]), 4),
                    "mean": round(float(mean), 4),
                    "std": round(float(std), 4),
                })

    # --- Significant changes (|growth| > 5%) ---
    significant = []
    for col in numeric_cols:
        pct = df[col].pct_change(fill_method=None)
        big = pct[pct.abs() > 0.05].head(10)
        for idx in big.index:
            val = pct.loc[idx]
            if pd.notna(val):
                significant.append({
                    "row": int(idx),
                    "column": col,
                    "change_pct": round(float(val * 100), 2),
                    "from_value": round(float(df[col].iloc[idx - 1]), 4) if idx > 0 else None,
                    "to_value": round(float(df[col].iloc[idx]), 4),
                })

    # --- KPI candidates (first and last row comparison) ---
    kpis = {}
    if len(df) >= 2:
        for col in numeric_cols:
            first = df[col].iloc[0]
            last = df[col].iloc[-1]
            if pd.notna(first) and pd.notna(last) and first != 0:
                kpis[col] = {
                    "latest": round(float(last), 4),
                    "earliest": round(float(first), 4),
                    "total_change_pct": round(float((last - first) / abs(first) * 100), 2),
                    "direction": "up" if last > first else "down" if last < first else "flat",
                }

    # --- Categorical breakdowns (top 10 per column) ---
    categorical_breakdowns = {}
    for col in categorical_cols:
        vc = df[col].value_counts().head(10)
        categorical_breakdowns[col] = {
            "total_unique": int(df[col].nunique()),
            "top_values": [
                {"value": str(v), "count": int(c), "pct": round(c / len(df) * 100, 2)}
                for v, c in vc.items()
            ],
        }
        # Check for case inconsistencies
        if df[col].dtype == 'object':
            lower_unique = df[col].dropna().str.lower().nunique()
            raw_unique = df[col].nunique()
            if lower_unique < raw_unique:
                categorical_breakdowns[col]["case_inconsistency"] = {
                    "raw_unique": raw_unique,
                    "normalized_unique": lower_unique,
                    "duplicated_by_case": raw_unique - lower_unique,
                }

    # --- Cross-tabulation: avg numeric by top categoricals ---
    cross_tabs = {}
    if numeric_cols and categorical_cols:
        # Pick the most important numeric col (highest variance or first)
        main_numeric = numeric_cols[-1] if 'price' in numeric_cols[-1].lower() or 'selling' in numeric_cols[-1].lower() else numeric_cols[0]
        for cat_col in categorical_cols[:3]:  # Top 3 categorical cols
            top_cats = df[cat_col].value_counts().head(10).index.tolist()
            grp = df[df[cat_col].isin(top_cats)].groupby(cat_col)[main_numeric].agg(['mean', 'median', 'count'])
            grp = grp.sort_values('mean', ascending=False).round(2)
            cross_tabs[f"{main_numeric}_by_{cat_col}"] = {
                "numeric_col": main_numeric,
                "category_col": cat_col,
                "data": [
                    {"category": str(idx), "mean": float(row['mean']), "median": float(row['median']), "count": int(row['count'])}
                    for idx, row in grp.iterrows()
                ],
            }

    # --- Time series aggregation ---
    time_series = {}
    date_col = detect_date_column(df)
    if date_col:
        try:
            df['_parsed_date'] = pd.to_datetime(df[date_col], format='mixed', utc=True, errors='coerce')
            df['_month'] = df['_parsed_date'].dt.to_period('M')
            monthly = df.groupby('_month').agg(
                **{f"avg_{c}": (c, 'mean') for c in numeric_cols},
                **{"volume": (numeric_cols[0], 'count')},
            ).sort_index()
            monthly = monthly[monthly['volume'] > max(10, len(df) * 0.001)]
            time_series = {
                "date_column": date_col,
                "periods": [str(idx) for idx in monthly.index],
                "metrics": {},
                "volume": monthly['volume'].tolist(),
            }
            for col in numeric_cols:
                key = f"avg_{col}"
                if key in monthly.columns:
                    time_series["metrics"][col] = [round(v, 2) for v in monthly[key].tolist()]
            df.drop(columns=['_parsed_date', '_month'], inplace=True, errors='ignore')
        except Exception:
            pass

    # --- Data quality report ---
    data_quality = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_pct": round(float(df.duplicated().mean() * 100), 2),
        "columns_with_nulls": {
            col: {"nulls": int(df[col].isna().sum()), "pct": round(float(df[col].isna().mean() * 100), 2)}
            for col in df.columns if df[col].isna().sum() > 0
        },
        "complete_columns": [col for col in df.columns if df[col].isna().sum() == 0],
    }

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "summary": summary,
        "growth_rates": growth_rates,
        "moving_averages": moving_averages,
        "correlations": corr,
        "anomalies": anomalies[:100],
        "anomaly_summary": anomaly_summary,
        "significant_changes": significant[:50],
        "kpis": kpis,
        "categorical_breakdowns": categorical_breakdowns,
        "cross_tabs": cross_tabs,
        "time_series": time_series,
        "data_quality": data_quality,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 analyze_data.py <input.csv> <output.json>")
        sys.exit(1)

    result = analyze(sys.argv[1])

    with open(sys.argv[2], "w") as f:
        json.dump(result, f, indent=2)

    print(f"Analysis complete: {result['row_count']} rows, {result['column_count']} columns")
    print(f"  Numeric columns: {len(result['numeric_columns'])}")
    print(f"  Categorical columns: {len(result['categorical_columns'])}")
    print(f"  Anomalies found: {len(result['anomalies'])}")
    print(f"  Significant changes: {len(result['significant_changes'])}")
    print(f"  Strong correlations: {len(result.get('correlations', {}).get('strong_correlations', []))}")
    print(f"  Time series periods: {len(result.get('time_series', {}).get('periods', []))}")
    print(f"  Data quality — duplicates: {result['data_quality']['duplicate_rows']} ({result['data_quality']['duplicate_pct']}%)")
    print(f"  Data quality — columns with nulls: {len(result['data_quality']['columns_with_nulls'])}")
    print(f"  Output: {sys.argv[2]}")
