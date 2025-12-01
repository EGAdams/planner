#!/usr/bin/env python3
"""
hybrid_letta__claude_sdk.py

Letta Orchestrator agent + Claude-based Coder & Tester tools.

- Letta runs as the orchestrator with long-term memory.
- The Coder & Tester are implemented as custom tools that call the Anthropic/Claude SDK.
- The orchestrator "sees" all messages, tool calls, and tool returns and can store
  specs, code, and tests in its memory blocks.

Requirements (host + Letta tool sandbox):

  pip install letta-client anthropic

Environment:

  LETTA_BASE_URL      # e.g. http://localhost:8283  (optional, defaults to that)
  OPENAI_API_KEY      # used by the Letta server for openai/gpt-4o-mini

Authentication:

  This script uses the OAuth token from Claude Code CLI (~/.claude/.credentials.json)
  for authenticating with the Anthropic API. Make sure you're logged into Claude Code
  before running this script.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
import textwrap
from typing import Optional

import letta_client
from letta_client import Letta


# ---------- Configuration ----------

# Where generated code / tests will be written on the host
WORKSPACE_DIR = Path(__file__).resolve().parent

# Claude model for the coder & tester tools
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest")

# Orchestrator model inside Letta (Letta only supports: letta, openai, google_ai)
ORCH_MODEL = os.environ.get("ORCH_MODEL", "openai/gpt-4o-mini")

# Initial task given to the orchestrator
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


# ---------- Tool implementations (executed inside Letta) ----------

def run_claude_coder(
    spec: str,
    language: str = "python",
    file_name: str = "generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Coder Agent.

    Args:
        spec: Natural-language spec for the feature to implement.
        language: Target programming language (e.g. "python", "typescript").
        file_name: File name to write the generated code into.
        workspace_dir: Optional workspace directory to write into. If not provided,
            defaults to the current working directory of the tool.

    Returns:
        A short status string including the file path where code was written.
    """
    import os
    from pathlib import Path
    from anthropic import Anthropic

    # Use Claude Pro subscription via CLI login (no explicit API key needed)
    # The SDK will automatically use stored credentials from 'claude login'
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key) if api_key else Anthropic()

    system_prompt = (
        "You are a senior software engineer (Coder Agent). "
        "Given a spec and target language, generate clean, "
        "production-quality code in a single file. "
        "Respond ONLY with the code for that file, no explanation."
    )

    user_prompt = (
        f"Target language: {language}\n\n"
        "Write the implementation for this spec as a single file:\n"
        "---------------- SPEC START ----------------\n"
        f"{spec}\n"
        "----------------- SPEC END -----------------\n"
    )

    resp = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
        max_tokens=4000,
        temperature=0.0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract text content
    parts = getattr(resp, "content", []) or []
    code_text = ""
    for p in parts:
        if getattr(p, "type", None) == "text":
            code_text += p.text

    if not code_text.strip():
        raise RuntimeError("Claude Coder returned empty content.")

    # Best-effort strip surrounding fences if Claude included ``` blocks
    if "```" in code_text:
        segments = code_text.split("```")
        if len(segments) >= 3:
            # content is usually in the 2nd segment
            code_text = segments[1]
            # strip possible "python" language tag on the first line
            lines = code_text.splitlines()
            if lines and lines[0].strip().startswith(("python", "py")):
                lines = lines[1:]
            code_text = "\n".join(lines)

    # Write to file
    base_dir = Path(workspace_dir or os.getcwd())
    base_dir.mkdir(parents=True, exist_ok=True)
    out_path = base_dir / file_name
    out_path.write_text(code_text, encoding="utf-8")

    return f"Code written to {out_path}"


