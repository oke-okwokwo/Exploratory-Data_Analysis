import os
from datetime import datetime
import pandas as pd
import numpy as np

print("The script is currently running, please wait...")

RAW_PATH = "./data/raw"
PROCESSED_PATH = "./data/processed"
OUTPUT_FILE = "Summary_Statistics.csv"


def is_id_column(series: pd.Series, column_name: str) -> bool:
    """
    Determine whether a numeric column should be treated as an ID.
    """
    name_flag = any(
        keyword in column_name.lower()
        for keyword in ["id", "key", "identifier"]
    )

    uniqueness_flag = series.nunique(dropna=True) == len(series)

    return name_flag or uniqueness_flag


def calculate_summary_statistics(raw_path: str = RAW_PATH) -> pd.DataFrame:
    results = []

    for file_name in os.listdir(raw_path):
        if not file_name.lower().endswith(".csv"):
            continue

        file_path = os.path.join(raw_path, file_name)
        table_name = os.path.splitext(file_name)[0]

        df = pd.read_csv(file_path, low_memory=False)

        # Identify numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Exclude ID-like numeric columns
        numeric_cols = [
            col for col in numeric_cols
            if not is_id_column(df[col], col)
        ]

        if not numeric_cols:
            continue

        date_updated = datetime.fromtimestamp(
            os.path.getmtime(file_path)
        ).strftime("%Y-%m-%d %H:%M:%S")

        for col in numeric_cols:
            col_data = df[col].dropna()

            mean = col_data.mean()
            std = col_data.std()
            variation_coeff = std / mean if mean != 0 else np.nan

            results.append({
                "Table Name": table_name,
                "Numeric Column(s)": col,
                "Minimum": col_data.min(),
                "Maximum": col_data.max(),
                "Median": col_data.median(),
                "Average": mean,
                "Standard Deviation": std,
                "Variation Coefficient": variation_coeff,
                "Date Updated": date_updated
            })

    return pd.DataFrame(results)


def main():
    os.makedirs(PROCESSED_PATH, exist_ok=True)

    summary_df = calculate_summary_statistics(RAW_PATH)

    output_path = os.path.join(PROCESSED_PATH, OUTPUT_FILE)
    summary_df.to_csv(output_path, index=False)

    print(f"Summary statistics exported to: {output_path}")


if __name__ == "__main__":
    main()
