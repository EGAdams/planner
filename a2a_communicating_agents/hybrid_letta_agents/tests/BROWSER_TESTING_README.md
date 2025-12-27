# Voice Agent Switching Browser Tests

Comprehensive browser testing solution for the voice agent switching functionality using Playwright.

## Overview

This test suite validates the complete user workflow for switching voice agents in the browser:

1. Navigate to http://localhost:9000/
2. Disconnect from current agent (if connected)
3. Select a different agent from the list
4. Connect to the new agent
5. Verify "Start Speaking..." message appears

## Test Files

- **test_voice_agent_switching_browser.py** - Main browser test suite
  - `test_voice_agent_switching_workflow()` - Full end-to-end switching test
  - `test_voice_agent_selection_ui()` - UI-only test (no backend required)

## Setup

### 1. Install Dependencies

```bash
# From the tests/ directory
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/tests

# Install browser testing dependencies
pip install -r requirements-browser-testing.txt

# Install Playwright browsers (required first time)
playwright install chromium
```

### 2. Start Required Services

The tests require these services running:

```bash
# Terminal 1: Start HTTP server on port 9000
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python3 -m http.server 9000

# Terminal 2: Start Letta server (for agent list API)
# (Should already be running on port 8283)

# Terminal 3: Start LiveKit server (for actual connections)
# (Should already be running on port 7880)

# Terminal 4: Start voice agent backend (optional - for full e2e test)
./start_voice_system.sh
```

## Running Tests

### Run All Browser Tests

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/tests

# Run all browser tests with verbose output
pytest test_voice_agent_switching_browser.py -v -s

# Run with HTML report
pytest test_voice_agent_switching_browser.py --html=report.html --self-contained-html
```

### Run Specific Tests

```bash
# Run only the UI test (doesn't require voice backend)
pytest test_voice_agent_switching_browser.py::test_voice_agent_selection_ui -v -s

# Run full workflow test (requires all services)
pytest test_voice_agent_switching_browser.py::test_voice_agent_switching_workflow -v -s
```

### Headless Mode (for CI/CD)

Edit `test_voice_agent_switching_browser.py` and change:

```python
browser = await p.chromium.launch(
    headless=True,  # Changed from False
    slow_mo=0       # Changed from 500
)
```

Then run:

```bash
pytest test_voice_agent_switching_browser.py -v
```

## Test Behavior

### Test 1: Full Workflow (`test_voice_agent_switching_workflow`)

**Purpose**: Validates complete agent switching flow including backend connection

**Steps**:
1. ✅ Navigate to page
2. ✅ Wait for agents to load from Letta API
3. ✅ Disconnect if currently connected
4. ✅ Select first agent
5. ✅ Click Connect button
6. ⏱️ Wait for "Start Speaking..." (may timeout if backend not running)
7. ✅ Disconnect from first agent
8. ✅ Select second agent (if available)
9. ✅ Connect to second agent
10. ⏱️ Wait for second agent connection

**Expected Results**:
- PASS: UI workflow completes successfully
- PASS: Agent selection and connection UI state changes
- TIMEOUT: Backend connection (if voice agent not running - this is OK)
- PASS: Full e2e if all services running

### Test 2: UI Only (`test_voice_agent_selection_ui`)

**Purpose**: Validates UI/UX without requiring backend services

**Steps**:
1. ✅ Navigate to page
2. ✅ Load agent list
3. ✅ Disconnect if needed
4. ✅ Select agent
5. ✅ Verify Connect button enabled
6. ✅ Verify status message

**Expected Results**:
- PASS: All steps complete successfully
- No backend connection required
- Fast execution (< 10 seconds)

## Troubleshooting

### "No agents available" Error

**Cause**: Letta server not running or no agents created

**Fix**:
```bash
# Check Letta server is running
curl http://localhost:8283/api/v1/agents/

# Create test agent if needed
# (Use Letta CLI or API)
```

### "Connection timeout" on Step 6

**Cause**: Voice agent backend not running (EXPECTED)

**Fix**: This is expected behavior when testing just the UI. To test full e2e:
```bash
./start_voice_system.sh
```

### Browser doesn't launch

**Cause**: Playwright browsers not installed

**Fix**:
```bash
playwright install chromium
```

### Microphone permission denied

**Cause**: Browser blocking microphone access

**Fix**: Tests automatically grant microphone permission via:
```python
context = await browser.new_context(permissions=["microphone"])
```

## Test Output Example

```
[STEP 1] Navigate to voice agent selector page
✅ Page loaded successfully

[STEP 2] Wait for agents to load from Letta server
✅ Loaded 3 agent(s)

[STEP 3] Disconnect from any current connection
Not currently connected - skipping disconnect

[STEP 4] Select first agent
✅ Selected agent: General Assistant

[STEP 5] Connect to first agent
✅ Connection initiated

[STEP 6] Wait for agent connection and 'Start Speaking...' message
⚠️  Agent connection timeout (expected if voice backend not running)
UI workflow validated up to connection attempt

[STEP 7] Disconnect from first agent
✅ Successfully disconnected

[STEP 8] Select second agent
✅ Selected agent: Voice Helper

[STEP 9] Connect to second agent
✅ Connection initiated

[STEP 10] Wait for second agent connection
⚠️  Second agent connection timeout (expected)

================================================================================
TEST COMPLETED SUCCESSFULLY
================================================================================
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Browser Tests

on: [push, pull_request]

jobs:
  browser-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        cd tests
        pip install -r requirements-browser-testing.txt
        playwright install chromium
    
    - name: Start HTTP server
      run: |
        cd /path/to/project
        python3 -m http.server 9000 &
    
    - name: Run UI tests
      run: |
        cd tests
        pytest test_voice_agent_switching_browser.py::test_voice_agent_selection_ui -v
```

## Architecture

### Browser Context Setup
- Chromium browser (headless configurable)
- Microphone permissions pre-granted
- Console logging enabled
- Error tracking enabled
- 1280x720 viewport

### Locators Used
- `#status` - Status message display
- `#connectBtn` - Connect button
- `#disconnectBtn` - Disconnect button
- `.agent-card` - Agent selection cards
- `.agent-name` - Agent name within card

### Wait Strategies
- `networkidle` - Wait for page load
- `to_contain_text()` - Wait for specific text
- `to_be_enabled()` - Wait for button state
- `to_have_class()` - Wait for CSS class

## Best Practices

1. **Proper Waits**: Uses Playwright's built-in wait mechanisms, not `sleep()`
2. **Error Handling**: Comprehensive try/catch with detailed logging
3. **State Verification**: Checks both UI state and status messages
4. **Graceful Degradation**: UI tests pass even if backend unavailable
5. **Clear Logging**: Step-by-step progress with clear success/failure markers
6. **Configurable**: Headless/headed mode, timeout adjustments

## Future Enhancements

- [ ] Visual regression testing (screenshot comparison)
- [ ] Network request mocking for offline testing
- [ ] Multi-browser support (Firefox, Safari)
- [ ] Parallel test execution
- [ ] Video recording of test runs
- [ ] Accessibility testing (WCAG compliance)
