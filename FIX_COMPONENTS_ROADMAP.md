# Fix Components Implementation Roadmap

## Overview

This roadmap provides a detailed implementation plan for the 36 menu items across 9 categories in the "Fix Components" section of the A2A Agent Collective Smart Menu. The goal is to bring `agent_messaging` to feature parity with `a2a_communicating_agents`.

---

## Implementation Strategy

### Phased Approach

We'll implement in three tiers based on dependencies:

- **TIER 1 (Foundation)**: Database and server infrastructure - must be completed first
- **TIER 2 (Core Services)**: Agent communication, memory, and transport - requires TIER 1
- **TIER 3 (Enhanced Features)**: Dashboard, voice, and service management - builds on TIER 2

### Implementation Method

For each menu item, we'll:
1. Reference working code from `a2a_communicating_agents`
2. Adapt implementation for `agent_messaging` context
3. Create shell script or Python implementation
4. Update menu config.json with actual action
5. Test the implementation
6. Document any issues or dependencies

---

## TIER 1: FOUNDATION (CRITICAL PRIORITY)

Must be completed before other tiers. These provide the core infrastructure.

### Category 1: PostgreSQL Setup (4 items)

**Dependencies**: None (pure infrastructure)
**Estimated Effort**: 2-3 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/scripts/`

#### 1.1 Initialize PostgreSQL Database

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/hybrid_letta_agents/init_letta_db.py`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/init_postgresql.sh
#!/bin/bash
# Check if PostgreSQL is installed
# Check if letta database exists
# Create database if needed
# Set permissions
# Report status
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/init_postgresql.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] PostgreSQL database "letta" exists
- [ ] User "letta" has proper permissions
- [ ] Connection string verified

**Testing**: Run script and verify with `psql -U letta -d letta -c '\dt'`

---

#### 1.2 Check PostgreSQL Connection

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/hybrid_letta_agents/init_letta_db.py` (connection logic)

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/check_postgresql.sh
#!/bin/bash
# Test connection to PostgreSQL
# Verify letta database exists
# Check user permissions
# Report connection status
# Display database info
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/check_postgresql.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Can connect to PostgreSQL server
- [ ] Can access letta database
- [ ] Displays connection status

**Testing**: Run and verify output shows successful connection

---

#### 1.3 Reset Database

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/reset_postgresql.sh
#!/bin/bash
# WARNING: Destructive operation
# Drop all tables in letta database
# Recreate schema
# Reset to clean state
# Confirmation prompt
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/reset_postgresql.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Prompts for confirmation
- [ ] Drops all tables
- [ ] Recreates clean schema

**Testing**: Run and verify tables are reset

---

#### 1.4 View Database Schema

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/view_postgresql_schema.sh
#!/bin/bash
# Connect to PostgreSQL
# List all tables
# Show table schemas
# Display relationships
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/view_postgresql_schema.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Lists all tables
- [ ] Shows columns for each table
- [ ] Readable format

**Testing**: Run and verify schema output

---

### Category 2: Letta Server Admin (4 items)

**Dependencies**: PostgreSQL Setup (Category 1) must be complete
**Estimated Effort**: 3-4 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/scripts/`

#### 2.1 Initialize Letta Database

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/hybrid_letta_agents/init_letta_db.py`

**Implementation Plan**:
```python
# Create script: agent_messaging/scripts/init_letta_db.py
# Copy from a2a_communicating_agents/hybrid_letta_agents/init_letta_db.py
# Set LETTA_PG_URI environment variable
# Import Letta ORM Base
# Run schema creation
# Verify tables created
```

**Action Update**:
```json
"action": "cd ../agent_messaging/scripts && python3 init_letta_db.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Letta schema tables created
- [ ] Tables verified in PostgreSQL
- [ ] No errors during creation

**Testing**: Run script and check PostgreSQL for Letta tables

---

