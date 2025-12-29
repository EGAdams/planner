# Agent_66 Memory Loading Fix - REST API Solution

## Problem Summary

Agent_66 was not loading memory blocks correctly in the voice agent, causing the agent to respond without its persona and knowledge context.

### Root Cause

The AsyncLetta client's `.agents.retrieve()` method returns **empty memory blocks** (`[]`), while the REST API endpoint returns **full memory blocks** with workspace, persona, role, and other critical context.

**Evidence**:
- REST API: `GET /v1/agents/agent-4dfca708...` returns complete memory blocks with persona, role, workspace, etc.
- AsyncLetta Client: `await letta_client.agents.retrieve(agent_id)` returns `agent.memory.blocks = []` (empty)

### Impact

- Voice agent had NO access to Agent_66's persona and knowledge
- Responses were generic and lacked the agent's specialized context
- Hybrid mode fast path (OpenAI streaming) was working without agent memory

## Solution Implemented

### File Modified
`letta_voice_agent_optimized.py` - `_load_agent_memory()` method (lines 258-347)

### Technical Change

**BEFORE (Buggy AsyncLetta client)**:
```python
agent = await self.letta_client.agents.retrieve(agent_id=self.agent_id)
blocks = agent.memory.blocks  # Returns [] (empty)
```

**AFTER (Working REST API)**:
```python
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(
        f"{LETTA_BASE_URL}/v1/agents/{self.agent_id}",
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    agent_data = response.json()

memory_blocks = agent_data.get('memory', {}).get('blocks', [])
```

### Key Improvements

1. **Direct REST API Call**: Bypasses buggy AsyncLetta client entirely
2. **Complete Memory Access**: Now loads ALL memory blocks (persona, role, workspace, etc.)
3. **Enhanced Logging**: Detailed logging of memory block labels and sizes
4. **Robust Error Handling**: Graceful fallback with full traceback on errors
5. **Multiple Persona Sources**: Checks for persona in "persona", "human", OR "role" blocks

## Verification Steps

### 1. Check Environment Configuration
```bash
# Confirm Agent_66 ID is configured
grep "VOICE_PRIMARY_AGENT_ID" .env
# Should show: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
```

### 2. Test REST API Directly (When Letta is Running)
```bash
curl http://localhost:8283/v1/agents/agent-4dfca708-49a8-4982-8e36-0f1146f9a66e | python3 -m json.tool
# Should return agent data with memory.blocks populated
```

### 3. Check Voice Agent Logs
After restarting the voice system, look for:
```
🧠 LOADING MEMORY - Agent ID: agent-4dfca708...
🧠 Fetching agent details via REST API (bypassing AsyncLetta client bug)
🧠 Retrieved agent data from REST API: Agent_66
🧠 Found N memory blocks in REST API response
✅ Loaded block 'persona': XXX chars
✅ Loaded block 'role': XXX chars
✅ Loaded block 'workspace': XXX chars
✅ Memory loaded successfully via REST API in X.XXs
   - Persona: XXX chars
   - Memory blocks: N
   - Block labels: ['persona', 'role', 'workspace', ...]
```

### 4. Test Voice Interaction
1. Start voice session
2. Agent should respond with Agent_66's persona and context
3. Check logs confirm memory blocks loaded
4. Responses should reflect Agent_66's specialized knowledge

## Expected Behavior

### Startup Sequence
1. Voice agent initializes
2. Fetches Agent_66 details via REST API
3. Loads all memory blocks (persona, role, workspace, etc.)
4. Builds enhanced system instructions with agent context
5. Ready to respond with Agent_66's knowledge

### During Conversation
1. User asks question
2. Hybrid mode uses OpenAI streaming with Agent_66's persona
3. Background Letta sync updates memory
4. Every 5 messages, memory is reloaded to pick up changes

## Testing Commands

### Restart Voice System
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./restart_voice_system.sh
```

### Monitor Logs
```bash
# Watch voice agent logs
tail -f logs/voice_agent_*.log

# Check for memory loading success
grep "Memory loaded successfully" logs/voice_agent_*.log

# Check for memory block details
grep "Block labels" logs/voice_agent_*.log
```

### Test Agent Selection
```javascript
// In browser console (voice-agent-selector.html)
// Should show Agent_66 with full memory context
const agentId = "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e";
// Test voice interaction and verify agent uses correct persona
```

## Success Criteria

- [ ] Voice agent starts without errors
- [ ] Logs show "Memory loaded successfully via REST API"
- [ ] Logs show multiple memory blocks loaded (persona, role, workspace, etc.)
- [ ] Voice responses reflect Agent_66's persona and knowledge
- [ ] No "empty memory blocks" warnings in logs
- [ ] Agent maintains context across conversation

## Rollback Plan

If the fix causes issues, revert to AsyncLetta client:
```bash
git diff letta_voice_agent_optimized.py
git checkout letta_voice_agent_optimized.py  # Revert changes
```

## Related Files

- `letta_voice_agent_optimized.py` - Main voice agent (MODIFIED)
- `.env` - Agent_66 configuration (VOICE_PRIMARY_AGENT_ID)
- `restart_voice_system.sh` - System restart script
- `voice-agent-selector.html` - Agent selection UI

## Technical Notes

### Why REST API Works But AsyncLetta Doesn't

The AsyncLetta client appears to have a bug in the `.agents.retrieve()` method where it either:
1. Doesn't properly deserialize the memory blocks from the API response
2. Returns a proxy/lazy object that doesn't populate blocks correctly
3. Has a version mismatch with the Letta server API

The REST API endpoint `/v1/agents/{agent_id}` works correctly and returns the full agent data structure with populated memory blocks.

### Performance Impact

- REST API call adds ~50-200ms to startup (one-time cost)
- No impact on response latency (memory loaded once at startup)
- Periodic reloads every 5 messages add minimal overhead (background)

### Future Improvements

1. File bug report with AsyncLetta maintainers
2. Consider caching memory blocks in Redis for multi-agent deployments
3. Add memory block versioning to detect changes without full reload
4. Implement intelligent memory refresh based on conversation topics

## Author

Fix implemented on: 2025-12-28
Issue: Agent_66 memory loading via AsyncLetta client returns empty blocks
Solution: Direct REST API call bypasses client bug and loads full memory

---

**STATUS: READY FOR TESTING**

Please restart the voice system and verify memory blocks load correctly in the logs.
