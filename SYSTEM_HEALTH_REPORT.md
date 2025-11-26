# System Health Investigation Report
**Date**: 2025-11-24
**Investigation Time**: ~5 hours 20 minutes after system start
**Status**: CRITICAL ISSUES IDENTIFIED

---

## Executive Summary

**Discrepancy Found**: The handoff.md report is OUTDATED and INCORRECT.

- **Reported Status**: 4 services running (PIDs: 34301, 46467, 46444, 46453)
- **Actual Status**: Only 3 services running, with DIFFERENT PIDs
- **Impact**: Agents experiencing critical failures (API quota exhaustion, ChromaDB errors)

---

## Actual System Status

### Running Services ✅

| Service | Reported PID | Actual PID | Status | Uptime |
|---------|--------------|------------|--------|--------|
| **Letta Server** | 34301 | 34301 ✅ | Running | 5h 48m |
| **Dashboard UI** | 46467 | 46480 ❌ | Running | 5h 11m |
| **Orchestrator Agent** | 46444 | 55563 ❌ | Running | 5h 8m |
| **Dashboard Agent** | 46453 | 55660 + 49522 ⚠️ | DUPLICATED | 5h 8m |

### Port Status
```
✅ Port 8283 (Letta): LISTENING - PID 34301
✅ Port 3000 (Dashboard UI): LISTENING - PID 46480
❌ No other ports bound by agents
```

---

## Critical Issues Discovered

### 1. DUPLICATE Dashboard Agent Process ⚠️
**Problem**: TWO dashboard agent processes running simultaneously
- PID 55660: Started 5h 8m ago (from start_a2a_system.sh)
- PID 49522: Started 5h 10m ago (unknown origin, started 2 minutes BEFORE the system startup)

**Evidence**:
```
Both processes writing to same log file:
- /home/adamsl/planner/logs/dashboard_agent.log
```

**Impact**: Potential race conditions, duplicate message processing

### 2. Orchestrator Agent API Quota Exhaustion ❌
**Problem**: Google Gemini API quota completely exhausted
- Quota: 200 requests per day (free tier)
- Status: "429 RESOURCE_EXHAUSTED"
- Impact: Agent cannot make decisions or route requests

**Evidence from logs/orchestrator.log**:
```
Error: 429 RESOURCE_EXHAUSTED
Message: You exceeded your current quota, please check your plan and billing details
Quota: generativelanguage.googleapis.com/generate_content_free_tier_requests
Limit: 200, model: gemini-2.0-flash
```

**Retry Delay**: 9-12 seconds between attempts (still failing)

### 3. ChromaDB Database Corruption ❌
**Problem**: ChromaDB internal errors preventing message board functionality
- Error: "Internal error: Error finding id"
- Impact: Agents cannot poll messages from RAG board transport

**Evidence from logs/dashboard_agent.log**:
```
chromadb.errors.InternalError: Error executing plan: Internal error: Error finding id
[RAGBoardTransport] Error polling messages: Error executing plan: Internal error: Error finding id
```

**Affected**: Both dashboard agent instances experiencing this issue

### 4. PID File Stale/Incorrect ❌
**Problem**: logs/a2a_system.pids contains wrong PIDs
- File shows: orchestrator:55563, dashboard_agent:55660
- Missing: Dashboard UI PID (46480)
- No mention of duplicate dashboard agent (49522)

---

## Root Cause Analysis

### Why User Sees Errors on Dashboard HTML

The user's observation is **100% CORRECT**:

1. **Only port 3000 responds**: Dashboard UI is the only service with HTTP interface
2. **Letta confirmed working**: Server operational at http://localhost:8283/
3. **Other services appear dead**: Agents have NO HTTP endpoints - they communicate via message board only

