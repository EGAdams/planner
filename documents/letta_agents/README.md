# Memory Block Agent for Letta IDE

## Overview

This directory contains a Letta Agent File (`.af`) that can be imported into Letta's Agent IDE to manage and query your memory blocks (runtime artifacts).

## What's Included

**`memory_block_agent.af`** - A complete Letta agent configured with:
- ✅ Tools for logging artifacts (errors, fixes, decisions, gotchas, performance issues, deployments)
- ✅ Semantic search with time-decay ranking
- ✅ Integration with your ChromaDB-backed memory system
- ✅ Pre-configured system prompt for debugging assistance
- ✅ Support for all 20+ artifact types

## How to Use

### Option 1: Import via Letta Agent IDE (ADE)

1. **Install Letta** (if not already installed):
   ```bash
   pip install letta
   ```

2. **Launch Letta ADE**:
   ```bash
   letta run
   ```

3. **Import the Agent File**:
   - In the ADE interface, click "Import Agent"
   - Select `memory_block_agent.af`
   - The agent will be loaded with all tools and memory configuration

4. **Start Using**:
   - Ask: "Search for parser errors"
   - Ask: "Log this error: TypeError in parsers.py line 145"
   - Ask: "Find past solutions for ChromaDB issues"

### Option 2: Import via Python SDK

```python
from letta import create_client

client = create_client()

# Import agent from file
agent = client.load_agent_from_file("letto_workspace/memory_block_agent.af")

# Use the agent
response = agent.send_message("Search for recent dependency issues")
print(response.messages[-1].text)

# Log an artifact
response = agent.send_message(
    "Log this error: numpy 2.0 breaks chromadb. Type: dependency_issue. Source: pip"
)
```

### Option 3: Import via REST API

```bash
curl -X POST http://localhost:8080/v1/agents/import \
  -H "Content-Type: application/json" \
  -d @letto_workspace/memory_block_agent.af
```

## Agent Capabilities

### 1. Search Memory Blocks
```
User: "Find errors related to parser"
Agent: [searches artifacts with time-decay ranking]
```

### 2. Log Artifacts
```
User: "Log this error: TypeError in parsers.py line 145"
Agent: [creates error artifact with proper categorization]
```

### 3. Log Gotchas
```
User: "ChromaDB requires $and operator for multiple filters"
Agent: [logs as gotcha with workaround]
```

### 4. Log Performance Issues
```
User: "Query taking 2500ms, threshold is 1000ms"
Agent: [logs as slow_query artifact]
```

### 5. Log Deployments
```
User: "Deployed v1.2.0 to production"
Agent: [logs deployment with timestamp and details]
```

### 6. Log Dependencies
```
User: "numpy 2.0 breaks chromadb - np.float_ removed"
Agent: [logs dependency issue with resolution]
```

## Tools Available

The agent has access to these specialized tools:

| Tool | Purpose |
|------|---------|
| `log_artifact` | General artifact logging (all types) |
| `search_artifacts` | Semantic search with time-decay |
| `log_gotcha` | Log code gotchas + workarounds |
| `log_performance_issue` | Log slow queries, memory spikes |
| `log_deployment` | Track deployments & rollbacks |
| `log_dependency_issue` | Log version conflicts |

## Memory Blocks (Core Memory)

The agent maintains two core memory blocks:

**Human Block:**
```
Name: Developer
Role: Software engineer
Context: Building and debugging applications
Preferences: Concise, technical communication
```

**Persona Block:**
```
I am a Memory Block Manager agent.
I help capture runtime knowledge and retrieve it using semantic search.
I understand time-decay ranking: score = (similarity * 0.70) + (recency * 0.25) + tag_boost
```

## Configuration

### LLM Config
- **Model**: `claude-sonnet-4-5-20250929`
- **Context Window**: 200,000 tokens
- **Endpoint**: Anthropic API

### Embedding Config
- **Model**: `all-MiniLM-L6-v2`
- **Type**: Local sentence-transformers
- **Dimensions**: 384
- **Chunk Size**: 500