#### 2.2 Start Letta Server

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/start_a2a_system.sh` (lines 61-79)
- `a2a_communicating_agents/hybrid_letta_agents/debug_letta_server.py`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/start_letta_server.sh
#!/bin/bash
# Set LETTA_PG_URI environment variable
# Check if server already running (port 8283)
# Start letta server in background
# Save PID to file
# Wait for server to be ready
# Verify server is running
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/start_letta_server.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Letta server starts on port 8283
- [ ] PID saved to logs/letta.pid
- [ ] Server accessible via HTTP
- [ ] No port conflicts

**Testing**: Run script and curl http://localhost:8283

---

#### 2.3 Check Letta Server Status

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/check_letta_status.sh
#!/bin/bash
# Check if port 8283 is active
# Check PID file exists and process running
# Query server health endpoint
# Display status information
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/check_letta_status.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Shows if server is running
- [ ] Displays PID if running
- [ ] Shows port status
- [ ] Health check result

**Testing**: Run with server running and stopped

---

#### 2.4 Stop Letta Server

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/stop_letta_server.sh
#!/bin/bash
# Read PID from logs/letta.pid
# Send SIGTERM to process
# Wait for graceful shutdown
# Kill if necessary
# Clean up PID file
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/stop_letta_server.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Gracefully stops server
- [ ] Cleans up PID file
- [ ] Verifies port is freed
- [ ] Handles case where server not running

**Testing**: Start server, run script, verify stopped

---

## TIER 2: CORE SERVICES (HIGH PRIORITY)

Requires TIER 1 completion. Implements agent communication and core functionality.

### Category 3: Basic Agent Communication Tests (4 items)

**Dependencies**: Letta Server Admin (Category 2)
**Estimated Effort**: 4-5 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/tests/`

#### 3.1 Test Agent Discovery

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `agent_messaging/run_collective.py`
- `agent_messaging/a2a_collective.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_agent_discovery.py
# Scan workspace for agent.json files
# Load agent cards
# Verify agent registry
# Test discovery mechanism
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_agent_discovery.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Discovers all agent.json files
- [ ] Loads agent cards correctly
- [ ] Registry contains expected agents
- [ ] No discovery errors

**Testing**: Run and verify agent count matches expected

---

#### 3.2 Test Message Transport

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `agent_messaging/message_transport.py`
- `agent_messaging/transport_factory.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_message_transport.py
# Test WebSocket transport
# Test Letta transport
# Test transport factory
# Verify message delivery
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_message_transport.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] WebSocket transport works
- [ ] Letta transport works
- [ ] Factory creates correct transport
- [ ] Messages delivered successfully

**Testing**: Run and verify all transports pass

---

#### 3.3 Test Agent Delegation

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/orchestrator_agent/a2a_dispatcher.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_agent_delegation.py
# Test request routing
# Test capability matching
# Test agent selection
# Verify delegation flow
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_agent_delegation.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Routes requests correctly
- [ ] Matches capabilities
- [ ] Selects appropriate agent
- [ ] Delegation completes

**Testing**: Run with sample requests

---

#### 3.4 Test Memory Backend

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `agent_messaging/letta_memory.py`
- `agent_messaging/chromadb_memory.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_memory_backend.py
# Test Letta memory operations
# Test ChromaDB memory operations
# Test memory factory
# Verify storage and retrieval
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_memory_backend.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Letta memory stores/retrieves
- [ ] ChromaDB memory stores/retrieves
- [ ] Factory creates correct backend
- [ ] No data loss

**Testing**: Run and verify memory operations

---

### Category 4: Orchestrator Agent Setup (4 items)

**Dependencies**: Basic Agent Communication Tests (Category 3)
**Estimated Effort**: 5-6 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/`

#### 4.1 Start Orchestrator Agent

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/orchestrator_agent/main.py`
- `a2a_communicating_agents/orchestrator_agent/a2a_dispatcher.py`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/start_orchestrator.sh
#!/bin/bash
# Copy orchestrator implementation from a2a_communicating_agents
# Adapt for agent_messaging structure
# Start orchestrator in background
# Save PID
# Verify running
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/start_orchestrator.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Orchestrator agent starts
- [ ] Loads agent.json card
- [ ] Registers capabilities
- [ ] Listens for requests

**Testing**: Start and verify agent responds

---

#### 4.2 Load Agent Card

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```python
# Create script: agent_messaging/scripts/load_agent_card.py
# Locate agent.json files
# Parse JSON schema
# Validate card structure
# Display agent information
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 scripts/load_agent_card.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Finds agent.json files
- [ ] Parses cards correctly
- [ ] Validates schema
- [ ] Displays agent info

**Testing**: Run and verify output

---

