#!/usr/bin/env python3
"""
Multi-service CORS proxy for WSL->Windows browser access
Proxies multiple services and adds CORS headers
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json

# Service mappings: proxy_port -> target_service
SERVICES = {
    8284: "http://localhost:8283",  # Letta Server
    3001: "http://localhost:3000",  # Dashboard API (proxy on 3001)
    8081: "http://localhost:8080",  # Office API (proxy on 8081)
}

class MultiCORSProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Proxy GET requests with CORS headers"""
        try:
            # Determine which service to proxy to based on the port we're listening on
            server_port = self.server.server_address[1]
            target_base = SERVICES.get(server_port)

            if not target_base:
                self.send_error(500, f"Unknown proxy port: {server_port}")
                return

            # Forward request to target service
            url = f"{target_base}{self.path}"
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
        server_port = self.server.server_address[1]
        target = SERVICES.get(server_port, "unknown")
        print(f"[Proxy {server_port}→{target}] {format % args}")

def start_proxy_server(port, target):
    """Start a single proxy server on the given port"""
    print(f"🔄 Starting CORS proxy on 0.0.0.0:{port} → {target}")
    server = HTTPServer(('0.0.0.0', port), MultiCORSProxyHandler)
    server.serve_forever()

if __name__ == "__main__":
    import threading

    print("=" * 60)
    print("🚀 Multi-Service CORS Proxy Starting")
    print("=" * 60)

    # Start each proxy in its own thread
    threads = []
    for port, target in SERVICES.items():
        thread = threading.Thread(target=start_proxy_server, args=(port, target), daemon=True)
        thread.start()
        threads.append(thread)
        print(f"✅ Proxy ready: http://172.26.163.131:{port} → {target}")

    print("=" * 60)
    print("🌐 All proxies running. Press Ctrl+C to stop.")
    print("=" * 60)

    # Keep main thread alive
    for thread in threads:
        thread.join()
