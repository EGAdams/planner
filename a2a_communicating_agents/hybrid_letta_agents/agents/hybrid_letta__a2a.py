#!/usr/bin/env python3
"""
hybrid_letta__a2a.py

Hybrid Letta + Claude Code using your existing A2A messaging infrastructure!

Architecture:
- Letta orchestrator with long-term memory
- Letta tools use rag_system.rag_tools (send/inbox) to communicate
- Host process (Claude Agent SDK) subscribes to messages and responds
- Zero API costs - uses Claude Pro subscription via Claude Agent SDK

Requirements:
  pip install letta-client claude-agent-sdk

Environment:
  LETTA_BASE_URL      # e.g. http://localhost:8283
  OPENAI_API_KEY      # used by Letta server for GPT-4o-mini
"""

from __future__ import annotations

import os
import sys
import asyncio
import json
from pathlib import Path
import textwrap
from typing import Optional
from threading import Thread, Event
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from rag_system.rag_tools import send, inbox
import letta_client
from letta_client import Letta
from claude_agent_sdk import query as claude_query


# ---------- Configuration ----------

WORKSPACE_DIR = Path(__file__).resolve().parent
ORCH_MODEL = os.environ.get("ORCH_MODEL", "openai/gpt-4o-mini")

# Topics for A2A messaging
TOPIC_CODER_REQUEST = "letta-coder-request"
TOPIC_CODER_RESPONSE = "letta-coder-response"
TOPIC_TESTER_REQUEST = "letta-tester-request"
TOPIC_TESTER_RESPONSE = "letta-tester-response"

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


# ---------- Letta Tool Implementations (using rag_system) ----------