#### 4.3 Test Routing Logic

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/orchestrator_agent/a2a_dispatcher.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_routing_logic.py
# Test capability matching
# Test request routing
# Test fallback logic
# Verify correct agent selection
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_routing_logic.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Routes based on capabilities
- [ ] Handles unknown requests
- [ ] Fallback logic works
- [ ] Correct agent selected

**Testing**: Run with various request types

---

#### 4.4 Check Agent Registry

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```python
# Create script: agent_messaging/scripts/check_agent_registry.py
# Query current registry
# List registered agents
# Show capabilities
# Display status
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 scripts/check_agent_registry.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Lists all registered agents
- [ ] Shows capabilities for each
- [ ] Displays agent status
- [ ] Readable format

**Testing**: Run and verify agent list

---

### Category 5: Memory Systems (4 items)

**Dependencies**: Letta Server Admin (Category 2)
**Estimated Effort**: 3-4 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/tests/`

#### 5.1 Test ChromaDB Memory

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `agent_messaging/chromadb_memory.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_chromadb_memory.py
# Initialize ChromaDB backend
# Test remember() operation
# Test recall() operation
# Test get_recent()
# Verify persistence
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_chromadb_memory.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] ChromaDB initializes
- [ ] Stores memories
- [ ] Recalls memories
- [ ] Persistence works

**Testing**: Run and verify operations

---

#### 5.2 Test Letta Memory Backend

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `agent_messaging/letta_memory.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_letta_memory.py
# Initialize Letta memory backend
# Test remember() with Letta
# Test recall() with Letta
# Test archival memory
# Verify server integration
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_letta_memory.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Connects to Letta server
- [ ] Stores in archival memory
- [ ] Recalls from memory
- [ ] Server integration works

**Testing**: Requires Letta server running

---

#### 5.3 Reset Memory Storage

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/reset_memory.sh
#!/bin/bash
# WARNING: Destructive operation
# Clear ChromaDB storage
# Clear Letta archival memory
# Reset memory indices
# Confirmation prompt
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/reset_memory.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Prompts for confirmation
- [ ] Clears all memory stores
- [ ] Resets indices
- [ ] Reports completion

**Testing**: Store data, reset, verify cleared

---

#### 5.4 View Memory Stats

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```python
# Create script: agent_messaging/scripts/view_memory_stats.py
# Query ChromaDB statistics
# Query Letta memory stats
# Calculate totals
# Display formatted output
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 scripts/view_memory_stats.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Shows ChromaDB stats
- [ ] Shows Letta memory stats
- [ ] Displays totals
- [ ] Readable format

**Testing**: Run and verify stats display

---

### Category 6: WebSocket & Transport (4 items)

**Dependencies**: Basic Agent Communication Tests (Category 3)
**Estimated Effort**: 3-4 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/tests/`

#### 6.1 Test WebSocket Connection

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `agent_messaging/websocket_transport.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_websocket_connection.py
# Start WebSocket server
# Test client connection
# Test message sending
# Test message receiving
# Test disconnection
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_websocket_connection.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] WebSocket connects
- [ ] Sends messages
- [ ] Receives messages
- [ ] Disconnects cleanly

**Testing**: Run and verify all operations

---

#### 6.2 Test Transport Factory

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `agent_messaging/transport_factory.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_transport_factory.py
# Test factory creates WebSocket transport
# Test factory creates Letta transport
# Test factory creates RAGBoard transport
# Verify correct type returned
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_transport_factory.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Creates WebSocket transport
- [ ] Creates Letta transport
- [ ] Creates RAGBoard transport
- [ ] Returns correct types

**Testing**: Run and verify creation

---

#### 6.3 Test Fallback Mechanisms

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_transport_fallback.py
# Simulate primary transport failure
# Test fallback to secondary
# Verify graceful degradation
# Test recovery
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_transport_fallback.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Detects transport failure
- [ ] Falls back to secondary
- [ ] Messages still delivered
- [ ] Recovers when primary available

**Testing**: Simulate failures and verify fallback

---

#### 6.4 Verify Message Routing

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_message_routing.py
# Test point-to-point routing
# Test broadcast routing
# Test topic-based routing
# Verify delivery confirmation
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_message_routing.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Point-to-point works
- [ ] Broadcast works
- [ ] Topic routing works
- [ ] Confirms delivery

**Testing**: Send various message types

---

## TIER 3: ENHANCED FEATURES (MEDIUM PRIORITY)

