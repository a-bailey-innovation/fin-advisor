# Financial Advisor Environment Configuration

This document explains the environment configuration setup for the Financial Advisor project, which consists of two separate services that can be deployed independently.

## Architecture Overview

```
Financial Advisor Project
├── Financial Advisor Agent (Vertex AI)
│   ├── .env (agent-specific configuration)
│   └── env.example (agent template)
└── MCP Server (Cloud Run)
    ├── .env (server-specific configuration)
    └── env.example (server template)
```

## Environment Files

### 1. Financial Advisor Agent Environment

**File**: `fin-advisor/.env` (copy from `env.example`)

**Purpose**: Configuration for the Financial Advisor agent deployed to Vertex AI

**Key Variables**:
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `USE_MCP_HTTP_SERVER`: Whether to use HTTP MCP server (true/false)
- `MCP_SERVER_URL`: URL of the deployed MCP server
- `DEFAULT_SESSION_ID`: Default session ID for agent operations
- `DEFAULT_USER_ID`: Default user ID for agent operations

### 2. MCP Server Environment

**File**: `fin-advisor/mcp_server/.env` (copy from `mcp_server/env.example`)

**Purpose**: Configuration for the MCP HTTP server deployed to Cloud Run

**Key Variables**:
- `CLOUD_RUN_MODE`: Whether running in Cloud Run (true/false)
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`: Database connection details
- `USE_PRIVATE_IP`: Whether to use VPC connector for private IP
- `CORS_ORIGINS`: Allowed CORS origins
- `ENABLE_CORS`: Whether to enable CORS middleware

## Setup Instructions

### For Local Development

1. **Set up Financial Advisor Agent**:
   ```bash
   cd fin-advisor
   cp env.example .env
   # Edit .env with your settings
   ```

2. **Set up MCP Server** (if testing locally):
   ```bash
   cd fin-advisor/mcp_server
   cp env.example .env
   # Edit .env with your database settings
   ```

### For Cloud Deployment

**No `.env` files needed!** Environment variables are set automatically:

1. **MCP Server**: Set via `--set-env-vars` in deployment script
2. **Financial Advisor Agent**: Set via Vertex AI deployment configuration

## Configuration Modes

### Mode 1: Direct Database Connection (Default)
```env
# In fin-advisor/.env
USE_MCP_HTTP_SERVER=false
DB_USER=finadvisor_user
DB_PASSWORD=your-password
DB_HOST=your-cloudsql-ip
```

### Mode 2: HTTP MCP Server (Recommended for Production)
```env
# In fin-advisor/.env
USE_MCP_HTTP_SERVER=true
MCP_SERVER_URL=https://your-mcp-server.run.app

# In fin-advisor/mcp_server/.env (for local testing)
CLOUD_RUN_MODE=false
DB_USER=finadvisor_user
DB_PASSWORD=your-password
DB_HOST=your-cloudsql-ip
```

## Environment Variable Reference

### Financial Advisor Agent Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | - | Yes |
| `GOOGLE_CLOUD_LOCATION` | GCP region | us-central1 | Yes |
| `USE_MCP_HTTP_SERVER` | Use HTTP MCP server | false | No |
| `MCP_SERVER_URL` | MCP server URL | - | If USE_MCP_HTTP_SERVER=true |
| `DEFAULT_SESSION_ID` | Default session ID | default_session | No |
| `DEFAULT_USER_ID` | Default user ID | default_user | No |
| `AGENT_TIMEOUT` | Agent timeout (seconds) | 300 | No |
| `MAX_RETRIES` | Maximum retries | 3 | No |

### MCP Server Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CLOUD_RUN_MODE` | Running in Cloud Run | false | No |
| `HTTP_HOST` | Server host | 0.0.0.0 | No |
| `HTTP_PORT` | Server port | 8080 | No |
| `DB_USER` | Database user | - | Yes |
| `DB_PASSWORD` | Database password | - | Yes |
| `DB_HOST` | Database host | - | Yes |
| `DB_PORT` | Database port | 5432 | No |
| `USE_PRIVATE_IP` | Use VPC private IP | false | No |
| `CORS_ORIGINS` | Allowed CORS origins | * | No |
| `ENABLE_CORS` | Enable CORS | true | No |

## Security Considerations

### Production Deployment
- **Never commit `.env` files** to version control
- **Use Google Secret Manager** for sensitive data in production
- **Set restrictive CORS origins** instead of using `*`
- **Use VPC connector** for private database access
- **Enable IAM authentication** for service-to-service communication

### Local Development
- **Use separate `.env` files** for each service
- **Use test/development database** instances
- **Set `DEBUG=false`** in production
- **Use strong passwords** even for development

## Troubleshooting

### Common Issues

1. **Agent can't connect to MCP server**:
   - Check `MCP_SERVER_URL` is correct
   - Verify `USE_MCP_HTTP_SERVER=true`
   - Check MCP server is running

2. **MCP server can't connect to database**:
   - Verify database credentials
   - Check `USE_PRIVATE_IP` setting
   - Verify VPC connector status

3. **CORS errors**:
   - Check `CORS_ORIGINS` configuration
   - Verify `ENABLE_CORS=true`
   - Check origin is in allowed list

### Debug Commands

```bash
# Check environment variables
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('USE_MCP_HTTP_SERVER:', os.getenv('USE_MCP_HTTP_SERVER'))"

# Test MCP server connection
curl https://your-mcp-server.run.app/health

# Check database connection
uv run python mcp_server/test_db_connection.py
```

## Migration Guide

### From Direct DB to HTTP MCP Server

1. **Deploy MCP server**:
   ```bash
   uv run deployment/setup_vpc.py
   uv run deployment/deploy_mcp_server.py
   ```

2. **Update agent configuration**:
   ```env
   USE_MCP_HTTP_SERVER=true
   MCP_SERVER_URL=https://your-mcp-server.run.app
   ```

3. **Redeploy agent**:
   ```bash
   uv run deployment/deploy.py --create
   ```

This setup provides maximum flexibility, allowing you to:
- Deploy services independently
- Use different configurations for different environments
- Scale services separately
- Maintain security isolation between services
