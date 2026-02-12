import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, send_from_directory, jsonify, request
from datetime import datetime

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

df = None
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'GraduateEmploymentSurveyNTUNUSSITSMUSUSSSUTD.csv')
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/components/<path:filename>')
def components(filename):
    return send_from_directory('components', filename)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

def get_salary_data():
    return [
        {
            "year": 2020,
            "gross_monthly_mean": 4500,
            "gross_monthly_median": 4200,
            "gross_mthly_25_percentile": 3500,
            "gross_mthly_75_percentile": 5200
        },
        {
            "year": 2021,
            "gross_monthly_mean": 4700,
            "gross_monthly_median": 4400,
            "gross_mthly_25_percentile": 3700,
            "gross_mthly_75_percentile": 5500
        },
        {
            "year": 2022,
            "gross_monthly_mean": 5000,
            "gross_monthly_median": 4700,
            "gross_mthly_25_percentile": 4000,
            "gross_mthly_75_percentile": 5800
        },
        {
            "year": 2023,
            "gross_monthly_mean": 5200,
            "gross_monthly_median": 4900,
            "gross_mthly_25_percentile": 4200,
            "gross_mthly_75_percentile": 6000
        },
        {
            "year": 2024,
            "gross_monthly_mean": 5500,
            "gross_monthly_median": 5200,
            "gross_mthly_25_percentile": 4500,
            "gross_mthly_75_percentile": 6300
        }
    ]

@app.route('/api/salary-data')
def salary_data():
    return jsonify(get_salary_data())

@app.route('/api/university-salary-data')
def university_salary_data():
    if df is not None:
        # Ensure 'gross_monthly_median' is numeric, coercing errors
        df['gross_monthly_median'] = pd.to_numeric(df['gross_monthly_median'], errors='coerce')
        
        # Drop rows where median is NaN after coercion
        df_cleaned = df.dropna(subset=['gross_monthly_median'])
        
        # Group by year and university, then calculate the median of the 'gross_monthly_median'
        uni_salary_data = df_cleaned.groupby(['year', 'university'])['gross_monthly_median'].median().reset_index()
        
        return jsonify(uni_salary_data.to_dict(orient='records'))
    return jsonify([])

@app.route('/api/employment-rate-data')
def employment_rate_data():
    if df is not None:
        # Ensure 'employment_rate_overall' is numeric, coercing errors
        df['employment_rate_overall'] = pd.to_numeric(df['employment_rate_overall'], errors='coerce')
        
        # Drop rows where employment rate is NaN after coercion
        df_cleaned = df.dropna(subset=['employment_rate_overall'])
        
        # Group by year and university, then calculate the mean of the 'employment_rate_overall'
        employment_data = df_cleaned.groupby(['year', 'university'])['employment_rate_overall'].mean().reset_index()
        
        return jsonify(employment_data.to_dict(orient='records'))
    return jsonify([])

@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')

@app.route('/salary-details')
def salary_details():
    """Salary details analytics page"""
    return render_template('salary_details.html')

@app.route('/api/salary-details')
def salary_details_api():
    """Return per-degree salary data with optional year/university filters"""
    if df is not None:
        result = df.copy()

        # Coerce numeric columns
        numeric_cols = ['gross_monthly_mean', 'gross_monthly_median',
                        'gross_mthly_25_percentile', 'gross_mthly_75_percentile',
                        'basic_monthly_mean', 'basic_monthly_median',
                        'employment_rate_overall', 'employment_rate_ft_perm']
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors='coerce')

        # Optional filters
        year = request.args.get('year')
        university = request.args.get('university')
        school = request.args.get('school')

        if year:
            result = result[result['year'] == int(year)]
        if university:
            result = result[result['university'] == university]
        if school:
            result = result[result['school'] == school]

        result = result.dropna(subset=['gross_monthly_median'])

        return jsonify({
            'data': result.to_dict(orient='records'),
            'years': sorted(df['year'].dropna().unique().tolist()),
            'universities': sorted(df['university'].dropna().unique().tolist()),
            'schools': sorted(df['school'].dropna().unique().tolist()),
        })
    return jsonify({'data': [], 'years': [], 'universities': [], 'schools': []})

@app.route('/university-details')
def university_details():
    """University comparison analytics page"""
    return render_template('university_details.html')

@app.route('/api/university-details')
def university_details_api():
    """Return per-degree data grouped by university with optional filters"""
    if df is not None:
        result = df.copy()
        numeric_cols = ['gross_monthly_mean', 'gross_monthly_median',
                        'gross_mthly_25_percentile', 'gross_mthly_75_percentile',
                        'basic_monthly_mean', 'basic_monthly_median',
                        'employment_rate_overall', 'employment_rate_ft_perm']
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors='coerce')

        year = request.args.get('year')
        university = request.args.get('university')
        if year:
            result = result[result['year'] == int(year)]
        if university:
            result = result[result['university'] == university]

        result = result.dropna(subset=['gross_monthly_median'])

        return jsonify({
            'data': result.to_dict(orient='records'),
            'years': sorted(df['year'].dropna().unique().tolist()),
            'universities': sorted(df['university'].dropna().unique().tolist()),
        })
    return jsonify({'data': [], 'years': [], 'universities': []})

