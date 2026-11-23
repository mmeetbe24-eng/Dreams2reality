# Dockerfile for Dreams2Reality Multi-User BCI Platform
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and clinical benchmarks
COPY bci-service/ ./bci-service/
COPY frontend/ ./frontend/
COPY Dataset/ ./Dataset/
COPY main.py .

# Expose default port
EXPOSE 8000

ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Run via main.py which dynamically binds to cloud $PORT
CMD ["python", "main.py"]
