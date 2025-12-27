# Interactive Voice Test - Quick Start

## TL;DR

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/tests

# Test with fake audio (recommended, default)
./run_interactive_voice_test.sh

# Test with real microphone (requires physical mic)
./run_interactive_voice_test.sh --real-device
```

## What It Does

1. Opens browser to voice agent selector
2. Connects to agent
3. Prompts you to press Enter to start talking
4. You press Enter (mic activates or fake audio starts)
5. You speak (or wait for fake audio)
6. Prompts you to press Enter to stop talking
7. Analyzes ALL logs
8. Shows detailed diagnosis of any issues

## Expected Output

### Successful Test
```
[1] MICROPHONE STATUS: ✅
[2] LIVEKIT CONNECTION: ✅
[3] WEBSOCKET CONNECTIONS: ✅
[4] PARTICIPANT EVENTS: ✅ (agent joined)
[5] AUDIO TRACKS: ✅
[9] DIAGNOSIS: ✅ No issues!
```

### Test with Issues
```
[1] MICROPHONE STATUS: ❌
[9] DIAGNOSIS: ❌ Microphone not enabled
[10] RECOMMENDATIONS:
    - Check microphone permissions
    - Verify device is connected
```

## Files Generated

- `voice_test_logs_YYYYMMDD_HHMMSS.json` - Complete log file
- Terminal output with analysis and recommendations

## Common Issues

### "Microphone device not found"
**Solution**: Use fake device mode (default)
```bash
./run_interactive_voice_test.sh
# or
python3 test_interactive_voice_manual.py --fake-device
```

### "Agent didn't join room"
**Check**:
```bash
# Is voice agent running?
ps aux | grep letta_voice_agent

# Check logs
tail -f /tmp/letta_voice_agent.log
```

## Help

Full documentation: `INTERACTIVE_VOICE_TEST_README.md`
Root cause analysis: `VOICE_ISSUE_ROOT_CAUSE_ANALYSIS.md`
Implementation details: `IMPLEMENTATION_SUMMARY.md`
