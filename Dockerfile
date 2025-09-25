FROM python:3.11

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

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "sector_api_modified:app", "--host", "0.0.0.0", "--port", "8000"]
