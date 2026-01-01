# Orchestrator Voice - Phase 2 Voice Integration

Voice announcements for task-orchestrator coordination events in the Hybrid Letta Agents system.

## Overview

The orchestrator voice module provides spoken feedback during task orchestration workflows, including:
- Agent deployment notifications
- TDD phase transitions (RED, GREEN, REFACTOR)
- Test execution results
- Validation summaries
- Task completion announcements

Built on top of `voice_utils.py` (Phase 1), this module integrates seamlessly with task orchestration logic.

## Features

- 5 core announcement functions for orchestration events
- Automatic voice synthesis using OpenAI TTS API
- Environment-based voice enable/disable
- Comprehensive logging for debugging
- Error-resistant design (returns None on failures)
- Type-safe with Python type hints

## Installation

No additional dependencies required beyond Phase 1 voice infrastructure:

- `voice_utils.py` - Core voice synthesis (Phase 1)
- `openai` - OpenAI API client

Both files must be in the same directory or Python path.

## Setup

### 1. Get OpenAI API Key

Voice synthesis requires an OpenAI API key:

1. Visit https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### 2. Configure Environment

Copy the example environment file and add your API key:

```bash
cp .env.example .env
# Edit .env and replace 'your_openai_api_key_here' with your actual key
```

Your `.env` file should look like:

```bash
# Required: OpenAI API key for voice synthesis
OPENAI_API_KEY=sk-your-actual-key-here

# Optional: Voice settings
VOICE_ENABLED=true
VOICE_MODEL=alloy
VOICE_OUTPUT_DIR=./voice_output
```

### 3. Test Voice Setup

Test that voice synthesis works:

```bash
python orchestrator_voice.py
```

If configured correctly, you should see audio files generated in `./voice_output/`.

### Troubleshooting Setup

**No API key configured:**
- Error: `OpenAI API key not found`
- Solution: Add `OPENAI_API_KEY` to `.env` file

**Voice not working:**
- Check: `VOICE_ENABLED=true` in `.env`
- Verify: OpenAI API key is valid
- Test: Run `python voice_utils.py "test message"`

**No audio output:**
- Voice synthesis creates audio files but doesn't play them automatically
- Files are saved to `VOICE_OUTPUT_DIR` (default: `./voice_output/`)
- To enable playback, set `play_audio=True` in function calls

## Quick Start

```python
from orchestrator_voice import (
    announce_agent_deployment,
    announce_tdd_phase,
    announce_test_results,
    announce_validation_summary,
    announce_completion
)

# Agent deployment
announce_agent_deployment("feature-implementation", "1.2.3")

# TDD phase transition
announce_tdd_phase("RED", "2.1")

# Test results
announce_test_results(18, 0, "2.3")

# Validation summary
details = {"tests_passed": True, "implementation_complete": True}
announce_validation_summary("complete", details)

# Task completion
deliverables = ["module.py", "test_module.py", "README.md"]
announce_completion("3.1", deliverables)
```

## API Reference

### `announce_agent_deployment(agent_name: str, task_id: str) -> Optional[str]`

Announce agent deployment for a task.

**Parameters:**
- `agent_name` (str): Name of the agent being deployed (e.g., "feature-implementation")
- `task_id` (str): Task identifier (e.g., "1.2.3")

**Returns:**
- `str | None`: Path to generated audio file, or None if voice disabled/error

**Example:**
```python
path = announce_agent_deployment("feature-implementation", "1.2.3")
# Speaks: "Deploying feature implementation agent for task 1.2.3"
```

**Notes:**
- Hyphens and underscores in agent names are replaced with spaces for natural speech
- Logs deployment events to INFO level

---

### `announce_tdd_phase(phase: str, task_id: str) -> Optional[str]`

Announce TDD phase transition (RED, GREEN, or REFACTOR).

**Parameters:**
- `phase` (str): TDD phase name ("RED", "GREEN", or "REFACTOR")
- `task_id` (str): Task identifier (e.g., "2.1")

**Returns:**
- `str | None`: Path to generated audio file, or None if voice disabled/error

**Example:**
```python
# RED phase
path = announce_tdd_phase("RED", "2.1")
# Speaks: "Entering RED phase for task 2.1. Writing failing tests."

# GREEN phase
path = announce_tdd_phase("GREEN", "2.1")
# Speaks: "Entering GREEN phase for task 2.1. Implementing minimal code."

# REFACTOR phase
path = announce_tdd_phase("REFACTOR", "2.1")
# Speaks: "Entering REFACTOR phase for task 2.1. Optimizing and enhancing."
```

**Notes:**
- Phase names are case-insensitive
- Provides phase-specific guidance messages
- Supports custom phase names with generic fallback

---

### `announce_test_results(passed: int, failed: int, task_id: str) -> Optional[str]`

Announce test execution results.

**Parameters:**
- `passed` (int): Number of tests that passed
- `failed` (int): Number of tests that failed
- `task_id` (str): Task identifier (e.g., "2.3")

**Returns:**
- `str | None`: Path to generated audio file, or None if voice disabled/error

