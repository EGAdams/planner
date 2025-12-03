#!/usr/bin/env python3
"""
Dashboard Operations Agent
Responsible for ensuring the dashboard server is running.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PLANNER_ROOT = Path(__file__).resolve().parents[2]
os.chdir(PLANNER_ROOT)

from a2a_communicating_agents.agent_messaging import inbox, post_message, create_jsonrpc_response  # noqa: E402
from rag_system.core.document_manager import DocumentManager  # noqa: E402

AGENT_NAME = "dashboard-agent"
DASHBOARD_DIR = PLANNER_ROOT / "dashboard"
DASHBOARD_LOG = PLANNER_ROOT / "dashboard-startup.log"
PORT = int(os.environ.get("ADMIN_PORT", "3000"))
BOOTSTRAP_GRACE_SECONDS = max(0, int(os.environ.get("OPS_AGENT_BOOTSTRAP_GRACE", "5")))
CREATE_FLAGS = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0


def check_server_status() -> bool:
    """Check if the server is running on the expected port."""
    try:
        response = requests.get(f"http://localhost:{PORT}", timeout=2)
        return response.status_code == 200
    except requests.ConnectionError:
        return False


def _resolve_dashboard_command() -> list[str]:
    npm_path = shutil.which("npm")
    if not npm_path:
        raise RuntimeError("Unable to find `npm` on PATH. Install Node.js to start the dashboard.")
    return [npm_path, "start"]


def start_server() -> Tuple[bool, str]:
    """Start the dashboard server."""
    print(f"[{AGENT_NAME}] Starting dashboard server...")

    dm = DocumentManager()
    dm.add_runtime_artifact(
        artifact_text=f"Attempting to start dashboard server on port {PORT}",
        artifact_type="runlog",
        source=AGENT_NAME,
        project_name="dashboard",
    )

    try:
        # Start dev servers
        dev_server_script = PLANNER_ROOT / "scripts" / "start_dev_servers.py"
        if dev_server_script.exists():
            print(f"[{AGENT_NAME}] Starting dev servers...")
            subprocess.Popen(
                [sys.executable, str(dev_server_script), "--mode", "windows"],
                cwd=str(PLANNER_ROOT),
                creationflags=CREATE_FLAGS,
            )
        else:
            print(f"[{AGENT_NAME}] Warning: Could not find start_dev_servers.py at {dev_server_script}")

        cmd = _resolve_dashboard_command()
        dashboard_env = os.environ.copy()
        dashboard_env.setdefault("ADMIN_PORT", str(PORT))

        DASHBOARD_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DASHBOARD_LOG, "a", encoding="utf-8") as log_handle:
            subprocess.Popen(
                cmd,
                cwd=str(DASHBOARD_DIR),
                env=dashboard_env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=CREATE_FLAGS,
            )

        time.sleep(5)

        if check_server_status():
            msg = "Dashboard server started successfully."
            print(f"[{AGENT_NAME}] {msg}")
            dm.log_deployment(
                action="start",
                details="Dashboard server started automatically by ops agent",
                environment="development",
                project_name="dashboard",
            )
            return True, msg

        msg = "Failed to verify server startup."
        print(f"[{AGENT_NAME}] {msg}")
        dm.add_runtime_artifact(
            artifact_text=f"Server startup failed. Check logs at {DASHBOARD_LOG}",
            artifact_type="error",
            source=AGENT_NAME,
            project_name="dashboard",
        )
        return False, msg
    except Exception as exc:  # pragma: no cover - defensive logging
        return False, str(exc)


def _detect_browser_binary() -> Optional[str]:
    candidates = [
        "google-chrome",
        "chromium-browser",
        "chromium",
        "chrome",
        "msedge",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        path_candidate = Path(candidate)
        if path_candidate.exists():
            return str(path_candidate)
    return None


def start_test_browser(url: Optional[str] = None, headless: bool = False):
    """Launch a browser to test the dashboard."""
    if url is None:
        url = f"http://localhost:{PORT}"

    print(f"[{AGENT_NAME}] Launching test browser for {url}...")

    dm = DocumentManager()
    dm.add_runtime_artifact(
        artifact_text=f"Launching test browser: url={url}, headless={headless}",
        artifact_type="runlog",
        source=AGENT_NAME,
        project_name="dashboard",
    )

    try:
        browser_path = _detect_browser_binary()
        if not browser_path:
            msg = "No suitable browser found. Please install Chrome or Chromium."
            print(f"[{AGENT_NAME}] {msg}")
            dm.add_runtime_artifact(
                artifact_text=msg,
                artifact_type="error",
                source=AGENT_NAME,
                project_name="dashboard",
            )
            return False, msg, None

        cmd = [browser_path]
        if headless:
            cmd.extend(["--headless", "--disable-gpu"])
        cmd.extend(
            [
                "--new-window",
                "--no-first-run",
                "--no-default-browser-check",
                url,
            ]
        )

        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        msg = f"Browser launched successfully (PID: {process.pid})"
        print(f"[{AGENT_NAME}] {msg}")
        dm.add_runtime_artifact(
            artifact_text=f"Test browser launched: {browser_path} -> {url} (PID: {process.pid})",
            artifact_type="runlog",
            source=AGENT_NAME,
            project_name="dashboard",
        )
        return True, msg, process.pid
    except Exception as exc:  # pragma: no cover - defensive logging
        msg = f"Failed to launch browser: {exc}"
        print(f"[{AGENT_NAME}] {msg}")
        dm.add_runtime_artifact(
            artifact_text=msg,
            artifact_type="error",
            source=AGENT_NAME,
            project_name="dashboard",
        )
        return False, msg, None


def run_agent_loop():
    """Main agent loop."""
    print(f"[{AGENT_NAME}] Agent started. Listening on topic 'ops'...")

    if check_server_status():
        print(f"[{AGENT_NAME}] Server is already running.")
    else:
        if BOOTSTRAP_GRACE_SECONDS:
            print(f"[{AGENT_NAME}] Server not running. Waiting {BOOTSTRAP_GRACE_SECONDS}s for bootstrap...")
            time.sleep(BOOTSTRAP_GRACE_SECONDS)
        if not check_server_status():
            print(f"[{AGENT_NAME}] Server still down after grace period. Starting now...")
            start_server()
        else:
            print(f"[{AGENT_NAME}] Server became healthy during grace window.")

    while True:
        messages = inbox("ops", limit=5)
        for msg in messages:
            try:
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
                        response = create_jsonrpc_response(
                            {"status": "running" if is_running else "stopped", "port": PORT},
                            req_id,
                        )
                        post_message(message=response, topic="ops", from_agent=AGENT_NAME)
                    elif "start" in task_desc:
                        if check_server_status():
                            result = {"success": True, "message": "Already running"}
                        else:
                            success, status_msg = start_server()
                            result = {"success": success, "message": status_msg}
                        response = create_jsonrpc_response(result, req_id)
                        post_message(message=response, topic="ops", from_agent=AGENT_NAME)
            except Exception:
                # Avoid crashing the loop on malformed inbox entries.
                continue

        time.sleep(10)


if __name__ == "__main__":
    run_agent_loop()
