# Financial Advisor CloudSQL Integration

This directory contains the CloudSQL integration components for the Financial Advisor application, including both MCP server implementation and direct database tools.

## Overview

The Financial Advisor now includes status logging capabilities that save agent execution information to a CloudSQL PostgreSQL database. This allows for:

- Tracking agent execution status
- Monitoring performance and errors
- Auditing financial advice sessions
- Debugging and analytics

## Architecture

### Direct Database Tool (Recommended)
- **File**: `financial_advisor/tools/__init__.py`
- **Approach**: Direct asyncpg connection to CloudSQL
- **Benefits**: Simple, reliable, no additional infrastructure
- **Usage**: Automatically available to all agents via `status_logger_tool`

### MCP Server (Alternative)
- **Files**: `mcp_server/server.py`, `mcp_server/db_operations.py`
- **Approach**: Model Context Protocol server for database operations
- **Benefits**: Decoupled, reusable across applications
- **Usage**: Can be run standalone or integrated with other MCP clients

## Database Schema

```sql
CREATE TABLE agent_status_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    agent_name VARCHAR(100),
    status_type VARCHAR(50),
    message TEXT,
    metadata JSONB
);
```

## Configuration

The system uses environment variables for database configuration:

```env
# CloudSQL Configuration
CLOUDSQL_CONNECTION_NAME=agent-space-demo-475212:us-central1:finadvisor-db
DB_NAME=FinAdvisor
DB_USER=finadvisor_user
DB_PASSWORD=FinAdvisorUser2024!
DB_HOST=34.29.136.71
DB_PORT=5432
```

## Usage

### Automatic Logging
The status logger tool is automatically available to all agents. Agents can log status messages like:

```python
# This happens automatically when agents use the log_status tool
await status_logger_tool.run(
    agent_name="data_analyst",
    status_type="info", 
    message="Starting market analysis for AAPL",
    metadata={"ticker": "AAPL", "analysis_type": "comprehensive"}
)
```

### Manual Testing
Test the database connection:
```bash
uv run python mcp_server/test_db_connection.py
```

Test the status logger tool:
```bash
uv run python tests/test_status_logger.py
```

## Deployment

The CloudSQL integration is automatically included when deploying the Financial Advisor:

```bash
uv run deployment/deploy.py --create
```

The deployment includes all necessary dependencies and the status logger tool is available to the deployed agent.

## Monitoring

You can query the status logs directly from the CloudSQL database:

```sql
-- Recent logs
SELECT * FROM agent_status_logs 
ORDER BY timestamp DESC 
LIMIT 100;

-- Logs by agent
SELECT * FROM agent_status_logs 
WHERE agent_name = 'data_analyst'
ORDER BY timestamp DESC;

-- Error logs
SELECT * FROM agent_status_logs 
WHERE status_type = 'error'
ORDER BY timestamp DESC;
```

## Troubleshooting

### Connection Issues
1. Verify CloudSQL instance is running: `gcloud sql instances describe finadvisor-db`
2. Check authorized networks: Ensure your IP is in the authorized networks list
3. Verify credentials in `.env` file
4. Test connection: `uv run python mcp_server/test_db_connection.py`

### Tool Issues
1. Check that the tool is properly imported in `financial_advisor/agent.py`
2. Verify database schema exists: Run `mcp_server/create_schema.sql`
3. Check logs for specific error messages

## Security Notes

- Database credentials are stored in `.env` file (not committed to git)
- Consider using Cloud SQL Auth Proxy for production
- Monitor database access logs
- Implement proper backup strategies for production use
