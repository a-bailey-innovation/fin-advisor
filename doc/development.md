# Financial Advisor Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.12+
- `uv` package manager
- Git
- Google Cloud CLI (for deployment testing)

### Initial Setup
```bash
# Clone repository
git clone https://github.com/a-bailey-innovation/fin-advisor.git
cd fin-advisor

# Install dependencies
uv sync

# Set up environment
cp .env.example .env  # Edit with your configuration
```

## Project Structure

```
financial-advisor/
├── financial_advisor/           # Core application
│   ├── __init__.py            # Package initialization
│   ├── agent.py             # Main financial coordinator agent
│   ├── prompt.py             # Agent prompts and instructions
│   ├── sub_agents/           # Specialized sub-agents
│   │   ├── data_analyst/     # Market data analysis agent
│   │   ├── trading_analyst/  # Trading strategy agent
│   │   ├── execution_analyst/# Execution planning agent
│   │   └── risk_analyst/     # Risk assessment agent
│   └── tools/               # Custom ADK tools
│       └── __init__.py       # Status logger tool
├── deployment/               # Deployment scripts
│   ├── deploy.py            # Main deployment script
│   └── test_deployment.py   # Testing script
├── mcp_server/              # MCP server implementation
│   ├── server.py           # MCP server
│   ├── db_operations.py    # Database operations
│   ├── config.py          # Configuration
│   └── test_db_connection.py # Database testing
├── tests/                  # Test suite
│   ├── test_agents.py      # Agent tests
│   └── test_status_logger.py # Status logger tests
├── doc/                    # Documentation
├── pyproject.toml         # Dependencies and metadata
└── README.md              # Project overview
```

## Core Components

### 1. Financial Coordinator Agent

**File**: `financial_advisor/agent.py`

The main orchestrator that coordinates all sub-agents:

```python
financial_coordinator = LlmAgent(
    name="financial_coordinator",
    model="gemini-2.5-pro",
    description="Guide users through financial advisory process",
    instruction=prompt.FINANCIAL_COORDINATOR_PROMPT,
    output_key="financial_coordinator_output",
    tools=[
        AgentTool(agent=data_analyst_agent),
        AgentTool(agent=trading_analyst_agent),
        AgentTool(agent=execution_analyst_agent),
        AgentTool(agent=risk_analyst_agent),
        status_logger_tool,
    ],
)
```

### 2. Sub-Agents

Each sub-agent follows the same pattern:

```python
# Example: data_analyst/agent.py
data_analyst_agent = LlmAgent(
    name="data_analyst",
    model="gemini-2.5-pro",
    description="Comprehensive market data analysis",
    instruction=prompt.DATA_ANALYST_PROMPT,
    output_key="market_data_analysis_output",
    tools=[google_search_tool, status_logger_tool],
)
```

### 3. Custom Tools

**File**: `financial_advisor/tools/__init__.py`

Custom ADK tools for specialized functionality:

```python
class StatusLoggerTool(BaseTool):
    """Custom tool for logging agent status to database"""
    
    def __init__(self):
        super().__init__(
            name="log_status",
            description="Log agent status messages to database"
        )
    
    async def run(self, agent_name: str, status_type: str, 
                  message: str, metadata: Dict[str, Any] = None) -> str:
        # Implementation for logging status
        pass
```

## Development Workflow

### 1. Local Development

#### Running the Agent Locally
```bash
# Start the financial advisor locally
uv run adk run financial_advisor

# Test specific functionality
uv run python -c "from financial_advisor.agent import root_agent; print('Agent loaded')"
```

#### Testing Individual Components
```bash
# Test status logger tool
uv run python tests/test_status_logger.py

# Test database connection
uv run python mcp_server/test_db_connection.py

# Test agent loading
uv run python tests/test_agents.py
```

### 2. Agent Development

#### Creating a New Sub-Agent

1. **Create Agent Directory**
```bash
mkdir financial_advisor/sub_agents/new_agent
touch financial_advisor/sub_agents/new_agent/__init__.py
touch financial_advisor/sub_agents/new_agent/agent.py
touch financial_advisor/sub_agents/new_agent/prompt.py
```

2. **Implement Agent**
```python
# financial_advisor/sub_agents/new_agent/agent.py
from google.adk.agents import LlmAgent
from . import prompt

new_agent = LlmAgent(
    name="new_agent",
    model="gemini-2.5-pro",
    description="Agent description",
    instruction=prompt.NEW_AGENT_PROMPT,
    output_key="new_agent_output",
    tools=[status_logger_tool],
)
```

3. **Add to Financial Coordinator**
```python
# financial_advisor/agent.py
from .sub_agents.new_agent import new_agent

financial_coordinator = LlmAgent(
    # ... existing configuration
    tools=[
        # ... existing tools
        AgentTool(agent=new_agent),
    ],
)
```

#### Creating Custom Tools

1. **Implement Tool Class**
```python
# financial_advisor/tools/custom_tool.py
from google.adk.tools import BaseTool

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Custom tool description"
        )
    
    async def run(self, param1: str, param2: int) -> str:
        # Tool implementation
        return "Tool result"
```

2. **Register Tool**
```python
# financial_advisor/tools/__init__.py
from .custom_tool import CustomTool

custom_tool = CustomTool()
```