@app.route('/employment-details')
def employment_details():
    """Employment analytics page"""
    return render_template('employment_details.html')

@app.route('/api/employment-details')
def employment_details_api():
    """Return employment data with optional filters"""
    if df is not None:
        result = df.copy()
        numeric_cols = ['employment_rate_overall', 'employment_rate_ft_perm',
                        'gross_monthly_mean', 'gross_monthly_median']
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors='coerce')

        year = request.args.get('year')
        university = request.args.get('university')
        if year:
            result = result[result['year'] == int(year)]
        if university:
            result = result[result['university'] == university]

        result = result.dropna(subset=['employment_rate_overall'])

        return jsonify({
            'data': result.to_dict(orient='records'),
            'years': sorted(df['year'].dropna().unique().tolist()),
            'universities': sorted(df['university'].dropna().unique().tolist()),
        })
    return jsonify({'data': [], 'years': [], 'universities': []})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route"""
    if request.method == 'POST':
        # Handle login logic here
        pass
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page route"""
    if request.method == 'POST':
        # Handle registration logic here
        pass
    return render_template('register.html')

# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    print("✅ Connected to PostgreSQL successfully!")
    return conn

# =========================
# CREATE TABLES
# =========================
def create_users_table():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('graduate', 'policymaker', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Users table ensured")


def create_graduate_employment_table():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS graduate_employment (
            year INT,
            university VARCHAR(255),
            school VARCHAR(255),
            degree VARCHAR(255),
            employment_rate_overall FLOAT,
            employment_rate_ft_perm FLOAT,
            basic_monthly_mean FLOAT,
            basic_monthly_median FLOAT,
            gross_monthly_mean FLOAT,
            gross_monthly_median FLOAT,
            gross_mthly_25_percentile FLOAT,
            gross_mthly_75_percentile FLOAT
        );
    """)
    

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Graduate employment table ensured")

def create_graduate_table():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS graduate (
            id SERIAL PRIMARY KEY,
            year INT,
            university VARCHAR(255),
            school VARCHAR(255),
            degree VARCHAR(255),
            employment_rate_overall FLOAT,
            employment_rate_ft_perm FLOAT,
            basic_monthly_mean FLOAT,
            basic_monthly_median FLOAT,
            gross_monthly_mean FLOAT,
            gross_monthly_median FLOAT,
            gross_mthly_25_percentile FLOAT,
            gross_mthly_75_percentile FLOAT
        );
    """)
    

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Graduate table ensured")

