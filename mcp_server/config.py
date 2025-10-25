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

# CloudSQL Configuration
CLOUDSQL_CONNECTION_NAME = os.getenv("CLOUDSQL_CONNECTION_NAME", "agent-space-demo-475212:us-central1:finadvisor-db")
DB_NAME = os.getenv("DB_NAME", "FinAdvisor")
DB_USER = os.getenv("DB_USER", "finadvisor_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "FinAdvisorUser2024!")
DB_HOST = os.getenv("DB_HOST", "34.29.136.71")  # Public IP from instance creation
DB_PORT = os.getenv("DB_PORT", "5432")

# MCP Server Configuration
MCP_SERVER_NAME = "finadvisor-db-server"
MCP_SERVER_VERSION = "1.0.0"

# Database connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
