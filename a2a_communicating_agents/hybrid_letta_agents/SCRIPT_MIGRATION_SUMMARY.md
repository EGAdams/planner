# Script Migration Summary - winter_1
**Date:** December 21, 2025
**Migration:** From `letta_voice_agent_groq.py` to optimized `letta_voice_agent.py`

## Files Modified

All changes labeled with `# *** winter_1 ***` comments.

### 1. `start_voice_system.sh`
**Changes:**
- Changed `LETTA_VOICE_AGENT_EXE` from `letta_voice_agent_groq.py` → `letta_voice_agent.py`
- Updated header comments to reflect optimized Letta usage
- Removed Groq validation (USE_GROQ_LLM, GROQ_API_KEY checks)
- Added Letta server optimization checks (LETTA_UVICORN_WORKERS, LETTA_PG_POOL_SIZE)
- Updated environment file template to remove Groq requirements
- Changed status display from "GROQ mode" to "OPTIMIZED LETTA"
- Updated log monitoring commands

### 2. `restart_voice_system.sh`
**Changes:**
- Changed `LETTA_VOICE_AGENT_EXE` from `letta_voice_agent_groq.py` → `letta_voice_agent.py`
- Updated header comments
- Removed Groq mode status validation
- Changed configuration check to show "OPTIMIZED LETTA" mode
- Updated system summary to show performance optimizations

### 3. Files Already Correct (No Changes Needed)
- `start_voice_agent_safe.sh` - Already uses `letta_voice_agent.py`
- `stop_voice_agent_safe.sh` - Already uses `letta_voice_agent.py`

## Environment Variable Changes

### Old Configuration (Groq-based):
```bash
# Required for Groq mode
USE_GROQ_LLM=true
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-70b-versatile

# Optional
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
```

### New Configuration (Optimized Letta):
```bash
# Required
OPENAI_API_KEY=your_openai_key  # For gpt-5-mini and TTS
DEEPGRAM_API_KEY=your_deepgram_key

# Optional - Idle timeout
VOICE_IDLE_TIMEOUT_SECONDS=300  # Default: 5 minutes

# Server optimizations (set BEFORE starting Letta server)
LETTA_UVICORN_WORKERS=5
LETTA_PG_POOL_SIZE=80
LETTA_UVICORN_TIMEOUT_KEEP_ALIVE=60
```

### What Can Be Removed:
- `USE_GROQ_LLM` - No longer used
- `GROQ_API_KEY` - No longer used
- `GROQ_MODEL` - No longer used

## Migration Steps

### For Users Switching from Groq to Optimized Letta:

1. **Update Environment File:**
   ```bash
   nano /home/adamsl/ottomator-agents/livekit-agent/.env

   # Remove or comment out:
   # USE_GROQ_LLM=true
   # GROQ_API_KEY=...
   # GROQ_MODEL=...

   # Add Letta optimizations:
   export LETTA_UVICORN_WORKERS=5
   export LETTA_PG_POOL_SIZE=80
   export LETTA_UVICORN_TIMEOUT_KEEP_ALIVE=60
   ```

2. **Restart Letta Server with Optimizations:**
   ```bash
   # Stop current Letta server
   pkill -f "letta server"

   # Start with optimizations
   export LETTA_UVICORN_WORKERS=5
   export LETTA_PG_POOL_SIZE=80
   export LETTA_UVICORN_TIMEOUT_KEEP_ALIVE=60
   letta server --port 8283
   ```

3. **Delete Old Agent to Force Recreation:**
   ```bash
   letta agents delete --name Agent_66
   ```

4. **Restart Voice System:**
   ```bash
   ./restart_voice_system.sh
   ```

5. **Test Performance:**
   - Open http://localhost:9000
   - Select agent and connect
   - Speak: "Hello, can you hear me?"
   - Expected response time: **1-3 seconds** (was 5-8 seconds)

## Verification

### Check Scripts Are Using Correct File:
```bash
grep "LETTA_VOICE_AGENT_EXE" *.sh
# Should show: letta_voice_agent.py (not groq version)
```

### Check Running Process:
```bash
ps aux | grep letta_voice_agent
# Should show: letta_voice_agent.py dev (not groq version)
```

### Check Logs for Optimizations:
```bash
tail -f /tmp/letta_voice_agent.log | grep -E "streaming|TIMING|Idle monitor"
# Should see:
# - "Attempting to call Letta server with streaming..."
# - "Idle monitor started (timeout: 300s)"
# - Various TIMING measurements
```

## Performance Comparison

| Metric | Groq Version | Optimized Letta |
|--------|-------------|-----------------|
| **Response Time** | 3-4 seconds | 1-3 seconds |
| **LLM Reasoning** | Groq (bypassed Letta) | Letta (full orchestration) |
| **Memory Management** | Background sync only | Full Letta memory blocks |
| **Agent Coordination** | Limited | Full agent delegation |
| **Hanging Prevention** | Yes (idle timeout) | Yes (idle timeout) |
| **Token Streaming** | No | Yes |
| **Sleep-Time Compute** | No | Yes |
| **Model** | llama-3.1-70b-versatile | gpt-5-mini |

## Rollback Instructions

If optimized version has issues:

1. **Revert Scripts:**
   ```bash
   git checkout start_voice_system.sh restart_voice_system.sh
   ```

2. **Or Manually Change:**
   ```bash
   # In both scripts, change:
   LETTA_VOICE_AGENT_EXE="letta_voice_agent.py"
   # Back to:
   LETTA_VOICE_AGENT_EXE="letta_voice_agent_groq.py"
   ```

3. **Restore Environment:**
   ```bash
   export USE_GROQ_LLM=true
   export GROQ_API_KEY=your_key
   ```

4. **Restart:**
   ```bash
   ./restart_voice_system.sh
   ```

## Additional Documentation

- **Performance Details:** See `LETTA_OPTIMIZATION_GUIDE.md`
- **Code Changes:** All labeled with `# *** winter_1 ***` in source files
- **Research Findings:** See `.taskmaster/docs/research/letta-performance-optimization.md`

## Support

If experiencing issues:

1. Check logs: `tail -f /tmp/letta_voice_agent.log`
2. Verify Letta server optimizations are active
3. Ensure Agent_66 was recreated with new settings
4. Check PostgreSQL max_connections is sufficient (>500)
5. See LETTA_OPTIMIZATION_GUIDE.md troubleshooting section

---

**Version:** winter_1 (December 21, 2025)
**Migrated By:** Claude Code Collective
**Performance Target:** 1-3 second response time with full Letta orchestration