Optional but valuable features. Requires TIER 2 completion.

### Category 7: Dashboard & UI Setup (4 items)

**Dependencies**: Orchestrator Agent Setup (Category 4)
**Estimated Effort**: 6-8 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/dashboard/`

#### 7.1 Start Dashboard Server

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/dashboard_agent/main.py`
- `a2a_communicating_agents/start_a2a_system.sh` (lines 117-136)

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/start_dashboard.sh
#!/bin/bash
# Check if port 3000 is free
# Start dashboard server
# Save PID
# Wait for server ready
# Open browser
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/start_dashboard.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Server starts on port 3000
- [ ] UI accessible
- [ ] No errors
- [ ] Browser opens

**Testing**: Access http://localhost:3000

---

#### 7.2 Build Dashboard Assets

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/build_dashboard.sh
#!/bin/bash
# Install npm dependencies
# Build React/Vue assets
# Compile CSS
# Generate production build
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/build_dashboard.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Dependencies installed
- [ ] Assets compiled
- [ ] No build errors
- [ ] Production ready

**Testing**: Verify build directory exists

---

#### 7.3 Test Dashboard Connectivity

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_dashboard_connectivity.py
# Test HTTP endpoint accessible
# Test WebSocket connection
# Test API endpoints
# Verify data flow
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_dashboard_connectivity.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] HTTP endpoint responds
- [ ] WebSocket connects
- [ ] API works
- [ ] Data flows

**Testing**: Run with dashboard running

---

#### 7.4 Open Dashboard in Browser

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/open_dashboard.sh
#!/bin/bash
# Check if dashboard running
# Detect browser (xdg-open, chrome, etc.)
# Open URL
# Report status
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/open_dashboard.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Detects running dashboard
- [ ] Opens browser
- [ ] Navigates to URL
- [ ] Works on Linux/WSL

**Testing**: Run and verify browser opens

---

### Category 8: Service Management (4 items)

**Dependencies**: All TIER 2 categories
**Estimated Effort**: 4-5 hours
**Working Directory**: `/home/adamsl/planner/agent_messaging/scripts/`

#### 8.1 Start All Services

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/start_a2a_system.sh`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/start_all_services.sh
#!/bin/bash
# Start PostgreSQL (if not running)
# Start Letta server
# Start orchestrator agent
# Start dashboard
# Save all PIDs
# Verify all running
# Report status
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/start_all_services.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] All services start in order
- [ ] PIDs saved
- [ ] Health checks pass
- [ ] Status report generated

**Testing**: Run and verify all services up

---

#### 8.2 Stop All Services

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/stop_all_services.sh
#!/bin/bash
# Read PIDs from files
# Stop dashboard
# Stop orchestrator
# Stop Letta server
# Clean up PID files
# Verify all stopped
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/stop_all_services.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Stops all services gracefully
- [ ] Cleans up PIDs
- [ ] Verifies ports freed
- [ ] Reports completion

**Testing**: Start all, then stop all

---

#### 8.3 View Service Status

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/view_service_status.sh
#!/bin/bash
# Check PostgreSQL status
# Check Letta server status
# Check orchestrator status
# Check dashboard status
# Display formatted table
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/view_service_status.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Shows all service states
- [ ] Displays PIDs if running
- [ ] Shows ports used
- [ ] Readable table format

**Testing**: Run with various service states

---

#### 8.4 View Service Logs

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/view_service_logs.sh
#!/bin/bash
# Display menu of services
# Tail selected log file
# Option to view full log
# Follow mode option
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/view_service_logs.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Lists available logs
- [ ] Displays log content
- [ ] Follow mode works
- [ ] User-friendly interface

**Testing**: Generate logs and view them

---

### Category 9: LiveKit Integration (4 items)

**Dependencies**: Letta Server Admin (Category 2)
**Estimated Effort**: 8-10 hours (complex)
**Working Directory**: `/home/adamsl/planner/agent_messaging/voice/`

#### 9.1 Initialize LiveKit Server

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/hybrid_letta_agents/LETTA_LIVEKIT_INTEGRATION_REVISED.md`
- `a2a_communicating_agents/hybrid_letta_agents/agents/VOICE_SETUP_GUIDE.md`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/init_livekit.sh
#!/bin/bash
# Check LiveKit installation
# Create config file
# Set API keys
# Initialize server
# Verify running
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/init_livekit.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] LiveKit server installed
- [ ] Config file created
- [ ] Server initializes
- [ ] API accessible

