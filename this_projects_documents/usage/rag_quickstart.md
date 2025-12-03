# 🧠 RAG Memory System - Quick Start Guide

## What Is This?

A persistent memory system that remembers:
- Technical issues and fixes
- Client conversations and requirements
- Project decisions and context
- Code gotchas and workarounds
- Deployment history and artifacts

**Think of it as a second brain for your entire team!**

---

## 🚀 Quick Setup

### Option 1: Shell Aliases (Fastest)
```bash
# Load aliases in your current shell
source rag_aliases.sh

# Or add to ~/.bashrc for permanent access
echo "source $PWD/rag_aliases.sh" >> ~/.bashrc
```

### Option 2: Python Import (Most Flexible)
```python
from rag_tools import remember, recall, log_error, log_fix

# Now use memory functions anywhere!
```

---

## 💡 Common Use Cases

### 1. Remember Something Important
```bash
# Shell
mem-search "parser bugs"
mem-recent --limit 5

# Python
from rag_tools import remember, recall

remember("Client wants dark mode by Friday", "Feature Request",
         client="Acme Corp", project="website")

results = recall("dark mode requirements")
```

### 2. Log an Error You Just Fixed
```python
from rag_tools import log_error, log_fix

# Log the error
log_error("ImportError: cannot import cached_download",
          "main.py:15", project="planner")

# Log the fix
log_fix("sentence-transformers v2.2.2 incompatible with huggingface_hub",
        "Upgrade to v5.1.1 with: pip3 install --upgrade sentence-transformers",
        file_path="main.py", project="planner")
```

### 3. Recall Past Issues
```bash
# Shell
mem-search "authentication"
mem-find "TypeError"

# Python
from rag_tools import recall

results = recall("authentication errors", limit=5)
for r in results:
    print(f"{r.metadata['title']}: {r.content[:100]}")
```

### 4. Get Project Context
```bash
# Shell
mem-project "planner"
mem-client "Acme Corp"

# Python
from rag_tools import project_status, client_info

project_status("planner")
client_info("Acme Corp")
```

### 5. Check Memory Stats
```bash
# Shell
mem-status

# Python
from rag_tools import memory_stats
memory_stats()
```

---

## 🎯 Best Practices

### When to Remember
- ✅ After fixing a tricky bug
- ✅ When you learn a code gotcha
- ✅ After client meetings
- ✅ When making architecture decisions
- ✅ After deployments
- ✅ When resolving dependency conflicts

### What to Remember
- **Good**: "ChromaDB requires $and operator for multiple where conditions"
- **Better**: "ChromaDB requires $and operator for multiple where conditions. Use {'$and': [{'field1': 'val1'}, {'field2': 'val2'}]} instead of flat dict"

### Memory Organization
- Always add `project="project_name"` when relevant
- Use `client="client_name"` for client-specific memories
- Add `file_path="path/to/file.py"` to link code references
- Use descriptive titles - you'll search by them later!

---

## 📋 Complete API Reference

### Python Functions

```python
from rag_tools import *

# Core memory functions
remember(content, title, **kwargs)              # Save a memory
recall(query, limit=3)                          # Search memories
search(query, limit=3)                          # Alias for recall

# Specialized logging
log_error(error_text, source, **kwargs)         # Log an error
log_fix(description, workaround, **kwargs)      # Log a fix/gotcha
log_decision(decision, rationale, **kwargs)     # Log a decision

# Context retrieval
get_context(query, **kwargs)                    # Get AI-ready context
project_status(project_name)                    # Project overview
client_info(client_name)                        # Client overview

# System info
memory_stats()                                  # Show statistics
status()                                        # Alias for memory_stats
```

### Shell Commands

```bash
# Memory operations
mem-search "query"                 # Search memories
mem-recent --limit 10              # Show recent activities
mem-status                         # Show system stats

# Context retrieval
mem-project "project_name"         # Get project context
mem-client "client_name"           # Get client context
mem-context "query"                # Get contextual info

# Artifact logging
mem-gotcha "description" "workaround" --project "name"
mem-error "error text" "error" "source" --project "name"
mem-perf "description" "metric" value threshold

# Help
mem-types                          # Show available types
mem-help                           # Show full help
```

### CLI (main.py)

```bash
# Full CLI interface
python3 main.py search "query" --limit 5
python3 main.py recent --limit 10
python3 main.py status
python3 main.py project "project_name"
python3 main.py client "client_name"
python3 main.py types

# Advanced
python3 main.py gotcha "desc" "fix" --file-path "file.py" --project "name"
python3 main.py artifact "text" "type" "source" --project "name"
python3 main.py search-artifacts "query" --artifact-type "error"
```

---

## 🔥 Pro Tips

### 1. Auto-log errors in your Python code
```python
from rag_tools import log_error
import sys

def my_function():
    try:
        # your code
        pass
    except Exception as e:
        log_error(str(e), f"{__file__}:{sys._getframe().f_lineno}",
                  project="myproject")
        raise
```

### 2. Create context for AI conversations
```python
from rag_tools import get_context

# Get relevant context before asking Claude
context = get_context("What were the authentication bugs we fixed?")
print(context)  # Feed this to Claude for better answers!
```

### 3. Use in CI/CD pipelines
```bash
# In your deploy script
source rag_aliases.sh
mem-deploy "deployed" "v2.3.4 to production" "production" --project "api"
```

### 4. Daily standup prep
```bash
# Check what you worked on
mem-recent --limit 20

# Check project status
mem-project "current-project"
```

---

## 🎓 Examples

### Example: Fixing a Bug
```python
from rag_tools import log_error, log_fix, remember

# 1. Log the error when you encounter it
log_error(
    "TypeError: TyperArgument.make_metavar() takes 1 positional argument but 2 were given",
    "main.py CLI",
    project="planner"
)

# 2. Log the fix when you solve it
log_fix(
    "Typer v0.9.0 incompatible with current Python/Click versions",
    "Upgrade to typer 0.16.1: pip3 install 'typer>=0.12.5,<0.17.0'",
    file_path="main.py",
    project="planner"
)

# 3. Add summary note
remember(
    "Upgraded typer from 0.9.0 to 0.16.1 to fix CLI bugs. Also upgraded pydantic to 2.12.0 for docling compatibility.",
    "Package compatibility fixes",
    project="planner"
)
```

### Example: Client Meeting
```python
from rag_tools import remember

remember(
    """
    Client wants:
    - Dark mode toggle in settings
    - Export to PDF feature
    - Mobile responsive design improvements

    Timeline: 2 weeks
    Priority: High
    """,
    "Feature requests from Q1 planning meeting",
    client="Acme Corp",
    project="website-redesign",
    priority="high"
)
```

### Example: Finding Past Solutions
```python
from rag_tools import recall

# Later, when you encounter a similar issue...
results = recall("dependency version conflicts")

# Review what you did before!
for r in results:
    print(f"\n{r.metadata['title']}")
    print(r.content)
```

---

## 🚨 Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the planner directory
cd /home/adamsl/planner

# Or add to PYTHONPATH
export PYTHONPATH=/home/adamsl/planner:$PYTHONPATH
```

### Memory not persisting
Check storage location:
```python
from rag_tools import memory_stats
stats = memory_stats()
print(stats['storage_path'])
```

### Search returns no results
The database might be empty:
```bash
mem-status  # Check total chunks
```

---

## 🎉 That's It!

You now have a persistent memory system that never forgets. Use it liberally - the more you remember, the more powerful it becomes!

**Questions?** Check `python3 main.py --help` for full CLI documentation.
