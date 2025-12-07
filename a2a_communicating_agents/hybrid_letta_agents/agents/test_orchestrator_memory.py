#!/usr/bin/env python3
"""
Test if the orchestrator agent remembers TDD workflow progress across multiple tasks.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hybrid_letta__codex_sdk import (
    create_letta_client,
    run_codex_coder,
    WORKSPACE_DIR,
    ORCH_MODEL,
)

def test_orchestrator_memory():
    """Test if orchestrator remembers what tasks it has completed."""
    print("Testing Orchestrator Memory...")
    print("="*70)

    client = create_letta_client()

    # Register the coder tool
    print("\n1. Registering coder tool...")
    coder_tool = client.tools.create_from_function(func=run_codex_coder)
    print(f"   ✓ {coder_tool.name}")

    # Create orchestrator with memory emphasis
    print("\n2. Creating orchestrator with memory...")
    orchestrator = client.agents.create(
        model=ORCH_MODEL,
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "role",
                "value": (
                    "You are an orchestrator who manages a Codex-based Coder. "
                    "You MUST remember and track all tasks you complete, including: "
                    "file paths, what was implemented, and your progress. "
                    "Update this memory block after each task completion."
                ),
                "limit": 3000,
            },
            {
                "label": "completed_tasks",
                "value": "No tasks completed yet.",
                "limit": 4000,
            },
            {
                "label": "workspace",
                "value": f"Workspace: {WORKSPACE_DIR}",
                "limit": 1000,
            },
        ],
        tools=[coder_tool.name],
        tool_exec_environment_variables={
            "ORCH_MODEL": ORCH_MODEL,
            "WORKSPACE_DIR": str(WORKSPACE_DIR),
            "CODEX_MODEL": os.environ.get("CODEX_MODEL", ""),
        },
    )
    print(f"   ✓ Agent: {orchestrator.id}")

    # Task 1: Create a simple function
    print("\n3. Sending Task 1: Create add function...")
    response1 = client.agents.messages.create(
        agent_id=orchestrator.id,
        messages=[{
            "role": "user",
            "content": (
                "Use the coder tool to create a simple Python function in add_simple.py "
                "that adds two numbers. Keep it minimal - just the function, no tests yet."
            )
        }],
        timeout=60,
    )

    print("\n   === Task 1 Response ===")
    for msg in response1.messages:
        if getattr(msg, "message_type", None) == "assistant_message":
            print(f"   {msg.content[:200]}...")

    # Task 2: Create another function
    print("\n4. Sending Task 2: Create multiply function...")
    response2 = client.agents.messages.create(
        agent_id=orchestrator.id,
        messages=[{
            "role": "user",
            "content": (
                "Now use the coder tool to create a multiply function in multiply_simple.py. "
                "Again, keep it simple."
            )
        }],
        timeout=60,
    )

    print("\n   === Task 2 Response ===")
    for msg in response2.messages:
        if getattr(msg, "message_type", None) == "assistant_message":
            print(f"   {msg.content[:200]}...")

    # Memory Test: Ask what was done
    print("\n5. Testing Memory: Asking what tasks were completed...")
    response3 = client.agents.messages.create(
        agent_id=orchestrator.id,
        messages=[{
            "role": "user",
            "content": (
                "What files have you created so far in our conversation? "
                "List them and briefly describe what each one does."
            )
        }],
        timeout=30,
    )

    print("\n   === Memory Test Response ===")
    remembered = False
    for msg in response3.messages:
        if getattr(msg, "message_type", None) == "assistant_message":
            content = msg.content
            print(f"   {content}")
            # Check if agent remembers both files
            if ("add_simple" in content.lower() and "multiply_simple" in content.lower()):
                remembered = True

    # Results
    print("\n" + "="*70)
    print("ORCHESTRATOR MEMORY TEST RESULTS")
    print("="*70)

    if remembered:
        print("✅ SUCCESS: Orchestrator remembers completed tasks!")
        print("   - Remembered creating add_simple.py")
        print("   - Remembered creating multiply_simple.py")
        print("   - Memory is working for tracking workflow progress")
    else:
        print("❌ FAILED: Orchestrator did not remember previous tasks")
        print("   - May not be using memory blocks to track progress")

    # Verify files exist
    print("\n6. Verifying generated files exist...")
    files_to_check = ["add_simple.py", "multiply_simple.py"]
    for fname in files_to_check:
        fpath = WORKSPACE_DIR / fname
        if fpath.exists():
            print(f"   ✓ {fname} exists")
        else:
            print(f"   ✗ {fname} NOT found")

    return remembered

if __name__ == "__main__":
    success = test_orchestrator_memory()
    sys.exit(0 if success else 1)
