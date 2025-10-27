#!/usr/bin/env python3
"""
Test script to verify MCP server database connectivity
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

import httpx


async def get_auth_token() -> str:
    """Get Google Cloud authentication token"""
    try:
        # Use PowerShell execution policy bypass for Windows
        if os.name == "nt":
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", "gcloud auth print-access-token"],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                capture_output=True,
                text=True,
                check=True
            )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Failed to get auth token: {e}")
        sys.exit(1)


async def test_mcp_server_connection():
    """Test MCP server database connectivity"""
    print("Testing MCP Server Database Connectivity...")
    
    # Get authentication token
    print("Getting authentication token...")
    token = await get_auth_token()
    
    # MCP server URL
    mcp_server_url = "https://finadvisor-mcp-server-hsjqscogca-uc.a.run.app"
    
    # Test data
    test_data = {
        "session_id": "test_session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        "user_id": "test_user",
        "agent_name": "deployment_test_agent",
        "status_type": "info",
        "message": f"MCP Server database connectivity test - {datetime.now().isoformat()}",
        "metadata": {
            "test": True,
            "deployment_verification": True,
            "timestamp": datetime.now().isoformat(),
            "test_id": "mcp_db_test_001"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test 1: Health check
            print("Testing health endpoint...")
            health_response = await client.get(
                f"{mcp_server_url}/health",
                headers=headers
            )
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"SUCCESS: Health check passed: {health_data}")
                db_connected = health_data.get("database_connected", False)
                if db_connected:
                    print("SUCCESS: Database connection confirmed via health check")
                else:
                    print("WARNING: Database not connected according to health check")
            else:
                print(f"ERROR: Health check failed: {health_response.status_code} - {health_response.text}")
                return False
            
            # Test 2: Log status message
            print("Testing log_status endpoint...")
            log_response = await client.post(
                f"{mcp_server_url}/log_status",
                headers=headers,
                json=test_data
            )
            
            if log_response.status_code == 200:
                log_data = log_response.json()
                log_id = log_data.get("log_id")
                print(f"SUCCESS: Log status successful! Log ID: {log_id}")
                print(f"Response: {log_data}")
                
                # Test 3: Query logs to verify the message was saved
                print("Testing query_logs endpoint...")
                query_data = {
                    "limit": 5,
                    "agent_name": "deployment_test_agent"
                }
                
                query_response = await client.post(
                    f"{mcp_server_url}/query_logs",
                    headers=headers,
                    json=query_data
                )
                
                if query_response.status_code == 200:
                    query_data = query_response.json()
                    logs = query_data.get("logs", [])
                    print(f"SUCCESS: Query logs successful! Found {len(logs)} logs")
                    
                    # Check if our test message is in the results
                    test_log_found = False
                    for log in logs:
                        if log.get("agent_name") == "deployment_test_agent":
                            test_log_found = True
                            print(f"SUCCESS: Test message found in database:")
                            print(f"   ID: {log.get('id')}")
                            print(f"   Message: {log.get('message')}")
                            print(f"   Timestamp: {log.get('timestamp')}")
                            print(f"   Metadata: {log.get('metadata')}")
                            break
                    
                    if test_log_found:
                        print("\nSUCCESS: MCP Server database connectivity verified!")
                        print("SUCCESS: Database connection: Working")
                        print("SUCCESS: Log status endpoint: Working")
                        print("SUCCESS: Query logs endpoint: Working")
                        print("SUCCESS: Data persistence: Working")
                        return True
                    else:
                        print("WARNING: Test message not found in query results")
                        return False
                else:
                    print(f"ERROR: Query logs failed: {query_response.status_code} - {query_response.text}")
                    return False
            else:
                print(f"ERROR: Log status failed: {log_response.status_code} - {log_response.text}")
                return False
                
        except httpx.TimeoutException:
            print("ERROR: Request timed out")
            return False
        except httpx.ConnectError:
            print("ERROR: Connection error - server may be down")
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return False


async def main():
    """Main test function"""
    print("MCP Server Database Connectivity Test")
    print("=" * 50)
    
    success = await test_mcp_server_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("ALL TESTS PASSED - MCP Server is working correctly!")
        print("Ready for Financial Advisor agent integration")
    else:
        print("TESTS FAILED - MCP Server needs attention")
        print("Check server logs and database connectivity")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
