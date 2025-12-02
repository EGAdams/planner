"""
TDD Tests for Orchestrator Voice Module - Phase 2 Voice Integration

Test Strategy:
1. Agent deployment announcements
2. TDD phase announcements
3. Test results announcements
4. Validation summary announcements
5. Task completion announcements

Following TDD methodology - tests written BEFORE implementation.
Maximum 5 essential tests for core functionality.
"""

from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import pytest

# Import will succeed if orchestrator_voice exists (GREEN phase goal)
from orchestrator_voice import (
    announce_agent_deployment,
    announce_tdd_phase,
    announce_test_results,
    announce_validation_summary,
    announce_completion
)


class TestOrchestratorVoice:
    """Test suite for orchestrator voice announcement functions."""

    @pytest.fixture
    def mock_text_to_speech(self):
        """Mock voice_utils.text_to_speech function."""
        with patch("orchestrator_voice.text_to_speech") as mock_tts:
            mock_tts.return_value = "/tmp/test_audio.mp3"
            yield mock_tts

    @pytest.fixture
    def mock_voice_disabled(self):
        """Mock voice_utils.text_to_speech returning None (disabled)."""
        with patch("orchestrator_voice.text_to_speech") as mock_tts:
            mock_tts.return_value = None
            yield mock_tts

    def test_announce_agent_deployment(self, mock_text_to_speech):
        """Test agent deployment announcement with voice enabled."""
        agent_name = "feature-implementation"
        task_id = "1.2.3"

        result = announce_agent_deployment(agent_name, task_id)

        # Verify voice synthesis was called with appropriate message
        assert mock_text_to_speech.called
        call_args = mock_text_to_speech.call_args[0][0]
        # Implementation converts hyphens to spaces for natural speech
        assert "feature implementation" in call_args.lower()
        assert "1.2.3" in call_args
        assert "deploy" in call_args.lower() or "agent" in call_args.lower()

        # Verify audio path returned
        assert result == "/tmp/test_audio.mp3"

    def test_announce_tdd_phase(self, mock_text_to_speech):
        """Test TDD phase announcements (RED, GREEN, REFACTOR)."""
        phases = ["RED", "GREEN", "REFACTOR"]
        task_id = "2.1"

        for phase in phases:
            result = announce_tdd_phase(phase, task_id)

            # Verify message contains phase and task ID
            call_args = mock_text_to_speech.call_args[0][0]
            assert phase.lower() in call_args.lower()
            assert "2.1" in call_args

            # Verify audio path returned
            assert result == "/tmp/test_audio.mp3"

    def test_announce_test_results(self, mock_text_to_speech):
        """Test test results announcements with pass/fail counts."""
        test_cases = [
            (18, 0, "2.3"),   # All passing
            (15, 3, "2.4"),   # Some failures
            (0, 5, "2.5"),    # All failing
        ]

        for passed, failed, task_id in test_cases:
            result = announce_test_results(passed, failed, task_id)

            # Verify message contains test counts
            call_args = mock_text_to_speech.call_args[0][0]

            # When all tests pass (failed == 0), message is optimized to "All X tests passing"
            # Otherwise, message includes both passed and failed counts
            if failed == 0 and passed > 0:
                assert str(passed) in call_args
                assert "passing" in call_args.lower()
            elif failed > 0:
                assert str(passed) in call_args
                assert str(failed) in call_args

            assert task_id in call_args
            assert "test" in call_args.lower()

            # Verify audio path returned
            assert result == "/tmp/test_audio.mp3"

    def test_announce_validation_summary(self, mock_text_to_speech):
        """Test validation summary announcements."""
        status = "complete"
        details = {
            "tests_passed": True,
            "implementation_complete": True,
            "documentation_updated": True
        }

        result = announce_validation_summary(status, details)

        # Verify voice synthesis was called with validation info
        assert mock_text_to_speech.called
        call_args = mock_text_to_speech.call_args[0][0]
        assert "complete" in call_args.lower() or "validation" in call_args.lower()

        # Verify audio path returned
        assert result == "/tmp/test_audio.mp3"

    def test_announce_completion(self, mock_text_to_speech):
        """Test task completion announcements."""
        task_id = "3.1"
        deliverables = [
            "test_orchestrator_voice.py",
            "orchestrator_voice.py",
            "ORCHESTRATOR_VOICE_README.md"
        ]

        result = announce_completion(task_id, deliverables)

        # Verify message contains task ID and deliverable info
        assert mock_text_to_speech.called
        call_args = mock_text_to_speech.call_args[0][0]
        assert "3.1" in call_args
        assert "complete" in call_args.lower() or "done" in call_args.lower()

        # Verify audio path returned
        assert result == "/tmp/test_audio.mp3"

    def test_voice_disabled_mode(self, mock_voice_disabled):
        """Test all functions return None when voice is disabled."""
        # Test all announcement functions with voice disabled
        result1 = announce_agent_deployment("test-agent", "1.1")
        result2 = announce_tdd_phase("RED", "1.2")
        result3 = announce_test_results(5, 2, "1.3")
        result4 = announce_validation_summary("complete", {})
        result5 = announce_completion("1.4", ["file.py"])

        # All should return None when voice disabled
        assert result1 is None
        assert result2 is None
        assert result3 is None
        assert result4 is None
        assert result5 is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
