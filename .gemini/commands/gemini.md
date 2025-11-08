# /gemini - Collective Routing Engine

---
allowed-tools: Task(*), Read(*), Write(*), Edit(*), MultiEdit(*), Glob(*), Grep(*), Bash(*), LS(*), TodoWrite(*), WebSearch(*), WebFetch(*), mcp__task-master__*, mcp__context7__*
description: 🚀 Fast routing engine for intelligent agent selection and request delegation
---

## 🎯 Purpose - Smart Routing

**Fast Agent Selection** - analyze user requests and route to the optimal specialized agent using proven patterns and decision matrices.

## 🚀 DYNAMIC ROUTING PROTOCOL V2

The system has been upgraded to a dynamic, file-system-based routing protocol. Static routing tables and decision trees are deprecated. The new protocol enables **Progressive Disclosure**, allowing the system to adapt to new capabilities without modifying its core logic.

### 🎯 DYNAMIC CAPABILITY ANALYSIS

When a request is received, the routing engine performs the following steps:

1.  **Scan for Capabilities:** The engine scans the `/home/adamsl/planner/.gemini/agents/` and `/home/adamsl/planner/.gemini/skills/` directories to discover all available agents and skills. This provides a real-time inventory of the system's capabilities.

2.  **Analyze Capabilities:** The engine reads the content or metadata of each discovered file to understand its purpose.
    *   For **Agents** (`.md` files), it extracts the `description:` field.
    *   For **Skills** (`.sh`, `.py`, etc.), it relies on descriptive filenames and internal comments.

3.  **Match Request to Capability:** The engine analyzes the user's prompt and compares it against the descriptions of the discovered agents and skills to find the best match. This is a semantic match, not just a keyword search.

4.  **Select and Execute:**
    *   If the best match is an **Agent**, the engine delegates the task to that agent (e.g., `Task(subagent_type="feature-implementation-agent", ...)`).
    *   If the best match is a **Skill**, the engine executes the skill using the `run_shell_command` tool (e.g., `run_shell_command(command="/home/adamsl/planner/.gemini/skills/my_skill.sh")`).

### ✨ Benefits of this Approach

*   **Extensibility:** New capabilities can be added by simply creating a new agent or skill file. The system discovers and uses them automatically.
*   **Efficiency:** The system is no longer burdened with a large, static list of rules.
*   **Adaptability:** The system can learn and evolve as new skills are created by agents.

## 🎮 ORCHESTRATION PATTERNS

**Pattern 1: Direct Implementation Delegation**
```bash
# User: "build a React todo app with TypeScript"
Task(subagent_type="component-implementation-agent", 
     prompt="Build React todo app with TypeScript - use Context7 for latest React patterns, implement TDD workflow")
```

**Pattern 2: Research-Backed Development**
```bash
# User: "implement authentication with best practices"
Task(subagent_type="feature-implementation-agent",
     prompt="Implement authentication with security best practices - research latest patterns via Context7, apply TDD methodology")
```

**Pattern 3: PRD-Based Development**
```bash
# User: "create application using PRD at path/to/prd.txt"
Task(subagent_type="prd-parser-agent",
     prompt="Parse PRD document and extract structured requirements:
     - Read PRD and identify all technologies mentioned
     - Extract functional and technical requirements
     - Create structured analysis for research handoff
     - Hand off to research-agent for technology research")
```

## ⚡ ROUTING RULES

### Execution Efficiency Rules
1. **Single Agent Default**: Prefer focused agent execution over complex orchestration (90% of requests)
2. **TaskMaster Only When Needed**: Use @task-orchestrator for truly complex coordination (10% of requests)
3. **Research Integration**: Every agent incorporates Context7 research into their execution
4. **TDD Compliance**: All implementation follows Test-Driven Development patterns
5. **Quality Validation**: Mandatory gate checkpoints for production readiness

### Strategic Decision Making
1. **Agent-First Thinking**: Always consider which collective agent can handle the request most efficiently
2. **Strategic Focus**: Maintain Gemini's orchestration role above all else
3. **Research-Backed Routing**: Use Context7 patterns and TaskMaster data for informed routing
4. **TDD Integration**: Ensure all implementation flows through TDD methodology
5. **Quality Gates**: Implement mandatory validation at every handoff point

## 🎯 Gemini-Optimized Output Format

```markdown
# 🚀✨ Gemini Collective: [User's Original Request]

## 🧠 Analysis & Routing Decision
- **Intent**: [Clear category]
- **Mode**: [USER IMPLEMENTATION / RESEARCH COORDINATION]
- **Agent Selected**: @[agent-name] 
- **Routing Reason**: [Why this agent was chosen]
- **Research Integration**: [Context7 libraries / TaskMaster coordination]

## 🎯 Agent Execution Summary
**Agent**: @[agent-name]
**Task Delegated**: "[Exact task given to agent]"
**TDD Requirement**: [Yes/No + methodology]
**Research Context**: [Context7 libraries + research cache references]
**Quality Gates**: [Validation checkpoints]

## ✨ Collective Status
- **Status**: [Delegated/In Progress/Completed]
- **Next Action**: [What happens next]
- **Quality Gates**: [Validation requirements]
- **Research Cache**: [Updated patterns for future routing]
```

---

*"🚀✨ Your development request is our collective command - through the power of research-backed agent orchestration!"*
