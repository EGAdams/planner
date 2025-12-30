# Voice Agent Selection Analysis - Key Findings

## Executive Summary

After analyzing the complete voice agent system, I've identified **7 critical points** where agent selection occurs and **7 potential failure points** that could cause the system to connect to the wrong Letta agent.

## Critical Discovery: TWO Agent Selection Mechanisms

The system uses **TWO DIFFERENT** mechanisms to determine which agent to use:

### 1. Initial Agent Selection (Server-Side)
**Location**: `letta_voice_agent_optimized.py`, `get_or_create_orchestrator()` (line 1027-1123)

```python
PRIMARY_AGENT_NAME = os.getenv("VOICE_PRIMARY_AGENT_NAME", "Agent_66")
PRIMARY_AGENT_ID = os.getenv("VOICE_PRIMARY_AGENT_ID")  # Optional override

# Priority 1: Use specific agent ID if configured
if PRIMARY_AGENT_ID:
    agent = await letta_client.agents.retrieve(agent_id=PRIMARY_AGENT_ID)
    return PRIMARY_AGENT_ID

# Priority 2: Search by agent name
for agent in agents:
    if agent.name == PRIMARY_AGENT_NAME:
        return agent.id
```

**This selection happens BEFORE the browser even connects!**

### 2. Agent Selection Message (Client-Side)
**Location**: `voice-agent-selector-debug.html`, RoomEvent.Connected handler (lines 554-571)

```javascript
const data = {
    type: "agent_selection",
    agent_id: selectedAgent.id,
    agent_name: selectedAgent.name
};
room.localParticipant.publishData(data, { reliable: true });
```

**This message is sent AFTER connection, but may be ignored or rejected!**

## The Problem: Timing and Precedence

```
Timeline:
1. User clicks "Connect"                          → t=0ms
2. LiveKit room connection established            → t=100ms
3. Browser sends agent_selection message          → t=150ms
4. Browser requests agent dispatch                → t=200ms
5. LiveKit dispatches job to worker               → t=300ms
6. Voice agent process starts                     → t=500ms
7. get_or_create_orchestrator() runs              → t=600ms  ⚠️ AGENT SELECTED HERE
8. Agent joins room                               → t=1000ms
9. agent_selection message finally received       → t=1200ms
10. switch_agent() called                         → t=1300ms ⚠️ TOO LATE if already wrong agent
```

**The agent is selected at t=600ms based on environment variables, but the browser's selection message doesn't arrive until t=1200ms!**

## 7 Potential Failure Points

### Failure Point 1: Environment Variable Misconfiguration ⚠️ HIGHEST RISK
**Impact**: Wrong agent selected from the start

```bash
# If these are wrong or missing:
VOICE_PRIMARY_AGENT_NAME=Agent_66     # Wrong name → wrong agent
VOICE_PRIMARY_AGENT_ID=<uuid>         # Wrong ID → wrong agent
```

**Symptoms**:
- Log shows: `"AGENT INITIALIZED - Agent Name: SomeOtherAgent"`
- Response includes wrong agent ID in debug prefix

**Fix**:
```bash
# Verify environment variables are set correctly
echo $VOICE_PRIMARY_AGENT_NAME
echo $VOICE_PRIMARY_AGENT_ID

# Check which agent was actually selected
grep "AGENT INITIALIZED" voice_agent.log
```

### Failure Point 2: Multiple Agents with Same Name
**Impact**: get_or_create_orchestrator() returns first match, which may not be the intended agent

```python
for agent in agents:
    if agent.name == PRIMARY_AGENT_NAME:  # Returns FIRST match only!
        return agent.id
```

**Symptoms**:
- Multiple agents named "Agent_66" in Letta
- Wrong Agent_66 instance selected

**Fix**:
- Use `VOICE_PRIMARY_AGENT_ID` to specify exact agent UUID
- Ensure only one agent with name "Agent_66" exists

### Failure Point 3: Agent Selection Message Ignored
**Impact**: Browser's agent choice never applied

**Root Causes**:
1. Message sent before agent process is ready
2. Message arrives but agent lock rejects it
3. Message parsing fails

**Symptoms**:
- Log shows: `"AGENT SELECTION MESSAGE RECEIVED"` but no switch happens
- Log shows: `"REJECTED - Agent switch to ... enforcing Agent_66"`

**Fix**:
- Ensure browser waits for participantConnected event before sending selection
- Check that selectedAgent.name matches PRIMARY_AGENT_NAME

### Failure Point 4: Duplicate Agent Instances
**Impact**: Multiple instances of same agent process different requests

```python
# Prevention mechanism (lines 96-99)
_ACTIVE_AGENT_INSTANCES = {}  # Track active instances
_AGENT_INSTANCE_LOCK = asyncio.Lock()

# But if lock fails or race condition occurs:
async with _AGENT_INSTANCE_LOCK:
    if agent_id in _ACTIVE_AGENT_INSTANCES:
        # Reuse existing instance
    else:
        # Create new instance ⚠️ If two threads race here
```

