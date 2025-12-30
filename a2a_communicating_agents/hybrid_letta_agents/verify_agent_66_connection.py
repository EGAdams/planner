#!/usr/bin/env python3
"""
Agent_66 Voice Connection Verification Script

This script verifies that the voice system is correctly configured to use Agent_66.
It checks all 7 failure points identified in the analysis and provides actionable fixes.

Usage:
    python3 verify_agent_66_connection.py
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import urllib.request
import urllib.error

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Expected Agent_66 configuration
EXPECTED_AGENT_NAME = "Agent_66"
EXPECTED_AGENT_ID_ENV = os.getenv("VOICE_PRIMARY_AGENT_ID")

class VerificationResult:
    def __init__(self, check_name: str):
        self.check_name = check_name
        self.passed = False
        self.message = ""
        self.fix_command = ""
        self.details = []

    def pass_check(self, message: str = "OK", details: List[str] = None):
        self.passed = True
        self.message = message
        self.details = details or []

    def fail_check(self, message: str, fix_command: str = "", details: List[str] = None):
        self.passed = False
        self.message = message
        self.fix_command = fix_command
        self.details = details or []

    def __str__(self):
        status = f"{GREEN}✓ PASS{RESET}" if self.passed else f"{RED}✗ FAIL{RESET}"
        output = f"{status} {BOLD}{self.check_name}{RESET}\n"
        output += f"  {self.message}\n"

        if self.details:
            for detail in self.details:
                output += f"    • {detail}\n"

        if not self.passed and self.fix_command:
            output += f"  {YELLOW}Fix:{RESET} {self.fix_command}\n"

        return output

def check_environment_variables() -> VerificationResult:
    """Check if Agent_66 environment variables are set correctly."""
    result = VerificationResult("Environment Variables")

    agent_id = os.getenv("VOICE_PRIMARY_AGENT_ID")
    agent_name = os.getenv("VOICE_PRIMARY_AGENT_NAME")
    hybrid_mode = os.getenv("USE_HYBRID_STREAMING", "true")

    issues = []
    details = []

    if not agent_id:
        issues.append("VOICE_PRIMARY_AGENT_ID not set")
    else:
        details.append(f"VOICE_PRIMARY_AGENT_ID: {agent_id}")

    if not agent_name:
        issues.append("VOICE_PRIMARY_AGENT_NAME not set")
    elif agent_name != EXPECTED_AGENT_NAME:
        issues.append(f"VOICE_PRIMARY_AGENT_NAME is '{agent_name}' (expected '{EXPECTED_AGENT_NAME}')")
    else:
        details.append(f"VOICE_PRIMARY_AGENT_NAME: {agent_name}")

    details.append(f"USE_HYBRID_STREAMING: {hybrid_mode}")

    if issues:
        result.fail_check(
            f"Missing or incorrect environment variables: {', '.join(issues)}",
            "Add to /home/adamsl/planner/.env:\n" +
            "    VOICE_PRIMARY_AGENT_ID=agent-4dfca708-49a8-4982-8e36-0f1146f9a66e\n" +
            "    VOICE_PRIMARY_AGENT_NAME=Agent_66\n" +
            "    USE_HYBRID_STREAMING=true",
            details
        )
    else:
        result.pass_check("Environment variables correctly configured", details)

    return result

def check_postgresql() -> VerificationResult:
    """Check if PostgreSQL is running."""
    result = VerificationResult("PostgreSQL Database")

    try:
        exit_code = subprocess.call(
            ['pg_isready', '-q'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if exit_code == 0:
            result.pass_check("PostgreSQL is running and accepting connections")
        else:
            result.fail_check(
                "PostgreSQL is not accepting connections",
                "sudo service postgresql start"
            )
    except FileNotFoundError:
        result.fail_check(
            "PostgreSQL client tools not found (pg_isready)",
            "Install PostgreSQL: sudo apt-get install postgresql-client"
        )
    except Exception as e:
        result.fail_check(f"Error checking PostgreSQL: {e}")

    return result

def check_letta_server() -> VerificationResult:
    """Check if Letta server is running and Agent_66 exists."""
    result = VerificationResult("Letta Server & Agent_66")

    try:
        # Check health endpoint
        req = urllib.request.Request("http://localhost:8283/admin/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                result.fail_check(
                    f"Letta server returned status {response.status}",
                    "cd /home/adamsl/planner && ./start_letta_dec_09_2025.sh"
                )
                return result

        # Check agents endpoint and look for Agent_66
        req = urllib.request.Request("http://localhost:8283/v1/agents/")
        with urllib.request.urlopen(req, timeout=5) as response:
            agents = json.loads(response.read().decode())

        agent_66 = None
        for agent in agents:
            if agent.get('name') == EXPECTED_AGENT_NAME:
                agent_66 = agent
                break

        if not agent_66:
            result.fail_check(
                f"{EXPECTED_AGENT_NAME} not found in Letta database",
                "Create Agent_66 using Letta UI or API",
                [f"Found {len(agents)} agents, but none named '{EXPECTED_AGENT_NAME}'"]
            )
        else:
            agent_id = agent_66.get('id')
            created = agent_66.get('created_at', 'unknown')

            details = [
                f"Agent ID: {agent_id}",
                f"Created: {created}",
                f"Total agents: {len(agents)}"
            ]

            # Check if environment matches
            if EXPECTED_AGENT_ID_ENV and agent_id != EXPECTED_AGENT_ID_ENV:
                result.fail_check(
                    f"Agent_66 ID mismatch! Database has {agent_id[:16]}... but env has {EXPECTED_AGENT_ID_ENV[:16]}...",
                    f"Update .env file: VOICE_PRIMARY_AGENT_ID={agent_id}",
                    details
                )
            else:
                result.pass_check("Letta server running and Agent_66 exists", details)

    except urllib.error.URLError as e:
        result.fail_check(
            f"Cannot connect to Letta server: {e.reason}",
            "cd /home/adamsl/planner && ./start_letta_dec_09_2025.sh"
        )
    except Exception as e:
        result.fail_check(f"Error checking Letta: {e}")

    return result

def check_livekit_server() -> VerificationResult:
    """Check if LiveKit server is running."""
    result = VerificationResult("LiveKit Server")

    try:
        req = urllib.request.Request("http://localhost:7880/")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200 or response.status == 404:
                # LiveKit returns 404 for root but server is running
                result.pass_check("LiveKit server is running on port 7880")
            else:
                result.fail_check(
                    f"LiveKit server returned unexpected status {response.status}",
                    "Check LiveKit startup script in /home/adamsl/ottomator-agents/livekit-agent/"
                )
    except urllib.error.URLError:
        result.fail_check(
            "Cannot connect to LiveKit server on port 7880",
            "cd /home/adamsl/ottomator-agents/livekit-agent && ./start_livekit.sh"
        )
    except Exception as e:
        result.fail_check(f"Error checking LiveKit: {e}")

    return result

def check_cors_proxy() -> VerificationResult:
    """Check if CORS proxy server is running."""
    result = VerificationResult("CORS Proxy Server")

    try:
        # Check HTML endpoint
        req = urllib.request.Request("http://localhost:9000/")
        with urllib.request.urlopen(req, timeout=5) as response:
            html_ok = response.status == 200

        # Check API proxy endpoint
        req = urllib.request.Request("http://localhost:9000/api/v1/agents/")
        with urllib.request.urlopen(req, timeout=5) as response:
            api_ok = response.status == 200

        if html_ok and api_ok:
            result.pass_check("CORS proxy running and proxying API correctly")
        else:
            result.fail_check(
                f"CORS proxy partially working (HTML: {html_ok}, API: {api_ok})",
                "cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents && python3 cors_proxy_server.py &"
            )

    except urllib.error.URLError:
        result.fail_check(
            "Cannot connect to CORS proxy on port 9000",
            "cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents && python3 cors_proxy_server.py > /tmp/cors_proxy.log 2>&1 &"
        )
    except Exception as e:
        result.fail_check(f"Error checking CORS proxy: {e}")

    return result

def check_voice_agent_worker() -> VerificationResult:
    """Check if voice agent worker is running."""
    result = VerificationResult("Voice Agent Worker")

    try:
        output = subprocess.check_output(
            ['ps', 'aux'],
            stderr=subprocess.DEVNULL,
            text=True
        )

        # Look for letta_voice_agent_optimized.py process
        lines = output.split('\n')
        agent_processes = [line for line in lines if 'letta_voice_agent_optimized.py' in line and 'grep' not in line]

        if len(agent_processes) == 0:
            result.fail_check(
                "Voice agent worker not running",
                "cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents && " +
                "source /home/adamsl/planner/.venv/bin/activate && " +
                "python3 letta_voice_agent_optimized.py dev > /tmp/voice_agent.log 2>&1 &"
            )
        elif len(agent_processes) == 1:
            # Extract PID
            pid = agent_processes[0].split()[1]
            result.pass_check(f"Voice agent worker running (PID: {pid})")
        else:
            pids = [line.split()[1] for line in agent_processes]
            result.fail_check(
                f"Multiple voice agent workers detected ({len(agent_processes)} processes)",
                f"Kill duplicates: kill {' '.join(pids)}",
                [f"PIDs: {', '.join(pids)}"]
            )

    except Exception as e:
        result.fail_check(f"Error checking voice agent: {e}")

    return result

def check_html_configuration() -> VerificationResult:
    """Check if HTML file has correct agent selection logic."""
    result = VerificationResult("HTML Agent Selection")

    html_file = Path("/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector-debug.html")

    if not html_file.exists():
        result.fail_check(f"HTML file not found: {html_file}")
        return result

    try:
        content = html_file.read_text()

        checks = {
            "PRIMARY_AGENT_NAME constant": f"const PRIMARY_AGENT_NAME = '{EXPECTED_AGENT_NAME}'",
            "agent_selection message": "type: 'agent_selection'",
            "agent_id field": "agent_id: selectedAgent.id",
            "test-room constant": "const roomName = 'test-room'",
        }

        missing = []
        found = []

        for check_name, check_string in checks.items():
            if check_string in content:
                found.append(check_name)
            else:
                missing.append(check_name)

        if missing:
            result.fail_check(
                f"HTML configuration incomplete: missing {', '.join(missing)}",
                "Review voice-agent-selector-debug.html for correct agent selection logic",
                found
            )
        else:
            result.pass_check("HTML correctly configured for Agent_66", found)

    except Exception as e:
        result.fail_check(f"Error reading HTML file: {e}")

    return result

def check_python_agent_lock() -> VerificationResult:
    """Check if Python backend has agent lock enforcement."""
    result = VerificationResult("Python Backend Agent Lock")

    py_file = Path("/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent_optimized.py")

    if not py_file.exists():
        result.fail_check(f"Python file not found: {py_file}")
        return result

    try:
        content = py_file.read_text()

        checks = {
            "PRIMARY_AGENT_NAME constant": f'PRIMARY_AGENT_NAME = os.getenv("VOICE_PRIMARY_AGENT_NAME", "{EXPECTED_AGENT_NAME}")',
            "PRIMARY_AGENT_ID constant": 'PRIMARY_AGENT_ID = os.getenv("VOICE_PRIMARY_AGENT_ID")',
            "switch_agent method": "async def switch_agent",
            "agent lock enforcement": "if agent_display_name != self.primary_agent_name:",
            "memory loading": "async def _load_agent_memory",
        }

        missing = []
        found = []

        for check_name, check_string in checks.items():
            if check_string in content:
                found.append(check_name)
            else:
                missing.append(check_name)

        if missing:
            result.fail_check(
                f"Python backend incomplete: missing {', '.join(missing)}",
                "Review letta_voice_agent_optimized.py for agent lock logic",
                found
            )
        else:
            result.pass_check("Python backend correctly enforces Agent_66 lock", found)

    except Exception as e:
        result.fail_check(f"Error reading Python file: {e}")

    return result

def main():
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}Agent_66 Voice Connection Verification{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

    checks = [
        check_environment_variables,
        check_postgresql,
        check_letta_server,
        check_livekit_server,
        check_cors_proxy,
        check_voice_agent_worker,
        check_html_configuration,
        check_python_agent_lock,
    ]

    results = []
    for check_func in checks:
        print(f"Running {check_func.__name__.replace('check_', '').replace('_', ' ')}...")
        result = check_func()
        results.append(result)
        print(result)

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Summary: {passed}/{total} checks passed{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    if passed == total:
        print(f"{GREEN}{BOLD}✓ All checks passed! Voice system is correctly configured for Agent_66.{RESET}\n")
        print(f"To test the voice interface:")
        print(f"  1. Open browser to: {BLUE}http://localhost:9000/debug{RESET}")
        print(f"  2. Verify Agent_66 is auto-selected")
        print(f"  3. Click 'Connect' button")
        print(f"  4. Grant microphone permission")
        print(f"  5. Speak: 'Hello, what is your name?'")
        print(f"  6. Check logs: {YELLOW}tail -f /tmp/voice_agent.log{RESET}")
        print()
        return 0
    else:
        print(f"{RED}{BOLD}✗ {total - passed} check(s) failed. Please fix the issues above.{RESET}\n")
        print(f"Quick fix (if all services are down):")
        print(f"  1. Start PostgreSQL: {YELLOW}sudo service postgresql start{RESET}")
        print(f"  2. Run startup script: {YELLOW}cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents && ./start_voice_system.sh{RESET}")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
