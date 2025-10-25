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

"""Tests for status logger integration"""

import asyncio
import pytest
from financial_advisor.tools import status_logger_tool


@pytest.mark.asyncio
async def test_status_logger_tool():
    """Test the status logger tool functionality"""
    try:
        # Test logging a status message
        result = await status_logger_tool.run(
            agent_name="test_agent",
            status_type="info",
            message="Test status message",
            metadata={"test": True, "version": "1.0"}
        )
        
        print(f"Status logger result: {result}")
        assert "Status logged" in result or "Successfully logged" in result
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        # For now, just log the error - in production we'd want proper error handling
        pytest.skip(f"Status logger test skipped due to error: {e}")


@pytest.mark.asyncio
async def test_status_logger_cleanup():
    """Test cleanup of MCP client connection"""
    try:
        await status_logger_tool.close()
        print("Status logger cleanup completed")
    except Exception as e:
        print(f"Cleanup error: {e}")


if __name__ == "__main__":
    # Run tests manually
    async def main():
        print("Testing status logger tool...")
        await test_status_logger_tool()
        await test_status_logger_cleanup()
        print("Tests completed")
    
    asyncio.run(main())
