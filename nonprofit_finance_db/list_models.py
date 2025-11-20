#!/usr/bin/env python3
"""List available Gemini models"""
import os
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    exit(1)

genai.configure(api_key=api_key)

print("Available Gemini models:\n")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")
        print(f"    Display Name: {model.display_name}")
        print(f"    Description: {model.description}")
        print()
