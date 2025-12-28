# Microphone Testing Updates

## Summary of Changes

Updated the microphone detection system to work properly in WSL2 and headless environments by using Chromium's fake media device support.

## Changes Made

### 1. Shell Script: `test_microphone.sh`

**Created**: New standalone shell script for microphone testing

**Key Features**:
- Uses virtual environment at `/home/adamsl/planner/.venv`
- Launches local HTTP server on port 18765 for secure context
- Configures Chromium with fake media device flags
- Provides detailed device enumeration and debug information
- Returns proper exit codes (0 = success, 1 = failure)

**Usage**:
```bash
./test_microphone.sh
```

### 2. Test File: `tests/test_voice_agent_switching_browser.py`

**Modified**: Browser fixture configuration (lines 311-317)

**Changes**:
```python
browser = await p.chromium.launch(
    headless=False,
    slow_mo=500,
    args=[
        '--use-fake-device-for-media-stream',  # NEW
        '--use-fake-ui-for-media-stream',      # NEW
    ])
```

**Modified**: `check_microphone_available()` method (lines 88-180)

**Improvements**:
- Enhanced JavaScript evaluation to return detailed device information
- Added debug information (API availability, secure context, protocol)
- Improved logging with device enumeration
- Better error handling and diagnostic messages
- Detects and warns about secure context issues

### 3. Test File: `tests/test_microphone_detection.py`

**Created**: Standalone test to verify microphone detection

**Features**:
- Self-contained test with embedded HTTP server
- Uses same detection logic as main test file
- Provides detailed test output
- Can be run independently of other tests

**Usage**:
```bash
source /home/adamsl/planner/.venv/bin/activate
python3 tests/test_microphone_detection.py
```

## Technical Details

### Why Fake Devices?

In WSL2 and headless environments, real hardware access to microphones is limited or unavailable. Chromium's fake device flags simulate media devices for testing:

- `--use-fake-device-for-media-stream`: Creates fake audio/video devices
- `--use-fake-ui-for-media-stream`: Bypasses permission prompts

### Fake Devices Created

When using these flags, Chromium creates:
- **3 Audio Input Devices**:
  - Fake Default Audio Input
  - Fake Audio Input 1
  - Fake Audio Input 2
- **3 Audio Output Devices**
- **1 Video Input Device**

### Secure Context Requirement

The MediaDevices API (used for `enumerateDevices()` and `getUserMedia()`) requires a **secure context**:
- HTTPS connections
- localhost (HTTP allowed)
- data: URLs are NOT secure contexts

## Test Results

All three implementations successfully detect fake microphone devices:

```
✅ MediaDevices API Available: True
✅ Is Secure Context: True
✅ Audio Input Devices: 3
✅ Total Devices: 7
```

## Troubleshooting

### No Microphone Found

If microphone detection fails:

1. **Check Secure Context**: Ensure using HTTPS or localhost
2. **Check Browser Flags**: Verify fake device flags are set
3. **Check Permissions**: Ensure 'microphone' permission granted
4. **Check Debug Info**: Review debug output for API availability

### Common Issues

| Issue | Solution |
|-------|----------|
| `MediaDevices API not available` | Not using secure context (localhost/HTTPS) |
| `isSecureContext: False` | Using data: URL or non-HTTPS connection |
| No fake devices | Missing browser launch flags |
| Permission denied | Missing microphone permission in context |

## Next Steps

The test suite can now:
1. ✅ Detect microphone availability in WSL2/headless mode
2. ✅ Run browser tests without real hardware
3. ✅ Validate LiveKit voice agent integration
4. ✅ Test agent switching with simulated audio devices

## Files Modified

1. ✅ `test_microphone.sh` - Shell script for quick testing
2. ✅ `tests/test_voice_agent_switching_browser.py` - Main test suite updates
3. ✅ `tests/test_microphone_detection.py` - Standalone verification test
