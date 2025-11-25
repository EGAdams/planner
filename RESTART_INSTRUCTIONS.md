# Quick System Restart Instructions

**Current Status**: System has critical issues requiring restart
- Duplicate dashboard agent processes
- ChromaDB database corruption
- Orchestrator API quota exhausted

---

## OPTION 1: Quick Restart (Fixes Duplicate Only)

```bash
cd /home/adamsl/planner

# Kill the duplicate dashboard agent
kill -TERM 49522

# Verify it's gone
ps -p 49522 || echo "Duplicate killed successfully"

# Check remaining services
ps aux | grep -E "(letta|python main.py|node.*server.js)" | grep -v grep
```

**This fixes**: Duplicate dashboard agent
**Still broken**: ChromaDB errors, API quota exhaustion

---

## OPTION 2: Full Clean Restart (Recommended)

### Step 1: Stop Everything
```bash
cd /home/adamsl/planner

# Stop via script
./stop_a2a_system.sh

# Force kill any stragglers
kill -TERM 49522 55660 55563 46480 2>/dev/null

# Verify all stopped (should show nothing)
ps aux | grep -E "(python main.py|node.*server.js)" | grep -v grep
```

### Step 2: Fix ChromaDB Corruption
```bash
# Back up corrupted database
mv storage/chromadb storage/chromadb.corrupted.$(date +%Y%m%d_%H%M%S)

# ChromaDB will auto-initialize fresh on next start
# NOTE: This loses message board history
```

### Step 3: Start Clean
```bash
# Start all services
./start_a2a_system.sh

# Wait for initialization
sleep 10
```

### Step 4: Verify Health
```bash
# Check all processes running
ps aux | grep -E "(letta|python main.py|node.*server.js)" | grep -v grep

# Should see:
# - 1x letta server
# - 1x node server (dashboard UI)
# - 2x python main.py (orchestrator + dashboard agent)
# Total: 4 processes

# Check ports
ss -tlnp | grep -E ":(3000|8283)"

# Should show:
# - Port 8283: letta
# - Port 3000: node

# Test HTTP endpoints
curl http://localhost:8283/v1/health
curl http://localhost:3000/

# Both should respond (8283 may return 307 redirect)
```

### Step 5: Check Logs
```bash
# Orchestrator - check for API quota errors
tail -n 50 logs/orchestrator.log

# If you see "429 RESOURCE_EXHAUSTED", the API quota is still exhausted
# You'll need to wait for daily reset or switch LLM providers

# Dashboard Agent - check for ChromaDB errors
tail -n 50 logs/dashboard_agent.log

# Should NOT see "chromadb.errors.InternalError" after DB reset

# Dashboard UI
tail -n 50 logs/dashboard.log

# Should show successful startup
```

---

## OPTION 3: Keep Letta Running (Partial Restart)

If you want to keep the Letta server running (PID 34301):

```bash
cd /home/adamsl/planner

# Stop only agent services
kill -TERM 49522 55660 55563 46480 2>/dev/null

# Fix ChromaDB
mv storage/chromadb storage/chromadb.corrupted.$(date +%Y%m%d_%H%M%S)

# Restart only agents and dashboard
# (You'll need to manually start these since start_a2a_system.sh starts everything)

# Start Dashboard UI
cd /home/adamsl/planner/admin-dashboard
source /home/adamsl/planner/.venv/bin/activate
npm start > /home/adamsl/planner/logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "dashboard_ui:$DASHBOARD_PID"

# Start Orchestrator Agent
cd /home/adamsl/planner/a2a_communicating_agents/orchestrator_agent
source /home/adamsl/planner/.venv/bin/activate
python main.py > /home/adamsl/planner/logs/orchestrator.log 2>&1 &
ORCH_PID=$!
echo "orchestrator:$ORCH_PID"

# Start Dashboard Agent
cd /home/adamsl/planner/a2a_communicating_agents/dashboard_agent
source /home/adamsl/planner/.venv/bin/activate
python main.py > /home/adamsl/planner/logs/dashboard_agent.log 2>&1 &
DASH_AGENT_PID=$!
echo "dashboard_agent:$DASH_AGENT_PID"

# Update PID file
cat > /home/adamsl/planner/logs/a2a_system.pids << EOF
letta:34301
dashboard_ui:$DASHBOARD_PID
orchestrator:$ORCH_PID
dashboard_agent:$DASH_AGENT_PID
EOF

cd /home/adamsl/planner
```

---

## Verification Commands

