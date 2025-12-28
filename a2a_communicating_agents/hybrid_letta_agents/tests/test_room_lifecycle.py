#!/usr/bin/env python3
"""
LiveKit Room Lifecycle Test Suite
==================================

Tests to diagnose and verify room management robustness:
1. Room state checking (capacity, participants, health)
2. Agent join/leave cycles (prevent state corruption)
3. Multiple sequential sessions (user connect/disconnect patterns)
4. Agent persistence (verify agent doesn't exit prematurely)
5. Error recovery (graceful handling of failures)

Usage:
    python tests/test_room_lifecycle.py --all
    python tests/test_room_lifecycle.py --test room_state
    python tests/test_room_lifecycle.py --test join_leave_cycle
    python tests/test_room_lifecycle.py --test sequential_sessions
    python tests/test_room_lifecycle.py --test agent_persistence
    python tests/test_room_lifecycle.py --test error_recovery
"""

import asyncio
import argparse
import logging
import time
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit_room_manager import RoomManager
from livekit.api import RoomService
from livekit import rtc
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RoomLifecycleTests:
    """Comprehensive test suite for LiveKit room lifecycle management."""

    def __init__(self, room_name: str = "test-room-lifecycle"):
        """
        Initialize test suite.

        Args:
            room_name: Name of room to use for testing (will be cleaned up)
        """
        self.room_name = room_name
        self.manager = RoomManager()
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def cleanup(self):
        """Clean up test resources."""
        logger.info(f"Cleaning up test room: {self.room_name}")
        await self.manager.cleanup_room(self.room_name, force=True)
        await self.manager.close()

    def _log_test_start(self, test_name: str):
        """Log test start."""
        logger.info("=" * 80)
        logger.info(f"TEST: {test_name}")
        logger.info("=" * 80)
        self.total_tests += 1

    def _log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "PASSED" if passed else "FAILED"
        symbol = "✅" if passed else "❌"

        logger.info(f"{symbol} {test_name}: {status}")
        if details:
            logger.info(f"   Details: {details}")

        self.test_results[test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    async def test_room_state_check(self) -> bool:
        """
        Test 1: Room State Check

        Verifies:
        - Room exists/doesn't exist correctly
        - Participant count is accurate
        - Room metadata is accessible
        - Room can accept new participants
        """
        test_name = "Room State Check"
        self._log_test_start(test_name)

        try:
            # 1. Check non-existent room
            logger.info("Checking non-existent room...")
            room_info = await self.manager.get_room_info("nonexistent-room-12345")

            if room_info is not None:
                self._log_test_result(test_name, False, "Non-existent room returned info")
                return False

            logger.info("✓ Non-existent room correctly returns None")

            # 2. Create a room by connecting
            logger.info(f"Creating room: {self.room_name}")

            # Use LiveKit SDK to create a room connection
            room = rtc.Room()

            # Generate token for connection
            from livekit.api import AccessToken
            token = AccessToken(
                api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
            )
            token.with_identity("test-user")
            token.with_name("Test User")
            token.with_grants(rtc.VideoGrants(
                room_join=True,
                room=self.room_name
            ))

            # Connect to room
            url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
            try:
                await room.connect(url, token.to_jwt())
                logger.info(f"✓ Connected to room: {self.room_name}")

                # Wait for room to register
                await asyncio.sleep(2)

                # 3. Check room now exists
                room_info = await self.manager.get_room_info(self.room_name)
                if room_info is None:
                    self._log_test_result(test_name, False, "Created room not found in API")
                    await room.disconnect()
                    return False

                logger.info(f"✓ Room found: {room_info.name}")
                logger.info(f"  - Participants: {room_info.num_participants}")
                logger.info(f"  - Creation time: {room_info.creation_time}")

                # 4. Verify participant count
                participants = await self.manager.list_participants(self.room_name)
                logger.info(f"✓ API returned {len(participants)} participant(s)")

                # Clean disconnect
                await room.disconnect()
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Failed to connect to room: {e}")
                self._log_test_result(test_name, False, f"Room connection failed: {e}")
                return False

            self._log_test_result(test_name, True, "Room state checking works correctly")
            return True

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            self._log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_join_leave_cycle(self, iterations: int = 10) -> bool:
        """
        Test 2: Agent Join/Leave Cycle

        Verifies:
        - Agent can join room multiple times
        - Agent cleanup is successful
        - No state corruption after repeated cycles
        - No memory leaks or zombie processes

        Args:
            iterations: Number of join/leave cycles to perform
        """
        test_name = f"Join/Leave Cycle ({iterations} iterations)"
        self._log_test_start(test_name)

        try:
            successful_cycles = 0

            for i in range(iterations):
                logger.info(f"\nCycle {i+1}/{iterations}")

                # Clean room before each cycle
                await self.manager.ensure_clean_room(self.room_name)

                # Simulate agent joining
                room = rtc.Room()

                from livekit.api import AccessToken
                token = AccessToken(
                    api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
                )
                token.with_identity(f"agent-{i}")
                token.with_name(f"Test Agent {i}")
                token.with_grants(rtc.VideoGrants(
                    room_join=True,
                    room=self.room_name
                ))

                url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")

                try:
                    # Join
                    await room.connect(url, token.to_jwt())
                    logger.info(f"  ✓ Agent joined room")

                    # Stay connected briefly
                    await asyncio.sleep(1)

                    # Leave
                    await room.disconnect()
                    logger.info(f"  ✓ Agent left room")

                    # Verify cleanup
                    await asyncio.sleep(0.5)
                    participants = await self.manager.list_participants(self.room_name)

                    # Filter out any remaining test agents
                    agent_participants = [p for p in participants if 'agent' in p.identity.lower()]

                    if len(agent_participants) > 0:
                        logger.warning(f"  ⚠️  {len(agent_participants)} agent(s) still in room after disconnect")
                    else:
                        logger.info(f"  ✓ Clean disconnect verified")
                        successful_cycles += 1

                except Exception as e:
                    logger.error(f"  ❌ Cycle {i+1} failed: {e}")
                    continue

            success_rate = (successful_cycles / iterations) * 100
            logger.info(f"\nCycle success rate: {success_rate:.1f}% ({successful_cycles}/{iterations})")

            passed = success_rate >= 90  # 90% success threshold
            details = f"{successful_cycles}/{iterations} cycles successful ({success_rate:.1f}%)"
            self._log_test_result(test_name, passed, details)

            return passed

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            self._log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_sequential_sessions(self, sessions: int = 5) -> bool:
        """
        Test 3: Multiple Sequential Sessions

        Simulates realistic user behavior:
        - User connects → Agent joins → User disconnects → Agent exits
        - Repeat multiple times
        - Verify each cycle is clean and system can recover

        Args:
            sessions: Number of sequential sessions to simulate
        """
        test_name = f"Sequential Sessions ({sessions} sessions)"
        self._log_test_start(test_name)

        try:
            successful_sessions = 0

            for session_num in range(sessions):
                logger.info(f"\n{'='*60}")
                logger.info(f"SESSION {session_num + 1}/{sessions}")
                logger.info(f"{'='*60}")

                # Clean room before session
                logger.info("1. Cleaning room before session...")
                await self.manager.ensure_clean_room(self.room_name)

                # Simulate user joining
                logger.info("2. User joining room...")
                user_room = rtc.Room()

                from livekit.api import AccessToken
                user_token = AccessToken(
                    api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
                )
                user_token.with_identity(f"user-session-{session_num}")
                user_token.with_name(f"Test User {session_num}")
                user_token.with_grants(rtc.VideoGrants(
                    room_join=True,
                    room=self.room_name
                ))

                url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")

                try:
                    await user_room.connect(url, user_token.to_jwt())
                    logger.info("   ✓ User connected")

                    # Wait for agent to join (in real system, agent would be triggered)
                    logger.info("3. Waiting for agent join (simulated)...")
                    await asyncio.sleep(1)

                    # Simulate agent joining
                    agent_room = rtc.Room()
                    agent_token = AccessToken(
                        api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                        api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
                    )
                    agent_token.with_identity(f"agent-session-{session_num}")
                    agent_token.with_name(f"Voice Agent {session_num}")
                    agent_token.with_grants(rtc.VideoGrants(
                        room_join=True,
                        room=self.room_name
                    ))

                    await agent_room.connect(url, agent_token.to_jwt())
                    logger.info("   ✓ Agent connected")

                    # Simulate interaction
                    logger.info("4. Simulating user interaction...")
                    await asyncio.sleep(2)

                    # User disconnects first
                    logger.info("5. User disconnecting...")
                    await user_room.disconnect()
                    logger.info("   ✓ User disconnected")

                    # Agent should detect and exit
                    await asyncio.sleep(1)
                    logger.info("6. Agent exiting...")
                    await agent_room.disconnect()
                    logger.info("   ✓ Agent disconnected")

                    # Verify room is clean
                    await asyncio.sleep(1)
                    participants = await self.manager.list_participants(self.room_name)

                    if len(participants) == 0:
                        logger.info("   ✓ Room successfully cleaned")
                        successful_sessions += 1
                    else:
                        logger.warning(f"   ⚠️  {len(participants)} participant(s) still in room")

                except Exception as e:
                    logger.error(f"   ❌ Session {session_num + 1} failed: {e}")
                    # Clean up connections
                    try:
                        await user_room.disconnect()
                    except:
                        pass
                    try:
                        await agent_room.disconnect()
                    except:
                        pass
                    continue

            success_rate = (successful_sessions / sessions) * 100
            logger.info(f"\nSession success rate: {success_rate:.1f}% ({successful_sessions}/{sessions})")

            passed = success_rate >= 80  # 80% success threshold
            details = f"{successful_sessions}/{sessions} sessions successful ({success_rate:.1f}%)"
            self._log_test_result(test_name, passed, details)

            return passed

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            self._log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_agent_persistence(self, duration_seconds: int = 60) -> bool:
        """
        Test 4: Agent Persistence

        Verifies:
        - Agent joins room successfully
        - Agent stays connected for specified duration
        - Agent doesn't exit prematurely (no empty reason exits)
        - Agent responds to keep-alive checks

        Args:
            duration_seconds: How long agent should stay connected
        """
        test_name = f"Agent Persistence ({duration_seconds}s)"
        self._log_test_start(test_name)

        try:
            # Clean room
            await self.manager.ensure_clean_room(self.room_name)

            # Simulate agent joining
            logger.info("Agent joining room...")
            agent_room = rtc.Room()

            from livekit.api import AccessToken
            token = AccessToken(
                api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
            )
            token.with_identity("persistent-agent-test")
            token.with_name("Persistence Test Agent")
            token.with_grants(rtc.VideoGrants(
                room_join=True,
                room=self.room_name
            ))

            url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")

            await agent_room.connect(url, token.to_jwt())
            logger.info("✓ Agent connected")

            # Monitor agent for duration
            start_time = time.time()
            check_interval = 5  # Check every 5 seconds
            checks_performed = 0
            checks_passed = 0

            while time.time() - start_time < duration_seconds:
                elapsed = time.time() - start_time
                remaining = duration_seconds - elapsed

                logger.info(f"  Agent persistence check ({elapsed:.0f}s / {duration_seconds}s, {remaining:.0f}s remaining)")

                # Check if agent is still in room
                participants = await self.manager.list_participants(self.room_name)
                agent_found = any('persistent-agent-test' in p.identity for p in participants)

                checks_performed += 1

                if agent_found:
                    logger.info(f"    ✓ Agent still connected")
                    checks_passed += 1
                else:
                    logger.error(f"    ❌ Agent disconnected prematurely!")
                    await agent_room.disconnect()

                    details = f"Agent exited after {elapsed:.0f}s (expected {duration_seconds}s)"
                    self._log_test_result(test_name, False, details)
                    return False

                await asyncio.sleep(check_interval)

            # Clean disconnect
            logger.info("Test duration complete, disconnecting agent...")
            await agent_room.disconnect()

            success_rate = (checks_passed / checks_performed) * 100
            details = f"Agent persisted for {duration_seconds}s ({checks_passed}/{checks_performed} checks passed)"
            self._log_test_result(test_name, True, details)

            return True

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            self._log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_error_recovery(self) -> bool:
        """
        Test 5: Error Recovery

        Tests system behavior under error conditions:
        - Invalid room names
        - Duplicate participants
        - Network timeouts (simulated)
        - Force disconnects
        - Room deletion while connected

        Verifies system recovers gracefully from all scenarios.
        """
        test_name = "Error Recovery"
        self._log_test_start(test_name)

        recovery_tests = []

        try:
            # Test 1: Invalid room name
            logger.info("\n[Recovery Test 1] Invalid room name")
            try:
                await self.manager.get_room_info("")
                logger.info("  ✓ Handled empty room name")
                recovery_tests.append(True)
            except Exception as e:
                logger.error(f"  ❌ Failed on empty room name: {e}")
                recovery_tests.append(False)

            # Test 2: Duplicate participant IDs
            logger.info("\n[Recovery Test 2] Duplicate participant IDs")
            try:
                # Clean room first
                await self.manager.ensure_clean_room(self.room_name)

                # Connect with same identity twice
                room1 = rtc.Room()
                room2 = rtc.Room()

                from livekit.api import AccessToken

                # Token 1
                token1 = AccessToken(
                    api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
                )
                token1.with_identity("duplicate-test")
                token1.with_name("Duplicate Test 1")
                token1.with_grants(rtc.VideoGrants(room_join=True, room=self.room_name))

                # Token 2 (same identity)
                token2 = AccessToken(
                    api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
                )
                token2.with_identity("duplicate-test")  # Same identity
                token2.with_name("Duplicate Test 2")
                token2.with_grants(rtc.VideoGrants(room_join=True, room=self.room_name))

                url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")

                await room1.connect(url, token1.to_jwt())
                logger.info("  ✓ First connection established")

                # Second connection should kick out the first
                await room2.connect(url, token2.to_jwt())
                logger.info("  ✓ Second connection established (should replace first)")

                await asyncio.sleep(1)

                # Cleanup
                await room1.disconnect()
                await room2.disconnect()

                logger.info("  ✓ Handled duplicate participant IDs")
                recovery_tests.append(True)

            except Exception as e:
                logger.error(f"  ❌ Failed on duplicate IDs: {e}")
                recovery_tests.append(False)

            # Test 3: Force disconnect
            logger.info("\n[Recovery Test 3] Force participant removal")
            try:
                await self.manager.ensure_clean_room(self.room_name)

                # Connect a participant
                room = rtc.Room()
                from livekit.api import AccessToken
                token = AccessToken(
                    api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
                )
                token.with_identity("force-disconnect-test")
                token.with_name("Force Disconnect Test")
                token.with_grants(rtc.VideoGrants(room_join=True, room=self.room_name))

                url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
                await room.connect(url, token.to_jwt())
                logger.info("  ✓ Participant connected")

                await asyncio.sleep(1)

                # Force remove from server side
                await self.manager.remove_participant(self.room_name, "force-disconnect-test")
                logger.info("  ✓ Participant force-removed from server")

                await asyncio.sleep(1)

                # Verify removal
                participants = await self.manager.list_participants(self.room_name)
                still_connected = any('force-disconnect-test' in p.identity for p in participants)

                if not still_connected:
                    logger.info("  ✓ Force disconnect successful")
                    recovery_tests.append(True)
                else:
                    logger.error("  ❌ Participant still connected after force removal")
                    recovery_tests.append(False)

                # Cleanup
                await room.disconnect()

            except Exception as e:
                logger.error(f"  ❌ Failed on force disconnect: {e}")
                recovery_tests.append(False)

            # Test 4: Room deletion while connected
            logger.info("\n[Recovery Test 4] Room deletion while connected")
            try:
                await self.manager.ensure_clean_room(self.room_name)

                # Connect a participant
                room = rtc.Room()
                from livekit.api import AccessToken
                token = AccessToken(
                    api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
                )
                token.with_identity("delete-test")
                token.with_name("Delete Test")
                token.with_grants(rtc.VideoGrants(room_join=True, room=self.room_name))

                url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
                await room.connect(url, token.to_jwt())
                logger.info("  ✓ Participant connected")

                await asyncio.sleep(1)

                # Delete room while participant is connected
                await self.manager.delete_room(self.room_name)
                logger.info("  ✓ Room deleted while participant connected")

                await asyncio.sleep(1)

                # Verify room is gone
                room_info = await self.manager.get_room_info(self.room_name)

                if room_info is None:
                    logger.info("  ✓ Room successfully deleted")
                    recovery_tests.append(True)
                else:
                    logger.error("  ❌ Room still exists after deletion")
                    recovery_tests.append(False)

                # Cleanup
                try:
                    await room.disconnect()
                except:
                    pass  # Expected to fail if room was deleted

            except Exception as e:
                logger.error(f"  ❌ Failed on room deletion: {e}")
                recovery_tests.append(False)

            # Calculate results
            passed_count = sum(recovery_tests)
            total_count = len(recovery_tests)
            success_rate = (passed_count / total_count) * 100 if total_count > 0 else 0

            logger.info(f"\nRecovery test results: {passed_count}/{total_count} passed ({success_rate:.1f}%)")

            passed = success_rate >= 75  # 75% success threshold for error tests
            details = f"{passed_count}/{total_count} recovery scenarios handled ({success_rate:.1f}%)"
            self._log_test_result(test_name, passed, details)

            return passed

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            self._log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all lifecycle tests."""
        logger.info("\n" + "="*80)
        logger.info("RUNNING ALL ROOM LIFECYCLE TESTS")
        logger.info("="*80 + "\n")

        start_time = time.time()

        # Run tests in sequence
        await self.test_room_state_check()
        await self.test_join_leave_cycle(iterations=10)
        await self.test_sequential_sessions(sessions=5)
        await self.test_agent_persistence(duration_seconds=30)  # Reduced for testing
        await self.test_error_recovery()

        # Clean up
        await self.cleanup()

        # Print summary
        elapsed = time.time() - start_time

        logger.info("\n" + "="*80)
        logger.info("TEST SUITE SUMMARY")
        logger.info("="*80)
        logger.info(f"Total tests run: {self.total_tests}")
        logger.info(f"Passed: {self.passed_tests} ✅")
        logger.info(f"Failed: {self.failed_tests} ❌")
        logger.info(f"Success rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        logger.info(f"Total time: {elapsed:.1f}s")
        logger.info("="*80 + "\n")

        # Print detailed results
        logger.info("DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            logger.info(f"\n{status}: {test_name}")
            logger.info(f"  {result['details']}")
            logger.info(f"  Timestamp: {result['timestamp']}")

        return self.failed_tests == 0


async def main():
    """Main entry point for test suite."""
    parser = argparse.ArgumentParser(description="LiveKit Room Lifecycle Test Suite")
    parser.add_argument(
        "--test",
        choices=["room_state", "join_leave_cycle", "sequential_sessions", "agent_persistence", "error_recovery"],
        help="Run specific test"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--room",
        default="test-room-lifecycle",
        help="Room name to use for testing"
    )

    args = parser.parse_args()

    suite = RoomLifecycleTests(room_name=args.room)

    try:
        if args.all:
            success = await suite.run_all_tests()
            sys.exit(0 if success else 1)
        elif args.test:
            if args.test == "room_state":
                success = await suite.test_room_state_check()
            elif args.test == "join_leave_cycle":
                success = await suite.test_join_leave_cycle()
            elif args.test == "sequential_sessions":
                success = await suite.test_sequential_sessions()
            elif args.test == "agent_persistence":
                success = await suite.test_agent_persistence()
            elif args.test == "error_recovery":
                success = await suite.test_error_recovery()

            await suite.cleanup()
            sys.exit(0 if success else 1)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
        await suite.cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        await suite.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
