# 🚀 Letta Shared Memory - Quick Start

## TL;DR

**Enable memory sharing across ALL AI agents in 3 commands:**

```bash
# 1. Start Letta server (one-time setup)
letta server

# 2. Sync your local memory to Letta
python3 -c "from rag_tools import sync; sync()"

# 3. Now all agents can access your memories!
python3 -c "from rag_tools import shared; shared()"
```

---

## What This Does

**Before:**
```
You + Claude → Local Memory (only you can see it)
Teammate + GPT → Their Local Memory (isolated)
```

**After:**
```
You + Claude ────┐
Teammate + GPT ──┼→ Letta Server → SHARED MEMORY
Other AI tools ──┘   (everyone sees everything)
```

---

## Setup in 2 Minutes

### Option 1: Local Server (Private, Free)

```bash
# Terminal 1: Start Letta server
letta server

# Terminal 2: Test it works
python3 -c "from rag_tools import shared; shared()"
# Should show: "No shared blocks found" (first time is normal)

# Terminal 2: Sync your memory
python3 -c "from rag_tools import sync; sync()"
# Should show: "✅ Memory synced to Letta server"

# Terminal 2: Verify
python3 -c "from rag_tools import shared; shared()"
# Should show your shared memory blocks!
```

### Option 2: Letta Cloud (Zero Setup)

```bash
# 1. Get API key from https://letta.com

# 2. Set environment variable
export LETTA_API_KEY="your_api_key_here"

# 3. Sync
python3 -c "from rag_tools import sync; sync()"

# Done! Your memory is now in the cloud, accessible anywhere
```

---

## Daily Usage

### As an AI Agent (like me, Claude!)

```python
from rag_tools import remember, sync, recall, shared

# 1. Do your normal work
remember("Fixed the parser bug", "Parser Fix", project="planner")
log_error("TypeError in parsers.py:145", "parsers.py:145")

# 2. Sync to share with other agents
sync()

# 3. Other agents can now see your work!
```

### Checking Shared Memory

```python
from rag_tools import shared, recall

# See what other agents have shared
shared()

# Search across all shared memories
recall("parser bugs")
```

---

## Real-World Example

**Monday morning - You work with Claude:**

```python
from rag_tools import remember, sync

remember("Client wants dark mode by Friday", "Urgent Request")
log_fix("ChromaDB needs $and operator", "Use {'$and': [...]} format")

# End of session - share with team
sync()
```

**Monday afternoon - Teammate uses GPT-4:**

```python
from rag_tools import recall

# GPT-4 finds your morning's work!
results = recall("ChromaDB operator")
# Sees your fix about $and operator
```

**Tuesday - You switch to local AI:**

```python
from rag_tools import shared

# Your local AI sees the GPT-4 session from Monday
shared()
# Can build on what GPT-4 discovered
```

---

## Integration with Existing Workflow

**No changes needed!** Just add one line:

```python
# Your existing code
from rag_tools import remember, recall, log_error

remember("Something important", "Title")
recall("past issues")

# NEW: Add this to share with other agents
from rag_tools import sync
sync()  # That's it!
```

---

## Commands Reference

```python
from rag_tools import sync, shared

# Sync local memory to Letta
sync()

# List shared memory blocks
shared()

# Sync with API key (for Letta Cloud)
sync(api_key="your_key")

# Sync specific project
sync(project_name="my_project")
```

---

## When to Sync

**Recommended:**
- ✅ End of work session
- ✅ After fixing major bugs
- ✅ After important client meetings
- ✅ Before switching AI agents/tools

**Optional but helpful:**
- Auto-sync every hour (via cron)
- Sync after every commit (via git hook)
- Sync on shell exit (via trap)

---

## Troubleshooting

### "Connection refused"

Letta server isn't running:

```bash
# Start it in another terminal
letta server
```

### "Unauthorized"

Using Letta Cloud without API key:

```bash
export LETTA_API_KEY="your_key"
```

Or use local server instead:

```bash
letta server  # In another terminal
python3 -c "from rag_tools import sync; sync()"  # Will use local automatically
```

### Nothing shows in `shared()`

First sync hasn't happened yet:

```bash
python3 -c "from rag_tools import sync; sync()"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Your Local Machine                 │
│                                                     │
│  ┌─────────────┐                                   │
│  │  RAG Tools  │                                   │
│  │             │                                   │
│  │  remember() │──→ ChromaDB ──┐                  │
│  │  recall()   │    (fast,      │                  │
│  │  log_*()    │     local)     │                  │
│  └─────────────┘                │                  │
│                                  │                  │
│  ┌─────────────┐                │                  │
│  │   sync()    │────────────────┘                  │
│  └─────────────┘                                   │
│         │                                           │
└─────────┼───────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│              Letta Server (Shared)                  │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │         Memory Blocks (Shared)              │   │
│  │                                             │   │
│  │  • shared_memory_planner                    │   │
│  │  • parser_bugs                              │   │
│  │  • chromadb_gotchas                         │   │
│  │  • deployment_notes                         │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
          ▲
          │
┌─────────┼───────────────────────────────────────────┐
│         │       Other Agents/Developers             │
│  ┌─────────────┐                                   │
│  │   GPT-4     │                                   │
│  │  Local AI   │                                   │
│  │   Claude    │                                   │
│  │   Web UI    │                                   │
│  └─────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

---

## Next Steps

1. ✅ **Choose setup**: Local server or Letta Cloud
2. ✅ **Test**: `python3 -c "from rag_tools import shared; shared()"`
3. ✅ **First sync**: `python3 -c "from rag_tools import sync; sync()"`
4. ✅ **Use normally**: Keep using `remember()`, `recall()`, etc.
5. ✅ **Share**: Add `sync()` to share with other agents

---

## Full Documentation

- **Detailed Setup**: `LETTA_SHARED_MEMORY_SETUP.md`
- **Memory Tools**: `RAG_QUICKSTART.md`
- **Agent Guide**: `CLAUDE_AGENT_MEMORY.md`

---

**Ready!** Your memories can now be shared across all AI agents! 🎉

```python
from rag_tools import sync
sync()  # Share your knowledge!
```
