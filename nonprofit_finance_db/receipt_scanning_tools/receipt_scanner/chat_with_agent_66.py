#!/usr/bin/env python3

from __future__ import annotations
import json, os, sys
import shutil
import subprocess
from pathlib import Path
import textwrap
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import letta_client
from letta_client import Letta

WORKSPACE_DIR = Path(__file__).resolve().parent
CONTRACT_LOG_NAME = "tdd_contracts.jsonl"
AGENT_ID_FILE = WORKSPACE_DIR / "agent_66_id.txt"
ORCH_MODEL = os.environ.get("ORCH_MODEL", "openai/gpt-5-nano")

def create_letta_client() -> Letta:
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    print(f"Using Letta at {base_url}")
    client = Letta(base_url=base_url)
    return client

def get_or_create_agent(client: Letta, force_new: bool = False) -> Any:
    """Get existing agent or create new one."""
    agent_id = None  # Check for existing agent ID
    if AGENT_ID_FILE.exists() and not force_new:
        try:
            agent_id = AGENT_ID_FILE.read_text().strip()
            print(f"Found existing agent ID: {agent_id}")

        except Exception as e:
            print(f"⚠ Error reading agent ID: {e}")
            agent_id = None
            print( "*** Agent 66 not found! Exiting... ***" )
            exit( 1 )

    return agent_id

# ---------- Main ----------
def main( user_message: str, force_new_agent: bool = False ):
    """Send a message to Agent 66."""

    print( "="*70 )
    print( "LETTA AGENT 66 INTERACTION" )
    print( "="*70 )

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
        print( "="*70 )

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
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":              # Check for reset flag
        print( "*** Reset not implemented yet! Exiting... ***" )    # reset_agent()
        sys.exit(0)
  
    if len(sys.argv) > 1:  # Get message from command line or enter interactive mode
        message = " ".join(sys.argv[1:]) # Single message mode
        main(message)

    else:
        # Interactive mode
        print("\n" + "="*70)
        print("INTERACTIVE MODE - Chat with Agent 66")
        print( "="*70 )
        print("Commands: 'exit', 'quit', 'q', 'x', to exit")
        print("="*70 + "\n")

        while True:
            try:
                message = input("\n💬 You: ").strip()

                if not message:
                    continue

                if message.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                main(message)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
