import pandas as pd
import psycopg2
import re

# =========================
# DATABASE CONFIG (LOCAL)
# =========================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "graduate_employment",
    "user": "postgres",
    "password": "admin"
}

CSV_PATH = "GraduateEmploymentSurveyNTUNUSSITSMUSUSSSUTD.csv"

# =========================
# LOAD CSV
# =========================
def load_csv(path):
    df = pd.read_csv(path)
    print(f"[INFO] Loaded CSV with {len(df)} rows")
    return df

# =========================
# CLEAN TEXT COLUMN
# =========================
def clean_text_column(df, col_name):
    """Remove unwanted trailing/leading characters like #, ^, extra spaces from string columns."""
    if col_name in df.columns:
        df[col_name] = df[col_name].astype(str)
        # Remove any trailing/leading non-alphanumeric characters and extra spaces
        df[col_name] = df[col_name].apply(lambda x: re.sub(r"[\s\#\^\*]+$", "", str(x)) if pd.notna(x) else "")
        df[col_name] = df[col_name].apply(lambda x: re.sub(r"^[\s\#\^\*]+", "", str(x)) if pd.notna(x) else "")

    return df

# =========================
# CLEAN + VALIDATE DATA
# =========================
def preprocess_data(df):
    # Remove duplicate rows
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"[INFO] After removing duplicates: {len(df)} rows")

    # Standardize missing values
    df = df.replace(["na", "N.A.", "NA", "-", "--"], pd.NA)

    # Remove % if the column exists and convert to float safely
    for col in ["employment_rate_overall", "employment_rate_ft_perm"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Strip spaces and remove trailing/leading unwanted characters
    str_cols = ["university", "school", "degree"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: re.sub(r"^[\s\#\^\*]+|[\s\#\^\*]+$", "", str(x)) if pd.notna(x) else "")
            df[col] = df[col].apply(lambda x: re.sub(r"\s+", " ", x))  # collapse multiple spaces
            df[col] = df[col].str.strip()


    # Columns that must exist and be numeric
    numeric_cols = [
        "employment_rate_overall",
        "employment_rate_ft_perm",
        "basic_monthly_mean",
        "basic_monthly_median",
        "gross_monthly_mean",
        "gross_monthly_median",
        "gross_mthly_25_percentile",
        "gross_mthly_75_percentile"
    ]

    # Convert year to integer
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Convert numeric columns
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Check for negative salaries
    salary_cols = [
        "basic_monthly_mean",
        "basic_monthly_median",
        "gross_monthly_mean",
        "gross_monthly_median",
        "gross_mthly_25_percentile",
        "gross_mthly_75_percentile"
    ]
    for col in salary_cols:
        df.loc[df[col] < 0, col] = pd.NA
        # Remove commas and convert to float
        df[col] = df[col].astype(str).str.replace(",", "").astype(float)

    # Employment rates must be 0-100
    for col in ["employment_rate_overall", "employment_rate_ft_perm"]:
        df.loc[(df[col] < 0) | (df[col] > 100), col] = pd.NA

    # Critical columns for analytics
    critical_cols = [
        "year",
        "university",
        "school",
        "degree",
        "basic_monthly_mean",
        "basic_monthly_median"
    ]

    # Split clean vs invalid rows
    clean_df = df.dropna(subset=critical_cols)
    invalid_df = df[df[critical_cols].isna().any(axis=1)]

    print(f"[INFO] Clean rows: {len(clean_df)}")
    print(f"[INFO] Invalid rows removed: {len(invalid_df)}")

    return clean_df, invalid_df

# =========================
# INSERT INTO POSTGRESQL
# =========================
def insert_into_db(df):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insert_sql = """
        INSERT INTO graduate_employment (
            year, university, school, degree,
            employment_rate_overall, employment_rate_ft_perm,
            basic_monthly_mean, basic_monthly_median,
            gross_monthly_mean, gross_monthly_median,
            gross_mthly_25_percentile, gross_mthly_75_percentile
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for _, row in df.iterrows():
        cur.execute(insert_sql, (
            int(row["year"]) if pd.notna(row["year"]) else None,
            row["university"],
            row["school"],
            row["degree"],
            row["employment_rate_overall"] if pd.notna(row["employment_rate_overall"]) else None,
            row["employment_rate_ft_perm"] if pd.notna(row["employment_rate_ft_perm"]) else None,
            row["basic_monthly_mean"] if pd.notna(row["basic_monthly_mean"]) else None,
            row["basic_monthly_median"] if pd.notna(row["basic_monthly_median"]) else None,
            row["gross_monthly_mean"] if pd.notna(row["gross_monthly_mean"]) else None,
            row["gross_monthly_median"] if pd.notna(row["gross_monthly_median"]) else None,
            row["gross_mthly_25_percentile"] if pd.notna(row["gross_mthly_25_percentile"]) else None,
            row["gross_mthly_75_percentile"] if pd.notna(row["gross_mthly_75_percentile"]) else None
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("[INFO] Data inserted into PostgreSQL successfully")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    df_raw = load_csv(CSV_PATH)
    df_clean, df_invalid = preprocess_data(df_raw)
    df_invalid.to_csv("invalid_rows.csv", index=False)
    insert_into_db(df_clean)
