#!/usr/bin/env python3
"""Test CloudSQL database connection and create schema"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.db_operations import db_manager
from mcp_server.config import DATABASE_URL

async def test_connection():
    """Test database connection and create schema"""
    try:
        print("Testing CloudSQL connection...")
        print(f"Database URL: {DATABASE_URL}")
        
        # Connect to database
        await db_manager.connect()
        print("✅ Successfully connected to CloudSQL")
        
        # Create tables
        await db_manager.create_tables()
        print("✅ Database tables created/verified")
        
        # Test logging a status message
        log_id = await db_manager.log_status(
            session_id="test_session",
            user_id="test_user",
            agent_name="test_agent",
            status_type="info",
            message="Test connection successful",
            metadata={"test": True}
        )
        print(f"✅ Successfully logged test message with ID: {log_id}")
        
        # Test querying logs
        logs = await db_manager.get_recent_logs(limit=5)
        print(f"✅ Retrieved {len(logs)} recent logs")
        for log in logs:
            print(f"  - {log['timestamp']}: {log['agent_name']} - {log['message']}")
        
        print("\n🎉 All tests passed! CloudSQL integration is working.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await db_manager.close()
        print("Database connection closed")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
