# Financial Advisor MCP HTTP Server

This directory contains the HTTP REST API server for Financial Advisor CloudSQL integration, designed to run on Google Cloud Run.

## Overview

The MCP HTTP Server provides a REST API interface for logging agent status messages to CloudSQL database. It's designed to be deployed separately from the Financial Advisor agent on Cloud Run with VPC connector for secure database access.

## Architecture

- **FastAPI**: Modern async web framework with automatic OpenAPI documentation
- **CloudSQL**: PostgreSQL database for storing agent status logs
- **VPC Connector**: Secure private IP access to CloudSQL (no public IPs)
- **IAM Authentication**: Service-to-service authentication using Google Cloud IAM
- **Cloud Run**: Serverless container platform for scalable deployment

## Environment Configuration

### Local Development

1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. Update `.env` with your local database settings:
   ```env
   CLOUD_RUN_MODE=false
   DB_HOST=your-local-db-host
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   ```

### Cloud Run Deployment

Environment variables are automatically set during deployment via the deployment script. No manual `.env` file needed in production.

## API Endpoints

### Health Check
- **GET** `/health` - Service health status
- **GET** `/` - Service information

### Status Logging
- **POST** `/log_status` - Log agent status message
- **GET** `/query_logs` - Query recent status logs

### Documentation
- **GET** `/docs` - Interactive API documentation (Swagger UI)
- **GET** `/redoc` - Alternative API documentation

## Local Development

### Prerequisites
- Python 3.12+
- `uv` package manager
- Access to CloudSQL database

### Setup
```bash
# Install dependencies
uv sync

# Copy environment configuration
cp env.example .env
# Edit .env with your database settings

# Run the server locally
uv run uvicorn http_server:app --host 0.0.0.0 --port 8080 --reload
```

### Testing
```bash
# Test health endpoint
curl http://localhost:8080/health

# Test API documentation
open http://localhost:8080/docs
```

## Cloud Run Deployment

### Prerequisites
- Google Cloud project with billing enabled
- CloudSQL instance running
- VPC network configured

### Deploy
```bash
# Set up VPC for private CloudSQL access
uv run ../deployment/setup_vpc.py

# Deploy to Cloud Run
uv run ../deployment/deploy_mcp_server.py
```

### Environment Variables (Set Automatically)
- `CLOUD_RUN_MODE=true`
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT`
- `USE_PRIVATE_IP=true` (when VPC connector is used)
- `CLOUDSQL_PRIVATE_IP` (private IP address)
- `ENABLE_CORS=true`
- `LOG_LEVEL=INFO`

## Security

- **VPC Connector**: Database access via private IP only
- **IAM Authentication**: Service-to-service authentication
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Environment Variables**: Sensitive data via environment variables
- **No Public IPs**: Database not accessible from internet

## Monitoring

- **Health Checks**: Built-in health check endpoint
- **Structured Logging**: JSON-formatted logs for Cloud Logging
- **Metrics**: Request metrics via Cloud Run monitoring
- **Error Tracking**: Comprehensive error handling and logging

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check VPC connector status
   - Verify CloudSQL private IP configuration
   - Check firewall rules

2. **Authentication Errors**
   - Verify service account permissions
   - Check IAM roles (Cloud SQL Client)

3. **CORS Issues**
   - Configure `CORS_ORIGINS` environment variable
   - Check `ENABLE_CORS` setting

### Debug Commands
```bash
# Check service status
gcloud run services describe finadvisor-mcp-server --region=us-central1

# View logs
gcloud logs read --service=finadvisor-mcp-server --limit=50

# Test endpoints
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://your-service-url.run.app/health
```

## File Structure

```
mcp_server/
├── http_server.py          # FastAPI application
├── config.py              # Configuration management
├── db_operations.py       # Database operations
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
└── README.md             # This file
```

## Integration with Financial Advisor

The Financial Advisor agent connects to this MCP server via HTTP API instead of direct database connection. This provides:

- **Scalability**: Independent scaling of logging service
- **Security**: Centralized database access control
- **Monitoring**: Dedicated logging service monitoring
- **Flexibility**: Can be used by multiple services
