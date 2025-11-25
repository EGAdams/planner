#!/usr/bin/env python3
"""
Simple CORS proxy for Letta server
Adds CORS headers to allow browser access from file:// protocol
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json

LETTA_BASE_URL = "http://localhost:8283"

class CORSProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Proxy GET requests to Letta with CORS headers"""
        try:
            # Forward request to Letta server
            url = f"{LETTA_BASE_URL}{self.path}"
            response = requests.get(url, timeout=5)

            # Send response with CORS headers
            self.send_response(response.status_code)
            self.send_cors_headers()
            self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
            self.end_headers()
            self.wfile.write(response.content)

        except Exception as e:
            self.send_error(500, f"Proxy error: {str(e)}")

    def send_cors_headers(self):
        """Add CORS headers to allow any origin"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[CORS Proxy] {format % args}")

if __name__ == "__main__":
    PORT = 8284  # Different port to avoid conflict with Letta
    HOST = '0.0.0.0'  # Bind to all interfaces for WSL->Windows access
    print(f"🔄 Starting CORS proxy on {HOST}:{PORT}")
    print(f"📡 Proxying requests to {LETTA_BASE_URL}")
    print(f"🌐 Dashboard can now access: http://172.26.163.131:{PORT}/v1/health/")

    server = HTTPServer((HOST, PORT), CORSProxyHandler)
    server.serve_forever()