def run_claude_tester(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
    file_name: str = "test_generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Claude Tester Agent.

    Args:
        code: Code under test.
        language: Programming language of the code.
        test_framework: e.g. "pytest", "unittest", "jest".
        file_name: File name to write the generated tests into.
        workspace_dir: Optional workspace directory to write into. If not provided,
            defaults to the current working directory of the tool.

    Returns:
        A short status string including the file path where tests were written.
    """
    import os
    from pathlib import Path
    from anthropic import Anthropic

    # Use Claude Pro subscription via CLI login (no explicit API key needed)
    # The SDK will automatically use stored credentials from 'claude login'
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key) if api_key else Anthropic()

    system_prompt = (
        "You are a senior test engineer (Tester Agent). "
        "Given some code, generate high-value automated tests. "
        "Cover edge cases and typical usage. "
        "Return a complete test file using the requested framework."
    )

    user_prompt = (
        f"Language: {language}\n"
        f"Test framework: {test_framework}\n\n"
        "Here is the code under test:\n"
        "---------------- CODE START ----------------\n"
        f"{code}\n"
        "----------------- CODE END -----------------\n\n"
        "Now write the full test file."
    )

    resp = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
        max_tokens=4000,
        temperature=0.0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    parts = getattr(resp, "content", []) or []
    test_text = ""
    for p in parts:
        if getattr(p, "type", None) == "text":
            test_text += p.text

    if not test_text.strip():
        raise RuntimeError("Claude Tester returned empty content.")

    # Best-effort strip ``` fences
    if "```" in test_text:
        segments = test_text.split("```")
        if len(segments) >= 3:
            test_text = segments[1]
            lines = test_text.splitlines()
            if lines and lines[0].strip().startswith(("python", "py")):
                lines = lines[1:]
            test_text = "\n".join(lines)

    base_dir = Path(workspace_dir or os.getcwd())
    base_dir.mkdir(parents=True, exist_ok=True)
    out_path = base_dir / file_name
    out_path.write_text(test_text, encoding="utf-8")

    return f"Tests written to {out_path}"


# ---------- Helpers ----------

def get_claude_oauth_token() -> str:
    """
    Read the Claude OAuth token from ~/.claude/.credentials.json
    This allows us to use the same authentication as Claude Code.
    """
    credentials_path = Path.home() / ".claude" / ".credentials.json"
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Claude credentials not found at {credentials_path}. "
            "Please run 'claude login' or ensure you're logged into Claude Code."
        )

    with open(credentials_path) as f:
        creds = json.load(f)

    oauth_data = creds.get("claudeAiOauth")
    if not oauth_data:
        raise ValueError("No claudeAiOauth found in credentials file")

    access_token = oauth_data.get("accessToken")
    if not access_token:
        raise ValueError("No accessToken found in OAuth credentials")

    return access_token


def create_letta_client() -> Letta:
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    print(f"Using self-hosted Letta at {base_url} (override with LETTA_BASE_URL).")
    client = Letta(base_url=base_url)
    return client


def ensure_workspace_dir() -> None:
    print(f"WORKSPACE_DIR = {WORKSPACE_DIR}")
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


# ---------- Main orchestration ----------

def main() -> None:
    print("Starting hybrid_letta__claude_sdk.py...")
    ensure_workspace_dir()

    # Get Claude OAuth token from ~/.claude/.credentials.json
    try:
        oauth_token = get_claude_oauth_token()
        print("✓ Successfully loaded Claude OAuth token from ~/.claude/.credentials.json")
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Error loading Claude OAuth token: {e}")
        print("\nPlease ensure you're logged into Claude Code.")
        return

    client = create_letta_client()

    # 1) Register tools (once). If they already exist with the same signature,
    #    create_from_function will upsert them.
    coder_tool = client.tools.create_from_function(func=run_claude_coder)
    print("Created coder_tool:")
    print(f"  - ID:   {coder_tool.id}")
    print(f"  - Name: {coder_tool.name}")

    tester_tool = client.tools.create_from_function(func=run_claude_tester)
    print("Created tester_tool:")
    print(f"  - ID:   {tester_tool.id}")
    print(f"  - Name: {tester_tool.name}")

    # 2) Create an orchestrator agent which can call those tools
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
                "value": f"Workspace directory on the host is: {WORKSPACE_DIR}",
                "limit": 2000,
            },
        ],
        tools=[coder_tool.name, tester_tool.name],
        # tool_exec_environment_variables are available as os.getenv(...) inside tools
        # Pass the OAuth token from Claude Code CLI to the tools
        tool_exec_environment_variables={
            "CLAUDE_MODEL": CLAUDE_MODEL,
            "WORKSPACE_DIR": str(WORKSPACE_DIR),
            "ANTHROPIC_API_KEY": oauth_token,  # Use OAuth token from ~/.claude/.credentials.json
        },
    )

    print(f"Created orchestrator agent: {orchestrator_agent.id}")

    # 3) Send initial high-level task to orchestrator
    print("Sending initial task to orchestrator...")
    try:
        response = client.agents.messages.create(
            agent_id=orchestrator_agent.id,
            messages=[{"role": "user", "content": USER_TASK}],
        )
    except letta_client.APIConnectionError as e:
        print("❌ Letta connection / timeout error while sending message.")
        print(repr(e))
        print(
            "\nHints:\n"
            "- Make sure your Letta server is running and reachable at LETTA_BASE_URL.\n"
            "- Confirm the server has OPENAI_API_KEY set so it can call openai/gpt-4o-mini.\n"
            "- Confirm ANTHROPIC_API_KEY is set on the host so the tools can call Claude.\n"
            "- If the operation is legitimately long-running, you can increase "
            "timeout_in_seconds further."
        )
        return

    # 4) Print orchestrator messages (including tool calls / returns)
    print("\n=== Orchestrator response ===\n")
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
            # Fallback for older SDK versions
            print(msg)

    print("\nDone. Check the workspace directory for generated files:")
    print(f"  {WORKSPACE_DIR}")


if __name__ == "__main__":
    main()
