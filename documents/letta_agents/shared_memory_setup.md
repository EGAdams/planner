# 🔗 Letta Shared Memory Setup - Multi-Agent Collaboration

## What Is This?

This enables **true shared memory across all AI agents** working on your projects. Any agent (Claude, GPT, local LLMs, etc.) can read and write to the same memory blocks via Letta Server.

## 🎯 Why Use Letta Shared Memory?

**Current Setup (Local ChromaDB):**
- ✅ Fast local search
- ✅ Private memory
- ❌ Each session is isolated
- ❌ Can't share across different AI agents
- ❌ Memory lost when switching tools

**With Letta Shared Memory:**
- ✅ **All agents share the same memory**
- ✅ **Persistent across tools and sessions**
- ✅ **Real-time sync** - Agent A logs error, Agent B finds it instantly
- ✅ **Supports multiple projects/teams**
- ✅ **Web UI for browsing memory**

---

## 🚀 Setup Options

### Option 1: Local Letta Server (Recommended for Teams)

**Pros**: Free, private, full control, no API limits
**Cons**: Need to run a server

#### Installation

```bash
# 1. Install Letta
pip install letta

# 2. Start Letta server
letta server

# Server will start at http://localhost:8283
# Keep this terminal running
```

#### Verify Connection

```bash
# In another terminal
curl http://localhost:8283/health

# Should return: {"status":"ok"}
```

---

### Option 2: Letta Cloud (Easiest)

**Pros**: No setup, managed service, accessible anywhere
**Cons**: Requires API key, may have rate limits

#### Setup

```bash
# 1. Get API key from https://letta.com
# 2. Set environment variable
export LETTA_API_KEY="your_api_key_here"

# Add to ~/.bashrc for persistence
echo 'export LETTA_API_KEY="your_api_key_here"' >> ~/.bashrc
```

---

## 🔧 Integration with Our Memory System

### Method 1: Sync Local Memory to Letta (Hybrid Approach)

Keep using our fast local ChromaDB, but periodically sync to Letta for sharing:

```bash
# Sync all local memory to Letta server
python3 letta_memory_bridge.py sync

# This creates a shared memory block that all agents can access
```

**When to sync:**
- After fixing major bugs
- End of work session
- Before switching to another AI agent
- After important client meetings

### Method 2: Direct Letta Access

Use Letta blocks directly without local storage:

```python
from letta_memory_bridge import LettaMemoryBridge

# Connect to Letta
bridge = LettaMemoryBridge()  # Auto-detects local or cloud

# Create a shared memory block
bridge.create_block(
    label="parser_bugs",
    value="Collection of parser-related bugs and fixes"
)

# List all shared blocks
blocks = bridge.list_blocks()
for block in blocks:
    print(f"{block.label}: {block.value[:100]}")
```

---

## 💡 Usage Examples

### Example 1: Multi-Agent Debug Session

**Agent A (Claude)** encounters an error:

```python
from rag_tools import log_error
from letta_memory_bridge import LettaMemoryBridge

# Log error locally
log_error("TypeError: parser.on is not a function", "parsers.py:145")

# Sync to Letta for other agents
bridge = LettaMemoryBridge()
bridge.sync_from_local_rag()
```

**Agent B (GPT-4)** later works on the same codebase:

```python
# Agent B queries Letta shared memory
bridge = LettaMemoryBridge()
blocks = bridge.list_blocks()

# Finds the error Agent A logged!
# Can use the solution without re-debugging
```

### Example 2: Team Shared Knowledge Base

Multiple developers/agents contributing to shared knowledge:

```bash
# Developer 1 with Claude
python3 letta_memory_bridge.py create-block \
  "chromadb_gotchas" \
  "1. Requires $and operator for multiple filters
   2. Embedding dimension must match model
   3. Collection names cannot have spaces"

# Developer 2 with local agent
python3 letta_memory_bridge.py list
# Sees the gotchas block created by Developer 1

# Developer 2 adds more
python3 letta_memory_bridge.py create-block \
  "deployment_checklist" \
  "1. Run tests
   2. Update version
   3. Tag release
   4. Deploy to staging first"
```

### Example 3: Cross-Session Memory

**Monday - Claude session:**
```python
remember("Client wants dark mode by Friday", "Urgent Feature", project="website")
bridge.sync_from_local_rag()
```

**Wednesday - GPT-4 session:**
```python
# GPT-4 can access Monday's memory via Letta
bridge = LettaMemoryBridge()
bridge.list_blocks()  # Sees "Urgent Feature" logged by Claude
```

---

## 🛠️ Advanced: Creating Letta Agents

Create specialized agents that automatically access shared memory:

```python
from letta_memory_bridge import LettaMemoryBridge

bridge = LettaMemoryBridge()

# Create an agent with access to shared project memory
agent_id = bridge.create_agent_with_shared_memory(
    agent_name="debug_assistant",
    project_name="planner"
)

# This agent can now read/write to shared memory blocks
# All agents using the same blocks see the same information
```

---

## 📊 Architecture Comparison

### Current (Local Only)
```
Claude Session A → ChromaDB (Local) → Isolated
GPT Session B   → ChromaDB (Local) → Isolated
```

