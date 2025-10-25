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
from google.adk.tools import BaseTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class StatusLoggerTool(BaseTool):
    """Custom ADK tool for logging agent status directly to CloudSQL database"""
    
    def __init__(self):
        super().__init__(
            name="log_status",
            description="Log agent status messages to CloudSQL database"
        )
        self._pool: Optional[asyncpg.Pool] = None
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
    
    async def run(
        self,
        agent_name: str,
        status_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute the status logging tool"""
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
                    "default_session",  # Could be passed from context
                    "default_user",     # Could be passed from context
                    agent_name,
                    status_type,
                    message,
                    json.dumps(metadata) if metadata else None
                )
                
                logger.info(f"Successfully logged status for {agent_name} with ID: {result}")
                return f"Status logged successfully with ID: {result}"
        
        except Exception as e:
            logger.error(f"Error in status logger tool: {e}")
            return f"Error logging status: {str(e)}"
    
    async def close(self) -> None:
        """Close database connection pool"""
        if self._pool:
            try:
                await self._pool.close()
                self._pool = None
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")

# Create global instance
status_logger_tool = StatusLoggerTool()
