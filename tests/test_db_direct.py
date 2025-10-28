#!/usr/bin/env python3
"""
Test script to verify MCP server database connectivity from within Cloud Run
"""

import asyncio
import os
import sys
from datetime import datetime

import asyncpg


async def test_database_connection():
    """Test database connection directly"""
    print("Testing direct database connection...")
    
    # Get database configuration from environment
    db_user = os.getenv("DB_USER", "finadvisor_user")
    db_password = os.getenv("DB_PASSWORD", "FinAdvisorUser2024!")
    db_name = os.getenv("DB_NAME", "FinAdvisor")
    db_port = os.getenv("DB_PORT", "5432")
    
    # Use private IP if configured
    use_private_ip = os.getenv("USE_PRIVATE_IP", "false").lower() == "true"
    cloudsql_private_ip = os.getenv("CLOUDSQL_PRIVATE_IP")
    
    if use_private_ip and cloudsql_private_ip:
        db_host = cloudsql_private_ip
        print(f"Using private IP: {db_host}")
    else:
        db_host = os.getenv("DB_HOST", "34.29.136.71")
        print(f"Using public IP: {db_host}")
    
    # Build connection string
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"Connection string: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
    
    try:
        # Test connection
        print("Attempting to connect to database...")
        conn = await asyncpg.connect(connection_string, timeout=30)
        
        # Test basic query
        print("Testing basic query...")
        result = await conn.fetchval("SELECT 1")
        print(f"Query result: {result}")
        
        # Test table existence
        print("Checking if status_logs table exists...")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'status_logs'
            )
        """)
        print(f"Table exists: {table_exists}")
        
        if table_exists:
            # Test inserting a test record
            print("Testing insert operation...")
            test_data = {
                "session_id": "test_session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                "user_id": "test_user",
                "agent_name": "direct_db_test",
                "status_type": "info",
                "message": f"Direct database connectivity test - {datetime.now().isoformat()}",
                "metadata": {"test": True, "direct_connection": True}
            }
            
            log_id = await conn.fetchval("""
                INSERT INTO status_logs (session_id, user_id, agent_name, status_type, message, metadata, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING id
            """, 
                test_data["session_id"],
                test_data["user_id"], 
                test_data["agent_name"],
                test_data["status_type"],
                test_data["message"],
                test_data["metadata"]
            )
            print(f"Insert successful! Log ID: {log_id}")
            
            # Test querying the record
            print("Testing query operation...")
            record = await conn.fetchrow("""
                SELECT id, session_id, user_id, agent_name, status_type, message, metadata, timestamp
                FROM status_logs 
                WHERE id = $1
            """, log_id)
            
            if record:
                print(f"Query successful! Record found:")
                print(f"  ID: {record['id']}")
                print(f"  Message: {record['message']}")
                print(f"  Timestamp: {record['timestamp']}")
                print(f"  Metadata: {record['metadata']}")
            else:
                print("ERROR: Record not found after insert")
                return False
        
        await conn.close()
        print("SUCCESS: Database connection test passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return False


async def main():
    """Main test function"""
    print("Direct Database Connectivity Test")
    print("=" * 50)
    
    success = await test_database_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: Database connectivity verified!")
        print("The MCP server should be able to connect to the database")
    else:
        print("ERROR: Database connectivity failed")
        print("Check VPC connector and CloudSQL configuration")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
