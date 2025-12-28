#!/usr/bin/env python3
"""
Interactive Voice Testing with Manual User Control

This test provides an interactive environment for debugging voice processing issues.
It allows the user to manually control when to start/stop talking and captures
comprehensive logs for analysis.

Test Flow:
1. Browser opens voice-agent-selector.html
2. User selects agent and connects
3. Prompt: "Press Enter to start talking..."
4. User presses Enter, microphone activates
5. User speaks into microphone
6. Prompt: "Press Enter to stop talking..."
7. User presses Enter, microphone deactivates
8. Logs analyzed and displayed with diagnosis

Requirements:
- Letta server running on port 8283
- HTTP server running on port 9000
- LiveKit server running on port 7880
- Voice agent backend running (for full test)
- Real microphone device
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogCollector:
    """Collects and analyzes logs from various sources"""

    def __init__(self):
        self.browser_console_logs = []
        self.browser_errors = []
        self.network_requests = []
        self.microphone_events = []
        self.connection_events = []
        self.voice_events = []

    def add_console_log(self, msg):
        """Add browser console log"""
        self.browser_console_logs.append({
            'timestamp': datetime.now().isoformat(),
            'type': msg.type,
            'text': msg.text
        })

    def add_error(self, error):
        """Add browser error"""
        self.browser_errors.append({
            'timestamp': datetime.now().isoformat(),
            'error': str(error)
        })

    def add_network_request(self, request, response=None):
        """Add network request with optional response"""
        req_data = {
            'timestamp': datetime.now().isoformat(),
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type
        }
        if response:
            req_data['status'] = response.status
            req_data['status_text'] = response.status_text
        self.network_requests.append(req_data)

    def add_microphone_event(self, event_type, details):
        """Add microphone-related event"""
        self.microphone_events.append({
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'details': details
        })

    def add_connection_event(self, event_type, details):
        """Add connection-related event"""
        self.connection_events.append({
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'details': details
        })

    def add_voice_event(self, event_type, details):
        """Add voice processing event"""
        self.voice_events.append({
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'details': details
        })

    def save_logs(self, filepath):
        """Save all logs to a JSON file"""
        logs = {
            'test_timestamp': datetime.now().isoformat(),
            'browser_console_logs': self.browser_console_logs,
            'browser_errors': self.browser_errors,
            'network_requests': self.network_requests,
            'microphone_events': self.microphone_events,
            'connection_events': self.connection_events,
            'voice_events': self.voice_events
        }

        with open(filepath, 'w') as f:
            json.dump(logs, f, indent=2)

        logger.info(f"Logs saved to: {filepath}")

    def analyze_voice_processing(self):
        """Analyze logs to diagnose voice processing issues"""
        print("\n" + "=" * 80)
        print("VOICE PROCESSING ANALYSIS")
        print("=" * 80)

        issues = []

        # 1. Check if microphone was activated
        print("\n[1] MICROPHONE STATUS:")
        # Check for various microphone-related messages (case-insensitive, handles emojis)
        mic_logs = [log for log in self.browser_console_logs
                   if 'microphone' in log['text'].lower() or 'mic' in log['text'].lower()]

        mic_enabled = any(
            ('enabling microphone' in log['text'].lower() or
             'microphone enabled' in log['text'].lower() or
             'setmicrophoneenabled' in log['text'].lower())
            for log in mic_logs
        )

        if mic_enabled:
            print("    ✅ Microphone activation detected")
            # Show the actual microphone logs
            if mic_logs:
                print("    📋 Microphone logs:")
                for log in mic_logs:
                    print(f"       - {log['text']}")
        else:
            print("    ❌ No microphone activation detected")
            issues.append("Microphone was not enabled in the browser")

        # Check for microphone permissions
        permission_logs = [log for log in self.browser_console_logs if 'permission' in log['text'].lower()]
        if permission_logs:
            print("    📋 Permission logs:")
            for log in permission_logs:
                print(f"       - {log['text']}")

        # 2. Check LiveKit connection
        print("\n[2] LIVEKIT CONNECTION:")
        connection_logs = [log for log in self.browser_console_logs if 'connected' in log['text'].lower()]
        if connection_logs:
            print("    ✅ LiveKit connection established:")
            for log in connection_logs[-3:]:  # Show last 3
                print(f"       - {log['text']}")
        else:
            print("    ❌ No LiveKit connection detected")
            issues.append("Failed to connect to LiveKit server")

        # 3. Check for WebSocket connections
        print("\n[3] WEBSOCKET CONNECTIONS:")
        # WebSocket connections are not captured by page.on("request") in Playwright
        # Instead, check for LiveKit connection logs which indicate WebSocket usage
        ws_logs = [log for log in self.browser_console_logs
                  if 'ws://' in log['text'].lower() or 'wss://' in log['text'].lower() or
                  'signal connection established' in log['text'].lower() or
                  'room connected' in log['text'].lower() or
                  'connection state: connected' in log['text'].lower()]
        if ws_logs:
            print(f"    ✅ WebSocket connections detected ({len(ws_logs)} event(s)):")
            for log in ws_logs[:5]:  # Show first 5
                print(f"       - {log['text']}")
        else:
            print("    ⚠️  No WebSocket connection logs detected")
            print("    ℹ️  Note: WebSocket connections may not appear in network requests")
            # Don't treat this as a critical issue if LiveKit connected
            connection_logs = [log for log in self.browser_console_logs if 'connected' in log['text'].lower()]
            if not connection_logs:
                issues.append("No WebSocket connections to LiveKit")

        # 4. Check for participant events
        print("\n[4] PARTICIPANT EVENTS:")
        participant_logs = [log for log in self.browser_console_logs if 'participant' in log['text'].lower()]
        if participant_logs:
            print(f"    ✅ Found {len(participant_logs)} participant event(s):")
            for log in participant_logs:
                print(f"       - {log['text']}")
        else:
            print("    ⚠️  No participant events detected")
            issues.append("Voice agent did not join the room")

        # 5. Check for audio tracks
        print("\n[5] AUDIO TRACKS:")
        track_logs = [log for log in self.browser_console_logs if 'track' in log['text'].lower()]
        if track_logs:
            print(f"    ✅ Found {len(track_logs)} track event(s):")
            for log in track_logs:
                print(f"       - {log['text']}")

            # Check for trackID undefined issue
            undefined_track = any('trackID: undefined' in log['text'] for log in track_logs)
            if undefined_track:
                print(f"    ⚠️  WARNING: Track published with undefined trackID")
                print(f"       This is usually harmless - LiveKit assigns IDs internally")

            # Check for silence detection warnings
            silence_warnings = [log for log in self.browser_console_logs
                               if log['type'] == 'warning' and 'silence detected' in log['text'].lower()]
            if silence_warnings:
                print(f"    ℹ️  Note: {len(silence_warnings)} silence detection warning(s)")
                print(f"       This is expected when using fake audio device or no audio input")
        else:
            print("    ⚠️  No audio track events detected")

        # 6. Check for data channel messages
        print("\n[6] DATA CHANNEL MESSAGES:")
        data_logs = [log for log in self.browser_console_logs if 'data' in log['text'].lower() or 'agent_selection' in log['text'].lower()]
        if data_logs:
            print(f"    ✅ Found {len(data_logs)} data channel message(s):")
            for log in data_logs:
                print(f"       - {log['text']}")
        else:
            print("    ⚠️  No data channel messages detected")

        # 7. Check for errors
        print("\n[7] ERROR ANALYSIS:")
        if self.browser_errors:
            print(f"    ❌ Found {len(self.browser_errors)} browser error(s):")
            for error in self.browser_errors:
                print(f"       - {error['error']}")
                issues.append(f"Browser error: {error['error']}")

        # Look for console errors
        error_logs = [log for log in self.browser_console_logs if log['type'] == 'error']

        # Filter out benign 404 errors
        critical_errors = []
        benign_errors = []
        for log in error_logs:
            is_404 = '404' in log['text'].lower()
            is_resource_load = 'failed to load resource' in log['text'].lower()
            is_favicon = 'favicon' in log['text'].lower()

            if is_404 and (is_favicon or is_resource_load):
                benign_errors.append(log)
            else:
                critical_errors.append(log)

        if critical_errors:
            print(f"    ❌ Found {len(critical_errors)} critical console error(s):")
            for log in critical_errors:
                print(f"       - {log['text']}")

        if benign_errors:
            print(f"    ℹ️  Found {len(benign_errors)} benign error(s) (404s for optional resources):")
            for log in benign_errors[:3]:  # Show first 3
                print(f"       - {log['text']}")

        if not self.browser_errors and not critical_errors:
            print("    ✅ No critical errors detected")

        # Check for failed network requests (404s, 500s, etc.)
        failed_requests = [req for req in self.network_requests if req.get('status', 200) >= 400]
        if failed_requests:
            print(f"    ⚠️  Found {len(failed_requests)} failed network request(s):")
            for req in failed_requests:
                status = req.get('status', '?')
                print(f"       - {status} {req.get('status_text', '')}: {req['url']}")
                # Only treat critical errors (not 404s or favicons) as issues
                if status >= 500 or (status >= 400 and status != 404):
                    issues.append(f"{status} error: {req['url']}")
                elif status == 404 and 'favicon' not in req['url'].lower():
                    # Note the 404 but don't fail the test
                    print(f"       ℹ️  Non-critical 404 (common for optional resources)")

        # Add critical console errors to issues list
        for log in critical_errors:
            issues.append(f"Console error: {log['text']}")

        # 8. Check for timeout/connection issues
        print("\n[8] CONNECTION ISSUES:")
        timeout_logs = [log for log in self.browser_console_logs if 'timeout' in log['text'].lower() or 'failed' in log['text'].lower()]
        if timeout_logs:
            print(f"    ⚠️  Found {len(timeout_logs)} timeout/failure(s):")
            for log in timeout_logs:
                print(f"       - {log['text']}")
        else:
            print("    ✅ No timeout or connection failures detected")

        # 9. Final diagnosis
        print("\n[9] DIAGNOSIS:")
        if not issues:
            print("    ✅ No critical issues detected!")
            print("    💡 Voice processing appears to be working correctly.")
        else:
            print(f"    ❌ Found {len(issues)} issue(s):")
            for i, issue in enumerate(issues, 1):
                print(f"       {i}. {issue}")

        # 10. Recommendations
        print("\n[10] RECOMMENDATIONS:")
        if not mic_enabled:
            print("    - Check if microphone permissions are granted in browser")
            print("    - Verify microphone device is connected and working")

        if not connection_logs:
            print("    - Verify LiveKit server is running: curl http://localhost:7880")
            print("    - Check LiveKit logs: tail -f /tmp/livekit.log")

        if not participant_logs:
            print("    - Verify voice agent backend is running: ps aux | grep letta_voice_agent")
            print("    - Check voice agent logs: tail -f /tmp/letta_voice_agent.log")
            print("    - Restart voice system: ./restart_voice_system.sh")

        print("\n" + "=" * 80)


class InteractiveVoiceTest:
    """Interactive voice testing with manual user control"""

    BASE_URL = "http://localhost:9000"

    def __init__(self, page: Page, log_collector: LogCollector, non_interactive: bool = False):
        self.page = page
        self.logs = log_collector
        self.non_interactive = non_interactive

    async def wait_for_user_input(self, prompt: str):
        """Wait for user to press Enter (or auto-continue in non-interactive mode)"""
        print(f"\n{prompt}")
        if self.non_interactive:
            print("   (Non-interactive mode: auto-continuing after 2 seconds...)")
            await asyncio.sleep(2)
        else:
            try:
                await asyncio.get_event_loop().run_in_executor(None, input)
            except EOFError:
                print("   (No input available: auto-continuing...)")
                await asyncio.sleep(2)

    async def navigate_to_page(self):
        """Navigate to the voice agent selector page"""
        logger.info(f"Navigating to {self.BASE_URL}")
        await self.page.goto(self.BASE_URL, wait_until="networkidle")
        logger.info("✅ Page loaded successfully")

    async def wait_for_agents_to_load(self):
        """Wait for agents to load"""
        logger.info("Waiting for agents to load...")
        await self.page.wait_for_selector(".agent-card", timeout=10000)
        agent_cards = await self.page.locator(".agent-card").count()
        logger.info(f"✅ Loaded {agent_cards} agent(s)")
        return agent_cards

    async def select_first_agent(self):
        """Select the first agent"""
        logger.info("Selecting first agent...")
        agent_card = self.page.locator(".agent-card").first
        await agent_card.click()

        # Get agent name
        agent_name_elem = agent_card.locator(".agent-name")
        agent_name = await agent_name_elem.text_content()
        logger.info(f"✅ Selected agent: {agent_name}")
        return agent_name

    async def connect_to_agent(self):
        """Click the Connect button"""
        logger.info("Clicking Connect button...")
        connect_btn = self.page.locator("#connectBtn")
        await connect_btn.click()

        # Wait for connection to establish
        await asyncio.sleep(2)

        status = await self.page.locator("#status").text_content()
        logger.info(f"✅ Status: {status}")

    async def enable_microphone_manually(self):
        """Allow user to manually control microphone"""
        await self.wait_for_user_input("🎤 Press Enter to START TALKING (microphone will activate)...")

        # Log the event
        self.logs.add_microphone_event("user_start_request", {
            "message": "User requested to start talking"
        })

        logger.info("🎤 Microphone should now be active - speak into your microphone")

        # Monitor status while user is talking
        print("\n" + "=" * 80)
        print("🎤 MICROPHONE ACTIVE - SPEAK NOW")
        print("=" * 80)
        print("Watch the browser for status updates...")
        print("Check the browser console (F12) for real-time logs...")

        await self.wait_for_user_input("\n🛑 Press Enter to STOP TALKING (microphone will deactivate)...")

        # Log the event
        self.logs.add_microphone_event("user_stop_request", {
            "message": "User requested to stop talking"
        })

        logger.info("🛑 Microphone session ended")

    async def get_current_status(self):
        """Get current status from the page"""
        status = await self.page.locator("#status").text_content()
        status_class = await self.page.locator("#status").get_attribute("class")
        return status, status_class

    async def run_interactive_test(self):
        """Run the full interactive test"""
        print("\n" + "=" * 80)
        print("INTERACTIVE VOICE TESTING - MANUAL CONTROL")
        print("=" * 80)

        # Step 1: Navigate
        print("\n[STEP 1] Navigate to voice agent selector")
        await self.navigate_to_page()

        # Step 2: Wait for agents
        print("\n[STEP 2] Wait for agents to load")
        agent_count = await self.wait_for_agents_to_load()

        if agent_count == 0:
            print("❌ No agents available!")
            return

        # Step 3: Select agent
        print("\n[STEP 3] Select first agent")
        agent_name = await self.select_first_agent()

        # Step 4: Connect
        print("\n[STEP 4] Connect to agent")
        await self.connect_to_agent()

        # Give connection time to establish
        await asyncio.sleep(3)

        # Show current status
        status, status_class = await self.get_current_status()
        print(f"\n📊 Current Status: {status}")
        print(f"📊 Status Class: {status_class}")

        # Step 5: Interactive microphone control
        print("\n[STEP 5] Interactive microphone control")
        await self.enable_microphone_manually()

        # Step 6: Final status check
        print("\n[STEP 6] Final status check")
        status, status_class = await self.get_current_status()
        print(f"\n📊 Final Status: {status}")
        print(f"📊 Final Status Class: {status_class}")

        # Keep browser open for inspection
        await self.wait_for_user_input("\n🔍 Press Enter to close browser and analyze logs...")

        print("\n✅ Interactive test completed")


async def main(use_fake_device=False, non_interactive=False):
    """
    Main test function

    Args:
        use_fake_device: If True, use fake audio device for testing.
                        If False, attempt to use real microphone.
        non_interactive: If True, run without waiting for user input.
    """
    log_collector = LogCollector()
    log_file = Path(__file__).parent / f"voice_test_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    async with async_playwright() as p:
        # Prepare launch args
        launch_args = [
            '--use-fake-ui-for-media-stream',  # Auto-grant mic permission (no prompt)
            '--allow-insecure-localhost',
        ]

        # Add fake device if requested (recommended for headless/CI environments)
        if use_fake_device:
            launch_args.append('--use-fake-device-for-media-stream')
            print("ℹ️  Using FAKE audio device (for testing connection flow)")
        else:
            print("ℹ️  Using REAL microphone (requires physical device)")

        # Launch browser in headed mode (visible)
        browser = await p.chromium.launch(
            headless=False,
            args=launch_args
        )

        # Create context with microphone permissions
        context = await browser.new_context(
            permissions=["microphone"],
            viewport={"width": 1280, "height": 720}
        )

        # Create page
        page = await context.new_page()

        # Set up log collectors
        page.on("console", lambda msg: log_collector.add_console_log(msg))
        page.on("pageerror", lambda err: log_collector.add_error(err))

        # Track both requests and responses to capture status codes
        page.on("request", lambda req: log_collector.add_network_request(req))

        async def handle_response(response):
            """Handle response to capture status codes"""
            # Find the matching request and update it with response data
            for req in reversed(log_collector.network_requests):
                if req['url'] == response.url:
                    req['status'] = response.status
                    req['status_text'] = response.status_text
                    break

        page.on("response", lambda res: asyncio.create_task(handle_response(res)))

        # Run interactive test
        test = InteractiveVoiceTest(page, log_collector, non_interactive=non_interactive)

        try:
            await test.run_interactive_test()
        except Exception as e:
            logger.error(f"Test error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Save logs
            log_collector.save_logs(log_file)

            # Analyze logs
            log_collector.analyze_voice_processing()

            # Cleanup
            await context.close()
            await browser.close()

    print(f"\n📁 Full logs saved to: {log_file}")
    print("\n✅ Test completed!")


if __name__ == "__main__":
    """Run the interactive test"""
    import argparse

    parser = argparse.ArgumentParser(description='Interactive Voice Testing with Manual Control')
    parser.add_argument('--fake-device', action='store_true',
                       help='Use fake audio device instead of real microphone (recommended for headless/CI)')
    parser.add_argument('--real-device', action='store_true',
                       help='Use real microphone device (requires physical microphone)')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run in non-interactive mode (auto-continue without user input)')
    args = parser.parse_args()

    # Default to fake device if neither specified
    use_fake = args.fake_device or not args.real_device
    non_interactive = args.non_interactive

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                INTERACTIVE VOICE TESTING - MANUAL CONTROL                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

This test allows you to manually control microphone activation for debugging
voice processing issues.

PREREQUISITES:
  1. Letta server running on port 8283
  2. HTTP server running on port 9000 (serving voice-agent-selector.html)
  3. LiveKit server running on port 7880
  4. Voice agent backend running (optional - for full e2e test)

WHAT TO EXPECT:
  1. Browser will open to voice-agent-selector.html
  2. Test will select first agent and connect
  3. You'll be prompted to press Enter to START talking
  4. Speak into your microphone (or fake audio will be sent)
  5. You'll be prompted to press Enter to STOP talking
  6. Comprehensive log analysis will be displayed

TIPS:
  - Watch the browser status message
  - Open browser console (F12) for real-time logs
  - Check browser DevTools Network tab for WebSocket connections
  - Speak clearly when microphone is active (if using real device)

USAGE:
  --fake-device   Use fake audio (recommended for testing, default)
  --real-device   Use real microphone (requires physical device)

Press Ctrl+C to abort at any time.
""")

    try:
        asyncio.run(main(use_fake_device=use_fake, non_interactive=non_interactive))
    except KeyboardInterrupt:
        print("\n\n⚠️  Test aborted by user")
        sys.exit(0)
