import os
import pandas as pd
from datetime import datetime

RAW_PATH = "/data/raw"
PROCESSED_PATH = "/data/processed"
OUTPUT_FILE = "Column-RowCount-duplicate.csv"

results = []

# Ensure output directory exists
os.makedirs(PROCESSED_PATH, exist_ok=True)

for file_name in os.listdir(RAW_PATH):
    if not file_name.lower().endswith(".csv"):
        continue

    file_path = os.path.join(RAW_PATH, file_name)
    table_name = os.path.splitext(file_name)[0]

    # Read CSV
    df = pd.read_csv(file_path)

    row_count = len(df)
    column_count = len(df.columns)

    # Unique rows
    unique_rows_count = df.drop_duplicates().shape[0]
    duplicate_rows_count = row_count - unique_rows_count

    # Null count (entire table)
    null_count = df.isna().sum().sum()

    # Identify unique columns (candidate primary keys)
    unique_columns = [
        col for col in df.columns
        if df[col].nunique(dropna=True) == row_count
    ]
    unique_columns_str = ", ".join(unique_columns) if unique_columns else "None"

    # File last modified timestamp
    date_updated = datetime.fromtimestamp(
        os.path.getmtime(file_path)
    ).strftime("%Y-%m-%d %H:%M:%S")

    results.append({
        "Table Name": table_name,
        "Unique Column(s)": unique_columns_str,
        "Column Count": column_count,
        "Row Count": row_count,
        "Unique Rows Count": unique_rows_count,
        "Duplicate Rows Count": duplicate_rows_count,
        "Null Count": null_count,
        "Date Updated": date_updated
    })

# Create results DataFrame
results_df = pd.DataFrame(results)

# Export to CSV
output_path = os.path.join(PROCESSED_PATH, OUTPUT_FILE)
results_df.to_csv(output_path, index=False)

print(f"EDA summary exported to: {output_path}")
