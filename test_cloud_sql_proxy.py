#!/usr/bin/env python3
"""
Test Cloud SQL Proxy connectivity for MCP Server
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the mcp_server directory to the path
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from config import get_database_url, CLOUDSQL_CONNECTION_NAME
from db_operations import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_cloud_sql_proxy():
    """Test Cloud SQL Proxy connectivity"""
    print("=" * 60)
    print("Cloud SQL Proxy Connectivity Test")
    print("=" * 60)
    
    # Check environment variables
    print("\n📋 Environment Configuration:")
    print(f"CLOUDSQL_CONNECTION_NAME: {CLOUDSQL_CONNECTION_NAME}")
    print(f"DB_USER: {os.getenv('DB_USER', 'Not set')}")
    print(f"DB_NAME: {os.getenv('DB_NAME', 'Not set')}")
    print(f"DB_HOST: {os.getenv('DB_HOST', 'Not set')}")
    print(f"DB_PORT: {os.getenv('DB_PORT', 'Not set')}")
    
    # Get database URL
    database_url = get_database_url()
    print(f"\n🔗 Database URL: {database_url.replace(os.getenv('DB_PASSWORD', ''), '***')}")
    
    # Test connection
    print("\n🧪 Testing Database Connection:")
    db_manager = DatabaseManager()
    
    try:
        await db_manager.connect()
        print("✅ Database connection successful!")
        
        # Test basic query
        print("\n📊 Testing basic query...")
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1 as test_value")
            print(f"✅ Query test successful: {result}")
            
            # Test table existence
            print("\n📋 Checking table existence...")
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'agent_status_logs'
                )
            """)
            print(f"✅ Table check: agent_status_logs exists = {table_exists}")
            
            if not table_exists:
                print("\n🔧 Creating tables...")
                await db_manager.create_tables()
                print("✅ Tables created successfully!")
            
            # Test insert
            print("\n📝 Testing insert operation...")
            test_id = await conn.fetchval("""
                INSERT INTO agent_status_logs 
                (session_id, user_id, agent_name, status_type, message, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, "test_session", "test_user", "test_agent", "info", "Cloud SQL Proxy test", '{"test": true}')
            print(f"✅ Insert test successful: ID = {test_id}")
            
            # Test select
            print("\n📖 Testing select operation...")
            logs = await conn.fetch("""
                SELECT id, agent_name, status_type, message, timestamp
                FROM agent_status_logs 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            print(f"✅ Select test successful: Found {len(logs)} records")
            for log in logs:
                print(f"   - {log['timestamp']}: {log['agent_name']} - {log['message']}")
        
        await db_manager.close()
        print("\n🎉 All tests passed! Cloud SQL Proxy is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

async def test_direct_connection():
    """Test direct connection (fallback)"""
    print("\n" + "=" * 60)
    print("Direct Connection Test (Fallback)")
    print("=" * 60)
    
    import asyncpg
    
    db_user = os.getenv("DB_USER", "finadvisor_user")
    db_password = os.getenv("DB_PASSWORD", "FinAdvisorUser2024!")
    db_name = os.getenv("DB_NAME", "FinAdvisor")
    db_host = os.getenv("DB_HOST", "34.29.136.71")
    db_port = os.getenv("DB_PORT", "5432")
    
    direct_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"🔗 Direct URL: {direct_url.replace(db_password, '***')}")
    
    try:
        conn = await asyncpg.connect(direct_url, command_timeout=10)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        print(f"✅ Direct connection successful: {result}")
        return True
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Starting Cloud SQL Proxy connectivity tests...")
    
    # Test Cloud SQL Proxy first
    proxy_success = await test_cloud_sql_proxy()
    
    # Test direct connection as fallback
    direct_success = await test_direct_connection()
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Cloud SQL Proxy: {'✅ PASS' if proxy_success else '❌ FAIL'}")
    print(f"Direct Connection: {'✅ PASS' if direct_success else '❌ FAIL'}")
    
    if proxy_success:
        print("\n🎉 Cloud SQL Proxy is working! This is the recommended approach.")
    elif direct_success:
        print("\n⚠️  Cloud SQL Proxy failed, but direct connection works.")
        print("   This is acceptable for testing but not recommended for production.")
    else:
        print("\n❌ Both connection methods failed. Check your configuration.")
        return 1
    
    return 0

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
