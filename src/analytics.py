import psycopg2
import pandas as pd

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

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# =========================
# ANALYTICS FUNCTIONS
# =========================
# =========================
# Salary Statistics Analysis
# =========================
def salary_statistics(university, degree):
    """
    Display mean and median salaries for a selected university and degree (programme),
    including optional gross salary percentiles.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            year,
            ROUND(AVG(basic_monthly_mean), 2) AS basic_mean,
            ROUND(AVG(basic_monthly_median), 2) AS basic_median,
            ROUND(AVG(gross_mthly_25_percentile), 2) AS gross_25th,
            ROUND(AVG(gross_mthly_75_percentile), 2) AS gross_75th
        FROM graduate_employment
        WHERE university = %s AND degree = %s
        GROUP BY year
        ORDER BY year;
    """

    cur.execute(query, (university, degree))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columns = [
        "Year",
        "Basic Mean",
        "Basic Median",
        "Gross 25th Percentile",
        "Gross 75th Percentile"
    ]
    df = pd.DataFrame(rows, columns=columns)
    return df

# =========================
# Employment Rate Trend Analysis
# =========================
def employment_trend(university=None, degree=None):
    """
    Show overall employment rates (and full-time permanent if available)
    over time, optionally filtered by university and/or degree.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            year,
            ROUND(AVG(employment_rate_overall), 2) AS overall_rate,
            ROUND(AVG(employment_rate_ft_perm), 2) AS ft_perm_rate
        FROM graduate_employment
        WHERE (%s IS NULL OR university = %s)
          AND (%s IS NULL OR degree = %s)
        GROUP BY year
        ORDER BY year;
    """

    cur.execute(query, (university, university, degree, degree))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columns = [
        "Year",
        "Overall Employment Rate",
        "Full-Time Permanent Employment Rate"
    ]
    df = pd.DataFrame(rows, columns=columns)
    return df

# =========================
# University Comparison Analysis
# =========================
def university_comparison(year, degree):
    """
    Compare median salaries and employment rates across universities for a given year and degree.
    Includes the degree (programme) column in the output.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            university,
            %s AS degree,
            ROUND(AVG(basic_monthly_median), 2) AS median_salary,
            ROUND(AVG(employment_rate_overall), 2) AS employment_rate
        FROM graduate_employment
        WHERE year = %s AND degree = %s
        GROUP BY university
        ORDER BY median_salary DESC;
    """

    cur.execute(query, (degree, year, degree))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columns = [
        "University",
        "Degree",
        "Median Salary",
        "Employment Rate"
    ]
    df = pd.DataFrame(rows, columns=columns)
    return df


# =========================
# TESTING
# =========================
if __name__ == "__main__":
    # -------------------------------
    # Salary Statistics Test
    # -------------------------------
    test_university = "Nanyang Technological University" # Hardcoded for testing
    test_degree = "Accountancy and Business" # Hardcoded for testing

    print("=== Salary Statistics Analysis ===")
    print(f"Selected University: {test_university}")
    print(f"Selected Degree (Programme): {test_degree}\n")

    salary_df = salary_statistics(test_university, test_degree)
    if salary_df.empty:
        print("No data found for the selected university/degree.\n")
    else:
        print(salary_df.to_string(index=False))
    print("\n" + "="*60 + "\n")

    # -------------------------------
    # Employment Trend Test
    # -------------------------------
    test_university = "Nanyang Technological University" # Hardcoded for testing
    test_degree = None  # None means all degrees Hardcoded for testing

    print("=== Employment Rate Trend Analysis ===")
    print(f"Selected University: {test_university}")
    print(f"Selected Degree (Programme): {test_degree}\n")

    emp_df = employment_trend(test_university, test_degree)
    if emp_df.empty:
        print("No employment data found for the selected filters.\n")
    else:
        print(emp_df.to_string(index=False))
    print("\n" + "="*60 + "\n")

    # -------------------------------
    # University Comparison Test
    # -------------------------------
    test_year = 2013 # Hardcoded for testing
    test_degree = "Accountancy and Business" # Hardcoded for testing

    print("=== University Comparison Analysis ===")
    print(f"Selected Year: {test_year}")
    print(f"Selected Degree (Programme): {test_degree}\n")

    uni_comp_df = university_comparison(test_year, test_degree)
    if uni_comp_df.empty:
        print("No data found for the selected year/degree.\n")
    else:
        print(uni_comp_df.to_string(index=False))
    print("\n" + "="*60 + "\n")
