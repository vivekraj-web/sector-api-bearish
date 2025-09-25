# Use Python from GitHub Container Registry instead of Docker Hub
FROM ghcr.io/astral-sh/python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sector_api_modified.py .

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "sector_api_modified:app", "--host", "0.0.0.0", "--port", "8000"]
