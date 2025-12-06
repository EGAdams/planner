# Agent Communication Issues - Root Cause Analysis

## Executive Summary

The "Transport rejected the message" error has **THREE separate root causes**:

1. **Timing Issue**: Orchestrator started before WebSocket server existed
2. **Architecture Issue**: `inbox()` and `post_message()` create new transport instances
3. **No Connection Sharing**: Each function call creates new RAG transport fallback

## Problem Breakdown (GoF Pattern: Chain of Responsibility)

### Issue 1: Transport Initialization Race Condition

**Symptoms:**
- "Transport rejected the message" error in orchestrator_chat.py
- WebSocket server logs show no message delivery

**Root Cause:**
- Process start order:
  - Orchestrator: 08:47:40
  - WebSocket server: 09:34:39 (47 minutes later!)
  - Result: Orchestrator fell back to RAG transport

**Fix:**
```bash
# Ensure proper startup order:
1. Start WebSocket server first
2. Wait for it to be ready (port 3030 listening)
3. Then start orchestrator and other agents
```

---

### Issue 2: Dual Transport Architecture Problem

**Symptoms:**
- Orchestrator logs show "Messenger initialized using: websocket"
- But same logs show "[RAGBoardTransport] Found 25 results"
- Both transports active simultaneously!

**Root Cause in Code:**

`orchestrator_agent/main.py`:
```python
# Line 277-281
def run(self):
    print(f"[{AGENT_NAME}] Started. Listening on topic 'orchestrator'...")
    self.discover_agents()

    while True:
        messages = inbox("orchestrator", limit=5, render=False)  # ❌ Creates NEW transport!
```

The `inbox()` function (from `agent_messaging/__init__.py`) creates a **new** transport instance on every call:

`agent_messaging/messenger.py` line 68:
```python
self.transport_name, self.transport = TransportFactory.create_transport(
    agent_id=self.agent_id,
    letta_base_url=base_url,
    letta_api_key=api_key
)
```

**Problem Flow:**
1. Orchestrator creates `AgentMessenger` with WebSocket → ✅ Connects
2. Orchestrator calls `inbox()` function → ❌ Creates NEW `AgentMessenger` with RAG fallback
3. Orchestrator calls `post_message()` → ❌ Creates ANOTHER new `AgentMessenger` with RAG
4. Result: orchestrator_chat sends via WebSocket, orchestrator reads via RAG → Messages never meet!

---

### Issue 3: No Singleton Transport Pattern

**Symptoms:**
- Every message operation loads sentence transformers model (expensive!)
- logs show continuous "[RAGBoardTransport] Found 25 results" polling

**Root Cause:**
No shared transport instance. Each function creates its own:

```python
inbox()       → creates AgentMessenger → creates TransportFactory → creates RAGBoardTransport
post_message() → creates AgentMessenger → creates TransportFactory → creates RAGBoardTransport
send_message() → creates AgentMessenger → creates TransportFactory → creates RAGBoardTransport
```

**Performance Impact:**
- Sentence transformer model loaded ~6x per second
- No connection reuse
- No message batching

---

## Solution Architecture (GoF Patterns)

### Solution 1: Singleton Transport Manager (Singleton Pattern)

Create a global transport instance that all functions share:

```python
# agent_messaging/transport_manager.py (NEW FILE)
class TransportManager:
    _instance = None
    _transport = None

    @classmethod
    def get_transport(cls, agent_id: str = None):
        if cls._transport is None:
            name, transport = TransportFactory.create_transport(agent_id=agent_id)
            cls._transport = transport
            cls._transport_name = name
        return cls._transport_name, cls._transport
```

### Solution 2: Strategy Pattern for Transport Selection

Refactor orchestrator to use its own messenger consistently:

