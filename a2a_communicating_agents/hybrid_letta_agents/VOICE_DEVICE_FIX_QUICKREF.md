# Voice Device Fix - Quick Reference Card

## The Problem
```
❌ Test PASSES but browser shows: "Error: Requested device not found"
❌ False-positive test result
❌ User experience broken despite passing tests
```

## The Root Cause
```
Browser has no audio input device (real or virtual)
→ LiveKit calls getUserMedia()
→ Fails: "Requested device not found"
→ Test passes anyway (broad exception handling)
```

## The Fix (Add 3 Lines of Code)

### File: `tests/test_voice_agent_switching_browser.py`

**Find line 213-216:**
```python
browser = await p.chromium.launch(
    headless=False,
    slow_mo=500
)
```

**Change to:**
```python
browser = await p.chromium.launch(
    headless=False,
    slow_mo=500,
    args=[
        '--use-fake-ui-for-media-stream',
        '--use-fake-device-for-media-stream',
        '--allow-file-access-from-files',
    ]
)
```

## Verify the Fix

### Step 1: Run this command
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/tests
pytest test_voice_agent_switching_browser.py::test_audio_device_availability -v -s
```

### Step 2: You should see
```
✅ Found 1 audio input device(s)
   Device 1: Fake Audio Input (default)
✅ Created 1 audio track(s)
   Track 1: Fake Audio Input (enabled=True, state=live)
AUDIO DEVICE INFRASTRUCTURE TEST PASSED
```

### Step 3: Run full tests
```bash
./run_browser_tests.sh
```

### Step 4: Verify
- ✅ No "Error: Requested device not found" in browser
- ✅ Status shows "Connected! Waiting for agent..." or "Start Speaking..."

## What Those Args Do

| Arg | What It Does |
|-----|--------------|
| `--use-fake-ui-for-media-stream` | Auto-grants getUserMedia (no permission prompt) |
| `--use-fake-device-for-media-stream` | Creates virtual microphone + camera |
| `--allow-file-access-from-files` | Allows local files to access devices |

## Full Implementation

For complete code changes including:
- Infrastructure test function
- Microphone validation method
- Updated test workflow
- Documentation updates

See: `VOICE_DEVICE_FIX_IMPLEMENTATION.md`

## Documentation

- **Quick Ref** (this): `VOICE_DEVICE_FIX_QUICKREF.md`
- **Summary**: `VOICE_DEVICE_ISSUE_SUMMARY.md`
- **Root Cause**: `VOICE_INPUT_DEVICE_ISSUE_ANALYSIS.md`
- **Implementation**: `VOICE_DEVICE_FIX_IMPLEMENTATION.md`

---
**Time to Fix:** 5 minutes (just the args)  
**Full Implementation:** 30 minutes (with tests + docs)
