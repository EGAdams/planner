# OpenAI Codex Sub-Agent Collective

## 📖 System Overview

Welcome to your OpenAI Codex Sub-Agent Collective installation! This system implements a research framework for reliable multi-agent coordination using hub-and-spoke architecture.

### What Just Happened?

The collective has been installed in your project with the following components:

#### 🧠 Behavioral Operating System (`AGENTS.md`)
This file contains the core behavioral directives that govern how the collective operates:
- **Directive 1**: Never implement directly - all work flows through agents
- **Directive 2**: Hub-and-spoke routing - all requests go through @routing-agent
- **Directive 3**: Test-driven validation - handoffs include contract validation

#### 🤖 Agent Definitions (`.codex/agents/`)
Each agent has specific capabilities and responsibilities:
- **@routing-agent**: Central hub for semantic request analysis and routing
- **@testing-implementation-agent**: Handles test frameworks and validation
- **@behavioral-transformation-agent**: Manages behavioral system changes
- **@hook-integration-agent**: Implements and manages hook systems

#### 🪝 Hook Scripts (`.codex/hooks/`)
Enforcement mechanisms that ensure directive compliance:
- **directive-enforcer.sh**: Validates behavioral directives before tool execution
- **collective-metrics.sh**: Collects performance and research metrics
- **test-driven-handoff.sh**: Validates handoff contracts during transitions
- **routing-executor.sh**: Executes routing decisions and agent handoffs

#### 🧪 Testing Framework (`.codex-collective/`)
Complete testing system for validating collective behavior:
- **Jest configuration**: Set up for contract validation testing
- **Test contracts**: Templates for handoff validation
- **Metrics collection**: Research data gathering

## 🚀 Getting Started

### 1. Restart OpenAI Codex
**IMPORTANT**: Restart OpenAI Codex to activate the hook system and agents.

### 2. Test the Installation
Try these commands to verify everything works:

```bash
# Check status
npx codex-code-collective status

# Validate installation
npx codex-code-collective validate
```

### 3. Try Agent Routing
In OpenAI Codex, try a request like:
> "Route this through @routing-agent to create a login component with validation"

## 🎯 How to Use the Collective

### Making Requests
Instead of asking Codex directly, route requests through agents:

**❌ Old Way (Direct):**
> "Create a login form component"

**✅ New Way (Agent Routed):**
> "Route to @routing-agent: Create a login form component with React hooks"

### Understanding Agent Routing
The @routing-agent will analyze your request and select the best agent:
- **Implementation tasks** → @implementation-agent
- **Testing tasks** → @testing-implementation-agent  
- **Research tasks** → @research-agent
- **Hook/behavioral tasks** → @hook-integration-agent

### Monitoring Activity
- **Metrics**: Check `.codex-collective/metrics/` for performance data
- **Logs**: Review `/tmp/collective-*.log` for detailed activity
- **Status**: Run `npx codex-code-collective status` for health check

## 📊 Research Framework

This collective is designed to prove three key hypotheses:

### H1: JIT Context Loading
**Theory**: Loading context on-demand is more efficient than pre-loading
**Measurement**: Context size, token reduction, load times
**Goal**: >30% reduction in token usage

### H2: Hub-and-Spoke Coordination  
**Theory**: Central routing outperforms peer-to-peer communication
**Measurement**: Routing accuracy, coordination overhead, violations
**Goal**: >95% routing compliance

### H3: Test-Driven Handoffs
**Theory**: Contract-based handoffs improve quality
**Measurement**: Handoff success rates, test pass rates, retry counts
**Goal**: >98% handoff success rate

## 🛡️ Behavioral Directives

The collective enforces three prime directives through hooks:

### Directive 1: Never Implement Directly
- All implementation must flow through specialized agents
- Direct coding by the hub controller is blocked
- Violations trigger re-routing to @routing-agent

### Directive 2: Collective Routing Protocol
- All requests enter through @routing-agent
- No direct agent-to-agent communication allowed
- Hub-and-spoke pattern strictly maintained

### Directive 3: Test-Driven Validation
- Handoffs require test contracts with pre/post conditions
- Failed validation triggers automatic re-routing
- Quality gates ensure delivery standards

## 🔧 Configuration

### Hook Configuration (`.codex/settings.json`)
Controls when and how hooks execute:
- **PreToolUse**: Validates directives before tool execution
- **PostToolUse**: Collects metrics and validates results
- **SubagentStop**: Ensures proper handoff validation

### Agent Configuration (`.codex/agents/*.json`)
Each agent definition includes:
- **Capabilities**: What the agent can do
- **Tools**: Which OpenAI Codex tools they can access
- **Specialization**: Their primary focus area
- **Fallbacks**: Alternative agents if unavailable

### Testing Configuration (`.codex-collective/`)
Jest-based testing framework:
- **Contract templates**: Pre-built validation patterns
- **Test suites**: Handoff, directive, and contract tests
- **Coverage reporting**: Quality metrics and reporting

## 🚨 Important Notes

### System Behavior Changes
With the collective active, OpenAI Codex will behave differently:
- **Routing Required**: Direct implementation requests may be blocked
- **Hook Validation**: Actions are validated before execution
- **Metrics Collection**: Performance data is automatically gathered
- **Quality Gates**: Failed handoffs trigger retries or escalation

### Troubleshooting
If something isn't working:
1. **Restart OpenAI Codex** - Hooks need to be reloaded
2. **Check Status** - Run `npx codex-code-collective status`
3. **Validate Installation** - Run `npx codex-code-collective validate`
4. **Review Logs** - Check `/tmp/collective-*.log` files
5. **Repair Installation** - Run `npx codex-code-collective repair`

### Getting Help
- **Status Command**: `npx codex-code-collective status`
- **Validation**: `npx codex-code-collective validate`  
- **Repair**: `npx codex-code-collective repair`
- **Documentation**: Review the files in `.codex/docs/`

## 🔬 Research Participation

By using this collective, you're participating in research on:
- **Multi-agent coordination patterns**
- **Context engineering efficiency** 
- **Test-driven development practices**
- **Behavioral enforcement systems**

Metrics are collected automatically (no personal data) to validate the research hypotheses.

## 🎯 Quick Reference

### Essential Commands
```bash
# Check collective health
npx codex-code-collective status

# Validate everything is working  
npx codex-code-collective validate

# Fix problems
npx codex-code-collective repair

# Remove collective
npx codex-code-collective clean
```

### Agent Routing Examples
```
"@routing-agent please create a user authentication system"
"Route to appropriate agent: implement API endpoint for user login"
"@routing-agent analyze the current codebase structure"
```

### File Structure
```
.codex/
├── settings.json        # Hook configuration
├── agents/             # Agent definitions  
├── hooks/              # Enforcement scripts
└── docs/               # This documentation

.codex-collective/
├── tests/              # Contract validation
├── metrics/            # Research data
└── package.json        # Testing framework
```

---

**Welcome to the future of AI-assisted development!** 🚀

The collective is now active and ready to coordinate your development work through intelligent agent routing and quality assurance.