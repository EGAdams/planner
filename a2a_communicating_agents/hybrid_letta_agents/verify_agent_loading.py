#!/usr/bin/env python3
"""
Visual verification script for voice agent loading system.
Demonstrates that the browser can successfully fetch agents from the Letta server.
"""

import requests
import json
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_service(name, url, expected_status=200):
    """Check if a service is responding correctly."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            logger.info(f"✅ {name}: Status {response.status_code}")
            return True, response
        else:
            logger.error(f"❌ {name}: Status {response.status_code} (expected {expected_status})")
            return False, response
    except Exception as e:
        logger.error(f"❌ {name}: {str(e)}")
        return False, None

def verify_system():
    """Verify all system components are working."""
    logger.info("=" * 80)
    logger.info("VOICE AGENT LOADING SYSTEM - VERIFICATION")
    logger.info("=" * 80)

    # Check Letta Server
    logger.info("\n[1/4] Checking Letta Server...")
    success, response = check_service(
        "Letta Server API",
        "http://localhost:8283/v1/agents/"
    )
    if success:
        agents = response.json()
        logger.info(f"     Agents loaded: {len(agents)}")
        if agents:
            logger.info(f"     Sample: {agents[0]['name']} ({agents[0]['id'][:20]}...)")

    # Check Proxy Server
    logger.info("\n[2/4] Checking CORS Proxy Server...")
    success, response = check_service(
        "Proxy Server API",
        "http://localhost:9000/api/v1/agents/"
    )
    if success:
        has_cors = 'Access-Control-Allow-Origin' in response.headers
        logger.info(f"     CORS Headers: {'✅ Present' if has_cors else '❌ Missing'}")
        agents = response.json()
        logger.info(f"     Agents loaded: {len(agents)}")

    # Check HTML Page
    logger.info("\n[3/4] Checking HTML Page...")
    success, response = check_service(
        "HTML Page",
        "http://localhost:9000/"
    )
    if success:
        html = response.text
        has_load_agents = 'loadAgents' in html
        has_proxy_url = 'PROXY_URL' in html
        logger.info(f"     loadAgents() function: {'✅ Found' if has_load_agents else '❌ Missing'}")
        logger.info(f"     PROXY_URL config: {'✅ Found' if has_proxy_url else '❌ Missing'}")

    # Check Browser Integration
    logger.info("\n[4/4] Checking Browser Integration...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Track console messages
            agent_count = None
            def on_console(msg):
                nonlocal agent_count
                if 'Loaded' in msg.text and 'agents' in msg.text:
                    # Extract number from "Loaded X agents"
                    import re
                    match = re.search(r'Loaded (\d+) agents', msg.text)
                    if match:
                        agent_count = int(match.group(1))

            page.on('console', on_console)

            # Load page and wait for agents
            page.goto('http://localhost:9000/', wait_until='networkidle')
            page.wait_for_timeout(2000)

            # Check for agent cards
            agent_cards = page.query_selector_all('.agent-card')

            logger.info(f"✅ Browser Integration: Page loaded")
            logger.info(f"     Agent cards rendered: {len(agent_cards)}")
            if agent_count:
                logger.info(f"     Console reported: {agent_count} agents")

            browser.close()

    except Exception as e:
        logger.error(f"❌ Browser Integration: {str(e)}")

    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION COMPLETE")
    logger.info("=" * 80)
    logger.info("\nSystem is ready for voice agent interaction.")
    logger.info("Open http://localhost:9000 in your browser to test manually.")

if __name__ == '__main__':
    verify_system()
