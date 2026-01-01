"""
Voice Utilities Module - Text-to-Speech Infrastructure

Provides text-to-speech conversion using OpenAI TTS API with configurable
voice models, output handling, and audio playback capabilities.

This module supports:
- Multiple OpenAI voice models (alloy, echo, fable, onyx, nova, shimmer)
- Environment-based configuration
- Cross-platform audio playback
- Graceful error handling
- Unique filename generation

Example:
    >>> from voice_utils import text_to_speech
    >>> audio_path = text_to_speech("Hello world", voice="nova")
    >>> print(f"Audio saved to: {audio_path}")
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

from openai import OpenAI


# Type alias for supported voice models
VoiceModel = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def _get_env_bool(key: str, default: bool = True) -> bool:
    """
    Get boolean value from environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Boolean value
    """
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _play_audio(audio_file_path: str) -> None:
    """
    Play audio file using platform-appropriate method.

    Attempts to use native audio players based on the operating system:
    - macOS: afplay
    - Linux: paplay (PulseAudio), aplay (ALSA), or ffplay (FFmpeg)
    - Windows: Default system player

    Args:
        audio_file_path: Path to audio file to play

    Raises:
        No exceptions raised - errors are logged as warnings
    """
    if not os.path.exists(audio_file_path):
        logger.warning(f"Audio file not found: {audio_file_path}")
        return

    try:
        logger.debug(f"Playing audio file: {audio_file_path}")

        # Platform-specific audio playback
        if sys.platform == "darwin":  # macOS
            os.system(f'afplay "{audio_file_path}"')
            logger.debug("Played audio using afplay (macOS)")

        elif sys.platform == "linux":
            # Try multiple Linux audio players in order of preference
            players = [
                ("paplay", "paplay"),  # PulseAudio
                ("aplay", "aplay"),    # ALSA
                ("ffplay", "ffplay -nodisp -autoexit")  # FFmpeg
            ]

            for player_name, player_cmd in players:
                if os.system(f'which {player_name} > /dev/null 2>&1') == 0:
                    os.system(f'{player_cmd} "{audio_file_path}" > /dev/null 2>&1')
                    logger.debug(f"Played audio using {player_name} (Linux)")
                    break
            else:
                logger.warning("No suitable audio player found on Linux")

        elif sys.platform == "win32":  # Windows
            os.system(f'start "" "{audio_file_path}"')
            logger.debug("Played audio using default player (Windows)")

        else:
            logger.warning(f"Audio playback not supported on platform: {sys.platform}")

    except Exception as e:
        logger.warning(f"Could not play audio: {e}")


def text_to_speech(
    text: str,
    voice: str = "alloy",
    output_file: Optional[str] = None,
    play_audio: bool = True
) -> Optional[str]:
    """
    Convert text to speech using OpenAI TTS API.

    This function provides a simple interface to OpenAI's text-to-speech API
    with automatic file management, cross-platform audio playback, and
    environment-based configuration.

    Args:
        text: Text to convert to speech. Empty or whitespace-only text returns None.
        voice: OpenAI voice model to use. Options: alloy (default), echo, fable,
               onyx, nova, shimmer. Can be overridden by VOICE_MODEL env var.
        output_file: Optional path to save audio file. If None, generates unique
                    filename in VOICE_OUTPUT_DIR with timestamp.
        play_audio: Whether to play the audio immediately after generation.

    Returns:
        Path to saved audio file (str), or None if:
        - VOICE_ENABLED=false in environment
        - Text is empty or whitespace-only
        - API call fails or other error occurs

    Environment Variables:
        VOICE_ENABLED: Enable/disable voice synthesis (default: true)
                      Accepts: true/false, 1/0, yes/no, on/off
        VOICE_MODEL: Default voice model (default: alloy)
        VOICE_OUTPUT_DIR: Directory for audio output (default: ./voice_output)
        OPENAI_API_KEY: OpenAI API key (required for API calls)

    Example:
        >>> # Basic usage with defaults
        >>> path = text_to_speech("Hello, world!")
        >>> print(f"Saved to: {path}")

        >>> # Custom voice and no playback
        >>> path = text_to_speech("Testing", voice="nova", play_audio=False)

        >>> # Custom output location
        >>> path = text_to_speech("Save here", output_file="/tmp/my_audio.mp3")

    Raises:
        No exceptions raised - all errors are caught and logged, returning None.
    """
    # Check if voice is enabled
    voice_enabled = _get_env_bool("VOICE_ENABLED", True)
    if not voice_enabled:
        logger.debug("Voice synthesis disabled by VOICE_ENABLED environment variable")
        return None

    # Validate input text
    if not text or not text.strip():
        logger.warning("Empty or whitespace-only text provided")
        return None

    # Get configuration from environment
    default_voice = os.getenv("VOICE_MODEL", "alloy")
    output_dir = os.getenv("VOICE_OUTPUT_DIR", "./voice_output")

    # Use environment default if voice not explicitly set
    if voice == "alloy":  # Default parameter value
        voice = default_voice

    logger.info(f"Generating speech with voice '{voice}' for {len(text)} characters")

    try:
        # Initialize OpenAI client
        client = OpenAI()

        # Generate unique filename if not specified
        if output_file is None:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            output_file = os.path.join(output_dir, f"tts_{timestamp}.mp3")
            logger.debug(f"Auto-generated output file: {output_file}")
        else:
            # Ensure directory exists for custom output file
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"Using custom output file: {output_file}")

        # Call OpenAI TTS API
        logger.debug(f"Calling OpenAI TTS API with model=tts-1, voice={voice}")
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        # Save audio to file
        with open(output_file, "wb") as f:
            f.write(response.content)

        file_size = os.path.getsize(output_file)
        logger.info(f"Successfully saved audio to {output_file} ({file_size} bytes)")

        # Play audio if requested
        if play_audio:
            logger.debug("Playing audio file")
            _play_audio(output_file)

        return output_file

    except Exception as e:
        logger.error(f"Error generating speech: {e}", exc_info=True)
        return None


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        output_path = text_to_speech(text)
        if output_path:
            print(f"Audio saved to: {output_path}")
        else:
            print("Failed to generate audio")
    else:
        print("Usage: python voice_utils.py <text to speak>")
