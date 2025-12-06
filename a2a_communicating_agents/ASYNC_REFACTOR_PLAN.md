# Complete Async/Await Refactor - Implementation Plan

## GoF Design Patterns Used

### 1. Singleton Pattern - TransportManager
**Purpose**: Single shared transport instance across all components
**Location**: `agent_messaging/transport_manager.py` (new)

```python
class TransportManager:
    """Singleton managing the global transport instance"""
    _instance = None
    _transport = None
    _transport_name = None
    _lock = asyncio.Lock()
```

### 2. Observer Pattern - Message Subscriptions
**Purpose**: Agents subscribe to topics and receive callbacks
**Implementation**: WebSocket transport already supports this

```python
# Agents subscribe once at startup
await transport.subscribe("orchestrator", callback=handle_message)

# Callbacks invoked when messages arrive
async def handle_message(message: AgentMessage):
    # Process immediately
```

### 3. Strategy Pattern - Transport Interface
**Purpose**: Clean interface for different transport backends
**Existing**: `MessageTransport` abstract base class

### 4. Factory Pattern - Transport Creation
**Purpose**: Automatic transport selection with fallback
**Existing**: `TransportFactory.create_transport_async()`

### 5. Facade Pattern - AgentMessenger
**Purpose**: Simple interface hiding transport complexity
**Enhanced**: Messenger uses TransportManager singleton

## Implementation Phases

### Phase 1: Core Infrastructure ✅ (30 min)
1. Create `TransportManager` singleton
2. Add async initialization support
3. Add connection lifecycle management

### Phase 2: Messenger Refactor (30 min)
1. Update `AgentMessenger` to use `TransportManager`
2. Convert all methods to async
3. Update `inbox()`, `post_message()`, `send()` to use shared transport

### Phase 3: Orchestrator Async Conversion (45 min)
1. Convert `Orchestrator` class to async
2. Implement Observer pattern for message handling
3. Replace polling loop with subscription callbacks
4. Update routing logic to be async

### Phase 4: Coder Agent Async (30 min)
1. Convert to async/await
2. Subscribe to "code" topic
3. Handle messages via callbacks

### Phase 5: Tester Agent Async (30 min)
1. Convert to async/await
2. Subscribe to "test" topic
3. Handle messages via callbacks

### Phase 6: Testing & Validation (30 min)
1. Unit tests for TransportManager
2. Integration tests for message flow
3. End-to-end orchestrator → coder → response test

**Total Time: ~3 hours**

## File Changes Overview

### New Files
- `agent_messaging/transport_manager.py` - Singleton transport
- `tests/test_transport_manager.py` - Unit tests
- `tests/test_async_communication.py` - Integration tests

### Modified Files
- `agent_messaging/messenger.py` - Use TransportManager, all async
- `agent_messaging/__init__.py` - Export async functions
- `orchestrator_agent/main.py` - Full async refactor
- `coder_agent/main.py` - Async conversion
- `tester_agent/main.py` - Async conversion

### Startup Scripts
- `start_orchestrator.sh` - No changes needed
- `start_coder_agent.sh` - No changes needed
- `start_tester_agent.sh` - No changes needed

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│         TransportManager (Singleton)        │
│  - Single WebSocket connection             │
│  - Thread-safe initialization              │
│  - Lifecycle management                    │
└──────────────┬──────────────────────────────┘
               │
               │ provides transport to
               │
    ┌──────────┴──────────┬──────────────────┐
    │                     │                  │
┌───▼────────┐    ┌──────▼─────┐    ┌──────▼─────┐
│Orchestrator│    │   Coder    │    │  Tester    │
│  (async)   │    │  (async)   │    │  (async)   │
│            │    │            │    │            │
│ subscribes │    │ subscribes │    │ subscribes │
│ "orchestr" │    │   "code"   │    │   "test"   │
└────────────┘    └────────────┘    └────────────┘
     │                 │                  │
     │                 │                  │
     └─────────────────┴──────────────────┘
                       │
                       │ all use
                       │
            ┌──────────▼──────────┐
            │  WebSocket Server   │
            │   (port 3030)       │
            │                     │
            │  - Routes messages  │
            │  - Topic-based pub/sub
            └─────────────────────┘
```

## Detailed Implementation

### Phase 1: TransportManager

```python
# agent_messaging/transport_manager.py

import asyncio
from typing import Optional, Tuple
from .message_transport import MessageTransport
from .transport_factory import TransportFactory

