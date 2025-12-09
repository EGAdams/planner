# Interactive Chat Interface - Quick Start

## What Changed ✅

### 1. Removed Code Duplication
- **OLD**: `hybrid_letta_persistent.py` defined `run_codex_coder` function locally
- **NEW**: Imports `run_codex_coder` from `hybrid_letta__codex_sdk.py`
- **Result**: Single source of truth, easier to maintain

### 2. Uses Codex SDK (Node.js Bridge)
- **Removed**: `codex` CLI binary with `--experimental-json`
- **Now Using**: Node.js bridge that calls Codex SDK
- **Benefits**: Better error handling, structured JSON communication

### 3. Interactive Chat Interface
- **OLD**: Hard-coded messages in Python scripts
- **NEW**: Real-time chat interface with persistent memory
- **Features**: Commands, status, reset, continuous conversation

---

## Quick Start

### Start Chat Session
```bash
python3 chat_with_letta.py
```

### Chat with Agent
```
You: Write a Hello World Python program

🤖 Agent (14.2s):
   [Using tool: get_current_time]
   [Using tool: run_codex_coder]
   [Using tool: memory_insert]

I have created a simple Python program that prints "Hello, World!"
The file is located at: /home/.../hello_world.py

This task was completed on December 6, 2025.
```

### Check What We've Done
```
You: What have we done today?

🤖 Agent (3.1s):

Today, we have completed the following task:
- December 6, 2025: Created a 'Hello, World!' Python program.
  File Path: /home/.../hello_world.py
```

### Reset Agent (Start Fresh)
```
You: /reset

⚠️  Reset agent and delete all memory? (yes/no): yes
✓ Agent reset! Starting fresh session...
```

---

## Chat Commands

| Command | Description |
|---------|-------------|
| `/quit`, `/exit` | Exit the chat |
| `/reset` | Delete agent memory and start fresh |
| `/status` | Show current agent ID and memory status |
| `/help` | Show help message |

---

## How It Works

### Agent Persistence
```
.letta_agent_id       ← Stores agent ID
↓
Same agent reused     ← Memory persists
↓
Agent remembers all previous conversations
```

### Memory Tracking
Every task is automatically tracked:
1. Agent calls `get_current_time()` → Gets timestamp
2. Agent executes task → Uses `run_codex_coder()`
3. Agent calls `memory_insert()` → Logs to task_history
4. Future questions recall from memory

---

## Architecture

### File Structure
```
hybrid_letta__codex_sdk.py    ← Defines run_codex_coder (Node bridge)
                              ↓ (import)
hybrid_letta_persistent.py    ← Imports run_codex_coder, adds memory
                              ↓ (import)
chat_with_letta.py            ← Interactive chat interface
```

### Codex Integration
```
Python (Letta tool)
    ↓
hybrid_letta__codex_sdk.run_codex_coder()
    ↓
Node.js bridge script (codex_coder_bridge.mjs)
    ↓
Codex SDK
    ↓
OpenAI API
```

---

## Example Session

```bash
$ python3 chat_with_letta.py

======================================================================
                    LETTA ORCHESTRATOR CHAT
======================================================================

  Type your messages to interact with the persistent agent
  Commands:
    /quit, /exit     - Exit the chat
    /reset           - Reset agent (delete memory)
    /status          - Show agent status
    /help            - Show this help

======================================================================

Using Letta at http://localhost:8283
Found existing agent ID: agent-abc123
✓ Reusing existing agent: agent-abc123

🤖 Agent ID: agent-abc123
💾 Memory: Persistent (saved to .letta_agent_id)

💬 Chat session started. Type your message...

You: Create a calculator that adds two numbers

⏳ Thinking...

🤖 Agent (16.4s):
   [Using tool: get_current_time]
   [Using tool: run_codex_coder]
   [Using tool: memory_insert]

I have created a simple calculator function in calculator.py.
The function takes two numbers and returns their sum.
This task was completed on December 6, 2025 at 09:30:15 PM.

You: What have we built so far?

⏳ Thinking...

🤖 Agent (2.8s):

So far today, we have built:
1. Hello World program (hello_world.py) - created at 09:15:22 PM
2. Calculator function (calculator.py) - created at 09:30:15 PM

You: /quit

👋 Goodbye!
```

---

## Environment Variables

Make sure these are set:

```bash
export LETTA_BASE_URL="http://localhost:8283"  # Letta server
export OPENAI_API_KEY="sk-..."                 # For Letta + Codex
export ORCH_MODEL="openai/gpt-4o-mini"        # Optional
export CODEX_MODEL="gpt-5.1-codex"            # Optional
export CODEX_NODE_BRIDGE="/path/to/codex_coder_bridge.mjs"  # Optional
```

---

## Contracts Alignment ✅

All tools write to the same contract log:

```
tdd_contracts.jsonl
├── test_generation contracts
├── code_generation contracts  ← run_codex_coder writes here
├── test_run contracts
└── tdd_validation contracts
```

**How contracts align:**
1. `run_codex_coder` imported from `hybrid_letta__codex_sdk.py`
2. `CONTRACT_LOG_NAME` passed via `tool_exec_environment_variables`
3. All tools write to same `tdd_contracts.jsonl` file
4. Contracts can be validated together

---

## Troubleshooting

### Agent doesn't remember
```bash
# Check if agent ID exists
cat .letta_agent_id

# Should show: agent-abc123...
# If empty or missing, agent was reset
```

### Can't import run_codex_coder
```bash
# Make sure files are in same directory
ls -l hybrid_letta__codex_sdk.py hybrid_letta_persistent.py

# Both should be present
```

### Codex SDK errors
```bash
# Check Node bridge exists
echo $CODEX_NODE_BRIDGE

# Or check default location
ls node_executables/codex_coder_bridge.mjs
```

---

## Benefits

### Before (Hard-coded Messages)
```python
# Had to edit Python file every time
message = "Write a Hello World program"  # ← Hard-coded
main(message)
```

### After (Interactive Chat)
```bash
$ python3 chat_with_letta.py
You: Write a Hello World program         # ← Interactive!
You: Create a calculator
You: What have we done today?
```

### Advantages
✅ No code editing required
✅ Natural conversation flow
✅ Full memory persistence
✅ Easy to test different prompts
✅ Agent tracks all interactions
✅ Quick status checks with `/status`
✅ Easy reset with `/reset`

---

## Next Steps

1. **Start chatting**: `python3 chat_with_letta.py`
2. **Try the memory**: Ask agent "What have we done?"
3. **Test persistence**: Exit and restart - agent remembers!
4. **Build something**: Have the agent create code iteratively
5. **Track progress**: Agent logs everything with timestamps

Happy coding with your persistent Letta orchestrator! 🚀
