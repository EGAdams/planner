#!/usr/bin/env python3
"""
hybrid_letta_claude_example.py

Letta Orchestrator + Claude Agent SDK Coder & Tester tools.

- Letta runs as the stateful orchestrator (sees all traffic, has memory).
- Coder & Tester are implemented as Letta custom tools that call the
  Claude Agent SDK from inside the tool execution environment.

Requirements (in the *Letta server tool environment*):
    pip install letta-client claude-agent-sdk anyio

Also make sure the Claude CLI is installed and working for claude-agent-sdk.
"""

import os
from letta_client import Letta


# ---------------------------------------------------------------------------
# Claude-backed tools (Coder & Tester)
# NOTE: All imports and helper functions live *inside* the tool functions,
#       because Letta executes them in an isolated environment.
# ---------------------------------------------------------------------------

def run_claude_coder(spec: str, language: str = "python") -> str:
    """
    Claude Coder Agent.

    Args:
        spec (str): Natural-language spec for the feature to implement.
        language (str): Target programming language (e.g. "python", "typescript").

    Returns:
        str: Generated source code as a single file (string).
    """
    import anyio
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        TextBlock,
    )

    async def _run_claude_once(prompt: str, system_prompt: str) -> str:
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            max_turns=1,
        )

        chunks = []

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)

        return "".join(chunks)

    system_prompt = (
        "You are a senior software engineer (Coder Agent). "
        "Given a spec and target language, generate clean, "
        "production-quality code in a single file. "
        "Respond primarily with code blocks and minimal explanation."
    )

    user_prompt = (
        f"Target language: {language}\n\n"
        "Write the implementation for this spec:\n"
        "---------------- SPEC START ----------------\n"
        f"{spec}\n"
        "----------------- SPEC END -----------------\n"
    )

    return anyio.run(_run_claude_once, user_prompt, system_prompt)


def run_claude_tester(
    code: str,
    language: str = "python",
    test_framework: str = "pytest",
) -> str:
    """
    Claude Tester Agent.

    Args:
        code (str): Code under test.
        language (str): Programming language of the code.
        test_framework (str): Test framework to use (e.g. "pytest", "unittest", "jest").

    Returns:
        str: Generated test file as a string.
    """
    import anyio
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        TextBlock,
    )

    async def _run_claude_once(prompt: str, system_prompt: str) -> str:
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            max_turns=1,
        )

        chunks = []

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)

        return "".join(chunks)

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

    return anyio.run(_run_claude_once, user_prompt, system_prompt)


# ---------------------------------------------------------------------------
# Letta client + Orchestrator Agent
# ---------------------------------------------------------------------------

def create_letta_client() -> Letta:
    """
    Create a Letta client for Cloud or self-hosted, with a bit of logging.
    """
    api_key = os.getenv("LETTA_API_KEY")
    base_url = os.getenv("LETTA_BASE_URL")

    if api_key:
        print("Using Letta Cloud (https://api.letta.com).")
        return Letta(api_key=api_key)

    # Self-hosted
    if not base_url:
        base_url = "http://localhost:8283"
    print(f"Using self-hosted Letta at {base_url} (set LETTA_BASE_URL to override).")
    return Letta(base_url=base_url)


def main() -> None:
    # 1) Connect to Letta
    client = create_letta_client()

    # 2) Register Claude-backed tools (Coder & Tester)
    coder_tool = client.tools.create_from_function(func=run_claude_coder)
    print("Created coder_tool:")
    print(f"  - ID:   {coder_tool.id}")
    print(f"  - Name: {coder_tool.name}")

    tester_tool = client.tools.create_from_function(func=run_claude_tester)
    print("Created tester_tool:")
    print(f"  - ID:   {tester_tool.id}")
    print(f"  - Name: {tester_tool.name}")

    # 3) Create Letta orchestrator agent
    model = os.getenv("LETTA_ORCHESTRATOR_MODEL", "openai/gpt-4o-mini")
    embedding = os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-3-small")

    print(f"Creating orchestrator with model: {model}")

    orchestrator = client.agents.create(
        name="hybrid_letta_claude_orchestrator",
        model=model,
        embedding=embedding,
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    "You are an orchestration agent that coordinates a Claude-based "
                    "Coder and Tester. You never hand-write code or tests yourself. "
                    "Instead, you:\n"
                    "1) Use the 'run_claude_coder' tool to generate code.\n"
                    "2) Use the 'run_claude_tester' tool to generate tests.\n"
                    "3) Store important code and tests in your memory blocks "
                    "for future reuse."
                ),
                "limit": 4000,
            },
            {
                "label": "project_log",
                "value": (
                    "High-level log of tasks, design decisions, generated code, and tests."
                ),
                "limit": 16000,
            },
        ],
        # Attach tools by *name* (recommended)
        tools=[
            coder_tool.name,
            tester_tool.name,
            # Optional core tools for memory management / messaging etc.
            "send_message",
            "archival_memory_insert",
            "memory_replace",
        ],
    )

    print(f"Created orchestrator agent: {orchestrator.id}")

    # 4) Send a test request to the orchestrator.
    #    It should call the coder & tester tools and then summarize.
    user_task = (
        "We are building a tiny library.\n\n"
        "Task: Implement a Python function "
        "`add(a: int, b: int) -> int` and then generate pytest tests for it.\n\n"
        "Workflow:\n"
        "- Call the Coder tool to write the implementation.\n"
        "- Call the Tester tool to write tests.\n"
        "- Store code + tests in your project_log memory.\n"
        "- Return a short human summary plus the final code and tests."
    )

    response = client.agents.messages.create(
        agent_id=orchestrator.id,
        messages=[
            {
                "role": "user",
                "content": user_task,
            }
        ],
    )

    print("\n=== Orchestrator response ===\n")

    # Prefer output_text if available, otherwise dump messages
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        print(output_text)
    else:
        for msg in response.messages:
            print(msg)


if __name__ == "__main__":
    main()
