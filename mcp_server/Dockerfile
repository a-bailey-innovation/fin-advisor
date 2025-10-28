# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Run the application with direct database connection
CMD ["sh", "-c", "echo 'Starting container...' && echo 'Starting FastAPI server with direct database connection...' && python3 -m uvicorn http_server:app --host 0.0.0.0 --port 8080"]

