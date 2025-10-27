# Financial Advisor Deployment Guide

## Overview

This document provides comprehensive instructions for deploying the Financial Advisor application to Google Cloud Platform using Vertex AI Agent Engine.

## Prerequisites

### Required Tools
- Python 3.12+
- `uv` package manager
- Google Cloud CLI (`gcloud`)
- Git

### Required Permissions
- Google Cloud Project with billing enabled
- Vertex AI API enabled
- Cloud SQL API enabled
- Storage API enabled
- Service Account with appropriate permissions

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/a-bailey-innovation/fin-advisor.git
cd fin-advisor
```

### 2. Install Dependencies
```bash
uv sync
```

### 3. Configure Environment Variables
Create `.env` file with the following variables:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GOOGLE_GENAI_USE_VERTEXAI=true

# Deployed Agent Configuration
AGENT_RESOURCE_ID=your-agent-resource-id
DEFAULT_USER_ID=financial_advisor_user

# CloudSQL Configuration (Optional)
DB_USER=finadvisor_user
DB_PASSWORD=your-secure-password
DB_NAME=FinAdvisor
DB_HOST=your-cloudsql-ip
DB_PORT=5432

# MCP Server Configuration (Optional)
MCP_SERVER_URL=https://your-mcp-server-url.run.app
```

### 4. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## Database Setup (Optional)

### 1. Create CloudSQL Instance
```bash
gcloud sql instances create finadvisor-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=your-root-password
```

### 2. Create Database and User
```bash
# Create database
gcloud sql databases create FinAdvisor --instance=finadvisor-db

# Create user
gcloud sql users create finadvisor_user \
    --instance=finadvisor-db \
    --password=your-user-password
```

### 3. Configure Authorized Networks
```bash
# Get your public IP
curl -s https://api.ipify.org

# Add to authorized networks
gcloud sql instances patch finadvisor-db \
    --authorized-networks=YOUR_PUBLIC_IP
```

### 4. Create Database Schema
```bash
uv run python mcp_server/test_db_connection.py
```

## Deployment Options

### Option 1: Standard Deployment (Recommended)

#### 1. Deploy Financial Advisor Agent
```bash
uv run deployment/deploy.py --create
```

#### 2. Test Deployment
```bash
uv run deployment/test_deployment.py
```

#### 3. Verify Agent Functionality
```bash
# Interactive testing
uv run deployment/test_deployment.py

# Check logs
gcloud logging read "resource.type=vertex_ai_agent" --limit=50
```

### Option 2: Deployment with CloudSQL Logging via Cloud Run

#### 1. Set Up VPC for CloudSQL Private IP Access
```bash
# Set up VPC network and connector for secure CloudSQL access
uv run deployment/setup_vpc.py
```

This script will:
- Create a VPC network (`finadvisor-vpc`)
- Create a VPC connector (`finadvisor-vpc-connector`)
- Enable private IP for CloudSQL instance
- Create necessary firewall rules
- Output the CloudSQL private IP address

#### 2. Deploy MCP Server to Cloud Run
```bash
# Deploy the HTTP MCP server to Cloud Run with VPC connector
uv run deployment/deploy_mcp_server.py
```

This script will:
- Create a service account with Cloud SQL Client role
- Build and deploy the MCP server to Cloud Run
- Configure VPC connector for private CloudSQL access
- Set up IAM authentication
- Output the service URL

#### 3. Update Environment Variables
```bash
# Copy the example environment file
cp env.example .env

# Update with your values (get MCP_SERVER_URL from deployment output)
# Set USE_MCP_HTTP_SERVER=true to enable HTTP logging
# Set CLOUDSQL_PRIVATE_IP=<private-ip-from-vpc-setup>
# Set USE_PRIVATE_IP=true
```

#### 4. Deploy Financial Advisor with HTTP Logging
```bash
uv run deployment/deploy.py --create
```

#### 5. Test the Complete Setup
```bash
# Test the deployed agent
uv run deployment/test_deployment.py

# Test MCP server endpoints
curl https://your-mcp-server-url.run.app/health
curl https://your-mcp-server-url.run.app/query_logs
```

## Verification and Testing