class TransportManager:
    """
    Singleton managing shared transport instance (GoF Singleton Pattern).

    Ensures all agents use the same WebSocket connection for efficient
    communication without creating duplicate connections or falling back
    to RAG transport.
    """

    _instance: Optional['TransportManager'] = None
    _transport: Optional[MessageTransport] = None
    _transport_name: Optional[str] = None
    _lock: asyncio.Lock = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._lock = asyncio.Lock()
        return cls._instance

    @classmethod
    async def get_transport(
        cls,
        agent_id: str,
        force_reconnect: bool = False,
        **kwargs
    ) -> Tuple[str, MessageTransport]:
        """
        Get or create the shared transport instance.
        Thread-safe via asyncio.Lock.
        """
        instance = cls()

        async with cls._lock:
            if force_reconnect or not cls._initialized:
                if cls._transport:
                    await cls._transport.disconnect()

                cls._transport_name, cls._transport = \
                    await TransportFactory.create_transport_async(
                        agent_id=agent_id,
                        **kwargs
                    )
                cls._initialized = True

            return cls._transport_name, cls._transport

    @classmethod
    async def disconnect(cls):
        """Disconnect the shared transport."""
        async with cls._lock:
            if cls._transport:
                await cls._transport.disconnect()
                cls._transport = None
                cls._transport_name = None
                cls._initialized = False

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if transport is initialized."""
        return cls._initialized
```

### Phase 2: Messenger Refactor

Key changes to `messenger.py`:

1. Use `TransportManager` instead of creating new transports
2. Convert all methods to async
3. Remove sync wrappers

```python
class AgentMessenger:
    """
    Facade for agent communication (GoF Facade Pattern).
    Uses TransportManager singleton for shared connection.
    """

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"agent-{uuid.uuid4().hex[:8]}"
        self._transport_initialized = False

    async def _ensure_transport(self):
        """Lazy initialization of transport via TransportManager."""
        if not self._transport_initialized:
            self.transport_name, self.transport = \
                await TransportManager.get_transport(self.agent_id)
            self._transport_initialized = True

    async def send_to_agent(
        self,
        agent_id: str,
        message: str,
        topic: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """Send message to specific agent (async)."""
        await self._ensure_transport()

        msg = AgentMessage(
            to_agent=agent_id,
            from_agent=self.agent_id,
            content=message,
            topic=topic or agent_id,
            priority=priority
        )

        return await self.transport.send(msg)

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[AgentMessage], Awaitable[None]]
    ):
        """
        Subscribe to topic (Observer Pattern).
        Callback invoked when messages arrive.
        """
        await self._ensure_transport()
        await self.transport.subscribe(topic, callback)

    async def read_messages(
        self,
        topic: str,
        limit: int = 10
    ) -> List[AgentMessage]:
        """Poll messages (fallback for non-WebSocket transports)."""
        await self._ensure_transport()

        if hasattr(self.transport, 'poll_messages'):
            return await self.transport.poll_messages("board", topic=topic)
        return []
```

Global helper functions:

```python
async def inbox_async(
    topic: str,
    limit: int = 10,
    agent_id: str = "global-inbox"
) -> List[AgentMessage]:
    """Async inbox using shared transport."""
    messenger = AgentMessenger(agent_id=agent_id)
    return await messenger.read_messages(topic, limit)

async def post_message_async(
    topic: str,
    content: str,
    agent_id: str = "global-sender",
    priority: MessagePriority = MessagePriority.NORMAL
) -> bool:
    """Async post using shared transport."""
    messenger = AgentMessenger(agent_id=agent_id)
    return await messenger.send_to_agent(
        agent_id="board",
        message=content,
        topic=topic,
        priority=priority
    )
```

### Phase 3: Orchestrator Async

```python
# orchestrator_agent/main.py

class Orchestrator:
    """
    Orchestrator using Observer Pattern for real-time message handling.
    Subscribes to 'orchestrator' topic and processes messages via callbacks.
    """

    def __init__(self, *, llm_client=None, model_id: Optional[str] = None):
        # ... existing init code ...
        self.messenger = AgentMessenger(agent_id=AGENT_NAME)
        self._running = False

    async def _handle_message(self, message: AgentMessage):
        """
        Observer callback for incoming messages (GoF Observer Pattern).
        Called automatically when messages arrive on subscribed topic.
        """
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

            # Route the message
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

### Phase 4 & 5: Coder and Tester Agents

Similar pattern for both:

```python
# coder_agent/main.py

class CoderAgent:
    """
    Coder agent using Observer Pattern.
    Subscribes to 'code' topic.
    """

    def __init__(self):
        self.agent_id = "coder-agent"
        self.messenger = AgentMessenger(agent_id=self.agent_id)
        self._running = False
        # ... other init ...

    async def _handle_message(self, message: AgentMessage):
        """Observer callback for code requests."""
        log_update(f"Received code request: {message.content[:50]}...")

        # Generate code
        code = await self._generate_code_async(message.content)

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

    async def _generate_code_async(self, request: str) -> str:
        """Generate code using LLM (async)."""
        # ... implementation ...
        pass

def main():
    agent = CoderAgent()
    asyncio.run(agent.run_async())

if __name__ == "__main__":
    main()
```

## Testing Strategy

### Unit Tests
```python
# tests/test_transport_manager.py

async def test_singleton_behavior():
    """Verify TransportManager is singleton."""
    tm1 = TransportManager()
    tm2 = TransportManager()
    assert tm1 is tm2

async def test_shared_transport():
    """Verify all agents use same transport."""
    name1, transport1 = await TransportManager.get_transport("agent1")
    name2, transport2 = await TransportManager.get_transport("agent2")
    assert transport1 is transport2
```

### Integration Tests
```python
# tests/test_async_communication.py

async def test_orchestrator_to_coder():
    """Test full message flow."""
    # Start orchestrator
    orchestrator = Orchestrator()
    asyncio.create_task(orchestrator.run_async())

    # Start coder
    coder = CoderAgent()
    asyncio.create_task(coder.run_async())

    # Send test message
    messenger = AgentMessenger("test-client")
    await messenger.send_to_agent(
        "board",
        "write hello world in python",
        topic="orchestrator"
    )

    # Wait for response
    await asyncio.sleep(2)

    # Verify code was generated
    # ... assertions ...
```

## Success Criteria

✅ All agents use single WebSocket connection (TransportManager)
✅ No RAG transport fallback for message passing
✅ Real-time message delivery via Observer callbacks
✅ No polling loops (except keep-alive)
✅ Sentence transformers loaded only once at startup
✅ Clean async/await throughout
✅ Full test coverage
✅ End-to-end orchestrator → coder → response works

## Rollback Plan

If issues arise:
1. All old code preserved with `.backup` extension
2. Can revert by restoring backups
3. `start_all.sh` works with both old and new code
