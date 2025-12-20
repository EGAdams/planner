#!/usr/bin/env python3
"""
Diagnostic script to check voice agent connectivity and API status.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/adamsl/planner/.env")
load_dotenv("/home/adamsl/ottomator-agents/livekit-agent/.env")

print("=" * 60)
print("VOICE AGENT DIAGNOSTIC")
print("=" * 60)
print()

# Check environment variables
print("1. ENVIRONMENT VARIABLES")
print("-" * 60)
env_vars = {
    "LIVEKIT_URL": os.getenv("LIVEKIT_URL"),
    "LIVEKIT_API_KEY": os.getenv("LIVEKIT_API_KEY"),
    "LIVEKIT_API_SECRET": os.getenv("LIVEKIT_API_SECRET")[:10] + "..." if os.getenv("LIVEKIT_API_SECRET") else None,
    "DEEPGRAM_API_KEY": "SET" if os.getenv("DEEPGRAM_API_KEY") else "NOT SET",
    "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "NOT SET",
    "CARTESIA_API_KEY": "SET" if os.getenv("CARTESIA_API_KEY") else "NOT SET",
    "LETTA_SERVER_URL": os.getenv("LETTA_SERVER_URL", "http://localhost:8283"),
}

for key, value in env_vars.items():
    status = "✅" if value and value != "NOT SET" else "❌"
    print(f"{status} {key}: {value}")

print()
print("2. LETTA SERVER STATUS")
print("-" * 60)

try:
    import requests
    response = requests.get("http://localhost:8283/v1/agents/", timeout=5)
    if response.status_code == 200:
        agents = response.json()
        print(f"✅ Letta server responding ({len(agents)} agents)")
        # Find voice orchestrator
        voice_orch = None
        for agent in agents:
            if agent.get('name') == 'voice_orchestrator':
                voice_orch = agent
                break
        if voice_orch:
            print(f"✅ voice_orchestrator found: {voice_orch['id']}")
        else:
            print("⚠️  voice_orchestrator not found (will be created)")
    else:
        print(f"❌ Letta server returned status {response.status_code}")
except Exception as e:
    print(f"❌ Letta server not accessible: {e}")

print()
print("3. LIVEKIT SERVER STATUS")
print("-" * 60)

try:
    import requests
    response = requests.get("http://localhost:7880/", timeout=5)
    if response.status_code == 200 and response.text == "OK":
        print("✅ Livekit server responding")
    else:
        print(f"⚠️  Livekit server responded but unexpected: {response.text[:50]}")
except Exception as e:
    print(f"❌ Livekit server not accessible: {e}")

print()
print("4. DEEPGRAM API TEST")
print("-" * 60)

deepgram_key = os.getenv("DEEPGRAM_API_KEY")
if deepgram_key:
    try:
        import requests
        # Simple API check - just verify the key format
        if deepgram_key.startswith("sk_"):
            print("✅ Deepgram API key format looks valid")
        else:
            print("⚠️  Deepgram API key format unexpected (should start with 'sk_')")

        # Try a simple API call to verify the key works
        print("   Testing Deepgram API connectivity...")
        headers = {
            "Authorization": f"Token {deepgram_key}",
        }
        response = requests.get("https://api.deepgram.com/v1/projects", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Deepgram API key is valid and working")
        elif response.status_code == 401:
            print("❌ Deepgram API key is INVALID (401 Unauthorized)")
        else:
            print(f"⚠️  Deepgram API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test Deepgram API: {e}")
else:
    print("❌ DEEPGRAM_API_KEY not set")

print()
print("5. VOICE AGENT PROCESS STATUS")
print("-" * 60)

import subprocess
result = subprocess.run(
    ["ps", "aux"],
    capture_output=True,
    text=True
)
voice_agent_lines = [line for line in result.stdout.split('\n') if 'letta_voice_agent' in line and 'grep' not in line]

if voice_agent_lines:
    print(f"✅ Voice agent running ({len(voice_agent_lines)} process(es))")
    for line in voice_agent_lines:
        parts = line.split()
        if 'dev' in line:
            print(f"   ✅ Running in DEV mode (correct)")
        elif 'start' in line:
            print(f"   ❌ Running in START mode (WRONG - should be 'dev')")
        print(f"   PID: {parts[1] if len(parts) > 1 else 'unknown'}")

    if len(voice_agent_lines) > 1:
        print(f"   ⚠️  WARNING: Multiple voice agents running (causes audio cutting)")
else:
    print("❌ Voice agent NOT running")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)

# Calculate overall status
issues = []
if not os.getenv("DEEPGRAM_API_KEY"):
    issues.append("Deepgram API key not set")
if not os.getenv("OPENAI_API_KEY"):
    issues.append("OpenAI API key not set")
if len(voice_agent_lines) == 0:
    issues.append("Voice agent not running")
elif len(voice_agent_lines) > 1:
    issues.append("Multiple voice agents running (duplicates)")
if not any('dev' in line for line in voice_agent_lines):
    issues.append("Voice agent in wrong mode (should be 'dev')")

if issues:
    print("❌ ISSUES FOUND:")
    for issue in issues:
        print(f"   - {issue}")
    print()
    print("RECOMMENDED ACTION:")
    print("   ./restart_voice_system.sh")
else:
    print("✅ All systems appear to be configured correctly")
    print()
    print("If the agent still doesn't respond to speech:")
    print("   1. Check browser console (F12) for errors")
    print("   2. Verify microphone is working (try recording in browser)")
    print("   3. Check voice agent logs for STT transcriptions")
    print("   4. Test Deepgram API key is valid (see test above)")

print()
