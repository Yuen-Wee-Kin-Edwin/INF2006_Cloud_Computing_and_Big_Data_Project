import os
import pandas as pd
from flask import Flask, render_template, send_from_directory

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


@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')


if __name__ == '__main__':
    # Debug mode should only be enabled in development

    # Set FLASK_DEBUG=1 environment variable to enable debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host="0.0.0.0", port=80)
