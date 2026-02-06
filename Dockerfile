# Use official Python 3.12 image
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy project files
COPY . /app

# Install virtual environment and dependencies
RUN python -m venv .venv
RUN . .venv/bin/activate && pip install --upgrade pip
RUN . .venv/bin/activate && pip install -r requirements.txt

# Expose port 5000 (Flask default)
EXPOSE 5000

# Run Flask app with Gunicorn
CMD ["/bin/bash", "-c", ". .venv/bin/activate && gunicorn -w 4 -b 0.0.0.0:5000 src.app:app"]
