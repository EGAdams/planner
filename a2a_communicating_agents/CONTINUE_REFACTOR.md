# Continue Async Refactor - Implementation Guide

## What's Been Completed ✅

### Phase 1: TransportManager Singleton ✅
- ✅ `agent_messaging/transport_manager.py` created
- ✅ Singleton pattern with asyncio.Lock for thread-safety
- ✅ Lifecycle management (connect/disconnect/reset)

### Phase 2: Messenger Refactor ✅
- ✅ `agent_messaging/messenger.py` refactored to use TransportManager
- ✅ All methods converted to async/await
- ✅ New async functions: send_to_agent_async, post_message_async, inbox_async, subscribe_async
- ✅ Backward compatibility wrappers for sync code
- ✅ `agent_messaging/__init__.py` updated with new exports

## Remaining Work - Phase 3-6

### Phase 3: Orchestrator Async Conversion (45 min)

**File**: `orchestrator_agent/main.py`
**Backup**: `orchestrator_agent/main.py.backup` (already created)

**Key Changes Needed**:

1. **Add async imports**:
```python
import asyncio
from a2a_communicating_agents.agent_messaging import (
    AgentMessenger,
    inbox_async,  # Use async version
    post_message_async  # Use async version
)
```

2. **Update Orchestrator.__init__**:
```python
def __init__(self, *, llm_client=None, model_id: Optional[str] = None):
    # ... existing init code ...
    self.messenger = AgentMessenger(agent_id=AGENT_NAME)  # Create messenger instance
    self._running = False
```

3. **Convert message handler to async callback (Observer Pattern)**:
```python
async def _handle_message(self, message: AgentMessage):
    """Observer callback for incoming messages."""
    # Check if already processed
    message_id = self._extract_message_id(message)
    if self._message_seen(message_id):
        return

    # Check if from self
    sender_name = (message.sender or "").strip().lower()
    if self._is_self_reference(sender_name):
        self._mark_message_processed(message_id)
        return

    try:
        content = message.content

        # Skip JSON-RPC responses
        if content.strip().startswith("{") and "jsonrpc" in content:
            log_update(f"Skipping machine response: {content[:50]}...")
            return

        log_update(f"Processing request: {content[:50]}...")

        # Route the message (sync routing is OK)
        decision = self.decide_route(content)

        if not decision or not decision.get("target_agent"):
            log_update("No target agent, responding directly")
            await self._respond_directly_async(
                user_request=content,
                reasoning=decision.get("reasoning") if decision else None
            )
            return

        # Forward to target agent
        target_agent = decision["target_agent"]
        log_update(f"Routing to {target_agent}")

        await self.messenger.send_to_agent(
            agent_id=target_agent,
            message=content,
            topic=self._get_topic_for_agent(target_agent)
        )

        self._mark_message_processed(message_id)

    except Exception as e:
        log_update(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
```

4. **Create async response method**:
```python
async def _respond_directly_async(
    self,
    user_request: str,
    reasoning: Optional[str] = None
):
    """Send response back to orchestrator topic."""
    response = f"Orchestrator: {reasoning or 'Processing...'}"
    await self.messenger.send_to_agent(
        agent_id="board",
        message=response,
        topic="orchestrator"
    )
```

5. **Convert main loop to async with Observer Pattern**:
```python
async def run_async(self):
    """
    Main async event loop using Observer Pattern.
    Subscribes to topic once, then handles messages via callbacks.
    """
    log_update("Started. Listening on topic 'orchestrator'...")

    # Discover agents
    self.discover_agents()

    # Subscribe to orchestrator topic (Observer Pattern)
    await self.messenger.subscribe("orchestrator", self._handle_message)

    log_update("Subscribed to 'orchestrator' topic. Waiting for messages...")

    # Keep running
    self._running = True
    try:
        while self._running:
            await asyncio.sleep(1)  # Just keep alive
    except KeyboardInterrupt:
        log_update("Shutting down...")
    finally:
        self._running = False

def stop(self):
    """Graceful shutdown."""
    self._running = False
```

6. **Update main() entry point**:
```python
def main():
    """Entry point with async support."""
    orchestrator = Orchestrator()

    try:
        asyncio.run(orchestrator.run_async())
    except KeyboardInterrupt:
        print(f"\n[{AGENT_NAME}] Shutting down gracefully...")

if __name__ == "__main__":
    main()
```

7. **Add helper method for topic routing**:
```python
def _get_topic_for_agent(self, agent_name: str) -> str:
    """Map agent name to its topic."""
    topic_map = {
        "coder-agent": "code",
        "tester-agent": "test",
        "dashboard-agent": "ops",
    }
    return topic_map.get(agent_name, agent_name)
```

