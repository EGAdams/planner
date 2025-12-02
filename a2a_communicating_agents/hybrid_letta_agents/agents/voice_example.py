#!/usr/bin/env python3
"""
Voice Utils Example - Demonstrates text-to-speech functionality

This example shows how to use the voice_utils module for text-to-speech
conversion with various configurations.
"""

import os
from voice_utils import text_to_speech


def example_basic():
    """Basic usage example."""
    print("Example 1: Basic text-to-speech")
    result = text_to_speech(
        "Hello! This is a basic example of text to speech.",
        play_audio=False  # Set to True to hear the audio
    )
    if result:
        print(f"  ✓ Audio saved to: {result}")
    else:
        print("  ✗ Failed to generate audio")
    print()


def example_custom_voice():
    """Example with different voice models."""
    print("Example 2: Different voice models")

    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    for voice in voices:
        result = text_to_speech(
            f"This is the {voice} voice speaking.",
            voice=voice,
            play_audio=False
        )
        if result:
            print(f"  ✓ Generated with {voice}: {result}")
        else:
            print(f"  ✗ Failed with {voice}")
    print()


def example_custom_output():
    """Example with custom output location."""
    print("Example 3: Custom output location")

    output_file = "/tmp/custom_voice_output.mp3"
    result = text_to_speech(
        "This will be saved to a custom location.",
        output_file=output_file,
        play_audio=False
    )

    if result:
        print(f"  ✓ Saved to custom location: {result}")
        # Clean up
        if os.path.exists(result):
            os.remove(result)
            print(f"  ✓ Cleaned up: {result}")
    else:
        print("  ✗ Failed to save to custom location")
    print()


def example_environment_config():
    """Example using environment variables."""
    print("Example 4: Environment variable configuration")

    # Save original environment
    original_voice_model = os.getenv("VOICE_MODEL")
    original_output_dir = os.getenv("VOICE_OUTPUT_DIR")

    try:
        # Set custom environment variables
        os.environ["VOICE_MODEL"] = "nova"
        os.environ["VOICE_OUTPUT_DIR"] = "./example_voice_output"

        result = text_to_speech(
            "This uses environment variables for configuration.",
            play_audio=False
        )

        if result:
            print(f"  ✓ Used VOICE_MODEL=nova: {result}")
            print(f"  ✓ Used VOICE_OUTPUT_DIR=./example_voice_output")

            # Clean up
            if os.path.exists(result):
                os.remove(result)
            output_dir = os.path.dirname(result)
            if os.path.exists(output_dir) and not os.listdir(output_dir):
                os.rmdir(output_dir)
        else:
            print("  ✗ Failed with environment variables")

    finally:
        # Restore original environment
        if original_voice_model:
            os.environ["VOICE_MODEL"] = original_voice_model
        elif "VOICE_MODEL" in os.environ:
            del os.environ["VOICE_MODEL"]

        if original_output_dir:
            os.environ["VOICE_OUTPUT_DIR"] = original_output_dir
        elif "VOICE_OUTPUT_DIR" in os.environ:
            del os.environ["VOICE_OUTPUT_DIR"]

    print()


def example_disabled_mode():
    """Example with voice synthesis disabled."""
    print("Example 5: Disabled mode")

    original_enabled = os.getenv("VOICE_ENABLED")

    try:
        os.environ["VOICE_ENABLED"] = "false"

        result = text_to_speech(
            "This should not generate any audio.",
            play_audio=False
        )

        if result is None:
            print("  ✓ Voice synthesis correctly disabled")
        else:
            print(f"  ✗ Unexpected result when disabled: {result}")

    finally:
        if original_enabled:
            os.environ["VOICE_ENABLED"] = original_enabled
        elif "VOICE_ENABLED" in os.environ:
            del os.environ["VOICE_ENABLED"]

    print()


def example_error_handling():
    """Example demonstrating error handling."""
    print("Example 6: Error handling")

    # Empty text
    result = text_to_speech("", play_audio=False)
    if result is None:
        print("  ✓ Empty text correctly handled (returned None)")
    else:
        print(f"  ✗ Unexpected result for empty text: {result}")

    # Whitespace-only text
    result = text_to_speech("   ", play_audio=False)
    if result is None:
        print("  ✓ Whitespace-only text correctly handled (returned None)")
    else:
        print(f"  ✗ Unexpected result for whitespace text: {result}")

    print()


def main():
    """Run all examples."""
    print("=" * 60)
    print("Voice Utils - Text-to-Speech Examples")
    print("=" * 60)
    print()

    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("   Examples will demonstrate functionality but may not")
        print("   actually generate audio without a valid API key.")
        print()

    example_basic()
    example_custom_voice()
    example_custom_output()
    example_environment_config()
    example_disabled_mode()
    example_error_handling()

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
