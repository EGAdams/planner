#!/usr/bin/env python3
"""
Test script to send a message to the orchestrator and see if it routes correctly.
"""
import asyncio
from agent_messaging.orchestrator_chat import send_message_to_orchestrator

async def test():
    print("Sending test message to orchestrator...")
    response = await send_message_to_orchestrator(
        "Please write a simple add function that takes two numbers and returns their sum."
    )
    print(f"\nResponse: {response}")

if __name__ == "__main__":
    asyncio.run(test())
