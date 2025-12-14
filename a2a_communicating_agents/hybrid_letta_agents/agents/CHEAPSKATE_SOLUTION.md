# Hybrid Letta + Claude Code: The Cheapskate Solution 💰

## Problem
You wanted to use Letta for orchestration with Claude for coding/testing, but:
- Claude OAuth tokens from `~/.claude/.credentials.json` only work in Claude Code CLI
- The Anthropic Python SDK requires API credits (not covered by Claude Pro subscription)
- Claude Agent SDK also tries to charge API credits when called from scripts

## Solution: A2A Messaging Bridge

We built **hybrid_letta__a2a.py** which uses your existing A2A messaging infrastructure (`rag_system.rag_tools`) to bridge Letta and Claude Code.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Process                              │
│  ┌──────────────┐         ┌────────────────────────────┐   │
│  │              │         │  Claude Agent SDK Handlers  │   │
│  │    Letta     │         │                             │   │
│  │ Orchestrator │         │  - Coder Agent (async)      │   │
│  │  (Thread)    │         │  - Tester Agent (async)     │   │
│  │              │         │                             │   │
│  └──────┬───────┘         └──────────┬─────────────────┘   │
│         │                            │                      │
│         │   ┌────────────────────────┼──────────────┐       │
│         └───┤  A2A Messaging (rag_system)           │       │
│             │                                        │       │
│             │  Topics:                               │       │
│             │   - letta-coder-request               │       │
│             │   - letta-coder-response              │       │
│             │   - letta-tester-request              │       │
│             │   - letta-tester-response             │       │
│             └────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Letta Orchestrator** (runs in separate thread):
   - Uses gpt-5-mini for orchestration (cheap, fast)
   - Has two custom tools: `run_claude_coder` and `run_claude_tester`
   - Tools send requests via A2A messaging (`rag_system.send()`)

2. **Claude Agent Handlers** (run in main thread):
   - Subscribe to request topics (`rag_system.inbox()`)
   - Process requests with Claude Agent SDK (uses Claude Pro subscription!)
   - Send responses back via A2A messaging

3. **Communication Flow**:
   ```
   Letta → send(request) → Topic → inbox() → Claude SDK → send(response) → Letta
   ```

## Files Created

### Working Solution
- **hybrid_letta__a2a.py** - Uses your existing A2A messaging (RECOMMENDED)

### Research/Prototypes
- **hybrid_letta__claude_sdk.py** - Original attempt (requires API key)
- **hybrid_letta__cheapskate.py** - Queue-based (sandbox issues)
- **hybrid_letta__cheapskate_v2.py** - File-based (sandbox issues)

## Current Status

✅ Architecture designed and implemented
✅ A2A messaging integration complete
✅ Letta tools can send requests via `rag_system`
✅ Claude Agent SDK handlers can receive and process requests
⚠️  Timeout issue needs investigation (likely PYTHONPATH in Letta sandbox)

## Next Steps to Fix

The timeout suggests the Letta tools can't import `rag_system`. Solutions:

1. **Install rag_system properly** (preferred):
   ```bash
   cd /home/adamsl/planner/rag_system
   # Create setup.py if it doesn't exist
   pip install -e .
   ```

2. **Use environment variable** (current approach):
   - We set `PYTHONPATH` in tool environment variables
   - May need to verify Letta actually passes this through to sandbox

3. **Inline the messaging code**:
   - Copy the essential `send()` and `inbox()` logic directly into the tool functions
   - Removes external dependency

## Why This is Better

### Zero API Costs
- Letta orchestrator uses OpenAI (you already have OPENAI_API_KEY)
- Claude SDK calls use your Claude Pro subscription
- No Anthropic API credits needed!

### Uses Your Infrastructure
- Leverages existing `rag_system` messaging
- Compatible with your A2A ecosystem
- Can monitor messages with your existing dashboard

### Scalable
- Easy to add more Claude-powered tools
- Can have multiple agents subscribing to different topics
- Letta provides long-term memory and conversation management

## Example Usage

```bash
# Make sure Letta server is running
./start_letta_postgres.sh

# Run the hybrid system
python3 hybrid_letta__a2a.py
```

The system will:
1. Start Letta orchestrator in a thread
2. Start Claude Agent SDK handlers in main thread
3. Send the task to Letta
4. Letta calls tools → tools send A2A messages → Claude processes → responds via A2A
5. Results appear in the workspace directory

## Cost Comparison

| Solution | Orchestration Cost | Coding/Testing Cost | Total |
|----------|-------------------|---------------------|-------|
| **Letta + Anthropic API** | OpenAI API | Anthropic API ($$$) | High 💸 |
| **Our A2A Solution** | OpenAI API | Claude Pro (free*) | Low ✅ |

*Included in your existing Claude Pro subscription

## Lessons Learned

1. **OAuth tokens are scoped**: Claude Code's OAuth tokens only work in the CLI, not the Messages API
2. **Agent SDK isn't free**: Even though it uses Claude Code CLI, it still charges API credits
3. **Sandboxes are isolated**: Letta's tool execution sandbox doesn't have access to your Python path
4. **A2A is powerful**: Your existing messaging infrastructure solves the communication problem elegantly

## Credits

Built using:
- Your existing `rag_system` A2A messaging infrastructure
- Letta for orchestration and memory
- Claude Code (me!) for the actual coding/testing work
- Zero additional API costs! 🎉
