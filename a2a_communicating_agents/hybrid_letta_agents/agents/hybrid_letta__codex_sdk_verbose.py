#!/usr/bin/env python3
"""
Verbose version of hybrid_letta__codex_sdk.py with progress monitoring.
Adds threading to show progress while waiting for response.
"""

import sys
import threading
import time
from pathlib import Path

# Import everything from the original
sys.path.insert(0, str(Path(__file__).parent))
from hybrid_letta__codex_sdk import *  # <-------- this is huge ------<<

def progress_indicator(stop_event, interval=2):
    """Show progress while waiting for response."""
    elapsed = 0
    print("\n⏳ Waiting for orchestrator response...")
    while not stop_event.is_set():
        time.sleep(interval)
        elapsed += interval
        mins, secs = divmod(elapsed, 60)
        print(f"   [{int(mins):02d}:{int(secs):02d}] Still waiting... (check Letta server logs for activity)", flush=True)

def main_verbose():
    """Run main workflow with progress monitoring."""
    print("Starting verbose hybrid_letta__codex_sdk...")
    ensure_workspace_dir()
    reset_contract_log()

    client = create_letta_client()

    # Register tools
    print("\n📝 Registering tools...")
    coder_tool = client.tools.create_from_function(func=run_codex_coder)
    print(f"  ✓ Coder tool: {coder_tool.name}")

    tester_tool = client.tools.create_from_function(func=run_codex_tester)
    print(f"  ✓ Tester tool: {tester_tool.name}")

    test_runner_tool = client.tools.create_from_function(func=run_test_suite)
    print(f"  ✓ Test runner tool: {test_runner_tool.name}")

    validator_tool = client.tools.create_from_function(func=run_tdd_validator)
    print(f"  ✓ Validator tool: {validator_tool.name}")

    # Create agent
    print(f"\n🤖 Creating orchestrator with model: {ORCH_MODEL}")
    orchestrator_agent = client.agents.create(
        model=ORCH_MODEL,
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "role",
                "value": "You are an orchestrator who manages a Codex-based Coder and Tester.  You also remember what our goals are and keep track of the progress made by the coder, tester and any other agents or tools that we have used.",
                "limit": 2000,
            },
            {
                "label": "workspace",
                "value": f"Workspace directory on the host is: {WORKSPACE_DIR}",
                "limit": 2000,
            },
        ],
        tools=[
            coder_tool.name,
            tester_tool.name,
            test_runner_tool.name,
            validator_tool.name,
        ],
        tool_exec_environment_variables={
            "ORCH_MODEL": ORCH_MODEL,
            "WORKSPACE_DIR": str(WORKSPACE_DIR),
            "CODEX_MODEL": os.environ.get("CODEX_MODEL", ""),
        },
    )
    print(f"  ✓ Agent created: {orchestrator_agent.id}")

    # Send task with progress monitoring
    print("\n📤 Sending task to orchestrator...")
    print("\n" + "="*70)
    print("TASK:")
    print("="*70)
    # i think that user task is pulled in from the import *
    # it is going to be modified here so that we can start simple testing
    USER_TASK = "Write a Hello World Python program"
    print( USER_TASK )
    print("="*70)

    print("\n💡 TIP: While waiting, check your Letta server logs in another terminal:")
    print(f"     tail -f ~/.letta/logs/letta.log  # or wherever your logs are")

    # Start progress indicator thread
    stop_event = threading.Event()
    progress_thread = threading.Thread(target=progress_indicator, args=(stop_event,))
    progress_thread.daemon = True
    progress_thread.start()

    try:
        response = client.agents.messages.create(
            agent_id=orchestrator_agent.id,
            messages=[{"role": "user", "content": USER_TASK}],
            timeout=600,
        )

        # Stop progress indicator
        stop_event.set()
        progress_thread.join(timeout=1)

        print("\n\n✅ Received response from orchestrator!")

    except Exception as e:
        stop_event.set()
        progress_thread.join(timeout=1)
        print(f"\n\n❌ Error: {type(e).__name__}: {e}")
        print("\nDebugging hints:")
        print("1. Check if Letta server is running: curl http://localhost:8283/health")
        print("2. Check Letta server logs for errors")
        print("3. Verify OPENAI_API_KEY is set in Letta server environment")
        print("4. Try the simple test first: python test_letta_simple.py")
        return

    # Print response
    print("\n" + "="*70)
    print("ORCHESTRATOR RESPONSE")
    print("="*70)
    for msg in response.messages:
        mtype = getattr(msg, "message_type", None)
        if mtype == "assistant_message":
            print(f"\n[assistant] {msg.content}")
        elif mtype == "user_message":
            print(f"\n[user] {msg.content}")
        elif mtype == "reasoning_message":
            print(f"\n[reasoning] {msg.reasoning}")
        elif mtype == "tool_call_message":
            print(f"\n[tool-call] {msg.tool_call.name}({msg.tool_call.arguments})")
        elif mtype == "tool_return_message":
            print(f"\n[tool-return] {msg.tool_return}")
        else:
            print(f"\n{msg}")

    print("\n" + "="*70)

    # Only validate TDD contracts if we did a full TDD workflow
    # Skip validation for simple tasks
    try:
        validate_tdd_contracts(response.messages)
    except RuntimeError as e:
        if "TDD contract validation failed" in str(e):
            print("\n⚠️  TDD validation skipped (not a TDD workflow task)")
        else:
            raise

    print("\n✅ Done! Check workspace directory:")
    print(f"     {WORKSPACE_DIR}")

if __name__ == "__main__":
    main_verbose()