**Symptoms**:
- Warning: `"Agent xxx already has active instance!"`
- Different responses from same agent queries
- Memory state inconsistencies

**Fix**:
- Voice agent should handle reconnects properly
- Check for existing instances before creating new ones

### Failure Point 5: Room Assignment Conflict
**Impact**: Multiple agents in same room, audio duplication

```python
# Prevention mechanism (lines 1404-1473)
_ROOM_TO_AGENT = {}  # Track which agent assigned to which room

async with _ROOM_ASSIGNMENT_LOCK:
    if room_name in _ROOM_TO_AGENT:
        # REJECT duplicate job request
        await job_request.reject()
```

**Symptoms**:
- Error: `"🚨 MULTI-AGENT CONFLICT DETECTED!"`
- Error: `"🚨 AGENT CONFLICT DETECTED! Already assigned to: ..."`
- Duplicate audio responses
- Message routing errors

**Fix**:
- Room manager cleans stale agents before new connection
- Job request handler rejects duplicate requests

### Failure Point 6: Memory Loading from Wrong Agent
**Impact**: Agent uses wrong persona and memory blocks

```python
async def _load_agent_memory(self) -> bool:
    # Uses self.agent_id to fetch memory
    response = await client.get(
        f"{LETTA_BASE_URL}/v1/agents/{self.agent_id}",  # ⚠️ Wrong agent_id → wrong memory
    )
```

**Symptoms**:
- Log shows: `"LOADING MEMORY - Agent ID: <wrong-id>"`
- Agent responds with wrong persona/knowledge
- Memory blocks don't match expected agent

**Fix**:
- Verify self.agent_id is correct before memory load
- Check log: `"Loaded block 'persona': ..."`

### Failure Point 7: Message Processing Uses Wrong Agent
**Impact**: User queries sent to wrong Letta agent

```python
async def llm_node(self, chat_ctx, tools, model_settings):
    # In legacy mode (non-hybrid):
    response = await self.letta_client.agents.messages.create(
        agent_id=self.agent_id,  # ⚠️ Wrong agent_id → wrong agent processes message
        messages=[{"role": "user", "content": user_message}]
    )
```

**Symptoms**:
- Log shows: `"Current Agent ID: <wrong-id>"` in query processing
- Responses don't match Agent_66's knowledge/persona
- Wrong agent's memory updated

**Fix**:
- Check debug prefix in every response: `"[DEBUG: Using Agent ID xxx | Req yyy]"`
- Verify agent_id matches expected Agent_66

## Debugging Checklist

Run these checks in order to diagnose agent selection issues:

### 1. Environment Check
```bash
echo "VOICE_PRIMARY_AGENT_NAME: $VOICE_PRIMARY_AGENT_NAME"
echo "VOICE_PRIMARY_AGENT_ID: $VOICE_PRIMARY_AGENT_ID"
echo "USE_HYBRID_STREAMING: $USE_HYBRID_STREAMING"
```

**Expected**:
```
VOICE_PRIMARY_AGENT_NAME: Agent_66
VOICE_PRIMARY_AGENT_ID: <specific-uuid-if-set>
USE_HYBRID_STREAMING: true
```

### 2. Agent List Check
```bash
curl http://localhost:8283/v1/agents/ | jq '.[] | {id, name}'
```

**Look for**:
- Only ONE agent named "Agent_66"
- Note the ID of Agent_66

### 3. Voice Agent Startup Logs
```bash
grep "AGENT INITIALIZED" voice_agent.log
```

**Expected**:
```
AGENT INITIALIZED
Agent Name: Agent_66
Agent ID: <expected-uuid>
```

### 4. Agent Selection Message Logs
```bash
grep "AGENT SELECTION MESSAGE" voice_agent.log
```

**Expected**:
```
AGENT SELECTION MESSAGE RECEIVED
Agent ID: <expected-uuid>
Agent Name: Agent_66
Current Assistant Agent ID: <should-match>
```

### 5. Memory Loading Logs
```bash
grep "LOADING MEMORY" voice_agent.log
```

**Expected**:
```
LOADING MEMORY - Agent ID: <expected-uuid>
LOADING MEMORY - Agent Name: Agent_66
Memory loaded successfully via REST API
```

### 6. Query Processing Logs
```bash
grep "NEW QUERY RECEIVED" voice_agent.log
```

**Expected**:
```
NEW QUERY RECEIVED
Request ID: abc12345
Current Agent ID: <expected-uuid>
Current Agent Name: Agent_66
```

### 7. Response Generation Logs
```bash
grep "RESPONSE GENERATED BY AGENT" voice_agent.log
```

**Expected**:
```
RESPONSE GENERATED BY AGENT: <expected-uuid>
```

### 8. Browser Response Check
- Every voice response should start with:
  ```
  [DEBUG: Using Agent ID abc12345 | Req xyz67890]
  ```
- Verify the Agent ID (last 8 chars) matches expected agent

## Solutions by Symptom

### Symptom: Voice agent connects to wrong agent from the start

**Root Cause**: Environment variable misconfiguration or wrong agent found

