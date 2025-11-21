# 🤖 Claude Agent Memory Integration

## For: Claude AI Agents Working on This Project

This document explains how to use the RAG memory system during your work sessions.

---

## 🎯 Why Use This?

As an AI agent, you should use this memory system to:
- **Remember** fixes and solutions you discover
- **Recall** past issues and their resolutions
- **Build context** across multiple conversation sessions
- **Track** project decisions and technical debt
- **Share knowledge** with future agents working on this codebase

**Think of it as your persistent brain!**

---

## 🚀 Quick Start for Agents

### During Any Work Session

1. **At the start of a session** - Check what's already known:
```python
from rag_tools import recall, memory_stats

# Check what we know about the current issue
results = recall("authentication errors")
results = recall("parser bugs")

# Or check overall stats
memory_stats()
```

2. **When you fix something** - Remember it:
```python
from rag_tools import log_fix, remember

log_fix(
    "Typer v0.9.0 has CLI bug with TyperArgument.make_metavar()",
    "Upgrade to v0.16.1: pip3 install 'typer>=0.12.5,<0.17.0'",
    file_path="main.py",
    project="planner"
)
```

3. **When you encounter an error** - Log it:
```python
from rag_tools import log_error

log_error(
    "ImportError: cannot import name 'cached_download' from 'huggingface_hub'",
    "main.py:15",
    project="planner"
)
```

4. **When you make a decision** - Document it:
```python
from rag_tools import log_decision

log_decision(
    "Using ChromaDB instead of Pinecone",
    "Need local-first solution, no external dependencies, fast semantic search",
    project="planner"
)
```

---

## 📋 Common Agent Workflows

### Workflow 1: Debugging an Error

```python
from rag_tools import recall, log_error, log_fix

# Step 1: Check if we've seen this before
past_issues = recall("ImportError cached_download")

# Step 2: If it's new, log the error
if not past_issues:
    log_error(
        "ImportError: cannot import cached_download",
        "main.py:15",
        project="planner"
    )

# Step 3: After fixing, log the solution
log_fix(
    "sentence-transformers v2.2.2 incompatible with huggingface_hub",
    "Upgrade to v5.1.1: pip3 install --upgrade sentence-transformers",
    project="planner"
)
```

### Workflow 2: Starting Work on a Project

```python
from rag_tools import project_status, recall

# Get full project context
project_status("planner")

# Check for specific concerns
recall("known bugs", limit=5)
recall("TODO items", limit=5)
recall("performance issues", limit=3)
```

### Workflow 3: Client Work

```python
from rag_tools import client_info, remember, recall

# Get client context
client_info("Acme Corp")

# Check past conversations
recall("Acme Corp requirements")

# Remember new info from this session
remember(
    "Client confirmed they want dark mode by Friday. Willing to pay extra for expedited delivery.",
    "Dark mode deadline confirmed",
    client="Acme Corp",
    project="website-redesign",
    priority="high"
)
```

### Workflow 4: Post-Session Summary

At the end of your session, save a summary:

```python
from rag_tools import remember

remember(
    """
    Session Summary:
    - Fixed sentence-transformers compatibility issue (v2.2.2 -> v5.1.1)
    - Upgraded typer (0.9.0 -> 0.16.1) and pydantic (2.5.0 -> 2.12.0)
    - Created RAG tools wrapper for easy access
    - Tested all integrations successfully

    Next steps:
    - Monitor for any new dependency conflicts
    - Consider adding automated memory logging
    """,
    "Work Session: Package Upgrades & RAG Integration",
    project="planner"
)
```

---

## 🎓 Best Practices for Agents

### DO:
✅ Log every significant bug you fix
✅ Remember workarounds and gotchas
✅ Check memory BEFORE starting work on an issue
✅ Add context (project, client, file_path) to memories
✅ Use descriptive titles - you'll search for them later
✅ Log decisions with rationale

### DON'T:
❌ Log trivial information (like "ran ls command")
❌ Duplicate memories - search first!
❌ Use vague titles like "bug fix" or "issue"
❌ Forget to add project/client context
❌ Skip logging just because it's "obvious"

---

## 🔧 Integration Methods

### Method 1: Python Import (Recommended)
```python
from rag_tools import remember, recall, log_error, log_fix, log_decision

# Use directly in any Python script
```

### Method 2: Shell Commands
```bash
# In Bash tool calls
bash -c "source /home/adamsl/planner/rag_aliases.sh && mem-search 'query'"
```

### Method 3: Direct CLI
```bash
python3 /home/adamsl/planner/main.py search "query"
python3 /home/adamsl/planner/main.py recent --limit 10
python3 /home/adamsl/planner/main.py status
```

