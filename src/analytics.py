import psycopg2
import pandas as pd
import os

# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    """Establish PostgreSQL database connection using environment variables only"""
    try:
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "5432")),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            sslmode="require"
        )
        return conn
    except KeyError as e:
        print(f"❌ Missing required environment variable: {e}")
        return None
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


# =========================
# ANALYTICS FUNCTIONS
# =========================

def salary_statistics(university, degree):
    """
    Return mean and median salaries over time for a university and degree.
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
        FROM graduate
        WHERE university = %s
          AND degree = %s
        ORDER BY year;
    """
    cur.execute(query, (university, degree))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "year",
        "basic_monthly_mean",
        "basic_monthly_median",
        "gross_mthly_25_percentile",
        "gross_mthly_75_percentile"
    ])
    return df


def employment_trend(universities=None, degrees=None):
    """
    Return employment rate trends over time.
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
        FROM graduate
        WHERE (%s IS NULL OR university = ANY(%s))
          AND (%s IS NULL OR degree = ANY(%s))
        ORDER BY year, university, degree;
    """
    cur.execute(query, (universities, universities, degrees, degrees))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "year",
        "university",
        "degree",
        "employment_rate_overall",
        "employment_rate_ft_perm"
    ])
    return df


def university_comparison(year=None, degrees=None):
    """
    Compare median salary and employment rate across universities.
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
        FROM graduate
        WHERE (%s IS NULL OR year = %s)
          AND (%s IS NULL OR degree = ANY(%s))
        ORDER BY year, degree, basic_monthly_median DESC;
    """
    cur.execute(query, (year, year, degrees, degrees))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "year",
        "university",
        "degree",
        "basic_monthly_median",
        "employment_rate_overall"
    ])
    return df

# =========================
# HELPER FUNCTIONS
# =========================

def resolve_university(keyword):
    """
    Return list of universities matching the keyword.
    """
    if not keyword or keyword.lower() == "all":
        return None  # no filter for "all"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT university
        FROM graduate
        WHERE university ILIKE %s
        ORDER BY university;
    """, (f"%{keyword}%",))
    results = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    return results if results else "NOT_FOUND"


def resolve_degree(keyword):
    """
    Return list of degrees matching the keyword.
    """
    if not keyword or keyword.lower() == "all":
        return None  # no filter for "all"

    conn = get_connection()
    cur = conn.cursor()

    # Exact match first
    cur.execute("""
        SELECT DISTINCT degree
        FROM graduate
        WHERE degree = %s
        ORDER BY degree;
    """, (keyword,))
    exact = [row[0] for row in cur.fetchall()]
    if exact:
        cur.close()
        conn.close()
        return exact

    # Fuzzy match if exact not found
    cur.execute("""
        SELECT DISTINCT degree
        FROM graduate
        WHERE degree ILIKE %s
        ORDER BY degree;
    """, (f"%{keyword}%",))
    fuzzy = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return fuzzy if fuzzy else "NOT_FOUND"
