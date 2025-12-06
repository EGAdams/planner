# Agent System Quick Reference Guide

## 🚀 Quick Start

### Launch Smart Menu
```bash
cd /home/adamsl/planner/smart_menu
python main.py
```

Navigate to: **A2A Communicating Agents → 🚀 Agent Lifecycle & Diagnostics**

## 📋 Common Operations

### Check Status
- **Menu**: 📊 Check Agent Status
- **Command**: `ps aux | grep -E "(orchestrator|coder|tester)_agent"`

### Start All Agents
```bash
cd /home/adamsl/planner/a2a_communicating_agents

# 1. Start WebSocket server first
./start_websocket_server.sh

# 2. Start orchestrator
./start_orchestrator.sh

# 3. Start specialist agents
./start_coder_agent.sh
./start_tester_agent.sh
```

### Stop All Agents
```bash
cd /home/adamsl/planner/a2a_communicating_agents

./stop_orchestrator.sh
./stop_coder_agent.sh
./stop_tester_agent.sh
./stop_websocket_server.sh
```

### Restart Everything (One Command)
- **Menu**: 🔄 Restart All Agents
- **What it does**: Stops all agents, waits, then starts them in correct order

## 🔍 Debugging

### Run Full Diagnostic
- **Menu**: 🔍 Run Full Agent Diagnostic
- **Shows**: Process status, recent logs, recent errors

### View Logs
```bash
# Orchestrator logs
tail -f logs/orchestrator.log

# Coder agent logs
tail -f a2a_communicating_agents/logs/coder_agent.log

# All errors
grep -i "error" logs/*.log | tail -20
```

### Chat with Orchestrator
- **Menu**: Open Orchestrator Chat Session
- **Or**: `cd a2a_communicating_agents/agent_messaging && python orchestrator_chat.py`

## 🛠️ Troubleshooting

### Agent Not Responding
1. Check status: Menu → 📊 Check Agent Status
2. Check logs: Menu → Show [Agent] Logs
3. Restart: Menu → ⏹️ Stop + ▶️ Start

### Wrong Agent Selected
1. Check orchestrator logs for routing decision
2. Verify API key is set: `env | grep OPENAI_API_KEY`
3. Restart orchestrator to reload code

### Messages Not Delivered
1. Check WebSocket server is running
2. Check transport connectivity
3. Restart all agents: Menu → 🔄 Restart All Agents

## 📁 File Locations

### Agent Directories
- **Orchestrator**: `a2a_communicating_agents/orchestrator_agent/`
- **Coder**: `a2a_communicating_agents/coder_agent/`
- **Tester**: `a2a_communicating_agents/tester_agent/`

### Configuration Files
- **Agent configs**: `*/agent.json` in each agent directory
- **Environment**: `.env` in project root

### Log Files
- **Main logs**: `logs/` directory
- **Agent logs**: `a2a_communicating_agents/logs/`

### Scripts
All in `a2a_communicating_agents/`:
- `start_orchestrator.sh` / `stop_orchestrator.sh`
- `start_coder_agent.sh` / `stop_coder_agent.sh`
- `start_tester_agent.sh` / `stop_tester_agent.sh`
- `start_websocket_server.sh` / `stop_websocket_server.sh`

## 💡 Tips

### Using the Smart Menu
- **Emoji indicators**:
  - ▶️ = Start
  - ⏹️ = Stop
  - 🔄 = Restart
  - 📊 = Status
  - 🔍 = Diagnostic

### Agent Startup Order
1. **Always start WebSocket server first** (if using WebSocket transport)
2. **Then orchestrator** (discovers other agents)
3. **Then specialist agents** (coder, tester)

### When to Restart
- After code changes to agent files
- When routing behavior changes
- If API keys are updated
- If agents become unresponsive

## 🎯 Common Tasks

### Test WebAssembly Code Generation
1. Ensure all agents running
2. Open orchestrator chat
3. Send: "please write a hello world snippet in WebAssembly"
4. Should route to coder-agent and generate WAT code

### Add a New Agent
1. Create agent directory with `main.py` and `agent.json`
2. Follow pattern from existing agents
3. Create start/stop scripts
4. Restart orchestrator to discover new agent
5. Add to smart menu

### Update Agent Capabilities
1. Edit `agent.json` in agent directory
2. Restart orchestrator (to reload config)
3. Test routing to ensure correct selection

## 🆘 Emergency Commands

### Kill Everything
```bash
pkill -f "orchestrator_agent/main.py"
pkill -f "coder_agent/main.py"
pkill -f "tester_agent/main.py"
pkill -f "websocket_server.py"
```

### Check What's Running
```bash
ps aux | grep -E "(orchestrator|coder|tester|websocket)" | grep -v grep
```

### View All Recent Activity
```bash
tail -n 50 logs/*.log a2a_communicating_agents/logs/*.log
```

## 📞 Getting Help

### Ask Claude (Me!)
- "check agent status"
- "debug agent communication"
- "why isn't the coder agent responding"
- "show orchestrator logs"

### Use the Debug Skill
I have the `agent-debug` skill that provides systematic diagnostics.
Just ask and I'll automatically use it!

---

**Last Updated**: December 5, 2024
**System**: A2A Communicating Agents with Smart Menu Integration
