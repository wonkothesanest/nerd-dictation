# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nerd-dictation is an offline speech-to-text utility for desktop Linux that supports multiple speech recognition engines (VOSK and Whisper). It's a single-file Python script (`nerd-dictation`) designed to be simple, hackable, and have zero overhead by relying on manual activation rather than background processes.

**Key Goal (from readme.rst:8)**: The maintainer wants to integrate an LLM for accurate translation and punctuation, with the ability to supply a prompt for the engine and temperature control. **Whisper integration has been completed** to address this goal, providing better punctuation and capitalization than VOSK.

## Architecture

### Single-File Design

The entire application is contained in the executable `nerd-dictation` file (Python script without `.py` extension). This design choice prioritizes:
- Easy hackability - users can directly modify behavior
- Minimal dependencies - only built-in modules plus STT engines (`vosk` required, `faster-whisper` optional)
- Simple distribution - no complex package structure

### Core Command Pattern

The tool operates through subcommands:
- `begin` - Start dictation (loads STT model, begins audio recording)
- `end` - Stop dictation and output text
- `cancel` - Stop dictation without output
- `suspend` - Pause the process (keeps model in memory)
- `resume` - Resume from suspended state

### Cookie-Based IPC

Commands communicate via a "cookie" file in `/tmp` (default: `nerd-dictation.cookie`):
- Contains the PID of the running process
- File modification time signals state changes
- `begin` creates the cookie, `end` touches it, `cancel` deletes it

### Signal-Based Suspend/Resume

Process control uses POSIX signals:
- `SIGUSR1` / `SIGTSTP` - suspend recording and pause process
- `SIGCONT` - resume recording
- `SIGHUP` - reload user configuration
- Suspend closes audio recording subprocess, stops STT processing (VOSK or Whisper)

### Audio Recording Pipeline

Three input methods supported via external commands:
- `PAREC` (default) - PulseAudio recording
- `SOX` - Alternative audio system
- `PW-CAT` - PipeWire recording

Audio subprocess output is made non-blocking and read in chunks to feed the STT engine.

### STT Engine Abstraction

The codebase uses an abstract `STTEngine` class (nerd-dictation:868-926) that defines a common interface for speech recognition engines:

**Core Methods:**
- `initialize()` - Load model and prepare for recognition
- `process_audio_chunk(data)` - Process raw PCM audio data
- `get_partial_result()` - Get work-in-progress transcription (streaming engines only)
- `get_final_result()` - Get completed transcription
- `reset()` - Clear state on suspend/resume
- `supports_progressive()` - Whether engine supports progressive typing

**Implementations:**

1. **VoskEngine** (nerd-dictation:928-1038)
   - Streaming recognition with partial results
   - Returns lowercase text without punctuation
   - Supports progressive typing mode
   - Lower memory usage (~50MB for small models)
   - Real-time processing (no latency)

2. **WhisperEngine** (nerd-dictation:1040-1260+)
   - Batch processing (processes complete audio buffer)
   - Returns properly formatted text with punctuation and capitalization
   - Deferred output mode only (no progressive typing)
   - Higher memory usage (150MB-3GB depending on model)
   - Includes silence detection to auto-transcribe during pauses
   - Uses `faster-whisper` library with CTranslate2 backend
   - Supports temperature control and initial prompts

### Text Processing Pipeline

1. **STT Recognition** - VOSK or Whisper engine
2. **Number Conversion** (optional) - Complex words-to-digits system
3. **Basic Processing** - Capitalization (VOSK only), newline removal
4. **User Configuration** - Custom Python script processing
5. **Output** - Simulated keystrokes or stdout

### Number Parsing System

Sophisticated number-to-digit conversion (`from_words_to_digits` class, nerd-dictation:473-799):
- Handles units, tens, scales (hundred, thousand, million, etc.)
- Detects series (e.g., "two four six eight" → "2468")
- Auto-delimits to prevent incorrect accumulation (e.g., "one hundred two hundred" → "100 200")
- Supports suffixes (ordinals: "first" → "1st")
- Handles mathematical expressions ("plus", "minus", "times", etc.)

### Progressive vs Deferred Output

