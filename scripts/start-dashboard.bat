@echo off
REM Windows batch file to start Dashboard in WSL2
REM Place this in your Windows Startup folder

wsl -d Ubuntu -u adamsl /home/adamsl/planner/start-dashboard.sh

REM Optional: Open browser after 10 seconds
timeout /t 10 /nobreak > nul
start http://localhost:3000
