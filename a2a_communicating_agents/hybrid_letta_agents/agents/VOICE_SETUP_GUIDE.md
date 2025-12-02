# Voice Setup Guide - Getting Voice Synthesis Working

This guide explains how to configure voice synthesis for the Hybrid Letta Agents system and troubleshoots common setup issues.

## Current Status

Voice synthesis is currently **NOT configured** because:

1. **Missing `.env` file** - Configuration file doesn't exist
2. **Missing OpenAI API key** - Required for TTS API calls
3. **Tests pass but voice is silent** - Implementation works, just needs API key

## Why Voice Isn't Working

The voice modules (`voice_utils.py` and `orchestrator_voice.py`) are fully implemented and tested, but they require an OpenAI API key to make text-to-speech API calls.

**Without an API key:**
- Voice functions return `None` instead of audio file paths
- No error messages (graceful degradation)
- Tests pass (using mocks)
- Implementation is correct but inactive

**With an API key:**
- Voice functions generate MP3 audio files
- Audio files saved to `./voice_output/`
- Optional audio playback
- Full voice announcements during task orchestration

## Setup Instructions

### Step 1: Get OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Sign in to your OpenAI account (or create one)
3. Click **"Create new secret key"**
4. Give it a name like "hybrid-letta-agents-voice"
5. Copy the key - it starts with `sk-` and looks like:
   ```
   sk-proj-abcdef123456...
   ```
6. **Important**: Save this key somewhere safe - you can't view it again!

### Step 2: Create `.env` File

In the `agents/` directory, create a `.env` file:

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/agents
cp .env.example .env
```

### Step 3: Configure API Key

Edit `.env` and add your OpenAI API key:

```bash
# Required: OpenAI API key for voice synthesis
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Optional: Voice settings (these are the defaults)
VOICE_ENABLED=true
VOICE_MODEL=alloy
VOICE_OUTPUT_DIR=./voice_output
```

Replace `sk-proj-your-actual-key-here` with your actual API key from Step 1.

### Step 4: Test Voice Setup

Test that voice synthesis works:

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/agents
source ../venv/bin/activate
python voice_utils.py "Hello, this is a test!"
```

**Expected output:**
```
2025-12-01 14:30:45 - voice_utils - INFO - Generating speech with voice 'alloy' for 22 characters
2025-12-01 14:30:46 - voice_utils - INFO - Successfully saved audio to ./voice_output/tts_20251201_143046_123456.mp3 (45678 bytes)
Audio saved to: ./voice_output/tts_20251201_143046_123456.mp3
```

**If successful:**
- Audio file created in `./voice_output/`
- File is a valid MP3 (you can play it manually)
- Voice synthesis is now working!

### Step 5: Test Orchestrator Voice

Test the orchestrator voice announcements:

```bash
python orchestrator_voice.py
```

You should see announcements for:
1. Agent deployment
2. TDD phases
3. Test results
4. Validation summary
5. Task completion

All audio files will be in `./voice_output/`.

## Configuration Options

### Voice Models

Choose from 6 OpenAI voice models by setting `VOICE_MODEL`:

```bash
VOICE_MODEL=alloy    # Balanced and versatile (default)
VOICE_MODEL=echo     # Warm and engaging
VOICE_MODEL=fable    # Expressive and dynamic
VOICE_MODEL=onyx     # Deep and authoritative
VOICE_MODEL=nova     # Energetic and friendly
VOICE_MODEL=shimmer  # Soft and gentle
```

### Output Directory

Change where audio files are saved:

```bash
VOICE_OUTPUT_DIR=/path/to/audio/files
```

Default is `./voice_output` in the current directory.

### Enable/Disable Voice

Temporarily disable voice without removing API key:

```bash
VOICE_ENABLED=false
```

This makes all voice functions return `None` immediately without API calls.

## Troubleshooting

### "OpenAI API key not found" error

**Problem:** Missing or invalid API key