```python
class Orchestrator:
    def __init__(self, ...):
        # Create messenger ONCE
        self.messenger = AgentMessenger(agent_id=AGENT_NAME)

    def run(self):
        while True:
            # Use messenger instance, not global function
            messages = self.messenger.read_messages("orchestrator", limit=5)

            for msg in messages:
                # Process and route
                target_agent = self.decide_route(msg.content)

                # Send using same messenger instance
                self.messenger.send_to_agent(
                    target_agent,
                    routed_message,
                    topic=target_topic
                )
```

### Solution 3: Observer Pattern for WebSocket Messages

Make orchestrator subscribe to WebSocket topic once:

```python
async def run_async(self):
    # Subscribe once at startup
    await self.messenger.transport.subscribe(
        "orchestrator",
        callback=self._message_handler
    )

    # Wait for messages via callback
    while True:
        await asyncio.sleep(0.1)  # Just keep alive

async def _message_handler(self, message: AgentMessage):
    # Process message when it arrives
    target = self.decide_route(message.content)
    await self.messenger.transport.send(routed_message)
```

---

## Implementation Priority

### Phase 1: Quick Fix (Restart with correct order)
1. Stop all agents
2. Start WebSocket server
3. Wait 2 seconds
4. Start orchestrator
5. Start other agents

**Impact:** Orchestrator will connect to WebSocket

### Phase 2: Architecture Fix (Refactor messenger usage)
1. Create `TransportManager` singleton
2. Refactor `inbox()` and `post_message()` to use shared transport
3. Update orchestrator to use messenger instance

**Impact:** Single transport, no duplication

### Phase 3: Performance Optimization (Async + Observer)
1. Convert orchestrator to async/await
2. Use WebSocket subscriptions instead of polling
3. Eliminate RAG transport entirely

**Impact:** Real-time messaging, no polling overhead

---

## Testing Strategy

### Test 1: Verify Transport Selection
```bash
# Run test to confirm WebSocket connection
/home/adamsl/planner/.venv/bin/python3 \
  .claude/skills/agent-debug/scripts/test_websocket.py
```

Expected: "✅ Successfully connected to WebSocket server!"

### Test 2: Verify Message Flow
```bash
# Send test message via orchestrator_chat
cd a2a_communicating_agents/agent_messaging
python3 orchestrator_chat.py

# In chat, type:
: test message

# Check WebSocket server logs
tail -f ../../logs/websocket.log
```

Expected: See message received and delivered

### Test 3: Verify No RAG Fallback
```bash
# Monitor orchestrator logs
tail -f logs/orchestrator.log | grep -E "(WebSocket|RAGBoard)"
```

Expected: Only see "Using WebSocket transport", NO "[RAGBoardTransport]" messages

---

## Files Needing Changes

### Critical Files:
1. `a2a_communicating_agents/orchestrator_agent/main.py`
   - Change: Use messenger instance instead of `inbox()`/`post_message()`

2. `a2a_communicating_agents/agent_messaging/messenger.py`
   - Change: Add singleton transport management

3. `a2a_communicating_agents/agent_messaging/__init__.py`
   - Change: Update `inbox()` and `post_message()` to use shared transport

### New Files Needed:
1. `a2a_communicating_agents/agent_messaging/transport_manager.py`
   - Purpose: Singleton transport instance management

### Startup Scripts:
1. `a2a_communicating_agents/start_orchestrator.sh`
   - Change: Add dependency check for WebSocket server

2. Create: `a2a_communicating_agents/start_all.sh`
   - Purpose: Start services in correct order with health checks

---

## Next Steps

1. **Immediate**: Restart agents in correct order (5 minutes)
2. **Short-term**: Implement transport manager singleton (1-2 hours)
3. **Long-term**: Convert to async/await architecture (1 day)

## Questions for Discussion

1. Do we want to keep RAG transport as fallback, or enforce WebSocket-only?
2. Should we add health checks to startup scripts?
3. Do we want to migrate all agents to async/await or just orchestrator?
4. Should we implement message queuing for reliability?
