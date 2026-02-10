import psycopg2
import pandas as pd
from tabulate import tabulate

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
# SALARY STATISTICS ANALYSIS
# =========================
def salary_statistics(university, degree):
    """
    Display mean and median salaries over time for a selected university and degree.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            year,
            basic_monthly_mean,
            basic_monthly_median,
            gross_mthly_25_percentile,
            gross_mthly_75_percentile
        FROM graduate_employment
        WHERE university = %s
          AND degree = %s
        ORDER BY year;
    """

    cur.execute(query, (university, degree))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "Year",
        "Basic Mean Salary",
        "Basic Median Salary",
        "Gross 25th Percentile",
        "Gross 75th Percentile"
    ])

    return df

# =========================
# EMPLOYMENT RATE TREND ANALYSIS
# =========================
def employment_trend(university=None, degrees=None):
    """
    Show employment rate trends over time.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            year,
            university,
            degree,
            employment_rate_overall,
            employment_rate_ft_perm
        FROM graduate_employment
        WHERE (%s IS NULL OR university = ANY(%s))
          AND (%s IS NULL OR degree = ANY(%s))
        ORDER BY year, university, degree;
    """

    cur.execute(query, (
        university, university,
        degrees, degrees
    ))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return pd.DataFrame(rows, columns=[
        "Year",
        "University",
        "Degree",
        "Overall Employment Rate (%)",
        "Full-Time Permanent Rate (%)"
    ])

# =========================
# UNIVERSITY COMPARISON ANALYSIS
# =========================
def university_comparison(year=None, degrees=None):
    """
    Compare salaries and employment outcomes across universities.
    Can filter by year and/or degree(s).
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            year,
            university,
            degree,
            basic_monthly_median,
            employment_rate_overall
        FROM graduate_employment
        WHERE (%s IS NULL OR year = %s)
          AND (%s IS NULL OR degree = ANY(%s))
        ORDER BY year, degree, basic_monthly_median DESC;
    """

    cur.execute(query, (year, year, degrees, degrees))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return pd.DataFrame(rows, columns=[
        "Year",
        "University",
        "Degree",
        "Median Salary",
        "Employment Rate Overall (%)"
    ])

# =========================
# HELPER FUNCTIONS
# =========================
def resolve_university(keyword):
    if not keyword or keyword.lower() == "all":
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT university
        FROM graduate_employment
        WHERE university ILIKE %s
        ORDER BY university;
    """, (f"%{keyword}%",))

    results = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return results if results else "NOT_FOUND"

def resolve_degree(keyword):
    if not keyword or keyword.lower() == "all":
        return None  # no filter for "all"

    conn = get_connection()
    cur = conn.cursor()

    # First try exact match
    cur.execute("""
        SELECT DISTINCT degree
        FROM graduate_employment
        WHERE degree = %s
        ORDER BY degree;
    """, (keyword,))
    exact = [row[0] for row in cur.fetchall()]
    if exact:
        cur.close()
        conn.close()
        return exact

    # If no exact match, try fuzzy match (ILIKE)
    cur.execute("""
        SELECT DISTINCT degree
        FROM graduate_employment
        WHERE degree ILIKE %s
        ORDER BY degree;
    """, (f"%{keyword}%",))
    fuzzy = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return fuzzy if fuzzy else "NOT_FOUND"



# =========================
# OUTPUT FORMATTING
# =========================
def print_table(df, title=None):
    if title:
        print(title)
    print(tabulate(
        df,
        headers="keys",
        tablefmt="grid",
        showindex=False,
        colalign=("center",) * len(df.columns)
    ))

def print_test_context(analysis_name, params):
    print("\n" + "=" * 70)
    print(f"ANALYSIS TYPE : {analysis_name}")
    print("TEST PARAMETERS:")
    for k, v in params.items():
        print(f"  - {k}: {v}")
    print("=" * 70 + "\n")

# =========================
# MAIN MENU
# =========================
def main_menu():
    print("\nGRADUATE EMPLOYMENT ANALYTICS")
    print("1. Salary Statistics Analysis")
    print("2. Employment Rate Trend Analysis")
    print("3. University Comparison Analysis")
    print("0. Exit")
    return input("\nSelect an option: ").strip()

if __name__ == "__main__":

    while True:
        choice = main_menu()

        # =========================
        # 1. Salary Statistics
        # =========================
        if choice == "1":
            # User must select exactly one university
            uni_input = input("Enter University name: ").strip()
            universities = resolve_university(uni_input)
            if universities == "NOT_FOUND":
                print("No university matched your keyword.")
                continue
            elif len(universities) > 1:
                print(f"Multiple universities matched. Please type exactly: {', '.join(universities)}")
                continue
            university = universities[0]

            # User must select exactly one degree
            deg_input = input("Enter Degree name: ").strip()
            degrees = resolve_degree(deg_input)
            if degrees == "NOT_FOUND":
                print("No degree matched your keyword.")
                continue
            elif len(degrees) > 1:
                print(f"Multiple degrees matched. Please type exactly: {', '.join(degrees)}")
                continue
            degree = degrees[0]

            print_test_context(
                "Salary Statistics Analysis",
                {
                    "Selected University": university,
                    "Selected Degree": degree,
                    "Metrics": "Basic Mean, Basic Median, Gross 25th & 75th Percentile"
                }
            )

            df = salary_statistics(university, degree)
            if df.empty:
                print("No data found.\n")
            else:
                print_table(df)


        # =========================
        # 2. Employment Trend Analysis
        # =========================
        elif choice == "2":
            uni_input = input("Enter University keyword (or 'all'): ").strip()
            deg_input = input("Enter Degree keyword (or 'all'): ").strip()

            universities = resolve_university(uni_input)
            degrees = resolve_degree(deg_input)

            if universities == "NOT_FOUND":
                print("No university matched your keyword.")
                continue

            if degrees == "NOT_FOUND":
                print("No degree matched your keyword.")
                continue

            print_test_context(
                "Employment Rate Trend Analysis",
                {
                    "University Filter": ', '.join(universities) if universities else "ALL",
                    "Degree Filter": ', '.join(degrees) if degrees else "ALL",
                }
            )

            df = employment_trend(universities, degrees)
            if df.empty:
                print("No data found.\n")
            else:
                print_table(df)

        # =========================
        # 3. University Comparison Analysis
        # =========================
        elif choice == "3":
            year_input = input("Enter Year (press Enter for all): ").strip()
            year = int(year_input) if year_input else None

            deg_input = input("Enter Degree keyword (or 'all'): ").strip()
            degrees = resolve_degree(deg_input)
            if degrees == "NOT_FOUND":
                print("No degree matched your keyword.")
                continue

            print_test_context(
                "University Comparison Analysis",
                {
                    "Year": year or "ALL",
                    "Degree Filter": ', '.join(degrees) if degrees else "ALL",
                    "Metrics": "Median Salary & Employment Rate"
                }
            )

            df = university_comparison(year, degrees)
            if df.empty:
                print("No data found.\n")
            else:
                print_table(df)

        # =========================
        # 0. Exit
        # =========================
        elif choice == "0":
            print("Exiting analytics. Goodbye.")
            break

        else:
            print("Invalid option. Please try again.")

