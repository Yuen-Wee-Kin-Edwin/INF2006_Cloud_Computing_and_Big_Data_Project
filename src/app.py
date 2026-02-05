import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html')


if __name__ == '__main__':
    # Debug mode should only be enabled in development
    # Set FLASK_DEBUG=1 environment variable to enable debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode)
