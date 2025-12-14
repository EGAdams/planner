#!/usr/bin/env python3
"""
Persistent Letta Orchestrator - Maintains memory across runs.

Key differences from hybrid_letta__codex_sdk.py:
1. Reuses existing agent instead of creating new one each run
2. Adds time/date tool for timestamping tasks
3. Enhanced memory tracking with timestamps
4. Agent remembers ALL previous work until explicitly reset
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
import textwrap
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import letta_client
from letta_client import Letta

# ---------- Configuration ----------

WORKSPACE_DIR = Path(__file__).resolve().parent
CONTRACT_LOG_NAME = "tdd_contracts.jsonl"
AGENT_ID_FILE = WORKSPACE_DIR / ".letta_agent_id"

ORCH_MODEL = os.environ.get("ORCH_MODEL", "openai/gpt-5-mini")

# ---------- Time Tool ----------

def get_current_time() -> str:
    """
    Get the current date and time.

    Returns:
        A string with the current date and time in ISO format with human-readable description.
    """
    import json
    from datetime import datetime

    now = datetime.now()

    result = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "human_readable": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
        "unix_epoch": int(now.timestamp()),
    }

    return json.dumps(result, indent=2)

# ---------- Tool implementations ----------

def run_codex_coder(
    spec: str,
    language: str = "python",
    file_name: str = "generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Codex Coder Agent (Python orchestrator).

    - Delegates code creation/editing to Codex via the Codex SDK (Node bridge).
    - Codex runs in `workspace-write` sandbox mode and writes files itself.
    - This function just orchestrates and logs a small contract.

    Args:
        spec: Natural-language spec for the feature to implement.
        language: Target programming language (e.g. "python", "typescript").
        file_name: Main file Codex should create/overwrite in the workspace.
        workspace_dir: Optional workspace directory. Defaults to current cwd.

    Returns:
        A JSON string with a contract, including Codex's report.
    """
    import os
    import json
    import shutil
    import subprocess
    import hashlib
    from pathlib import Path

    base_dir = Path(workspace_dir or os.getcwd()).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    # Locate Node
    node_bin = shutil.which("node")
    if not node_bin:
        raise RuntimeError(
            "Node.js binary not found on PATH. Please install Node 18+."
        )

    # Locate the Codex Node bridge script
    bridge_path_env = os.environ.get("CODEX_NODE_BRIDGE")
    bridge_path = (
        Path(bridge_path_env).resolve()
        if bridge_path_env
        else (base_dir / "node_executables" / "codex_coder_bridge.mjs")
    )
    if not bridge_path.exists():
        raise RuntimeError(
            f"Codex bridge script not found at {bridge_path}. "
            "Set CODEX_NODE_BRIDGE or place codex_coder_bridge.mjs there."
        )

    # Decide which Codex model to use (same logic you had before)
    model_name = os.environ.get("CODEX_MODEL")
    if not model_name:
        orch_model = os.environ.get("ORCH_MODEL", "")
        candidate = orch_model.split("/", 1)[-1] if "/" in orch_model else orch_model
        if candidate and not candidate.startswith("gpt-4o"):
            model_name = candidate
        else:
            model_name = "gpt-5.1-codex"

    payload = {
        "spec": spec,
        "language": language,
        "fileName": file_name,
        "workspaceDir": str(base_dir),
        "model": model_name,
    }

    completed = subprocess.run(
        [node_bin, str(bridge_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(base_dir),
        check=False,
    )

    if completed.returncode != 0:
        # The bridge writes a JSON error payload even on failure
        msg = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"Codex bridge failed with exit code {completed.returncode}: {msg}"
        )

    try:
        bridge_result = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Failed to parse Codex bridge output as JSON: {exc}\n"
            f"Raw output:\n{completed.stdout}"
        ) from exc

    status = bridge_result.get("status", "unknown")
    if status == "error":
        raise RuntimeError(
            f"Codex bridge reported error: {bridge_result.get('message')}"
        )

    # Where we *expect* the main file to be, according to our contract.
    out_path = base_dir / file_name

    contract = {
        "contract_type": "code_generation",
        "status": status,
        "file_path": str(out_path),
        "language": language,
        "spec_hash": hashlib.sha256(spec.encode("utf-8")).hexdigest(),
        "workspace_dir": str(base_dir),
        # Pass through the Codex-side report so downstream tools can inspect it.
        "codex_report": bridge_result,
    }

    # Optional: log to JSONL file
    try:
        default_log_name = CONTRACT_LOG_NAME  # type: ignore[name-defined]
    except NameError:
        default_log_name = "tdd_contracts.jsonl"

    log_name = os.environ.get("CONTRACT_LOG_NAME", default_log_name)
    log_path = base_dir / log_name
    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(contract) + "\n")
    except OSError:
        # Best-effort logging; don't fail the whole run.
        pass

    return json.dumps(contract, indent=2)

# ---------- Agent Management ----------

