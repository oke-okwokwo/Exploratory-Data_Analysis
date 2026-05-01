import boto3
import time
import pandas as pd
import os
import re
from botocore.exceptions import ClientError
import platform

# Ensure the screen is cleared before running the script
if platform.system() == "Windows":
    os.system("cls")
else:
    os.system("clear")

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
SESSION_PROFILE = "default"
REGION = "eu-west-2"
DATABASE_NAME = "feesextract"
OUTPUT_LOCATION = "s3://dsa-cdl-s3-athena-notprod/"
LOCAL_OUTPUT_DIR = "./athena_exports"

# ------------------------------------------------------------------
# AWS Session & Athena client
# ------------------------------------------------------------------
session = boto3.Session(
    profile_name=SESSION_PROFILE,
    region_name=REGION
)

athena = session.client("athena")
os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# Helper: wait for Athena query completion
# ------------------------------------------------------------------
def wait_for_query(query_execution_id):
    while True:
        response = athena.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        state = response["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return response
        time.sleep(2)

# ------------------------------------------------------------------
# Helper: run Athena query + fetch all rows
# ------------------------------------------------------------------
def run_query(query):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE_NAME},
        ResultConfiguration={"OutputLocation": OUTPUT_LOCATION}
    )

    exec_id = response["QueryExecutionId"]
    result = wait_for_query(exec_id)

    if result["QueryExecution"]["Status"]["State"] != "SUCCEEDED":
        raise RuntimeError("Query failed")

    paginator = athena.get_paginator("get_query_results")
    rows = []

    for page in paginator.paginate(QueryExecutionId=exec_id):
        rows.extend(page["ResultSet"]["Rows"])

    return rows

# ------------------------------------------------------------------
# NEW: Cleanup helper for stray braces
# ------------------------------------------------------------------
def clean_text(text):
    if not text:
        return text
    return text.lstrip("{").rstrip("}")

# ------------------------------------------------------------------
# UPDATED: Key/Value parser (brace-safe)
# ------------------------------------------------------------------
def parse_key_value_string(text):
    """
    Handles rows like:
      {id= 1, name= Bob, status= ACTIVE}
    """
    if not text:
        return {}

    text = clean_text(text)

    pairs = re.findall(r'([^=,;|]+)=\s*([^,;|]+)', text)

    return {
        clean_text(k.strip()): clean_text(v.strip())
        for k, v in pairs
    }

# ------------------------------------------------------------------
# Step 1: Get tables
# ------------------------------------------------------------------
print(f"\nFetching tables from '{DATABASE_NAME}'...\n")

table_rows = run_query("SHOW TABLES")
tables = [r["Data"][0]["VarCharValue"] for r in table_rows[1:]]

for t in tables:
    print(f" - {t}")

# ------------------------------------------------------------------
# Step 2: Transform each table to tabular CSV
# ------------------------------------------------------------------
print("\nTransforming tables to tabular CSVs...\n")

for table in tables:
    print(f"Processing: {table}")

    try:
        rows = run_query(f"SELECT body FROM {DATABASE_NAME}.{table}")

        if len(rows) <= 1:
            print("   ⚠️ Empty table")
            continue

        records = []

        for row in rows[1:]:  # skip header
            record = {}

            for col in row["Data"]:
                cell = col.get("VarCharValue")
                parsed = parse_key_value_string(cell)
                record.update(parsed)

            if record:
                records.append(record)

        if not records:
            print("   ⚠️ No key-value data found")
            continue

        df = pd.DataFrame(records)

        csv_path = f"{LOCAL_OUTPUT_DIR}/{table}.csv"
        df.to_csv(csv_path, index=False)

        print(f"   ✅ {len(df)} rows written → {csv_path}")

    except ClientError as e:
        print(f"   ❌ Athena error: {e}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n✅ All tables transformed and exported cleanly.")


