import os
import time
from pathlib import Path

import pandas as pd

from Scripts.outliers_STD import analyze_tables


def test_outliers_std_basic(tmp_path: Path):
    # Arrange: create raw + processed structure
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Two CSVs with overlapping numeric columns: id, value, other
    # 'id' should be excluded as ID-like
    # 'value' should have outlier in table1 (e.g., 100)
    df1 = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "value": [10, 11, 9, 10, 100],
            "other": [1.0, 2.0, 3.0, 4.0, 5.0],
            "text": ["a", "b", "c", "d", "e"],
        }
    )
    df2 = pd.DataFrame(
        {
            "id": [10, 11, 12, 13, 14],
            "value": [10, 10, 11, 9, 10],
            "other": [2.0, 2.5, 3.5, 4.5, 5.5],
            "text": ["x", "y", "z", "w", "v"],
        }
    )

    f1 = raw_dir / "table_one.csv"
    f2 = raw_dir / "table_two.csv"
    df1.to_csv(f1, index=False)
    df2.to_csv(f2, index=False)

    # Force a predictable modified time (not strictly required, but stabilizes the check)
    now = time.time()
    os.utime(f1, (now, now))
    os.utime(f2, (now, now))

    # Act
    result = analyze_tables(raw_dir=raw_dir, processed_dir=processed_dir, output_name="Outliers_STD.csv")

    # Assert: output file exists
    out_file = processed_dir / "Outliers_STD.csv"
    assert out_file.exists()

    # Assert: result has expected columns
    expected_cols = ["Table Name", "Numeric Column", "Average", "Standard Deviation", "list of outliers", "Date updated"]
    assert list(result.columns) == expected_cols

    # Assert: 'id' excluded, but 'value' and 'other' included (both are numeric in BOTH tables)
    assert "id" not in set(result["Numeric Column"].tolist())
    assert set(result["Numeric Column"].tolist()) == {"value", "other"}

    # We should have 2 tables * 2 cols = 4 rows
    assert len(result) == 4

    # Check rounding to 1 decimal place
    # table_one, value mean = (10+11+9+10+100)/5 = 140/5 = 28.0
    row_t1_value = result[(result["Table Name"] == "table_one") & (result["Numeric Column"] == "value")].iloc[0]
    assert row_t1_value["Average"] == 28.0
    assert isinstance(row_t1_value["Average"], float)

    # Outliers: 100 should be flagged (IQR method)
    assert "100" in str(row_t1_value["list of outliers"])

    # table_two, value should have no outliers
    row_t2_value = result[(result["Table Name"] == "table_two") & (result["Numeric Column"] == "value")].iloc[0]
    assert row_t2_value["list of outliers"] == "No Outliers"

    # Standard deviation should always be present (might be NaN if <2 points, but here it should be numeric)
    assert pd.notna(row_t1_value["Standard Deviation"])
    assert pd.notna(row_t2_value["Standard Deviation"])

    # Date updated populated
    assert isinstance(row_t1_value["Date updated"], str) and len(row_t1_value["Date updated"]) > 0
    assert isinstance(row_t2_value["Date updated"], str) and len(row_t2_value["Date updated"]) > 0
