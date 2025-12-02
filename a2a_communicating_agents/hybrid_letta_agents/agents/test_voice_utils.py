"""
TDD Tests for Voice Utilities Module - Text-to-Speech Infrastructure

Test Strategy:
1. Basic text-to-speech conversion
2. Voice model selection
3. File output handling
4. Environment variable configuration
5. Error handling for API failures
6. Audio playback functionality (mocked for testing)
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import will fail initially (RED phase)
from voice_utils import text_to_speech


class TestTextToSpeech:
    """Test suite for text_to_speech function."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for audio output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        with patch("voice_utils.OpenAI") as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.content = b"fake_audio_data"
            mock_client.return_value.audio.speech.create.return_value = mock_response
            yield mock_client

    @pytest.fixture
    def mock_audio_playback(self):
        """Mock audio playback functionality."""
        with patch("voice_utils._play_audio") as mock_play:
            yield mock_play

    def test_basic_text_to_speech_conversion(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test basic text-to-speech conversion with default settings."""
        text = "Hello, this is a test."

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            result_path = text_to_speech(text, play_audio=False)

        # Verify file was created
        assert os.path.exists(result_path)
        assert result_path.startswith(temp_output_dir)

        # Verify OpenAI API was called correctly
        mock_openai_client.return_value.audio.speech.create.assert_called_once()
        call_kwargs = mock_openai_client.return_value.audio.speech.create.call_args[1]
        assert call_kwargs["input"] == text
        assert call_kwargs["model"] == "tts-1"
        assert call_kwargs["voice"] == "alloy"

    @pytest.mark.parametrize(
        "voice_name",
        ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    )
    def test_voice_model_selection(
        self, voice_name, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test different voice model selections."""
        text = "Testing voice selection."

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            result_path = text_to_speech(text, voice=voice_name, play_audio=False)

        # Verify correct voice was used
        call_kwargs = mock_openai_client.return_value.audio.speech.create.call_args[1]
        assert call_kwargs["voice"] == voice_name
        assert os.path.exists(result_path)

    def test_custom_output_file_path(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test specifying a custom output file path."""
        text = "Custom output path test."
        custom_path = os.path.join(temp_output_dir, "custom_audio.mp3")

        with patch.dict(os.environ, {"VOICE_ENABLED": "true"}):
            result_path = text_to_speech(text, output_file=custom_path, play_audio=False)

        assert result_path == custom_path
        assert os.path.exists(result_path)

    def test_environment_variable_voice_enabled(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test VOICE_ENABLED environment variable."""
        text = "Environment variable test."

        # Test with VOICE_ENABLED=false
        with patch.dict(os.environ, {"VOICE_ENABLED": "false", "VOICE_OUTPUT_DIR": temp_output_dir}):
            result_path = text_to_speech(text, play_audio=False)

        # Should return None or empty string when disabled
        assert result_path is None or result_path == ""
        mock_openai_client.return_value.audio.speech.create.assert_not_called()

    def test_environment_variable_default_voice(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test VOICE_MODEL environment variable for default voice."""
        text = "Default voice from env test."

        with patch.dict(
            os.environ,
            {"VOICE_MODEL": "nova", "VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}
        ):
            result_path = text_to_speech(text, play_audio=False)

        # Should use environment variable voice as default
        call_kwargs = mock_openai_client.return_value.audio.speech.create.call_args[1]
        assert call_kwargs["voice"] == "nova"

    def test_environment_variable_output_directory(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test VOICE_OUTPUT_DIR environment variable."""
        text = "Output directory env test."

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            result_path = text_to_speech(text, play_audio=False)

        assert result_path.startswith(temp_output_dir)

    def test_audio_playback_enabled(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test audio playback when play_audio=True."""
        text = "Playback test."

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            result_path = text_to_speech(text, play_audio=True)

        # Verify playback was called
        mock_audio_playback.assert_called_once_with(result_path)

    def test_audio_playback_disabled(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test audio playback when play_audio=False."""
        text = "No playback test."

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            result_path = text_to_speech(text, play_audio=False)

        # Verify playback was NOT called
        mock_audio_playback.assert_not_called()

    def test_api_error_handling(
        self, temp_output_dir, mock_audio_playback
    ):
        """Test graceful handling of API errors."""
        text = "Error handling test."

        with patch("voice_utils.OpenAI") as mock_client:
            mock_client.return_value.audio.speech.create.side_effect = Exception("API Error")

            with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
                # Should return None on error, not raise
                result_path = text_to_speech(text, play_audio=False)

            assert result_path is None

    def test_unique_filename_generation(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test that unique filenames are generated for each call."""
        text = "Unique filename test."

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            path1 = text_to_speech(text, play_audio=False)
            path2 = text_to_speech(text, play_audio=False)

        # Filenames should be different
        assert path1 != path2
        assert os.path.exists(path1)
        assert os.path.exists(path2)

    def test_output_directory_creation(
        self, mock_openai_client, mock_audio_playback
    ):
        """Test that output directory is created if it doesn't exist."""
        text = "Directory creation test."
        nonexistent_dir = "/tmp/nonexistent_voice_dir_12345"

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": nonexistent_dir, "VOICE_ENABLED": "true"}):
            with patch("os.makedirs") as mock_makedirs:
                result_path = text_to_speech(text, play_audio=False)

            # Verify makedirs was called
            mock_makedirs.assert_called()

    def test_empty_text_handling(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test handling of empty text input."""
        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            result_path = text_to_speech("", play_audio=False)

        # Should return None for empty text
        assert result_path is None

    def test_audio_file_contains_data(
        self, temp_output_dir, mock_openai_client, mock_audio_playback
    ):
        """Test that saved audio file contains data."""
        text = "File content test."

        with patch.dict(os.environ, {"VOICE_OUTPUT_DIR": temp_output_dir, "VOICE_ENABLED": "true"}):
            result_path = text_to_speech(text, play_audio=False)

        # Verify file has content
        assert os.path.getsize(result_path) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
