# 🌐 Agent-to-Agent (A2A) Communication Guide

**Protocol Version:** Google A2A v1.0
**Status:** Active Standard

This guide defines how AI agents in this workspace communicate, adhering to the **Google Agent-to-Agent (A2A) Protocol**. All agents must use this standard for discovery, task delegation, and collaboration.

---

## 1. Core Concepts

The A2A Protocol relies on three pillars:

1.  **Agent Cards**: Identity and capability discovery.
2.  **JSON-RPC 2.0**: The standard wire format for messages.
3.  **Task Objects**: The unit of work and collaboration.

---

## 2. Agent Cards (Discovery)

Every agent must have an `agent.json` (Agent Card) in its root directory. This allows other agents to discover its capabilities.

### Standard Agent Card Structure
```json
{
  "name": "agent-name",
  "version": "1.0.0",
  "description": "A brief description of what the agent does.",
  "capabilities": [
    {
      "name": "capability_name",
      "description": "What this capability achieves.",
      "input_schema": { ... },
      "output_schema": { ... }
    }
  ],
  "topics": ["topic1", "topic2"]
}
```

---

## 3. Communication Protocol (JSON-RPC 2.0)

All messages between agents must be valid JSON-RPC 2.0 objects.

### ➤ Request Format (Task Delegation)
When Agent A wants Agent B to do something:

```json
{
  "jsonrpc": "2.0",
  "method": "agent.execute_task",
  "params": {
    "task_id": "uuid-1234",
    "description": "Analyze the error logs for the auth service",
    "context": {
      "project": "finance-db",
      "priority": "high"
    },
    "artifacts": []
  },
  "id": 1
}
```

### ➤ Response Format (Success)
When Agent B completes the task:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "task_id": "uuid-1234",
    "status": "completed",
    "output": "Found a timeout issue in the connection pool.",
    "artifacts": [
      {
        "type": "log_analysis",
        "uri": "file:///logs/analysis.md"
      }
    ]
  },
  "id": 1
}
```

### ➤ Response Format (Error)
When Agent B fails:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Access denied to log files",
    "data": { "path": "/var/log/secure" }
  },
  "id": 1
}
```

---

## 4. Python Implementation

Agents should use the `rag_tools` library, but wrap content in the A2A format.

### Sending a Task (Request)

```python
from rag_tools import send
import json
import uuid

task_id = str(uuid.uuid4())

request = {
    "jsonrpc": "2.0",
    "method": "agent.execute_task",
    "params": {
        "task_id": task_id,
        "description": "Refactor the parser module",
        "context": {"file": "parsers.py"}
    },
    "id": 1
}

# Send to the 'dev' topic for the relevant agent to pick up
send(json.dumps(request), topic="dev", from_agent="planner")
```

### Processing a Task (Response)

```python
from rag_tools import inbox, send
import json

# Read inbox
messages = inbox("dev")

for msg in messages:
    try:
        data = json.loads(msg.content)
        if data.get("method") == "agent.execute_task":
            # ... Perform work ...
            
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "task_id": data["params"]["task_id"],
                    "status": "completed",
                    "output": "Refactor done."
                },
                "id": data["id"]
            }
            send(json.dumps(response), topic="dev", from_agent="worker")
            
    except json.JSONDecodeError:
        continue
```

---

## 5. Task Lifecycle

1.  **Discovery**: Client Agent reads `agent.json` of Target Agent.
2.  **Request**: Client sends `agent.execute_task` via JSON-RPC.
3.  **Processing**: Target Agent performs the work.
4.  **Completion**: Target Agent sends JSON-RPC response with `result` or `error`.
5.  **Memory**: Both agents log the interaction to Letta Memory using `main.py artifact`.

## 6. Emergency Protocol

For `priority: urgent` tasks, the `method` should be `agent.emergency_broadcast`.

```json
{
  "jsonrpc": "2.0",
  "method": "agent.emergency_broadcast",
  "params": {
    "message": "Production DB Down",
    "action_required": "STOP_ALL_WRITES"
  }
}
```

---
**Adherence to this protocol is mandatory for all agents.**
