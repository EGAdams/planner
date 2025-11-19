#!/usr/bin/env python3
"""
Dashboard Operations Agent
Responsible for ensuring the dashboard server is running.
"""

import sys
import os
import time
import json
import subprocess
import requests
from datetime import datetime

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_messaging import inbox, send, post_message, create_jsonrpc_response
from rag_system.core.document_manager import DocumentManager

AGENT_NAME = "dashboard-ops-agent"
DASHBOARD_DIR = "/home/adamsl/planner/dashboard"
PORT = 3000

def check_server_status():
    """Check if the server is running on the expected port"""
    try:
        response = requests.get(f"http://localhost:{PORT}", timeout=2)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def start_server():
    """Start the dashboard server"""
    print(f"[{AGENT_NAME}] Starting dashboard server...")
    
    # Log intention to memory
    dm = DocumentManager()
    dm.add_runtime_artifact(
        artifact_text="Attempting to start dashboard server on port 3000",
        artifact_type="runlog",
        source=AGENT_NAME,
        project_name="dashboard"
    )
    
    try:
        # Use the existing startup script logic but directly in python for better control
        # or just execute the shell command
        cmd = f"cd {DASHBOARD_DIR} && env ADMIN_PORT={PORT} nohup npm start > /home/adamsl/planner/dashboard-startup.log 2>&1 &"
        subprocess.Popen(cmd, shell=True)
        
        # Wait for startup
        time.sleep(5)
        
        if check_server_status():
            msg = "Dashboard server started successfully."
            print(f"[{AGENT_NAME}] {msg}")
            
            # Log success to memory
            dm.log_deployment(
                action="start",
                details="Dashboard server started automatically by ops agent",
                environment="development",
                project_name="dashboard"
            )
            return True, msg
        else:
            msg = "Failed to verify server startup."
            print(f"[{AGENT_NAME}] {msg}")
            
            # Log failure
            dm.add_runtime_artifact(
                artifact_text=f"Server startup failed. Check logs at {DASHBOARD_DIR}/dashboard-startup.log",
                artifact_type="error",
                source=AGENT_NAME,
                project_name="dashboard"
            )
            return False, msg
            
    except Exception as e:
        return False, str(e)

def start_test_browser(url=None, headless=False):
    """Launch a browser to test the dashboard"""
    if url is None:
        url = f"http://localhost:{PORT}"
    
    print(f"[{AGENT_NAME}] Launching test browser for {url}...")
    
    # Log intention to memory
    dm = DocumentManager()
    dm.add_runtime_artifact(
        artifact_text=f"Launching test browser: url={url}, headless={headless}",
        artifact_type="runlog",
        source=AGENT_NAME,
        project_name="dashboard"
    )
    
    try:
        # Detect browser (prefer Chrome/Chromium)
        browser_candidates = [
            "google-chrome",
            "chromium-browser", 
            "chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]
        
        browser_path = None
        for candidate in browser_candidates:
            try:
                result = subprocess.run(["which", candidate], capture_output=True, text=True)
                if result.returncode == 0:
                    browser_path = result.stdout.strip()
                    break
            except:
                continue
        
        if not browser_path:
            msg = "No suitable browser found. Please install Chrome or Chromium."
            print(f"[{AGENT_NAME}] {msg}")
            dm.add_runtime_artifact(
                artifact_text=msg,
                artifact_type="error",
                source=AGENT_NAME,
                project_name="dashboard"
            )
            return False, msg, None
        
        # Build browser command
        cmd = [browser_path]
        if headless:
            cmd.extend(["--headless", "--disable-gpu"])
        cmd.extend([
            "--new-window",
            "--no-first-run",
            "--no-default-browser-check",
            url
        ])
        
        # Launch browser
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        msg = f"Browser launched successfully (PID: {process.pid})"
        print(f"[{AGENT_NAME}] {msg}")
        
        # Log success
        dm.add_runtime_artifact(
            artifact_text=f"Test browser launched: {browser_path} -> {url} (PID: {process.pid})",
            artifact_type="runlog",
            source=AGENT_NAME,
            project_name="dashboard"
        )
        
        return True, msg, process.pid
        
    except Exception as e:
        msg = f"Failed to launch browser: {str(e)}"
        print(f"[{AGENT_NAME}] {msg}")
        dm.add_runtime_artifact(
            artifact_text=msg,
            artifact_type="error",
            source=AGENT_NAME,
            project_name="dashboard"
        )
        return False, msg, None


def run_agent_loop():
    """Main agent loop"""
    print(f"[{AGENT_NAME}] Agent started. Listening on topic 'ops'...")
    
    # Initial check
    if not check_server_status():
        print(f"[{AGENT_NAME}] Server not running on startup. Starting now...")
        start_server()
    else:
        print(f"[{AGENT_NAME}] Server is already running.")

    while True:
        # Check inbox for tasks
        messages = inbox("ops", limit=5)
        
        for msg in messages:
            try:
                # Parse JSON-RPC message
                # Note: In a real implementation we would track processed IDs to avoid duplicates
                # For this demo, we'll assume the inbox handles unread or we just process latest
                
                # Extract content if it's wrapped in the A2A markdown format
                content = msg.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                
                data = json.loads(content)
                
                if data.get("jsonrpc") != "2.0":
                    continue
                    
                method = data.get("method")
                params = data.get("params", {})
                req_id = data.get("id")
                
                if method == "agent.execute_task":
                    task_desc = params.get("description", "").lower()
                    
                    if "status" in task_desc or "check" in task_desc:
                        is_running = check_server_status()
                        response = create_jsonrpc_response({
                            "status": "running" if is_running else "stopped",
                            "port": PORT
                        }, req_id)
                        
                        post_message(
                            message=response,
                            topic="ops",
                            from_agent=AGENT_NAME
                        )
                        
                    elif "start" in task_desc:
                        if check_server_status():
                            result = {"success": True, "message": "Already running"}
                        else:
                            success, msg = start_server()
                            result = {"success": success, "message": msg}
                            
                        response = create_jsonrpc_response(result, req_id)
                        post_message(
                            message=response,
                            topic="ops",
                            from_agent=AGENT_NAME
                        )
                        
            except Exception as e:
                # print(f"Error processing message: {e}")
                pass
        
        # Sleep before next check
        time.sleep(10)

if __name__ == "__main__":
    run_agent_loop()
