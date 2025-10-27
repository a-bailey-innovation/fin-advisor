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

"""Custom tools for Financial Advisor"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import asyncpg
import httpx
from google.adk.tools import BaseTool
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class StatusLoggerTool(BaseTool):
    """Custom ADK tool for logging agent status via HTTP API or direct DB connection"""
    
    def __init__(self):
        super().__init__(
            name="log_status",
            description="Log agent status messages to CloudSQL database via HTTP API or direct connection"
        )
        self._pool: Optional[asyncpg.Pool] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._use_http_server = os.getenv("USE_MCP_HTTP_SERVER", "false").lower() == "true"
        self._mcp_server_url = os.getenv("MCP_SERVER_URL")
        self._default_session_id = os.getenv("DEFAULT_SESSION_ID", "default_session")
        self._default_user_id = os.getenv("DEFAULT_USER_ID", "default_user")
        self._db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    async def _ensure_db_connection(self) -> None:
        """Ensure database connection pool is established"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    self._db_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=30
                )
                logger.info("Connected to CloudSQL database")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
    
    async def _ensure_http_client(self) -> None:
        """Ensure HTTP client is established"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
            logger.info("HTTP client initialized")
    
    async def _get_auth_token(self) -> Optional[str]:
        """Get Google Cloud authentication token for Cloud Run"""
        try:
            # Try to get default credentials
            from google.auth import default
            credentials, project = default()
            
            # Refresh the token
            request = Request()
            credentials.refresh(request)
            
            return credentials.token
        except Exception as e:
            logger.warning(f"Failed to get auth token: {e}")
            return None
    
    async def _log_via_http(
        self,
        agent_name: str,
        status_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log status via HTTP API"""
        try:
            await self._ensure_http_client()
            
            # Prepare request data
            request_data = {
                "session_id": self._default_session_id,
                "user_id": self._default_user_id,
                "agent_name": agent_name,
                "status_type": status_type,
                "message": message,
                "metadata": metadata
            }
            
            # Get authentication token
            auth_token = await self._get_auth_token()
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            # Make HTTP request
            response = await self._http_client.post(
                f"{self._mcp_server_url}/log_status",
                json=request_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                log_id = result.get("log_id")
                logger.info(f"Successfully logged status for {agent_name} via HTTP with ID: {log_id}")
                return f"Status logged successfully via HTTP with ID: {log_id}"
            else:
                error_msg = f"HTTP request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error logging status via HTTP: {e}")
            raise
    
    async def _log_via_database(
        self,
        agent_name: str,
        status_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log status via direct database connection"""
        try:
            # Ensure database connection
            await self._ensure_db_connection()
            
            # Log to database
            async with self._pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    INSERT INTO agent_status_logs 
                    (session_id, user_id, agent_name, status_type, message, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    self._default_session_id,
                    self._default_user_id,
                    agent_name,
                    status_type,
                    message,
                    json.dumps(metadata) if metadata else None
                )
                
                logger.info(f"Successfully logged status for {agent_name} with ID: {result}")
                return f"Status logged successfully with ID: {result}"
        
        except Exception as e:
            logger.error(f"Error logging status to database: {e}")
            raise
    
    async def run(
        self,
        agent_name: str,
        status_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute the status logging tool"""
        try:
            # Try HTTP server first if configured
            if self._use_http_server and self._mcp_server_url:
                try:
                    return await self._log_via_http(agent_name, status_type, message, metadata)
                except Exception as e:
                    logger.warning(f"HTTP logging failed, falling back to direct DB: {e}")
                    # Fall back to direct database connection
                    return await self._log_via_database(agent_name, status_type, message, metadata)
            else:
                # Use direct database connection
                return await self._log_via_database(agent_name, status_type, message, metadata)
        
        except Exception as e:
            logger.error(f"Error in status logger tool: {e}")
            return f"Error logging status: {str(e)}"
    
    async def close(self) -> None:
        """Close database connection pool and HTTP client"""
        if self._pool:
            try:
                await self._pool.close()
                self._pool = None
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
        
        if self._http_client:
            try:
                await self._http_client.aclose()
                self._http_client = None
                logger.info("HTTP client closed")
            except Exception as e:
                logger.error(f"Error closing HTTP client: {e}")

# Create global instance
status_logger_tool = StatusLoggerTool()
