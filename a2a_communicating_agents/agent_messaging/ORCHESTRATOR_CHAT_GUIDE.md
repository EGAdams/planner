# Orchestrator Chat System Guide

**Last Updated**: 2025-12-04
**Status**: ✅ WORKING

---

## Overview

The Orchestrator Chat System provides a terminal-based interactive chat interface to communicate with the Orchestrator Agent. This allows you to send requests, kick off other agents (like Coder and Tester agents), and receive responses in real-time.

## Quick Start

### From Smart Menu
```bash
# Run the Smart Menu and select:
"Open Orchestrator Chat Session"
```

### Direct Command
```bash
cd /home/adamsl/planner/a2a_communicating_agents
python agent_messaging/orchestrator_chat.py --auto-start
```

## System Architecture

### Message Flow

```
User Input (Chat Session)
    ↓
orchestrator_chat.py sends message
    ↓
    to_agent="board"
    topic="orchestrator"
    from_agent="dashboard-ui"
    ↓
RAG Transport (ChromaDB + JSONL cache)
    ↓
Orchestrator Agent polls topic="orchestrator"
    ↓
Orchestrator processes & routes request
    ↓
Orchestrator responds
    ↓
    to_agent="board"  ← CRITICAL: Must be set!
    topic="orchestrator"
    from_agent="orchestrator-agent"
    ↓
RAG Transport tags as "to:board"
    ↓
Chat session polls for agent_id="board", topic="orchestrator"
    ↓
Response appears in chat!
```

### Key Components

1. **orchestrator_chat.py**: Interactive chat client
   - Default agent_name: `dashboard-ui`
   - Default topic: `orchestrator`
   - Polls with `agent_id="board"`

2. **orchestrator_agent/main.py**: Orchestrator backend
   - Listens on topic: `orchestrator`
   - Polls every 10 seconds
   - Routes requests to specialist agents
   - **MUST** set `to_agent="board"` in all responses

3. **RAG Transport** (rag_board_transport.py):
   - Stores messages in ChromaDB
   - Local JSONL cache: `/home/adamsl/planner/storage/message_board.jsonl`
   - Filters by `to:{agent_id}` tags
   - Supports metadata-based queries

4. **Messenger** (messenger.py):
   - `post_message()`: Wrapper for posting to board
   - `post_to_board()`: Core posting logic
   - **Updated**: Now accepts `to_agent` parameter

## Critical Configuration

### For Responses to Appear in Chat

When posting messages that should be visible in the chat session, **always** include `to_agent="board"`:

```python
# ✅ CORRECT - Chat will see this
post_message(
    message="Your response here",
    topic="orchestrator",
    from_agent="orchestrator-agent",
    to_agent="board"  # ← Required!
)

# ❌ WRONG - Chat will NOT see this
post_message(
    message="Your response here",
    topic="orchestrator",
    from_agent="orchestrator-agent"
    # Missing to_agent="board"
)
```

### Why This Matters

The RAG transport filters messages by the `to:{agent_id}` tag:
- Chat session polls with `agent_id="board"`
- RAG transport looks for tag `to:board`
- Without `to_agent="board"`, the tag isn't created
- Message is stored but chat can't find it

## Troubleshooting

### Problem: Chat sends messages but gets no response

**Diagnosis**:
1. Check if Orchestrator is running:
   ```bash
   ps aux | grep orchestrator
   ```

2. Check orchestrator logs:
   ```bash
   tail -f /home/adamsl/planner/logs/orchestrator.log
   ```

3. Verify message was received:
   ```bash
   # Check JSONL cache
   tail -n 20 /home/adamsl/planner/storage/message_board.jsonl | grep orchestrator
   ```

**Solution**: Ensure Orchestrator responses include `to_agent="board"` (fixed in 2025-12-04 update)

### Problem: "Transport rejected the message"

**Diagnosis**: RAG transport connection issue

**Solution**:
1. Check ChromaDB directory exists:
   ```bash
   ls -la /home/adamsl/planner/storage/chromadb/
   ```

2. Restart chat session

### Problem: Messages appear delayed

**Explanation**: Orchestrator polls every 10 seconds, so responses may take up to 10 seconds to appear.

**To verify it's working**:
- After sending message, wait 15 seconds
- Type `/refresh` or press Enter to poll for new messages

## API Reference

### OrchestratorChatSession

```python
session = OrchestratorChatSession(
    agent_name="dashboard-ui",    # Your identity
    topic="orchestrator",         # Topic to monitor
    poll_limit=25,               # Max messages per poll
)

# Send message
session.send_user_message("Hello, orchestrator!")

# Fetch new messages
messages = session.fetch_new_messages()

# Display messages
session.render_messages(messages)
```

### Chat Commands

- `/refresh` or `/r`: Poll for new messages
- `/quit` or `/q`: Exit chat
- `/help`: Show available commands
- Empty line: Same as `/refresh`

## Recent Fixes (2025-12-04)

### Issue
Orchestrator received messages but responses weren't visible in chat session.

### Root Cause
Orchestrator's `post_message()` calls didn't specify `to_agent="board"`, so RAG transport didn't tag messages properly for chat session polling.

### Changes Made

1. **messenger.py**:
   - Added `to_agent` parameter to `post_to_board()`
   - Added `to_agent` parameter to `post_message()`
   - Default value: `"board"`

2. **orchestrator_agent/main.py**:
   - Added `to_agent="board"` to routing confirmation (line 350)
   - Added `to_agent="board"` to "no agent found" message (line 359)
   - Added `to_agent="board"` to direct responses (line 403)

### Files Changed
- `agent_messaging/messenger.py` (lines 266, 281, 361)
- `orchestrator_agent/main.py` (lines 350, 359, 403)

## Testing Checklist

After making changes to the chat system:

- [ ] Restart Orchestrator Agent
- [ ] Open chat session from Smart Menu
- [ ] Send test message: "Hello, can you hear me?"
- [ ] Wait 15 seconds
- [ ] Verify response appears in chat
- [ ] Test routing: "Can you help me write some code?"
- [ ] Verify routing confirmation appears
- [ ] Check logs for errors: `tail -f logs/orchestrator.log`

## Development Notes

### Adding New Response Points

When adding new places where Orchestrator responds, remember:

```python
# Template for responses visible in chat
post_message(
    message="Your response text",
    topic="orchestrator",         # Chat listens here
    from_agent=AGENT_NAME,        # Your identity
    to_agent="board"              # ← Don't forget!
)
```

### Message Deduplication

Both chat session and orchestrator deduplicate messages by `document_id`:
- Chat: `orchestrator_chat.py` lines 167-170
- Orchestrator: `main.py` lines 256-257

This prevents showing the same message twice.

### Transport Fallback Chain

The system tries transports in this order:
1. WebSocket (fastest) - `ws://localhost:3030`
2. Letta (medium) - `http://localhost:8283`
3. RAG Board (always available) - ChromaDB + JSONL

Currently, RAG Board is the primary transport.

## See Also

- `unified_memory_system.md` - RAG and memory architecture
- `a2a_project_roadmap.md` - Overall project roadmap
- `QUICK_REFERENCE.md` - System commands and status

---

**System is ready for chat communication!** 💬