**Solutions:**
1. Check `.env` file exists in `agents/` directory
2. Verify `OPENAI_API_KEY` is set in `.env`
3. Ensure key starts with `sk-`
4. Try exporting directly:
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   python voice_utils.py "test"
   ```

### Voice functions return None

**Problem:** Voice synthesis is disabled or failing

**Check:**
1. `VOICE_ENABLED=true` in `.env` (or not set - defaults to true)
2. OpenAI API key is valid and has credits
3. Check logs for error messages:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Tests pass but no voice

**Problem:** Tests use mocks, not real API calls

**Solution:** This is expected behavior! Tests pass without API key because they mock the TTS calls. To get actual voice:
1. Configure API key (see Step 1-3 above)
2. Run the actual modules, not tests:
   ```bash
   python voice_utils.py "test message"
   python orchestrator_voice.py
   ```

### No audio playback

**Problem:** Audio files created but not playing automatically

**Check:**
1. Audio files exist in `VOICE_OUTPUT_DIR`
2. Files are valid MP3s (try playing manually)
3. Platform audio player is available:
   - **macOS**: `afplay` (built-in)
   - **Linux**: Install `paplay`, `aplay`, or `ffplay`
   - **Windows**: Default media player

**Note:** The modules create audio files but playback depends on platform. Files are always saved even if playback fails.

### API rate limits or costs

**Problem:** Concerned about API usage

**Info:**
- OpenAI TTS pricing: ~$0.015 per 1000 characters
- Example: 100-character announcement = $0.0015 (~0.15 cents)
- Rate limits: Tier 1 = 500 requests/day
- To disable: Set `VOICE_ENABLED=false` in `.env`

## Testing with Voice Enabled

Run tests with voice synthesis:

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/agents
source ../venv/bin/activate

# Tests still use mocks (fast, no API calls)
python -m pytest test_orchestrator_voice.py -v

# Run actual implementation (makes real API calls)
python orchestrator_voice.py
python orchestrator_voice_example.py
```

## Integration with Task Orchestrator

Once voice is configured, orchestrator announcements will automatically speak:

```python
from orchestrator_voice import announce_agent_deployment

# This will generate and play voice announcement
announce_agent_deployment("feature-implementation", "1.2.3")
# Speaks: "Deploying feature implementation agent for task 1.2.3"
```

No code changes needed - just configure the API key!

## Security Notes

1. **Never commit `.env` file** - It's in `.gitignore`
2. **Keep API key secret** - Don't share in code or logs
3. **Use separate keys** - Different keys for dev/prod
4. **Rotate keys regularly** - Revoke and create new keys periodically
5. **Monitor usage** - Check OpenAI dashboard for unexpected usage

## Cost Estimation

Typical task orchestration session:
- Agent deployment: ~50 chars = $0.00075
- TDD phase: ~60 chars = $0.0009
- Test results: ~70 chars = $0.00105
- Completion: ~50 chars = $0.00075

Total per task: ~$0.003 (0.3 cents)

For 100 tasks/day: ~$0.30/day (~$9/month)

## Alternative: Disable Voice

If you don't want voice synthesis, you can disable it:

```bash
# In .env
VOICE_ENABLED=false
```

Or simply don't configure the API key - all voice functions will gracefully return `None`.

## Summary

**Why voice isn't working now:**
- Missing OpenAI API key

**How to fix:**
1. Get API key from https://platform.openai.com/api-keys
2. Create `.env` file from `.env.example`
3. Add API key to `.env`
4. Test with `python voice_utils.py "test"`

**Once configured:**
- Voice announcements will work automatically
- Audio files saved to `./voice_output/`
- Optional playback during announcements
- No code changes needed

## Support

For issues:
1. Check logs with `logging.basicConfig(level=logging.DEBUG)`
2. Test with simple text: `python voice_utils.py "test"`
3. Verify API key at https://platform.openai.com/api-keys
4. Check OpenAI API status: https://status.openai.com/

For questions about the voice implementation itself, see:
- `VOICE_UTILS_README.md` - Core TTS infrastructure
- `ORCHESTRATOR_VOICE_README.md` - Orchestration announcements
- `voice_utils.py` - Implementation with detailed docstrings