### Method 4: Direct Python (No Import)
```bash
python3 -c "
from rag_tools import recall
results = recall('authentication')
"
```

---

## 🧠 Memory Retrieval Strategies

### Semantic Search
The system uses semantic embeddings, so search by **meaning**, not exact words:

```python
# These all work:
recall("login problems")
recall("authentication failures")
recall("users can't sign in")
recall("credential errors")
```

### Time-Aware Search
Recent memories are weighted higher. Use this to your advantage:

```python
# Get recent work
recall("bug fixes", limit=10)  # Recent fixes first

# Get all-time knowledge
recall("architecture decisions", limit=20)
```

### Context Filtering
Use parameters to narrow down:

```python
from rag_tools import get_context

# Get project-specific context
context = get_context("database issues", project="planner")

# Get client-specific context
context = get_context("requirements", client="Acme Corp")
```

---

## 📊 Monitoring Memory Health

Check memory stats regularly:

```python
from rag_tools import memory_stats

stats = memory_stats()
# Shows: total memories, clients, projects, document types
```

**Good memory health:**
- Total chunks: 50-1000 (not too sparse, not too dense)
- Document types: Balanced mix of artifacts, notes, decisions
- Clients/Projects: Properly tagged

**Warning signs:**
- Too few memories (< 10): System isn't being used
- Too many memories (> 5000): Consider archiving old data
- No client/project tags: Memories not properly categorized

---

## 🎬 Example: Full Session Integration

```python
#!/usr/bin/env python3
"""
Example: How an agent should use memory throughout a session
"""
from rag_tools import *

# === START OF SESSION ===

print("Starting work session...")

# 1. Check system status
memory_stats()

# 2. Get project context
project_status("planner")

# 3. Check for known issues related to current task
known_issues = recall("CLI bugs", limit=3)
if known_issues:
    print("Found relevant past issues:")
    for issue in known_issues:
        print(f"  - {issue.metadata['title']}")

# === DURING WORK ===

# 4. Log error when encountered
try:
    # ... some code that fails ...
    raise TypeError("TyperArgument.make_metavar() error")
except Exception as e:
    log_error(str(e), "main.py:456", project="planner")

# 5. After investigation, log the fix
log_fix(
    "Typer v0.9.0 incompatible with current Python",
    "Upgrade to v0.16.1",
    project="planner"
)

# === END OF SESSION ===

# 6. Save session summary
remember(
    "Fixed Typer CLI compatibility issue. System now working correctly.",
    "Session: Typer CLI Fix",
    project="planner"
)

print("Session complete! Memories saved.")
```

---

## 🚨 When Things Go Wrong

### Memory not persisting?
```python
# Check storage path
stats = memory_stats()
print(stats['storage_path'])
# Should be: storage/chromadb
```

### Search returns nothing?
```python
# Check if memory exists
stats = memory_stats()
if stats['total_chunks'] == 0:
    print("No memories yet! Start remembering things.")
```

### Import errors?
```bash
# Make sure you're in the right directory
cd /home/adamsl/planner

# Or set PYTHONPATH
export PYTHONPATH=/home/adamsl/planner:$PYTHONPATH
```

---

## 💪 Power User Tips

### 1. Batch Operations
```python
from rag_tools import remember

# Save multiple related memories at once
memories = [
    ("Bug in parser", "Parser returns None on empty input"),
    ("Fix applied", "Added null check in parser.py:142"),
    ("Test added", "Added test_empty_input() in test_parser.py")
]

for title, content in memories:
    remember(content, title, project="planner")
```

### 2. Context for AI Conversations
```python
from rag_tools import get_context

# Get context to feed to Claude for better answers
context = get_context("What authentication issues have we seen?")
print(context)
# Now use this context in your prompt to Claude!
```

### 3. Memory-Driven Development
```python
# Before starting ANY task, check memory
results = recall("task_name similar_keywords")

# This prevents:
# - Re-solving solved problems
# - Making same mistakes twice
# - Forgetting important gotchas
```

---

## 🎉 Ready to Go!

You now have:
- ✅ Persistent memory across sessions
- ✅ Semantic search capabilities
- ✅ Client/project context management
- ✅ Error and fix tracking
- ✅ Decision documentation

**Remember**: The more you use it, the smarter the system becomes!

---

## 📚 Additional Resources

- **Quick Reference**: See `RAG_QUICKSTART.md`
- **Full CLI Docs**: Run `python3 main.py --help`
- **Python Tools**: See `rag_tools.py` for all available functions

**Happy remembering! 🧠✨**