# =========================
# INSERT DATA
# =========================
def insert_graduate_data(df):
    conn = get_db_connection()
    cur = conn.cursor()

    insert_sql = """
        INSERT INTO graduate (
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
    print(f"✅ Inserted {len(df)} rows into graduate table")


def insert_sample_users():
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if table already has data
    cur.execute("SELECT COUNT(*) FROM users;")
    count = cur.fetchone()[0]
    if count > 0:
        print("[INFO] Users table already has data. Skipping sample insert.")
        cur.close()
        conn.close()
        return

    # Sample users
    sample_users = [
        ("grad_user", "grad@gmail.com", "password123", "graduate"),
        ("policy_user", "policy@gmail.com", "password123", "policymaker"),
        ("admin_user", "admin@gmail.com", "password123", "admin")
    ]

    insert_sql = """
        INSERT INTO users (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """

    for user in sample_users:
        cur.execute(insert_sql, user)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Sample users inserted")

# =========================
# CLEAN GRADUATE TABLE IN PLACE
# =========================
def clean_graduate_employment_table():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE graduate
        SET degree = regexp_replace(degree, '^[\s\#\^\*]+|[\s\#\^\*]+$', '', 'g'),
            university = regexp_replace(university, '^[\s\#\^\*]+|[\s\#\^\*]+$', '', 'g');
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("[INFO] Trailing symbols removed from graduate_employment table!")




# =========================
# APP ROUTES (preview / test)
# =========================
@app.route('/preview-cleaned-data')
def preview_cleaned_data():
    try:
        df_raw = load_csv(DATA_FILE)
        df_clean, _ = preprocess_data(df_raw)
        return df_clean.to_html(classes='table table-striped', index=False)
    except Exception as e:
        return f"<h3>Error:</h3><pre>{e}</pre>"

@app.route('/preview-cleaned-json')
def preview_cleaned_json():
    df_raw = load_csv(DATA_FILE)
    df_clean, _ = preprocess_data(df_raw)
    metadata = {
        'columns': df_clean.dtypes.apply(lambda x: str(x)).to_dict(),
        'null_counts': df_clean.isna().sum().to_dict(),
        'row_count': len(df_clean)
    }
    preview_data = df_clean.head(10).to_dict(orient='records')
    return jsonify({'metadata': metadata, 'preview': preview_data})

@app.route('/users')
def preview_users():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all users (or limit to first 20 for sanity)
    cur.execute("SELECT id, username, email, role, created_at FROM users ORDER BY id LIMIT 20;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convert to pandas DataFrame for a nice HTML table
    df_users = pd.DataFrame(rows, columns=["id", "username", "email", "role", "created_at"])

    # Render as HTML table
    preview_html = df_users.to_html(classes='table table-striped', index=False)

    return f"<h2>Preview of Users Table</h2>{preview_html}"

@app.route('/graduate-table')
def preview_graduate_table():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch first 10 rows from graduate table
    cur.execute("SELECT * FROM graduate;")
    rows = cur.fetchall()
    
    # Get column names
    colnames = [desc[0] for desc in cur.description]
    
    cur.close()
    conn.close()
    
    # Convert to Pandas DataFrame for easy HTML table
    df_preview = pd.DataFrame(rows, columns=colnames)
    preview_html = df_preview.to_html(classes='table table-striped', index=False)
    
    return f"<h2>Preview of Graduate Table (first 10 rows)</h2>{preview_html}"

# =========================
# ANALYTICS HELPER FUNCTIONS
# =========================
@app.route('/analytics/salary')
def analytics_salary():
    uni_kw = request.args.get('university', 'all')  # default = 'all'
    deg_kw = request.args.get('degree', 'all')      # default = 'all'

    universities = resolve_university(uni_kw)
    degrees = resolve_degree(deg_kw)

    if universities == "NOT_FOUND":
        return jsonify({"error": "University not found"}), 404
    if degrees == "NOT_FOUND":
        return jsonify({"error": "Degree not found"}), 404

    # Support multiple universities/degrees if 'all'
    if len(universities) > 1 or len(degrees) > 1:
        return jsonify({"error": "Multiple universities/degrees matched. Please specify one."}), 400

    df = salary_statistics(universities[0], degrees[0])
    return df.to_html(classes='table table-striped', index=False)

@app.route('/analytics/salary-form')
def analytics_salary_form():
    # Load unique universities and degrees from the DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT university FROM graduate;")
    universities = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT degree FROM graduate;")
    degrees = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    html = "<h2>Salary Analytics Preview</h2>"
    html += "<form action='/analytics/salary' method='get'>"
    html += "University: <select name='university'>"
    for u in universities:
        html += f"<option value='{u}'>{u}</option>"
    html += "</select><br>"

    html += "Degree: <select name='degree'>"
    for d in degrees:
        html += f"<option value='{d}'>{d}</option>"
    html += "</select><br><br>"

    html += "<input type='submit' value='View Salary'>"
    html += "</form>"

    return html

@app.route('/analytics/employment')
def analytics_employment():
    uni_kw = request.args.get('university', 'all')
    deg_kw = request.args.get('degree', 'all')

    universities = resolve_university(uni_kw)
    degrees = resolve_degree(deg_kw)

    # 'all' case returns None, which is valid
    if universities == "NOT_FOUND":
        return jsonify({"error": "No university matched"}), 404
    if degrees == "NOT_FOUND":
        return jsonify({"error": "No degree matched"}), 404

    df = employment_trend(universities, degrees)
    return df.to_html(classes='table table-striped', index=False)


@app.route('/analytics/university-comparison')
def analytics_comparison():
    year_input = request.args.get('year')
    year = int(year_input) if year_input else None
    deg_kw = request.args.get('degree', 'all')

    degrees = resolve_degree(deg_kw)
    if degrees == "NOT_FOUND":
        return jsonify({"error": "No degree matched"}), 404

    df = university_comparison(year, degrees)
    return df.to_html(classes='table table-striped', index=False)

# =========================
# MAIN APP ENTRY
# =========================

if __name__ == '__main__':
    # Debug mode should only be enabled in development
    create_users_table()               # Users table
    create_graduate_table()            # App-facing graduate table
    create_graduate_employment_table() # Optional CSV backup

    # 2️⃣ Load CSV and insert into app-facing table only if empty
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM graduate;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    if count == 0:
        print("[INFO] Graduate table empty. Loading CSV...")
        df_raw = load_csv(DATA_FILE)
        df_clean, _ = preprocess_data(df_raw)

        # Insert into app-facing table
        insert_graduate_data(df_clean)
        clean_graduate_employment_table()  # Clean the graduate table
    else:
        print("[INFO] Graduate table already has data. Skipping CSV load.")

    # 3️⃣ Insert sample users if table empty
    insert_sample_users()

    # Set FLASK_DEBUG=1 environment variable to enable debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host="0.0.0.0", port=80)
