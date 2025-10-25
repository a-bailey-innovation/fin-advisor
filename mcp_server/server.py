# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MCP Server for Financial Advisor CloudSQL Integration"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Resource,
    Tool,
)

from .config import MCP_SERVER_NAME, MCP_SERVER_VERSION
from .db_operations import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server(MCP_SERVER_NAME)

@server.list_resources()
async def list_resources() -> ListResourcesResult:
    """List available database resources"""
    return ListResourcesResult(
        resources=[
            Resource(
                uri="finadvisor://agent_status_logs",
                name="Agent Status Logs",
                description="Database table containing agent status messages",
                mimeType="application/json"
            )
        ]
    )

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available MCP tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="log_agent_status",
                description="Log agent status message to CloudSQL database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier"
                        },
                        "user_id": {
                            "type": "string", 
                            "description": "User identifier"
                        },
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent logging the status"
                        },
                        "status_type": {
                            "type": "string",
                            "description": "Type of status (info, warning, error, success)"
                        },
                        "message": {
                            "type": "string",
                            "description": "Status message content"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional metadata as JSON object"
                        }
                    },
                    "required": ["session_id", "user_id", "agent_name", "status_type", "message"]
                }
            ),
            Tool(
                name="query_agent_logs",
                description="Query recent agent status logs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of logs to return",
                            "default": 100
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Filter by session ID"
                        },
                        "agent_name": {
                            "type": "string",
                            "description": "Filter by agent name"
                        }
                    }
                }
            )
        ]
    )

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "log_agent_status":
            # Extract arguments
            session_id = arguments.get("session_id")
            user_id = arguments.get("user_id")
            agent_name = arguments.get("agent_name")
            status_type = arguments.get("status_type")
            message = arguments.get("message")
            metadata = arguments.get("metadata")
            
            # Validate required fields
            if not all([session_id, user_id, agent_name, status_type, message]):
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": "Error: Missing required fields (session_id, user_id, agent_name, status_type, message)"
                    }],
                    isError=True
                )
            
            # Log to database
            log_id = await db_manager.log_status(
                session_id=session_id,
                user_id=user_id,
                agent_name=agent_name,
                status_type=status_type,
                message=message,
                metadata=metadata
            )
            
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Successfully logged status with ID: {log_id}"
                }]
            )
        
        elif name == "query_agent_logs":
            # Extract arguments
            limit = arguments.get("limit", 100)
            session_id = arguments.get("session_id")
            agent_name = arguments.get("agent_name")
            
            # Query logs
            logs = await db_manager.get_recent_logs(
                limit=limit,
                session_id=session_id,
                agent_name=agent_name
            )
            
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(logs, indent=2, default=str)
                }]
            )
        
        else:
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Unknown tool: {name}"
                }],
                isError=True
            )
    
    except Exception as e:
        logger.error(f"Error in tool call {name}: {e}")
        return CallToolResult(
            content=[{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            isError=True
        )

async def main():
    """Main function to run the MCP server"""
    try:
        # Initialize database connection
        await db_manager.connect()
        await db_manager.create_tables()
        
        logger.info(f"Starting {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        # Clean up database connection
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
