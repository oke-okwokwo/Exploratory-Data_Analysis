# summary_statistics_1.py

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np
import pandas as pd
import platform

# Ensure the screen is cleared before running the script
if platform.system() == "Windows":
    os.system("cls")
else:
    os.system("clear")

print("The script is currently running, please wait...") 

RAW_PATH = Path("./data/raw")
PROCESSED_PATH = Path("./data/processed")
OUTPUT_FILE = "Summary_Statistics.csv"


ID_NAME_KEYWORDS = ("id", "key", "identifier", "uuid", "guid")


def _file_modified_iso(filepath: Path) -> str:
    """
    Return file last-modified timestamp as ISO-8601 string (UTC).
    """
    ts = filepath.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def is_id_column(series: pd.Series, column_name: str) -> bool:
    """
    Heuristic to identify numeric ID-like columns:
      - Column name contains ID-ish keywords; OR
      - Values are (almost) all unique among non-null values and cover most rows.
    """
    name = (column_name or "").lower()
    name_flag = any(k in name for k in ID_NAME_KEYWORDS)

    non_null = series.dropna()
    if len(non_null) == 0:
        uniqueness_flag = False
    else:
        # If nearly every non-null is unique, and the column is mostly populated,
        # treat it as an ID-like field.
        unique_ratio = non_null.nunique(dropna=True) / len(non_null)
        coverage_ratio = len(non_null) / len(series) if len(series) else 0.0
        uniqueness_flag = (unique_ratio >= 0.995) and (coverage_ratio >= 0.80)

    return bool(name_flag or uniqueness_flag)


def _numeric_columns_excluding_ids(df: pd.DataFrame) -> List[str]:
    """
    Determine numeric columns in a table, excluding numeric columns identified as IDs.
    - Attempts to coerce object columns to numeric (e.g., "123" -> 123).
    """
    numeric_cols: List[str] = []

    for col in df.columns:
        s = df[col]

        # Try to coerce to numeric; if most values become numeric, treat as numeric.
        if pd.api.types.is_numeric_dtype(s):
            s_num = s
        else:
            s_num = pd.to_numeric(s, errors="coerce")
            # Consider it numeric if it has at least one numeric value and
            # numeric coverage is decent vs non-null original.
            orig_non_null = s.notna().sum()
            num_non_null = s_num.notna().sum()
            if orig_non_null == 0 or num_non_null == 0:
                continue
            # If at least 90% of non-null values are numeric after coercion
            if (num_non_null / orig_non_null) < 0.90:
                continue

        # Exclude ID-like numeric columns
        if is_id_column(s_num, str(col)):
            continue

        numeric_cols.append(str(col))

    return numeric_cols


def calculate_summary_statistics(
    raw_path: Path = RAW_PATH,
    processed_path: Path = PROCESSED_PATH,
    output_file: str = OUTPUT_FILE,
) -> pd.DataFrame:
    """
    Calculate summary statistics for all CSV tables in raw_path and save results to processed_path/output_file.

    Output columns (in order):
      Table Name, Numeric Column(s), Minimum, maximum, median, Average,
      Standard deviation, Variation Coefficient, Date updated
    """
    raw_path = Path(raw_path)
    processed_path = Path(processed_path)
    processed_path.mkdir(parents=True, exist_ok=True)

    rows: List[dict] = []

    for csv_path in sorted(raw_path.glob("*.csv")):
        table_name = csv_path.stem
        date_updated = _file_modified_iso(csv_path)

        df = pd.read_csv(csv_path)

        numeric_cols = _numeric_columns_excluding_ids(df)

        # One output row per numeric column
        for col in numeric_cols:
            s_num = pd.to_numeric(df[col], errors="coerce").dropna()
            if s_num.empty:
                continue

            minimum = float(s_num.min())
            maximum = float(s_num.max())
            median = float(s_num.median())
            average = float(s_num.mean())
            std_dev = float(s_num.std(ddof=1))  # sample std dev

            # Variation coefficient = std_dev / average
            if average == 0 or np.isclose(average, 0.0):
                var_coeff = np.nan
            else:
                var_coeff = float(std_dev / average)

            rows.append(
                {
                    "Table Name": table_name,
                    "Numeric Column(s)": col,
                    "Minimum": minimum,
                    "maximum": maximum,
                    "median": median,
                    "Average": average,
                    "Standard deviation": std_dev,
                    "Variation Coefficient": var_coeff,
                    "Date updated": date_updated,
                }
            )

    result = pd.DataFrame(
        rows,
        columns=[
            "Table Name",
            "Numeric Column(s)",
            "Minimum",
            "maximum",
            "median",
            "Average",
            "Standard deviation",
            "Variation Coefficient",
            "Date updated",
        ],
    )

    out_path = processed_path / output_file
    result.to_csv(out_path, index=False)

    return result


def main() -> None:
    calculate_summary_statistics()


if __name__ == "__main__":
    main()  # Run the summary statistics_1

  # Automatically run tests after the main script
    try:
        import pytest
        print("\nRunning tests...\n")
        # Run all tests in the ./tests folder
        pytest_args = ["-q", "--tb=short", "./tests/test_summary_statistics_1.py"]
        pytest.main(pytest_args)
    except ImportError:
        print("pytest not installed. Skipping tests.")

