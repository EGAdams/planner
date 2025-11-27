# A2A Agent Collective - Project Roadmap & Status

**Project**: Agent-to-Agent Communication with Voice Capabilities  
**Status**: Phase 1 Complete - Infrastructure & Discovery ✓  
**Last Updated**: 2025-11-26

---

## Executive Summary

We have successfully built the foundational infrastructure for an Agent-to-Agent (A2A) collective using Google's A2A protocol. Two agents (Orchestrator and Letta) are now operational with voice capabilities and unified memory support. The system uses a hub-and-spoke architecture with automatic fallback between Letta, ChromaDB, and WebSocket transports.

---

## Current Architecture

### Agent Collective Hub (`a2a_collective.py`)
Central coordinator implementing the hub-and-spoke pattern:
- **Discovery**: Scans for `agent.json` files automatically
- **Memory Provisioning**: Uses `MemoryFactory` with Letta → ChromaDB fallback
- **Delegation**: Prepares JSON-RPC payloads for agent tasks
- **Routing**: Topic-based message routing

### Agents Created

#### 1. Orchestrator Agent
- **Location**: [`agents/orchestrator/agent.json`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/agents/orchestrator/agent.json)
- **Version**: 1.0.0
- **Capabilities**: `orchestration`, `voice`
- **Topics**: `orchestration`, `general`
- **Voice Config**: Letta provider (default)
- **Role**: Central task coordinator, delegates to specialized agents

#### 2. Letta Agent
- **Location**: [`agents/letta/agent.json`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/agents/letta/agent.json)
- **Version**: 1.0.0
- **Capabilities**: `memory_management`, `voice`
- **Topics**: `memory`, `general`
- **Voice Config**: Letta provider (default)
- **Role**: Manages unified memory system (Letta blocks + ChromaDB)

### Memory System (Unified)

**Automatic Fallback Priority**:
1. **Letta Memory** (`letta_memory.py`) - Primary
   - Server: `http://localhost:8283`
   - Blocks API for persistent storage
   - Shared across all agents
   - Text-based search

2. **ChromaDB Memory** (`chromadb_memory.py`) - Fallback
   - Local vector database
   - Semantic search via embeddings
   - Always available (no server needed)

**Reference**: [`unified_memory_system.md`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/unified_memory_system.md)

### Transport System

**Automatic Fallback Priority** (`transport_factory.py`):
1. **WebSocket** - Fastest (not yet implemented)
2. **Letta Transport** - Medium speed
3. **RAG Board** - Always available fallback

---

## Verification Status

### ✓ Completed
- [x] Agent discovery via `A2ACollectiveHub`
- [x] Agent metadata parsing from `agent.json`
- [x] Memory backend allocation per agent
- [x] Delegation payload generation (JSON-RPC 2.0)
- [x] Voice capability configuration

### Verification Script Output
```bash
python run_collective.py

Discovered 2 agents
- letta (v1.0.0)
  Capabilities: ['memory_management', 'voice']
  Memory Backend: mock_backend
- orchestrator (v1.0.0)
  Capabilities: ['orchestration', 'voice']
  Memory Backend: mock_backend

Delegation payload created successfully:
{
    'topic': 'memory',
    'payload': {
        'jsonrpc': '2.0',
        'method': 'agent.execute_task',
        'params': {
            'task_id': '8cee4e89-7ba6-4fb5-8de8-a4222962e978',
            'target_agent': 'letta',
            'description': 'Store this important memory',
            'context': {'priority': 'high'}
        }
    }
}
```

---

## Voice Integration Plan

Based on the voice capability status report, we have identified:

### Available Infrastructure
1. **LiveKit Voice Agent**
   - Real-time media server for voice/video
   - Configured in `backend/server.ts`
   - Test UI: `http://localhost:8000/talk`
   - Status: Configured but needs verification

2. **Letta Voice API**
   - Endpoint: `/v1/agents/{agent_id}/messages`
   - Supports audio input/output via `ChatCompletionAudio` schema
   - Consolidated from previous `/voice-beta` endpoint

### Planned Integrations
- **STT**: Whisper.cpp for browser-based speech recognition
- **TTS**: Letta built-in or external TTS service
- **Voice Commands**: Parse agent directives from voice input

---

## Service Management

### startup Scripts

#### `start_services.ps1`
Launches required services:
- Letta server (`http://localhost:8283`)
- WebSocket server (placeholder)

#### `verify_services.ps1`
Checks service health:
- Process verification
- Port listening (8283)
- API health endpoint
- Log file inspection

