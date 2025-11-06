# Server Consolidation Handoff

## Summary

The initial goal was to consolidate two applications running on `localhost:3000` and `localhost:3030` into a single, functional application. The user prefers the "Server Monitor Dashboard" running on port 3000, which was correctly detecting the "LiveKit Voice Agent" and the "Pydantic Web Server".

## Current Situation

- The "System Administration Dashboard" is running on `localhost:3030`.
- The "Server Monitor Dashboard" on `localhost:3000` is **not** currently running, despite the `start-dashboard.sh` script attempting to start it.
- The `dashboard-startup.log` file indicates that the `server-monitor-app` (port 3000) is being started, but it is not staying active.
- The log file also shows that the `livekit-voice-agent` and `pydantic-web-server` are dying unexpectedly. This may be related to the `livekit-server` not running.

## What Was Done

1.  **Initial Investigation:** The `start-dashboard.sh` script was identified as the source of the two running applications.
2.  **First Change (Reverted):** The `start-dashboard.sh` script was modified to only start the server on port 3030. This was reverted after the user clarified that the server on port 3000 was the preferred one.
3.  **Configuration Change:** The `livekit-server` was uncommented in the `SERVER_REGISTRY` in `/home/adamsl/planner/dashboard/backend/server.ts`. This was done to address the issue of the "System Administration Dashboard" not detecting any servers.

## Next Steps

1.  **Diagnose the `server-monitor-app`:** Determine why the "Server Monitor App" on port 3000 is not staying running. Check for any errors in the application's own logs, if available.
2.  **Investigate `livekit-server`:** The `livekit-server` is referenced in the backend configuration but may not be running. The `livekit-voice-agent` and `pydantic-web-server` may have a dependency on it, causing them to fail.
3.  **Consolidate Frontends:** Once both servers are stable, the final goal is to have a single, working dashboard. This may involve consolidating the frontends of the "Server Monitor Dashboard" and the "System Administration Dashboard".

## Relevant Files

-   `/home/adamsl/planner/start-dashboard.sh`: The script that starts both servers.
-   `/home/adamsl/planner/dashboard/backend/server.ts`: The backend configuration for the "System Administration Dashboard" on port 3030.
-   `/home/adamsl/planner/server-monitor-app/server.js`: The server for the "Server Monitor App" on port 3000.
-   `/home/adamsl/planner/dashboard-startup.log`: The log file for the `start-dashboard.sh` script.