**Testing**: Verify LiveKit responds

---

#### 9.2 Test Voice Communication

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/hybrid_letta_agents/test_letta_voice_connection.py`

**Implementation Plan**:
```python
# Create test: agent_messaging/tests/test_voice_communication.py
# Test audio stream setup
# Test voice input
# Test voice output
# Test bidirectional communication
```

**Action Update**:
```json
"action": "cd ../agent_messaging && python3 tests/test_voice_communication.py",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Audio stream works
- [ ] Input captured
- [ ] Output plays
- [ ] Bidirectional works

**Testing**: Requires audio device

---

#### 9.3 Start Voice Agent

**Current State**: `echo 'Not implemented yet.'`

**Source Reference**:
- `a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent.py`
- `a2a_communicating_agents/hybrid_letta_agents/agents/orchestrator_voice.py`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/start_voice_agent.sh
#!/bin/bash
# Copy voice agent implementation
# Start voice agent with LiveKit
# Save PID
# Verify running
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/start_voice_agent.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Voice agent starts
- [ ] Connects to LiveKit
- [ ] Accepts voice input
- [ ] Responds with voice

**Testing**: Send voice input, verify response

---

#### 9.4 Check LiveKit Status

**Current State**: `echo 'Not implemented yet.'`

**Implementation Plan**:
```bash
# Create script: agent_messaging/scripts/check_livekit_status.sh
#!/bin/bash
# Check if LiveKit server running
# Query API for status
# Check active rooms
# Display connection info
```

**Action Update**:
```json
"action": "bash ../agent_messaging/scripts/check_livekit_status.sh",
"working_directory": "/home/adamsl/planner/smart_menu"
```

**Success Criteria**:
- [ ] Shows server status
- [ ] Lists active rooms
- [ ] Displays connections
- [ ] API health check

**Testing**: Run with LiveKit running

---

## Implementation Tracking

### Progress Checklist

#### TIER 1: Foundation
- [ ] Category 1: PostgreSQL Setup (0/4 complete)
  - [ ] 1.1 Initialize PostgreSQL Database
  - [ ] 1.2 Check PostgreSQL Connection
  - [ ] 1.3 Reset Database
  - [ ] 1.4 View Database Schema

- [ ] Category 2: Letta Server Admin (0/4 complete)
  - [ ] 2.1 Initialize Letta Database
  - [ ] 2.2 Start Letta Server
  - [ ] 2.3 Check Letta Server Status
  - [ ] 2.4 Stop Letta Server

**TIER 1 Status**: 0/8 items complete (0%)

#### TIER 2: Core Services
- [ ] Category 3: Basic Agent Communication Tests (0/4 complete)
  - [ ] 3.1 Test Agent Discovery
  - [ ] 3.2 Test Message Transport
  - [ ] 3.3 Test Agent Delegation
  - [ ] 3.4 Test Memory Backend

- [ ] Category 4: Orchestrator Agent Setup (0/4 complete)
  - [ ] 4.1 Start Orchestrator Agent
  - [ ] 4.2 Load Agent Card
  - [ ] 4.3 Test Routing Logic
  - [ ] 4.4 Check Agent Registry

- [ ] Category 5: Memory Systems (0/4 complete)
  - [ ] 5.1 Test ChromaDB Memory
  - [ ] 5.2 Test Letta Memory Backend
  - [ ] 5.3 Reset Memory Storage
  - [ ] 5.4 View Memory Stats

- [ ] Category 6: WebSocket & Transport (0/4 complete)
  - [ ] 6.1 Test WebSocket Connection
  - [ ] 6.2 Test Transport Factory
  - [ ] 6.3 Test Fallback Mechanisms
  - [ ] 6.4 Verify Message Routing

**TIER 2 Status**: 0/16 items complete (0%)

#### TIER 3: Enhanced Features
- [ ] Category 7: Dashboard & UI Setup (0/4 complete)
  - [ ] 7.1 Start Dashboard Server
  - [ ] 7.2 Build Dashboard Assets
  - [ ] 7.3 Test Dashboard Connectivity
  - [ ] 7.4 Open Dashboard in Browser

