FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Python dependencies first (wheels available for all packages)
# NOTE: If build fails with pthread_create error on Windows, run:
#   set DOCKER_BUILDKIT=0
#   docker build -t binance-dcr-bot .
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create directories for data persistence
RUN mkdir -p /app/logs /app/data/historical /app/charts_output

EXPOSE 5000

# Default command runs dashboard mode
CMD ["python", "main.py", "--mode", "dashboard", "--port", "5000"]
