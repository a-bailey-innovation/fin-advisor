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

"""VPC Setup Script for CloudSQL Private IP Access"""

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
        cmd_str = " ".join(cmd[1:])  # Skip 'gcloud' and join the rest
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

def create_vpc_network(network_name: str = "finadvisor-vpc") -> bool:
    """Create VPC network if it doesn't exist"""
    try:
        # Check if network exists
        result = run_command([
            "gcloud", "compute", "networks", "describe", network_name,
            "--format", "value(name)"
        ], check=False)
        
        if result.returncode == 0:
            print(f"VPC network '{network_name}' already exists")
            return True
        
        # Create the network
        print(f"Creating VPC network '{network_name}'...")
        run_command([
            "gcloud", "compute", "networks", "create", network_name,
            "--subnet-mode", "auto",
            "--description", "VPC network for Financial Advisor CloudSQL access"
        ])
        print(f"VPC network '{network_name}' created successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create VPC network: {e}")
        return False

def create_vpc_connector(
    connector_name: str = "finadvisor-vpc-connector",
    network_name: str = "finadvisor-vpc",
    region: str = "us-central1",
    ip_range: str = "10.8.0.0/28"
) -> bool:
    """Create VPC connector for Cloud Run"""
    try:
        # Check if connector exists
        result = run_command([
            "gcloud", "compute", "networks", "vpc-access", "connectors", "describe", connector_name,
            "--region", region,
            "--format", "value(name)"
        ], check=False)
        
        if result.returncode == 0:
            print(f"VPC connector '{connector_name}' already exists")
            return True
        
        # Create the connector
        print(f"Creating VPC connector '{connector_name}'...")
        run_command([
            "gcloud", "compute", "networks", "vpc-access", "connectors", "create", connector_name,
            "--region", region,
            "--subnet", f"{network_name}-subnet",
            "--subnet-project", get_project_id(),
            "--range", ip_range,
            "--min-instances", "2",
            "--max-instances", "3"
        ])
        print(f"VPC connector '{connector_name}' created successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create VPC connector: {e}")
        return False

def enable_cloudsql_private_ip(
    instance_name: str = "finadvisor-db",
    network_name: str = "finadvisor-vpc"
) -> bool:
    """Enable private IP for CloudSQL instance"""
    try:
        # Check if private IP is already enabled
        result = run_command([
            "gcloud", "sql", "instances", "describe", instance_name,
            "--format", "value(settings.ipConfiguration.privateNetwork)"
        ], check=False)
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"Private IP already enabled for CloudSQL instance '{instance_name}'")
            return True
        
        # Enable private IP
        print(f"Enabling private IP for CloudSQL instance '{instance_name}'...")
        run_command([
            "gcloud", "sql", "instances", "patch", instance_name,
            "--network", f"projects/{get_project_id()}/global/networks/{network_name}",
            "--no-assign-ip"
        ])
        print(f"Private IP enabled for CloudSQL instance '{instance_name}'")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to enable private IP for CloudSQL: {e}")
        return False

def get_cloudsql_private_ip(instance_name: str = "finadvisor-db") -> Optional[str]:
    """Get the private IP address of the CloudSQL instance"""
    try:
        result = run_command([
            "gcloud", "sql", "instances", "describe", instance_name,
            "--format", "value(ipAddresses[0].ipAddress)"
        ])
        
        private_ip = result.stdout.strip()
        if private_ip:
            print(f"CloudSQL private IP: {private_ip}")
            return private_ip
        else:
            print("No private IP found for CloudSQL instance")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to get CloudSQL private IP: {e}")
        return None

def create_firewall_rules(network_name: str = "finadvisor-vpc") -> bool:
    """Create firewall rules for CloudSQL access"""
    try:
        # Allow CloudSQL access from VPC
        rule_name = f"allow-cloudsql-{network_name}"
        
        # Check if rule exists
        result = run_command([
            "gcloud", "compute", "firewall-rules", "describe", rule_name,
            "--format", "value(name)"
        ], check=False)
        
        if result.returncode == 0:
            print(f"Firewall rule '{rule_name}' already exists")
            return True
        
        # Create firewall rule
        print(f"Creating firewall rule '{rule_name}'...")
        run_command([
            "gcloud", "compute", "firewall-rules", "create", rule_name,
            "--network", network_name,
            "--allow", "tcp:5432",
            "--source-ranges", "10.8.0.0/28",
            "--description", "Allow CloudSQL access from VPC connector"
        ])
        print(f"Firewall rule '{rule_name}' created successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create firewall rules: {e}")
        return False

def main():
    """Main function to set up VPC for CloudSQL private IP access"""
    print("Setting up VPC for CloudSQL private IP access...")
    
    # Get configuration from environment or use defaults
    project_id = get_project_id()
    network_name = os.getenv("VPC_NETWORK_NAME", "finadvisor-vpc")
    connector_name = os.getenv("VPC_CONNECTOR_NAME", "finadvisor-vpc-connector")
    region = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    instance_name = os.getenv("CLOUDSQL_INSTANCE_NAME", "finadvisor-db")
    
    print(f"Project ID: {project_id}")
    print(f"Network Name: {network_name}")
    print(f"Connector Name: {connector_name}")
    print(f"Region: {region}")
    print(f"CloudSQL Instance: {instance_name}")
    
    success = True
    
    # Step 1: Create VPC network
    if not create_vpc_network(network_name):
        success = False
    
    # Step 2: Create VPC connector
    if success and not create_vpc_connector(connector_name, network_name, region):
        success = False
    
    # Step 3: Enable CloudSQL private IP
    if success and not enable_cloudsql_private_ip(instance_name, network_name):
        success = False
    
    # Step 4: Create firewall rules
    if success and not create_firewall_rules(network_name):
        success = False
    
    # Step 5: Get private IP
    if success:
        private_ip = get_cloudsql_private_ip(instance_name)
        if private_ip:
            print(f"\nVPC setup completed successfully!")
            print(f"CloudSQL Private IP: {private_ip}")
            print(f"VPC Connector: {connector_name}")
            print(f"\nNext steps:")
            print(f"1. Set CLOUDSQL_PRIVATE_IP={private_ip} in your environment")
            print(f"2. Set USE_PRIVATE_IP=true in your environment")
            print(f"3. Deploy the MCP server to Cloud Run with VPC connector")
        else:
            print("Failed to get CloudSQL private IP")
            success = False
    else:
        print("VPC setup failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