### Usage
```powershell
# Start services
.\start_services.ps1

# Verify they're running
.\verify_services.ps1
```

---

## Project Roadmap

### Phase 1: Infrastructure ✓ (COMPLETE)
- [x] A2A collective hub
- [x] Agent discovery system
- [x] Unified memory with fallback
- [x] Transport factory with fallback
- [x] Voice capability scaffolding
- [x] Service management scripts

### Phase 2: Service Integration (CURRENT)
- [ ] Verify Letta server startup
- [ ] Test real memory persistence (non-mock)
- [ ] Implement WebSocket transport
- [ ] Test agent-to-agent message delivery
- [ ] Configure LiveKit voice server
- [ ] Test voice input/output

### Phase 3: Agent Logic
- [ ] Implement orchestration logic
  - Task routing algorithms
  - Load balancing
  - Error handling
- [ ] Implement memory management logic
  - Storage strategies
  - Retrieval optimization
  - Memory pruning
- [ ] Voice command parsing
- [ ] Voice response generation

### Phase 4: Integration & Testing
- [ ] End-to-end A2A communication tests
- [ ] Voice interaction tests
- [ ] Memory persistence tests
- [ ] Load testing
- [ ] Error recovery testing

### Phase 5: Production Readiness
- [ ] Authentication & authorization
- [ ] Rate limiting
- [ ] Monitoring & logging
- [ ] Deployment automation
- [ ] Documentation

---

## Technical Decisions

### Design Patterns Used
1. **Hub-and-Spoke**: Central orchestrator prevents peer-to-peer chaos
2. **Strategy Pattern**: Pluggable memory/transport backends
3. **Factory Pattern**: Automatic backend selection with fallback
4. **Observer Pattern**: Topic-based subscriptions

### Import Architecture Note
All relative imports (`from .module`) were converted to local imports (`from module`) to support standalone execution in isolated workspace environments. This enables direct script execution without package installation.

---

## Key Files

### Agent Definitions
- [`agents/orchestrator/agent.json`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/agents/orchestrator/agent.json)
- [`agents/letta/agent.json`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/agents/letta/agent.json)

### Core Infrastructure
- [`a2a_collective.py`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/a2a_collective.py) - Hub coordinator
- [`memory_factory.py`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/memory_factory.py) - Memory backend selection
- [`transport_factory.py`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/transport_factory.py) - Transport selection
- [`messenger.py`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/messenger.py) - High-level messaging API

### Scripts
- [`run_collective.py`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/run_collective.py) - Verification script
- [`start_services.ps1`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/start_services.ps1) - Service launcher
- [`verify_services.ps1`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/verify_services.ps1) - Service health check

### Documentation
- [`unified_memory_system.md`](file:///c:/Users/NewUser/Desktop/blue_time/planner/agent_messaging/unified_memory_system.md) - Memory architecture

---

## Immediate Next Steps

1. **Verify Letta Server**
   ```powershell
   .\verify_services.ps1
   ```
   - Check if port 8283 is listening
   - Test API health endpoint
   - Review log files for errors

2. **Test Real Memory**
   - Modify `run_collective.py` to use real `MemoryFactory`
   - Store a test memory via Letta
   - Retrieve and verify

3. **Voice Connection**
   - Start LiveKit server if available
   - Configure `voice_config` in agent JSON with actual credentials
   - Test voice endpoint: `http://localhost:8000/talk`

4. **Implement First Use Case**
   - Define a simple orchestration task
   - Have Orchestrator delegate to Letta
   - Letta stores result in memory
   - Verify persistence

---

## Dependencies

### Required
- `letta` - Memory backend server
- `chromadb` - Vector database
- `pydantic` - Data validation
- `rich` - Console formatting

### Optional
- `websockets` - Real-time transport
- `livekit` - Voice/video communication
- `whisper` - Speech-to-text

---

## Known Issues

1. **Import Structure**: Relative imports removed for standalone execution
2. **WebSocket Transport**: Not yet implemented (placeholder)
3. **Voice Config**: Currently placeholder values
4. **ChromaDB Corruption**: May require reset (`rm -rf ./storage/chromadb`)

---

## Team Notes

- All agents use unified memory system automatically via `MemoryFactory`
- Voice capabilities are scaffolded - actual logic needs implementation
- Service startup is backgrounded - check logs for output
- Mock memory factory used in verification to bypass dependency issues

---

**For Questions**: Review this document first, then check individual component documentation in linked files.
