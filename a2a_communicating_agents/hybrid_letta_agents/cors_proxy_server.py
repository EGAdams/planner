#!/usr/bin/env python3
"""
Simple CORS proxy server for the Letta voice agent selector.
Serves static files and proxies API calls to avoid CORS issues.
"""

import http.server
import json
import os
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import urlparse, parse_qs
import logging
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LETTA_API_URL = "http://localhost:8283"
PROJECT_ROOT = Path(__file__).parent

# Load Livekit credentials for token generation
LIVEKIT_ENV_FILE = Path("/home/adamsl/ottomator-agents/livekit-agent/.env")
if LIVEKIT_ENV_FILE.exists():
    with open(LIVEKIT_ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        """Handle GET requests - proxy API calls or serve static files."""
        if self.path.startswith('/api/token'):
            # Generate fresh Livekit token
            try:
                from livekit import api

                # Parse query parameters
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                room = params.get('room', ['test-room'])[0]
                identity = params.get('identity', ['user1'])[0]
                ttl_hours = int(params.get('ttl', ['24'])[0])

                api_key = os.environ.get('LIVEKIT_API_KEY')
                api_secret = os.environ.get('LIVEKIT_API_SECRET')

                if not api_key or not api_secret:
                    raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET not configured")

                # Generate token
                token = api.AccessToken(api_key, api_secret) \
                    .with_identity(identity) \
                    .with_name('User') \
                    .with_ttl(timedelta(hours=ttl_hours)) \
                    .with_grants(api.VideoGrants(
                        room_join=True,
                        room=room,
                        can_publish=True,
                        can_subscribe=True,
                        can_publish_data=True,
                    ))

                jwt = token.to_jwt()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'token': jwt,
                    'url': os.environ.get('LIVEKIT_URL', 'ws://localhost:7880'),
                    'room': room,
                    'ttl_hours': ttl_hours
                }).encode())
                logger.info(f"Generated token for room: {room}, ttl: {ttl_hours}h")

            except ImportError:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "livekit package not installed"}).encode())
                logger.error("livekit package not installed")
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                logger.error(f"Token generation error: {e}")

        elif self.path.startswith('/api/'):
            # Proxy API requests to Letta
            api_endpoint = self.path.replace('/api/', '')
            try:
                response = urlopen(f"{LETTA_API_URL}/{api_endpoint}")
                data = response.read()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
                logger.info(f"Proxied API call: {api_endpoint}")
            except URLError as e:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to reach Letta API: {str(e)}"}).encode())
                logger.error(f"API proxy error: {e}")
        elif self.path == '/' or self.path == '/voice-agent-selector.html':
            # Serve the HTML file
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html_file = PROJECT_ROOT / 'voice-agent-selector.html'
            if html_file.exists():
                with open(html_file, 'rb') as f:
                    self.wfile.write(f.read())
                logger.info("Served voice-agent-selector.html")
            else:
                self.wfile.write(b"<h1>HTML file not found</h1>")
                logger.error(f"HTML file not found: {html_file}")
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    os.chdir(PROJECT_ROOT)
    server = http.server.HTTPServer(('localhost', 9000), CORSRequestHandler)
    logger.info("CORS proxy server starting on http://localhost:9000")
    logger.info("- Serves HTML from http://localhost:9000")
    logger.info("- Proxies Letta API via http://localhost:9000/api/v1/agents/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