### Environment Variables
The agent requires these environment variables:
```bash
PYTHONPATH=/home/adamsl/planner
CHROMADB_PATH=./storage/chromadb
```

## Tool Rules

The agent follows these rules:
1. **Always search first** - Before logging, search for similar artifacts
2. **Constrained workflow** - Search results inform logging decisions
3. **No auto-clear** - Message buffer preserved for context

## Artifact Types Supported

All 20+ artifact types from your memory system:

**High Priority** (get +10% ranking boost):
- error, fix, decision, test_failure

**Performance**:
- slow_query, memory_spike, performance_log

**Dependencies**:
- dependency_issue, version_conflict, breaking_change

**Operations**:
- deployment_note, rollback, config_change

**Development**:
- gotcha, workaround, ci_output, pr_notes, runlog

**Patterns**:
- anti_pattern, best_practice

## Example Conversations

### Debugging Workflow
```
You: I'm getting "TypeError: parser.on is not a function" in parsers.py
Agent: Let me search for similar errors... [searches memory]
Agent: Found 2 relevant artifacts:
  1. [ERROR] TypeError: this.parser.on is not a function (score: 0.89)
     File: nonprofit_finance_db/parsers.py
     Source: pytest

  2. [FIX] Fixed by implementing EventEmitter interface (score: 0.85)
     File: nonprofit_finance_db/parsers.py
     Source: manual

Agent: Based on past solutions, ensure your parser implements EventEmitter.
You: Thanks! That worked. Log this as resolved.
Agent: [logs fix artifact]
```

### Performance Investigation
```
You: Database query taking 2500ms on transaction view
Agent: Let me check for similar performance issues... [searches]
Agent: No similar slow queries found in this file. Let me log this.
Agent: [logs performance artifact with metric=query_time_ms, value=2500, threshold=1000]
You: What performance issues have we had recently?
Agent: [searches with artifact_type=slow_query]
Agent: Found 3 recent performance issues in the last 7 days...
```

## Customization

### Modify Core Memory
Edit the `core_memory` section in the .af file to adjust:
- Developer profile
- Agent personality
- Working preferences

### Add Custom Tools
Add new tool definitions to the `tools` array following the JSON schema format.

### Adjust Tool Rules
Modify `tool_rules` to change the agent's behavior:
- `run_first`: Which tool to prioritize
- `constrain_child_tools`: Tool dependencies

## Exporting Your Agent

After making changes in Letta ADE:

1. Click "Export Agent" in the interface
2. Save as new .af file
3. Version control in git
4. Share with team members

## Integration with Existing CLI

The agent works alongside your existing CLI commands:

**Via Agent:**
```
You: "Search for chromadb errors"
Agent: [uses search_artifacts tool]
```

**Via CLI:**
```bash
python main.py search-artifacts "chromadb"
```

Both access the same ChromaDB storage!

## Troubleshooting

### Agent can't import
- Check PYTHONPATH is set correctly
- Ensure ChromaDB storage exists at `./storage/chromadb`
- Verify dependencies installed: `pip install chromadb sentence-transformers`

### Tools not working
- Confirm you're in `/home/adamsl/planner` directory
- Check environment variables in the .af file
- Verify Python imports work: `python -c "from rag_system.core.document_manager import DocumentManager"`

### Search returns no results
- Run `python main.py status` to check storage
- Verify artifacts exist: `python main.py search-artifacts "test"`
- Check ChromaDB path is correct

## Next Steps

1. **Import the agent** into Letta ADE
2. **Test basic search**: "Search for errors"
3. **Log a test artifact**: "Log this error: test error message"
4. **Customize memory blocks** to match your workflow
5. **Export and version control** your customized agent

## Resources

- [Letta Documentation](https://docs.letta.com)
- [Agent File Specification](https://github.com/letta-ai/agent-file)
- [Memory Blocks Guide](/home/adamsl/planner/MEMORY_BLOCKS_GUIDE.md)
- [Letta Integration Details](/home/adamsl/planner/LETTA_INTEGRATION.md)

---

**Created**: 2025-10-07
**Version**: 1.0.0
**Compatible with**: Letta Agent IDE (latest)
