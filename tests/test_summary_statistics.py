import sys
from pathlib import Path

# Add project root to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import numpy as np
from Scripts.summary_statistics import calculate_summary_statistics


def test_summary_statistics_basic(tmp_path):
    """
    Test numeric column detection, ID exclusion, and statistics correctness.
    """

    # Create temporary raw data directory
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Create sample CSV file
    test_csv = raw_dir / "sample_table.csv"
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],                # Should be excluded (ID)
        "age": [20, 30, 40, 50],           # Numeric
        "salary": [30000, 40000, 50000, 60000],  # Numeric
        "department": ["A", "B", "A", "B"]  # Non-numeric
    })
   





