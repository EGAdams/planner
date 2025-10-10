@echo off
REM Start Admin Dashboard Server
REM This script starts the admin dashboard in the background

echo Starting Admin Dashboard...

cd /d %~dp0
wsl bash -c "cd /home/adamsl/planner/dashboard && node backend/dist/server.js > /tmp/admin-dashboard.log 2>&1 &"

echo Admin Dashboard started. Access it at http://localhost:3030
echo Logs are available at /tmp/admin-dashboard.log in WSL
