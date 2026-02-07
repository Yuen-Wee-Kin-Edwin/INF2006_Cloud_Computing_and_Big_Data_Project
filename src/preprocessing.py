import pandas as pd
import psycopg2

# =========================
# CONFIG (LOCAL TESTING)
# =========================
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "graduate_employment"
DB_USER = "postgres"
DB_PASSWORD = "admin"

CSV_PATH = "GraduateEmploymentSurveyNTUNUSSITSMUSUSSSUTD.csv"  # your local CSV file

# =========================
# LOAD CSV
# =========================
def load_csv(path):
    df = pd.read_csv(path)
    print(f"Loaded CSV with {len(df)} rows")
    return df

# =========================
# CLEAN DATA
# =========================
def clean_data(df):
    # Identify rows with complete essential salary info
    salary_cols = ["basic_monthly_mean", "basic_monthly_median"]
    mask = df[salary_cols].notna().all(axis=1)

    df_clean = df[mask].copy()
    df_removed = df[~mask].copy()

    # Fill missing employment rate with 0 (only for clean data)
    if "employment_rate_overall" in df_clean.columns:
        df_clean["employment_rate_overall"] = df_clean["employment_rate_overall"].fillna(0)

    # Convert numeric columns
    numeric_cols = [
        "basic_monthly_mean",
        "basic_monthly_median",
        "gross_monthly_mean",
        "gross_monthly_median",
        "gross_monthly_25_percentile",
        "gross_monthly_75_percentile",
        "employment_rate_overall",
        "employment_rate_ft_perm"
    ]

    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

    print(f"Cleaned dataset: {len(df_clean)} rows")
    print(f"Removed (NA salary): {len(df_removed)} rows")

    return df_clean, df_removed


# =========================
# INSERT INTO POSTGRESQL
# =========================
def insert_into_db(df):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    cur = conn.cursor()

    insert_sql = """
    INSERT INTO graduate_employment (
        year,
        university,
        school,
        degree,
        basic_monthly_mean,
        basic_monthly_median,
        gross_monthly_mean,
        gross_monthly_median,
        gross_monthly_25_percentile,
        gross_monthly_75_percentile,
        employment_rate_overall,
        employment_rate_ft_perm
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """


    for _, row in df.iterrows():
        cur.execute(insert_sql, (
            int(row["year"]),
            row["university"],
            row["school"],
            row["degree"],
            row.get("basic_monthly_mean"),
            row.get("basic_monthly_median"),
            row.get("gross_monthly_mean"),
            row.get("gross_monthly_median"),
            row.get("employment_rate_overall"),
            row.get("employment_rate_ft_perm"),
            row.get("gross_monthly_25_percentile"),
            row.get("gross_monthly_75_percentile")
        ))

    conn.commit()
    cur.close()
    conn.close()

    print("Data successfully inserted into PostgreSQL")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    df = load_csv(CSV_PATH)
    df_clean, df_removed = clean_data(df)

    # Optional: inspect removed rows
    print(df_removed.head())

    insert_into_db(df_clean)

