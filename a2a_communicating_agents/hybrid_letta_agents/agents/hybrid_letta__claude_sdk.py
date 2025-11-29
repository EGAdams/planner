"""
Minimal example: Letta as an orchestrator with Claude-based Coder & Tester agents.

- Letta orchestrator = stateful agent with memory + tools
- Tools = Python functions that call Claude Agent SDK:
    - run_claude_coder()  → generates code
    - run_claude_tester() → generates tests for that code

Letta "sees" all tool calls and responses, so code, tests, and outputs
end up in the orchestrator’s transcript + memory blocks.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from typing import List

import anyio
from letta_client import Letta
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)


# ---------- Claude helper layer (Coder & Tester "agents") ----------

async def _run_claude_once(prompt: str, system_prompt: str) -> str:
    """
    Low-level helper: run a single Claude Agent SDK query and return text.
    """
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        max_turns=1,  # keep it single-turn for simplicity
    )

    chunks: List[str] = []

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)

    return "".join(chunks)


def run_claude_coder(spec: str, language: str = "python") -> str:
    """
    Claude Coder Agent.

    Args:
        spec: Natural-language spec for the feature to implement.
        language: Target programming language (e.g. 'python', 'typescript').

    Returns:
        Generated source code as a string.
    """
    system_prompt = (
        "You are a senior software engineer (Coder Agent). "
        "Given a spec and target language, generate clean, "
        "production-quality code in a single file. "
        "Respond primarily with code blocks."
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
        code: Code under test.
        language: Programming language of the code.
        test_framework: e.g. 'pytest', 'unittest', 'jest'.

    Returns:
        Generated test file as a string.
    """
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


# ---------- Letta orchestrator setup ----------

def create_letta_client() -> Letta:
    """
    Create a Letta client for either Cloud or self-hosted.

    Env vars:
      - LETTA_API_KEY  → use Letta Cloud
      - LETTA_BASE_URL → use self-hosted (default http://localhost:8283)
    """
    api_key = os.getenv("LETTA_API_KEY")
    base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")

    if api_key:
        # Letta Cloud
        return Letta(api_key=api_key)  # project="default-project" optional
    else:
        # Self-hosted Letta
        return Letta(base_url=base_url)


def main() -> None:
    # 1) Connect to Letta server
    client = create_letta_client()

    # 2) Register Claude-based tools so the orchestrator can call them
    #    Letta inspects the function docstrings to build the JSON schema.
    coder_tool = client.tools.create_from_function(func=run_claude_coder)
    print(f"Created coder_tool: {coder_tool}")
    print(f"  - ID: {coder_tool.id if hasattr(coder_tool, 'id') else 'N/A'}")
    print(f"  - Name: {coder_tool.name if hasattr(coder_tool, 'name') else 'N/A'}")
    
    tester_tool = client.tools.create_from_function(func=run_claude_tester)
    print(f"Created tester_tool: {tester_tool}")
    print(f"  - ID: {tester_tool.id if hasattr(tester_tool, 'id') else 'N/A'}")
    print(f"  - Name: {tester_tool.name if hasattr(tester_tool, 'name') else 'N/A'}")

    # 3) Create a Letta orchestrator agent that only coordinates + remembers
    #    Use openai/gpt-4o-mini as default (fast and capable)
    model = os.getenv("LETTA_ORCHESTRATOR_MODEL", "openai/gpt-4o-mini")
    embedding = os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-ada-002")
    
    print(f"Creating orchestrator with model: {model}")

    try:
        orchestrator = client.agents.create(
            name="letta_orchestrator",
            model=model,
            embedding=embedding,
            memory_blocks=[
                {
                    "label": "persona",
                    "value": (
                        "You are an orchestration agent that coordinates a Claude-based "
                        "Coder and Tester. You never hand-write code or tests. "
                        "Instead, you:\n"
                        "1) Use the 'run_claude_coder' tool to generate code.\n"
                        "2) Use the 'run_claude_tester' tool to generate tests.\n"
                        "3) Summarize important code + test artifacts into your memory "
                        "blocks for future reuse."
                    ),
                },
                {
                    "label": "project_log",
                    "value": "High-level log of tasks, design decisions, code, and tests.",
                },
            ],
            tools=[
                coder_tool.name,
                tester_tool.name,
            ],
        )
    except Exception as e:
        print(f"Error creating agent: {e}")
        print(f"Trying simplified agent creation...")
        orchestrator = client.agents.create(
            name="  hestrator",
            model=model,
            embedding=embedding,
        )

    print(f"Created orchestrator agent: {orchestrator.id}")

    # 4) Send a task to the orchestrator.
    #    It will decide when to call the coder/tester tools, and all traffic
    #    (tool inputs + outputs) will be stored in its stateful memory.
    response = client.agents.messages.create(
        agent_id=orchestrator.id,
        messages=[
            {
                "role": "user",
                "content": (
                    "We are building a tiny library.\n\n"
                    "Task: Implement a Python function "
                    "`add(a: int, b: int) -> int` and then generate pytest "
                    "tests for it.\n\n"
                    "Workflow:\n"
                    "- Call the Coder tool to write the implementation.\n"
                    "- Call the Tester tool to write tests.\n"
                    "- Store code + tests in your project_log memory.\n"
                    "- Return a short human summary plus the final code and tests."
                ),
            }
        ],
    )

    def extract_assistant_text(messages: List) -> str:
        chunks: List[str] = []
        for msg in messages:
            if getattr(msg, "message_type", None) != "assistant_message":
                continue

            content = getattr(msg, "content", None)
            if isinstance(content, list):
                for block in content:
                    text = getattr(block, "text", None)
                    if text:
                        chunks.append(text)
            elif isinstance(content, str):
                chunks.append(content)

        return "\n\n".join(chunks)

    print("\n=== Orchestrator response ===\n")
    print(extract_assistant_text(response.messages))


if __name__ == "__main__":
    main()
