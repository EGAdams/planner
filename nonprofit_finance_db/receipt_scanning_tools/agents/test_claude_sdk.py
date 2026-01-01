import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode='acceptEdits',
        cwd="/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/agents"
    )

    async for message in query(
        prompt="write a python function that adds two numbers",
        options=options
    ):
        print(message)


asyncio.run(main())