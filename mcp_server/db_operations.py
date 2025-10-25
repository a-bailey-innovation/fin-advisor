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

"""Database operations for CloudSQL integration"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import asyncpg
from .config import DATABASE_URL

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages CloudSQL database connections and operations"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Establish connection pool to CloudSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("Connected to CloudSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def create_tables(self) -> None:
        """Create the agent_status_logs table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS agent_status_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id VARCHAR(255),
            user_id VARCHAR(255),
            agent_name VARCHAR(100),
            status_type VARCHAR(50),
            message TEXT,
            metadata JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_agent_status_logs_timestamp 
        ON agent_status_logs(timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_agent_status_logs_session_id 
        ON agent_status_logs(session_id);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_table_sql)
            logger.info("Database tables created/verified")
    
    async def log_status(
        self,
        session_id: str,
        user_id: str,
        agent_name: str,
        status_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Log agent status message to database"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    INSERT INTO agent_status_logs 
                    (session_id, user_id, agent_name, status_type, message, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    session_id,
                    user_id,
                    agent_name,
                    status_type,
                    message,
                    json.dumps(metadata) if metadata else None
                )
                logger.info(f"Logged status for agent {agent_name}: {status_type}")
                return result
        except Exception as e:
            logger.error(f"Failed to log status: {e}")
            raise
    
    async def get_recent_logs(
        self,
        limit: int = 100,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query recent status logs"""
        try:
            conditions = []
            params = []
            param_count = 0
            
            if session_id:
                param_count += 1
                conditions.append(f"session_id = ${param_count}")
                params.append(session_id)
            
            if agent_name:
                param_count += 1
                conditions.append(f"agent_name = ${param_count}")
                params.append(agent_name)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            params.append(limit)
            
            query = f"""
                SELECT id, timestamp, session_id, user_id, agent_name, 
                       status_type, message, metadata
                FROM agent_status_logs
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${param_count + 1}
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to query logs: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()
