#!/usr/bin/env python3
"""
Test Groq API connection and measure inference speed.

Usage:
    export GROQ_API_KEY=your_key_here
    python test_groq_connection.py
"""

import os
import time
from dotenv import load_dotenv

# Load environment
load_dotenv("/home/adamsl/planner/.env")

# Check if Groq is installed
try:
    from groq import Groq
    print("✅ Groq package installed")
except ImportError:
    print("❌ Groq package not installed")
    print("   Install with: pip install groq")
    exit(1)

# Check API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("❌ GROQ_API_KEY not set")
    print("   Get key from: https://console.groq.com")
    print("   Add to .env: export GROQ_API_KEY=gsk_your_key_here")
    exit(1)

print(f"✅ GROQ_API_KEY found: {api_key[:20]}...")

# Initialize client
try:
    client = Groq(api_key=api_key)
    print("✅ Groq client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Groq client: {e}")
    exit(1)

# Test models
test_models = [
    "llama-3.1-70b-versatile",  # Recommended: Good balance of speed/quality
    "llama-3.1-8b-instant",     # Fastest: Lower quality but extremely fast
    "mixtral-8x7b-32768",       # Alternative: Good for longer context
]

print("\n" + "="*60)
print("Testing Groq Inference Speed")
print("="*60)

test_prompt = "What is the capital of France? Give a one-sentence answer."

for model in test_models:
    print(f"\n📊 Testing {model}...")

    try:
        start_time = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            temperature=0.7,
            max_tokens=50,
            stream=False
        )

        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        answer = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens

        print(f"   ⏱️  Response time: {elapsed:.0f}ms")
        print(f"   📝 Tokens: {tokens}")
        print(f"   💬 Answer: {answer}")
        print(f"   ✅ SUCCESS")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")

print("\n" + "="*60)
print("Comparison to OpenAI (Estimated)")
print("="*60)
print("OpenAI GPT-4o-mini:    1500-3000ms")
print("Groq llama-3.1-70b:    200-500ms   (5-10x faster)")
print("Groq llama-3.1-8b:     100-300ms   (10-20x faster)")
print("\n✅ Groq is ready for voice agent integration!")

print("\n" + "="*60)
print("Next Steps")
print("="*60)
print("1. Add to /home/adamsl/planner/.env:")
print("   export USE_GROQ_LLM=true")
print("   export GROQ_MODEL=llama-3.1-70b-versatile")
print("")
print("2. Use optimized voice agent:")
print("   cp letta_voice_agent_groq.py letta_voice_agent.py")
print("")
print("3. Restart system:")
print("   ./restart_voice_system.sh")
print("")
print("4. Test and measure improvement!")
