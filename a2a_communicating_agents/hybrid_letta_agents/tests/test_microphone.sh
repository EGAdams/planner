#!/usr/bin/env bash
#
# Microphone Test Script
# Tests if a microphone is available using Playwright
#

set -e

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
    print("Checking for microphone availability...")

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)

        # Create context with microphone permissions
        context = await browser.new_context(permissions=["microphone"])
        page = await context.new_page()

        try:
            # Navigate to a blank page
            await page.goto("about:blank")

            # Use JavaScript to check for audio input devices
            has_microphone = await page.evaluate("""
                async () => {
                    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                        return false;
                    }
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    const audioInputs = devices.filter(d => d.kind === 'audioinput');

                    // Print device info for debugging
                    console.log('Found', audioInputs.length, 'audio input device(s)');
                    audioInputs.forEach((device, idx) => {
                        console.log(`  [${idx}] ${device.label || 'Unknown Device'} (ID: ${device.deviceId})`);
                    });

                    return audioInputs.length > 0;
                }
            """)

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
