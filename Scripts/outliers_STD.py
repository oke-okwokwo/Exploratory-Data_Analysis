
#!/usr/bin/env python3
"""
outliers_STD.py

Reads all CSV files in ./data/raw, finds numeric columns that are numeric in *all* tables (intersection),
excludes numeric ID-like columns, then for each table & numeric column computes:
- Average (rounded to 1 decimal)
- Standard deviation (rounded to 1 decimal)
- Outliers list using IQR rule (or "No Outliers" if none)
- Date updated from file last-modified timestamp

Outputs: ./data/processed/Outliers_STD.csv
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

import numpy as np
import pandas as pd
import platform

# Ensure the screen is cleared before running the script
if platform.system() == "Windows":
    os.system("cls")
else:
    os.system("clear")

print("The script is currently running, please wait...")  

DEFAULT_RAW_DIR = Path("./data/raw")
DEFAULT_PROCESSED_DIR = Path("./data/processed")
DEFAULT_OUTPUT_NAME = "Outliers_STD.csv"


def _file_modified_iso(path: Path) -> str:
    ts = path.stat().st_mtime
    # Use UTC ISO format for consistent tests/runs
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")


def _coerce_numeric_series(s: pd.Series) -> pd.Series:
    # Convert strings like "1,234" safely; keep NaNs
    if s.dtype == object:
        s = s.astype(str).str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _numeric_columns_in_df(df: pd.DataFrame, min_numeric_ratio: float = 0.9) -> Set[str]:
    """
    Identify numeric columns by attempting coercion. A column is "numeric" if
    at least min_numeric_ratio of non-null entries are numeric after coercion.
    """
    numeric_cols: Set[str] = set()
    for col in df.columns:
        ser = df[col]
        coerced = _coerce_numeric_series(ser)
        non_null = ser.notna().sum()
        if non_null == 0:
            continue
        numeric_non_null = coerced.notna().sum()
        if (numeric_non_null / non_null) >= min_numeric_ratio:
            numeric_cols.add(col)
    return numeric_cols


def _looks_like_id_column(name: str, numeric_values: pd.Series) -> bool:
    """
    Heuristic ID detection:
    - Column name contains 'id' (case-insensitive) OR ends with common id patterns
    - AND values are mostly integers
    - AND high uniqueness ratio (identifier-like)
    """
    lname = name.strip().lower()
    name_suggests_id = (
        "id" == lname
        or lname.endswith("_id")
        or lname.endswith("id")
        or lname.startswith("id_")
        or " id " in f" {lname} "
        or "id" in lname
    )
    if not name_suggests_id:
        return False

    vals = numeric_values.dropna()
    if len(vals) < 3:
        return False

    # Mostly integer-ish?
    intish_ratio = np.mean(np.isclose(vals % 1, 0))
    if intish_ratio < 0.95:
        return False

    # High uniqueness suggests identifier
    uniq_ratio = vals.nunique(dropna=True) / len(vals)
    return uniq_ratio >= 0.9


def _iqr_outliers(values: pd.Series) -> List[float]:
    """
    Outliers by IQR rule: < Q1 - 1.5*IQR or > Q3 + 1.5*IQR
    Returns unique outlier values as floats, sorted.
    """
    v = values.dropna().astype(float)
    if len(v) < 4:
        return []

    q1 = np.percentile(v, 25)
    q3 = np.percentile(v, 75)
    iqr = q3 - q1
    if iqr == 0:
        return []

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outs = v[(v < lower) | (v > upper)]
    if outs.empty:
        return []
    unique_sorted = sorted(set(outs.tolist()))
    return unique_sorted


def analyze_tables(
    raw_dir: Path = DEFAULT_RAW_DIR,
    processed_dir: Path = DEFAULT_PROCESSED_DIR,
    output_name: str = DEFAULT_OUTPUT_NAME,
) -> pd.DataFrame:
    """
    Core function for computing the output table. Returns the result DataFrame
    and also writes it to processed_dir/output_name.
    """
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted([p for p in raw_dir.glob("*.csv") if p.is_file()])
    if not csv_files:
        # Still create an empty output with correct columns
        empty = pd.DataFrame(
            columns=["Table Name", "Numeric Column", "Average", "Standard Deviation", "list of outliers", "Date updated"]
        )
        out_path = processed_dir / output_name
        empty.to_csv(out_path, index=False)
        return empty

    # Read all tables and determine numeric columns per table
    tables: dict[Path, pd.DataFrame] = {}
    numeric_cols_per_table: dict[Path, Set[str]] = {}

    for f in csv_files:
        df = pd.read_csv(f, low_memory=False)
        tables[f] = df
        numeric_cols_per_table[f] = _numeric_columns_in_df(df)

    # Intersection: numeric columns that are numeric in all tables
    common_numeric_cols: Set[str] = set.intersection(*numeric_cols_per_table.values()) if numeric_cols_per_table else set()

    results = []
    for f, df in tables.items():
        table_name = f.stem  # exact file name without extension
        date_updated = _file_modified_iso(f)

        for col in sorted(common_numeric_cols):
            if col not in df.columns:
                continue

            numeric_series = _coerce_numeric_series(df[col])

            # Exclude ID-like numeric columns
            if _looks_like_id_column(col, numeric_series):
                continue

            mean_val = float(np.nanmean(numeric_series.values)) if numeric_series.notna().any() else np.nan
            std_val = float(np.nanstd(numeric_series.values, ddof=1)) if numeric_series.dropna().shape[0] >= 2 else np.nan

            mean_rounded = round(mean_val, 1) if np.isfinite(mean_val) else np.nan
            std_rounded = round(std_val, 1) if np.isfinite(std_val) else np.nan

            outliers = _iqr_outliers(numeric_series)
            if outliers:
                # Keep a compact, readable format
                outliers_str = "; ".join(str(int(x)) if float(x).is_integer() else str(x) for x in outliers)
            else:
                outliers_str = "No Outliers"

            results.append(
                {
                    "Table Name": table_name,
                    "Numeric Column": col,
                    "Average": mean_rounded,
                    "Standard Deviation": std_rounded,
                    "list of outliers": outliers_str,
                    "Date updated": date_updated,
                }
            )

    result_df = pd.DataFrame(
        results,
        columns=["Table Name", "Numeric Column", "Average", "Standard Deviation", "list of outliers", "Date updated"],
    )

    out_path = processed_dir / output_name
    result_df.to_csv(out_path, index=False)
    return result_df


def main() -> None:
    analyze_tables(DEFAULT_RAW_DIR, DEFAULT_PROCESSED_DIR, DEFAULT_OUTPUT_NAME)
    print(f"Outlier detection complete → {DEFAULT_PROCESSED_DIR}")

if __name__ == "__main__":
    main()  # Run the outlier script

  # Automatically run tests after the main script
    try:
        import pytest
        print("\nRunning tests...\n")
        # Run all tests in the ./tests folder
        pytest_args = ["-q", "--tb=short", "./tests/test_outliers_std.py"]
        pytest.main(pytest_args)
    except ImportError:
        print("pytest not installed. Skipping tests.")