### With Letta Shared Memory
```
Claude Session A ─┐
                  ├→ ChromaDB (Local, fast) ─┐
GPT Session B   ─┤                           ├→ Sync → Letta Server (Shared)
Local Agent C   ─┤                           │
Web Agent D     ─┘                           │
                                             │
All agents read/write same memory blocks ───┘
```

---

## 🔄 Sync Strategies

### Strategy 1: Manual Sync (Recommended to Start)

```bash
# At end of work session
python3 letta_memory_bridge.py sync

# Or in Python
from letta_memory_bridge import LettaMemoryBridge
bridge = LettaMemoryBridge()
bridge.sync_from_local_rag()
```

### Strategy 2: Auto-Sync Hook

Add to your shell profile:

```bash
# In ~/.bashrc
function mem-sync-on-exit {
    python3 /home/adamsl/planner/letta_memory_bridge.py sync --project planner
}
trap mem-sync-on-exit EXIT
```

### Strategy 3: Scheduled Sync

```bash
# Sync every hour via cron
0 * * * * cd /home/adamsl/planner && python3 letta_memory_bridge.py sync
```

---

## 🔐 Security & Privacy

### Local Server
- Runs on your machine
- No data leaves your network
- Full control over memory blocks
- Recommended for sensitive projects

### Letta Cloud
- Data stored on Letta's servers
- Encrypted in transit (HTTPS)
- Use for non-sensitive projects
- Great for distributed teams

---

## 🚨 Troubleshooting

### "Connection refused" error

**Local Server:**
```bash
# Check if server is running
curl http://localhost:8283/health

# If not, start it
letta server
```

**Letta Cloud:**
```bash
# Check API key is set
echo $LETTA_API_KEY

# If not set
export LETTA_API_KEY="your_key_here"
```

### "Unauthorized" error

You're connecting to Letta Cloud without an API key:

```python
# Explicitly use local server
bridge = LettaMemoryBridge(base_url="http://localhost:8283")

# Or set API key for cloud
bridge = LettaMemoryBridge(api_key="your_key_here")
```

### Blocks not syncing

```bash
# Force sync with verbose output
python3 -c "
from letta_memory_bridge import LettaMemoryBridge
bridge = LettaMemoryBridge()
bridge.sync_from_local_rag()
"
```

---

## 🎓 Complete Workflow Example

### Setup (One-time)

```bash
# 1. Start Letta server (or get API key for cloud)
letta server

# 2. Test connection
python3 letta_memory_bridge.py list

# 3. Initial sync
python3 letta_memory_bridge.py sync
```

### Daily Usage

**Morning - Start work with Claude:**

```python
from rag_tools import recall, remember
from letta_memory_bridge import LettaMemoryBridge

# Check shared memory for overnight updates
bridge = LettaMemoryBridge()
blocks = bridge.list_blocks()

# Check local memory
recall("yesterday's issues")

# Do work...
remember("Fixed auth bug", "Auth Fix")
```

**Afternoon - Switch to another AI agent:**

```bash
# Sync your morning work
python3 letta_memory_bridge.py sync

# Other agent can now see your morning's work in shared blocks
```

**Evening - Check team updates:**

```bash
# See what other agents/developers added
python3 letta_memory_bridge.py list
```

---

## 📈 Benefits by Use Case

### Solo Developer
- ✅ Memory persists across different AI tools
- ✅ Session continuity even after computer restarts
- ✅ Can query memory from any device

### Team of Developers
- ✅ Share debugging solutions
- ✅ Collective knowledge base
- ✅ Onboarding new team members faster

### Multiple AI Agents
- ✅ Claude learns from GPT's discoveries
- ✅ Local agents share with cloud agents
- ✅ Automated agents contribute to knowledge base

---

## 🔮 Future Enhancements

Potential additions to the shared memory system:

- [ ] **Bi-directional sync** - Letta changes update local ChromaDB
- [ ] **Conflict resolution** - Handle simultaneous edits
- [ ] **Memory versioning** - Track who changed what when
- [ ] **Memory subscriptions** - Get notified of new blocks
- [ ] **Cross-project memory** - Share gotchas across all projects
- [ ] **Memory analytics** - Which blocks are most accessed
- [ ] **Memory cleanup** - Auto-archive old blocks

---

## 📚 Next Steps

1. **Choose your setup**: Local server or Letta Cloud
2. **Test connection**: Run `python3 letta_memory_bridge.py list`
3. **Do initial sync**: `python3 letta_memory_bridge.py sync`
4. **Start using**: All new memories auto-sync or manual sync
5. **Share with team**: Give them this guide!

---

## 💬 Quick Commands Reference

```bash
# Start local Letta server
letta server

# Sync local memory to Letta
python3 letta_memory_bridge.py sync

# List shared blocks
python3 letta_memory_bridge.py list

# Create new shared block
python3 letta_memory_bridge.py create-block "label" "content"

# Use with Letta Cloud
python3 letta_memory_bridge.py sync --api-key=YOUR_KEY

# Use specific project
python3 letta_memory_bridge.py sync --project=myproject
```

---

**Status**: Ready to use! 🎉

Choose your setup and start sharing memory across all your AI agents!
