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

"""Configuration management for MCP Server"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cloud Run Configuration
CLOUD_RUN_MODE = os.getenv("CLOUD_RUN_MODE", "false").lower() == "true"
VPC_CONNECTOR_NAME = os.getenv("VPC_CONNECTOR_NAME", "finadvisor-vpc-connector")

# CloudSQL Configuration
CLOUDSQL_CONNECTION_NAME = os.getenv("CLOUDSQL_CONNECTION_NAME", "agent-space-demo-475212:us-central1:finadvisor-db")
DB_NAME = os.getenv("DB_NAME", "FinAdvisor")
DB_USER = os.getenv("DB_USER", "finadvisor_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "FinAdvisorUser2024!")
DB_HOST = os.getenv("DB_HOST", "34.29.136.71")  # Public IP from instance creation
DB_PORT = os.getenv("DB_PORT", "5432")

# CloudSQL Private IP Configuration (for VPC connector)
CLOUDSQL_PRIVATE_IP = os.getenv("CLOUDSQL_PRIVATE_IP")  # Set by CloudSQL when private IP is enabled
USE_PRIVATE_IP = os.getenv("USE_PRIVATE_IP", "false").lower() == "true"

# MCP Server Configuration
MCP_SERVER_NAME = "finadvisor-db-server"
MCP_SERVER_VERSION = "1.0.0"

# HTTP Server Configuration
HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))

# Database connection configuration
def get_database_url() -> str:
    """Get database URL based on configuration"""
    print(f"DEBUG: CLOUD_RUN_MODE={CLOUD_RUN_MODE}")
    print(f"DEBUG: USE_PRIVATE_IP={USE_PRIVATE_IP}")
    print(f"DEBUG: CLOUDSQL_PRIVATE_IP={CLOUDSQL_PRIVATE_IP}")
    print(f"DEBUG: CLOUDSQL_CONNECTION_NAME={CLOUDSQL_CONNECTION_NAME}")
    
    if CLOUD_RUN_MODE and USE_PRIVATE_IP and CLOUDSQL_PRIVATE_IP:
        # Use private IP for VPC connector
        host = CLOUDSQL_PRIVATE_IP
        print(f"Using private IP: {host}")
    elif CLOUD_RUN_MODE and CLOUDSQL_CONNECTION_NAME and os.getenv("VPC_CONNECTOR_NAME"):
        # Use Cloud SQL Proxy for Cloud Run with VPC connector
        host = "127.0.0.1"  # Cloud SQL Proxy listens on localhost
        print(f"Using Cloud SQL Proxy: {host}")
    else:
        # Use public IP (fallback)
        host = DB_HOST
        print(f"Using public IP: {host}")
    
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{host}:{DB_PORT}/{DB_NAME}"

# Database connection string - will be set at runtime
DATABASE_URL = None
