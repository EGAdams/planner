#!/bin/bash

# Test Voice Output Fix
# Verifies that agent responses are spoken (not just displayed as text)

echo "=================================================="
echo "Voice Output Test Script"
echo "=================================================="
echo ""

echo "Step 1: Verify fix is applied"
echo "------------------------------"
if grep -q "audio_enabled=True" letta_voice_agent_optimized.py; then
    echo "✅ Fix applied: audio_enabled=True found in code"
else
    echo "❌ Fix NOT applied: audio_enabled=True not found"
    echo "   Run: vim letta_voice_agent_optimized.py +1296"
    exit 1
fi
echo ""

echo "Step 2: Check if voice system is running"
echo "-----------------------------------------"
if pgrep -f "letta_voice_agent_optimized.py" > /dev/null; then
    echo "✅ Voice agent process is running"
    echo "   PID(s): $(pgrep -f 'letta_voice_agent_optimized.py' | tr '\n' ' ')"
    echo ""
    echo "⚠️  WARNING: Voice agent is running with OLD code"
    echo "   You MUST restart for fix to take effect:"
    echo "   ./restart_voice_system.sh"
else
    echo "⚠️  Voice agent is NOT running"
    echo "   Start with: ./start_voice_system.sh"
fi
echo ""

echo "Step 3: Verify TTS configuration"
echo "--------------------------------"
if grep -q "tts = openai.TTS\|tts = cartesia.TTS" letta_voice_agent_optimized.py; then
    echo "✅ TTS provider configured in code"
    echo "   Provider: $(grep -o 'tts = .*\.TTS' letta_voice_agent_optimized.py | head -1)"
else
    echo "❌ TTS provider not found in code"
fi
echo ""

echo "Step 4: Check environment variables"
echo "-----------------------------------"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OPENAI_API_KEY is set (length: ${#OPENAI_API_KEY} chars)"
else
    echo "⚠️  OPENAI_API_KEY not set (needed for OpenAI TTS)"
fi

if [ -n "$CARTESIA_API_KEY" ]; then
    echo "✅ CARTESIA_API_KEY is set (length: ${#CARTESIA_API_KEY} chars)"
else
    echo "ℹ️  CARTESIA_API_KEY not set (optional, falls back to OpenAI TTS)"
fi

if [ -n "$TTS_PROVIDER" ]; then
    echo "ℹ️  TTS_PROVIDER override: $TTS_PROVIDER"
fi
echo ""

echo "Step 5: Restart instructions"
echo "----------------------------"
echo "To apply the fix, restart the voice system:"
echo ""
echo "  ./restart_voice_system.sh"
echo ""
echo "Then test with:"
echo "  1. Open http://localhost:9000"
echo "  2. Connect to voice room"
echo "  3. Ask: 'What time is it?'"
echo "  4. Expected: HEAR the answer (not just see text)"
echo ""

echo "Step 6: Monitor voice output"
echo "----------------------------"
echo "After restarting, monitor logs for TTS activity:"
echo ""
echo "  tail -f voice_agent_debug.log | grep -E 'TTS|audio|🔊|tts_node'"
echo ""
echo "Expected log entries:"
echo "  - 'Using OpenAI TTS' or 'Using Cartesia TTS'"
echo "  - 'tts_node processing...'"
echo "  - 'Audio frames published...'"
echo ""

echo "=================================================="
echo "Test Checklist"
echo "=================================================="
echo ""
echo "Before testing:"
echo "  [ ] Fix applied (audio_enabled=True)"
echo "  [ ] Voice system restarted"
echo "  [ ] Environment variables set"
echo ""
echo "During testing:"
echo "  [ ] User asks voice question"
echo "  [ ] Agent SPEAKS response (audio)"
echo "  [ ] Response also appears as text (transcript)"
echo "  [ ] No duplicate audio"
echo ""
echo "If voice output still doesn't work:"
echo "  1. Check browser audio permissions"
echo "  2. Check speaker/headphone connection"
echo "  3. Check Livekit room audio tracks"
echo "  4. Check voice_agent_debug.log for TTS errors"
echo ""
