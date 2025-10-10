# PowerShell script to start Admin Dashboard
# Can be used with Windows Task Scheduler for auto-start

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$wslPath = "/home/adamsl/planner/dashboard"

Write-Host "Starting Admin Dashboard..." -ForegroundColor Green

# Start the dashboard server in WSL
Start-Process wsl -ArgumentList "bash", "-c", "cd $wslPath && node backend/dist/server.js > /tmp/admin-dashboard.log 2>&1 &" -WindowStyle Hidden

Write-Host "Admin Dashboard started." -ForegroundColor Green
Write-Host "Access it at http://localhost:3030" -ForegroundColor Cyan
Write-Host "Logs: /tmp/admin-dashboard.log in WSL" -ForegroundColor Yellow
