# Test Setup and Execution Guide

## Summary of Fixed Issues

### What Was Broken
1. **Missing pytest dependency**: The test file `test_orchestrator_voice.py` required pytest but it was not installed
2. **No requirements.txt file**: The project had no Python dependency management file
3. **Externally-managed Python environment**: The system Python is protected and requires a virtual environment
4. **Missing OpenAI and Letta client libraries**: Dependencies for voice_utils.py and hybrid_letta__codex_sdk.py were not installed

### What Was Fixed
1. Created `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/requirements.txt` with:
   - pytest>=8.0.0 (for testing framework)
   - openai>=1.0.0 (for TTS API in voice_utils.py)
   - letta-client>=0.5.0 (for Letta orchestration)

2. Created Python virtual environment at `venv/`

3. Installed all dependencies in the virtual environment

4. Verified tests can now execute properly

## Test Execution Results

### Current Status: 4 PASSED, 2 FAILED (out of 6 tests)

The test infrastructure is working correctly. The 2 failures are **test assertion issues**, not dependency or infrastructure problems:

#### Failed Tests (Implementation vs Test Expectation Mismatch)
1. **test_announce_agent_deployment**: Test expects "feature-implementation" in message, but implementation converts hyphens to spaces ("feature implementation")
2. **test_announce_test_results**: Test expects failed count "0" in message, but implementation uses optimized message "All 18 tests passing" when no failures

#### Passing Tests (4/6)
- test_announce_tdd_phase ✓
- test_announce_validation_summary ✓
- test_announce_completion ✓
- test_voice_disabled_mode ✓

## How to Run Tests Going Forward

### Option 1: Using Virtual Environment Python Directly
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./venv/bin/python agents/test_orchestrator_voice.py
```

### Option 2: Using pytest with Virtual Environment
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./venv/bin/pytest agents/test_orchestrator_voice.py -v
```

### Option 3: Activate Virtual Environment First
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
source venv/bin/activate
pytest agents/test_orchestrator_voice.py -v
deactivate  # When done
```

### Run All Tests in Directory
```bash
./venv/bin/pytest agents/ -v
```

### Run Specific Test
```bash
./venv/bin/pytest agents/test_orchestrator_voice.py::TestOrchestratorVoice::test_announce_tdd_phase -v
```

## Installing Additional Dependencies

If you need to add more Python packages:

```bash
# Add to requirements.txt first
echo "new-package>=1.0.0" >> requirements.txt

# Install using virtual environment pip
./venv/bin/pip install -r requirements.txt
```

## Project Structure

```
hybrid_letta_agents/
├── requirements.txt           # Python dependencies (CREATED)
├── venv/                      # Virtual environment (CREATED)
├── agents/
│   ├── test_orchestrator_voice.py    # Test file (NOW RUNNABLE)
│   ├── orchestrator_voice.py         # Implementation
│   ├── voice_utils.py               # Voice utilities
│   ├── add.py                       # Simple add function
│   └── hybrid_letta__codex_sdk.py   # Letta integration
└── TEST_SETUP_README.md       # This file (CREATED)
```

## Dependencies Installed

### Testing Framework
- **pytest 9.0.1**: Full-featured Python testing framework
- **pluggy 1.6.0**: Plugin system for pytest
- **iniconfig 2.3.0**: Configuration parsing
- **packaging 25.0**: Version handling
- **pygments 2.19.2**: Syntax highlighting

### Voice Utilities (OpenAI TTS)
- **openai 2.8.1**: OpenAI API client for text-to-speech
- **httpx 0.28.1**: HTTP client
- **pydantic 2.12.5**: Data validation
- **jiter 0.12.0**: JSON parsing
- **anyio 4.12.0**: Async I/O
- **tqdm 4.67.1**: Progress bars

### Letta Orchestration
- **letta-client 1.3.2**: Letta orchestration framework

## TDD Methodology Notes

The test file follows TDD best practices:
- Tests written BEFORE implementation (RED phase)
- Implementation created to pass tests (GREEN phase)
- Code refactored while keeping tests green (REFACTOR phase)
- Maximum 5 essential tests for core functionality

## Next Steps

To fix the 2 failing tests, you have two options:

### Option A: Fix Test Assertions (Recommended)
Update test expectations to match implementation behavior:
- Accept "feature implementation" instead of "feature-implementation"
- Accept optimized success messages that don't include "0 failed"

### Option B: Modify Implementation
Change implementation to match test expectations:
- Keep hyphens in agent names
- Always include pass/fail counts in messages

## Environment Variables (Optional)

The voice utilities support these environment variables:
- `VOICE_ENABLED`: Enable/disable voice synthesis (default: true)
- `VOICE_MODEL`: Default voice model (default: alloy)
- `VOICE_OUTPUT_DIR`: Directory for audio output (default: ./voice_output)
- `OPENAI_API_KEY`: OpenAI API key for TTS calls

Example:
```bash
export VOICE_ENABLED=false
./venv/bin/pytest agents/test_orchestrator_voice.py -v
```

## Troubleshooting

### If tests fail to import modules
```bash
# Ensure virtual environment is activated or use full path
./venv/bin/python -c "import pytest; import openai; print('OK')"
```

### If you get "externally-managed-environment" error
Always use the virtual environment Python:
- ✓ `./venv/bin/python`
- ✓ `./venv/bin/pytest`
- ✗ `python3` or `pip3` (system Python)

### Recreate Virtual Environment
```bash
rm -rf venv
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

---

**Test infrastructure is now fully operational!** ✓
