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
