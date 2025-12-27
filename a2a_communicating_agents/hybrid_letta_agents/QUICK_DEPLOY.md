# Quick Deploy - Hybrid Streaming Voice Agent

## TLDR
Reduce response time from 16s to 1.8s by using direct OpenAI streaming instead of Letta-buffered responses.

---

## 3-Step Deployment

### 1. Update Startup Script
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

# Edit start_voice_system.sh
# Change line 35:
LETTA_VOICE_AGENT_EXE="letta_voice_agent_hybrid.py"
```

### 2. Configure Environment
```bash
# Add to /home/adamsl/ottomator-agents/livekit-agent/.env
echo "USE_HYBRID_STREAMING=true" >> /home/adamsl/ottomator-agents/livekit-agent/.env
echo "VOICE_MODEL=gpt-4o-mini" >> /home/adamsl/ottomator-agents/livekit-agent/.env
```

### 3. Restart
```bash
./restart_voice_system.sh
```

---

## Validate

### Monitor Performance
```bash
tail -f /tmp/voice_agent.log | grep -E "⚡|Total llm_node"
```

Expected output:
```
⚡ Using hybrid mode - direct OpenAI streaming
⚡ TTFT: 1200ms
✅ Total llm_node latency: 1.35s
```

### Run Tests
```bash
source /home/adamsl/planner/.venv/bin/activate
python3 test_hybrid_performance.py
```

Expected result:
```
✅ HYBRID APPROACH VALIDATED
End-to-end: 1.80s < 3.0s
```

---

## Rollback

If issues occur:
```bash
# Disable hybrid mode
export USE_HYBRID_STREAMING=false
./restart_voice_system.sh
```

Or revert startup script:
```bash
LETTA_VOICE_AGENT_EXE="letta_voice_agent.py"  # Original
```

---

## How It Works

BEFORE:
```
Voice → STT → Letta (buffers 5s) → TTS → 16s total ❌
```

AFTER:
```
Voice → STT → OpenAI Direct (1s) → TTS → 1.8s total ✅
             └─> Letta memory (background, 5s, non-blocking)
```

---

## Tradeoffs

GAINED:
- 8.9x faster (16s → 1.8s)
- <3s response time
- True streaming

SACRIFICED:
- Voice doesn't use Letta orchestration
- Memory updates in background (5s lag)
- No real-time agent delegation

MITIGATION:
- Text chat uses full Letta
- Memory lag typically unnoticed
- Environment variable to switch modes

---

## Key Files

Implementation:
- letta_voice_agent_hybrid.py (new production file)
- letta_voice_agent.py (original, keep as backup)

Tests:
- test_hybrid_performance.py (validates <3s target)

Docs:
- HYBRID_OPTIMIZATION_COMPLETE.md (full details)
- PERFORMANCE_ANALYSIS.md (root cause analysis)

---

## Support

Issues? Check logs:
```bash
tail -f /tmp/voice_agent.log
tail -f /tmp/letta_server.log
```

Need full Letta features?
```bash
export USE_HYBRID_STREAMING=false
./restart_voice_system.sh
```

---

DEPLOYMENT TIME: 2 minutes
IMPROVEMENT: 8.9x faster
STATUS: Production ready ✅
