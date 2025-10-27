#!/usr/bin/env python3
print("Python startup script starting...")
print("Script is working")
print("Starting FastAPI server...")

import subprocess
cmd = ["python3", "-m", "uvicorn", "http_server:app", "--host", "0.0.0.0", "--port", "8080"]
print(f"Using command: {' '.join(cmd)}")

try:
    subprocess.run(cmd, check=True)
except Exception as e:
    print(f"Failed to start FastAPI server: {e}")
    import sys
    sys.exit(1)
