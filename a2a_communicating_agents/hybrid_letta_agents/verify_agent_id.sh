#!/bin/bash
# Quick verification of Agent_66 ID

echo "========================================="
echo "Agent_66 ID Verification"
echo "========================================="
echo ""

FULL_ID=$(grep "VOICE_PRIMARY_AGENT_ID" .env | cut -d'=' -f2)
LAST_8="${FULL_ID: -8}"

echo "Full Agent ID:  $FULL_ID"
echo "Last 8 chars:   $LAST_8"
echo ""
echo "When you ask the voice agent a question, you should HEAR:"
echo "  [DEBUG: Using Agent ID $LAST_8]"
echo ""
echo "If you hear a different ID, the agent is NOT using Agent_66!"
echo "========================================="
