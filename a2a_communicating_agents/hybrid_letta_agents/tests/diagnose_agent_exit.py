#!/usr/bin/env python3
"""
Agent Exit Diagnostic Tool
===========================

Diagnoses why voice agent is exiting prematurely with empty reason.

Based on user's logs:
    INFO:livekit.agents:process exiting
    21:51:14.696 INFO   livekit.agents   process exiting {"reason": "", "pid": 31248, ...}

This tool:
1. Monitors agent lifecycle in real-time
2. Captures exit reasons and stack traces
3. Checks for premature "room_cleanup" messages
4. Verifies room ID matching (test-room vs RM_H6QwQceiVUUQ)
5. Logs all data messages to identify triggers

Usage:
    python tests/diagnose_agent_exit.py --room test-room --duration 120
"""

import asyncio
import argparse
import logging
import time
import sys
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit import rtc
from livekit.api import AccessToken
from livekit_room_manager import RoomManager

# Configure logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class AgentExitDiagnostic:
    """
    Diagnostic tool to identify why agents exit prematurely.
    """

    def __init__(self, room_name: str = "test-room"):
        self.room_name = room_name
        self.manager = RoomManager()
        self.events_log = []
        self.data_messages = []
        self.start_time = None
        self.agent_joined = False
        self.agent_exited = False
        self.exit_reason = None

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an event with timestamp."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_ms": int((time.time() - self.start_time) * 1000) if self.start_time else 0,
            "type": event_type,
            "details": details
        }
        self.events_log.append(event)
        logger.info(f"[{event_type}] {json.dumps(details, indent=2)}")

    async def diagnose_room_id_mismatch(self):
        """
        Check for room ID mismatch issue.

        User's log shows:
        - Browser connects to "test-room"
        - Agent gets "RM_H6QwQceiVUUQ" (different room!)
        - They never meet
        """
        logger.info("="*80)
        logger.info("DIAGNOSTIC 1: Room ID Mismatch Check")
        logger.info("="*80)

        # Clean room first
        await self.manager.ensure_clean_room(self.room_name)

        # Get room info
        room_info = await self.manager.get_room_info(self.room_name)

        if room_info:
            logger.warning(f"⚠️  Room '{self.room_name}' already exists!")
            logger.warning(f"   Room ID: {room_info.sid if hasattr(room_info, 'sid') else 'N/A'}")
            logger.warning(f"   Participants: {room_info.num_participants}")

            self.log_event("room_exists", {
                "room_name": self.room_name,
                "room_id": room_info.sid if hasattr(room_info, 'sid') else None,
                "participants": room_info.num_participants
            })
        else:
            logger.info(f"✓ Room '{self.room_name}' does not exist (will be created fresh)")
            self.log_event("room_not_exists", {"room_name": self.room_name})

        # Connect as user and check room ID
        logger.info(f"\nConnecting as user to room '{self.room_name}'...")

        user_room = rtc.Room()

        # Set up event handlers to capture room info
        @user_room.on("connected")
        def on_connected():
            logger.info(f"✓ User connected to room")
            logger.info(f"   Room name: {user_room.name}")
            logger.info(f"   Room SID: {user_room.sid if hasattr(user_room, 'sid') else 'N/A'}")

            self.log_event("user_connected", {
                "room_name": user_room.name,
                "room_sid": user_room.sid if hasattr(user_room, 'sid') else None
            })

        token = AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
            api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
        )
        token.with_identity("diagnostic-user")
        token.with_name("Diagnostic User")
        token.with_grants(rtc.VideoGrants(
            room_join=True,
            room=self.room_name
        ))

        url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")

        try:
            await user_room.connect(url, token.to_jwt())

            # Wait for connection to stabilize
            await asyncio.sleep(2)

            # Get room info from API
            room_info_after = await self.manager.get_room_info(self.room_name)

            if room_info_after:
                logger.info(f"\nRoom info from API:")
                logger.info(f"   Name: {room_info_after.name}")
                logger.info(f"   SID: {room_info_after.sid if hasattr(room_info_after, 'sid') else 'N/A'}")
                logger.info(f"   Participants: {room_info_after.num_participants}")

                # Check if room name matches room SID
                if hasattr(room_info_after, 'sid') and room_info_after.name != room_info_after.sid:
                    logger.info(f"✓ Room name and SID are different (normal)")
                    logger.info(f"   Agent should join room NAME: '{room_info_after.name}'")
                    logger.info(f"   NOT room SID: '{room_info_after.sid}'")

                self.log_event("room_info_verified", {
                    "room_name": room_info_after.name,
                    "room_sid": room_info_after.sid if hasattr(room_info_after, 'sid') else None,
                    "participants": room_info_after.num_participants
                })
            else:
                logger.error(f"❌ Room '{self.room_name}' not found in API after connection!")
                self.log_event("room_api_mismatch", {"room_name": self.room_name})

            await user_room.disconnect()

        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            import traceback
            traceback.print_exc()
            self.log_event("connection_failed", {"error": str(e)})

    async def diagnose_premature_cleanup(self, duration_seconds: int = 60):
        """
        Monitor for premature room_cleanup messages.

        User's log shows:
            INFO:__mp_main__:🧹 Room cleanup requested - preparing to exit room

        This is triggered by data_received handler receiving {"type": "room_cleanup"}.
        This tool monitors for such messages and identifies when/why they're sent.
        """
        logger.info("\n" + "="*80)
        logger.info("DIAGNOSTIC 2: Premature Cleanup Detection")
        logger.info("="*80)

        self.start_time = time.time()

        # Clean room
        await self.manager.ensure_clean_room(self.room_name)

        # Connect as both user and agent to monitor messages
        user_room = rtc.Room()
        agent_room = rtc.Room()

        cleanup_detected = False
        agent_switch_detected = False

        # Set up data message monitoring on agent side
        @agent_room.on("data_received")
        def on_agent_data(data_packet: rtc.DataPacket):
            try:
                message_str = data_packet.data.decode('utf-8')
                message_data = json.loads(message_str)

                elapsed = time.time() - self.start_time
                logger.info(f"\n[{elapsed:.1f}s] AGENT received data message:")
                logger.info(f"   Type: {message_data.get('type')}")
                logger.info(f"   Full message: {json.dumps(message_data, indent=2)}")

                self.data_messages.append({
                    "timestamp": datetime.now().isoformat(),
                    "elapsed_seconds": elapsed,
                    "recipient": "agent",
                    "message": message_data
                })

                if message_data.get("type") == "room_cleanup":
                    nonlocal cleanup_detected
                    cleanup_detected = True
                    logger.error(f"❌ ROOM_CLEANUP MESSAGE DETECTED at {elapsed:.1f}s!")
                    logger.error(f"   This will trigger agent to exit!")
                    self.log_event("room_cleanup_detected", {
                        "elapsed_seconds": elapsed,
                        "message": message_data
                    })

                if message_data.get("type") == "agent_selection":
                    nonlocal agent_switch_detected
                    agent_switch_detected = True
                    logger.warning(f"⚠️  AGENT_SELECTION MESSAGE DETECTED at {elapsed:.1f}s!")
                    logger.warning(f"   Agent: {message_data.get('agent_name')} ({message_data.get('agent_id')})")
                    self.log_event("agent_selection_detected", {
                        "elapsed_seconds": elapsed,
                        "message": message_data
                    })

            except Exception as e:
                logger.error(f"Error processing data message: {e}")

        # Set up data monitoring on user side too
        @user_room.on("data_received")
        def on_user_data(data_packet: rtc.DataPacket):
            try:
                message_str = data_packet.data.decode('utf-8')
                message_data = json.loads(message_str)

                elapsed = time.time() - self.start_time
                logger.info(f"\n[{elapsed:.1f}s] USER received data message:")
                logger.info(f"   Type: {message_data.get('type')}")

                self.data_messages.append({
                    "timestamp": datetime.now().isoformat(),
                    "elapsed_seconds": elapsed,
                    "recipient": "user",
                    "message": message_data
                })

            except Exception as e:
                logger.error(f"Error processing user data message: {e}")

        # Connect user
        user_token = AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
            api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
        )
        user_token.with_identity("diagnostic-user")
        user_token.with_name("Diagnostic User")
        user_token.with_grants(rtc.VideoGrants(
            room_join=True,
            room=self.room_name
        ))

        # Connect agent
        agent_token = AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
            api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
        )
        agent_token.with_identity("diagnostic-agent")
        agent_token.with_name("Diagnostic Agent")
        agent_token.with_grants(rtc.VideoGrants(
            room_join=True,
            room=self.room_name
        ))

        url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")

        try:
            logger.info("\nConnecting user...")
            await user_room.connect(url, user_token.to_jwt())
            logger.info("✓ User connected")

            await asyncio.sleep(1)

            logger.info("\nConnecting agent...")
            await agent_room.connect(url, agent_token.to_jwt())
            logger.info("✓ Agent connected")

            self.agent_joined = True
            self.log_event("agent_joined", {"room": self.room_name})

            # Monitor for duration
            logger.info(f"\nMonitoring for {duration_seconds}s...")
            logger.info("Watching for:")
            logger.info("  - room_cleanup messages")
            logger.info("  - agent_selection messages")
            logger.info("  - premature disconnects")

            check_interval = 5
            checks = duration_seconds // check_interval

            for i in range(checks):
                elapsed = time.time() - self.start_time
                remaining = duration_seconds - elapsed

                logger.info(f"\n[Check {i+1}/{checks}] Elapsed: {elapsed:.0f}s, Remaining: {remaining:.0f}s")

                # Check if agent is still connected
                participants = await self.manager.list_participants(self.room_name)
                agent_found = any('diagnostic-agent' in p.identity for p in participants)

                if not agent_found and self.agent_joined and not self.agent_exited:
                    logger.error(f"❌ AGENT EXITED PREMATURELY at {elapsed:.0f}s!")
                    self.agent_exited = True
                    self.log_event("agent_exited_prematurely", {
                        "elapsed_seconds": elapsed,
                        "cleanup_message_detected": cleanup_detected,
                        "agent_switch_detected": agent_switch_detected
                    })
                    break
                elif agent_found:
                    logger.info(f"   ✓ Agent still connected")

                await asyncio.sleep(check_interval)

            # Disconnect
            logger.info("\nTest complete, disconnecting...")
            await user_room.disconnect()
            await agent_room.disconnect()

            # Summary
            logger.info("\n" + "="*80)
            logger.info("DIAGNOSTIC SUMMARY")
            logger.info("="*80)
            logger.info(f"Duration: {duration_seconds}s")
            logger.info(f"Agent joined: {self.agent_joined}")
            logger.info(f"Agent exited prematurely: {self.agent_exited}")
            logger.info(f"room_cleanup detected: {cleanup_detected}")
            logger.info(f"agent_selection detected: {agent_switch_detected}")
            logger.info(f"Data messages received: {len(self.data_messages)}")

            if cleanup_detected:
                logger.error("\n❌ ROOT CAUSE: Browser is sending room_cleanup message!")
                logger.error("   Check browser JavaScript for:")
                logger.error("   - sendDataMessage({type: 'room_cleanup'})")
                logger.error("   - sendDataMessage({type: 'agent_selection'})")
                logger.error("   - These should ONLY be sent when user explicitly changes agents!")

        except Exception as e:
            logger.error(f"❌ Diagnostic failed: {e}")
            import traceback
            traceback.print_exc()
            self.log_event("diagnostic_failed", {"error": str(e)})

    async def save_diagnostic_report(self, output_file: str = "diagnostic_report.json"):
        """Save diagnostic results to JSON file."""
        report = {
            "diagnostic_timestamp": datetime.now().isoformat(),
            "room_name": self.room_name,
            "agent_joined": self.agent_joined,
            "agent_exited": self.agent_exited,
            "exit_reason": self.exit_reason,
            "events": self.events_log,
            "data_messages": self.data_messages,
            "summary": {
                "total_events": len(self.events_log),
                "total_data_messages": len(self.data_messages),
                "cleanup_messages": sum(1 for msg in self.data_messages if msg.get("message", {}).get("type") == "room_cleanup"),
                "agent_selection_messages": sum(1 for msg in self.data_messages if msg.get("message", {}).get("type") == "agent_selection"),
            }
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n✓ Diagnostic report saved to: {output_file}")

    async def cleanup(self):
        """Clean up resources."""
        await self.manager.cleanup_room(self.room_name, force=True)
        await self.manager.close()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Agent Exit Diagnostic Tool")
    parser.add_argument(
        "--room",
        default="test-room",
        help="Room name to test"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="How long to monitor (seconds)"
    )
    parser.add_argument(
        "--output",
        default="diagnostic_report.json",
        help="Output file for diagnostic report"
    )

    args = parser.parse_args()

    diagnostic = AgentExitDiagnostic(room_name=args.room)

    try:
        logger.info("\n" + "="*80)
        logger.info("AGENT EXIT DIAGNOSTIC TOOL")
        logger.info("="*80)
        logger.info(f"Room: {args.room}")
        logger.info(f"Duration: {args.duration}s")
        logger.info(f"Output: {args.output}")
        logger.info("="*80 + "\n")

        # Run diagnostics
        await diagnostic.diagnose_room_id_mismatch()
        await asyncio.sleep(2)
        await diagnostic.diagnose_premature_cleanup(args.duration)

        # Save report
        await diagnostic.save_diagnostic_report(args.output)

        # Cleanup
        await diagnostic.cleanup()

        logger.info("\n✓ Diagnostic complete!")

    except KeyboardInterrupt:
        logger.info("\nDiagnostic interrupted by user")
        await diagnostic.cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        await diagnostic.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
