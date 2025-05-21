FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Copy requirements first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py

# Expose port
EXPOSE 5000

# Run gunicorn server with logging configuration
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--log-level", "info", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log", "main:app"]