#!/usr/bin/env python3
"""
Test script for the Financial Advisor agent
"""

import os
import asyncio
from dotenv import load_dotenv
from vertexai import agent_engines

# Load environment variables
load_dotenv()

async def test_agent():
    """Test the deployed Financial Advisor agent"""
    
    # Get agent resource ID from environment
    agent_resource_id = os.getenv("AGENT_RESOURCE_ID")
    if not agent_resource_id:
        print("Error: AGENT_RESOURCE_ID not found in environment variables")
        return
    
    print("Testing Financial Advisor Agent")
    print("=" * 50)
    print(f"Agent Resource ID: {agent_resource_id}")
    print()
    
    try:
        # Get the deployed agent
        print("Connecting to deployed agent...")
        agent = agent_engines.get(agent_resource_id)
        print(f"Connected to agent: {agent.display_name}")
        print(f"Resource: {agent.resource_name}")
        print()
        
        # Create a session first
        print("Creating session...")
        session = agent.create_session(user_id="test_user")
        print(f"Session created: {session}")
        print()
        
        # Test queries
        test_queries = [
            "Hello! Can you help me analyze Apple stock (AAPL)?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"Test Query {i}: {query}")
            print("-" * 40)
            
            try:
                # Query the agent using stream_query
                print("Sending query to agent...")
                response_stream = agent.stream_query(
                    message=query,
                    user_id="test_user",
                    session_id=session['id']
                )
                
                print("Response received:")
                response_text = ""
                for chunk in response_stream:
                    if isinstance(chunk, dict) and 'content' in chunk:
                        content = chunk['content']
                        if 'parts' in content:
                            for part in content['parts']:
                                if 'text' in part:
                                    text = part['text']
                                    response_text += text
                                    print(text, end="", flush=True)
                                elif 'function_response' in part:
                                    func_resp = part['function_response']
                                    if 'response' in func_resp and 'result' in func_resp['response']:
                                        result = func_resp['response']['result']
                                        response_text += result
                                        print(result, end="", flush=True)
                
                print("\n")
                print("-" * 40)
                print()
                
            except Exception as e:
                print(f"Error querying agent: {e}")
                print()
        
        print("Agent testing completed!")
        
    except Exception as e:
        print(f"Error connecting to agent: {e}")
        print("Make sure the agent is deployed and running")

if __name__ == "__main__":
    asyncio.run(test_agent())
