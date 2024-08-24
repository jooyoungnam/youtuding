FROM python:3.9-slim

# Install necessary packages including ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure necessary directories exist and have correct permissions
RUN mkdir -p downloads && mkdir -p /app/db && chmod -R 777 downloads && chmod -R 777 /app/db

# Start Celery worker and Flask application with Gunicorn
CMD celery -A app.celery worker --loglevel=info & gunicorn -w 4 -b 0.0.0.0:8000 --timeout 600 app:app
