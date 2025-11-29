"""
TDD Test: Verify Letta Server Can Start and Respond to Health Checks
"""
import requests
import time
import subprocess
import sys


def test_letta_health_endpoint():
    """Test: Letta server /health endpoint returns 200 OK"""
    health_url = "http://localhost:8283/v1/health/"
    timeout = 5  # seconds

    print("=" * 60)
    print("TDD: Testing Letta Server Health Endpoint")
    print("=" * 60)

    try:
        print(f"\n[TEST] Attempting to connect to {health_url}...")
        response = requests.get(health_url, timeout=timeout)

        if response.status_code == 200:
            print(f"[PASS] Health endpoint returned 200 OK")
            print(f"[PASS] Response: {response.text}")
            return True
        else:
            print(f"[FAIL] Health endpoint returned status {response.status_code}")
            print(f"       Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Cannot connect to Letta server on port 8283")
        print(f"       Server may not be running.")
        print(f"\n[HINT] Start the server with: letta server")
        return False

    except requests.exceptions.Timeout:
        print(f"[FAIL] Connection timed out after {timeout} seconds")
        return False

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_letta_health_endpoint()
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Letta server is running and healthy!")
    else:
        print("[FAIL] Letta server is not accessible")
    print("=" * 60)
    sys.exit(0 if success else 1)