Two typing modes:
- **Progressive** (default) - Types as you speak, using backspaces to correct misrecognitions
- **Deferred** (`--defer-output`) - Waits until end to type full text

Progressive mode uses diff algorithm to minimize character changes (nerd-dictation:1043-1051).

### Input Simulation

Multiple tools supported for keystroke simulation:
- `XDOTOOL` (default) - X11 only
- `YDOTOOL` - Universal (requires setup)
- `DOTOOL` / `DOTOOLC` - Universal, uses persistent subprocess with stdin protocol
- `WTYPE` - Wayland
- `STDOUT` - Output with Ctrl-H for backspaces

DOTOOL is special: maintains persistent subprocess (nerd-dictation:216-256) to avoid startup overhead per keystroke.

## Whisper-Specific Features

### Silence Detection & Auto-Transcription

Whisper includes intelligent silence detection that automatically transcribes when it detects a pause in speech:

- **RMS Energy Analysis**: Calculates root-mean-square energy of each audio chunk to detect silence
- **Configurable Threshold**: `--whisper-silence-threshold` (default: 0.01)
- **Configurable Duration**: `--whisper-silence-duration` (default: 0.5 seconds)
- **Auto-Transcribe**: When silence is detected after speech, automatically transcribes the buffered audio
- **Progressive-Like Experience**: Provides near-real-time output despite batch processing

This allows Whisper to feel more responsive despite its batch-processing nature, automatically outputting text at natural pause points (end of sentences, breaths, etc.).

### Temperature & Prompt Control

Addresses the maintainer's original goal for LLM-style control:

- **Temperature** (`--whisper-temperature`): Controls randomness in transcription (0.0 = deterministic, 1.0 = creative)
- **Initial Prompt** (`--whisper-initial-prompt`): Guides transcription style, vocabulary, and formatting
  - Example: "Technical documentation with proper punctuation and capitalization."
  - Helps with domain-specific vocabulary, acronyms, proper nouns
  - Influences punctuation style

### Model Selection

Multiple model sizes available via `--whisper-model`:
- `tiny` - Fastest, ~150MB RAM, lowest accuracy
- `base` - Good balance (default), ~300MB RAM
- `small` - Better accuracy, ~600MB RAM
- `medium` - High accuracy, ~1.5GB RAM
- `large` - Best accuracy, ~3GB RAM
- `turbo` - Optimized large model

### Compute Type Optimization

Via `--whisper-compute-type`:
- `float16` - Fastest (requires GPU or modern CPU with FP16 support)
- `float32` - Standard precision
- `int8` - Quantized, lowest memory usage, slight accuracy tradeoff
- Auto-fallback: If float16 fails on CPU, automatically falls back to int8

### Language Support

- Auto-detection by default
- Manual specification via `--whisper-language` (e.g., `en`, `es`, `fr`, `de`, `ja`, etc.)
- Supports 99 languages

## Development Environment

### Virtual Environment Setup

**IMPORTANT:** Development and testing require dependencies to be installed. Always activate the virtual environment before running tests or development commands:

```bash
# Activate the venv
source /home/dusty/workspace/dusty/venv/bin/activate

# Verify dependencies are available
pip list | grep -E "(numpy|whisper|scipy)"
```

**Required Dependencies for Whisper Testing:**
- `faster-whisper` (1.2.0+) - Whisper speech recognition engine
- `numpy` (1.26.4+) - Audio processing and manipulation
- `scipy` (1.14.1+) - Audio resampling

Without these dependencies, Whisper-related tests will be skipped.

## Development Commands

**Note:** Always activate the venv first: `source /home/dusty/workspace/dusty/venv/bin/activate`

### Code Quality

Format code:
```bash
black nerd-dictation
```

Type checking:
```bash
mypy --strict nerd-dictation
```

Linting:
```bash
pylint nerd-dictation --disable=C0103,C0111,C0301,C0302,C0415,E0401,E0611,I1101,R0801,R0902,R0903,R0912,R0913,R0914,R0915,R1705,W0212,W0703
```

### Testing

**IMPORTANT:** Activate venv before running tests:
```bash
source /home/dusty/workspace/dusty/venv/bin/activate
```

