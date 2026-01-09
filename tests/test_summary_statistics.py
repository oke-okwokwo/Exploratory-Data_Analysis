import numpy as np
import pandas as pd
from Scripts.summary_statistics import calculate_summary_statistics



def test_summary_statistics_basic(tmp_path):
    # Create mock raw directory
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Create sample CSV where non-ID numeric columns are NOT all-unique
    test_csv = raw_dir / "test_table.csv"
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],                 # unique -> should be excluded as ID
        "age": [20, 20, 30, 30],            # repeated -> should be included
        "salary": [30000, 30000, 50000, 50000],  # repeated -> should be included
        "category": ["A", "B", "A", "B"]
    })
    df.to_csv(test_csv, index=False)

    # Run calculation
    result_df = calculate_summary_statistics(str(raw_dir))

    # Assertions
    assert not result_df.empty
    assert "id" not in result_df["Numeric Column(s)"].values
    assert set(result_df["Numeric Column(s)"].values) == {"age", "salary"}
  
    # Check a couple of stats for age
    age_stats = result_df[result_df["Numeric Column(s)"] == "age"].iloc[0]
    assert age_stats["Minimum"] == 20
    assert age_stats["Maximum"] == 30
    assert age_stats["Median"] == 25
    assert age_stats["Average"] == 25
   

def test_std_and_variation_coefficient_rounding(tmp_path):

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Carefully chosen values to test rounding behavior
    # Values: mean = 25
    # std (sample) ≈ 5.7735 → rounded to 5.8
    # variation coeff = (5.8 / 25) * 100 = 23.2
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "value": [20, 20, 30, 30]
    })

    csv_path = raw_dir / "rounding_test.csv"
    df.to_csv(csv_path, index=False)

    result_df = calculate_summary_statistics(str(raw_dir))

    value_row = result_df[result_df["Numeric Column(s)"] == "value"].iloc[0]

    # Validate rounded standard deviation
    assert value_row["Standard Deviation"] == 5.8

    # Validate rounded variation coefficient (%)
    assert value_row["Variation Coefficient"] == 23.2





