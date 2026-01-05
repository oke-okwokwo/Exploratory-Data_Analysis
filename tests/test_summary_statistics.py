import os
import pandas as pd
import numpy as np
from summary_statistics import calculate_summary_statistics


def test_summary_statistics(tmp_path):
    # Create mock raw directory
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Create sample CSV
    test_csv = raw_dir / "test_table.csv"
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "age": [20, 30, 40, 50],
        "salary": [30000, 40000, 50000, 60000],
        "category": ["A", "B", "A", "B"]
    })
    df.to_csv(test_csv, index=False)

    # Run calculation
    result_df = calculate_summary_statistics(str(raw_dir))

    # Assertions
    assert not result_df.empty
    assert "id" not in result_df["Numeric Column(s)"].values
    assert set(result_df["Numeric Column(s)"]) == {"age", "salary"}

    age_stats = result_df[result_df["Numeric Column(s)"] == "age"].iloc[0]
    assert age_stats["Minimum"] == 20
    assert age_stats["Maximum"] == 50
    assert age_stats["Median"] == 35
    assert age_stats["Average"] == 35
