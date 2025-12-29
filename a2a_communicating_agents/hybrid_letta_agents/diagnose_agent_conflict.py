#!/usr/bin/env python3
"""
Diagnostic script to identify Agent_66 room conflict issues.

This script analyzes:
1. Currently running agent processes
2. Active Livekit rooms and participants
3. Recent log patterns showing agent initialization
4. Agent ID consistency across the system
5. Multiple agent instance detection

Usage:
    python3 diagnose_agent_conflict.py
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def check_running_processes():
    """Check for multiple running agent processes."""
    print("\n" + "="*80)
    print("1. CHECKING RUNNING AGENT PROCESSES")
    print("="*80)

    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )

    agent_processes = []
    for line in result.stdout.split('\n'):
        if 'letta_voice_agent' in line and 'grep' not in line:
            agent_processes.append(line)

    print(f"\nFound {len(agent_processes)} agent process(es):")
    for proc in agent_processes:
        print(f"  {proc}")

    if len(agent_processes) > 1:
        print("\n⚠️  WARNING: Multiple agent processes detected!")
        print("   This could cause room conflicts if they're all handling the same room.")

    return len(agent_processes)

async def check_livekit_rooms():
    """Check active Livekit rooms and participants."""
    print("\n" + "="*80)
    print("2. CHECKING LIVEKIT ROOMS AND PARTICIPANTS")
    print("="*80)

    try:
        from livekit_room_manager import RoomManager

        manager = RoomManager()
        try:
            rooms = await manager.list_rooms()

            print(f"\nFound {len(rooms)} active room(s):")

            room_data = []
            for room in rooms:
                participants = await manager.list_participants(room.name)

                print(f"\n  Room: {room.name}")
                print(f"    Created: {datetime.fromtimestamp(room.creation_time)}")
                print(f"    Num participants (metadata): {room.num_participants}")
                print(f"    Participants (actual): {len(participants)}")

                agent_count = 0
                human_count = 0

                for p in participants:
                    is_agent = (
                        'agent' in p.identity.lower() or
                        'bot' in p.identity.lower() or
                        p.identity.startswith('AW_')
                    )

                    if is_agent:
                        agent_count += 1
                        print(f"      - [AGENT] {p.identity} (joined: {datetime.fromtimestamp(p.joined_at)})")
                    else:
                        human_count += 1
                        print(f"      - [HUMAN] {p.identity} (joined: {datetime.fromtimestamp(p.joined_at)})")

                room_data.append({
                    'name': room.name,
                    'agents': agent_count,
                    'humans': human_count,
                    'total': len(participants)
                })

                if agent_count > 1:
                    print(f"\n    ⚠️  WARNING: {agent_count} agents in same room!")
                    print(f"       This causes audio duplication and message routing conflicts!")

            # Summary
            print("\n" + "-"*80)
            print("Room Summary:")
            for rd in room_data:
                status = "✅ OK" if rd['agents'] <= 1 else "❌ CONFLICT"
                print(f"  {status} {rd['name']}: {rd['agents']} agent(s), {rd['humans']} human(s)")

            return room_data

        finally:
            await manager.close()

    except Exception as e:
        print(f"\n❌ Error checking Livekit rooms: {e}")
        import traceback
        traceback.print_exc()
        return []

async def analyze_recent_logs():
    """Analyze recent logs for agent initialization patterns."""
    print("\n" + "="*80)
    print("3. ANALYZING RECENT LOGS")
    print("="*80)

    log_file = Path(__file__).parent / "voice_agent_debug.log"

    if not log_file.exists():
        print(f"\n⚠️  Log file not found: {log_file}")
        return

    # Read last 500 lines
    result = subprocess.run(
        ["tail", "-500", str(log_file)],
        capture_output=True,
        text=True
    )

    lines = result.stdout.split('\n')

    # Count key events
    job_requests = []
    agent_inits = []
    agent_switches = []

    for i, line in enumerate(lines):
        if "Job request received" in line:
            job_requests.append((i, line))
        elif "VOICE AGENT INITIALIZATION" in line:
            agent_inits.append((i, line))
        elif "AGENT SWITCH REQUEST" in line:
            agent_switches.append((i, line))

    print(f"\nRecent activity in last 500 log lines:")
    print(f"  - Job requests: {len(job_requests)}")
    print(f"  - Agent initializations: {len(agent_inits)}")
    print(f"  - Agent switch requests: {len(agent_switches)}")

    # Check for rapid multiple initializations (possible duplicate dispatch)
    if len(agent_inits) > 1:
        print("\n  Recent agent initializations:")
        for idx, line in agent_inits[-5:]:
            print(f"    Line {idx}: {line.strip()}")

    # Check for multiple job requests to same room
    if len(job_requests) > 1:
        print("\n  Recent job requests:")
        for idx, line in job_requests[-5:]:
            print(f"    Line {idx}: {line.strip()}")

    # Check for agent switching activity
    if len(agent_switches) > 0:
        print("\n  Recent agent switch requests:")
        for idx, line in agent_switches[-3:]:
            print(f"    Line {idx}: {line.strip()}")

    return {
        'job_requests': len(job_requests),
        'agent_inits': len(agent_inits),
        'agent_switches': len(agent_switches)
    }

async def check_agent_configuration():
    """Check agent configuration and environment variables."""
    print("\n" + "="*80)
    print("4. CHECKING AGENT CONFIGURATION")
    print("="*80)

    # Check environment variables
    primary_agent_name = os.getenv("VOICE_PRIMARY_AGENT_NAME", "Agent_66")
    primary_agent_id = os.getenv("VOICE_PRIMARY_AGENT_ID", "NOT SET")

    print(f"\nEnvironment configuration:")
    print(f"  VOICE_PRIMARY_AGENT_NAME: {primary_agent_name}")
    print(f"  VOICE_PRIMARY_AGENT_ID: {primary_agent_id}")

    # Check if agent exists in Letta
    try:
        from letta_client import AsyncLetta
        import httpx

        letta_base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
        letta_api_key = os.getenv("LETTA_API_KEY")

        if letta_api_key:
            client = AsyncLetta(api_key=letta_api_key)
        else:
            client = AsyncLetta(base_url=letta_base_url)

        # List agents
        agents = await client.agents.list()
        agents_list = list(agents) if agents else []

        print(f"\nAgents in Letta server ({len(agents_list)} total):")

        agent_66_found = False
        agent_66_id = None

        for agent in agents_list:
            if hasattr(agent, 'name') and agent.name == primary_agent_name:
                agent_66_found = True
                agent_66_id = agent.id
                print(f"  ✅ {agent.name} (ID: {agent.id})")
            elif hasattr(agent, 'name'):
                print(f"     {agent.name} (ID: {agent.id})")

        if agent_66_found:
            print(f"\n✅ {primary_agent_name} found in Letta: {agent_66_id}")

            if primary_agent_id != "NOT SET" and primary_agent_id != agent_66_id:
                print(f"\n⚠️  WARNING: Environment VOICE_PRIMARY_AGENT_ID ({primary_agent_id})")
                print(f"   does not match actual {primary_agent_name} ID ({agent_66_id})!")
        else:
            print(f"\n❌ {primary_agent_name} NOT FOUND in Letta server!")

        return {
            'agent_exists': agent_66_found,
            'agent_id': agent_66_id,
            'env_id': primary_agent_id
        }

    except Exception as e:
        print(f"\n❌ Error checking Letta agents: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_recommendations(process_count, room_data, log_stats, agent_config):
    """Generate recommendations based on diagnostic results."""
    print("\n" + "="*80)
    print("5. RECOMMENDATIONS")
    print("="*80)

    issues_found = []
    recommendations = []

    # Check for multiple processes
    if process_count > 1:
        issues_found.append(f"Multiple agent processes running ({process_count})")
        recommendations.append(
            "CRITICAL: Kill duplicate agent processes:\n"
            "  1. Run: ps aux | grep letta_voice_agent\n"
            "  2. Kill duplicates: kill <PID>\n"
            "  3. Keep only ONE agent process running"
        )

    # Check for multiple agents in rooms
    for rd in room_data:
        if rd['agents'] > 1:
            issues_found.append(f"Multiple agents in room '{rd['name']}' ({rd['agents']} agents)")
            recommendations.append(
                f"Room '{rd['name']}' has {rd['agents']} agents (should be 1):\n"
                f"  Solution: Restart voice system to clear room state:\n"
                f"    ./restart_voice_system.sh"
            )

    # Check for rapid re-initialization
    if log_stats and log_stats['agent_inits'] > 5:
        issues_found.append(f"High agent initialization count ({log_stats['agent_inits']} in last 500 lines)")
        recommendations.append(
            "Excessive agent initializations detected:\n"
            "  Possible causes:\n"
            "    - HTML client reconnecting too frequently\n"
            "    - Room health monitor dispatching duplicates\n"
            "    - Agent switch logic creating multiple instances\n"
            "  Check: Browser console logs and room_health_monitor.py logs"
        )

    # Check for agent ID mismatch
    if agent_config and agent_config.get('agent_exists'):
        if agent_config['env_id'] != "NOT SET" and agent_config['env_id'] != agent_config['agent_id']:
            issues_found.append("Environment VOICE_PRIMARY_AGENT_ID mismatch")
            recommendations.append(
                f"Update .env file with correct agent ID:\n"
                f"  VOICE_PRIMARY_AGENT_ID={agent_config['agent_id']}\n"
                f"  Then restart the voice system"
            )

    # Print results
    if not issues_found:
        print("\n✅ No critical issues detected!")
        print("\nSystem appears healthy. If you're still experiencing problems:")
        print("  - Check browser console logs")
        print("  - Verify audio routing in browser DevTools")
        print("  - Monitor voice_agent_debug.log in real-time: tail -f voice_agent_debug.log")
    else:
        print(f"\n❌ Found {len(issues_found)} issue(s):\n")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")

        print("\n" + "-"*80)
        print("RECOMMENDED ACTIONS:\n")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}\n")

async def main():
    """Run all diagnostics."""
    print("="*80)
    print("LETTA VOICE AGENT - CONFLICT DIAGNOSTIC TOOL")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run diagnostics
    process_count = await check_running_processes()
    room_data = await check_livekit_rooms()
    log_stats = await analyze_recent_logs()
    agent_config = await check_agent_configuration()

    # Generate recommendations
    generate_recommendations(process_count, room_data, log_stats, agent_config)

    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
