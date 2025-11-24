
# A2A Agent System Startup Script (Windows PowerShell)
# Starts Letta Server, Orchestrator Agent, Dashboard Ops Agent, and System Admin Dashboard

$ErrorActionPreference = "Stop"

$PLANNER_ROOT = "C:\Users\NewUser\Desktop\blue_time\planner"
$LOG_DIR = "$PLANNER_ROOT\logs"
$PIDS_FILE = "$LOG_DIR\a2a_system.pids"

# Create logs directory
if (-not (Test-Path -Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR | Out-Null
}

# Function to log info
function Log-Info {
    param([string]$message)
    Write-Host "[A2A System] $message" -ForegroundColor Green
}

# Function to log warning
function Log-Warn {
    param([string]$message)
    Write-Host "[A2A System] $message" -ForegroundColor Yellow
}

# Function to log error
function Log-Error {
    param([string]$message)
    Write-Host "[A2A System] $message" -ForegroundColor Red
}

# Clean up old PID file
if (Test-Path -Path $PIDS_FILE) {
    Remove-Item -Path $PIDS_FILE
}
New-Item -ItemType File -Path $PIDS_FILE | Out-Null

Log-Info "Starting A2A Agent System..."
Log-Info "Agent Cards (agent.json) location: $PLANNER_ROOT\<agent>\"
Write-Host ""

# ========================================
# 1. Start Letta Server (Unified Memory)
# ========================================
Log-Info "Step 1/4: Starting Letta Server (Unified Memory Backend)..."

# Check if port 8283 is in use
$port8283 = Get-NetTCPConnection -LocalPort 8283 -ErrorAction SilentlyContinue
if ($port8283) {
    Log-Warn "Letta server already running on port 8283"
}
else {
    $lettaProcess = Start-Process -FilePath "letta" -ArgumentList "server" -RedirectStandardOutput "$LOG_DIR\letta.log" -RedirectStandardError "$LOG_DIR\letta.err.log" -PassThru -NoNewWindow
    "letta:$($lettaProcess.Id)" | Out-File -FilePath $PIDS_FILE -Append -Encoding ascii
    Log-Info "Letta server started (PID: $($lettaProcess.Id))"
    Start-Sleep -Seconds 5
}

# Verify Letta is running
$port8283 = Get-NetTCPConnection -LocalPort 8283 -ErrorAction SilentlyContinue
if ($port8283) {
    Log-Info "✓ Letta server is running on port 8283"
}
else {
    Log-Error "✗ Letta server failed to start. Check $LOG_DIR\letta.log"
}
Write-Host ""

# ========================================
# 2. Start Orchestrator Agent
# ========================================
Log-Info "Step 2/4: Starting Orchestrator Agent..."
Log-Info "Agent Card: $PLANNER_ROOT\orchestrator_agent\agent.json"

$orchestratorProcess = Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory "$PLANNER_ROOT\orchestrator_agent" -RedirectStandardOutput "$LOG_DIR\orchestrator.log" -RedirectStandardError "$LOG_DIR\orchestrator.err.log" -PassThru -NoNewWindow
"orchestrator:$($orchestratorProcess.Id)" | Out-File -FilePath $PIDS_FILE -Append -Encoding ascii
Log-Info "Orchestrator agent started (PID: $($orchestratorProcess.Id))"
Log-Info "  - Capabilities: route_request, discover_agents"
Log-Info "  - Topics: orchestrator, general"
Start-Sleep -Seconds 2
Write-Host ""

# ========================================
# 3. Start Dashboard Ops Agent
# ========================================
Log-Info "Step 3/4: Starting Dashboard Ops Agent..."
Log-Info "Agent Card: $PLANNER_ROOT\dashboard_ops_agent\agent.json"

$dashboardOpsProcess = Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory "$PLANNER_ROOT\dashboard_ops_agent" -RedirectStandardOutput "$LOG_DIR\dashboard_ops.log" -RedirectStandardError "$LOG_DIR\dashboard_ops.err.log" -PassThru -NoNewWindow
"dashboard_ops:$($dashboardOpsProcess.Id)" | Out-File -FilePath $PIDS_FILE -Append -Encoding ascii
Log-Info "Dashboard Ops agent started (PID: $($dashboardOpsProcess.Id))"
Log-Info "  - Capabilities: check_status, start_server, start_test_browser"
Log-Info "  - Topics: ops, dashboard, maintenance"
Start-Sleep -Seconds 2
Write-Host ""

# ========================================
# 4. Start System Admin Dashboard
# ========================================
Log-Info "Step 4/4: Starting System Admin Dashboard..."

# Check if port 3000 is in use
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Log-Warn "Dashboard already running on port 3000"
}
else {
    $env:ADMIN_PORT = "3000"
    $dashboardProcess = Start-Process -FilePath "npm" -ArgumentList "start" -WorkingDirectory "$PLANNER_ROOT\dashboard" -RedirectStandardOutput "$LOG_DIR\dashboard.log" -RedirectStandardError "$LOG_DIR\dashboard.err.log" -PassThru -NoNewWindow
    "dashboard:$($dashboardProcess.Id)" | Out-File -FilePath $PIDS_FILE -Append -Encoding ascii
    Log-Info "Dashboard started (PID: $($dashboardProcess.Id))"
    Start-Sleep -Seconds 5
}

# Verify Dashboard is running
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Log-Info "✓ Dashboard is running on port 3000"
}
else {
    Log-Error "✗ Dashboard failed to start. Check $LOG_DIR\dashboard.log"
}
Write-Host ""

# ========================================
# Summary
# ========================================
Log-Info "========================================="
Log-Info "A2A Agent System Status:"
Log-Info "========================================="
Log-Info "Letta Server:       http://localhost:8283"
Log-Info "System Dashboard:   http://localhost:3000"
Log-Info ""
Log-Info "Active A2A Agents:"
if ($orchestratorProcess) { Log-Info "  - orchestrator-agent    (PID: $($orchestratorProcess.Id))" }
if ($dashboardOpsProcess) { Log-Info "  - dashboard-ops-agent   (PID: $($dashboardOpsProcess.Id))" }
Log-Info ""
Log-Info "Logs: $LOG_DIR"
Log-Info "PIDs: $PIDS_FILE"
Log-Info ""
Log-Info "To stop all services, run: Stop-Process -Id <PID>"
Log-Info "========================================="
Write-Host ""
Log-Info "Opening dashboard in browser..."
Start-Sleep -Seconds 2

# Open browser
Start-Process "http://localhost:3000"
Log-Info "A2A Agent System startup complete!"