**What to Keep Unchanged**:
- All sync helper methods (_extract_message_id, _message_seen, etc.)
- discover_agents() method
- decide_route() method (sync LLM calls are fine)
- Agent discovery and profiling logic

### Phase 4: Coder Agent Async (30 min)

**File**: `coder_agent/main.py`

**Pattern** (similar to orchestrator):

```python
import asyncio
from a2a_communicating_agents.agent_messaging import AgentMessenger

class CoderAgent:
    def __init__(self):
        self.agent_id = "coder-agent"
        self.messenger = AgentMessenger(agent_id=self.agent_id)
        self._running = False
        # ... other init ...

    async def _handle_message(self, message: AgentMessage):
        """Observer callback for code requests."""
        log_update(f"Received code request: {message.content[:50]}...")

        # Generate code (can call sync OpenAI functions)
        code = self._generate_code(message.content)

        # Send response
        await self.messenger.send_to_agent(
            agent_id="board",
            message=code,
            topic="orchestrator"  # Reply back to orchestrator topic
        )

    async def run_async(self):
        """Main event loop with Observer Pattern."""
        log_update("Started. Listening on topic 'code'...")

        # Subscribe to code topic
        await self.messenger.subscribe("code", self._handle_message)

        log_update("Subscribed to 'code' topic. Waiting for requests...")

        self._running = True
        while self._running:
            await asyncio.sleep(1)

    def _generate_code(self, request: str) -> str:
        """Generate code using LLM (sync is OK)."""
        # ... existing implementation ...
        pass

def main():
    agent = CoderAgent()
    asyncio.run(agent.run_async())

if __name__ == "__main__":
    main()
```

### Phase 5: Tester Agent Async (30 min)

**File**: `tester_agent/main.py`

**Same pattern** as coder agent:
- Subscribe to "test" topic
- Handle messages via async callback
- Run tests (sync is fine)
- Send results back to "orchestrator" topic

### Phase 6: Testing & Validation (30 min)

**Steps**:

1. **Stop all agents**:
```bash
bash stop_all.sh
```

2. **Start all agents** (scripts work with both sync/async):
```bash
bash start_all.sh
```

3. **Check logs for WebSocket connection**:
```bash
# Should see "Using WebSocket transport" for all agents
tail -50 ../logs/orchestrator.log | grep -E "(WebSocket|RAG)"
tail -50 logs/coder_agent.log | grep -E "(WebSocket|RAG)"
tail -50 logs/tester_agent.log | grep -E "(WebSocket|RAG)"
```

4. **Test message flow**:
```bash
cd agent_messaging
python3 orchestrator_chat.py

# Type: write a hello world in python
# Should see:
# - orchestrator receives via WebSocket
# - routes to coder
# - coder generates code
# - response appears
```

5. **Verify no RAG fallback**:
```bash
# Should see NO "[RAGBoardTransport]" messages in logs
tail -f ../logs/orchestrator.log | grep RAGBoard
# (should be empty)
```

## Implementation Order

1. **Start with orchestrator** - It's the hub, most critical
2. **Then coder agent** - Test orchestrator → coder flow
3. **Then tester agent** - Complete the triangle
4. **Test thoroughly** - End-to-end message flow
5. **Monitor logs** - Ensure WebSocket-only, no RAG fallback

## Success Criteria ✅

When complete, you should see:

```bash
# In logs/websocket.log
✅ Agent 'orchestrator-agent' connected (total: 1)
✅ Agent 'orchestrator-agent' subscribed to topic 'orchestrator'
✅ Agent 'coder-agent' connected (total: 2)
✅ Agent 'coder-agent' subscribed to topic 'code'
✅ Agent 'tester-agent' connected (total: 3)
✅ Agent 'tester-agent' subscribed to topic 'test'

# In logs/orchestrator.log
✅ Agent 'orchestrator-agent' using shared websocket transport
Subscribed to 'orchestrator' topic. Waiting for messages...

# NO "[RAGBoardTransport]" messages anywhere!
```

## Rollback if Needed

All files have `.backup` extensions:
- `orchestrator_agent/main.py.backup`
- `agent_messaging/messenger.py.backup`

To roll back:
```bash
mv orchestrator_agent/main.py.backup orchestrator_agent/main.py
mv agent_messaging/messenger.py.backup agent_messaging/messenger.py
```

## Next Steps

After this refactor is complete:

1. **Remove RAG transport fallback** (keep for memory/storage only)
2. **Add connection health checks**
3. **Add reconnection logic** for WebSocket failures
4. **Performance metrics** - Message latency, throughput
5. **Load testing** - Multiple concurrent messages
