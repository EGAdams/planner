#!/usr/bin/env bash
#
# Microphone Test Script
# Tests if a microphone is available using Playwright
#

set -e

# Activate virtual environment
VENV_PATH="/home/adamsl/planner/.venv"
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "❌ Virtual environment not found at $VENV_PATH"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/check_microphone.py"

# Create the Python microphone check script
cat > "$PYTHON_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Microphone Availability Test
Checks if a microphone is available in the browser
"""

import asyncio
import sys
from playwright.async_api import async_playwright


async def check_microphone_available():
    """
    Check if a microphone is available in the browser

    Returns:
        bool: True if microphone is available, False otherwise
    """
    import http.server
    import socketserver
    import threading
    import time

    print("Checking for microphone availability...")

    # Start a simple HTTP server in a background thread
    PORT = 18765
    html_content = """<!DOCTYPE html>
<html>
<head><title>Microphone Test</title></head>
<body><h1>Testing Microphone Access</h1></body>
</html>"""

    class MyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())

        def log_message(self, format, *args):
            pass  # Suppress server logs

    httpd = socketserver.TCPServer(("", PORT), MyHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)  # Give server time to start

    async with async_playwright() as p:
        # Launch browser with flags to use fake media devices
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--use-fake-device-for-media-stream',
                '--use-fake-ui-for-media-stream',
            ]
        )

        # Create context with microphone permissions
        context = await browser.new_context(permissions=["microphone"])
        page = await context.new_page()

        try:
            # Navigate to localhost (secure context)
            await page.goto(f"http://localhost:{PORT}")

            # Use JavaScript to check for audio input devices
            device_info = await page.evaluate("""
                async () => {
                    // Check what's available
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
                            error: null
                        };
                    } catch (err) {
                        return {
                            hasAPI: true,
                            audioInputs: [],
                            allDevices: [],
                            error: err.toString()
                        };
                    }
                }
            """)

            # Print detailed device information
            print(f"\nDevice Detection Results:")
            print(f"  MediaDevices API Available: {device_info['hasAPI']}")

            # Print debug info if available
            if 'debug' in device_info:
                print(f"\n  Debug Information:")
                for key, value in device_info['debug'].items():
                    print(f"    {key}: {value}")

            if device_info['error']:
                print(f"\n  Error: {device_info['error']}")

            print(f"\n  Total Devices Found: {len(device_info['allDevices'])}")
            for idx, device in enumerate(device_info['allDevices']):
                print(f"    [{idx}] {device['kind']}: {device['label']}")

            print(f"\n  Audio Input Devices: {len(device_info['audioInputs'])}")
            for idx, device in enumerate(device_info['audioInputs']):
                print(f"    [{idx}] {device['label']} (ID: {device['deviceId']})")

            has_microphone = len(device_info['audioInputs']) > 0

            if has_microphone:
                print("✅ Microphone is available")
                return True
            else:
                print("⚠️  No microphone devices found")
                return False

        except Exception as e:
            print(f"⚠️  Could not check microphone availability: {e}")
            return False
        finally:
            await context.close()
            await browser.close()
            httpd.shutdown()  # Stop the HTTP server


async def main():
    """Main entry point"""
    has_mic = await check_microphone_available()
    sys.exit(0 if has_mic else 1)


if __name__ == "__main__":
    asyncio.run(main())
EOF

# Make the Python script executable
chmod +x "$PYTHON_SCRIPT"

# Check if Playwright is installed
echo "Checking Playwright installation..."
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "❌ Playwright is not installed"
    echo "Please install it with: pip install playwright"
    echo "Then run: playwright install chromium"
    exit 1
fi

# Check if Playwright browsers are installed
if ! python3 -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()" 2>/dev/null; then
    echo "⚠️  Playwright browsers may not be installed"
    echo "Please run: playwright install chromium"
fi

echo ""
echo "========================================="
echo "  MICROPHONE AVAILABILITY TEST"
echo "========================================="
echo ""

# Run the microphone check
python3 "$PYTHON_SCRIPT"
result=$?

echo ""
echo "========================================="
if [ $result -eq 0 ]; then
    echo "  TEST PASSED: Microphone available"
else
    echo "  TEST FAILED: No microphone found"
fi
echo "========================================="
echo ""

# Cleanup
rm -f "$PYTHON_SCRIPT"

exit $result
