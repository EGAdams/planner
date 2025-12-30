#!/usr/bin/env python3
"""
Network connectivity diagnostic for WSL/Windows communication.
Tests if services are accessible from Windows (via WSL IP).
"""

import socket
import requests
import json
from pathlib import Path

WSL_IP = "172.26.163.131"
LOCALHOST = "127.0.0.1"

def test_port(host, port, service_name):
    """Test if a port is accessible."""
    print(f"\n{'='*60}")
    print(f"Testing {service_name} on {host}:{port}")
    print('='*60)
    
    # TCP socket test
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((host, port))
    sock.close()
    
    if result == 0:
        print(f"✅ TCP connection successful to {host}:{port}")
        return True
    else:
        print(f"❌ TCP connection failed to {host}:{port} (error code: {result})")
        return False

def test_http_endpoint(url, service_name):
    """Test if an HTTP endpoint is accessible."""
    print(f"\n{'='*60}")
    print(f"Testing HTTP endpoint: {service_name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ HTTP request successful")
        print(f"   Status code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if len(response.text) < 500:
            print(f"   Response: {response.text[:200]}")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTP connection failed: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ HTTP request timeout")
        return False
    except Exception as e:
        print(f"❌ HTTP request error: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("WSL/WINDOWS NETWORK CONNECTIVITY DIAGNOSTIC")
    print("="*80)
    print(f"WSL IP Address: {WSL_IP}")
    print(f"Testing from: WSL (localhost)")
    print("="*80)
    
    results = {}
    
    # Test 1: CORS Proxy on localhost
    results['cors_proxy_localhost'] = test_port(LOCALHOST, 9000, "CORS Proxy (localhost)")
    
    # Test 2: CORS Proxy on WSL IP (Windows accessibility)
    results['cors_proxy_wsl_ip'] = test_port(WSL_IP, 9000, "CORS Proxy (WSL IP - Windows view)")
    
    # Test 3: Letta server on localhost
    results['letta_localhost'] = test_port(LOCALHOST, 8283, "Letta Server (localhost)")
    
    # Test 4: Letta server on WSL IP
    results['letta_wsl_ip'] = test_port(WSL_IP, 8283, "Letta Server (WSL IP - Windows view)")
    
    # Test 5: LiveKit server on localhost
    results['livekit_localhost'] = test_port(LOCALHOST, 7880, "LiveKit Server (localhost)")
    
    # Test 6: LiveKit server on WSL IP
    results['livekit_wsl_ip'] = test_port(WSL_IP, 7880, "LiveKit Server (WSL IP - Windows view)")
    
    # Test 7: HTTP endpoints
    results['cors_proxy_http'] = test_http_endpoint("http://localhost:9000", "CORS Proxy HTTP")
    results['letta_http'] = test_http_endpoint("http://localhost:8283/v1/health", "Letta Health Check")
    
    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    
    for service, status in results.items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        print(f"{status_str}: {service}")
    
    # Diagnosis
    print("\n" + "="*80)
    print("DIAGNOSIS AND RECOMMENDATIONS")
    print("="*80)
    
    if not results['cors_proxy_wsl_ip']:
        print("\n❌ CRITICAL ISSUE: CORS Proxy not accessible from WSL IP")
        print("   Problem: Server is bound to 'localhost' instead of '0.0.0.0'")
        print("   Impact: Windows browser cannot connect to CORS proxy")
        print("   Fix: Update cors_proxy_server.py line 297:")
        print("        FROM: server = http.server.HTTPServer(('localhost', 9000), CORSRequestHandler)")
        print("        TO:   server = http.server.HTTPServer(('0.0.0.0', 9000), CORSRequestHandler)")
        
    if not results['letta_wsl_ip']:
        print("\n❌ ISSUE: Letta Server not accessible from WSL IP")
        print("   Problem: Server is bound to 'localhost' instead of '0.0.0.0'")
        print("   Impact: Cannot access Letta API from Windows")
        print("   Fix: Update Letta server configuration to bind to 0.0.0.0:8283")
    
    if results['livekit_wsl_ip']:
        print("\n✅ LiveKit Server is correctly accessible from Windows")
        print("   Binding: 0.0.0.0:7880 (IPv6: :::7880)")
    
    if not results['cors_proxy_wsl_ip'] or not results['letta_wsl_ip']:
        print("\n" + "="*80)
        print("WINDOWS BROWSER ACCESS INSTRUCTIONS")
        print("="*80)
        print(f"Once services are bound to 0.0.0.0, access from Windows browser at:")
        print(f"  http://{WSL_IP}:9000/debug")
        print(f"\nNOTE: You may need to allow Windows Firewall access to these ports.")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
