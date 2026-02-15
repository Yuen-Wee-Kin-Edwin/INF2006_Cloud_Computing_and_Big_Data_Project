import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, send_from_directory, jsonify, request, session, redirect, url_for, flash
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import secrets
from functools import wraps
import boto3
from io import StringIO


from preprocessing import load_csv, preprocess_data
from analytics import salary_statistics, employment_trend, university_comparison, resolve_university, resolve_degree

# =========================
# FLASK APP CONFIGURATION
# =========================
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# =========================
# LOAD CSV FROM S3
# =========================
df = None

S3_BUCKET = os.getenv("S3_BUCKET", "edwin-daaas-csv")
S3_KEY = os.getenv("S3_KEY", "GraduateEmploymentSurveyNTUNUSSITSMUSUSSSUTD.csv")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def load_csv_from_s3(bucket: str, key: str, region: str = "us-east-1") -> pd.DataFrame:
    s3 = boto3.client("s3", region_name=region)
    obj = s3.get_object(Bucket=bucket, Key=key)
    csv_content = obj["Body"].read().decode("utf-8")
    return pd.read_csv(StringIO(csv_content))

try:
    print(f"📦 Loading CSV from S3: s3://{S3_BUCKET}/{S3_KEY}")
    df = load_csv_from_s3(S3_BUCKET, S3_KEY, AWS_REGION)
    print("✅ CSV loaded from S3 successfully:", df.shape)
except Exception as e:
    print("❌ Failed to load CSV from S3:", e)
    df = None

# =========================
# DATABASE HELPER FUNCTIONS
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


def hash_password(password, salt=None):
    """Hash password with salt using SHA-256"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pwd_hash, salt

# =========================
# AUTHENTICATION DECORATOR
# =========================
def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to require specific role(s) for protected routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =========================
# MAIN ROUTES
# =========================
@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page - shows analytics overview"""
    return render_template('dashboard.html')

# =========================
# STATIC FILE SERVING
# =========================
@app.route('/components/<path:filename>')
def components(filename):
    return send_from_directory('components', filename)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# =========================
