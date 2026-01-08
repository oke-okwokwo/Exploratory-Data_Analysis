import sys
from pathlib import Path

# Add project root to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import os
from datetime import datetime

import pandas as pd
import pytest

from Scripts.column_row_count import analyze_tables


def test_analyze_tables_counts_and_duplicates(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    # Create a CSV with duplicates and nulls
    # Rows:
    # 1) (1, "a")
    # 2) (1, "a")  -> duplicate of row 1
    # 3) (2, None) -> null in value
    df1 = pd.DataFrame({"id": [1, 1, 2], "value": ["a", "a", None]})
    f1 = raw_dir / "table_one.csv"
    df1.to_csv(f1, index=False)

    # Create a second CSV with a unique column and no duplicates
    df2 = pd.DataFrame({"pk": [10, 11, 12], "x": [5, 6, 7]})
    f2 = raw_dir / "table_two.csv"
    df2.to_csv(f2, index=False)

    out_name = "Column-RowCount-duplicate.csv"
    result_df = analyze_tables(
        raw_path=str(raw_dir),
        processed_path=str(processed_dir),
        output_file=out_name,
    )

    # Output file exists
    out_path = processed_dir / out_name
    assert out_path.exists()

    # Result has two rows (two tables)
    assert len(result_df) == 2

    # table_one assertions
    row1 = result_df[result_df["Table Name"] == "table_one"].iloc[0]
    assert row1["Column Count"] == 2
    assert row1["Row count"] == 3
    assert row1["Duplicate rows count"] == 1
    assert row1["Unique rows count"] == 2
    assert row1["Null count"] == 1
    # Unique column(s): id is not unique; value is not unique; expect "None"
    assert row1["Unique Coumn(s)"] == "None"
    # Date updated should look like ISO Zulu format
    assert row1["Date updated"].endswith("Z")

    # table_two assertions
    row2 = result_df[result_df["Table Name"] == "table_two"].iloc[0]
    assert row2["Column Count"] == 2
    assert row2["Row count"] == 3
    assert row2["Duplicate rows count"] == 0
    assert row2["Unique rows count"] == 3
    assert row2["Null count"] == 0
    # pk should be unique (no nulls, all distinct)
    assert "pk" in row2["Unique Coumn(s)"]
    assert row2["Date updated"].endswith("Z")


def test_analyze_tables_missing_raw_path(tmp_path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        analyze_tables(raw_path=str(missing), processed_path=str(tmp_path))