**Example:**
```python
# All tests passing
path = announce_test_results(18, 0, "2.3")
# Speaks: "All 18 tests passing for task 2.3. GREEN phase complete."

# Some failures
path = announce_test_results(15, 3, "2.4")
# Speaks: "Test results for task 2.4: 15 passed, 3 failed out of 18 tests."

# No tests
path = announce_test_results(0, 0, "2.5")
# Speaks: "No tests run for task 2.5."
```

**Notes:**
- Provides context-specific messages based on results
- Automatically calculates total test count
- Celebrates all-passing test suites

---

### `announce_validation_summary(status: str, details: dict) -> Optional[str]`

Announce validation summary with status and details.

**Parameters:**
- `status` (str): Validation status (e.g., "complete", "partial", "failed")
- `details` (dict): Dictionary containing validation details (boolean values)

**Returns:**
- `str | None`: Path to generated audio file, or None if voice disabled/error

**Example:**
```python
# Complete validation
details = {
    "tests_passed": True,
    "implementation_complete": True,
    "documentation_updated": True
}
path = announce_validation_summary("complete", details)
# Speaks: "Validation complete: 3 of 3 checks passed"

# Partial validation
details = {
    "tests_passed": True,
    "implementation_complete": True,
    "documentation_updated": False
}
path = announce_validation_summary("partial", details)
# Speaks: "Validation partial: 2 of 3 checks passed"
```

**Notes:**
- Automatically counts True values in details dictionary
- Handles empty details gracefully
- Status can be any descriptive string

---

### `announce_completion(task_id: str, deliverables: list) -> Optional[str]`

Announce task completion with deliverables.

**Parameters:**
- `task_id` (str): Task identifier (e.g., "3.1")
- `deliverables` (list): List of deliverable file names or descriptions

**Returns:**
- `str | None`: Path to generated audio file, or None if voice disabled/error

**Example:**
```python
# With deliverables
deliverables = ["test_module.py", "module.py", "README.md"]
path = announce_completion("3.1", deliverables)
# Speaks: "Task 3.1 complete with 3 deliverables"

# Without deliverables
path = announce_completion("3.2", [])
# Speaks: "Task 3.2 complete"
```

**Notes:**
- Counts deliverables automatically
- Handles empty deliverable lists
- Logs completion events to INFO level

---

## Environment Configuration

The module respects all voice_utils.py environment variables:

```bash
# Enable/disable voice synthesis (default: true)
export VOICE_ENABLED=true

# Default voice model (default: alloy)
export VOICE_MODEL=nova

# Output directory for audio files (default: ./voice_output)
export VOICE_OUTPUT_DIR=/path/to/audio/files

# OpenAI API key (required)
export OPENAI_API_KEY=sk-...
```

## Integration Examples

### Basic TDD Workflow

```python
from orchestrator_voice import (
    announce_agent_deployment,
    announce_tdd_phase,
    announce_test_results,
    announce_completion
)

task_id = "4.2"

# Deploy agent
announce_agent_deployment("feature-implementation", task_id)

# RED phase
announce_tdd_phase("RED", task_id)
announce_test_results(0, 5, task_id)  # Tests fail

# GREEN phase
announce_tdd_phase("GREEN", task_id)
announce_test_results(5, 0, task_id)  # Tests pass

# REFACTOR phase
announce_tdd_phase("REFACTOR", task_id)
announce_test_results(5, 0, task_id)  # Tests still pass

# Complete
deliverables = ["module.py", "test_module.py"]
announce_completion(task_id, deliverables)
```

### Multi-Agent Coordination

```python
agents = [
    ("research-agent", "5.1"),
    ("feature-implementation", "5.2"),
    ("testing-validation", "5.3"),
]

# Deploy all agents
for agent_name, task_id in agents:
    announce_agent_deployment(agent_name, task_id)

# Report completions
for agent_name, task_id in agents:
    announce_completion(task_id, [f"{agent_name}_output.json"])
```

### Conditional Announcements

```python
def run_tests_with_announcements(task_id: str):
    """Run tests and announce only if there are failures."""
    passed, failed = run_test_suite()

    if failed > 0:
        # Alert on failures
        announce_test_results(passed, failed, task_id)
        return False
    else:
        # Silent success
        return True
```

### Task Orchestrator Integration

```python
class TaskOrchestrator:
    """Task orchestrator with voice announcements."""

    def deploy_agent(self, agent_name: str, task_id: str):
        """Deploy agent with announcement."""
        announce_agent_deployment(agent_name, task_id)
        # ... deploy logic ...

    def run_tdd_cycle(self, task_id: str):
        """Run TDD cycle with phase announcements."""
        announce_tdd_phase("RED", task_id)
        # ... write tests ...

        announce_tdd_phase("GREEN", task_id)
        # ... implement code ...

        announce_tdd_phase("REFACTOR", task_id)
        # ... optimize ...

        passed, failed = run_tests()
        announce_test_results(passed, failed, task_id)

    def complete_task(self, task_id: str, deliverables: list):
        """Complete task with announcement."""
        announce_completion(task_id, deliverables)
        # ... finalization logic ...
```

