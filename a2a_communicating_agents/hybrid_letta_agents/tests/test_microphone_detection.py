#!/usr/bin/env python3
"""
Simple test to verify microphone detection with fake devices
"""

import asyncio
import http.server
import socketserver
import threading
import time
from playwright.async_api import async_playwright


async def test_microphone_with_fake_devices():
    """Test microphone detection using fake media devices"""

    # Start a simple HTTP server
    PORT = 18766
    html_content = """<!DOCTYPE html>
<html>
<head><title>Microphone Test</title></head>
<body><h1>Testing Microphone Detection</h1></body>
</html>"""

    class MyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())

        def log_message(self, format, *args):
            pass  # Suppress logs

    httpd = socketserver.TCPServer(("", PORT), MyHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    try:
        async with async_playwright() as p:
            # Launch with fake device flags (same as updated test)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--use-fake-device-for-media-stream',
                    '--use-fake-ui-for-media-stream',
                ])

            context = await browser.new_context(permissions=['microphone'])
            page = await context.new_page()

            await page.goto(f'http://localhost:{PORT}')

            # Use the same JavaScript as the updated test
            device_info = await page.evaluate("""
                async () => {
                    const debugInfo = {
                        hasNavigator: typeof navigator !== 'undefined',
                        hasMediaDevices: typeof navigator !== 'undefined' && 'mediaDevices' in navigator,
                        hasGetUserMedia: typeof navigator !== 'undefined' && navigator.mediaDevices && 'getUserMedia' in navigator.mediaDevices,
                        hasEnumerateDevices: typeof navigator !== 'undefined' && navigator.mediaDevices && 'enumerateDevices' in navigator.mediaDevices,
                        isSecureContext: typeof window !== 'undefined' && window.isSecureContext,
                        protocol: window.location.protocol
                    };

                    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                        return {
                            hasAPI: false,
                            audioInputs: [],
                            allDevices: [],
                            error: 'MediaDevices API not available',
                            debug: debugInfo
                        };
                    }

                    try {
                        const devices = await navigator.mediaDevices.enumerateDevices();
                        const audioInputs = devices.filter(d => d.kind === 'audioinput');

                        return {
                            hasAPI: true,
                            audioInputs: audioInputs.map(d => ({
                                label: d.label || 'Unknown Device',
                                deviceId: d.deviceId,
                                kind: d.kind
                            })),
                            allDevices: devices.map(d => ({
                                label: d.label || 'Unknown Device',
                                deviceId: d.deviceId,
                                kind: d.kind
                            })),
                            error: null,
                            debug: debugInfo
                        };
                    } catch (err) {
                        return {
                            hasAPI: true,
                            audioInputs: [],
                            allDevices: [],
                            error: err.toString(),
                            debug: debugInfo
                        };
                    }
                }
            """)

            # Print results
            print("\n" + "=" * 60)
            print("MICROPHONE DETECTION TEST RESULTS")
            print("=" * 60)
            print(f"MediaDevices API Available: {device_info['hasAPI']}")
            print(f"Is Secure Context: {device_info['debug']['isSecureContext']}")
            print(f"Protocol: {device_info['debug']['protocol']}")

            if device_info['error']:
                print(f"Error: {device_info['error']}")

            print(f"\nTotal Devices: {len(device_info['allDevices'])}")
            for idx, device in enumerate(device_info['allDevices']):
                print(f"  [{idx}] {device['kind']}: {device['label']}")

            print(f"\nAudio Input Devices: {len(device_info['audioInputs'])}")
            for idx, device in enumerate(device_info['audioInputs']):
                print(f"  [{idx}] {device['label']}")

            has_microphone = len(device_info['audioInputs']) > 0

            print("\n" + "=" * 60)
            if has_microphone:
                print("✅ TEST PASSED: Microphone detection working correctly")
                print(f"   Found {len(device_info['audioInputs'])} audio input device(s)")
            else:
                print("❌ TEST FAILED: No microphone devices found")
            print("=" * 60 + "\n")

            await context.close()
            await browser.close()

            return has_microphone

    finally:
        httpd.shutdown()


if __name__ == "__main__":
    result = asyncio.run(test_microphone_with_fake_devices())
    exit(0 if result else 1)
