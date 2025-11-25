# Quick Start: Static Admin Page

## Open the Static Administration Page

The static admin page can be opened directly in any web browser without starting any servers.

### Option 1: Direct File Access (Recommended)
```bash
# Open with default browser (Linux/WSL2)
xdg-open /home/adamsl/planner/sys_admin_static.html

# Or copy path and paste in browser address bar:
file:///home/adamsl/planner/sys_admin_static.html
```

### Option 2: From Windows (WSL2)
```
1. Open File Explorer
2. Navigate to: \\wsl$\Ubuntu\home\adamsl\planner
3. Double-click: sys_admin_static.html
```

### Option 3: Copy to Desktop
```bash
# Copy to Windows Desktop (if in WSL2)
cp /home/adamsl/planner/sys_admin_static.html /mnt/c/Users/*/Desktop/

# Then double-click the file on your desktop
```

## What's Included

The static page shows:
- System status and configuration
- Python version blocker details
- Database initialization status
- Resolution steps with commands
- Diagnostic information
- File locations
- Next actions

## Features

- No server required (fully offline)
- No network dependencies
- Embedded diagnostic data
- Copy-paste ready commands
- Complete troubleshooting guide

## Note

This page is **static** - it contains snapshot data from when it was created (2025-11-24). For real-time server health checks, use the dynamic version (`sys_admin_debug.html`) after starting servers.
