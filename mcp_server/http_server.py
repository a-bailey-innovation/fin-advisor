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

"""HTTP REST API Server for Financial Advisor CloudSQL Integration"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import MCP_SERVER_NAME, MCP_SERVER_VERSION
from db_operations import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=MCP_SERVER_NAME,
    version=MCP_SERVER_VERSION,
    description="HTTP REST API for Financial Advisor CloudSQL Integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
enable_cors = os.getenv("ENABLE_CORS", "true").lower() == "true"

if enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Pydantic models for request/response
class LogStatusRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    agent_name: str = Field(..., description="Name of the agent logging the status")
    status_type: str = Field(..., description="Type of status (info, warning, error, success)")
    message: str = Field(..., description="Status message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as JSON object")

class LogStatusResponse(BaseModel):
    success: bool
    log_id: Optional[int] = None
    message: str

class QueryLogsRequest(BaseModel):
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of logs to return")
    session_id: Optional[str] = Field(None, description="Filter by session ID")
    agent_name: Optional[str] = Field(None, description="Filter by agent name")

class QueryLogsResponse(BaseModel):
    success: bool
    logs: List[Dict[str, Any]]
    count: int

class HealthResponse(BaseModel):
    status: str
    version: str
    database_connected: bool

# Dependency to ensure database connection
async def get_db_manager():
    """Dependency to ensure database connection is established"""
    if not db_manager.pool:
        await db_manager.connect()
        await db_manager.create_tables()
    return db_manager

@app.get("/test-connectivity", response_model=Dict[str, Any])
async def test_connectivity():
    """Test outbound connectivity"""
    import httpx
    
    results = {}
    
    # Test HTTP connectivity
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://httpbin.org/ip")
            results["http_connectivity"] = {
                "status": "success",
                "response": response.json()
            }
    except Exception as e:
        results["http_connectivity"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # Test database connectivity
    try:
        import asyncpg
        conn = await asyncpg.connect(
            "postgresql://finadvisor_user:FinAdvisorUser2024!@34.29.136.71:5432/FinAdvisor",
            command_timeout=10
        )
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        results["database_connectivity"] = {
            "status": "success",
            "result": result
        }
    except Exception as e:
        results["database_connectivity"] = {
            "status": "failed",
            "error": str(e)
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Test database connection
        db_connected = False
        if db_manager.pool:
            try:
                async with db_manager.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                db_connected = True
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
        
        return HealthResponse(
            status="healthy",
            version=MCP_SERVER_VERSION,
            database_connected=db_connected
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/log_status", response_model=LogStatusResponse)
async def log_status(
    request: LogStatusRequest,
    db: Any = Depends(get_db_manager)
):
    """Log agent status message to CloudSQL database"""
    try:
        log_id = await db.log_status(
            session_id=request.session_id,
            user_id=request.user_id,
            agent_name=request.agent_name,
            status_type=request.status_type,
            message=request.message,
            metadata=request.metadata
        )
        
        logger.info(f"Successfully logged status for agent {request.agent_name}: {request.status_type}")
        
        return LogStatusResponse(
            success=True,
            log_id=log_id,
            message=f"Status logged successfully with ID: {log_id}"
        )
    
    except Exception as e:
        logger.error(f"Error logging status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log status: {str(e)}"
        )

@app.get("/query_logs", response_model=QueryLogsResponse)
async def query_logs(
    limit: int = 100,
    session_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    db: Any = Depends(get_db_manager)
):
    """Query recent agent status logs"""
    try:
        logs = await db.get_recent_logs(
            limit=limit,
            session_id=session_id,
            agent_name=agent_name
        )
        
        return QueryLogsResponse(
            success=True,
            logs=logs,
            count=len(logs)
        )
    
    except Exception as e:
        logger.error(f"Error querying logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query logs: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "service": MCP_SERVER_NAME,
        "version": MCP_SERVER_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "log_status": "/log_status",
            "query_logs": "/query_logs",
            "docs": "/docs"
        }
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        await db_manager.connect()
        await db_manager.create_tables()
        logger.info(f"Started {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
    except Exception as e:
        logger.warning(f"Failed to connect to database on startup: {e}")
        logger.warning("Server will start without database connection - some endpoints may not work")
        logger.info(f"Started {MCP_SERVER_NAME} v{MCP_SERVER_VERSION} (without database)")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connection on shutdown"""
    try:
        await db_manager.close()
        logger.info("Server shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "http_server:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=False
    )
