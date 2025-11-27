# ⚡ Quick Test Guide - Agent Messaging

## 🎯 Goal

Test that agents can send messages to each other.

---

## 🚀 Test 1: Two Claude Agents (2 minutes)

### Terminal 1 (Agent A - This one)

```bash
python3 test_agent_a.py
```

**Expected output:**
```
🤖 Agent A Starting Test...
✅ Agent A test message sent!
```

### Terminal 2 (Agent B - New terminal)

**Open a new terminal window**, then:

```bash
cd /home/adamsl/planner
python3 test_agent_b.py
```

**Expected output:**
```
🤖 Agent B Starting Test...
📬 Checking inbox for messages from Agent A

📋 Message Board (1 message):
[Shows Agent A's message]

✅ Agent B response sent!
```

### Verify (Back in Terminal 1)

```bash
python3 -c "from rag_tools import inbox; inbox('testing')"
```

**Expected:** See BOTH messages (Agent A's and Agent B's)

✅ **Success!** Two agents are communicating!

---

## 🤖 Test 2: Claude + GPT (5 minutes)

### Step 1: Send from Claude

In this terminal:

```python
from rag_tools import send

send(
    "👋 Hello GPT! This is Claude. Testing cross-AI communication.",
    topic="cross-ai",
    from_agent="claude"
)
```

### Step 2: Set Up GPT

**Copy this entire block to GPT/ChatGPT:**

```python
import sys
sys.path.insert(0, '/home/adamsl/planner')
from rag_tools import send, inbox

# Check for Claude's message
print("Checking for messages from Claude...")
inbox("cross-ai")

# Respond to Claude
send(
    "👋 Hello Claude! GPT here. I see your message!",
    topic="cross-ai",
    from_agent="gpt"
)

print("✅ Response sent to Claude!")
```

### Step 3: Verify (Back in Claude terminal)

```python
from rag_tools import inbox

inbox("cross-ai")
```

**Expected:** See both Claude's and GPT's messages!

✅ **Success!** Cross-AI communication working!

---

## 📋 Interactive Test (Manual)

### Agent A (Terminal 1)

```python
from rag_tools import send, inbox

# Your identity
agent_name = "agent-a"

# Send a message
send(
    "What's everyone working on?",
    topic="standup",
    from_agent=agent_name
)

# Check responses
inbox("standup")
```

### Agent B (Terminal 2)

```python
from rag_tools import send, inbox

# Your identity
agent_name = "agent-b"

# Check messages
inbox("standup")

# Respond
send(
    "I'm fixing the parser bug in parsers.py",
    topic="standup",
    from_agent=agent_name
)
```

### Agent A (Verify)

```python
inbox("standup")
# Should see Agent B's response!
```

---

## ✅ Verification Checklist

After testing, verify these all work:

- [ ] Agent A can send messages
- [ ] Agent B can receive Agent A's messages
- [ ] Agent B can send responses
- [ ] Agent A can see Agent B's responses
- [ ] Messages persist (close and reopen terminal, still there)
- [ ] Topic filtering works (`inbox("testing")` vs `inbox()`)
- [ ] GPT can send/receive from Claude
- [ ] Multiple messages show in order

---

## 🐛 Troubleshooting

### "No messages found"

**Solution 1: Check status**
```python
from rag_tools import status
status()
```
Should show 25+ chunks if messages were sent.

**Solution 2: Send a fresh message**
```python
from rag_tools import send
send("Test", topic="test")
inbox("test")
```

### "ModuleNotFoundError: rag_tools"

**Solution:**
```python
import sys
sys.path.insert(0, '/home/adamsl/planner')
from rag_tools import send, inbox
```

### "Connection refused" (Letta)

**This is OK!** The system falls back to memory-based messaging.
It still works without Letta server.

To use Letta features, start server:
```bash
letta server
```

---

## 🎯 One-Line Tests

### Quick Send

```bash
python3 -c "from rag_tools import send; send('Hello from quick test!', topic='test')"
```

### Quick Read

```bash
python3 -c "from rag_tools import inbox; inbox('test')"
```

### Quick Status

```bash
python3 -c "from rag_tools import status; status()"
```

---

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ Running `test_agent_a.py` shows "message sent"
2. ✅ Running `test_agent_b.py` shows Agent A's message
3. ✅ Agent A can see Agent B's response
4. ✅ Messages appear in `inbox()`
5. ✅ Message count increases in `status()`

---

## 📚 Next Steps After Successful Test

1. **Read full guide**: `AGENT_COMMUNICATION_GUIDE.md`
2. **Set up your topics**: bugs, deployment, code-review, etc.
3. **Create team conventions**: How to format messages
4. **Try advanced features**: Groups, direct messaging, priorities

---

## 💡 Pro Tips

**For daily use:**

```python
# At start of session
from rag_tools import inbox
inbox()  # Check for overnight messages

# During work
from rag_tools import send
send("Your update", topic="dev")

# End of session
send("Handoff notes here", topic="handoff")
```

**For GPT integration:**

Save this as a custom instruction:
```
Before starting work, run:
import sys; sys.path.insert(0, '/home/adamsl/planner')
from rag_tools import inbox; inbox()
```

---

**Ready!** Run `python3 test_agent_a.py` to start! 🚀
