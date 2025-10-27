#!/bin/bash

echo "=== MCP Server Startup Debug ==="
echo "CLOUD_RUN_MODE: $CLOUD_RUN_MODE"
echo "CLOUDSQL_CONNECTION_NAME: $CLOUDSQL_CONNECTION_NAME"
echo "VPC_CONNECTOR_NAME: $VPC_CONNECTOR_NAME"
echo "All environment variables:"
env | grep -E "(CLOUD|SQL|DB)" | sort

# Start Cloud SQL Auth Proxy (v2) in the background - DISABLED due to port issues
if [ "false" = "true" ] && [ -n "$CLOUDSQL_CONNECTION_NAME" ]; then
    echo "Starting Cloud SQL Auth Proxy (v2)..."
    cloud-sql-proxy --port 5432 --address 127.0.0.1 --auto-iam-authn $CLOUDSQL_CONNECTION_NAME &
    PROXY_PID=$!
    
    # Wait for proxy to start and be ready
    echo "Waiting for Cloud SQL Proxy to be ready..."
    sleep 10
    
    # Test if the proxy is ready by trying to connect
    for i in {1..30}; do
        if nc -z 127.0.0.1 5432; then
            echo "Cloud SQL Proxy is ready!"
            break
        fi
        echo "Waiting for Cloud SQL Proxy... attempt $i/30"
        sleep 2
    done
    
    echo "Cloud SQL Proxy started with PID: $PROXY_PID"
else
    echo "Skipping Cloud SQL Proxy startup - conditions not met"
    echo "CLOUD_RUN_MODE check: $CLOUD_RUN_MODE"
    echo "CLOUDSQL_CONNECTION_NAME check: '$CLOUDSQL_CONNECTION_NAME'"
fi

# Start the application
echo "Starting MCP HTTP Server..."
exec uvicorn http_server:app --host 0.0.0.0 --port 8080
