#!/usr/bin/env python3
"""
hybrid_letta__cheapskate.py

Budget-friendly Letta Orchestrator + Claude Code Agent architecture.

Architecture:
- Letta runs as the orchestrator with long-term memory
- Letta tools DON'T call Anthropic API directly (no API credits needed!)
- Instead, tools communicate with the host process via a queue
- Host process uses Claude Agent SDK to leverage Claude Code's subscription
- This keeps everything within your Claude Pro subscription budget

Requirements:
  pip install letta-client claude-agent-sdk

Environment:
  LETTA_BASE_URL      # e.g. http://localhost:8283 (optional, defaults to that)
  OPENAI_API_KEY      # used by the Letta server for openai/gpt-4o-mini

How it works:
  1. Main thread runs Claude Agent SDK (has access to Claude Code)
  2. Separate thread runs Letta orchestrator
  3. Communication via thread-safe queues
  4. Letta tools send requests → Host processes with Claude → Returns results
"""

from __future__ import annotations

import os
import asyncio
import json
from pathlib import Path
import textwrap
from typing import Optional, Dict, Any
from queue import Queue, Empty
from threading import Thread, Event
from dataclasses import dataclass
import time

import letta_client
from letta_client import Letta
from claude_agent_sdk import query as claude_query


# ---------- Configuration ----------

WORKSPACE_DIR = Path(__file__).resolve().parent
ORCH_MODEL = os.environ.get("ORCH_MODEL", "openai/gpt-4o-mini")

# Initial task for the orchestrator
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


# ---------- Communication Infrastructure ----------

@dataclass
class ClaudeRequest:
    """Request from Letta tool to host process."""
    request_id: str
    request_type: str  # "coder" or "tester"
    spec: str
    language: str
    file_name: str
    workspace_dir: str
    # For tester only:
    code: Optional[str] = None
    test_framework: Optional[str] = None


@dataclass
class ClaudeResponse:
    """Response from host process to Letta tool."""
    request_id: str
    success: bool
    result: str
    error: Optional[str] = None


# Global queues for inter-thread communication
request_queue: Queue[ClaudeRequest] = Queue()
response_queue: Queue[ClaudeResponse] = Queue()


# ---------- Letta Tool Implementations ----------

