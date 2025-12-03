#!/usr/bin/env python3
"""
Test script to demonstrate the dashboard agent's browser testing capability.
This script sends a message to the dashboard-agent to launch a test browser.
"""

import sys
import os
import time

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from a2a_communicating_agents.agent_messaging import post_message, inbox, create_jsonrpc_request

def test_browser_launch(url=None, headless=False):
    """Send a request to launch a test browser"""
    
    # Create a JSON-RPC request for the dashboard ops agent
    request_params = {
        "description": "launch test browser",
        "url": url or "http://localhost:3000",
        "headless": headless
    }
    
    request = create_jsonrpc_request(
        method="agent.execute_task",
        params=request_params
    )
    
    print(f"Sending browser test request to dashboard-agent...")
    print(f"  URL: {request_params['url']}")
    print(f"  Headless: {request_params['headless']}")
    
    # Post the message to the ops topic
    post_message(
        message=request,
        topic="ops",
        from_agent="test-script"
    )
    
    print("\nRequest sent! Waiting for response...")
    
    # Wait a bit for the agent to process
    time.sleep(3)
    
    # Check inbox for response
    messages = inbox("ops", limit=10)
    
    for msg in messages:
        if "browser" in msg.content.lower() or "pid" in msg.content.lower():
            print(f"\nResponse received:")
            print(msg.content)
            break
    else:
        print("\nNo response yet. The agent may be processing the request.")
        print("Check the dashboard-agent logs for more details.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the dashboard browser launching capability")
    parser.add_argument("--url", help="URL to open (default: http://localhost:3000)", default=None)
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    test_browser_launch(url=args.url, headless=args.headless)