def create_letta_client() -> Letta:
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    print(f"Using Letta at {base_url}")
    client = Letta(base_url=base_url)
    return client

def get_or_create_agent(client: Letta, force_new: bool = False) -> Any:
    """Get existing agent or create new one."""

    # Check for existing agent ID
    agent_id = None
    if AGENT_ID_FILE.exists() and not force_new:
        try:
            agent_id = AGENT_ID_FILE.read_text().strip()
            print(f"Found existing agent ID: {agent_id}")

            # Verify agent still exists
            try:
                # Try to send a test message to verify agent exists
                client.agents.messages.create(
                    agent_id=agent_id,
                    messages=[{"role": "user", "content": "ping"}],
                    timeout=10,
                )
                print(f"✓ Reusing existing agent: {agent_id}")
                return agent_id
            except Exception as e:
                print(f"⚠ Agent {agent_id} no longer exists: {e}")
                agent_id = None
                AGENT_ID_FILE.unlink()
        except Exception as e:
            print(f"⚠ Error reading agent ID: {e}")
            agent_id = None

    # Create new agent
    print("Creating new persistent agent...")

    # Register tools first
    coder_tool = client.tools.create_from_function(func=run_codex_coder)
    time_tool = client.tools.create_from_function(func=get_current_time)

    print(f"  ✓ Registered tools: {coder_tool.name}, {time_tool.name}")

    agent = client.agents.create(
        model=ORCH_MODEL,
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "role",
                "value": textwrap.dedent("""
                    You are a persistent orchestrator agent with long-term memory.

                    CRITICAL MEMORY RULES:
                    1. You MUST remember ALL tasks you complete - NEVER forget previous work
                    2. ALWAYS use get_current_time tool to timestamp your work
                    3. Update your task_history memory block after EVERY task
                    4. When asked "what have we done?", recall ALL previous tasks with timestamps
                    5. Track: what was done, when it was done, which tools were used, file paths

                    You have access to:
                    - run_codex_coder: Generate code using Codex
                    - get_current_time: Get current date/time for timestamping

                    WORKFLOW:
                    1. Before any task: call get_current_time to record when you start
                    2. Execute the task using appropriate tools
                    3. After task: update task_history with timestamp, action, and results
                    4. Confirm completion with details (what, when, where)
                """).strip(),
                "limit": 3000,
            },
            {
                "label": "task_history",
                "value": "No tasks completed yet. This will be updated after each task.",
                "limit": 5000,
            },
            {
                "label": "workspace",
                "value": f"Workspace directory: {WORKSPACE_DIR}\nAll files are created here.",
                "limit": 1000,
            },
        ],
        tools=[coder_tool.name, time_tool.name],
        tool_exec_environment_variables={
            "ORCH_MODEL": ORCH_MODEL,
            "WORKSPACE_DIR": str(WORKSPACE_DIR),
            "CODEX_MODEL": os.environ.get("CODEX_MODEL", ""),
            "CONTRACT_LOG_NAME": CONTRACT_LOG_NAME,
        },
    )

    agent_id = agent.id
    print(f"✓ Created new agent: {agent_id}")

    # Save agent ID for future runs
    AGENT_ID_FILE.write_text(agent_id)
    print(f"✓ Saved agent ID to {AGENT_ID_FILE}")

    return agent_id

def reset_agent():
    """Delete the agent ID file to force creation of new agent."""
    if AGENT_ID_FILE.exists():
        AGENT_ID_FILE.unlink()
        print("✓ Agent ID deleted. Next run will create new agent.")
    else:
        print("No agent ID file found.")

# ---------- Main ----------

def main(user_message: str, force_new_agent: bool = False):
    """Send a message to the persistent orchestrator."""

    print("="*70)
    print("PERSISTENT LETTA ORCHESTRATOR")
    print("="*70)

    client = create_letta_client()
    agent_id = get_or_create_agent(client, force_new=force_new_agent)

    print(f"\n📤 Sending message to agent...")
    print(f"Message: {user_message}")

    start_time = datetime.now()

    try:
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": user_message}],
            timeout=120,
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ Response received ({elapsed:.1f}s)")

        print("\n" + "="*70)
        print("AGENT RESPONSE")
        print("="*70)

        for msg in response.messages:
            mtype = getattr(msg, "message_type", None)
            if mtype == "assistant_message":
                print(f"\n{msg.content}")
            elif mtype == "tool_call_message":
                print(f"\n[TOOL CALL] {msg.tool_call.name}({msg.tool_call.arguments})")
            elif mtype == "tool_return_message":
                ret = str(msg.tool_return)
                if len(ret) > 300:
                    ret = ret[:300] + "..."
                print(f"[TOOL RETURN] {ret}")

        print("\n" + "="*70)

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        raise

if __name__ == "__main__":
    import sys

    # Check for reset flag
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_agent()
        sys.exit(0)

    # Get message from command line or use default
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "Write a Hello World Python program"

    main(message)