## Testing

Run the test suite (requires pytest):

```bash
cd agents
python -m pytest test_orchestrator_voice.py -v
```

Expected output:
```
test_orchestrator_voice.py::TestOrchestratorVoice::test_announce_agent_deployment PASSED
test_orchestrator_voice.py::TestOrchestratorVoice::test_announce_tdd_phase PASSED
test_orchestrator_voice.py::TestOrchestratorVoice::test_announce_test_results PASSED
test_orchestrator_voice.py::TestOrchestratorVoice::test_announce_validation_summary PASSED
test_orchestrator_voice.py::TestOrchestratorVoice::test_announce_completion PASSED
test_orchestrator_voice.py::TestOrchestratorVoice::test_voice_disabled_mode PASSED

6 tests passed
```

## Example Usage

Run the comprehensive example script:

```bash
# With voice enabled (generates audio)
python orchestrator_voice_example.py

# With voice disabled (no audio)
VOICE_ENABLED=false python orchestrator_voice_example.py
```

The example script demonstrates:
- Basic announcements for all functions
- Complete TDD workflow simulation
- Multi-agent coordination patterns
- Test failure recovery scenarios
- Conditional announcement logic
- Voice disabled mode

## Logging

The module provides comprehensive logging at multiple levels:

- **INFO**: Successful announcements, function calls
- **WARNING**: Empty parameters, edge cases
- **ERROR**: API failures, unexpected errors

Configure logging level:

```python
import logging
logging.getLogger("orchestrator_voice").setLevel(logging.DEBUG)
```

## Error Handling

The module handles all errors gracefully:

- Returns `None` on any error (API failures, voice disabled, etc.)
- Logs detailed error information for debugging
- Never raises exceptions to calling code
- Validates input parameters

Example:

```python
result = announce_agent_deployment("test-agent", "1.1")
if result is None:
    print("Announcement failed or voice disabled")
else:
    print(f"Announcement successful: {result}")
```

## Audio File Management

Audio files are managed by voice_utils.py:

- Saved to `VOICE_OUTPUT_DIR` (default: `./voice_output`)
- Named with timestamps: `tts_20251201_132851_836770.mp3`
- Not played automatically (controlled by voice_utils)

To enable audio playback during announcements, modify the voice_utils.text_to_speech calls in orchestrator_voice.py to set `play_audio=True`.

## Performance Considerations

- Each announcement makes one OpenAI TTS API call (~1-2 seconds)
- Audio files are typically 50-200 KB
- Consider async/threading for multiple simultaneous announcements
- Voice disabled mode has near-zero overhead

## Comparison with Phase 1

| Feature | Phase 1 (voice_utils) | Phase 2 (orchestrator_voice) |
|---------|---------------------|----------------------------|
| Purpose | Core TTS infrastructure | Orchestration announcements |
| Functions | 1 (text_to_speech) | 5 (specialized announcements) |
| Complexity | Low-level API wrapper | High-level orchestration logic |
| Testing | 18 comprehensive tests | 6 essential tests |
| Messages | User-provided text | Auto-generated from context |
| Use Cases | General voice synthesis | Task coordination workflow |

## TDD Development Process

This module was developed using strict Test-Driven Development:

1. **RED Phase**: Wrote 6 failing tests covering all functions
2. **GREEN Phase**: Implemented minimal code to pass all tests
3. **REFACTOR Phase**: Enhanced with logging, documentation, examples

See `tdd_contracts.jsonl` for complete TDD audit trail.

## Dependencies

- `voice_utils.py` - Phase 1 voice infrastructure (required)
- `openai` - OpenAI API client (required)
- `pytest` - Testing framework (development only)

## Troubleshooting

### Announcements return None

Check if voice is enabled:

```bash
export VOICE_ENABLED=true
```

Verify OpenAI API key:

```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Import errors

Ensure voice_utils.py is in the same directory or Python path:

```bash
cd agents
python orchestrator_voice.py
```

### No audio output

The module saves audio files but doesn't play them by default. To enable playback, modify the function calls to set `play_audio=True` in voice_utils.text_to_speech.

### Tests not running

Run from the agents directory with pytest:

```bash
cd agents
python -m pytest test_orchestrator_voice.py -v
```

## Future Enhancements

Potential Phase 3 enhancements:
- Custom voice models per announcement type
- Audio playback control from orchestrator_voice
- Announcement queuing for batch processing
- Progress percentage announcements
- Error recovery announcements
- Multi-language support

## License

Part of the Hybrid Letta Agents project.

## Contributing

When modifying this module:

1. Write tests first (TDD)
2. Run full test suite
3. Update this README if behavior changes
4. Log changes in `tdd_contracts.jsonl`

## Support

For issues or questions, refer to the main project documentation or `voice_utils.py` documentation.

---

**Phase 2 Complete**: Orchestrator voice announcements fully integrated with task coordination workflows.
