#!/usr/bin/env python3
"""
Playwright test for voice agent connection from WSL.
Tests LED states and connection behavior.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_voice_agent_connection():
    """Test voice agent connection and capture LED states."""
    
    print("\n" + "="*80)
    print("PLAYWRIGHT VOICE AGENT CONNECTION TEST (WSL)")
    print("="*80)
    
    async with async_playwright() as p:
        # Launch browser (headless for WSL, can change to headed=True if X server available)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
        
        # Navigate to debug page
        print("\n1. Navigating to debug page...")
        try:
            await page.goto("http://localhost:9000/debug", timeout=10000)
            print("✅ Page loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            await browser.close()
            return
        
        # Wait for page to be ready
        await page.wait_for_load_state("domcontentloaded")
        
        # Take initial screenshot
        await page.screenshot(path="/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/screenshot_initial.png")
        print("📸 Screenshot saved: screenshot_initial.png")
        
        # Check initial LED states
        print("\n2. Checking initial LED states...")
        led_states = await check_led_states(page)
        print_led_states(led_states)
        
        # Click connect button
        print("\n3. Clicking Connect button...")
        connect_btn = await page.query_selector("#connectBtn")
        if connect_btn:
            await connect_btn.click()
            print("✅ Connect button clicked")
        else:
            print("❌ Connect button not found")
            await browser.close()
            return
        
        # Wait for connection attempts (10 seconds)
        print("\n4. Waiting for connection attempts (10 seconds)...")
        await asyncio.sleep(10)
        
        # Check LED states after connection attempt
        print("\n5. Checking LED states after connection...")
        led_states = await check_led_states(page)
        print_led_states(led_states)
        
        # Take final screenshot
        await page.screenshot(path="/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/screenshot_connected.png")
        print("\n📸 Screenshot saved: screenshot_connected.png")
        
        # Get event log
        print("\n6. Capturing event log...")
        log_entries = await page.query_selector_all("#debugLog .event-log-entry")
        print(f"\nEvent log ({len(log_entries)} entries):")
        print("-" * 80)
        for entry in log_entries[-20:]:  # Last 20 entries
            text = await entry.inner_text()
            category = await entry.get_attribute("data-category")
            print(f"  [{category.upper()}] {text}")
        
        # Get state information
        print("\n7. Capturing state information...")
        states = {
            'agentId': await get_state_value(page, '#stateAgentId'),
            'agentName': await get_state_value(page, '#stateAgentName'),
            'roomName': await get_state_value(page, '#stateRoomName'),
            'websocketUrl': await get_state_value(page, '#stateWebSocketUrl'),
            'liveKitState': await get_state_value(page, '#stateLiveKitState'),
            'audioState': await get_state_value(page, '#stateAudioState'),
            'participantCount': await get_state_value(page, '#stateParticipantCount'),
            'errorMessage': await get_state_value(page, '#stateErrorMessage'),
        }
        
        print("\nState Values:")
        print("-" * 80)
        for key, value in states.items():
            print(f"  {key}: {value}")
        
        await browser.close()
        
        # Analysis
        print("\n" + "="*80)
        print("ANALYSIS")
        print("="*80)
        analyze_results(led_states, states)

async def check_led_states(page):
    """Check all LED states."""
    leds = {
        'agentSelection': '#ledAgentSelection',
        'webSocket': '#ledWebSocket',
        'liveKitRoom': '#ledLiveKit',
        'audioInput': '#ledAudioInput',
        'audioOutput': '#ledAudioOutput',
        'messageSend': '#ledMessageSend',
        'messageReceive': '#ledMessageReceive',
        'agentResponse': '#ledAgentResponse',
    }
    
    states = {}
    for name, selector in leds.items():
        element = await page.query_selector(selector)
        if element:
            state = await element.get_attribute('data-state')
            states[name] = state or 'unknown'
        else:
            states[name] = 'not_found'
    
    return states

async def get_state_value(page, selector):
    """Get text content of state element."""
    element = await page.query_selector(selector)
    if element:
        return await element.inner_text()
    return 'N/A'

def print_led_states(led_states):
    """Print LED states in a formatted way."""
    print("-" * 80)
    for name, state in led_states.items():
        icon = {
            'connected': '🟢',
            'connecting': '🟡',
            'disconnected': '⚫',
            'error': '🔴',
            'unknown': '❓',
            'not_found': '❌'
        }.get(state, '❓')
        print(f"  {icon} {name}: {state}")
    print("-" * 80)

def analyze_results(led_states, states):
    """Analyze test results and provide diagnosis."""
    issues = []
    
    if led_states.get('agentSelection') == 'connected':
        print("✅ Agent selection successful")
    else:
        issues.append("Agent selection failed")
    
    if led_states.get('webSocket') != 'connected':
        issues.append("WebSocket connection failed - LiveKit server not accessible")
    
    if led_states.get('liveKitRoom') != 'connected':
        issues.append("LiveKit room connection failed")
    
    if led_states.get('audioInput') != 'connected':
        issues.append("Audio input not working - mic permission or track publishing issue")
    
    if states.get('errorMessage') and states['errorMessage'] != '-':
        issues.append(f"Error message: {states['errorMessage']}")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ All checks passed!")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    asyncio.run(test_voice_agent_connection())
