#!/usr/bin/env python3
"""
Test script to directly call OpenAI API with the same model used by hybrid_letta__codex_sdk.py
This will help diagnose if the OpenAI API call is hanging or returning errors.
"""

import os
import sys
import time
from datetime import datetime

def test_openai_api():
    """Test direct OpenAI API call"""
    
    print(f"[{datetime.now()}] Starting OpenAI API test...")
    print(f"[{datetime.now()}] Python version: {sys.version}")
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set!")
        return False
    
    print(f"[{datetime.now()}] OPENAI_API_KEY is set (length: {len(api_key)} chars)")
    
    # Import OpenAI
    try:
        print(f"[{datetime.now()}] Importing openai package...")
        import openai
        print(f"[{datetime.now()}] OpenAI package version: {openai.__version__}")
    except ImportError as e:
        print(f"ERROR: Failed to import openai: {e}")
        print("Install with: pip install openai")
        return False
    
    # Create client
    try:
        print(f"[{datetime.now()}] Creating OpenAI client...")
        client = openai.OpenAI(api_key=api_key)
        print(f"[{datetime.now()}] OpenAI client created successfully")
    except Exception as e:
        print(f"ERROR: Failed to create OpenAI client: {e}")
        return False
    
    # Test model - same as hybrid_letta__codex_sdk.py uses
    model = "gpt-4o-mini"
    print(f"\n[{datetime.now()}] Testing model: {model}")
    
    # Simple test message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello World' and nothing else."}
    ]
    
    # Make the API call
    try:
        print(f"[{datetime.now()}] Sending chat completion request...")
        print(f"[{datetime.now()}] Messages: {messages}")
        
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=50,
            timeout=30  # 30 second timeout
        )
        
        elapsed = time.time() - start_time
        print(f"\n[{datetime.now()}] ✅ SUCCESS! Response received in {elapsed:.2f} seconds")
        print(f"[{datetime.now()}] Response ID: {response.id}")
        print(f"[{datetime.now()}] Model used: {response.model}")
        print(f"[{datetime.now()}] Completion tokens: {response.usage.completion_tokens}")
        print(f"[{datetime.now()}] Prompt tokens: {response.usage.prompt_tokens}")
        print(f"[{datetime.now()}] Total tokens: {response.usage.total_tokens}")
        print(f"\n[{datetime.now()}] Assistant response:")
        print(f"  {response.choices[0].message.content}")
        
        return True
        
    except openai.APITimeoutError as e:
        print(f"\n❌ ERROR: API request timed out after 30 seconds")
        print(f"[{datetime.now()}] {type(e).__name__}: {e}")
        return False
        
    except openai.APIConnectionError as e:
        print(f"\n❌ ERROR: Failed to connect to OpenAI API")
        print(f"[{datetime.now()}] {type(e).__name__}: {e}")
        return False
        
    except openai.RateLimitError as e:
        print(f"\n❌ ERROR: Rate limit exceeded")
        print(f"[{datetime.now()}] {type(e).__name__}: {e}")
        return False
        
    except openai.AuthenticationError as e:
        print(f"\n❌ ERROR: Authentication failed - check your API key")
        print(f"[{datetime.now()}] {type(e).__name__}: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error occurred")
        print(f"[{datetime.now()}] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming_api():
    """Test streaming API call (sometimes hangs are due to streaming issues)"""
    
    print(f"\n{'='*70}")
    print(f"[{datetime.now()}] Testing STREAMING API call...")
    print(f"{'='*70}\n")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return False
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        print(f"[{datetime.now()}] Sending streaming request...")
        start_time = time.time()
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Count from 1 to 5, one number per line."}],
            stream=True,
            timeout=30
        )
        
        print(f"[{datetime.now()}] Streaming response:")
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        
        elapsed = time.time() - start_time
        print(f"\n\n[{datetime.now()}] ✅ Streaming completed in {elapsed:.2f} seconds")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR in streaming: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*70)
    print("OpenAI API Test Script")
    print("="*70)
    
    # Test 1: Standard API call
    success1 = test_openai_api()
    
    # Test 2: Streaming API call
    success2 = test_streaming_api()
    
    # Summary
    print(f"\n{'='*70}")
    print("Test Summary:")
    print(f"  Standard API call: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"  Streaming API call: {'✅ PASSED' if success2 else '❌ FAILED'}")
    print(f"{'='*70}")
    
    sys.exit(0 if (success1 and success2) else 1)
