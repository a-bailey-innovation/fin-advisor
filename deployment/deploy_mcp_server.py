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

"""Cloud Run Deployment Script for MCP Server"""

import os
import subprocess
import sys
from typing import Optional

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    
    # Use PowerShell execution policy bypass for gcloud commands on Windows
    if cmd[0] == "gcloud" and os.name == "nt":
        # Properly escape the command for PowerShell
        cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd[1:])
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", f"gcloud {cmd_str}"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if result.stdout:
        print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result

def get_project_id() -> str:
    """Get the current GCP project ID"""
    result = run_command(["gcloud", "config", "get-value", "project"])
    project_id = result.stdout.strip()
    if not project_id:
        raise ValueError("No GCP project configured. Run 'gcloud config set project PROJECT_ID'")
    return project_id

def create_service_account(service_account_name: str = "finadvisor-mcp-server") -> bool:
    """Create service account for Cloud Run"""
    try:
        project_id = get_project_id()
        service_account_email = f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
        
        # Check if service account exists
        result = run_command([
            "gcloud", "iam", "service-accounts", "describe", service_account_email,
            "--format", "value(email)"
        ], check=False)
        
        if result.returncode == 0:
            print(f"Service account '{service_account_email}' already exists")
            return True
        
        # Create service account
        print(f"Creating service account '{service_account_name}'...")
        run_command([
            "gcloud", "iam", "service-accounts", "create", service_account_name,
            "--display-name", "Financial Advisor MCP Server",
            "--description", "Service account for Financial Advisor MCP Server on Cloud Run"
        ])
        
        # Add Cloud SQL Client role
        print("Adding Cloud SQL Client role...")
        run_command([
            "gcloud", "projects", "add-iam-policy-binding", project_id,
            "--member", f"serviceAccount:{service_account_email}",
            "--role", "roles/cloudsql.client"
        ])
        
        print(f"Service account '{service_account_email}' created successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create service account: {e}")
        return False

def build_and_deploy(
    service_name: str = "finadvisor-mcp-server",
    region: str = "us-central1",
    vpc_connector: str = "finadvisor-vpc-connector",
    service_account: str = "finadvisor-mcp-server"
) -> Optional[str]:
    """Build and deploy the MCP server to Cloud Run"""
    try:
        project_id = get_project_id()
        service_account_email = f"{service_account}@{project_id}.iam.gserviceaccount.com"
        
        # Get environment variables
        db_user = os.getenv("DB_USER", "finadvisor_user")
        db_password = os.getenv("DB_PASSWORD", "FinAdvisorUser2024!")
        db_name = os.getenv("DB_NAME", "FinAdvisor")
        db_host = os.getenv("DB_HOST", "34.29.136.71")
        db_port = os.getenv("DB_PORT", "5432")
        cloudsql_private_ip = os.getenv("CLOUDSQL_PRIVATE_IP")
        use_private_ip = os.getenv("USE_PRIVATE_IP", "false")
        
        # Build environment variables
        env_vars = [
            f"DB_USER={db_user}",
            f"DB_PASSWORD={db_password}",
            f"DB_NAME={db_name}",
            f"DB_HOST={db_host}",
            f"DB_PORT={db_port}",
            f"USE_PRIVATE_IP={use_private_ip}",
            f"ENABLE_CORS=true",
            f"CORS_ORIGINS=*",
            f"LOG_LEVEL=INFO",
        ]
        
        if cloudsql_private_ip:
            env_vars.append(f"CLOUDSQL_PRIVATE_IP={cloudsql_private_ip}")
        
        # Deploy to Cloud Run
        print(f"Deploying '{service_name}' to Cloud Run...")
        cmd = [
            "gcloud", "run", "deploy", service_name,
            "--source", "mcp_server",
            "--platform", "managed",
            "--region", region,
            "--project", project_id,
            "--service-account", service_account_email,
            "--memory", "512Mi",
            "--cpu", "1",
            "--max-instances", "10",
            "--min-instances", "0",
            "--concurrency", "100",
            "--timeout", "300",
            "--set-env-vars", ",".join(env_vars),
            "--no-allow-unauthenticated"
        ]
        
        # Add VPC connector if specified
        if vpc_connector:
            cmd.extend(["--vpc-connector", vpc_connector])
        
        result = run_command(cmd)
        
        # Extract service URL from output
        output_lines = result.stdout.split('\n')
        service_url = None
        for line in output_lines:
            if "Service URL:" in line:
                service_url = line.split("Service URL:")[1].strip()
                break
        
        if service_url:
            print(f"Service deployed successfully!")
            print(f"Service URL: {service_url}")
            return service_url
        else:
            print("Failed to extract service URL")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to deploy service: {e}")
        return None

def test_deployment(service_url: str) -> bool:
    """Test the deployed service"""
    try:
        print(f"Testing deployed service at {service_url}...")
        
        # Test health endpoint
        result = run_command([
            "curl", "-f", f"{service_url}/health"
        ], check=False)
        
        if result.returncode == 0:
            print("Health check passed")
            return True
        else:
            print("Health check failed")
            return False
            
    except Exception as e:
        print(f"Failed to test deployment: {e}")
        return False

def main():
    """Main function to deploy MCP server to Cloud Run"""
    print("Deploying MCP Server to Cloud Run...")
    
    # Get configuration from environment or use defaults
    service_name = os.getenv("MCP_SERVICE_NAME", "finadvisor-mcp-server")
    region = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    vpc_connector = os.getenv("VPC_CONNECTOR_NAME", "finadvisor-vpc-connector")
    service_account = os.getenv("MCP_SERVICE_ACCOUNT", "finadvisor-mcp-server")
    
    # Use actual project details
    project_id = get_project_id()
    if project_id == "agent-space-demo-475212":
        print(f"Using project: {project_id}")
    else:
        print(f"Unexpected project: {project_id}")
    
    print(f"Service Name: {service_name}")
    print(f"Region: {region}")
    print(f"VPC Connector: {vpc_connector}")
    print(f"Service Account: {service_account}")
    
    success = True
    
    # Step 1: Create service account
    if not create_service_account(service_account):
        success = False
    
    # Step 2: Build and deploy
    if success:
        service_url = build_and_deploy(service_name, region, vpc_connector, service_account)
        if not service_url:
            success = False
    
    # Step 3: Test deployment
    if success and service_url:
        if not test_deployment(service_url):
            success = False
    
    if success:
        print(f"\nMCP Server deployed successfully!")
        print(f"Service URL: {service_url}")
        print(f"\nNext steps:")
        print(f"1. Set MCP_SERVER_URL={service_url} in your environment")
        print(f"2. Set USE_MCP_HTTP_SERVER=true in your environment")
        print(f"3. Update the Financial Advisor agent to use the HTTP server")
    else:
        print("Deployment failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