# AUTHENTICATION ROUTES
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'danger')
            return render_template('login.html')
        
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, username, email, password_hash, salt, role FROM users WHERE email = %s;", (email,))
            user = cur.fetchone()

            if user:
                user_id, username, user_email, stored_hash, salt, role = user
                pwd_hash, _ = hash_password(password, salt)

                if pwd_hash == stored_hash:
                    session['user_id'] = user_id
                    session['username'] = username
                    session['role'] = role
                    flash(f'Welcome back, {username}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Incorrect password.', 'danger')
            else:
                flash('No account found with that email.', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login.', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page route"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'graduate')  # Default role is 'graduate'

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # Validate role
        valid_roles = ['graduate', 'policymaker', 'admin']
        if role not in valid_roles:
            role = 'graduate'

        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again later.', 'danger')
            return render_template('register.html')
        
        cur = conn.cursor()
        try:
            pwd_hash, salt = hash_password(password)
            cur.execute(
                "INSERT INTO users (username, email, password_hash, salt, role) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                (username, email, pwd_hash, salt, role)
            )
            user_id = cur.fetchone()[0]
            conn.commit()

            session['user_id'] = user_id
            session['username'] = username
            session['role'] = role
            flash('Registration successful! Welcome aboard!', 'success')
            return redirect(url_for('dashboard'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Username or email already exists.', 'danger')
        except Exception as e:
            conn.rollback()
            print(f"Registration error: {e}")
            flash('An error occurred during registration.', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout route"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('index'))

# =========================
# ANALYTICS PAGES
# =========================
@app.route('/salary-details')
@login_required
def salary_details():
    """Salary details analytics page"""
    return render_template('salary_details.html')

@app.route('/university-details')
@login_required
def university_details():
    """University comparison analytics page"""
    return render_template('university_details.html')

@app.route('/employment-details')
@login_required
def employment_details():
    """Employment analytics page"""
    return render_template('employment_details.html')

# =========================
# API ENDPOINTS - FILTERS
# =========================
@app.route('/api/filters')
def get_filters():
    """Get all available filter options (years, universities, schools, degrees)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get unique years
        cur.execute("SELECT DISTINCT year FROM graduate WHERE year IS NOT NULL ORDER BY year DESC;")
        years = [row[0] for row in cur.fetchall()]
        
        # Get unique universities
        cur.execute("SELECT DISTINCT university FROM graduate WHERE university IS NOT NULL ORDER BY university;")
        universities = [row[0] for row in cur.fetchall()]
        
        # Get unique schools
        cur.execute("SELECT DISTINCT school FROM graduate WHERE school IS NOT NULL ORDER BY school;")
        schools = [row[0] for row in cur.fetchall()]
        
        # Get unique degrees
        cur.execute("SELECT DISTINCT degree FROM graduate WHERE degree IS NOT NULL ORDER BY degree;")
        degrees = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'years': years,
            'universities': universities,
            'schools': schools,
            'degrees': degrees
        })
    except Exception as e:
        print(f"Error fetching filters: {e}")
        return jsonify({'error': 'Failed to fetch filter options'}), 500

# =========================
# API ENDPOINTS - SALARY ANALYTICS
# =========================
@app.route('/api/salary-details')
def salary_details_api():
    """
    Return per-degree salary data with optional filters
    Query params: year, university, school, degree
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic query
        query = """
            SELECT 
                year,
                university,
                school,
                degree,
                employment_rate_overall,
                employment_rate_ft_perm,
                basic_monthly_mean,
                basic_monthly_median,
                gross_monthly_mean,
                gross_monthly_median,
                gross_mthly_25_percentile,
                gross_mthly_75_percentile
            FROM graduate
            WHERE 1=1
        """
        params = []
        
        # Apply filters
        year = request.args.get('year')
        university = request.args.get('university')
        school = request.args.get('school')
        degree = request.args.get('degree')
        
        if year:
            query += " AND year = %s"
            params.append(int(year))
        if university:
            query += " AND university = %s"
            params.append(university)
        if school:
            query += " AND school = %s"
            params.append(school)
        if degree:
            query += " AND degree = %s"
            params.append(degree)
        
        query += " ORDER BY year DESC, university, degree;"
        
        cur.execute(query, params)
        data = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        print(f"Error in salary_details_api: {e}")
        return jsonify({'error': 'Failed to fetch salary data'}), 500

@app.route('/api/salary-statistics')
def salary_statistics_api():
    """
    Get salary statistics for specific university and degree over time
    Query params: university, degree
    """
    university = request.args.get('university')
    degree = request.args.get('degree')
    
    if not university or not degree:
        return jsonify({'error': 'Both university and degree parameters are required'}), 400
    
    try:
        # Use analytics function
        df_result = salary_statistics(university, degree)
        
        if df_result.empty:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No data found for the specified filters'
            })
        
        return jsonify({
            'success': True,
            'data': df_result.to_dict(orient='records')
        })
    except Exception as e:
        print(f"Error in salary_statistics_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/salary-summary')
def salary_summary_api():
    """
    Get summary statistics (highest median, average salary) with filters
    Query params: year, university
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        year = request.args.get('year')
        university = request.args.get('university')
        
        # Query for highest median salary
        query_highest = """
            SELECT 
                university,
                degree,
                gross_monthly_median
            FROM graduate
            WHERE gross_monthly_median IS NOT NULL
        """
        params = []
        
        if year:
            query_highest += " AND year = %s"
            params.append(int(year))
        if university:
            query_highest += " AND university = %s"
            params.append(university)
        
        query_highest += " ORDER BY gross_monthly_median DESC LIMIT 1;"
        
        cur.execute(query_highest, params)
        highest_median = cur.fetchone()
        
        # Query for average salary
        query_avg = """
            SELECT 
                AVG(gross_monthly_median) as average_salary,
                AVG(employment_rate_overall) as average_employment_rate
            FROM graduate
            WHERE gross_monthly_median IS NOT NULL
        """
        params_avg = []
        
        if year:
            query_avg += " AND year = %s"
            params_avg.append(int(year))
        if university:
            query_avg += " AND university = %s"
            params_avg.append(university)
        
        cur.execute(query_avg, params_avg)
        averages = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'highest_median': highest_median,
            'averages': averages
        })
    except Exception as e:
        print(f"Error in salary_summary_api: {e}")
        return jsonify({'error': 'Failed to fetch salary summary'}), 500

# =========================
# API ENDPOINTS - EMPLOYMENT ANALYTICS
# =========================
@app.route('/api/employment-details')
def employment_details_api():
    """
    Return employment data with optional filters
    Query params: year, university, school, degree
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                year,
                university,
                school,
                degree,
                employment_rate_overall,
                employment_rate_ft_perm,
                gross_monthly_median
            FROM graduate
            WHERE employment_rate_overall IS NOT NULL
        """
        params = []
        
        year = request.args.get('year')
        university = request.args.get('university')
        school = request.args.get('school')
        degree = request.args.get('degree')
        
        if year:
            query += " AND year = %s"
            params.append(int(year))
        if university:
            query += " AND university = %s"
            params.append(university)
        if school:
            query += " AND school = %s"
            params.append(school)
        if degree:
            query += " AND degree = %s"
            params.append(degree)
        
        query += " ORDER BY year DESC, employment_rate_overall DESC;"
        
        cur.execute(query, params)
        data = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        print(f"Error in employment_details_api: {e}")
        return jsonify({'error': 'Failed to fetch employment data'}), 500

@app.route('/api/employment-trend')
def employment_trend_api():
    """
    Get employment trend over time for specific universities/degrees
    Query params: university (optional), degree (optional)
    """
    university = request.args.get('university', 'all')
    degree = request.args.get('degree', 'all')
    
    try:
        # Resolve universities and degrees using analytics functions
        universities = resolve_university(university)
        degrees = resolve_degree(degree)
        
        if universities == "NOT_FOUND":
            return jsonify({'error': 'University not found'}), 404
        if degrees == "NOT_FOUND":
            return jsonify({'error': 'Degree not found'}), 404
        
        # Use analytics function
        df_result = employment_trend(universities, degrees)
        
        if df_result.empty:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No data found for the specified filters'
            })
        
        return jsonify({
            'success': True,
            'data': df_result.to_dict(orient='records')
        })
    except Exception as e:
        print(f"Error in employment_trend_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/employment-summary')
def employment_summary_api():
    """
    Get employment summary statistics with filters
    Query params: year, university
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        year = request.args.get('year')
        university = request.args.get('university')
        
        query = """
            SELECT 
                AVG(employment_rate_overall) as avg_employment_rate,
                AVG(employment_rate_ft_perm) as avg_ft_perm_rate,
                MAX(employment_rate_overall) as max_employment_rate,
                MIN(employment_rate_overall) as min_employment_rate
            FROM graduate
            WHERE employment_rate_overall IS NOT NULL
        """
        params = []
        
        if year:
            query += " AND year = %s"
            params.append(int(year))
        if university:
            query += " AND university = %s"
            params.append(university)
        
        cur.execute(query, params)
        summary = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        print(f"Error in employment_summary_api: {e}")
        return jsonify({'error': 'Failed to fetch employment summary'}), 500

# =========================
# API ENDPOINTS - UNIVERSITY COMPARISON
# =========================
@app.route('/api/university-comparison')
def university_comparison_api():
    """
    Compare universities for specific year and/or degree
    Query params: year (optional), degree (optional)
    """
    year_input = request.args.get('year')
    year = int(year_input) if year_input else None
    degree = request.args.get('degree', 'all')
    
    try:
        degrees = resolve_degree(degree)
        
        if degrees == "NOT_FOUND":
            return jsonify({'error': 'Degree not found'}), 404
        
        # Use analytics function
        df_result = university_comparison(year, degrees)
        
        if df_result.empty:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No data found for the specified filters'
            })
        
        return jsonify({
            'success': True,
            'data': df_result.to_dict(orient='records')
        })
    except Exception as e:
        print(f"Error in university_comparison_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/university-details') 
def university_details_api(): 
    """ 
    Return per-university aggregated data with filters 
    Query params: year, university 
    """ 
    conn = get_db_connection() 
    if not conn: 
        return jsonify({'error': 'Database connection failed'}), 500 
     
    try: 
        cur = conn.cursor(cursor_factory=RealDictCursor) 
         
        query = """ 
            SELECT  
                year, 
                university, 
                degree, 
                school, 
                employment_rate_overall, 
                employment_rate_ft_perm, 
                gross_monthly_median, 
                gross_monthly_mean 
            FROM graduate 
            WHERE 1=1 
        """ 
        params = [] 
         
        year = request.args.get('year') 
        university = request.args.get('university') 
         
        if year: 
            query += " AND year = %s" 
            params.append(int(year)) 
        if university: 
            query += " AND university = %s" 
            params.append(university) 
         
        query += " ORDER BY university, gross_monthly_median DESC;" 
         
        cur.execute(query, params) 
        data = cur.fetchall() 
         
        cur.close() 
        conn.close() 
         
        return jsonify({ 
            'success': True, 
            'data': data, 
            'count': len(data) 
        }) 
    except Exception as e: 
        print(f"Error in university_details_api: {e}") 
        return jsonify({'error': 'Failed to fetch university data'}), 500

# =========================
# LEGACY API ENDPOINTS (for backwards compatibility)
# =========================
@app.route('/api/salary-data')
def salary_data():
    """Legacy endpoint - returns mock salary data"""
    return jsonify([
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
    ])

@app.route('/api/university-salary-data') 
def university_salary_data(): 
    """Legacy endpoint - returns aggregated university salary data""" 
    conn = get_db_connection() 
    if not conn: 
        return jsonify([]) 
     
    try: 
        cur = conn.cursor(cursor_factory=RealDictCursor) 
        cur.execute(""" 
            SELECT  
                year, 
                university, 
                AVG(gross_monthly_median) as gross_monthly_median 
            FROM graduate 
            WHERE gross_monthly_median IS NOT NULL 
            GROUP BY year, university 
            ORDER BY year, university; 
        """) 
        data = cur.fetchall() 
        cur.close() 
        conn.close() 
        return jsonify(data) 
    except Exception as e: 
        print(f"Error: {e}") 
        return jsonify([]) 
 
@app.route('/api/employment-rate-data') 
def employment_rate_data(): 
    """Legacy endpoint - returns aggregated employment rate data""" 
    conn = get_db_connection() 
    if not conn: 
        return jsonify([]) 
     
    try: 
        cur = conn.cursor(cursor_factory=RealDictCursor) 
        cur.execute(""" 
            SELECT  
                year, 
                university, 
                AVG(employment_rate_overall) as employment_rate_overall 
            FROM graduate 
            WHERE employment_rate_overall IS NOT NULL 
            GROUP BY year, university 
            ORDER BY year, university; 
        """) 
        data = cur.fetchall() 
        cur.close() 
        conn.close() 
        return jsonify(data) 
    except Exception as e: 
        print(f"Error: {e}") 
        return jsonify([])
    
# =========================
# DATABASE SETUP FUNCTIONS
# =========================
def create_tables():
    """Create all required database tables"""
    conn = get_db_connection()
    if not conn:
        print("Cannot create tables - no database connection")
        return
    
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(64) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'graduate' CHECK (role IN ('graduate', 'policymaker', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Graduate employment data table
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
    
    # Create indexes for better query performance
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_graduate_year ON graduate(year);
        CREATE INDEX IF NOT EXISTS idx_graduate_university ON graduate(university);
        CREATE INDEX IF NOT EXISTS idx_graduate_degree ON graduate(degree);
        CREATE INDEX IF NOT EXISTS idx_graduate_school ON graduate(school);
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ All tables created successfully")

def insert_graduate_data(df):
    """Insert graduate employment data from dataframe into database"""
    conn = get_db_connection()
    if not conn:
        print("Cannot insert data - no database connection")
        return
    
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
            row["university"] if pd.notna(row["university"]) else None,
            row["school"] if pd.notna(row["school"]) else None,
            row["degree"] if pd.notna(row["degree"]) else None,
            float(row["employment_rate_overall"]) if pd.notna(row["employment_rate_overall"]) else None,
            float(row["employment_rate_ft_perm"]) if pd.notna(row["employment_rate_ft_perm"]) else None,
            float(row["basic_monthly_mean"]) if pd.notna(row["basic_monthly_mean"]) else None,
            float(row["basic_monthly_median"]) if pd.notna(row["basic_monthly_median"]) else None,
            float(row["gross_monthly_mean"]) if pd.notna(row["gross_monthly_mean"]) else None,
            float(row["gross_monthly_median"]) if pd.notna(row["gross_monthly_median"]) else None,
            float(row["gross_mthly_25_percentile"]) if pd.notna(row["gross_mthly_25_percentile"]) else None,
            float(row["gross_mthly_75_percentile"]) if pd.notna(row["gross_mthly_75_percentile"]) else None
        ))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Inserted {len(df)} rows into graduate table")

def clean_graduate_data():
    """Clean graduate table data (remove trailing symbols)"""
    conn = get_db_connection()
    if not conn:
        return
    
    cur = conn.cursor()
    cur.execute("""
        UPDATE graduate
        SET 
            degree = TRIM(regexp_replace(degree, '[#^*]+', '', 'g')),
            university = TRIM(regexp_replace(university, '[#^*]+', '', 'g')),
            school = TRIM(regexp_replace(school, '[#^*]+', '', 'g'))
        WHERE 
            degree ~ '[#^*]' OR 
            university ~ '[#^*]' OR 
            school ~ '[#^*]';
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Graduate data cleaned")

def insert_sample_users():
    """Insert sample users for testing"""
    conn = get_db_connection()
    if not conn:
        return
    
    cur = conn.cursor()
    
    # Check if users already exist
    cur.execute("SELECT COUNT(*) FROM users;")
    count = cur.fetchone()[0]
    if count > 0:
        print("[INFO] Users table already has data. Skipping sample insert.")
        cur.close()
        conn.close()
        return
    
    # Sample users (username, email, plaintext password, role)
    sample_users = [
        ("graduate_user", "graduate@example.com", "password123", "graduate"),
        ("policy_user", "policy@example.com", "password123", "policymaker"),
        ("admin_user", "admin@example.com", "password123", "admin")
    ]
    
    insert_sql = """
        INSERT INTO users (username, email, password_hash, salt, role)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    for username, email, password, role in sample_users:
        pwd_hash, salt = hash_password(password)
        cur.execute(insert_sql, (username, email, pwd_hash, salt, role))
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Sample users inserted")

# =========================
# DEBUG/PREVIEW ROUTES
# =========================
@app.route('/preview-cleaned-data')
def preview_cleaned_data():
    """Preview cleaned CSV data as HTML table"""
    try:
        df_raw = load_csv(DATA_FILE)
        df_clean, _ = preprocess_data(df_raw)
        return df_clean.head(50).to_html(classes='table table-striped', index=False)
    except Exception as e:
        return f"<h3>Error:</h3><pre>{e}</pre>"

@app.route('/preview-cleaned-json')
def preview_cleaned_json():
    """Preview cleaned CSV data as JSON"""
    try:
        df_raw = load_csv(DATA_FILE)
        df_clean, _ = preprocess_data(df_raw)
        metadata = {
            'columns': df_clean.dtypes.apply(lambda x: str(x)).to_dict(),
            'null_counts': df_clean.isna().sum().to_dict(),
            'row_count': len(df_clean)
        }
        preview_data = df_clean.head(10).to_dict(orient='records')
        return jsonify({'metadata': metadata, 'preview': preview_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users')
def preview_users():
    """Preview users table as HTML"""
    conn = get_db_connection()
    if not conn:
        return "<h3>Database connection error</h3>"
    
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            id, username, email, password_hash, role, created_at
        FROM users
        ORDER BY id
        LIMIT 50;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    df_users = pd.DataFrame(rows, columns=["id", "username", "email", "password_hash", "role", "created_at"])
    preview_html = df_users.to_html(classes='table table-striped', index=False)
    
    return f"<h2>Preview of Users Table</h2>{preview_html}"

@app.route('/graduate-table')
def preview_graduate_table():
    """Preview graduate table as HTML"""
    conn = get_db_connection()
    if not conn:
        return "<h3>Database connection error</h3>"
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM graduate LIMIT 50;")
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    
    df_preview = pd.DataFrame(rows, columns=colnames)
    preview_html = df_preview.to_html(classes='table table-striped', index=False)
    
    return f"<h2>Preview of Graduate Table (first 50 rows)</h2>{preview_html}"

# =========================
# ERROR HANDLERS
# =========================
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# =========================
# APPLICATION INITIALIZATION
# =========================
def initialize_app():
    """Initialize application - create tables and load data"""
    print("=" * 60)
    print("INITIALIZING APPLICATION")
    print("=" * 60)
    
    # Create all tables
    create_tables()
    
    # Check if graduate table has data
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM graduate;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count == 0:
            print("[INFO] Graduate table is empty. Loading CSV data from S3...")

            if df is not None:
                df_clean, _ = preprocess_data(df)
                insert_graduate_data(df_clean)
                clean_graduate_data()
                print("✅ S3 data loaded into database")
            else:
                print("❌ No CSV data available")

        else:
            print(f"[INFO] Graduate table already has {count} rows. Skipping CSV load.")
    
    # Insert sample users
    insert_sample_users()
    
    print("=" * 60)
    print("APPLICATION INITIALIZED")
    print("=" * 60)

# =========================
# MAIN ENTRY POINT
# =========================
if __name__ == '__main__':
    # Initialize the application
    initialize_app()
    
    # Get configuration from environment
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"\n🚀 Starting Flask server on {host}:{port}")
    print(f"   Debug mode: {debug_mode}")
    print(f"   Access at: http://localhost:{port}\n")
    
    app.run(debug=debug_mode, host=host, port=port)
