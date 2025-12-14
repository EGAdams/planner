# Agent Communication System - Migration Guide

**Version:** 1.0
**Date:** December 14, 2025
**Author:** Claude Code Team
**Purpose:** Complete guide to recreate the agent communication system in a new directory

---

## Table of Contents
1. [System Overview](#system-overview)
2. [How It Works (Simple Explanation)](#how-it-works-simple-explanation)
3. [Prerequisites](#prerequisites)
4. [Required Files - Complete List](#required-files-complete-list)
5. [Step-by-Step Migration Instructions](#step-by-step-migration-instructions)
6. [Configuration](#configuration)
7. [Testing the System](#testing-the-system)
8. [Troubleshooting](#troubleshooting)

---

## System Overview

This is an **agent-to-agent communication system** that allows different AI agents or programs to talk to each other. Think of it like a messaging app for computer programs.

**Key Features:**
- **Primary Method:** WebSocket (fast, real-time messaging)
- **Fallback 1:** Letta (backup when WebSocket fails)
- **Fallback 2:** RAG Board (final backup, always available)
- **Memory System:** Stores and retrieves past messages
- **Topic-based:** Agents can subscribe to specific topics/channels

---

## How It Works (Simple Explanation)

### The Simple Version
Imagine you have three ways to send a letter:
1. **Email (WebSocket)** - Fastest, but needs internet
2. **Text message (Letta)** - Medium speed, different network
3. **Physical mail (RAG Board)** - Always works, but slower

The system tries email first. If that fails, it tries text message. If that fails, it uses physical mail. This ensures messages ALWAYS get delivered.

### The Technical Flow

```
Your Agent wants to send a message
    ↓
TransportManager checks: "Do we already have a connection?"
    ↓
If NO → TransportFactory creates connection
    ↓
Try WebSocket first
    ├─ Success? → Use WebSocket for all future messages
    ├─ Failed? → Try Letta
        ├─ Success? → Use Letta for all future messages
        ├─ Failed? → Try RAG Board
            └─ Success? → Use RAG Board
    ↓
AgentMessenger sends your message using the working transport
    ↓
Other agents receive the message instantly (if WebSocket)
    or retrieve it when they check (if Letta/RAG)
```

**Key Design Pattern:**
- **TransportManager** = Singleton (only ONE connection for all agents)
- **TransportFactory** = Creates the right type of connection
- **AgentMessenger** = Easy-to-use interface for sending/receiving messages

---

## Prerequisites

### Required Software
You need Python installed on your machine. Here's what to check:

```bash
# Check Python version (need 3.10 or higher)
python3 --version

# Check pip is installed
pip3 --version
```

### Required Python Packages
These will be installed later, but here's the list:

```
websockets>=15.0.1       # For WebSocket connections
letta-client>=1.3.1      # For Letta fallback
chromadb>=1.3.0          # For memory storage
pydantic>=2.12.5         # For data validation
rich>=14.2.0             # For pretty console output
```

---

## Required Files - Complete List

### Core System Files (MUST HAVE)

**Location on Source Machine:** `/home/adamsl/planner/a2a_communicating_agents/agent_messaging/`

#### 1. Transport System (How messages travel)
```
agent_messaging/__init__.py                    # Package exports
agent_messaging/message_transport.py           # Base interface for all transports
agent_messaging/websocket_transport.py         # WebSocket implementation
agent_messaging/letta_transport.py             # Letta fallback implementation
agent_messaging/rag_board_transport.py         # RAG Board fallback implementation
agent_messaging/transport_factory.py           # Creates the right transport
agent_messaging/transport_manager.py           # Manages shared connections (Singleton)
```

**Full Paths:**
```
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/__init__.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/message_transport.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/websocket_transport.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/letta_transport.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/rag_board_transport.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/transport_factory.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/transport_manager.py
```

#### 2. Message System (Message structure)
```
agent_messaging/message_models.py              # AgentMessage, ConnectionConfig
agent_messaging/messenger.py                   # High-level API (AgentMessenger class)
```

**Full Paths:**
```
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/message_models.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/messenger.py
```

#### 3. Memory System (Remembers past messages)
```
agent_messaging/memory_backend.py              # Base memory interface
agent_messaging/letta_memory.py                # Letta-based memory
agent_messaging/chromadb_memory.py             # ChromaDB-based memory
agent_messaging/memory_factory.py              # Creates memory instances
```

**Full Paths:**
```
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/memory_backend.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/letta_memory.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/chromadb_memory.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/memory_factory.py
```

#### 4. WebSocket Server (Routes messages)
```
agent_messaging/websocket_server.py            # Server that routes messages
```

**Full Path:**
```
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/websocket_server.py
```

#### 5. Utility Scripts (Helper tools)
```
agent_messaging/send_agent_message.py          # Example: send a message
agent_messaging/send_hello.py                  # Example: send hello message
```

**Full Paths:**
```
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/send_agent_message.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/send_hello.py
```

---

### RAG System Files (REQUIRED for RAG Board fallback)

**Location on Source Machine:** `/home/adamsl/planner/rag_system/`

```
rag_system/__init__.py
rag_system/core/__init__.py
rag_system/core/document_manager.py            # Manages documents/messages
rag_system/core/rag_engine.py                  # RAG search engine
rag_system/core/context_provider.py            # Provides context
rag_system/models/__init__.py
rag_system/models/document.py                  # Document/Message models
rag_system/utils/__init__.py
rag_system/utils/text_processing.py            # Text utilities
rag_system/rag_tools.py                        # RAG helper functions
```

**Full Paths:**
```
/home/adamsl/planner/rag_system/__init__.py
/home/adamsl/planner/rag_system/core/__init__.py
/home/adamsl/planner/rag_system/core/document_manager.py
/home/adamsl/planner/rag_system/core/rag_engine.py
/home/adamsl/planner/rag_system/core/context_provider.py
/home/adamsl/planner/rag_system/models/__init__.py
/home/adamsl/planner/rag_system/models/document.py
/home/adamsl/planner/rag_system/utils/__init__.py
/home/adamsl/planner/rag_system/utils/text_processing.py
/home/adamsl/planner/rag_system/rag_tools.py
```

---

### Optional Files (Nice to have, not critical)

#### Test Files
```
agent_messaging/tests/test_memory_system.py
agent_messaging/tests/test_memory_system.sh
agent_messaging/tests/test_agent_discovery.sh
agent_messaging/tests/test_delegation.sh
```

**Full Paths:**
```
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/tests/test_memory_system.py
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/tests/test_memory_system.sh
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/tests/test_agent_discovery.sh
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/tests/test_delegation.sh
```

#### Documentation
```
agent_messaging/unified_memory_system.md
agent_messaging/ORCHESTRATOR_CHAT_GUIDE.md
agent_messaging/a2a_project_roadmap.md
```

**Full Paths:**
```
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/unified_memory_system.md
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/ORCHESTRATOR_CHAT_GUIDE.md
/home/adamsl/planner/a2a_communicating_agents/agent_messaging/a2a_project_roadmap.md
```

---

## Step-by-Step Migration Instructions

Follow these steps **EXACTLY** in this order.

### Step 1: Create New Directory Structure

On the new machine, create the directory structure:

```bash
# Choose where you want to install it
# Example: /home/yourname/new_project/

# Create main directory
mkdir -p /home/yourname/new_project/agent_messaging
mkdir -p /home/yourname/new_project/rag_system
mkdir -p /home/yourname/new_project/agent_messaging/tests
mkdir -p /home/yourname/new_project/agent_messaging/storage/chromadb
mkdir -p /home/yourname/new_project/rag_system/core
mkdir -p /home/yourname/new_project/rag_system/models
mkdir -p /home/yourname/new_project/rag_system/utils
mkdir -p /home/yourname/new_project/rag_system/storage
```

### Step 2: Copy All Files

You have two options:

#### Option A: Using SCP (if copying from another machine)

```bash
# From the NEW machine, run these commands
# Replace 'adamsl@source-machine' with actual username and hostname

# Copy agent_messaging directory
scp -r adamsl@source-machine:/home/adamsl/planner/a2a_communicating_agents/agent_messaging/* \
    /home/yourname/new_project/agent_messaging/

# Copy rag_system directory
scp -r adamsl@source-machine:/home/adamsl/planner/rag_system/* \
    /home/yourname/new_project/rag_system/
```

#### Option B: Manual Copy (if on same machine or using USB drive)

```bash
# Copy from source to destination
cp -r /home/adamsl/planner/a2a_communicating_agents/agent_messaging/* \
    /home/yourname/new_project/agent_messaging/

cp -r /home/adamsl/planner/rag_system/* \
    /home/yourname/new_project/rag_system/
```

### Step 3: Install Python Dependencies

```bash
# Navigate to your new project
cd /home/yourname/new_project

# Create a virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows

# Install required packages
pip install websockets>=15.0.1
pip install letta-client>=1.3.1
pip install chromadb>=1.3.0
pip install pydantic>=2.12.5
pip install rich>=14.2.0

# Optional: Save to requirements.txt
cat > requirements.txt << EOF
websockets>=15.0.1
letta-client>=1.3.1
chromadb>=1.3.0
pydantic>=2.12.5
rich>=14.2.0
EOF
```

### Step 4: Verify File Structure

Make sure your directory looks like this:

```bash
# Run this command to check
tree -L 2 /home/yourname/new_project

# Should output something like:
/home/yourname/new_project/
├── agent_messaging/
│   ├── __init__.py
│   ├── message_transport.py
│   ├── websocket_transport.py
│   ├── letta_transport.py
│   ├── rag_board_transport.py
│   ├── transport_factory.py
│   ├── transport_manager.py
│   ├── message_models.py
│   ├── messenger.py
│   ├── memory_backend.py
│   ├── letta_memory.py
│   ├── chromadb_memory.py
│   ├── memory_factory.py
│   ├── websocket_server.py
│   ├── send_agent_message.py
│   ├── send_hello.py
│   ├── storage/
│   └── tests/
├── rag_system/
│   ├── __init__.py
│   ├── core/
│   ├── models/
│   ├── utils/
│   ├── rag_tools.py
│   └── storage/
├── venv/
└── requirements.txt
```

### Step 5: Update Import Paths

The system uses **relative imports**, which should work automatically. However, if you get import errors, you may need to update the Python path.

**Create a setup file:**

```bash
# Create setup.py in /home/yourname/new_project/
cat > /home/yourname/new_project/setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="agent_messaging",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "websockets>=15.0.1",
        "letta-client>=1.3.1",
        "chromadb>=1.3.0",
        "pydantic>=2.12.5",
        "rich>=14.2.0",
    ],
)
EOF

# Install in development mode
pip install -e .
```

---

## Configuration

### Environment Variables

The system uses these environment variables. Create a `.env` file:

```bash
# Create .env file
cat > /home/yourname/new_project/.env << 'EOF'
# WebSocket Configuration
WEBSOCKET_URL=ws://localhost:3030

# Letta Configuration (optional, for fallback)
LETTA_BASE_URL=http://localhost:8283
LETTA_API_KEY=your_letta_api_key_here

# Memory Configuration
MEMORY_STORAGE_PATH=/home/yourname/new_project/agent_messaging/storage
EOF
```

**Load environment variables:**

```bash
# Add to your shell profile or run before using the system
export $(cat /home/yourname/new_project/.env | xargs)
```

### Configuration Settings

You can also configure the system in code:

```python
from agent_messaging import AgentMessenger
from agent_messaging.message_models import ConnectionConfig

# Create configuration
config = ConnectionConfig(
    url="ws://localhost:3030",
    reconnect_attempts=3,
    reconnect_delay=1.0,
    timeout=30.0
)

# Create messenger with config
messenger = AgentMessenger("my-agent-id", ws_config=config)
```

---

## Testing the System

### Test 1: Start WebSocket Server

```bash
# In Terminal 1
cd /home/yourname/new_project
source venv/bin/activate
python agent_messaging/websocket_server.py
```

**Expected Output:**
```
[12:34:56] INFO: WebSocket server starting on ws://localhost:3030
[12:34:56] INFO: Server ready for connections
```

### Test 2: Send a Test Message

```bash
# In Terminal 2 (keep server running in Terminal 1)
cd /home/yourname/new_project
source venv/bin/activate
python agent_messaging/send_hello.py
```

**Expected Output:**
```
Connecting to WebSocket at ws://localhost:3030
Connected successfully!
Sending hello message...
Message sent successfully!
```

### Test 3: Python API Test

Create a test script:

```bash
cat > /home/yourname/new_project/test_messaging.py << 'EOF'
import asyncio
from agent_messaging import AgentMessenger, AgentMessage

async def test_messaging():
    # Create two agents
    agent_a = AgentMessenger("agent-a")
    agent_b = AgentMessenger("agent-b")

    # Agent B subscribes to messages
    received = []
    async def handle_message(msg: AgentMessage):
        print(f"Agent B received: {msg.content}")
        received.append(msg)

    await agent_b.subscribe("general", handle_message)

    # Agent A sends message
    await agent_a.send_to_agent(
        "agent-b",
        "Hello from Agent A!",
        topic="general"
    )

    # Wait for message delivery
    await asyncio.sleep(1)

    # Verify
    assert len(received) == 1, "Message not received!"
    print("✓ Test passed! Message delivered successfully.")

    # Cleanup
    await agent_a.disconnect()
    await agent_b.disconnect()

if __name__ == "__main__":
    asyncio.run(test_messaging())
EOF

# Run test
python test_messaging.py
```

**Expected Output:**
```
Agent B received: Hello from Agent A!
✓ Test passed! Message delivered successfully.
```

### Test 4: Fallback System Test

```bash
# Stop the WebSocket server (Ctrl+C in Terminal 1)
# Then run the test again

python test_messaging.py
```

**Expected Output:**
```
WARNING: WebSocket unavailable, using Letta transport...
# OR
WARNING: WebSocket unavailable, using RAG message board (fallback)
Agent B received: Hello from Agent A!
✓ Test passed! Message delivered successfully.
```

---

## Troubleshooting

### Problem 1: "Module not found" errors

**Solution:**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install in development mode
pip install -e /home/yourname/new_project

# Or add to Python path
export PYTHONPATH=/home/yourname/new_project:$PYTHONPATH
```

### Problem 2: WebSocket server won't start

**Symptoms:** Port already in use

**Solution:**
```bash
# Find process using port 3030
lsof -i :3030
# OR
netstat -tulpn | grep 3030

# Kill the process
kill -9 <PID>

# Or change port in .env
WEBSOCKET_URL=ws://localhost:3031
```

### Problem 3: "No module named 'rag_system'"

**Solution:**
```bash
# Check rag_system is in the right location
ls -la /home/yourname/new_project/rag_system

# Verify __init__.py exists
ls /home/yourname/new_project/rag_system/__init__.py

# Add to Python path
export PYTHONPATH=/home/yourname/new_project:$PYTHONPATH
```

### Problem 4: Permission errors on storage directory

**Solution:**
```bash
# Give write permissions
chmod -R 755 /home/yourname/new_project/agent_messaging/storage
chmod -R 755 /home/yourname/new_project/rag_system/storage
```

### Problem 5: Letta fallback not working

**Solution:**
```bash
# Check Letta server is running
curl http://localhost:8283/health

# If not running, start Letta server
letta server

# Or disable Letta fallback (will use RAG only)
# In transport_factory.py, remove LettaTransport from priority list
```

---

## Quick Reference Commands

```bash
# Start WebSocket Server
cd /home/yourname/new_project
source venv/bin/activate
python agent_messaging/websocket_server.py

# Send Test Message
python agent_messaging/send_hello.py

# Run Tests
python -m pytest agent_messaging/tests/

# Check System Status
python -c "from agent_messaging import AgentMessenger; print('✓ System OK')"

# View Logs
tail -f /var/log/agent_messaging.log  # If logging to file
```

---

## File Checklist

Use this checklist to verify all files are copied:

### Core System (17 files - MUST HAVE)
- [ ] `agent_messaging/__init__.py`
- [ ] `agent_messaging/message_transport.py`
- [ ] `agent_messaging/websocket_transport.py`
- [ ] `agent_messaging/letta_transport.py`
- [ ] `agent_messaging/rag_board_transport.py`
- [ ] `agent_messaging/transport_factory.py`
- [ ] `agent_messaging/transport_manager.py`
- [ ] `agent_messaging/message_models.py`
- [ ] `agent_messaging/messenger.py`
- [ ] `agent_messaging/memory_backend.py`
- [ ] `agent_messaging/letta_memory.py`
- [ ] `agent_messaging/chromadb_memory.py`
- [ ] `agent_messaging/memory_factory.py`
- [ ] `agent_messaging/websocket_server.py`
- [ ] `agent_messaging/send_agent_message.py`
- [ ] `agent_messaging/send_hello.py`

### RAG System (10 files - MUST HAVE)
- [ ] `rag_system/__init__.py`
- [ ] `rag_system/core/__init__.py`
- [ ] `rag_system/core/document_manager.py`
- [ ] `rag_system/core/rag_engine.py`
- [ ] `rag_system/core/context_provider.py`
- [ ] `rag_system/models/__init__.py`
- [ ] `rag_system/models/document.py`
- [ ] `rag_system/utils/__init__.py`
- [ ] `rag_system/utils/text_processing.py`
- [ ] `rag_system/rag_tools.py`

### Directories (7 directories)
- [ ] `agent_messaging/`
- [ ] `agent_messaging/storage/`
- [ ] `agent_messaging/storage/chromadb/`
- [ ] `agent_messaging/tests/`
- [ ] `rag_system/`
- [ ] `rag_system/core/`
- [ ] `rag_system/models/`
- [ ] `rag_system/utils/`
- [ ] `rag_system/storage/`

---

## Summary

**What you need to do:**
1. Create directory structure (Step 1)
2. Copy 27 files from source machine (Step 2)
3. Install 5 Python packages (Step 3)
4. Verify structure (Step 4)
5. Run setup.py (Step 5)
6. Configure .env file (Configuration section)
7. Test with provided scripts (Testing section)

**Estimated Time:** 30-60 minutes

**If you get stuck:**
1. Check the troubleshooting section
2. Verify all files were copied correctly
3. Ensure Python virtual environment is activated
4. Check environment variables are set

**Support:**
- Review this document from the beginning
- Check file paths are correct
- Verify Python version is 3.10+
- Ensure all dependencies are installed

---

**End of Migration Guide**
