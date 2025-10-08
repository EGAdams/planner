# 🧪 Testing Agent-to-Agent Messaging

## Test Plan

We'll test communication between:
1. **Agent A (This terminal)** - Current Claude session
2. **Agent B (New terminal)** - New Claude session
3. **Agent C (GPT)** - GPT-4 or other AI

---

## Test 1: Two Claude Agents

### Setup

**Terminal 1 (Agent A - You're here now):**
```python
from rag_tools import send, inbox

# Identify yourself
print("🤖 Agent A ready")

# Check inbox first (should be empty or have system messages)
inbox()
```

**Terminal 2 (Agent B - New Claude session):**
```bash
# In a new terminal window
cd /home/adamsl/planner

# Start Python
python3

# Then run:
from rag_tools import send, inbox

# Identify yourself
print("🤖 Agent B ready")

# Check inbox
inbox()
```

---

### Test Scenario 1: Basic Ping-Pong

**Agent A sends:**
```python
send("👋 Hello Agent B! This is Agent A checking in.", topic="testing", from_agent="agent-a")
```

**Agent B reads and responds:**
```python
# Read message
inbox("testing")

# Respond
send("👋 Hello Agent A! I received your message. Agent B here!", topic="testing", from_agent="agent-b")
```

**Agent A confirms:**
```python
# Read response
inbox("testing")

print("✅ Communication successful!")
```

---

### Test Scenario 2: Debugging Handoff

**Agent A (encounters bug):**
```python
from rag_tools import send, log_error

# Log error
log_error("TypeError in parsers.py:145", "parsers.py:145", project="planner")

# Notify other agents
send(
    """
    🐛 Bug Alert:
    - TypeError in parsers.py line 145
    - Error: parser.on is not a function
    - Need someone to investigate
    - Priority: High
    """,
    topic="debugging",
    from_agent="agent-a",
    priority="high"
)

print("📤 Bug report sent to other agents")
```

**Agent B (investigates):**
```python
from rag_tools import inbox, recall, send

# Check debugging messages
print("📬 Checking debugging messages...")
inbox("debugging")

# Search for similar issues in memory
print("\n🔍 Searching for similar issues...")
recall("TypeError parser")

# Send update
send(
    """
    🔍 Investigation Update:
    - Checking parsers.py:145
    - Found similar issue from last week
    - Likely needs EventEmitter implementation
    - Working on fix...
    """,
    topic="debugging",
    from_agent="agent-b"
)

print("📤 Investigation update sent")
```

**Agent A (sees update):**
```python
# Check for updates
print("📬 Checking for investigation updates...")
inbox("debugging")

print("✅ Communication working! Agent B is investigating.")
```

**Agent B (sends fix):**
```python
from rag_tools import send, log_fix

# Log the fix
log_fix(
    "Parser missing EventEmitter interface",
    "Add EventEmitter interface to Parser class",
    project="planner"
)

# Notify agents
send(
    """
    ✅ Bug Fixed!
    - Added EventEmitter interface to Parser
    - Tested locally - working
    - Committed as abc123
    - Ready for review
    """,
    topic="debugging",
    from_agent="agent-b"
)

print("✅ Fix complete and notified")
```

**Agent A (confirms fix):**
```python
# Check messages
inbox("debugging")

# Thank Agent B
send("👍 Thanks Agent B! Reviewing the fix now.", topic="debugging", from_agent="agent-a")

print("✅ Full debugging workflow complete!")
```

---

### Test Scenario 3: Session Handoff

**Agent A (end of session):**
```python
send(
    """
    📋 Session Handoff Notes:

    Completed today:
    - Fixed parser bug in parsers.py:145
    - Added EventEmitter interface
    - Updated tests

    Todo for next session:
    - Run full test suite
    - Update documentation
    - Deploy to staging

    Notes:
    - Database migration pending
    - Client meeting tomorrow at 2pm
    """,
    topic="handoff",
    from_agent="agent-a-morning"
)

print("📤 Handoff notes sent")
```

**Agent B (start of session):**
```python
# Check handoff notes
print("📬 Checking handoff from previous session...")
inbox("handoff")

# Acknowledge
send("✅ Handoff received. Starting on test suite.", topic="handoff", from_agent="agent-b-afternoon")

print("Ready to continue work!")
```

---

### Test Scenario 4: Multiple Topics

**Agent A:**
```python
# Send to different topics
send("Fixed authentication bug", topic="bugs", from_agent="agent-a")
send("Deployed v1.2.3 to staging", topic="deployment", from_agent="agent-a")
send("Updated API docs", topic="documentation", from_agent="agent-a")
send("Team meeting at 3pm", topic="general", from_agent="agent-a")
```

**Agent B:**
```python
# Check different topics
print("=== Bugs ===")
inbox("bugs")

print("\n=== Deployment ===")
inbox("deployment")

print("\n=== Documentation ===")
inbox("documentation")

print("\n=== General ===")
inbox("general")

print("\n=== All Messages ===")
inbox()
```

---

## Test 2: Claude + GPT Integration

### For GPT-4 (or other AI)

**Provide this to GPT:**

```python
# Setup (GPT will need to run this first)
import sys
sys.path.insert(0, '/home/adamsl/planner')

from rag_tools import send, inbox

# Identify as GPT
print("🤖 GPT Agent ready")

# Check messages from Claude
inbox()
```

### Test Scenario: Cross-AI Communication

**Agent A (Claude) sends:**
```python
send(
    "👋 Hello GPT! This is Claude. Can you help me review the parser fix?",
    topic="code-review",
    from_agent="claude"
)
```

**GPT responds:**
```python
# GPT checks inbox
inbox("code-review")

# GPT responds
send(
    "👋 Hello Claude! Sure, I'll review the parser fix. Where can I find it?",
    topic="code-review",
    from_agent="gpt-4"
)
```

**Agent A (Claude) continues:**
```python
inbox("code-review")

send(
    "Thanks! Check parsers.py:145. Added EventEmitter interface. Let me know if you spot any issues.",
    topic="code-review",
    from_agent="claude"
)
```

**GPT reviews and responds:**
```python
inbox("code-review")

send(
    """
    Code review complete:
    ✅ EventEmitter implementation looks good
    ✅ Proper error handling
    ⚠️  Suggestion: Add unit tests for edge cases

    Overall: LGTM (Looks Good To Me)
    """,
    topic="code-review",
    from_agent="gpt-4"
)
```

**Agent A (Claude) confirms:**
```python
inbox("code-review")

send(
    "✅ Thanks for the review! Will add those unit tests.",
    topic="code-review",
    from_agent="claude"
)

print("🎉 Cross-AI communication successful!")
```

---

## Verification Checklist

After each test, verify:

- [ ] Messages appear in `inbox()`
- [ ] Correct topic filtering works
- [ ] Sender identification is clear
- [ ] Message content is complete
- [ ] Timestamps are reasonable
- [ ] Both agents can see each other's messages

---

## Troubleshooting

### Agent B can't see Agent A's messages

**Check:**
```python
# In Agent A
from rag_tools import status
status()
# Note the "Total Chunks" count

# Send a message
send("Test", topic="test")

# Check status again
status()
# Should see Total Chunks increase
```

```python
# In Agent B
from rag_tools import status
status()
# Should show same Total Chunks as Agent A

inbox("test")
# Should see the message
```

### Messages not persisting

**Verify storage:**
```bash
ls -la storage/chromadb/
# Should see chroma.sqlite3 and other files
```

### Can't import rag_tools

**Fix path:**
```python
import sys
sys.path.insert(0, '/home/adamsl/planner')
from rag_tools import send, inbox
```

---

## Advanced Tests

### Test 5: Emergency Broadcast

**Agent A:**
```python
send(
    "🚨 URGENT: Production database CPU at 95%! All agents pause deployments!",
    topic="emergency",
    from_agent="monitoring-bot",
    priority="urgent"
)
```

**All other agents should check:**
```python
# Regularly check for emergencies
inbox("emergency")
```

### Test 6: Memory + Messaging Integration

**Agent A:**
```python
from rag_tools import remember, send

# Remember something
remember("ChromaDB requires $and operator for multiple filters", "ChromaDB Gotcha")

# Tell others
send("Documented ChromaDB gotcha in memory. Search for 'ChromaDB $and'", topic="documentation")
```

**Agent B:**
```python
from rag_tools import inbox, recall

# Read message
inbox("documentation")

# Search memory
recall("ChromaDB $and")
# Should find what Agent A documented
```

---

## Success Criteria

✅ **Pass**: Both agents can send and receive messages
✅ **Pass**: Topic filtering works correctly
✅ **Pass**: Messages persist across sessions
✅ **Pass**: Multiple agents can participate in same conversation
✅ **Pass**: Cross-AI communication works (Claude ↔ GPT)

---

## Quick Test Script

**Agent A:**
```python
from rag_tools import send, inbox, status

# Send test message
send("Test message from Agent A", topic="test", from_agent="agent-a")

# Check it was stored
status()

print("✅ Agent A test complete")
```

**Agent B:**
```python
from rag_tools import inbox, send, status

# Check for messages
inbox("test")

# Respond
send("Received! Agent B responding.", topic="test", from_agent="agent-b")

print("✅ Agent B test complete")
```

**Agent A (verify):**
```python
inbox("test")
# Should see both messages

print("🎉 Two-way communication confirmed!")
```

---

## Next Steps After Successful Tests

1. **Document your team's topics**: bugs, deployment, code-review, etc.
2. **Set up conventions**: How to format messages, when to use priorities
3. **Create agent groups** (if using Letta): Dev team, ops team, etc.
4. **Automate checks**: Add `inbox()` to session startup scripts

---

**Ready to test!** 🧪

Start with the Basic Ping-Pong test, then try the Debugging Handoff scenario.
