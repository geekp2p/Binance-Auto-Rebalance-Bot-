# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python dependencies
# Using --no-compile and single-threaded pip to avoid resource exhaustion on Windows Docker
COPY requirements.txt /app/
RUN pip install --no-compile -r requirements.txt && \
    find /usr/local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Copy application code and create directories in single layer
COPY . /app/
RUN mkdir -p /app/logs /app/data/historical /app/charts_output

EXPOSE 5000

# Default command runs dashboard mode
CMD ["python", "main.py", "--mode", "dashboard", "--port", "5000"]
