# Planner - System Administration Dashboard

A comprehensive system administration dashboard for managing multiple servers and services across your development environment.

## 🎯 Quick Start

### Automated Startup
```bash
/home/adamsl/planner/start_sys_admin_dash.sh
```

### Manual Startup
```bash
cd /home/adamsl/planner/dashboard
env ADMIN_PORT=3000 npm start
```

### Cross-Platform Launcher (Windows or WSL)
Use the helper script to boot every service (Letta, orchestrator, dashboard agents, dashboard UI, and the expense categorizer API) with one command:

```powershell
python scripts/start_dev_servers.py --mode windows
```

The script keeps the servers attached to the current terminal—press `Ctrl+C` to stop everything cleanly.  
Pass `--mode wsl` (plus `--wsl-root /home/adamsl/planner` if needed) to keep using the old WSL stack, or `--standalone-letta` when you want a second dedicated `./letta server` instance just like the legacy workflow.

On Windows, the launcher will automatically install Python (pip) dependencies, build the dashboard backend (`npm install && npm run build`), and cache a `.windows_python_bootstrap` sentinel so subsequent runs start immediately.  
Use `--skip-bootstrap` to manage dependencies yourself, or `--force-bootstrap` if you need to reinstall packages after an upgrade.

### Access Dashboard
- **URL**: http://localhost:3000
- **Dashboard Port**: 3000 (consolidated, stable)

## 📋 What's Included

### System Administration Dashboard
- Real-time server monitoring and management
- Process orchestration for managed services
- Server-Sent Events (SSE) for live updates
- RESTful API for server control
- Health checks and status monitoring

### Managed Services
The dashboard controls three main services:

1. **LiveKit Server** (ports 7880, 7881)
   - Real-time media server for voice/video communication
   - Location: `/home/adamsl/ottomator-agents/livekit-agent`

2. **LiveKit Voice Agent** (dynamic ports)
   - Voice interaction agent powered by LiveKit
   - Location: `/home/adamsl/ottomator-agents/livekit-agent`

3. **Pydantic Web Server** (port 8001)
   - Pydantic AI agent web endpoint
   - Location: `/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version`

## 🚀 Features

- **Single Port Architecture**: Consolidated from dual-port setup for stability
- **Process Management**: Start/stop/restart managed services via API
- **Real-time Monitoring**: Live status updates using Server-Sent Events
- **Health Checks**: Automatic health monitoring for all services
- **Process State Persistence**: Maintains service state across restarts
- **Responsive UI**: Works on desktop and mobile browsers

## 🔧 Core Technologies

- **Backend**: TypeScript, Node.js, Express
- **Frontend**: HTML5, CSS3, JavaScript
- **Process Management**: ServerOrchestrator, ProcessManager, ProcessMonitor
- **Testing**: Jest (TDD validated)
- **Communication**: Server-Sent Events (SSE)

## 📊 Project Structure

```
planner/
├── dashboard/
│   ├── backend/
│   │   ├── server.ts              # Main backend server
│   │   ├── services/              # Business logic modules
│   │   ├── __tests__/             # Jest test suite
│   │   └── dist/                  # Compiled output
│   ├── public/                    # Frontend assets
│   ├── package.json              # Dependencies
│   └── .env                       # Port configuration
├── start_sys_admin_dash.sh        # Automated startup script
├── start-dashboard.bat            # Windows startup batch file
├── dashboard-startup.log          # Startup logs
└── CLAUDE.md                      # Development instructions
```

## ✅ Architecture Status

**Single Server Architecture**: ✅ Complete
- Port 3000: Main consolidated server (ACTIVE)
- Port 3030: Deprecated (no longer used)
- Test coverage: 8/8 passing (100%)
- Stability: Production-ready

## 🛠️ Configuration

### Environment Variables
```bash
ADMIN_PORT=3000          # Dashboard port (default)
NODE_ENV=production      # Environment mode
```

### Port Configuration
- Dashboard: `3000` (consolidated)
- LiveKit: `7880, 7881`
- Pydantic: `8001`

All ports are explicitly configured in `start_sys_admin_dash.sh` to prevent conflicts with system environment variables.

## 🐛 Troubleshooting

### Server Won't Start
1. Check port 3000 is available: `lsof -i :3000`
2. Kill conflicting process: `kill -9 <PID>`
3. Check logs: `cat dashboard-startup.log`

### Managed Services Not Starting
1. Verify service directories exist
2. Check required dependencies (livekit-server, Python venv)
3. Review ProcessOrchestrator configuration in `server.ts`

### Environment Variable Override
If server still binds to port 3030:
```bash
unset ADMIN_PORT
export ADMIN_PORT=3000
```

## 📚 Documentation

- **SERVER_ARCHITECTURE.md**: Technical architecture, server consolidation details
- **PROCESS_MANAGEMENT_STRATEGY.md**: Process management, startup automation, troubleshooting

## 🚀 Next Steps

1. Run startup script and verify dashboard loads
2. Test managed service start/stop via dashboard UI
3. Monitor logs for any errors
4. Consider systemd service for production deployment

---

**Status**: Production Ready
**Last Updated**: November 6, 2025
**Port**: 3000 (Consolidated & Stable)
