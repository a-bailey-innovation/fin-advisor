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

"""Integration tests for MCP HTTP Server"""

import asyncio
import json
import os
import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

# Import the HTTP server
from mcp_server.http_server import app
from mcp_server.db_operations import db_manager

class TestMCPHTTPServer:
    """Test suite for MCP HTTP Server endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint returns service information"""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "finadvisor-db-server"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "endpoints" in data
    
    def test_health_endpoint_no_db(self):
        """Test health endpoint when database is not connected"""
        with patch.object(db_manager, 'pool', None):
            response = self.client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert data["database_connected"] == False
    
    def test_health_endpoint_with_db(self):
        """Test health endpoint when database is connected"""
        # Mock database connection
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        with patch.object(db_manager, 'pool', mock_pool):
            response = self.client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert data["database_connected"] == True
    
    def test_log_status_endpoint_success(self):
        """Test log_status endpoint with valid data"""
        # Mock database operations
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=123)
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        with patch.object(db_manager, 'pool', mock_pool):
            with patch.object(db_manager, 'log_status', return_value=123):
                request_data = {
                    "session_id": "test_session",
                    "user_id": "test_user",
                    "agent_name": "test_agent",
                    "status_type": "info",
                    "message": "Test message",
                    "metadata": {"key": "value"}
                }
                
                response = self.client.post("/log_status", json=request_data)
                assert response.status_code == 200
                
                data = response.json()
                assert data["success"] == True
                assert data["log_id"] == 123
                assert "Status logged successfully" in data["message"]
    
    def test_log_status_endpoint_missing_fields(self):
        """Test log_status endpoint with missing required fields"""
        request_data = {
            "session_id": "test_session",
            "user_id": "test_user",
            # Missing agent_name, status_type, message
        }
        
        response = self.client.post("/log_status", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_log_status_endpoint_database_error(self):
        """Test log_status endpoint when database operation fails"""
        with patch.object(db_manager, 'log_status', side_effect=Exception("Database error")):
            request_data = {
                "session_id": "test_session",
                "user_id": "test_user",
                "agent_name": "test_agent",
                "status_type": "info",
                "message": "Test message"
            }
            
            response = self.client.post("/log_status", json=request_data)
            assert response.status_code == 500
            
            data = response.json()
            assert "Failed to log status" in data["detail"]
    
    def test_query_logs_endpoint_success(self):
        """Test query_logs endpoint with valid parameters"""
        mock_logs = [
            {
                "id": 1,
                "timestamp": "2024-01-01T00:00:00",
                "session_id": "test_session",
                "user_id": "test_user",
                "agent_name": "test_agent",
                "status_type": "info",
                "message": "Test message",
                "metadata": None
            }
        ]
        
        with patch.object(db_manager, 'get_recent_logs', return_value=mock_logs):
            response = self.client.get("/query_logs?limit=10&session_id=test_session")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == True
            assert data["count"] == 1
            assert len(data["logs"]) == 1
            assert data["logs"][0]["id"] == 1
    
    def test_query_logs_endpoint_no_filters(self):
        """Test query_logs endpoint without filters"""
        mock_logs = []
        
        with patch.object(db_manager, 'get_recent_logs', return_value=mock_logs):
            response = self.client.get("/query_logs")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == True
            assert data["count"] == 0
            assert data["logs"] == []
    
    def test_query_logs_endpoint_database_error(self):
        """Test query_logs endpoint when database operation fails"""
        with patch.object(db_manager, 'get_recent_logs', side_effect=Exception("Database error")):
            response = self.client.get("/query_logs")
            assert response.status_code == 500
            
            data = response.json()
            assert "Failed to query logs" in data["detail"]

class TestStatusLoggerToolHTTP:
    """Test suite for StatusLoggerTool HTTP client functionality"""
    
    @pytest.fixture
    def mock_http_response(self):
        """Mock HTTP response for testing"""
        response = AsyncMock()
        response.status_code = 200
        response.json.return_value = {"success": True, "log_id": 123, "message": "Success"}
        return response
    
    @pytest.mark.asyncio
    async def test_log_via_http_success(self, mock_http_response):
        """Test successful HTTP logging"""
        from financial_advisor.tools import StatusLoggerTool
        
        tool = StatusLoggerTool()
        tool._use_http_server = True
        tool._mcp_server_url = "https://test-server.run.app"
        
        with patch('httpx.AsyncClient.post', return_value=mock_http_response):
            with patch.object(tool, '_get_auth_token', return_value="test_token"):
                result = await tool._log_via_http(
                    agent_name="test_agent",
                    status_type="info",
                    message="Test message",
                    metadata={"key": "value"}
                )
                
                assert "Status logged successfully via HTTP with ID: 123" in result
    
    @pytest.mark.asyncio
    async def test_log_via_http_failure(self):
        """Test HTTP logging failure"""
        from financial_advisor.tools import StatusLoggerTool
        
        tool = StatusLoggerTool()
        tool._use_http_server = True
        tool._mcp_server_url = "https://test-server.run.app"
        
        # Mock HTTP error response
        error_response = AsyncMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient.post', return_value=error_response):
            with pytest.raises(Exception) as exc_info:
                await tool._log_via_http(
                    agent_name="test_agent",
                    status_type="info",
                    message="Test message"
                )
            
            assert "HTTP request failed with status 500" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_log_via_database_success(self):
        """Test successful database logging"""
        from financial_advisor.tools import StatusLoggerTool
        
        tool = StatusLoggerTool()
        
        # Mock database connection
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=456)
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        tool._pool = mock_pool
        
        result = await tool._log_via_database(
            agent_name="test_agent",
            status_type="info",
            message="Test message",
            metadata={"key": "value"}
        )
        
        assert "Status logged successfully with ID: 456" in result
    
    @pytest.mark.asyncio
    async def test_run_with_http_fallback(self):
        """Test run method with HTTP fallback to database"""
        from financial_advisor.tools import StatusLoggerTool
        
        tool = StatusLoggerTool()
        tool._use_http_server = True
        tool._mcp_server_url = "https://test-server.run.app"
        
        # Mock HTTP failure and database success
        with patch.object(tool, '_log_via_http', side_effect=Exception("HTTP failed")):
            with patch.object(tool, '_log_via_database', return_value="DB success"):
                result = await tool.run(
                    agent_name="test_agent",
                    status_type="info",
                    message="Test message"
                )
                
                assert result == "DB success"
    
    @pytest.mark.asyncio
    async def test_run_direct_database(self):
        """Test run method with direct database connection"""
        from financial_advisor.tools import StatusLoggerTool
        
        tool = StatusLoggerTool()
        tool._use_http_server = False
        
        with patch.object(tool, '_log_via_database', return_value="DB success"):
            result = await tool.run(
                agent_name="test_agent",
                status_type="info",
                message="Test message"
            )
            
            assert result == "DB success"

class TestVPCConnectivity:
    """Test suite for VPC connectivity and CloudSQL private IP access"""
    
    def test_config_private_ip_detection(self):
        """Test configuration detects private IP usage"""
        from mcp_server.config import get_database_url, USE_PRIVATE_IP, CLOUDSQL_PRIVATE_IP
        
        # Test with private IP enabled
        with patch.dict(os.environ, {
            'USE_PRIVATE_IP': 'true',
            'CLOUDSQL_PRIVATE_IP': '10.0.0.1',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_pass',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db'
        }):
            url = get_database_url()
            assert '10.0.0.1' in url
            assert 'postgresql://test_user:test_pass@10.0.0.1:5432/test_db' == url
    
    def test_config_public_ip_fallback(self):
        """Test configuration falls back to public IP"""
        from mcp_server.config import get_database_url
        
        # Test with private IP disabled
        with patch.dict(os.environ, {
            'USE_PRIVATE_IP': 'false',
            'DB_HOST': '34.29.136.71',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_pass',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db'
        }):
            url = get_database_url()
            assert '34.29.136.71' in url
            assert 'postgresql://test_user:test_pass@34.29.136.71:5432/test_db' == url

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