- [ ] Category 8: Service Management (0/4 complete)
  - [ ] 8.1 Start All Services
  - [ ] 8.2 Stop All Services
  - [ ] 8.3 View Service Status
  - [ ] 8.4 View Service Logs

- [ ] Category 9: LiveKit Integration (0/4 complete)
  - [ ] 9.1 Initialize LiveKit Server
  - [ ] 9.2 Test Voice Communication
  - [ ] 9.3 Start Voice Agent
  - [ ] 9.4 Check LiveKit Status

**TIER 3 Status**: 0/12 items complete (0%)

**OVERALL STATUS**: 0/36 items complete (0%)

---

## Development Workflow

### For Each Menu Item:

1. **Read the roadmap section** for the item you're implementing
2. **Review source references** from `a2a_communicating_agents`
3. **Create the implementation** (script or test file)
4. **Test the implementation** following success criteria
5. **Update menu config.json** with the actual action
6. **Test via smart menu** to verify it works
7. **Mark item complete** in this roadmap
8. **Commit changes** to git
9. **Update overall progress** percentage

### File Structure to Create:

```
agent_messaging/
├── scripts/
│   ├── init_postgresql.sh
│   ├── check_postgresql.sh
│   ├── reset_postgresql.sh
│   ├── view_postgresql_schema.sh
│   ├── init_letta_db.py
│   ├── start_letta_server.sh
│   ├── check_letta_status.sh
│   ├── stop_letta_server.sh
│   ├── start_orchestrator.sh
│   ├── load_agent_card.py
│   ├── check_agent_registry.py
│   ├── reset_memory.sh
│   ├── view_memory_stats.py
│   ├── start_dashboard.sh
│   ├── build_dashboard.sh
│   ├── open_dashboard.sh
│   ├── start_all_services.sh
│   ├── stop_all_services.sh
│   ├── view_service_status.sh
│   ├── view_service_logs.sh
│   ├── init_livekit.sh
│   ├── start_voice_agent.sh
│   └── check_livekit_status.sh
│
└── tests/
    ├── test_agent_discovery.py
    ├── test_message_transport.py
    ├── test_agent_delegation.py
    ├── test_memory_backend.py
    ├── test_routing_logic.py
    ├── test_chromadb_memory.py
    ├── test_letta_memory.py
    ├── test_websocket_connection.py
    ├── test_transport_factory.py
    ├── test_transport_fallback.py
    ├── test_message_routing.py
    ├── test_dashboard_connectivity.py
    └── test_voice_communication.py
```

---

## Estimated Timeline

**Assuming 4-6 hours of focused work per day:**

- **Week 1**: TIER 1 - Foundation (PostgreSQL + Letta Server)
- **Week 2**: TIER 2 Part 1 - Agent Communication + Orchestrator
- **Week 3**: TIER 2 Part 2 - Memory + Transport
- **Week 4**: TIER 3 - Dashboard + Service Management + LiveKit

**Total Estimated Effort**: 40-50 hours over 4 weeks

---

## Success Metrics

### TIER 1 Complete When:
- ✅ PostgreSQL database initialized and accessible
- ✅ Letta server can start/stop reliably
- ✅ Database schema visible and correct
- ✅ All health checks passing

### TIER 2 Complete When:
- ✅ Agents can discover each other
- ✅ Messages route correctly between agents
- ✅ Memory systems store and recall data
- ✅ Transport layer robust and tested

### TIER 3 Complete When:
- ✅ Dashboard accessible and functional
- ✅ All services can be managed together
- ✅ Voice integration working (optional)
- ✅ System fully operational

### Overall Project Complete When:
- ✅ All 36 menu items implemented
- ✅ All tests passing
- ✅ Documentation updated
- ✅ agent_messaging at feature parity with a2a_communicating_agents

---

## Notes

- **Create `agent_messaging/scripts/` directory** if it doesn't exist
- **Create `agent_messaging/logs/` directory** for PID files and logs
- **Use virtual environment** from `a2a_communicating_agents` or create new one
- **Test incrementally** - don't wait until end to test
- **Commit frequently** - after each working implementation
- **Update this roadmap** as you complete items
- **Document issues** encountered for future reference

---

**Last Updated**: 2025-12-02
**Status**: Planning Complete - Ready for Implementation
**Next Action**: Begin TIER 1 - Item 1.1 (Initialize PostgreSQL Database)