**Solution**:
1. Check `PRIMARY_AGENT_NAME` and `PRIMARY_AGENT_ID` environment variables
2. Verify only one agent named "Agent_66" exists
3. Set `VOICE_PRIMARY_AGENT_ID` to specific UUID to force correct agent
4. Restart voice agent process after env changes

### Symptom: Agent selection message sent but ignored

**Root Cause**: Agent lock enforcement or message timing

**Solution**:
1. Verify `selectedAgent.name === "Agent_66"` in browser
2. Check if agent lock is rejecting switch (intended behavior for non-Agent_66)
3. Ensure message sent after `participantConnected` event

### Symptom: Duplicate agents in same room

**Root Cause**: Room assignment lock failure or stale room state

**Solution**:
1. Run room cleanup: `python cleanup_livekit_room.py`
2. Check `_ROOM_TO_AGENT` tracking in logs
3. Verify `request_handler()` rejects duplicate jobs

### Symptom: Agent uses wrong memory/persona

**Root Cause**: `self.agent_id` corrupted or wrong agent selected

**Solution**:
1. Check memory loading logs for correct agent ID
2. Verify `_load_agent_memory()` uses correct REST API call
3. Force memory reload by disconnecting and reconnecting

### Symptom: Responses don't match Agent_66's knowledge

**Root Cause**: Wrong agent processing queries or hybrid mode using wrong system instructions

**Solution**:
1. Check debug prefix in responses for agent ID
2. Verify `llm_node()` uses correct `self.agent_id`
3. In hybrid mode, check `agent_system_instructions` contains correct persona

## Recommended Configuration

To ensure consistent Agent_66 connection:

```bash
# In .env file or environment
VOICE_PRIMARY_AGENT_NAME=Agent_66
VOICE_PRIMARY_AGENT_ID=<specific-uuid-of-agent-66>  # STRONGLY RECOMMENDED
USE_HYBRID_STREAMING=true

# Get Agent_66 UUID
curl http://localhost:8283/v1/agents/ | jq '.[] | select(.name=="Agent_66") | .id'
```

**Why set VOICE_PRIMARY_AGENT_ID?**
- Removes ambiguity from name matching
- Prevents selecting wrong agent if duplicates exist
- Fastest agent selection (no search needed)

## Testing Agent Selection

```python
#!/usr/bin/env python3
"""Test which agent the voice system would select"""

import os
from letta_client import AsyncLetta
import asyncio

async def test_agent_selection():
    PRIMARY_AGENT_NAME = os.getenv("VOICE_PRIMARY_AGENT_NAME", "Agent_66")
    PRIMARY_AGENT_ID = os.getenv("VOICE_PRIMARY_AGENT_ID")

    client = AsyncLetta(base_url="http://localhost:8283")

    print(f"Environment configuration:")
    print(f"  PRIMARY_AGENT_NAME: {PRIMARY_AGENT_NAME}")
    print(f"  PRIMARY_AGENT_ID: {PRIMARY_AGENT_ID}")
    print()

    # Test Priority 1: Specific agent ID
    if PRIMARY_AGENT_ID:
        try:
            agent = await client.agents.retrieve(agent_id=PRIMARY_AGENT_ID)
            print(f"✅ SELECTED: {agent.name} (ID: {agent.id})")
            print(f"   Method: Specific agent ID from environment")
            return agent.id
        except Exception as e:
            print(f"❌ Configured agent ID not found: {e}")

    # Test Priority 2: Search by name
    agents = await client.agents.list()
    matches = [a for a in agents if a.name == PRIMARY_AGENT_NAME]

    if matches:
        agent = matches[0]
        print(f"✅ SELECTED: {agent.name} (ID: {agent.id})")
        print(f"   Method: First match by name")
        if len(matches) > 1:
            print(f"⚠️  WARNING: {len(matches)} agents with name '{PRIMARY_AGENT_NAME}'")
            print(f"   Only first match used. Consider setting VOICE_PRIMARY_AGENT_ID")
        return agent.id
    else:
        print(f"❌ No agent found with name '{PRIMARY_AGENT_NAME}'")
        print(f"   Voice agent would CREATE NEW AGENT")
        return None

if __name__ == "__main__":
    asyncio.run(test_agent_selection())
```

Save as `test_agent_selection.py` and run:
```bash
python test_agent_selection.py
```

## Conclusion

The voice agent system has a **complex agent selection flow** with multiple checkpoints:

1. **Primary Selection** (server-side): Environment variables determine initial agent
2. **Agent Lock** (server-side): Only PRIMARY_AGENT_NAME allowed for voice
3. **Browser Selection** (client-side): Can request agent switch, but subject to lock
4. **Instance Tracking** (server-side): Prevents duplicate instances
5. **Room Assignment** (server-side): One agent per room enforcement
6. **Memory Loading** (server-side): Uses current self.agent_id
7. **Message Processing** (server-side): Uses current self.agent_id

**The most reliable fix is to set VOICE_PRIMARY_AGENT_ID to the exact UUID of Agent_66.** This eliminates all ambiguity and ensures the correct agent is selected every time.
