# Voice Utils - Text-to-Speech Infrastructure

Production-ready text-to-speech utilities using OpenAI TTS API with comprehensive testing, logging, and cross-platform audio playback.

## Features

- OpenAI TTS API integration with all 6 voice models
- Environment-based configuration for easy deployment
- Cross-platform audio playback (macOS, Linux, Windows)
- Automatic file management with unique timestamped filenames
- Comprehensive error handling and logging
- Full test coverage with pytest
- Type-safe with Python type hints

## Installation

The required dependencies are already installed in the project environment:

- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management (optional)

No additional audio libraries required - uses native OS audio players.

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

Your `.env` file should contain at minimum:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

Optional settings:

```bash
VOICE_ENABLED=true
VOICE_MODEL=alloy
VOICE_OUTPUT_DIR=./voice_output
```

### 3. Test Voice Setup

Test that voice synthesis works:

```bash
python voice_utils.py "Hello, this is a test!"
```

If configured correctly, you should see:
- Audio file created in `./voice_output/`
- Audio automatically plays (if supported on your platform)
- Output message: `Audio saved to: ./voice_output/tts_TIMESTAMP.mp3`

### Troubleshooting Setup

**Error: "OpenAI API key not found"**
- Add `OPENAI_API_KEY` to `.env` file or export as environment variable
- Verify the key starts with `sk-`
- Check the `.env` file is in the same directory as `voice_utils.py`

**Voice synthesis disabled:**
- Check `VOICE_ENABLED=true` in environment
- Default is `true`, only set to `false` to disable

**No audio playback:**
- Audio files are still created in `VOICE_OUTPUT_DIR`
- Check your platform's audio player is installed:
  - macOS: `afplay` (built-in)
  - Linux: `paplay`, `aplay`, or `ffplay`
  - Windows: Default media player
- Try playing the file manually from `./voice_output/`

## Quick Start

```python
from voice_utils import text_to_speech

# Basic usage - generates audio and plays it
audio_path = text_to_speech("Hello, this is a test!")
print(f"Audio saved to: {audio_path}")

# Custom voice model
audio_path = text_to_speech("Testing different voice", voice="nova")

# Save without playing
audio_path = text_to_speech("Silent generation", play_audio=False)

# Custom output location
audio_path = text_to_speech(
    "Custom location test",
    output_file="/tmp/my_audio.mp3"
)
```

## Environment Configuration

Configure behavior via environment variables:

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

## Voice Models

OpenAI provides 6 voice models, each with different characteristics:

- `alloy` - Balanced and versatile (default)
- `echo` - Warm and engaging
- `fable` - Expressive and dynamic
- `onyx` - Deep and authoritative
- `nova` - Energetic and friendly
- `shimmer` - Soft and gentle

## API Reference

### `text_to_speech(text, voice="alloy", output_file=None, play_audio=True)`

Convert text to speech using OpenAI TTS API.

**Parameters:**

- `text` (str): Text to convert to speech. Returns None if empty/whitespace.
- `voice` (str): Voice model to use. Default: "alloy" (or VOICE_MODEL env var)
- `output_file` (str | None): Optional custom output path. Default: auto-generated
- `play_audio` (bool): Whether to play audio immediately. Default: True

**Returns:**

- `str | None`: Path to saved audio file, or None if disabled/error

**Environment Variables:**

- `VOICE_ENABLED`: Enable/disable synthesis (true/false, 1/0, yes/no, on/off)
- `VOICE_MODEL`: Default voice model
- `VOICE_OUTPUT_DIR`: Output directory
- `OPENAI_API_KEY`: API key (required)

**Example:**

```python
# All parameters
path = text_to_speech(
    text="Hello world",
    voice="echo",
    output_file="/tmp/greeting.mp3",
    play_audio=False
)
```

## Audio Playback

The module automatically detects the platform and uses appropriate audio players:

- **macOS**: `afplay` (built-in)
- **Linux**: Tries `paplay` (PulseAudio) → `aplay` (ALSA) → `ffplay` (FFmpeg)
- **Windows**: Default system player via `start` command

No external Python audio libraries required!

## Testing

Comprehensive test suite with 18 tests covering:

- Basic functionality
- All 6 voice models
- Environment variable configuration
- File output handling
- Audio playback (mocked)
- Error handling
- Unique filename generation

Run tests:

```bash
cd agents
python -m pytest test_voice_utils.py -v
```

Expected output:
```
18 passed, 1 warning in 0.64s
```

## Command-Line Usage

Run directly as a script:

```bash
python voice_utils.py "Text to speak"
```

This will generate audio with default settings and print the output path.

## Error Handling

The module gracefully handles all errors:

- Returns `None` on any error (API failures, file I/O, etc.)
- Logs detailed error information for debugging
- Never raises exceptions to calling code

Example:

```python
result = text_to_speech("Test")
if result is None:
    print("Voice synthesis failed or disabled")
else:
    print(f"Success: {result}")
```

## Logging

Built-in logging at multiple levels:

- `INFO`: Successful operations, API calls
- `DEBUG`: Detailed execution flow
- `WARNING`: Non-critical issues (playback failures, missing players)
- `ERROR`: API errors, file I/O errors

Configure logging level:

```python
import logging
logging.getLogger("voice_utils").setLevel(logging.DEBUG)
```

## File Management

### Auto-generated Filenames

When `output_file=None`, files are named with timestamps:

```
voice_output/tts_20251201_132851_836770.mp3
```

Format: `tts_YYYYMMDD_HHMMSS_microseconds.mp3`

### Directory Creation

Output directories are created automatically if they don't exist.

### File Cleanup

The module doesn't automatically delete old audio files. Implement cleanup as needed:

```python
import os
import glob
import time

# Delete files older than 24 hours
output_dir = "./voice_output"
for file in glob.glob(f"{output_dir}/tts_*.mp3"):
    if os.path.getmtime(file) < time.time() - 86400:
        os.remove(file)
```

## WSL2 Compatibility

The module works in WSL2 environments:

- File I/O works natively
- Audio playback requires Linux audio server (PulseAudio/ALSA)
- Consider setting `play_audio=False` in headless environments

## TDD Development Process

This module was developed using strict Test-Driven Development:

1. **RED Phase**: Wrote 18 failing tests first
2. **GREEN Phase**: Implemented minimal code to pass all tests
3. **REFACTOR Phase**: Enhanced with logging, documentation, type hints

See `tdd_contracts.jsonl` for complete TDD audit trail.

## Integration Examples

### With Hybrid Letta Agents

```python
from voice_utils import text_to_speech

def agent_speak(message: str) -> None:
    """Make agent speak a message."""
    audio_path = text_to_speech(
        message,
        voice=os.getenv("AGENT_VOICE", "nova"),
        play_audio=True
    )
    if audio_path:
        print(f"Agent spoke: {message}")
```

### Batch Processing

```python
from voice_utils import text_to_speech

messages = [
    "First announcement",
    "Second announcement",
    "Third announcement"
]

for i, msg in enumerate(messages):
    text_to_speech(
        msg,
        output_file=f"announcement_{i+1}.mp3",
        play_audio=False
    )
```

### Disabled Mode

```python
import os
os.environ["VOICE_ENABLED"] = "false"

# All calls return None immediately without API calls
result = text_to_speech("This won't be generated")
assert result is None
```

## Performance Considerations

- API calls take ~1-2 seconds depending on text length
- Audio files are typically 50-200 KB for short messages
- Consider async/threading for multiple simultaneous requests
- Set `play_audio=False` for faster batch processing

## Troubleshooting

### "No module named 'openai'"

```bash
pip install openai
```

### "Error generating speech: AuthenticationError"

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Audio playback not working (Linux)

Install an audio player:

```bash
# Ubuntu/Debian
sudo apt-get install pulseaudio-utils

# Or
sudo apt-get install alsa-utils
```

### Tests failing with import errors

Run tests from the `agents` directory:

```bash
cd agents
python -m pytest test_voice_utils.py -v
```

## License

Part of the Hybrid Letta Agents project.

## Contributing

When modifying this module:

1. Write tests first (TDD)
2. Run full test suite
3. Update this README if behavior changes
4. Log changes in `tdd_contracts.jsonl`

## Support

For issues or questions, refer to the main project documentation.
