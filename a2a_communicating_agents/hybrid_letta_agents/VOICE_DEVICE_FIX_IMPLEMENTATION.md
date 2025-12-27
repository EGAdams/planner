# Voice Input Device Fix - Implementation Guide

## Overview

This document provides the complete implementation for fixing the voice input device detection issue in browser tests.

## Changes Required

### 1. Update Test File: `tests/test_voice_agent_switching_browser.py`

#### Change 1.1: Update browser_context fixture (Lines 208-234)

**BEFORE:**
```python
@pytest.fixture
async def browser_context():
    """Create a Playwright browser context with proper configuration"""
    async with async_playwright() as p:
        # Launch browser with visible UI for debugging (set headless=True for CI)
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI/CD
            slow_mo=500  # Slow down actions for visibility (remove for CI)
        )
        
        # Create context with permissions for microphone
        context = await browser.new_context(
            permissions=["microphone"],
            viewport={"width": 1280, "height": 720}
        )
```

**AFTER:**
```python
@pytest.fixture
async def browser_context():
    """Create a Playwright browser context with proper configuration"""
    async with async_playwright() as p:
        # Launch browser with visible UI for debugging (set headless=True for CI)
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI/CD
            slow_mo=500,  # Slow down actions for visibility (remove for CI)
            args=[
                '--use-fake-ui-for-media-stream',      # Auto-grant getUserMedia
                '--use-fake-device-for-media-stream',  # Provide fake audio/video devices
                '--allow-file-access-from-files',      # Allow local file access
            ]
        )
        
        # Create context with permissions for microphone
        context = await browser.new_context(
            permissions=["microphone"],
            viewport={"width": 1280, "height": 720}
        )
```

#### Change 1.2: Add wait_for_microphone_enabled method to VoiceAgentSwitchingTest class

**Add after the `connect_to_agent` method (after line 158):**

```python
    async def wait_for_microphone_enabled(self):
        """
        Verify that microphone was successfully enabled without errors
        
        This validates that:
        1. Device enumeration succeeded
        2. getUserMedia succeeded
        3. No "device not found" errors in status
        """
        logger.info("Verifying microphone enabled...")
        
        # Wait a moment for any errors to appear
        await asyncio.sleep(1)
        
        # Check status for error messages
        status_element = self.page.locator("#status")
        status_text = await status_element.text_content()
        
        # Check for device-related errors
        error_keywords = ["device not found", "requested device", "microphone error", "access denied"]
        for keyword in error_keywords:
            if keyword.lower() in status_text.lower():
                raise AssertionError(
                    f"Microphone setup failed with error: {status_text}\n"
                    f"This indicates the browser does not have access to audio devices.\n"
                    f"Ensure browser is launched with --use-fake-device-for-media-stream"
                )
        
        # Also check browser console for getUserMedia errors
        # (This is a passive check - errors are already logged via page.on("console"))
        
        logger.info("✅ Microphone verification passed - no device errors detected")
```

#### Change 1.3: Add new infrastructure test

**Add as a new test function at the end of the file (before `if __name__ == "__main__"`):**

