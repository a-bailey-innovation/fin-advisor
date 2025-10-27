# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    wget \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Cloud SQL Auth Proxy (v2) with explicit PostgreSQL support
RUN wget https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64 -O cloud-sql-proxy \
    && chmod +x cloud-sql-proxy \
    && mv cloud-sql-proxy /usr/local/bin/

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Debug: List all files to see what was copied
RUN echo "=== Files in /app ===" && ls -la

# Debug: Check if startup.py exists and is readable
RUN echo "=== Checking startup.py ===" && ls -la startup.py && head -5 startup.py

# Make startup script executable
RUN chmod +x startup.py

# Debug: Verify startup.py is executable
RUN echo "=== Verifying startup.py permissions ===" && ls -la startup.py

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Run the application with direct database connection
CMD ["sh", "-c", "echo 'Starting container...' && echo 'Starting FastAPI server with direct database connection...' && python3 -m uvicorn http_server:app --host 0.0.0.0 --port 8080"]

