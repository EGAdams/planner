"""
Orchestrator Voice Module - Phase 2 Voice Integration

Provides voice announcements for task-orchestrator coordination events
including agent deployment, TDD phases, test results, validation, and completion.

This module integrates with voice_utils.py to provide spoken feedback
during task orchestration workflows.

Example:
    >>> from orchestrator_voice import announce_agent_deployment
    >>> audio_path = announce_agent_deployment("feature-implementation", "1.2.3")
    >>> if audio_path:
    ...     print(f"Announcement saved to: {audio_path}")
"""

from __future__ import annotations

import logging
from typing import Optional

from voice_utils import text_to_speech


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def announce_agent_deployment(agent_name: str, task_id: str) -> Optional[str]:
    """
    Announce agent deployment for a task.

    Args:
        agent_name: Name of the agent being deployed (e.g., "feature-implementation")
        task_id: Task identifier (e.g., "1.2.3")

    Returns:
        Path to generated audio file, or None if voice disabled/error

    Example:
        >>> path = announce_agent_deployment("feature-implementation", "1.2.3")
        >>> print(f"Deployed agent announced: {path}")
    """
    if not agent_name or not task_id:
        logger.warning("Empty agent_name or task_id provided")
        return None

    # Format agent name for speech (replace hyphens/underscores with spaces)
    formatted_agent = agent_name.replace("-", " ").replace("_", " ")

    message = f"Deploying {formatted_agent} agent for task {task_id}"
    logger.info(f"Agent deployment: {message}")

    return text_to_speech(message, play_audio=True)


def announce_tdd_phase(phase: str, task_id: str) -> Optional[str]:
    """
    Announce TDD phase transition (RED, GREEN, or REFACTOR).

    Args:
        phase: TDD phase name ("RED", "GREEN", or "REFACTOR")
        task_id: Task identifier (e.g., "2.1")

    Returns:
        Path to generated audio file, or None if voice disabled/error

    Example:
        >>> path = announce_tdd_phase("RED", "2.1")
        >>> print(f"TDD phase announced: {path}")
    """
    if not phase or not task_id:
        logger.warning("Empty phase or task_id provided")
        return None

    phase_upper = phase.upper()

    # Create phase-specific messages
    phase_messages = {
        "RED": f"Entering RED phase for task {task_id}. Writing failing tests.",
        "GREEN": f"Entering GREEN phase for task {task_id}. Implementing minimal code.",
        "REFACTOR": f"Entering REFACTOR phase for task {task_id}. Optimizing and enhancing."
    }

    message = phase_messages.get(
        phase_upper,
        f"TDD phase {phase} for task {task_id}"
    )

    logger.info(f"TDD phase transition: {message}")

    return text_to_speech(message, play_audio=False)


def announce_test_results(passed: int, failed: int, task_id: str) -> Optional[str]:
    """
    Announce test execution results.

    Args:
        passed: Number of tests that passed
        failed: Number of tests that failed
        task_id: Task identifier (e.g., "2.3")

    Returns:
        Path to generated audio file, or None if voice disabled/error

    Example:
        >>> path = announce_test_results(18, 0, "2.3")
        >>> print(f"Test results announced: {path}")
    """
    if task_id is None:
        logger.warning("task_id is None")
        return None

    total = passed + failed

    # Create results-specific message
    if failed == 0 and passed > 0:
        message = f"All {passed} tests passing for task {task_id}. GREEN phase complete."
    elif failed > 0:
        message = f"Test results for task {task_id}: {passed} passed, {failed} failed out of {total} tests."
    else:
        message = f"No tests run for task {task_id}."

    logger.info(f"Test results: {message}")

    return text_to_speech(message, play_audio=False)


def announce_validation_summary(status: str, details: dict) -> Optional[str]:
    """
    Announce validation summary with status and details.

    Args:
        status: Validation status (e.g., "complete", "partial", "failed")
        details: Dictionary containing validation details

    Returns:
        Path to generated audio file, or None if voice disabled/error

    Example:
        >>> details = {"tests_passed": True, "implementation_complete": True}
        >>> path = announce_validation_summary("complete", details)
        >>> print(f"Validation announced: {path}")
    """
    if not status:
        logger.warning("Empty status provided")
        return None

    # Count validation items
    if details:
        passed_items = sum(1 for v in details.values() if v is True)
        total_items = len(details)
        detail_summary = f"{passed_items} of {total_items} checks passed"
    else:
        detail_summary = "no details provided"

    message = f"Validation {status}: {detail_summary}"
    logger.info(f"Validation summary: {message}")

    return text_to_speech(message, play_audio=False)


def announce_completion(task_id: str, deliverables: list) -> Optional[str]:
    """
    Announce task completion with deliverables.

    Args:
        task_id: Task identifier (e.g., "3.1")
        deliverables: List of deliverable file names or descriptions

    Returns:
        Path to generated audio file, or None if voice disabled/error

    Example:
        >>> deliverables = ["test_module.py", "module.py", "README.md"]
        >>> path = announce_completion("3.1", deliverables)
        >>> print(f"Completion announced: {path}")
    """
    if not task_id:
        logger.warning("Empty task_id provided")
        return None

    deliverable_count = len(deliverables) if deliverables else 0

    if deliverable_count > 0:
        message = f"Task {task_id} complete with {deliverable_count} deliverables"
    else:
        message = f"Task {task_id} complete"

    logger.info(f"Task completion: {message}")

    return text_to_speech(message, play_audio=False)


# Example usage
if __name__ == "__main__":
    import sys

    print("Orchestrator Voice Module - Example Usage\n")

    # Test all announcement functions
    print("1. Agent Deployment:")
    path = announce_agent_deployment("feature-implementation", "1.2.3")
    print(f"   Audio path: {path}\n")

    print("2. TDD Phase (RED):")
    path = announce_tdd_phase("RED", "2.1")
    print(f"   Audio path: {path}\n")

    print("3. Test Results:")
    path = announce_test_results(18, 0, "2.3")
    print(f"   Audio path: {path}\n")

    print("4. Validation Summary:")
    details = {"tests_passed": True, "implementation_complete": True}
    path = announce_validation_summary("complete", details)
    print(f"   Audio path: {path}\n")

    print("5. Task Completion:")
    deliverables = ["test_orchestrator_voice.py", "orchestrator_voice.py", "README.md"]
    path = announce_completion("3.1", deliverables)
    print(f"   Audio path: {path}\n")
