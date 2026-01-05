#!/usr/bin/env python3
"""
Test script for rest_executor API
Creates a 'project' directory via API call
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8787"
EXECUTOR_TOKEN = "6c9f1e4b5a2d8f7c0b3e9a4d7f2c1e8"

def test_create_directory():
    """Test creating a 'project' directory via the API"""

    payload = {
        "command": "mkdir project",
        "cwd": "."
    }

    try:
        url = f"{API_BASE_URL}/run"
        headers = {
            "Authorization": f"Bearer {EXECUTOR_TOKEN}",
            "Content-Type": "application/json"
        }

        print(f"Testing API at: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code in [200, 201]:
            print("\n✓ Command executed successfully!")
            result = response.json()
            if 'output' in result:
                print(f"Output: {result['output']}")
        else:
            print(f"\n✗ Failed with status code {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to {API_BASE_URL}")
        print("  Make sure the server is running")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_create_directory()
