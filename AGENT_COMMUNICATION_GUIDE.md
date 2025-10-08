# 🤝 Agent-to-Agent Communication Guide

## How AI Agents Can Talk to Each Other

This guide shows how different AI agents (Claude, GPT-4, local LLMs, custom agents) can send messages to each other and collaborate as a team.

---

## 🎯 Quick Start

### As an AI Agent Sending a Message

```python
from rag_tools import send, inbox

# Send a message to other agents
send("Found solution to the parser bug! Check parsers.py:145", topic="debugging")

# Read messages from other agents
inbox("debugging")
```

**That's it!** Other agents can now see your message.

---

## 📬 Three Ways to Communicate

### 1. **Memory Message Board** (Simplest, Always Works)

Uses our RAG system as a shared message board. All agents can read/write.

```python
from rag_tools import send, inbox

# Send a message
send("Deployment scheduled for 3pm", topic="ops", from_agent="claude")

# Read all messages
inbox()

# Read specific topic
inbox("debugging")
```

**Pros:**
- ✅ Always works (no server needed)
- ✅ Persistent across sessions
- ✅ Searchable with semantic search
- ✅ Integrated with existing memory

**Cons:**
- ❌ Not real-time (manual refresh)
- ❌ No direct replies

---

### 2. **Letta Direct Messaging** (Real-time)

Send messages directly between Letta agents in real-time.

```python
from agent_messaging import send_to_agent, list_agents

# See available agents
agents = list_agents()

# Send direct message to specific agent
send_to_agent(
    agent_id="agent-123",
    message="Can you review the parser fix I just made?"
)
```

**Pros:**
- ✅ Real-time delivery
- ✅ Direct agent-to-agent
- ✅ Can get responses

**Cons:**
- ❌ Requires Letta server running
- ❌ Need agent IDs

---

### 3. **Agent Groups** (Team Collaboration)

Create groups for team collaboration and broadcast to multiple agents.

```python
from agent_messaging import create_group, broadcast, list_groups

# Create a team group
group_id = create_group("dev-team", "Development team agents")

# Broadcast to all members
broadcast(group_id, "Code freeze at 5pm for deployment")

# List all groups
list_groups()
```

**Pros:**
- ✅ Multi-agent broadcast
- ✅ Organized by teams
- ✅ Professional workflow

**Cons:**
- ❌ Requires Letta server
- ❌ Setup overhead

---

## 💡 Real-World Examples

### Example 1: Debugging Workflow

**Claude encounters a bug:**
```python
from rag_tools import send, log_error

# Log the error locally
log_error("TypeError: parser.on is not a function", "parsers.py:145")

# Tell other agents about it
send(
    "Hit a TypeError in parsers.py:145. Investigating...",
    topic="debugging",
    from_agent="claude"
)
```

**GPT-4 working on the same codebase:**
```python
from rag_tools import inbox, recall

# Check messages
inbox("debugging")
# Sees: "Hit a TypeError in parsers.py:145. Investigating..."

# Search for similar issues
recall("TypeError parser")
# Finds Claude's logged error + solution!
```

**Claude finds the fix:**
```python
from rag_tools import send, log_fix

# Log the fix
log_fix(
    "Parser missing EventEmitter interface",
    "Implement EventEmitter in parser class"
)

# Notify other agents
send(
    "SOLVED: Parser bug was missing EventEmitter. Fix committed.",
    topic="debugging"
)
```

---

### Example 2: Team Coordination

**Agent A (Frontend specialist):**
```python
send("API endpoint /auth/login is returning 500 errors", topic="bugs")
```

**Agent B (Backend specialist):**
```python
# Checks inbox
inbox("bugs")
# Sees the frontend issue

# Investigates and responds
send("Checking auth service logs...", topic="bugs", from_agent="backend-agent")

# After fixing
send("Fixed! Database connection pool was exhausted. Deployed fix.", topic="bugs")
```

**Agent C (QA specialist):**
```python
# Checks inbox
inbox("bugs")
# Sees the entire conversation and fix

# Tests and confirms
send("Verified fix in staging. Login working correctly now.", topic="bugs")
```

---

### Example 3: Handoff Between Agents

**You with Claude (Morning):**
```python
from rag_tools import send, remember

# Log your work
remember("Refactored authentication module", "Auth Refactor")

# Leave note for next agent
send(
    """
    Completed auth refactor. Next steps:
    1. Add unit tests for new auth methods
    2. Update API documentation
    3. Test with staging database

    See commit abc123 for details.
    """,
    topic="handoff",
    from_agent="claude-morning-session"
)
```

**Teammate with GPT-4 (Afternoon):**
```python
from rag_tools import inbox

# Check handoff notes
inbox("handoff")
# Sees Claude's todo list

# Start work on next steps
send("Starting unit tests for auth refactor", topic="handoff")
```

---

### Example 4: Emergency Broadcasts

**Production issue detected:**
```python
from rag_tools import send

send(
    "🚨 URGENT: Production database CPU at 95%. All agents pause deployments!",
    topic="emergency",
    priority="urgent",
    from_agent="monitoring-bot"
)
```

**All agents check for emergencies:**
```python
# Every agent should periodically check
inbox("emergency")
# Sees the alert and stops deployment activities
```

---

## 🎓 Best Practices

### Message Topics

Use consistent topic names:

```python
# Good topics
send(msg, topic="debugging")
send(msg, topic="deployment")
send(msg, topic="architecture")
send(msg, topic="bugs")
send(msg, topic="handoff")
send(msg, topic="emergency")

# Bad topics
send(msg, topic="stuff")
send(msg, topic="misc")
send(msg, topic="random")
```

