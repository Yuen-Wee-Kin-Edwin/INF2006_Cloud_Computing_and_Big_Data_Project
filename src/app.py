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


if __name__ == '__main__':
    # Debug mode should only be enabled in development

    # Set FLASK_DEBUG=1 environment variable to enable debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host="0.0.0.0", port=80)
