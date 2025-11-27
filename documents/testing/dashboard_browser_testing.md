# Dashboard Agent Browser Testing Capability

## Overview

The `dashboard-agent` now has the ability to launch a test browser to verify that the dashboard is working correctly. This capability is useful for automated testing, debugging, and verification workflows.

## What Was Added

### 1. Agent Configuration (`agent.json`)
Added a new capability called `start_test_browser` with the following schema:

```json
{
  "name": "start_test_browser",
  "description": "Launch a test browser instance to verify the dashboard is working correctly.",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "URL to open in the browser (defaults to localhost:3000)"
      },
      "headless": {
        "type": "boolean",
        "description": "Whether to run in headless mode (defaults to false)"
      }
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "success": {
        "type": "boolean"
      },
      "message": {
        "type": "string"
      },
      "browser_pid": {
        "type": "integer",
        "description": "Process ID of the launched browser"
      }
    }
  }
}
```

### 2. Implementation (`main.py`)

Added the `start_test_browser()` function that:
- Automatically detects available browsers (Chrome/Chromium)
- Supports both headless and GUI modes
- Returns the browser process ID for tracking
- Logs all actions to the RAG memory system

Updated the agent loop to handle browser test requests by checking for keywords like "browser" or "test" in the task description.

## How to Use

### Method 1: Using the Test Script

We've provided a convenient test script:

```bash
# Launch browser with default settings (localhost:3000, GUI mode)
python test_dashboard_browser.py

# Launch browser with custom URL
python test_dashboard_browser.py --url http://localhost:8080

# Launch browser in headless mode
python test_dashboard_browser.py --headless

# Combine options
python test_dashboard_browser.py --url http://localhost:3000 --headless
```

### Method 2: Using Agent Messaging Directly

You can send a JSON-RPC message to the agent:

```python
from agent_messaging import post_message, create_jsonrpc_request

request_params = {
    "description": "launch test browser",
    "url": "http://localhost:3000",
    "headless": False
}

request = create_jsonrpc_request(
    method="agent.execute_task",
    params=request_params
)

post_message(
    message=request,
    topic="ops",
    from_agent="your-agent-name"
)
```

### Method 3: Natural Language Request

If you have an orchestrator agent, you can simply ask:

```
"Please launch a test browser for the dashboard"
"Open the dashboard in a browser for testing"
"Start a headless browser test"
```

## Browser Detection

The agent automatically searches for browsers in this order:

1. `google-chrome`
2. `chromium-browser`
3. `chromium`
4. `/usr/bin/google-chrome`
5. `/usr/bin/chromium-browser`
6. `/usr/bin/chromium`

If no suitable browser is found, it will return an error message asking you to install Chrome or Chromium.

## Response Format

The agent responds with a JSON-RPC result containing:

```json
{
  "success": true,
  "message": "Browser launched successfully (PID: 12345)",
  "browser_pid": 12345
}
```

Or on failure:

```json
{
  "success": false,
  "message": "No suitable browser found. Please install Chrome or Chromium.",
  "browser_pid": null
}
```

## Testing the Integration

1. **Ensure the dashboard server is running:**
   ```bash
   cd /home/adamsl/planner/dashboard
   npm start
   ```

2. **Start the dashboard ops agent (if not already running):**
   ```bash
   cd /home/adamsl/planner/dashboard_ops_agent
   python main.py
   ```

3. **Run the test script:**
   ```bash
   cd /home/adamsl/planner
   python test_dashboard_browser.py
   ```

4. **Verify:** A browser window should open displaying the dashboard at `http://localhost:3000`

## Memory Logging

All browser launch attempts are logged to the RAG memory system with:
- **Type:** `runlog` or `error`
- **Source:** `dashboard-agent`
- **Project:** `dashboard`
- **Details:** URL, headless mode, browser path, and PID

You can query these logs later for debugging or audit purposes.

## Troubleshooting

### No browser found
- **Issue:** Agent reports "No suitable browser found"
- **Solution:** Install Chrome or Chromium:
  ```bash
  # Ubuntu/Debian
  sudo apt install chromium-browser
  
  # Or Google Chrome
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  sudo dpkg -i google-chrome-stable_current_amd64.deb
  ```

### Browser launches but shows blank page
- **Issue:** Browser opens but doesn't load the dashboard
- **Solution:** Ensure the dashboard server is running on the expected port (default: 3000)
- **Check:** Run `curl http://localhost:3000` to verify the server responds

### Agent not responding
- **Issue:** No response after sending the request
- **Solution:** 
  - Verify the dashboard-agent is running
  - Check the agent logs for errors
  - Ensure you're posting to the correct topic ("ops")

## Next Steps

Now that the browser testing capability is available, you can:

1. **Integrate with CI/CD:** Add automated browser tests to your build pipeline
2. **Create Test Suites:** Build comprehensive test scenarios using the agent
3. **Add Screenshot Capability:** Extend the agent to capture screenshots
4. **Implement Assertions:** Add validation to verify specific elements are present
5. **Add Playwright/Selenium:** Integrate more advanced browser automation tools

## Files Modified

- `/home/adamsl/planner/dashboard_ops_agent/agent.json` - Added capability definition
- `/home/adamsl/planner/dashboard_ops_agent/main.py` - Added browser launch function and handler
- `/home/adamsl/planner/test_dashboard_browser.py` - Created test script
- `/home/adamsl/planner/DASHBOARD_BROWSER_TESTING.md` - This documentation

## Example Workflow

Here's a complete workflow demonstrating the capability:

```python
#!/usr/bin/env python3
"""Example: Automated dashboard verification workflow"""

import time
from agent_messaging import post_message, create_jsonrpc_request, inbox

def verify_dashboard():
    # Step 1: Check if server is running
    print("Step 1: Checking server status...")
    request = create_jsonrpc_request(
        method="agent.execute_task",
        params={"description": "check status"}
    )
    post_message(request, topic="ops", from_agent="workflow")
    time.sleep(2)
    
    # Step 2: Launch test browser
    print("Step 2: Launching test browser...")
    request = create_jsonrpc_request(
        method="agent.execute_task",
        params={
            "description": "launch test browser",
            "url": "http://localhost:3000",
            "headless": False
        }
    )
    post_message(request, topic="ops", from_agent="workflow")
    time.sleep(3)
    
    # Step 3: Check results
    print("Step 3: Checking results...")
    messages = inbox("ops", limit=10)
    for msg in messages:
        print(f"  {msg.content}")
    
    print("\nWorkflow complete!")

if __name__ == "__main__":
    verify_dashboard()
```

---

**Created:** 2025-11-19  
**Author:** Dashboard Agent Enhancement  
**Version:** 1.0