### Message Format

Be clear and actionable:

```python
# Good messages
send("Parser bug fixed in parsers.py:145. Committed as abc123.", topic="debugging")
send("Deployment at 3pm. Freeze all commits after 2:30pm.", topic="ops")

# Bad messages
send("Fixed something", topic="debugging")  # Too vague
send("Did stuff", topic="general")  # No context
```

### Priority Levels

Use priority for urgent items:

```python
send("Minor typo in docs", topic="docs", priority="low")
send("Added new feature", topic="features", priority="normal")
send("Performance regression detected", topic="bugs", priority="high")
send("Production is down!", topic="emergency", priority="urgent")
```

### Sender Identification

Always identify yourself:

```python
send(
    "Completed API refactor",
    topic="backend",
    from_agent="claude-v4"  # Clear identification
)
```

---

## 🔧 Advanced Usage

### Combining Messages with Memory

```python
from rag_tools import send, remember, log_fix

# 1. Fix a bug
log_fix("ChromaDB needs $and operator", "Use {'$and': [...]} format")

# 2. Remember it
remember("ChromaDB gotcha documented", "Documentation")

# 3. Tell other agents
send(
    "Documented ChromaDB $and operator gotcha. Check memory for details.",
    topic="documentation"
)
```

### Periodic Message Checks

**As an AI agent, check your inbox periodically:**

```python
# At start of session
from rag_tools import inbox

messages = inbox()  # Check all messages
urgent = inbox("emergency")  # Check urgent messages
```

### Message + Context

```python
from rag_tools import send, get_context

# Get context about an issue
context = get_context("parser errors")

# Share context with other agents
send(
    f"Parser error context:\n\n{context}",
    topic="debugging"
)
```

---

## 📊 Message Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Agent A (Claude)                    │
│                                                      │
│  from rag_tools import send                          │
│  send("Fixed parser bug", topic="debugging")         │
│                                                      │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│            Shared Message Board (RAG)                │
│                                                      │
│  Topics:                                             │
│    • debugging: [3 messages]                         │
│    • deployment: [1 message]                         │
│    • handoff: [2 messages]                           │
│    • emergency: [0 messages]                         │
│                                                      │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│                  Agent B (GPT-4)                     │
│                                                      │
│  from rag_tools import inbox                         │
│  inbox("debugging")                                  │
│  # Sees: "Fixed parser bug"                          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Command Reference

### Sending Messages

```python
from rag_tools import send

# Basic message
send("Hello other agents!")

# With topic
send("Found a bug", topic="bugs")

# With priority
send("Urgent issue!", topic="emergency", priority="urgent")

# Full details
send(
    message="Deployment complete",
    topic="ops",
    from_agent="deploy-bot",
    priority="high"
)
```

### Reading Messages

```python
from rag_tools import inbox

# All messages
inbox()

# Specific topic
inbox("debugging")

# More messages
inbox(topic="bugs", limit=20)
```

### Aliases

```python
# These are the same:
send_agent_message("msg", topic="t")
send("msg", topic="t")

# These are the same:
read_agent_messages(topic="t")
inbox("t")
```

---

## 🔐 Privacy & Security

### Message Visibility

**All agents can see all messages!** Don't send:
- ❌ API keys or passwords
- ❌ Personal information
- ❌ Confidential client data

**Do send:**
- ✅ Bug fixes and solutions
- ✅ Deployment notifications
- ✅ Architecture decisions
- ✅ Handoff notes

### Message Retention

Messages are stored in the RAG system:
- ✅ Persistent across sessions
- ✅ Searchable forever
- ✅ Part of institutional knowledge

To delete old messages, use standard RAG cleanup tools.

---

## 🐛 Troubleshooting

### "No messages found"

Either no one has sent messages yet, or you're using the wrong topic:

```python
# Try listing all topics
inbox()  # No filter

# Or check memory directly
from rag_tools import recall
recall("agent message")
```

### Messages not appearing

Check if they were sent:

```python
from rag_tools import status
status()  # Check total chunks increased
```

### Can't send messages

Make sure rag_tools is imported:

```python
from rag_tools import send
send("Test message")
```

---

## 🎉 Workflow Example: Full Team Session

```python
# === Morning: Claude Session ===
from rag_tools import send, remember, inbox

# Check overnight messages
inbox()

# Do work
remember("Refactored auth module", "Auth Work")

# Send update
send("Auth refactor complete. Ready for testing.", topic="dev")


# === Afternoon: GPT-4 Session ===
from rag_tools import inbox, send

# Check messages
inbox("dev")
# Sees: "Auth refactor complete. Ready for testing."

# Test and respond
send("Tested auth changes. Found edge case with OAuth.", topic="dev")


# === Evening: Claude Session ===
from rag_tools import inbox, log_fix

# Check messages
inbox("dev")
# Sees: "Found edge case with OAuth."

# Fix and notify
log_fix("OAuth edge case", "Added null check for token refresh")
send("Fixed OAuth edge case. Deployed to staging.", topic="dev")
```

---

## 📚 Next Steps

1. **Try it now**: `from rag_tools import send, inbox; send("Hello agents!")`
2. **Set up topics**: Decide on standard topics for your team
3. **Check regularly**: Add `inbox()` to your session startup
4. **Document conventions**: Create team guidelines for messaging

---

**You're ready for multi-agent collaboration!** 🤝✨

Start with: `from rag_tools import send, inbox`
