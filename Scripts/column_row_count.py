import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import platform

# Ensure the screen is cleared before running the script
if platform.system() == "Windows":
    os.system("cls")
else:
    os.system("clear")

print("The script is currently running, please wait...")  

RAW_PATH = "./data/raw"
PROCESSED_PATH = "./data/processed"
OUTPUT_FILE = "Column-RowCount-duplicate.csv"


@dataclass
class TableStats:
    table_name: str
    unique_columns: str
    column_count: int
    row_count: int
    unique_rows_count: int
    duplicate_rows_count: int
    null_count: int
    date_updated: str


def _last_modified_iso(file_path: str) -> str:
    """
    Return the file's last modified timestamp as ISO 8601 in UTC, e.g. 2026-01-08T12:34:56Z
    """
    ts = os.path.getmtime(file_path)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _detect_unique_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that are uniquely identifying *by themselves*:
    - no nulls
    - nunique == number of rows

    Returns a list of column names. (Does not attempt multi-column composite keys.)
    """
    if df.empty:
        return []

    unique_cols: List[str] = []
    n = len(df)

    for col in df.columns:
        s = df[col]
        # exclude columns that contain any nulls (can't uniquely identify every row)
        if s.isna().any():
            continue
        if s.nunique(dropna=False) == n:
            unique_cols.append(str(col))

    return unique_cols


def analyze_csv_file(file_path: str) -> TableStats:
    file_name = os.path.basename(file_path)
    table_name = os.path.splitext(file_name)[0]

    # Read CSV: first row is header by default in pandas
    df = pd.read_csv(file_path, low_memory=False)

    column_count = int(df.shape[1])
    row_count = int(df.shape[0])

    # Duplicate rows based on all columns (pandas treats NaNs as equal for duplicated())
    dup_mask = df.duplicated(keep="first")
    duplicate_rows_count = int(dup_mask.sum())
    unique_rows_count = int(row_count - duplicate_rows_count)

    # Total nulls across the table
    null_count = int(df.isna().sum().sum())

    unique_cols = _detect_unique_columns(df)
    unique_columns_str = ", ".join(unique_cols) if unique_cols else "None"

    date_updated = _last_modified_iso(file_path)

    return TableStats(
        table_name=table_name,
        unique_columns=unique_columns_str,
        column_count=column_count,
        row_count=row_count,
        unique_rows_count=unique_rows_count,
        duplicate_rows_count=duplicate_rows_count,
        null_count=null_count,
        date_updated=date_updated,
    )


def analyze_tables(
    raw_path: str = RAW_PATH,
    processed_path: str = PROCESSED_PATH,
    output_file: str = OUTPUT_FILE,
) -> pd.DataFrame:
    """
    Analyze all CSV files in raw_path and write a summary CSV to processed_path/output_file.
    Returns the resulting DataFrame.
    """
    if not os.path.isdir(raw_path):
        raise FileNotFoundError(f"Raw path not found: {raw_path}")

    os.makedirs(processed_path, exist_ok=True)

    rows: List[TableStats] = []

    for file_name in sorted(os.listdir(raw_path)):
        if not file_name.lower().endswith(".csv"):
            continue

        file_path = os.path.join(raw_path, file_name)
        if not os.path.isfile(file_path):
            continue

        rows.append(analyze_csv_file(file_path))

    df_out = pd.DataFrame(
        [
            {
                "Table Name": r.table_name,
                "Unique Column(s)": r.unique_columns,  # spelled as requested
                "Column Count": r.column_count,
                "Row count": r.row_count,
                "Unique rows count": r.unique_rows_count,
                "Duplicate rows count": r.duplicate_rows_count,
                "Null count": r.null_count,
                "Date updated": r.date_updated,
            }
            for r in rows
        ],
        columns=[
            "Table Name",
            "Unique Column(s)",
            "Column Count",
            "Row count",
            "Unique rows count",
            "Duplicate rows count",
            "Null count",
            "Date updated",
        ],
    )

    out_path = os.path.join(processed_path, output_file)
    df_out.to_csv(out_path, index=False)
    print(f"The output file {OUTPUT_FILE} exported to: {PROCESSED_PATH}")
    return df_out
    

def main() -> None:
    analyze_tables()




if __name__ == "__main__":
    main()  # Run the coulumn_row_count.py script

  # Automatically run tests after the main script
    try:
        import pytest
        print("\nRunning tests...\n")
        # Run all tests in the ./tests folder
        pytest_args = ["-q", "--tb=short", "./tests/test_column_row_count.py"]
        pytest.main(pytest_args)
    except ImportError:
        print("pytest not installed. Skipping tests.")