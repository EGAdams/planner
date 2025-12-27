# Interactive Voice Test - Manual Control

Comprehensive interactive testing tool for debugging voice processing issues with manual microphone control.

## Overview

This test provides a **manual, interactive environment** for debugging voice agent issues. Unlike automated tests, this allows you to:

- **Manually control** when microphone starts/stops
- **Speak into real microphone** (not fake device)
- **Watch browser status** in real-time
- **Collect comprehensive logs** for analysis
- **Get detailed diagnosis** of voice processing failures

## Quick Start

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/tests

# Run the interactive test
./run_interactive_voice_test.sh
```

## Test Flow

```
1. Browser opens voice-agent-selector.html
2. Test selects first agent and clicks Connect
3. Terminal prompts: "Press Enter to START TALKING..."
4. → User presses Enter
5. → User speaks into microphone
6. Terminal prompts: "Press Enter to STOP TALKING..."
7. → User presses Enter
8. Terminal prompts: "Press Enter to close browser and analyze logs..."
9. → Comprehensive log analysis displayed
10. → Diagnosis of voice processing issues provided
```

## Prerequisites

### Required Services

1. **Letta Server** (port 8283)
   ```bash
   # Check if running
   curl http://localhost:8283/api/v1/agents/
   ```

2. **HTTP Server** (port 9000)
   ```bash
   # Auto-started by test script, or run manually:
   cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
   python3 -m http.server 9000
   ```

3. **LiveKit Server** (port 7880)
   ```bash
   # Check if running
   curl http://localhost:7880
   ```

4. **Voice Agent Backend** (optional - for full e2e test)
   ```bash
   # Check if running
   ps aux | grep letta_voice_agent

   # Start if needed
   ./start_voice_system.sh
   ```

### Python Dependencies

```bash
# Install if not already installed
pip install playwright asyncio

# Install Playwright browsers
playwright install chromium
```

## Features

### 1. Manual Microphone Control

- **Press Enter to START** - Microphone activates, speak now
- **Press Enter to STOP** - Microphone deactivates
- Uses **REAL microphone** (not fake device)
- Auto-grants microphone permissions (no browser prompt)

### 2. Comprehensive Log Collection

Collects logs from:
- ✅ Browser console logs
- ✅ Browser errors
- ✅ Network requests (HTTP/WebSocket)
- ✅ Microphone events
- ✅ Connection events
- ✅ Voice processing events

### 3. Detailed Log Analysis

Analyzes:
1. **Microphone Status** - Was microphone activated?
2. **LiveKit Connection** - Did browser connect to LiveKit?
3. **WebSocket Connections** - Are WebSockets established?
4. **Participant Events** - Did voice agent join the room?
5. **Audio Tracks** - Are audio tracks being sent/received?
6. **Data Channel Messages** - Is agent selection being sent?
7. **Error Analysis** - Any browser or console errors?
8. **Connection Issues** - Any timeouts or failures?

### 4. Root Cause Diagnosis

Provides specific diagnosis:
- ❌ Microphone not enabled → Check permissions
- ❌ No LiveKit connection → Check LiveKit server
- ❌ No WebSocket connections → Check network/firewall
- ❌ Agent didn't join room → Check voice agent backend
- ✅ No issues detected → Voice processing working!

### 5. Actionable Recommendations

Provides specific troubleshooting steps based on issues found:
- Commands to check service status
- Log file locations
- Restart instructions

## Usage

### Basic Test Run

```bash
cd tests
./run_interactive_voice_test.sh
```

### Direct Python Execution

```bash
cd tests
python3 test_interactive_voice_manual.py
```

### What to Watch

While test is running:

1. **Terminal Output**
   - Follow the prompts
   - Watch for status updates
   - Press Enter at each prompt

2. **Browser Window**
   - Watch status message changes
   - Open DevTools (F12) for real-time logs
   - Check Network tab for WebSocket connections

3. **Browser Console (F12)**
   - Look for "Connected" messages
   - Watch for participant events
   - Check for error messages

## Example Output

### Successful Test

```
[1] MICROPHONE STATUS:
    ✅ Microphone activation detected

[2] LIVEKIT CONNECTION:
    ✅ LiveKit connection established:
       - ✅ Room connected successfully
       - ✅ Signal connection established

[3] WEBSOCKET CONNECTIONS:
    ✅ Found 1 WebSocket connection(s):
       - ws://localhost:7880

[4] PARTICIPANT EVENTS:
    ✅ Found 1 participant event(s):
       - 👤 Participant connected: voice-agent

[5] AUDIO TRACKS:
    ✅ Found 2 track event(s):
       - 🎵 Track subscribed: audio from voice-agent
       - Track published: audio

[6] DATA CHANNEL MESSAGES:
    ✅ Found 1 data channel message(s):
       - 📤 Sent agent selection: agent-abc123

[7] ERROR ANALYSIS:
    ✅ No browser errors detected

[8] CONNECTION ISSUES:
    ✅ No timeout or connection failures detected

[9] DIAGNOSIS:
    ✅ No critical issues detected!
    💡 Voice processing appears to be working correctly.
```

### Test with Issues

```
[1] MICROPHONE STATUS:
    ✅ Microphone activation detected

[2] LIVEKIT CONNECTION:
    ✅ LiveKit connection established

[3] WEBSOCKET CONNECTIONS:
    ✅ Found 1 WebSocket connection(s)

[4] PARTICIPANT EVENTS:
    ⚠️  No participant events detected

