import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, send_from_directory, jsonify, request
from datetime import datetime

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

DATA_FILE='./data/GraduateEmploymentSurveyNTUNUSSITSMUSUSSSUTD.csv'
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


@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')


if __name__ == '__main__':
    # Debug mode should only be enabled in development

    # Set FLASK_DEBUG=1 environment variable to enable debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host="0.0.0.0", port=80)
