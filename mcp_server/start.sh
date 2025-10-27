#!/bin/bash

echo "=== MCP Server Startup with Cloud SQL Proxy ==="
echo "CLOUD_RUN_MODE: $CLOUD_RUN_MODE"
echo "CLOUDSQL_CONNECTION_NAME: $CLOUDSQL_CONNECTION_NAME"
echo "DB_HOST: $DB_HOST"
echo "DB_PORT: $DB_PORT"
echo "All environment variables:"
env | grep -E "(CLOUD|SQL|DB)" | sort

# Function to cleanup background processes
cleanup() {
    echo "Shutting down..."
    if [ ! -z "$PROXY_PID" ]; then
        echo "Stopping Cloud SQL Proxy (PID: $PROXY_PID)"
        kill $PROXY_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start Cloud SQL Auth Proxy (v2) in the background
if [ -n "$CLOUDSQL_CONNECTION_NAME" ]; then
    echo "Starting Cloud SQL Auth Proxy (v2)..."
    echo "Connection: $CLOUDSQL_CONNECTION_NAME"
    echo "Proxy will listen on: 127.0.0.1:5432"
    
    # Start the proxy with proper configuration
    cloud-sql-proxy \
        --port 5432 \
        --address 127.0.0.1 \
        --auto-iam-authn \
        --enable-iam-login \
        "$CLOUDSQL_CONNECTION_NAME" &
    
    PROXY_PID=$!
    echo "Cloud SQL Proxy started with PID: $PROXY_PID"
    
    # Wait for proxy to start and be ready
    echo "Waiting for Cloud SQL Proxy to be ready..."
    sleep 10
    
    # Test if the proxy is ready by trying to connect
    for i in {1..30}; do
        if nc -z 127.0.0.1 5432; then
            echo "✅ Cloud SQL Proxy is ready!"
            break
        fi
        echo "Waiting for Cloud SQL Proxy... attempt $i/30"
        sleep 2
    done
    
    # Final check
    if ! nc -z 127.0.0.1 5432; then
        echo "❌ Cloud SQL Proxy failed to start properly"
        exit 1
    fi
    
    echo "✅ Cloud SQL Proxy is running and ready"
else
    echo "⚠️  CLOUDSQL_CONNECTION_NAME not set, skipping Cloud SQL Proxy"
    echo "Will attempt direct connection to: $DB_HOST:$DB_PORT"
fi

# Start the application
echo "Starting MCP HTTP Server..."
exec uvicorn http_server:app --host 0.0.0.0 --port 8080
