#!/usr/bin/env python3
"""
Verify JWT token validity and expiration time.
Usage: ./verify_token.py [token]
If no token provided, reads from voice-agent-selector.html
"""

import json
import base64
import sys
import re
from datetime import datetime
from pathlib import Path


def decode_token(token):
    """Decode JWT token and extract payload."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    payload = parts[1]
    # Add padding if needed
    padding = len(payload) % 4
    if padding:
        payload += '=' * (4 - padding)

    return json.loads(base64.urlsafe_b64decode(payload))


def analyze_token(token):
    """Analyze token and display details."""
    try:
        data = decode_token(token)

        issued = datetime.fromtimestamp(data.get('nbf', 0))
        expires = datetime.fromtimestamp(data.get('exp', 0))
        now = datetime.now()

        hours_remaining = (expires.timestamp() - now.timestamp()) / 3600

        print("=" * 60)
        print("JWT TOKEN ANALYSIS")
        print("=" * 60)
        print(f"Subject: {data.get('sub', 'N/A')}")
        print(f"Name: {data.get('name', 'N/A')}")
        print(f"Issuer: {data.get('iss', 'N/A')}")
        print(f"Room: {data.get('video', {}).get('room', 'N/A')}")
        print("-" * 60)
        print(f"Issued:  {issued.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Expires: {expires.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

        if expires > now:
            print(f"Status:  ✓ VALID (expires in {hours_remaining:.1f} hours)")
            return 0
        else:
            print(f"Status:  ✗ EXPIRED ({abs(hours_remaining):.1f} hours ago)")
            print("\nTo generate a fresh token, run:")
            print("  ./update_voice_token.sh")
            return 1

    except Exception as e:
        print(f"ERROR: Failed to decode token: {e}")
        return 2


def main():
    if len(sys.argv) > 1:
        # Token provided as argument
        token = sys.argv[1]
    else:
        # Read from HTML file
        html_file = Path(__file__).parent / 'voice-agent-selector.html'
        if not html_file.exists():
            print(f"ERROR: HTML file not found: {html_file}")
            sys.exit(2)

        with open(html_file) as f:
            content = f.read()
            match = re.search(r"const TOKEN = '([^']+)'", content)
            if not match:
                print("ERROR: Could not find TOKEN in HTML file")
                sys.exit(2)
            token = match.group(1)

    return analyze_token(token)


if __name__ == '__main__':
    sys.exit(main())
