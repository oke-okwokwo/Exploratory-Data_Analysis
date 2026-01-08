# tests/test_summary_statistics_1.py

from pathlib import Path
import math

import pandas as pd

from Scripts.summary_statistics_1 import calculate_summary_statistics


def test_summary_statistics_excludes_id_columns_and_calculates_correctly(tmp_path: Path):
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create a sample CSV:
    # - customer_id should be excluded (ID-like)
    # - value should be included
    # - qty is numeric-as-strings and should be included
    # - note is non-numeric
    csv_content = """customer_id,value,qty,note
1,10,1,foo
2,20,2,bar
3,30,3,baz
4,40,4,qux
"""
    (raw_dir / "sales.csv").write_text(csv_content, encoding="utf-8")

    df = calculate_summary_statistics(
        raw_path=raw_dir,
        processed_path=processed_dir,
        output_file="Summary_Statistics.csv",
    )

    # Output file exists
    out_path = processed_dir / "Summary_Statistics.csv"
    assert out_path.exists()

    out_df = pd.read_csv(out_path)
    assert len(out_df) == len(df)

    # Ensure customer_id excluded
    assert "customer_id" not in set(out_df["Numeric Column(s)"].astype(str))

    # Ensure expected numeric columns present
    cols = set(out_df["Numeric Column(s)"].astype(str))
    assert "value" in cols
    assert "qty" in cols

    # Validate stats for "value" column: [10,20,30,40]
    row_value = out_df[out_df["Numeric Column(s)"] == "value"].iloc[0]
    assert row_value["Table Name"] == "sales"
    assert row_value["Minimum"] == 10
    assert row_value["maximum"] == 40
    assert row_value["median"] == 25
    assert row_value["Average"] == 25

    # Sample std dev for [10,20,30,40]:
    # mean=25; deviations=(-15,-5,5,15); squares=(225,25,25,225) sum=500; / (n-1)=166.6667; sqrt=12.9099
    assert math.isclose(row_value["Standard deviation"], 12.909944, rel_tol=1e-6, abs_tol=1e-6)

    # Variation coefficient = std / avg
    assert math.isclose(row_value["Variation Coefficient"], 12.909944 / 25, rel_tol=1e-6, abs_tol=1e-6)