[7] ERROR ANALYSIS:
    ✅ No browser errors detected

[8] CONNECTION ISSUES:
    ⚠️  Found 1 timeout/failure(s):
       - ⏱️ Agent join timeout! No agent joined the room.

[9] DIAGNOSIS:
    ❌ Found 1 issue(s):
       1. Voice agent did not join the room

[10] RECOMMENDATIONS:
    - Verify voice agent backend is running: ps aux | grep letta_voice_agent
    - Check voice agent logs: tail -f /tmp/letta_voice_agent.log
    - Restart voice system: ./restart_voice_system.sh
```

## Log Files

Logs are saved to:
```
tests/voice_test_logs_YYYYMMDD_HHMMSS.json
```

Example: `voice_test_logs_20251226_143022.json`

### Log File Structure

```json
{
  "test_timestamp": "2025-12-26T14:30:22.123456",
  "browser_console_logs": [
    {
      "timestamp": "2025-12-26T14:30:25.123",
      "type": "log",
      "text": "✅ Room connected successfully"
    }
  ],
  "browser_errors": [],
  "network_requests": [
    {
      "timestamp": "2025-12-26T14:30:24.456",
      "url": "ws://localhost:7880",
      "method": "GET",
      "resource_type": "websocket"
    }
  ],
  "microphone_events": [
    {
      "timestamp": "2025-12-26T14:30:30.789",
      "event": "user_start_request",
      "details": {"message": "User requested to start talking"}
    }
  ],
  "connection_events": [],
  "voice_events": []
}
```

## Troubleshooting

### "No agents available"

**Problem**: Letta server has no agents

**Fix**:
```bash
# Check Letta server
curl http://localhost:8283/api/v1/agents/

# Create agents if needed via Letta CLI or API
```

### "Connection timeout"

**Problem**: LiveKit server not responding

**Fix**:
```bash
# Check LiveKit server
curl http://localhost:7880

# Check LiveKit logs
tail -f /tmp/livekit.log

# Restart LiveKit if needed
```

### "Agent didn't join room"

**Problem**: Voice agent backend not running or not connecting

**Fix**:
```bash
# Check if running
ps aux | grep letta_voice_agent

# Check logs
tail -f /tmp/letta_voice_agent.log

# Restart voice system
./restart_voice_system.sh
```

### Browser doesn't launch

**Problem**: Playwright not installed

**Fix**:
```bash
pip install playwright
playwright install chromium
```

### Microphone not working

**Problem**: Microphone permissions or device issue

**Fix**:
1. Check system microphone settings
2. Test microphone in other apps
3. Check browser console for permission errors
4. Try different microphone device

## Tips

1. **Open Browser DevTools (F12)** before pressing Enter
   - Watch Console tab for real-time logs
   - Watch Network tab for WebSocket connections
   - Watch Application > Storage for any data

2. **Speak clearly** when microphone is active
   - Normal speaking volume
   - Reduce background noise
   - Watch browser status for feedback

3. **Check all services** before running test
   - Letta server must be running
   - LiveKit server must be running
   - HTTP server (auto-started by script)
   - Voice agent backend (for full test)

4. **Review logs** after test completes
   - JSON log file has complete history
   - Terminal analysis shows key issues
   - Compare with working test logs

## Advanced Usage

### Run with specific agent

Modify `test_interactive_voice_manual.py`:

```python
async def select_specific_agent(self, agent_id):
    """Select agent by ID"""
    # Find agent card with matching ID
    agent_cards = self.page.locator(".agent-card")
    count = await agent_cards.count()

    for i in range(count):
        card = agent_cards.nth(i)
        id_elem = card.locator(".agent-id")
        card_id = await id_elem.text_content()

        if agent_id in card_id:
            await card.click()
            return
```

### Capture screenshots

Add to test:

```python
# Take screenshot at key points
await self.page.screenshot(path="test_screenshot_connected.png")
```

### Record video

Modify browser context:

```python
context = await browser.new_context(
    permissions=["microphone"],
    viewport={"width": 1280, "height": 720},
    record_video_dir="test_videos/"
)
```

## Architecture

### Components

1. **LogCollector** - Collects logs from all sources
2. **InteractiveVoiceTest** - Orchestrates test flow
3. **main()** - Sets up Playwright and runs test

### Log Collection Points

- `page.on("console")` → Browser console logs
- `page.on("pageerror")` → Browser errors
- `page.on("request")` → Network requests
- Manual events → Microphone/connection events

### Analysis Engine

- Parses collected logs
- Identifies patterns (connected, timeout, error)
- Correlates events across sources
- Generates diagnosis with root causes
- Provides actionable recommendations

## Comparison with Automated Test

| Feature | Automated Test | Interactive Test |
|---------|---------------|------------------|
| Microphone | Fake device | Real microphone |
| User Control | None | Full control |
| Timing | Fixed | User-paced |
| Log Analysis | Basic | Comprehensive |
| Diagnosis | None | Detailed |
| Use Case | CI/CD | Debugging |

## Next Steps

After running this test and getting diagnosis:

1. **If microphone issues** → Check system audio settings
2. **If connection issues** → Check LiveKit server and logs
3. **If agent join issues** → Check voice agent backend and logs
4. **If no issues found** → Voice processing is working!

Then test with automated test suite:
```bash
./run_browser_tests.sh
```

## Support

For issues or questions:
1. Check log file for detailed trace
2. Review browser console (F12) during test
3. Check service logs (LiveKit, voice agent, Letta)
4. Compare with example output above