def run_claude_coder(
    spec: str,
    language: str = "python",
    file_name: str = "generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Coder Agent (via host process).

    This tool doesn't call the Anthropic API directly. Instead, it sends a request
    to the host process via a queue, waits for the response, and returns it.

    Args:
        spec: Natural-language specification for the code to generate.
        language: Target programming language (e.g., "python", "javascript").
        file_name: Name of the file to write the generated code to.
        workspace_dir: Directory to write the file to (defaults to current directory).

    Returns:
        Status message indicating where the code was written.
    """
    import uuid
    import os
    import time
    from queue import Empty
    from dataclasses import dataclass
    from typing import Optional

    # Import the shared queues
    import sys
    import importlib.util
    spec_module = importlib.util.spec_from_file_location("main", __file__)
    main_module = importlib.util.module_from_spec(spec_module)
    request_queue = main_module.request_queue
    response_queue = main_module.response_queue

    @dataclass
    class ClaudeRequest:
        request_id: str
        request_type: str
        spec: str
        language: str
        file_name: str
        workspace_dir: str
        code: Optional[str] = None
        test_framework: Optional[str] = None

    request_id = str(uuid.uuid4())
    workspace = workspace_dir or os.getcwd()

    # Send request to host process
    req = ClaudeRequest(
        request_id=request_id,
        request_type="coder",
        spec=spec,
        language=language,
        file_name=file_name,
        workspace_dir=workspace,
    )
    request_queue.put(req)

    # Wait for response (with timeout)
    timeout = 120  # 2 minutes
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = response_queue.get(timeout=1)
            if response.request_id == request_id:
                if response.success:
                    return response.result
                else:
                    raise RuntimeError(f"Coder failed: {response.error}")
        except Empty:
            continue

    raise TimeoutError(f"No response received for request {request_id} after {timeout}s")


def run_claude_tester(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
    file_name: str = "test_generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Tester Agent (via host process).

    This tool doesn't call the Anthropic API directly. Instead, it sends a request
    to the host process via a queue, waits for the response, and returns it.

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

    request_id = str(uuid.uuid4())
    workspace = workspace_dir or os.getcwd()

    # Send request to host process
    req = ClaudeRequest(
        request_id=request_id,
        request_type="tester",
        spec="",  # Not used for tester
        language=language,
        file_name=file_name,
        workspace_dir=workspace,
        code=code,
        test_framework=test_framework,
    )
    request_queue.put(req)

    # Wait for response (with timeout)
    timeout = 120  # 2 minutes
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = response_queue.get(timeout=1)
            if response.request_id == request_id:
                if response.success:
                    return response.result
                else:
                    raise RuntimeError(f"Tester failed: {response.error}")
        except Empty:
            continue

    raise TimeoutError(f"No response received for request {request_id} after {timeout}s")


# ---------- Host Process: Claude Agent SDK Handler ----------

async def process_claude_requests(shutdown_event: Event):
    """
    Host process that handles Claude Agent SDK calls.
    Runs in the main thread with access to Claude Code.
    """
    print("🤖 Claude Agent SDK handler started...")

    while not shutdown_event.is_set():
        try:
            # Check for requests (non-blocking)
            request = request_queue.get(timeout=0.5)
        except Empty:
            continue

        print(f"📨 Received {request.request_type} request: {request.request_id}")

        try:
            if request.request_type == "coder":
                result = await handle_coder_request(request)
            elif request.request_type == "tester":
                result = await handle_tester_request(request)
            else:
                raise ValueError(f"Unknown request type: {request.request_type}")

            # Send success response
            response = ClaudeResponse(
                request_id=request.request_id,
                success=True,
                result=result,
            )
            response_queue.put(response)
            print(f"✅ Completed {request.request_type} request: {request.request_id}")

        except Exception as e:
            # Send error response
            response = ClaudeResponse(
                request_id=request.request_id,
                success=False,
                result="",
                error=str(e),
            )
            response_queue.put(response)
            print(f"❌ Failed {request.request_type} request: {request.request_id} - {e}")

    print("🛑 Claude Agent SDK handler stopped")


async def handle_coder_request(request: ClaudeRequest) -> str:
    """Use Claude Agent SDK to generate code."""
    prompt = f"""Generate production-quality {request.language} code for the following specification.
Return ONLY the code, no explanations or markdown.

Specification:
{request.spec}

File name: {request.file_name}
"""

    # Call Claude via Agent SDK (uses Claude Code subscription)
    code_text = ""
    async for message in claude_query(prompt=prompt):
        # Extract text from assistant messages
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    code_text += block.text

    if not code_text.strip():
        raise RuntimeError("Claude returned empty code")

    # Clean up markdown fences if present
    code_text = clean_code_fences(code_text, request.language)

    # Write to file
    workspace = Path(request.workspace_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    out_path = workspace / request.file_name
    out_path.write_text(code_text, encoding="utf-8")

    return f"Code written to {out_path}"


async def handle_tester_request(request: ClaudeRequest) -> str:
    """Use Claude Agent SDK to generate tests."""
    prompt = f"""Generate comprehensive tests for the following {request.language} code.
Use the {request.test_framework} framework.
Return ONLY the test code, no explanations or markdown.

Code under test:
{request.code}

Test file name: {request.file_name}
"""

    # Call Claude via Agent SDK (uses Claude Code subscription)
    test_text = ""
    async for message in claude_query(prompt=prompt):
        # Extract text from assistant messages
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    test_text += block.text

    if not test_text.strip():
        raise RuntimeError("Claude returned empty tests")

    # Clean up markdown fences if present
    test_text = clean_code_fences(test_text, request.language)

    # Write to file
    workspace = Path(request.workspace_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    out_path = workspace / request.file_name
    out_path.write_text(test_text, encoding="utf-8")

    return f"Tests written to {out_path}"


def clean_code_fences(text: str, language: str) -> str:
    """Remove markdown code fences from text."""
    if "```" not in text:
        return text

    segments = text.split("```")
    if len(segments) >= 3:
        # Content is usually in the 2nd segment
        text = segments[1]
        # Strip language tag on first line
        lines = text.splitlines()
        if lines and lines[0].strip().lower() in ["python", "py", "javascript", "js", "typescript", "ts"]:
            lines = lines[1:]
        text = "\n".join(lines)

    return text


# ---------- Letta Thread ----------

def run_letta_orchestrator(shutdown_event: Event):
    """
    Run Letta orchestrator in a separate thread.
    """
    print("🧠 Starting Letta orchestrator thread...")

    try:
        # Create Letta client
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
                print(f"[tool-call] {msg.tool_call.name} args={msg.tool_call.arguments}")
            elif mtype == "tool_return_message":
                print(f"[tool-return] {msg.tool_return}")
            else:
                print(msg)

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
    print("🚀 Starting Hybrid Letta (Cheapskate Edition)")
    print(f"Workspace: {WORKSPACE_DIR}\n")

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    # Shutdown coordination
    shutdown_event = Event()

    # Start Letta in a separate thread
    letta_thread = Thread(target=run_letta_orchestrator, args=(shutdown_event,), daemon=True)
    letta_thread.start()

    # Run Claude Agent SDK handler in main thread (needs async context)
    try:
        await process_claude_requests(shutdown_event)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        shutdown_event.set()

    # Wait for Letta thread to finish
    letta_thread.join(timeout=5)

    print("\n👋 Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