### 3. Prompt Engineering

#### Prompt Structure
Each agent prompt follows this structure:

```python
AGENT_PROMPT = """
**IMPORTANT: Use the log_status tool to track progress.**

Logging Requirements:
- Log start: log_status(agent_name="agent_name", status_type="info", message="Starting task")
- Log progress: log_status(agent_name="agent_name", status_type="info", message="Progress update")
- Log completion: log_status(agent_name="agent_name", status_type="success", message="Task completed")
- Log errors: log_status(agent_name="agent_name", status_type="error", message="Error details")

Objective: Clear description of agent purpose

Process:
1. Step-by-step instructions
2. Tool usage guidelines
3. Output format requirements

Expected Output: Detailed output specification
"""
```

#### Best Practices
- Use clear, specific instructions
- Include logging requirements
- Provide examples
- Define expected outputs
- Include error handling

### 4. Testing

#### Unit Testing
```python
# tests/test_new_agent.py
import pytest
from financial_advisor.sub_agents.new_agent import new_agent

def test_agent_loading():
    assert new_agent is not None
    assert new_agent.name == "new_agent"

def test_agent_tools():
    assert len(new_agent.tools) > 0
    assert any(tool.name == "log_status" for t in new_agent.tools)
```

#### Integration Testing
```python
# tests/test_agent_integration.py
import pytest
from financial_advisor.agent import financial_coordinator

def test_coordinator_has_all_agents():
    agent_tools = [tool for tool in financial_coordinator.tools 
                   if hasattr(tool, 'agent')]
    assert len(agent_tools) == 4  # data, trading, execution, risk

def test_status_logger_available():
    tool_names = [tool.name for tool in financial_coordinator.tools]
    assert "log_status" in tool_names
```

#### Database Testing
```python
# tests/test_database.py
import pytest
import asyncio
from mcp_server.db_operations import log_status_message

@pytest.mark.asyncio
async def test_log_status_message():
    result = await log_status_message(
        agent_name="test_agent",
        user_id="test_user",
        session_id="test_session",
        message="Test message",
        status_type="info"
    )
    assert result["status"] == "success"
```

### 5. Database Development

#### Schema Management
```sql
-- mcp_server/create_schema.sql
CREATE TABLE IF NOT EXISTS agent_status_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    agent_name VARCHAR(100),
    status_type VARCHAR(50),
    message TEXT,
    metadata JSONB
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_status_logs_timestamp ON agent_status_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_status_logs_agent_name ON agent_status_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_status_logs_session_id ON agent_status_logs(session_id);
```

#### Database Operations
```python
# mcp_server/db_operations.py
import asyncpg
from datetime import datetime

async def log_status_message(agent_name: str, user_id: str, 
                           session_id: str, message: str, status_type: str):
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        result = await conn.fetchval(
            """
            INSERT INTO agent_status_logs 
            (session_id, user_id, agent_name, status_type, message)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            session_id, user_id, agent_name, status_type, message
        )
        return {"status": "success", "id": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            await conn.close()
```

### 6. Deployment Development

#### Local Testing
```bash
# Test deployment script
uv run deployment/deploy.py --help

# Test with environment variables
GOOGLE_CLOUD_PROJECT=test-project uv run deployment/deploy.py --create
```

#### Staging Deployment
```bash
# Deploy to staging environment
uv run deployment/deploy.py --create --staging

# Test deployed agent
uv run deployment/test_deployment.py --staging
```

## Development Best Practices

### 1. Code Organization
- Keep agents focused on single responsibilities
- Use clear, descriptive names
- Follow consistent patterns
- Document complex logic

### 2. Error Handling
- Implement comprehensive error handling
- Log errors with context
- Provide meaningful error messages
- Test error scenarios

### 3. Performance
- Use async/await for I/O operations
- Implement connection pooling
- Monitor resource usage
- Optimize database queries

### 4. Security
- Never hardcode credentials
- Use environment variables
- Validate all inputs
- Implement proper access controls

### 5. Testing
- Write comprehensive tests
- Test edge cases
- Mock external dependencies
- Maintain test coverage

## Debugging

### Common Issues

#### Agent Loading Errors
```bash
# Check agent imports
uv run python -c "from financial_advisor.agent import root_agent; print('OK')"

# Check dependencies
uv run python -c "import google.adk; print('ADK available')"
```

#### Database Connection Issues
```bash
# Test database connection
uv run python mcp_server/test_db_connection.py

# Check environment variables
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DB_HOST:', os.getenv('DB_HOST'))"
```

#### Deployment Issues
```bash
# Check Google Cloud authentication
gcloud auth list

# Check project configuration
gcloud config get-value project

# Test deployment permissions
gcloud projects describe YOUR_PROJECT_ID
```

### Debug Tools

#### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use in your code
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

#### Database Debugging
```python
# Check database logs
async def debug_database():
    conn = await asyncpg.connect(DATABASE_URL)
    logs = await conn.fetch("SELECT * FROM agent_status_logs ORDER BY timestamp DESC LIMIT 10")
    for log in logs:
        print(f"{log['timestamp']}: {log['agent_name']} - {log['message']}")
    await conn.close()
```

This development guide provides comprehensive instructions for developing, testing, and maintaining the Financial Advisor application.
