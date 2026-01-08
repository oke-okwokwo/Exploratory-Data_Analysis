import os
import subprocess
from datetime import datetime
import pandas as pd
import numpy as np
import pytest
import platform

# Ensure the screen is cleared before running the script
if platform.system() == "Windows":
    os.system("cls")
else:
    os.system("clear")

print("The script is currently running, please wait...")   

RAW_PATH = "./data/raw"
PROCESSED_PATH = "./data/processed"
OUTPUT_FILE = "Outliers.csv"


def is_id_column(series: pd.Series) -> bool:
    """Heuristic to detect ID-like numeric columns."""
    name = series.name.lower()

    if any(k in name for k in ["id", "uuid", "key"]):
        return True

    if pd.api.types.is_integer_dtype(series):
        unique_ratio = series.nunique(dropna=True) / len(series.dropna())
        if unique_ratio > 0.9:
            return True

    return False


def detect_outliers(series: pd.Series) -> list:
    """Detect outliers using IQR."""
    series = series.dropna()
    if series.empty:
        return []

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 3.0 * iqr
    upper = q3 + 3.0 * iqr

    return series[(series < lower) | (series > upper)].tolist()


def load_tables():
    tables = {}
    for file in os.listdir(RAW_PATH):
        if file.endswith(".csv"):
            path = os.path.join(RAW_PATH, file)
            tables[file] = pd.read_csv(path, low_memory=False)
    return tables


def find_common_numeric_columns(tables: dict) -> set:
    numeric_sets = []

    for df in tables.values():
        numeric_cols = set(
            col for col in df.columns
            if pd.api.types.is_numeric_dtype(df[col])
        )
        numeric_sets.append(numeric_cols)

    return set.intersection(*numeric_sets)


def main():
    os.makedirs(PROCESSED_PATH, exist_ok=True)

    tables = load_tables()
    common_numeric_cols = find_common_numeric_columns(tables)

    results = []

    for table_name, df in tables.items():
        file_path = os.path.join(RAW_PATH, table_name)
        modified_time = datetime.fromtimestamp(
            os.path.getmtime(file_path)
        ).isoformat()

        for col in common_numeric_cols:
            if is_id_column(df[col]):
                continue

            outliers = detect_outliers(df[col])

            if outliers:
                results.append({
                    "Table Name": table_name,
                    "Numeric Column": col,
                    "Outliers": outliers,
                    "Date Updated": modified_time
                })

    output_path = os.path.join(PROCESSED_PATH, OUTPUT_FILE)
    pd.DataFrame(results).to_csv(output_path, index=False)

    print(f"Outlier detection complete → {output_path}")


if __name__ == "__main__":
    main()  # Run the outlier script

  # Automatically run tests after the main script
    try:
        import pytest
        print("\nRunning tests...\n")
        # Run all tests in the ./tests folder
        pytest_args = ["-q", "--tb=short", "./tests/test_outliers.py"]
        pytest.main(pytest_args)
    except ImportError:
        print("pytest not installed. Skipping tests.")
