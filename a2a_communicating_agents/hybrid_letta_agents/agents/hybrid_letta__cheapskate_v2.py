#!/usr/bin/env python3
"""
hybrid_letta__cheapskate_v2.py

Budget-friendly Letta Orchestrator + Claude Code Agent architecture.
Uses FILE-BASED communication to avoid sandbox issues.

Architecture:
- Letta runs as the orchestrator with long-term memory
- Letta tools write request JSON files to a shared directory
- Host process (main thread) watches for requests and processes them with Claude Agent SDK
- Host writes response JSON files that tools can read
- This keeps everything within your Claude Pro subscription budget

Requirements:
  pip install letta-client claude-agent-sdk

Environment:
  LETTA_BASE_URL      # e.g. http://localhost:8283  (optional, defaults to that)
  OPENAI_API_KEY      # used by the Letta server for openai/gpt-5-mini
"""

from __future__ import annotations

import os
import asyncio
import json
from pathlib import Path
import textwrap
from typing import Optional
from threading import Thread, Event
import time

import letta_client
from letta_client import Letta
from claude_agent_sdk import query as claude_query


# ---------- Configuration ----------

WORKSPACE_DIR = Path(__file__).resolve().parent
COMM_DIR = WORKSPACE_DIR / ".letta_claude_comm"  # Communication directory
ORCH_MODEL = os.environ.get("ORCH_MODEL", "openai/gpt-5-mini")

USER_TASK = textwrap.dedent(
    """
    You are the Orchestrator Agent in a small team:

    - You have a *Coder Tool* that can generate code using Claude.
    - You have a *Tester Tool* that can generate tests for that code using Claude.
    - Your job is to:
      1. Call the Coder Tool to implement a small Python function.
      2. Call the Tester Tool to generate tests for that function.
      3. Confirm to the human where you saved the code and tests.

    Implement a Python function called `add(a: int, b: int) -> int` that returns a + b
    and generate a small pytest test file that covers typical and edge cases.
    """
).strip()


# ---------- Letta Tool Implementations (File-based) ----------