After any restart option, run these to verify health:

```bash
# 1. Process check (should show 4 processes)
echo "=== Running Processes ==="
ps aux | grep -E "(letta|python main.py|node.*server.js)" | grep -v grep | wc -l
# Expected: 4

# 2. Port check (should show 2 ports)
echo "=== Port Listeners ==="
ss -tlnp 2>/dev/null | grep -E ":(3000|8283)"
# Expected:
#   Port 8283 (letta)
#   Port 3000 (node)

# 3. PID file accuracy
echo "=== PID File ==="
cat logs/a2a_system.pids

# 4. Verify each PID exists
while IFS=: read -r service pid; do
  if ps -p "$pid" > /dev/null 2>&1; then
    echo "✅ $service (PID $pid) running"
  else
    echo "❌ $service (PID $pid) NOT running"
  fi
done < logs/a2a_system.pids

# 5. Check for duplicate dashboard agents
echo "=== Dashboard Agent Count (should be 1) ==="
ps aux | grep "python main.py" | grep -v grep | wc -l
# Expected: 2 (orchestrator + dashboard agent)

# 6. HTTP health checks
echo "=== HTTP Health ==="
echo -n "Letta: "
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8283/v1/health

echo -n "Dashboard: "
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/

# 7. Recent errors
echo "=== Recent Orchestrator Errors ==="
grep -i "error\|429" logs/orchestrator.log | tail -5

echo "=== Recent Dashboard Agent Errors ==="
grep -i "error\|chromadb" logs/dashboard_agent.log | tail -5
```

---

## Expected Output After Successful Restart

```
=== Running Processes ===
4

=== Port Listeners ===
LISTEN 0      2048        127.0.0.1:8283       0.0.0.0:*    users:(("letta",pid=34301,fd=15))
LISTEN 0      511         127.0.0.1:3000       0.0.0.0:*    users:(("node",pid=XXXXX,fd=22))

=== PID File ===
letta:34301
dashboard_ui:XXXXX
orchestrator:XXXXX
dashboard_agent:XXXXX

✅ letta (PID 34301) running
✅ dashboard_ui (PID XXXXX) running
✅ orchestrator (PID XXXXX) running
✅ dashboard_agent (PID XXXXX) running

=== Dashboard Agent Count (should be 1) ===
2

=== HTTP Health ===
Letta: 307
Dashboard: 200

=== Recent Orchestrator Errors ===
(Should be empty or show old errors before restart)

=== Recent Dashboard Agent Errors ===
(Should be empty or show old errors before restart)
```

---

## Known Remaining Issue: API Quota

**Problem**: Orchestrator agent uses Google Gemini API (free tier: 200 requests/day)

**Symptoms**:
- Orchestrator logs show "429 RESOURCE_EXHAUSTED"
- Agent cannot make routing decisions

**Solutions**:

### Option A: Wait for Quota Reset
- Quota resets daily (check: https://ai.dev/usage?tab=rate-limit)
- No code changes needed
- Temporary solution only

### Option B: Upgrade API Plan
- Get paid Google Gemini API key
- Update configuration with new key
- Permanent solution

### Option C: Switch LLM Provider
- Configure OpenAI, Anthropic Claude, or other provider
- Update orchestrator agent configuration
- Requires code changes

**Recommendation**: Wait for quota reset first, then implement Option B or C for production use.

---

## Accessing the System

After restart:

1. **Dashboard UI**: http://localhost:3000
2. **Letta Server**: http://localhost:8283
3. **Logs**: `tail -f logs/*.log`
4. **Stop**: `./stop_a2a_system.sh`

---

## Troubleshooting

### "Port already in use" error
```bash
# Find what's using the port
lsof -ti:3000 | xargs kill -9
lsof -ti:8283 | xargs kill -9

# Then restart
./start_a2a_system.sh
```

### Agents won't start
```bash
# Check Python version
python --version  # Should be 3.12.3

# Verify virtual environment
source .venv/bin/activate
which python  # Should show .venv/bin/python

# Check for import errors
cd a2a_communicating_agents/orchestrator_agent
python -c "import agent_messaging"  # Should not error
```

### Dashboard shows connection errors
- Agents don't have HTTP endpoints (this is normal)
- Dashboard communicates via ChromaDB message board
- If ChromaDB is corrupted, dashboard can't reach agents

---

**Choose your restart option and execute the commands above.**

**Recommended**: OPTION 2 (Full Clean Restart) to fix all issues except API quota.
