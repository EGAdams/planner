# DEPRECATED - Server Monitor App

This directory contains the **old proxy server** that is **NO LONGER USED**.

## What Happened

The Server Monitor App was originally created as a proxy layer running on port 3000, forwarding requests to the Admin Dashboard Backend on port 3030.

## Current Architecture (After Consolidation)

The **Admin Dashboard Backend** now runs directly on port 3000 and serves everything:
- Process management via ServerOrchestrator
- API endpoints
- Static files
- Server-Sent Events (SSE) for real-time updates

## DO NOT START THIS SERVER

This server-monitor-app directory is kept for historical reference only. The consolidated server in `/dashboard` handles all functionality.

## Startup Script

The startup script `/home/adamsl/planner/start_sys_admin_dash.sh` now only starts the consolidated server on port 3000.

## Migration Date

Consolidated: November 6, 2025
