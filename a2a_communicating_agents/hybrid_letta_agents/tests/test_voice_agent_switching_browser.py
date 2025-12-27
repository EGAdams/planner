#!/usr/bin/env python3
"""
Voice Agent Switching Browser Test

This test validates the voice agent switching functionality using Playwright
to test the actual browser workflow at http://localhost:9000/

Test Scenario:
1. Navigate to the voice agent selector page
2. Disconnect from any current connection
3. Select a different agent from the dropdown/list
4. Connect to the new agent
5. Verify "Start Speaking..." message appears

Requirements:
- Letta server running on port 8283 (for agent list)
- HTTP server running on port 9000 (serving voice-agent-selector.html)
- LiveKit server running on port 7880 (for actual connection)
"""

import pytest
import asyncio
import re
from playwright.async_api import async_playwright, Page, expect
import logging
import sys

# Configure logging
logging.basicConfig( level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s" )
logger = logging.getLogger( __name__ )


class VoiceAgentSwitchingTest:
    """Test suite for voice agent switching browser functionality"""

    BASE_URL = "http://localhost:9000"
    TEST_TIMEOUT = 30000  # 30 seconds
    AGENT_JOIN_TIMEOUT = 20000  # 20 seconds for agent to join

    def __init__( self, page: Page ):
        self.page = page
        self.console_errors = []  # Track console errors
        self.console_warnings = []  # Track console warnings

        # Capture console messages
        page.on( "console", self._on_console )
        page.on( "pageerror", self._on_page_error )

    def _on_console( self, msg ):
        """Capture console messages and track errors/warnings"""
        text = msg.text
        msg_type = msg.type

        # Log all console messages
        print( f"[Browser Console] {msg_type.upper()}: {text}" )
        if msg_type == "error":
            logger.error( f"Browser console ERROR: {text}" )
            self.console_errors.append( text )
        elif msg_type == "warning":
            logger.warning( f"Browser console WARNING: {text}" )
            self.console_warnings.append( text )
        else:
            logger.info( f"Browser console: {text}" )

    def _on_page_error( self, err ):
        """Capture page errors"""
        error_text = str( err )
        logger.error( f"Browser page error: {error_text}" )
        self.console_errors.append( error_text )

    def get_errors( self ):
        """Get all captured errors"""
        return self.console_errors.copy()

    def clear_errors( self ):
        """Clear captured errors"""
        self.console_errors.clear()
        self.console_warnings.clear()

    async def navigate_to_page( self ):
        """Navigate to the voice agent selector page"""
        logger.info( f"Navigating to {self.BASE_URL}" )
        await self.page.goto( self.BASE_URL, wait_until="networkidle" )
        await expect(
            self.page
        ).to_have_title( "Letta Voice Agent - Multi-Agent Selector" )
        logger.info( "✅ Page loaded successfully" )

    async def check_microphone_available( self ):
        """
        Check if a microphone is available in the browser

        Returns:
            bool: True if microphone is available, False otherwise
        """
        logger.info( "Checking for microphone availability..." )

        try:
            # Use JavaScript to check for audio input devices
            has_microphone = await self.page.evaluate( """
                async () => {
                    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                        return false;
                    }
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    const audioInputs = devices.filter(d => d.kind === 'audioinput');
                    return audioInputs.length > 0;
                }
            """ )

            if has_microphone:
                logger.info( "✅ Microphone is available" )
            else:
                logger.warning( "⚠️  No microphone devices found" )

            return has_microphone

        except Exception as e:
            logger.warning( f"⚠️  Could not check microphone availability: {e}" )
            return False

    async def wait_for_agents_to_load( self ):
        """Wait for agents to load from Letta server"""
        logger.info( "Waiting for agents to load..." )

        # Wait for status to show agents loaded
        status_element = self.page.locator( "#status" )

        # Wait for either success or error state (max 10 seconds)
        try:
            await status_element.wait_for( state="visible", timeout=10000 )

            # Check if we got an error loading agents
            status_class = await status_element.get_attribute( "class" )
            if "error" in status_class:
                status_text = await status_element.text_content()
                raise Exception( f"Failed to load agents: {status_text}" )

            # Wait for agent cards to appear
            await self.page.wait_for_selector( ".agent-card", timeout=5000 )

            # Count agents
            agent_cards = await self.page.locator( ".agent-card" ).count()
            logger.info( f"✅ Loaded {agent_cards} agent(s)" )

            return agent_cards

        except Exception as e:
            logger.error( f"❌ Error loading agents: {e}" )
            raise

    async def disconnect_if_connected( self ):
        """Click disconnect button if it's enabled"""
        disconnect_btn = self.page.locator( "#disconnectBtn" )

        # Check if disconnect button is enabled
        is_disabled = await disconnect_btn.is_disabled()

        if not is_disabled:
            logger.info( "Currently connected - clicking Disconnect" )
            await disconnect_btn.click()

            # Wait for status to update to "Disconnected"
            await expect( self.page.locator( "#status" )
                         ).to_contain_text( "Disconnected", timeout=5000 )
            logger.info( "✅ Successfully disconnected" )
            return True
        else:
            logger.info( "Not currently connected - skipping disconnect" )
            return False

    async def select_agent( self, agent_index: int = 0 ):
        """
        Select an agent from the list

        Args:
            agent_index: Index of agent to select (default: 0 = first agent)

        Returns:
            Agent name that was selected
        """
        logger.info( f"Selecting agent at index {agent_index}" )

        # Get all agent cards
        agent_cards = self.page.locator( ".agent-card" )
        agent_count = await agent_cards.count()

        if agent_count == 0:
            raise Exception( "No agents available to select" )

        if agent_index >= agent_count:
            raise Exception(
                f"Agent index {agent_index} out of range (only {agent_count} agents)"
            )

        # Click the agent card
        target_card = agent_cards.nth( agent_index )
        await target_card.click()

        # Wait for card to be selected (has 'selected' class)
        await expect( target_card ).to_have_class( re.compile( "selected" ) )

        # Get agent name
        agent_name_elem = target_card.locator( ".agent-name" )
        agent_name = await agent_name_elem.text_content()

        logger.info( f"✅ Selected agent: {agent_name}" )

        # Verify connect button is now enabled
        connect_btn = self.page.locator( "#connectBtn" )
        await expect( connect_btn ).to_be_enabled()

        return agent_name

    async def connect_to_agent( self ):
        """Click the Connect button"""
        logger.info( "Clicking Connect button" )

        connect_btn = self.page.locator( "#connectBtn" )
        await connect_btn.click()

        # Wait for status to change (either "Connecting..." or error)
        status_element = self.page.locator( "#status" )

        # Give it a moment to update
        await self.page.wait_for_timeout( 1000 )

        # Check if we got an error (e.g., microphone check failed)
        status_class = await status_element.get_attribute( "class" )
        status_text = await status_element.text_content()

        if "error" in status_class:
            logger.error( f"❌ Connection failed with error: {status_text}" )
            raise AssertionError( f"Connection failed: {status_text}" )

        # Otherwise we should see "Connecting..." or "Connected..."
        if "Connecting" not in status_text and "Connected" not in status_text:
            raise AssertionError(
                f"Unexpected status after connect: {status_text}" )

        logger.info( f"✅ Connection initiated: {status_text}" )

    async def wait_for_agent_connection( self, expected_agent_name: str ):
        """
        Wait for the agent to connect and "Start Speaking..." message to appear

        Args:
            expected_agent_name: Name of agent we expect to connect
        """
        logger.info( f"Waiting for agent '{expected_agent_name}' to connect..." )

        status_element = self.page.locator( "#status" )

        # Wait for one of these status messages:
        # - "Agent "<name>" connected! Start speaking..."
        # - "Connected! Waiting for agent..."

        try:
            # Wait for connected state (max 20 seconds for agent to join)
            await expect( status_element ).to_contain_text(
                "Start speaking",
                timeout=self.AGENT_JOIN_TIMEOUT,
                ignore_case=True )

            status_text = await status_element.text_content()
            logger.info( f"✅ Agent connected: {status_text}" )

            # Verify the correct agent name is in the status
            if expected_agent_name not in status_text:
                raise AssertionError(
                    f"Connected to wrong agent. Expected '{expected_agent_name}' "
                    f"but got: {status_text}" )

            # Verify status has 'connected' class
            status_class = await status_element.get_attribute( "class" )
            assert ( "connected" in status_class
                    ), f"Status doesn't have 'connected' class: {status_class}"

            # Check for console errors (device errors, etc.)
            if self.console_errors:
                error_list = "\n  - ".join( self.console_errors )
                raise AssertionError(
                    f"Browser errors detected during connection:\n  - {error_list}"
                )

            logger.info( "✅ Agent connection verified successfully" )
            return True

        except Exception as e:
            # Get current status for debugging
            status_text = await status_element.text_content()
            status_class = await status_element.get_attribute( "class" )
            logger.error(
                f"❌ Connection failed. Status: {status_text}, Class: {status_class}"
            )

            # Log any console errors
            if self.console_errors:
                logger.error( f"Console errors: {self.console_errors}" )

            raise

    async def verify_microphone_enabled( self ):
        """Verify that the microphone is actually enabled"""
        logger.info( "Verifying microphone is enabled..." )

        # Check via JavaScript
        mic_enabled = await self.page.evaluate(
            "() => window.room?.localParticipant?.isMicrophoneEnabled ?? false"
        )

        if not mic_enabled:
            raise AssertionError( "Microphone is not enabled" )

        logger.info( "✅ Microphone is enabled" )
        return True


@pytest.fixture
async def browser_context():
    """Create a Playwright browser context with proper configuration"""
    async with async_playwright() as p:
        # Launch browser with visible UI for debugging (set headless=True for CI)
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI/CD
            slow_mo=500,  # Slow down actions for visibility (remove for CI)
        )

        # Create context with permissions for microphone
        context = await browser.new_context( permissions=[ "microphone" ],
                                            viewport={
                                                "width": 1280,
                                                "height": 720
                                            } )

        # Create page (console handlers will be attached by VoiceAgentSwitchingTest)
        page = await context.new_page()

        yield page

        # Cleanup
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_voice_agent_switching_workflow( browser_context ):
    """
    Test the complete voice agent switching workflow

    Steps:
    1. Load page and wait for agents
    2. Wait for agents to load from Letta server
    3. Check for microphone availability (skip if not available)
    4. Disconnect if currently connected
    5. Select first agent
    6. Connect to agent
    7. Verify connection and "Start Speaking..." message
    8. Verify microphone is enabled
    9. Disconnect from first agent
    10. Select second agent (if available)
    11. Connect to second agent
    12. Verify connection to second agent
    13. Verify microphone is enabled for second agent
    """
    page = browser_context
    test = VoiceAgentSwitchingTest( page )

    logger.info( "=" * 80 )
    logger.info( "VOICE AGENT SWITCHING TEST - FULL WORKFLOW" )
    logger.info( "=" * 80 )

    # Step 1: Navigate to page
    logger.info( "\n[STEP 1] Navigate to voice agent selector page" )
    await test.navigate_to_page()

    # Step 2: Wait for agents to load
    logger.info( "\n[STEP 2] Wait for agents to load from Letta server" )
    agent_count = await test.wait_for_agents_to_load()

    if agent_count < 1:
        pytest.skip( "No agents available - cannot test switching" )

    # Step 3: Check for microphone availability
    logger.info( "\n[STEP 3] Check for microphone availability" )
    has_microphone = await test.check_microphone_available()

    if not has_microphone:
        pytest.skip(
            "No microphone available - cannot test voice functionality" )

    # Step 4: Disconnect if currently connected
    logger.info( "\n[STEP 4] Disconnect from any current connection" )
    await test.disconnect_if_connected()

    # Step 5: Select first agent
    logger.info( "\n[STEP 5] Select first agent" )
    first_agent_name = await test.select_agent( 0 )

    # Step 6: Connect to first agent
    logger.info( "\n[STEP 6] Connect to first agent" )
    await test.connect_to_agent()

    # Step 7: Wait for "Start Speaking..." message
    logger.info(
        "\n[STEP 7] Wait for agent connection and 'Start Speaking...' message" )
    # NOTE: This will fail if voice agent backend is not running or if there are device errors
    await test.wait_for_agent_connection( first_agent_name )

    # Step 8: Verify microphone is enabled
    logger.info( "\n[STEP 8] Verify microphone is enabled" )
    await test.verify_microphone_enabled()

    # Step 9: Test switching to second agent (if available)
    if agent_count >= 2:
        logger.info( "\n[STEP 9] Disconnect from first agent" )
        await test.disconnect_if_connected()

        logger.info( "\n[STEP 10] Select second agent" )
        second_agent_name = await test.select_agent( 1 )

        assert (
            second_agent_name
            != first_agent_name ), "Second agent should be different from first"

        logger.info( "\n[STEP 11] Connect to second agent" )
        await test.connect_to_agent()

        logger.info( "\n[STEP 12] Wait for second agent connection" )
        await test.wait_for_agent_connection( second_agent_name )

        logger.info(
            "\n[STEP 13] Verify microphone is enabled for second agent" )
        await test.verify_microphone_enabled()
    else:
        logger.info(
            "\n⚠️  Only one agent available - cannot test switching between agents"
        )

    logger.info( "\n" + "=" * 80 )
    logger.info( "TEST COMPLETED SUCCESSFULLY" )
    logger.info( "=" * 80 )