def run_claude_coder(
    spec: str,
    language: str = "python",
    file_name: str = "generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Coder Agent (via A2A messaging).

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
    import json
    import sys
    from pathlib import Path

    # Import rag_system
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
    from rag_system.rag_tools import send, inbox

    request_id = str(uuid.uuid4())
    workspace = workspace_dir or "/tmp"

    # Send request via A2A
    request_data = {
        "request_id": request_id,
        "spec": spec,
        "language": language,
        "file_name": file_name,
        "workspace_dir": workspace,
    }
    send(
        message=json.dumps(request_data),
        topic="letta-coder-request",
        from_agent="letta-orchestrator",
    )

    # Wait for response
    timeout = 120
    start_time = time.time()

    while time.time() - start_time < timeout:
        messages = inbox(topic="letta-coder-response", limit=50, render=False)

        for msg in messages:
            try:
                response_data = json.loads(msg.content)
                if response_data.get("request_id") == request_id:
                    if response_data.get("success"):
                        return response_data["result"]
                    else:
                        raise RuntimeError(f"Coder failed: {response_data.get('error')}")
            except (json.JSONDecodeError, KeyError):
                continue

        time.sleep(1)

    raise TimeoutError(f"No response received for coder request {request_id} after {timeout}s")


def run_claude_tester(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
    file_name: str = "test_generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Tester Agent (via A2A messaging).

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
    import json
    import sys
    from pathlib import Path

    # Import rag_system
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
    from rag_system.rag_tools import send, inbox

    request_id = str(uuid.uuid4())
    workspace = workspace_dir or "/tmp"

    # Send request via A2A
    request_data = {
        "request_id": request_id,
        "code": code,
        "language": language,
        "test_framework": test_framework,
        "file_name": file_name,
        "workspace_dir": workspace,
    }
    send(
        message=json.dumps(request_data),
        topic="letta-tester-request",
        from_agent="letta-orchestrator",
    )

    # Wait for response
    timeout = 120
    start_time = time.time()

    while time.time() - start_time < timeout:
        messages = inbox(topic="letta-tester-response", limit=50, render=False)

        for msg in messages:
            try:
                response_data = json.loads(msg.content)
                if response_data.get("request_id") == request_id:
                    if response_data.get("success"):
                        return response_data["result"]
                    else:
                        raise RuntimeError(f"Tester failed: {response_data.get('error')}")
            except (json.JSONDecodeError, KeyError):
                continue

        time.sleep(1)

    raise TimeoutError(f"No response received for tester request {request_id} after {timeout}s")


# ---------- Host Process: Claude Agent SDK Handler (A2A subscriber) ----------

async def process_coder_requests(shutdown_event: Event):
    """Subscribe to coder requests and handle them with Claude Agent SDK."""
    print("🤖 Coder Agent (Claude SDK) started...")
    seen_requests = set()

    while not shutdown_event.is_set():
        try:
            # Check for new coder requests
            messages = inbox(topic=TOPIC_CODER_REQUEST, limit=50, render=False)

            for msg in messages:
                try:
                    request_data = json.loads(msg.content)
                    request_id = request_data.get("request_id")

                    if request_id in seen_requests:
                        continue

                    seen_requests.add(request_id)
                    print(f"📨 Processing coder request: {request_id}")

                    # Handle with Claude Agent SDK
                    result = await handle_coder_request(request_data)

                    # Send response
                    response_data = {
                        "request_id": request_id,
                        "success": True,
                        "result": result,
                    }
                    send(
                        message=json.dumps(response_data),
                        topic=TOPIC_CODER_RESPONSE,
                        from_agent="claude-coder",
                    )
                    print(f"✅ Completed coder request: {request_id}")

                except Exception as e:
                    print(f"❌ Error processing coder request: {e}")
                    # Send error response
                    response_data = {
                        "request_id": request_id,
                        "success": False,
                        "error": str(e),
                    }
                    send(
                        message=json.dumps(response_data),
                        topic=TOPIC_CODER_RESPONSE,
                        from_agent="claude-coder",
                    )

        except Exception as e:
            print(f"⚠️  Coder agent error: {e}")

        await asyncio.sleep(1)

    print("🛑 Coder Agent stopped")


async def process_tester_requests(shutdown_event: Event):
    """Subscribe to tester requests and handle them with Claude Agent SDK."""
    print("🧪 Tester Agent (Claude SDK) started...")
    seen_requests = set()

    while not shutdown_event.is_set():
        try:
            # Check for new tester requests
            messages = inbox(topic=TOPIC_TESTER_REQUEST, limit=50, render=False)

            for msg in messages:
                try:
                    request_data = json.loads(msg.content)
                    request_id = request_data.get("request_id")

                    if request_id in seen_requests:
                        continue

                    seen_requests.add(request_id)
                    print(f"📨 Processing tester request: {request_id}")

                    # Handle with Claude Agent SDK
                    result = await handle_tester_request(request_data)

                    # Send response
                    response_data = {
                        "request_id": request_id,
                        "success": True,
                        "result": result,
                    }
                    send(
                        message=json.dumps(response_data),
                        topic=TOPIC_TESTER_RESPONSE,
                        from_agent="claude-tester",
                    )
                    print(f"✅ Completed tester request: {request_id}")

                except Exception as e:
                    print(f"❌ Error processing tester request: {e}")
                    # Send error response
                    response_data = {
                        "request_id": request_id,
                        "success": False,
                        "error": str(e),
                    }
                    send(
                        message=json.dumps(response_data),
                        topic=TOPIC_TESTER_RESPONSE,
                        from_agent="claude-tester",
                    )

        except Exception as e:
            print(f"⚠️  Tester agent error: {e}")

        await asyncio.sleep(1)

    print("🛑 Tester Agent stopped")


async def handle_coder_request(request_data: dict) -> str:
    """Use Claude Agent SDK to generate code."""
    spec = request_data["spec"]
    language = request_data["language"]
    file_name = request_data["file_name"]
    workspace_dir = request_data["workspace_dir"]

    prompt = f"""Generate production-quality {language} code for this specification.
Return ONLY the code, no explanations or markdown fences.

Specification:
{spec}

File: {file_name}
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

    prompt = f"""Generate comprehensive tests for this {language} code using {test_framework}.
Return ONLY the test code, no explanations or markdown fences.

Code under test:
{code}

Test file: {file_name}
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
    print("🧠 Starting Letta orchestrator...")

    try:
        base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
        print(f"   Connecting to Letta at {base_url}")
        client = Letta(base_url=base_url)

        # Register tools
        coder_tool = client.tools.create_from_function(func=run_claude_coder)
        print(f"✓ Coder tool: {coder_tool.id}")

        tester_tool = client.tools.create_from_function(func=run_claude_tester)
        print(f"✓ Tester tool: {tester_tool.id}")

        # Create orchestrator agent
        orchestrator_agent = client.agents.create(
            model=ORCH_MODEL,
            embedding="openai/text-embedding-3-small",
            memory_blocks=[
                {
                    "label": "role",
                    "value": "You orchestrate Claude Coder and Claude Tester via A2A messaging.",
                    "limit": 2000,
                },
                {
                    "label": "workspace",
                    "value": f"Workspace: {WORKSPACE_DIR}",
                    "limit": 2000,
                },
            ],
            tools=[coder_tool.name, tester_tool.name],
            tool_exec_environment_variables={
                "WORKSPACE_DIR": str(WORKSPACE_DIR),
                "PYTHONPATH": str(Path(__file__).resolve().parent.parent.parent.parent),
            },
        )

        print(f"✓ Orchestrator: {orchestrator_agent.id}\n")

        # Send task
        print("📤 Sending task to orchestrator...\n")
        response = client.agents.messages.create(
            agent_id=orchestrator_agent.id,
            messages=[{"role": "user", "content": USER_TASK}],
        )

        # Print response
        print("="*60)
        print("ORCHESTRATOR RESPONSE")
        print("="*60 + "\n")

        for msg in response.messages:
            mtype = getattr(msg, "message_type", None)
            if mtype == "assistant_message":
                print(f"[assistant] {msg.content}")
            elif mtype == "tool_call_message":
                print(f"[tool-call] {msg.tool_call.name}")
            elif mtype == "tool_return_message":
                print(f"[tool-return] {msg.tool_return}")

        print("\n" + "="*60)
        print(f"✅ Check workspace: {WORKSPACE_DIR}")
        print("="*60)

    except Exception as e:
        print(f"❌ Letta error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutdown_event.set()
        print("\n🛑 Letta orchestrator stopped")


# ---------- Main ----------

async def main():
    print("🚀 Hybrid Letta + A2A + Claude Code (Zero API Costs!)")
    print(f"Workspace: {WORKSPACE_DIR}\n")

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    shutdown_event = Event()

    # Start Letta in a thread
    letta_thread = Thread(target=run_letta_orchestrator, args=(shutdown_event,), daemon=True)
    letta_thread.start()

    # Run Claude Agent SDK handlers in main thread
    try:
        await asyncio.gather(
            process_coder_requests(shutdown_event),
            process_tester_requests(shutdown_event),
        )
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        shutdown_event.set()

    letta_thread.join(timeout=5)
    print("\n👋 Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
