# Simple Migration Instructions - For Engineers

**What:** Move the agent communication system to a new directory

**Time Needed:** 15-30 minutes

**Difficulty:** Easy (just follow steps)

---

## Super Simple Version (Automated)

If you want the script to do everything for you:

```bash
# 1. Copy this directory to where you want the system
cp -r communication_setup_plan /your/new/location/

# 2. Go to that location
cd /your/new/location/communication_setup_plan

# 3. Run the migration script (it installs to current directory)
./migrate_agent_system.sh

# 4. Follow the prompts
# That's it! The script does everything else.
```

**OR** if you're already in the directory you want to use:

```bash
# Just run the script - it uses current directory by default
./migrate_agent_system.sh
```

The script will:
- ✓ Create all directories
- ✓ Copy all 27 files
- ✓ Set up Python environment
- ✓ Install all dependencies
- ✓ Create test scripts
- ✓ Verify everything works

---

## Manual Version (If You Want Control)

### Step 1: Copy Everything

```bash
# Create your new project directory
mkdir -p /your/new/project
cd /your/new/project

# Create directories
mkdir -p agent_messaging
mkdir -p rag_system

# Copy files
cp -r /home/adamsl/planner/a2a_communicating_agents/agent_messaging/* \
      agent_messaging/

cp -r /home/adamsl/planner/rag_system/* \
      rag_system/
```

### Step 2: Install Python Stuff

```bash
# Make sure you're in your project directory
cd /your/new/project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install websockets letta-client chromadb pydantic rich
```

### Step 3: Test It Works

```bash
# Terminal 1: Start server (from your project directory)
python agent_messaging/websocket_server.py

# Terminal 2: Send test message (from your project directory)
python agent_messaging/send_hello.py
```

If you see "Message sent successfully!" you're done!

---

## What Files You're Copying (27 total)

### Main System (17 files)
Located in: `/home/adamsl/planner/a2a_communicating_agents/agent_messaging/`

```
__init__.py
message_transport.py
websocket_transport.py        ← WebSocket (primary)
letta_transport.py             ← Letta fallback
rag_board_transport.py         ← RAG fallback
transport_factory.py           ← Chooses which transport to use
transport_manager.py           ← Manages connections
message_models.py              ← Message structure
messenger.py                   ← Easy API
memory_backend.py              ← Memory interface
letta_memory.py                ← Letta memory
chromadb_memory.py             ← ChromaDB memory
memory_factory.py              ← Creates memory
websocket_server.py            ← Server that routes messages
send_agent_message.py          ← Example script
send_hello.py                  ← Test script
```

### RAG System (10 files)
Located in: `/home/adamsl/planner/rag_system/`

```
__init__.py
core/__init__.py
core/document_manager.py       ← Manages messages
core/rag_engine.py             ← Search engine
core/context_provider.py       ← Context provider
models/__init__.py
models/document.py             ← Message structure
utils/__init__.py
utils/text_processing.py       ← Text helpers
rag_tools.py                   ← RAG utilities
```

---

## How the System Works (In 3 Sentences)

1. **WebSocket is tried first** (fast, real-time) - if it works, use it
2. **Letta is tried second** (medium speed) - if WebSocket fails
3. **RAG Board is tried last** (always works) - if both fail

That's it. It automatically picks the best available method.

---

## Common Problems & Solutions

### "Module not found" error
```bash
# Make sure you're in the right directory
cd /your/new/project

# Activate virtual environment first!
source venv/bin/activate
```

### "Port already in use" error
```bash
# Kill existing server
killall -9 python
# Then restart server
```

### "Permission denied" error
```bash
# Give yourself permission (from your project directory)
chmod -R 755 agent_messaging
chmod -R 755 rag_system
```

---

## Quick Commands Cheat Sheet

```bash
# Start server
python agent_messaging/websocket_server.py

# Test system
python agent_messaging/send_hello.py

# Check if installed correctly
python -c "from agent_messaging import AgentMessenger; print('OK')"

# See what packages are installed
pip list | grep -E "websocket|letta|chromadb"
```

---

## Need More Help?

1. **Automated way:** Use `migrate_agent_system.sh` script
2. **Manual way:** Follow Step 1-3 above
3. **Full details:** Read `AGENT_COMMUNICATION_SYSTEM_MIGRATION_GUIDE.md`
4. **File list:** Check `MIGRATION_QUICK_REFERENCE.txt`

---

## That's It!

Don't overthink it. Either:
- Run the script (easiest)
- Copy files + install packages (simple)

Then test it. If test works, you're done.