**The HTML errors are likely showing**:
- Failed API calls to non-existent agent HTTP endpoints (agents don't have HTTP servers)
- Timeout errors from trying to communicate with agents
- ChromaDB errors preventing agent message retrieval

### Why Services Report as "Healthy" but Failing

- **Letta Server**: Actually healthy (HTTP 307 redirect to /v1/health, which returns 200)
- **Dashboard UI**: Healthy (HTTP 200)
- **Orchestrator Agent**: Process running but FUNCTIONALLY DEAD (API quota exhausted, cannot process requests)
- **Dashboard Agent**: Process running but FAILING (ChromaDB errors, duplicate instances)

### Timeline Reconstruction

1. **~5h 10m ago**: Unknown process started dashboard agent (PID 49522)
2. **~5h 8m ago**: User ran start_a2a_system.sh, which started:
   - Orchestrator agent (PID 55563)
   - Dashboard agent (PID 55660) - creating DUPLICATE
3. **~5h 11m ago**: Dashboard UI restarted (different PID than reported)
4. **Since startup**: Orchestrator exhausted API quota, ChromaDB corruption occurred

---

## Service Health Verification Commands

### Check What's Actually Running
```bash
# Letta Server
curl -i http://localhost:8283/v1/health
ps -p 34301 -o pid,cmd,etime,stat

# Dashboard UI
curl -i http://localhost:3000/
ps -p 46480 -o pid,cmd,etime,stat

# Orchestrator Agent (no HTTP interface)
ps -p 55563 -o pid,cmd,etime,stat
tail -n 20 logs/orchestrator.log

# Dashboard Agent (DUPLICATED)
ps -p 55660,49522 -o pid,cmd,etime,stat
tail -n 20 logs/dashboard_agent.log

# Port listeners
ss -tlnp | grep -E ":(3000|8283)"
```

### Check Critical Errors
```bash
# Orchestrator API quota errors
grep -i "quota" logs/orchestrator.log | tail -5

# ChromaDB errors
grep -i "chromadb.errors" logs/dashboard_agent.log | tail -5

# Dashboard agent duplicate detection
lsof -p 55660,49522 | grep "dashboard_agent.log"
```

---

## Recommended Actions

### IMMEDIATE: Stop Duplicate Dashboard Agent
```bash
# Kill the older, unknown dashboard agent process
kill -TERM 49522

# Verify only one dashboard agent running
ps aux | grep "python main.py" | grep -v grep
```

### CRITICAL: Fix API Quota Issue
**Option 1**: Wait for quota reset (resets daily)
**Option 2**: Upgrade to paid Google Gemini API plan
**Option 3**: Switch to different LLM provider (OpenAI, Anthropic, etc.)

### CRITICAL: Fix ChromaDB Corruption
```bash
# Back up current ChromaDB
cp -r storage/chromadb storage/chromadb.backup.$(date +%Y%m%d_%H%M%S)

# Option 1: Delete corrupted collection and reinitialize
# (Will lose message board history)
rm -rf storage/chromadb/*

# Option 2: Try to repair (if chromadb has repair tools)
# (Research needed for specific repair procedure)

# Restart affected agents after DB fix
./stop_a2a_system.sh
./start_a2a_system.sh
```

### Update PID File
```bash
# After stopping duplicates and restarting cleanly
cat > logs/a2a_system.pids << EOF
letta:34301
dashboard_ui:46480
orchestrator:55563
dashboard_agent:55660
EOF
```

---

## Step-by-Step Restart Procedure

### 1. Clean Shutdown
```bash
cd /home/adamsl/planner

# Stop all services
./stop_a2a_system.sh

# Kill any remaining processes
kill -TERM 49522 55660 55563 46480 2>/dev/null

# Verify all stopped
ps aux | grep -E "(python main.py|node.*server.js)" | grep -v grep
```

### 2. Address Root Causes
```bash
# Back up corrupted ChromaDB
mv storage/chromadb storage/chromadb.corrupted.$(date +%Y%m%d_%H%M%S)

# ChromaDB will auto-initialize on next start
# NOTE: This will lose message board history

# Check API quota status at: https://ai.dev/usage?tab=rate-limit
# Wait for reset or configure alternative LLM provider
```

### 3. Clean Start
```bash
# Start all services fresh
./start_a2a_system.sh

# Wait 10 seconds for initialization
sleep 10
```

### 4. Verify Health
```bash
# Check processes
ps aux | grep -E "(letta|python main.py|node.*server.js)" | grep -v grep

# Check ports
ss -tlnp | grep -E ":(3000|8283)"

# Check HTTP endpoints
curl -i http://localhost:8283/v1/health
curl -i http://localhost:3000/

# Check logs for errors
tail -n 50 logs/orchestrator.log
tail -n 50 logs/dashboard_agent.log
tail -n 50 logs/dashboard.log

# Verify no API quota errors
grep -i "429" logs/orchestrator.log | wc -l  # Should be 0

# Verify no ChromaDB errors
grep -i "chromadb.errors" logs/dashboard_agent.log | wc -l  # Should be 0
```

### 5. Update Documentation
```bash
# Update PID file with actual PIDs
./start_a2a_system.sh  # Already writes correct PIDs

# Update handoff.md with current status
# (Manual edit required)
```

---

## Why Dashboard HTML Shows Errors

The sys_admin_debug.html file likely tries to:
1. Connect to agent HTTP endpoints (agents don't have HTTP servers)
2. Query agent status via HTTP (not supported - agents use message board)
3. Display ChromaDB query results (ChromaDB is corrupted)
4. Show orchestrator routing decisions (orchestrator API quota exhausted)

**The dashboard UI (port 3000) is the ONLY HTTP interface**. The HTML debug file should connect to:
- http://localhost:3000/ (Dashboard UI) ✅ Works
- http://localhost:8283/ (Letta Server) ✅ Works
- NOT directly to agents (they have no HTTP interface) ❌

---

## Current System Architecture Reality

```
┌─────────────────────────────────────────┐
│      Letta Server (8283)                │
│   Status: ✅ HEALTHY (PID 34301)        │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┬──────────────────┐
    │                   │                  │
┌───▼──────────────┐ ┌──▼────────────┐ ┌──▼──────────────┐
│ Orchestrator     │ │ Dashboard     │ │  Dashboard      │
│   Agent          │ │   Agent       │ │   Web UI        │
│ PID: 55563       │ │ PID: 55660    │ │ PID: 46480      │
│ Status: ❌ DEAD  │ │ PID: 49522    │ │ Status: ✅ OK   │
│ (API Quota)      │ │ Status: ❌    │ │ Port: 3000      │
│                  │ │ (ChromaDB +   │ │                 │
│                  │ │  Duplicate)   │ │                 │
└──────────────────┘ └───────────────┘ └─────────────────┘
```

**Communication Method**: Message board via ChromaDB RAG system
**Problem**: ChromaDB corrupted, preventing agent communication

---

## Summary

**What Handoff.md Claimed**: "ALL SYSTEMS RUNNING - READY FOR PRODUCTION USE"

**Reality**:
- Letta Server: ✅ Healthy
- Dashboard UI: ✅ Healthy (but different PID)
- Orchestrator Agent: ❌ API quota exhausted, cannot function
- Dashboard Agent: ❌ Duplicated + ChromaDB errors

**User Observation**: 100% CORRECT - agents are effectively non-functional

**Next Steps**:
1. Kill duplicate dashboard agent (PID 49522)
2. Fix or replace corrupted ChromaDB
3. Address API quota (wait for reset or switch provider)
4. Restart system cleanly
5. Update handoff.md with accurate status

---

**Investigation Complete**: System requires immediate maintenance before production use.