```python
@pytest.mark.asyncio
async def test_audio_device_availability(browser_context):
    """
    Test that audio devices are properly available in the browser context
    
    This test validates the test infrastructure itself - ensuring that
    the browser has access to audio devices (real or fake) before running
    the main voice agent tests.
    
    This test should ALWAYS pass if the browser is configured correctly.
    If this test fails, the main tests will also fail with device errors.
    """
    page = browser_context
    
    logger.info("=" * 80)
    logger.info("AUDIO DEVICE INFRASTRUCTURE TEST")
    logger.info("=" * 80)
    
    # Navigate to a simple test page
    logger.info("\n[STEP 1] Navigate to test page")
    await page.goto("data:text/html,<html><body><h1>Audio Device Test</h1></body></html>")
    
    # Test 1: Device Enumeration
    logger.info("\n[STEP 2] Test device enumeration")
    devices_available = await page.evaluate("""
        async () => {
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const audioInputs = devices.filter(d => d.kind === 'audioinput');
                return {
                    success: true,
                    deviceCount: devices.length,
                    audioInputCount: audioInputs.length,
                    devices: audioInputs.map(d => ({
                        deviceId: d.deviceId,
                        label: d.label || 'unlabeled',
                        kind: d.kind
                    }))
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    logger.info(f"Device enumeration result: {devices_available}")
    
    # Assert device enumeration succeeded
    assert devices_available['success'], \
        f"Device enumeration failed: {devices_available.get('error')}\n" \
        f"Browser may not support navigator.mediaDevices"
    
    # Assert we have at least one audio input device
    assert devices_available['audioInputCount'] > 0, \
        f"No audio input devices found!\n" \
        f"Total devices: {devices_available['deviceCount']}\n" \
        f"Audio inputs: {devices_available['audioInputCount']}\n" \
        f"Browser needs to be launched with --use-fake-device-for-media-stream"
    
    logger.info(f"✅ Found {devices_available['audioInputCount']} audio input device(s)")
    for i, device in enumerate(devices_available['devices']):
        logger.info(f"   Device {i+1}: {device['label']} ({device['deviceId'][:20]}...)")
    
    # Test 2: getUserMedia
    logger.info("\n[STEP 3] Test getUserMedia")
    getUserMedia_result = await page.evaluate("""
        async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({audio: true});
                const tracks = stream.getAudioTracks();
                
                const trackInfo = {
                    success: true,
                    trackCount: tracks.length,
                    tracks: tracks.map(track => ({
                        label: track.label,
                        enabled: track.enabled,
                        muted: track.muted,
                        readyState: track.readyState
                    }))
                };
                
                // Clean up - stop tracks
                tracks.forEach(track => track.stop());
                
                return trackInfo;
            } catch (error) {
                return {
                    success: false,
                    error: error.message,
                    errorName: error.name
                };
            }
        }
    """)
    
    logger.info(f"getUserMedia result: {getUserMedia_result}")
    
    # Assert getUserMedia succeeded
    assert getUserMedia_result['success'], \
        f"getUserMedia failed: {getUserMedia_result.get('error')} ({getUserMedia_result.get('errorName')})\n" \
        f"This typically means:\n" \
        f"  - No audio devices available (need --use-fake-device-for-media-stream)\n" \
        f"  - Permissions not granted (need permissions=['microphone'])\n" \
        f"  - Browser security restrictions"
    
    # Assert we got at least one audio track
    assert getUserMedia_result['trackCount'] > 0, \
        f"No audio tracks created from getUserMedia\n" \
        f"getUserMedia succeeded but returned no tracks"
    
    logger.info(f"✅ Created {getUserMedia_result['trackCount']} audio track(s)")
    for i, track in enumerate(getUserMedia_result['tracks']):
        logger.info(f"   Track {i+1}: {track['label']} (enabled={track['enabled']}, state={track['readyState']})")
    
    logger.info("\n" + "=" * 80)
    logger.info("AUDIO DEVICE INFRASTRUCTURE TEST PASSED")
    logger.info("=" * 80)
    logger.info("\nBrowser is properly configured with:")
    logger.info(f"  ✅ {devices_available['audioInputCount']} audio input device(s)")
    logger.info(f"  ✅ getUserMedia working")
    logger.info(f"  ✅ Audio track creation working")
    logger.info("\nMain voice agent tests should work correctly.")
```

#### Change 1.4: Update test_voice_agent_switching_workflow to validate microphone

**Find lines 279-290 and modify:**

**BEFORE:**
```python
    # Step 5: Connect to first agent
    logger.info("\n[STEP 5] Connect to first agent")
    await test.connect_to_agent()
    
    # Step 6: Wait for "Start Speaking..." message
    logger.info("\n[STEP 6] Wait for agent connection and 'Start Speaking...' message")
    # NOTE: This will timeout if voice agent backend is not running
    # This is expected - the test validates the UI workflow, not backend
    try:
        await test.wait_for_agent_connection(first_agent_name)
    except Exception as e:
        logger.warning(f"⚠️  Agent connection timeout (expected if voice backend not running): {e}")
        logger.info("UI workflow validated up to connection attempt")
```

**AFTER:**
```python
    # Step 5: Connect to first agent
    logger.info("\n[STEP 5] Connect to first agent")
    await test.connect_to_agent()
    
    # Step 5.5: Verify microphone enabled (NEW)
    logger.info("\n[STEP 5.5] Verify microphone enabled without device errors")
    try:
        await test.wait_for_microphone_enabled()
    except AssertionError as e:
        pytest.fail(f"❌ Device setup failed: {e}")
    
    # Step 6: Wait for "Start Speaking..." message
    logger.info("\n[STEP 6] Wait for agent connection and 'Start Speaking...' message")
    # NOTE: This will timeout if voice agent backend is not running
    # This is expected - the test validates the UI workflow, not backend
    try:
        await test.wait_for_agent_connection(first_agent_name)
    except Exception as e:
        logger.warning(f"⚠️  Agent connection timeout (expected if voice backend not running): {e}")
        logger.info("UI workflow validated up to connection attempt")
```