### 1. Health Checks
```bash
# Test agent deployment
uv run deployment/test_deployment.py

# Test database connection (if using CloudSQL)
uv run python mcp_server/test_db_connection.py

# Test status logger tool
uv run python tests/test_status_logger.py
```

### 2. Monitor Deployment
```bash
# View agent logs
gcloud logging read "resource.type=vertex_ai_agent" --limit=50

# View Cloud Run logs (if using MCP server)
gcloud logs read --service=finadvisor-mcp-server --limit=50

# View MCP server logs
gcloud logs read --service=finadvisor-mcp-server --limit=50 --format="table(timestamp,severity,textPayload)"

# Check database logs
uv run python -c "
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = f'postgresql://{os.getenv(\"DB_USER\")}:{os.getenv(\"DB_PASSWORD\")}@{os.getenv(\"DB_HOST\")}:{os.getenv(\"DB_PORT\")}/{os.getenv(\"DB_NAME\")}'

async def check_logs():
    conn = await asyncpg.connect(DATABASE_URL)
    logs = await conn.fetch('SELECT * FROM agent_status_logs ORDER BY timestamp DESC LIMIT 10')
    for log in logs:
        print(f'{log[\"timestamp\"]}: {log[\"agent_name\"]} - {log[\"message\"]}')
    await conn.close()

asyncio.run(check_logs())
"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```bash
# Re-authenticate
gcloud auth application-default login
gcloud auth login
```

#### 2. Permission Errors
```bash
# Check permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Add required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/aiplatform.user"
```

#### 3. Database Connection Issues
```bash
# Check CloudSQL instance status
gcloud sql instances describe finadvisor-db

# Test connection
gcloud sql connect finadvisor-db --user=finadvisor_user --database=FinAdvisor
```

#### 4. Agent Deployment Failures
```bash
# Check Vertex AI quotas
gcloud compute project-info describe --project=YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

#### 5. VPC and CloudSQL Connectivity Issues
```bash
# Check VPC connector status
gcloud compute networks vpc-access connectors describe finadvisor-vpc-connector --region=us-central1

# Check CloudSQL private IP
gcloud sql instances describe finadvisor-db --format="value(ipAddresses[0].ipAddress)"

# Test VPC connectivity
gcloud compute ssh your-instance --zone=us-central1-a --command="ping -c 3 10.0.0.1"

# Check firewall rules
gcloud compute firewall-rules list --filter="name~allow-cloudsql"
```

#### 6. MCP Server Issues
```bash
# Check Cloud Run service status
gcloud run services describe finadvisor-mcp-server --region=us-central1

# View Cloud Run logs
gcloud logs read --service=finadvisor-mcp-server --limit=50

# Test MCP server endpoints
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" https://your-mcp-server-url.run.app/health
```

### Debug Commands

```bash
# Check environment variables
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))"

# Test agent loading
uv run python -c "from financial_advisor.agent import root_agent; print('Agent loaded successfully')"

# Test database schema
uv run python mcp_server/test_db_connection.py

# View recent logs
gcloud logging read "resource.type=vertex_ai_agent" --limit=20 --format="table(timestamp,severity,textPayload)"
```

## Production Considerations

### 1. Security
- Use Google Secret Manager for sensitive credentials
- Enable Cloud SQL Auth Proxy for production
- Implement proper IAM roles and permissions
- Use VPC for network isolation

### 2. Monitoring
- Set up Cloud Monitoring alerts
- Configure log-based metrics
- Implement health checks
- Monitor database performance

### 3. Scaling
- Configure auto-scaling for Cloud Run
- Use connection pooling for database
- Implement caching strategies
- Monitor resource usage

### 4. Backup and Recovery
- Enable automated database backups
- Implement disaster recovery procedures
- Test backup restoration processes
- Document recovery procedures

## Maintenance

### Regular Tasks
- Monitor agent performance and logs
- Update dependencies regularly
- Review and rotate credentials
- Test backup and recovery procedures

### Updates
- Deploy updates during maintenance windows
- Test in staging environment first
- Maintain rollback procedures
- Document all changes

This deployment guide ensures a robust, scalable, and maintainable Financial Advisor application on Google Cloud Platform.
