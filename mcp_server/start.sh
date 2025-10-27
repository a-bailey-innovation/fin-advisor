#!/bin/bash

# Start Cloud SQL Auth Proxy (v2) in the background
if [ "$CLOUD_RUN_MODE" = "true" ] && [ -n "$CLOUDSQL_CONNECTION_NAME" ]; then
    echo "Starting Cloud SQL Auth Proxy (v2)..."
    cloud-sql-proxy --port 5432 --address 127.0.0.1 $CLOUDSQL_CONNECTION_NAME &
    PROXY_PID=$!
    
    # Wait for proxy to start and be ready
    echo "Waiting for Cloud SQL Auth Proxy to be ready..."
    sleep 10
    
    # Test if the proxy is ready by trying to connect
    for i in {1..30}; do
        if nc -z 127.0.0.1 5432; then
            echo "Cloud SQL Auth Proxy is ready!"
            break
        fi
        echo "Waiting for Cloud SQL Auth Proxy... attempt $i/30"
        sleep 2
    done
    
    echo "Cloud SQL Auth Proxy started with PID: $PROXY_PID"
fi

# Start the application
echo "Starting MCP HTTP Server..."
exec uvicorn http_server:app --host 0.0.0.0 --port 8080