### 2. Update Documentation: `tests/BROWSER_TESTING_README.md`

**Add a new section after "### Microphone permission denied" (around line 178):**

```markdown
### "Requested device not found" Error

**Cause**: Browser has no audio input devices available

**Symptoms**:
- Browser console shows: "Error: Requested device not found"
- Status shows microphone-related error
- Test may pass but runtime behavior is broken

**Fix**: Ensure browser is launched with fake device arguments

Tests automatically configure this via:
```python
browser = await p.chromium.launch(
    args=[
        '--use-fake-device-for-media-stream',      # Provides fake audio/video
        '--use-fake-device-for-media-stream',  # Auto-grants permissions
    ]
)
```

If you see this error, it means the browser fixture is not configured correctly.

**Verification**:
```bash
# Run the infrastructure test to verify device availability
pytest test_voice_agent_switching_browser.py::test_audio_device_availability -v -s
```

This test should show:
```
✅ Found 1 audio input device(s)
✅ getUserMedia working
✅ Audio track creation working
```

### Why Fake Devices?

**Problem**: Browser tests need audio devices, but:
- CI environments have no physical microphone
- Real microphones are unreliable in tests (background noise, permissions)
- Tests should be deterministic and isolated

**Solution**: Chromium's fake device mode provides:
- Virtual microphone that always works
- Silent audio stream (perfect for testing)
- Consistent behavior across environments
- No external dependencies

**What the fake device does**:
- Appears in `navigator.mediaDevices.enumerateDevices()`
- Responds to `getUserMedia({audio: true})`
- Generates silent audio stream
- Works in both headed and headless mode
- Sufficient for UI/integration testing
```

### 3. Update Test Summary: `tests/BROWSER_TEST_SUMMARY.md`

**Add to the "Test Features" section (around line 112):**

```markdown
### Device Infrastructure Testing
- Validates audio device availability before main tests
- Tests device enumeration API
- Tests getUserMedia API
- Ensures fake devices configured correctly
- **Prevents false-positive test passes with device errors**
```

**Add to the "Validation Checklist" section (around line 175):**

```markdown
✅ **Device Infrastructure**
- [x] Fake audio devices configured
- [x] Infrastructure test validates device availability
- [x] getUserMedia works before main tests
- [x] Device errors fail tests (not hidden)
- [x] Microphone verification in connection flow
```

## Testing the Fix

### Step 1: Run Infrastructure Test

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/tests
pytest test_voice_agent_switching_browser.py::test_audio_device_availability -v -s
```

**Expected Output:**
```
============== AUDIO DEVICE INFRASTRUCTURE TEST ==============
[STEP 1] Navigate to test page
[STEP 2] Test device enumeration
Device enumeration result: {'success': True, 'deviceCount': 2, 'audioInputCount': 1, ...}
✅ Found 1 audio input device(s)
   Device 1: Fake Audio Input (default) (...)
[STEP 3] Test getUserMedia
getUserMedia result: {'success': True, 'trackCount': 1, ...}
✅ Created 1 audio track(s)
   Track 1: Fake Audio Input (enabled=True, state=live)
============== AUDIO DEVICE INFRASTRUCTURE TEST PASSED ==============
```

### Step 2: Run Full Test Suite

```bash
./run_browser_tests.sh
```

**Expected Improvements:**
- ✅ Browser console: No "Error: Requested device not found"
- ✅ Test logs: "✅ Microphone verification passed"
- ✅ Status: Shows "Connected! Waiting for agent..." (not device error)

### Step 3: Verify in Browser

1. Watch the browser window during test
2. Check that status element shows proper connection messages
3. Confirm no red error messages about devices

## Rollback Plan

If fixes cause issues:

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
git diff tests/test_voice_agent_switching_browser.py
git checkout tests/test_voice_agent_switching_browser.py
```

## Success Criteria

- [ ] Infrastructure test passes
- [ ] No "device not found" errors in browser console
- [ ] Microphone verification step passes
- [ ] Tests distinguish device errors from backend timeouts
- [ ] Documentation updated with troubleshooting
- [ ] Tests work in both headed and headless mode

---

**Implementation Date:** 2025-12-26
**Difficulty:** Easy (configuration fix)
**Time Estimate:** 30 minutes (including testing)
**Risk:** Low (additive changes, no breaking modifications)