def run_claude_coder(
    spec: str,
    language: str = "python",
    file_name: str = "generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Coder Agent (via host process using file-based communication).

    Args:
        spec: Natural-language specification for the code to generate.
        language: Target programming language (e.g., "python", "javascript").
        file_name: Name of the file to write the generated code to.
        workspace_dir: Directory to write the file to (defaults to current directory).

    Returns:
        Status message indicating where the code was written.
    """
    import uuid
    import time
    from pathlib import Path
    import json
    import os

    request_id = str(uuid.uuid4())
    workspace = workspace_dir or os.getcwd()

    # Get communication directory from environment
    comm_dir = Path(os.environ.get("LETTA_COMM_DIR", "/tmp/letta_claude_comm"))
    comm_dir.mkdir(parents=True, exist_ok=True)

    # Write request file
    request_file = comm_dir / f"req_{request_id}.json"
    request_data = {
        "request_id": request_id,
        "request_type": "coder",
        "spec": spec,
        "language": language,
        "file_name": file_name,
        "workspace_dir": workspace,
    }
    request_file.write_text(json.dumps(request_data), encoding="utf-8")

    # Wait for response file
    response_file = comm_dir / f"res_{request_id}.json"
    timeout = 120
    start_time = time.time()

    while time.time() - start_time < timeout:
        if response_file.exists():
            response_data = json.loads(response_file.read_text(encoding="utf-8"))
            # Clean up files
            request_file.unlink(missing_ok=True)
            response_file.unlink(missing_ok=True)

            if response_data.get("success"):
                return response_data["result"]
            else:
                raise RuntimeError(f"Coder failed: {response_data.get('error')}")

        time.sleep(0.5)

    raise TimeoutError(f"No response received for request {request_id} after {timeout}s")


def run_claude_tester(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
    file_name: str = "test_generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Tester Agent (via host process using file-based communication).

    Args:
        code: The code to generate tests for.
        language: Programming language of the code (e.g., "python", "javascript").
        test_framework: Testing framework to use (e.g., "pytest", "unittest", "jest").
        file_name: Name of the file to write the tests to.
        workspace_dir: Directory to write the file to (defaults to current directory).

    Returns:
        Status message indicating where the tests were written.
    """
    import uuid
    import time
    from pathlib import Path
    import json
    import os

    request_id = str(uuid.uuid4())
    workspace = workspace_dir or os.getcwd()

    # Get communication directory from environment
    comm_dir = Path(os.environ.get("LETTA_COMM_DIR", "/tmp/letta_claude_comm"))
    comm_dir.mkdir(parents=True, exist_ok=True)

    # Write request file
    request_file = comm_dir / f"req_{request_id}.json"
    request_data = {
        "request_id": request_id,
        "request_type": "tester",
        "code": code,
        "language": language,
        "test_framework": test_framework,
        "file_name": file_name,
        "workspace_dir": workspace,
    }
    request_file.write_text(json.dumps(request_data), encoding="utf-8")

    # Wait for response file
    response_file = comm_dir / f"res_{request_id}.json"
    timeout = 120
    start_time = time.time()

    while time.time() - start_time < timeout:
        if response_file.exists():
            response_data = json.loads(response_file.read_text(encoding="utf-8"))
            # Clean up files
            request_file.unlink(missing_ok=True)
            response_file.unlink(missing_ok=True)

            if response_data.get("success"):
                return response_data["result"]
            else:
                raise RuntimeError(f"Tester failed: {response_data.get('error')}")

        time.sleep(0.5)

    raise TimeoutError(f"No response received for request {request_id} after {timeout}s")


# ---------- Host Process: Claude Agent SDK Handler ----------

async def process_claude_requests(shutdown_event: Event):
    """
    Host process that handles Claude Agent SDK calls.
    Watches for request files, processes them, writes response files.
    """
    print("🤖 Claude Agent SDK handler started...")
    print(f"   Watching: {COMM_DIR}")

    COMM_DIR.mkdir(parents=True, exist_ok=True)

    while not shutdown_event.is_set():
        # Find pending requests
        request_files = list(COMM_DIR.glob("req_*.json"))

        for request_file in request_files:
            try:
                request_data = json.loads(request_file.read_text(encoding="utf-8"))
                request_id = request_data["request_id"]
                request_type = request_data["request_type"]

                print(f"📨 Processing {request_type} request: {request_id}")

                if request_type == "coder":
                    result = await handle_coder_request(request_data)
                elif request_type == "tester":
                    result = await handle_tester_request(request_data)
                else:
                    raise ValueError(f"Unknown request type: {request_type}")

                # Write success response
                response_file = COMM_DIR / f"res_{request_id}.json"
                response_data = {
                    "request_id": request_id,
                    "success": True,
                    "result": result,
                }
                response_file.write_text(json.dumps(response_data), encoding="utf-8")
                print(f"✅ Completed {request_type} request: {request_id}")

            except Exception as e:
                # Write error response
                response_file = COMM_DIR / f"res_{request_id}.json"
                response_data = {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                }
                response_file.write_text(json.dumps(response_data), encoding="utf-8")
                print(f"❌ Failed {request_type} request: {request_id} - {e}")

        await asyncio.sleep(0.5)

    print("🛑 Claude Agent SDK handler stopped")


async def handle_coder_request(request_data: dict) -> str:
    """Use Claude Agent SDK to generate code."""
    spec = request_data["spec"]
    language = request_data["language"]
    file_name = request_data["file_name"]
    workspace_dir = request_data["workspace_dir"]

    prompt = f"""Generate production-quality {language} code for the following specification.
Return ONLY the code, no explanations or markdown fences.

Specification:
{spec}

File name: {file_name}
"""

    # Call Claude via Agent SDK
    code_text = ""
    async for message in claude_query(prompt=prompt):
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    code_text += block.text

    if not code_text.strip():
        raise RuntimeError("Claude returned empty code")

    # Clean up markdown fences
    code_text = clean_code_fences(code_text)

    # Write to file
    workspace = Path(workspace_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    out_path = workspace / file_name
    out_path.write_text(code_text, encoding="utf-8")

    return f"Code written to {out_path}"


async def handle_tester_request(request_data: dict) -> str:
    """Use Claude Agent SDK to generate tests."""
    code = request_data["code"]
    language = request_data["language"]
    test_framework = request_data["test_framework"]
    file_name = request_data["file_name"]
    workspace_dir = request_data["workspace_dir"]

    prompt = f"""Generate comprehensive tests for the following {language} code.
Use the {test_framework} framework.
Return ONLY the test code, no explanations or markdown fences.

Code under test:
{code}

Test file name: {file_name}
"""

    # Call Claude via Agent SDK
    test_text = ""
    async for message in claude_query(prompt=prompt):
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    test_text += block.text

    if not test_text.strip():
        raise RuntimeError("Claude returned empty tests")

    # Clean up markdown fences
    test_text = clean_code_fences(test_text)

    # Write to file
    workspace = Path(workspace_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    out_path = workspace / file_name
    out_path.write_text(test_text, encoding="utf-8")

    return f"Tests written to {out_path}"


def clean_code_fences(text: str) -> str:
    """Remove markdown code fences from text."""
    if "```" not in text:
        return text

    segments = text.split("```")
    if len(segments) >= 3:
        text = segments[1]
        lines = text.splitlines()
        if lines and lines[0].strip().lower() in ["python", "py", "javascript", "js", "typescript", "ts"]:
            lines = lines[1:]
        text = "\n".join(lines)

    return text.strip()


# ---------- Letta Thread ----------

def run_letta_orchestrator(shutdown_event: Event):
    """Run Letta orchestrator in a separate thread."""
    print("🧠 Starting Letta orchestrator thread...")

    try:
        base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
        print(f"Connecting to Letta at {base_url}")
        client = Letta(base_url=base_url)

        # Register tools
        coder_tool = client.tools.create_from_function(func=run_claude_coder)
        print(f"✓ Created coder_tool: {coder_tool.id}")

        tester_tool = client.tools.create_from_function(func=run_claude_tester)
        print(f"✓ Created tester_tool: {tester_tool.id}")

        # Create orchestrator agent
        print(f"Creating orchestrator with model: {ORCH_MODEL}")
        orchestrator_agent = client.agents.create(
            model=ORCH_MODEL,
            embedding="openai/text-embedding-3-small",
            memory_blocks=[
                {
                    "label": "role",
                    "value": "You are an orchestrator who manages a Claude Coder and Claude Tester.",
                    "limit": 2000,
                },
                {
                    "label": "workspace",
                    "value": f"Workspace directory: {WORKSPACE_DIR}",
                    "limit": 2000,
                },
            ],
            tools=[coder_tool.name, tester_tool.name],
            tool_exec_environment_variables={
                "WORKSPACE_DIR": str(WORKSPACE_DIR),
                "LETTA_COMM_DIR": str(COMM_DIR),
            },
        )

        print(f"✓ Created orchestrator agent: {orchestrator_agent.id}")

        # Send initial task
        print("\n📤 Sending task to orchestrator...")
        response = client.agents.messages.create(
            agent_id=orchestrator_agent.id,
            messages=[{"role": "user", "content": USER_TASK}],
        )

        # Print response
        print("\n" + "="*60)
        print("ORCHESTRATOR RESPONSE")
        print("="*60 + "\n")

        for msg in response.messages:
            mtype = getattr(msg, "message_type", None)
            if mtype == "assistant_message":
                print(f"[assistant] {msg.content}")
            elif mtype == "user_message":
                print(f"[user] {msg.content}")
            elif mtype == "reasoning_message":
                print(f"[reasoning] {msg.reasoning}")
            elif mtype == "tool_call_message":
                print(f"[tool-call] {msg.tool_call.name}")
            elif mtype == "tool_return_message":
                print(f"[tool-return] {msg.tool_return}")

        print("\n" + "="*60)
        print(f"✅ Done! Check workspace: {WORKSPACE_DIR}")
        print("="*60)

    except Exception as e:
        print(f"❌ Letta orchestrator error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutdown_event.set()
        print("🛑 Letta orchestrator thread stopped")


# ---------- Main ----------

async def main():
    print("🚀 Starting Hybrid Letta (Cheapskate Edition v2 - File-based)")
    print(f"Workspace: {WORKSPACE_DIR}")
    print(f"Communication dir: {COMM_DIR}\n")

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    COMM_DIR.mkdir(parents=True, exist_ok=True)

    # Shutdown coordination
    shutdown_event = Event()

    # Start Letta in a separate thread
    letta_thread = Thread(target=run_letta_orchestrator, args=(shutdown_event,), daemon=True)
    letta_thread.start()

    # Run Claude Agent SDK handler in main thread
    try:
        await process_claude_requests(shutdown_event)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        shutdown_event.set()

    # Wait for Letta thread
    letta_thread.join(timeout=5)

    # Cleanup
    if COMM_DIR.exists():
        for f in COMM_DIR.glob("*.json"):
            f.unlink()

    print("\n👋 Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