Run number conversion tests:
```bash
python3 tests/from_words_to_digits.py
```

Run Whisper engine tests (requires dependencies):
```bash
python3 test_whisper_engine.py
```

Run tests with auto-reloading on file change (Linux with inotifywait):
```bash
bash -c 'while true; do inotifywait -e close_write nerd-dictation tests/from_words_to_digits.py ; python3 tests/from_words_to_digits.py ; done'
```

### Manual Testing

Basic test sequence (VOSK):
```bash
./nerd-dictation begin --vosk-model-dir=./model &
# Speak something
./nerd-dictation end
```

Whisper test sequence:
```bash
./nerd-dictation begin --stt-engine=WHISPER --whisper-model=base &
# Speak something (will auto-transcribe on silence or when you run 'end')
./nerd-dictation end
```

Whisper with custom settings:
```bash
./nerd-dictation begin \
  --stt-engine=WHISPER \
  --whisper-model=small \
  --whisper-language=en \
  --whisper-temperature=0.2 \
  --whisper-initial-prompt="Technical documentation with proper punctuation." &
# Speak...
./nerd-dictation end
```

## User Configuration

Location: `~/.config/nerd-dictation/nerd-dictation.py`

Must define function:
```python
def nerd_dictation_process(text: str) -> str:
    # Process and return text
    return text
```

Configuration is:
- Lazy-loaded on first text processing (nerd-dictation:1376-1377)
- Reloadable via `SIGHUP` signal without restarting
- Optional - absence doesn't cause errors
- Can access `sys.argv` for custom arguments (using `--` to end arg parsing)

See `examples/` directory for reference configurations.

## Important Technical Details

### Delayed Imports

STT engine imports are delayed until after audio recording starts to minimize latency between user activation and recording start. This prevents missing the beginning of speech:
- VOSK: imported in `VoskEngine.initialize()`
- Whisper: imported in `WhisperEngine.initialize()` and `_is_silence()` (numpy)

### Message Output

All informational messages go to `stderr` (hacking.rst:40-43). Only transcribed text goes to `stdout`. This allows piping output: `nerd-dictation begin --output=STDOUT --timeout=1.0`

### File Paths

Default paths:
- VOSK Model: `~/.config/nerd-dictation/model`
- Whisper Models: `~/.config/nerd-dictation/whisper-models/`
- Config: `~/.config/nerd-dictation/nerd-dictation.py`
- Cookie: `/tmp/nerd-dictation.cookie`

Uses `XDG_CONFIG_HOME` if set, otherwise `~/.config`.

Whisper models are automatically downloaded by `faster-whisper` to the `whisper-models/` directory on first use.

## Code Style Conventions

- Python 3.6+ compatibility (typed as strings for Py3.6)
- Type hints required (checked with `mypy --strict`)
- Single file, only built-in modules except STT engines (`vosk`, `faster-whisper`)
- Functions prefixed with subsystem comments (e.g., "# Simulate Input: XDOTOOL")
- Global state avoided except for DOTOOL subprocess reference
- Class-based abstraction for STT engines (see `STTEngine` base class)

## Choosing Between VOSK and Whisper

### Use VOSK when:
- You want real-time progressive typing (text appears as you speak)
- You need minimal latency
- You have limited RAM (<1GB available)
- You want minimal dependencies
- You're using grammar constraints (VOSK-specific feature)
- You prefer to do your own punctuation/capitalization in post-processing

### Use Whisper when:
- You want accurate punctuation and capitalization out-of-the-box
- You need higher transcription accuracy
- You can accept slight delay (0.5-2s after speaking)
- You have sufficient RAM (at least 500MB for `base` model)
- You want to use temperature and prompt control
- You want better multilingual support
- You're dictating longer-form content (paragraphs, not commands)

### Default Choice
VOSK remains the default engine for backward compatibility and its zero-configuration experience. Users can easily switch by adding `--stt-engine=WHISPER` to their commands.

## Contributing Notes

From hacking.rst:
- Personal features should go in user configuration, not the main script
- Open an issue if unsure whether a feature belongs in core
- Ensure recording starts as quickly as possible (critical for UX)