@pytest.mark.asyncio
async def test_voice_agent_selection_ui( browser_context ):
    """
    Test just the UI selection workflow without waiting for backend connection

    This test validates:
    - Agent list loads
    - Agent can be selected
    - UI state changes correctly
    - Connect button becomes enabled
    """
    page = browser_context
    test = VoiceAgentSwitchingTest( page )

    logger.info( "=" * 80 )
    logger.info( "VOICE AGENT SELECTION UI TEST (No Backend Required)" )
    logger.info( "=" * 80 )

    # Navigate and load agents
    await test.navigate_to_page()
    agent_count = await test.wait_for_agents_to_load()

    if agent_count < 1:
        pytest.skip( "No agents available" )

    # Disconnect if needed
    await test.disconnect_if_connected()

    # Select agent
    agent_name = await test.select_agent( 0 )

    # Verify UI state
    connect_btn = page.locator( "#connectBtn" )
    await expect( connect_btn ).to_be_enabled()

    status = page.locator( "#status" )
    status_text = await status.text_content()
    assert "Click Connect" in status_text or "selected" in status_text.lower()

    logger.info( "✅ UI selection workflow validated successfully" )


if __name__ == "__main__":
    """Run tests directly with pytest"""
    pytest.main([ __file__, "-v", "-s" ])
