#!/usr/bin/env python3
"""
Simple test to verify Cloud SQL Proxy configuration works
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the mcp_server directory to the path
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from config import get_database_url
from db_operations import DatabaseManager

async def test_simple_connection():
    """Test simple database connection"""
    print("Testing Cloud SQL Proxy configuration...")
    
    # Get database URL
    database_url = get_database_url()
    print(f"Database URL: {database_url.replace(os.getenv('DB_PASSWORD', ''), '***')}")
    
    # Test connection
    db_manager = DatabaseManager()
    
    try:
        await db_manager.connect()
        print("✅ Database connection successful!")
        
        # Test basic query
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1 as test")
            print(f"✅ Query test successful: {result}")
            
            # Test insert
            test_id = await conn.fetchval("""
                INSERT INTO agent_status_logs 
                (session_id, user_id, agent_name, status_type, message)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, "proxy_test", "test_user", "proxy_test", "info", "Cloud SQL Proxy test")
            print(f"✅ Insert test successful: ID = {test_id}")
        
        await db_manager.close()
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_connection())
    sys.exit(0 if success else 1)
