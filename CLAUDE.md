# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nerd-dictation is an offline speech-to-text utility for desktop Linux that uses the VOSK-API. It's a single-file Python script (`nerd-dictation`) designed to be simple, hackable, and have zero overhead by relying on manual activation rather than background processes.

**Key Goal (from readme.rst:8)**: The maintainer wants to integrate an LLM for accurate translation and punctuation, with the ability to supply a prompt for the engine and temperature control.

## Architecture

### Single-File Design

The entire application is contained in the executable `nerd-dictation` file (Python script without `.py` extension). This design choice prioritizes:
- Easy hackability - users can directly modify behavior
- Minimal dependencies - only built-in modules plus `vosk` for speech-to-text
- Simple distribution - no complex package structure

### Core Command Pattern

The tool operates through subcommands:
- `begin` - Start dictation (loads VOSK model, begins audio recording)
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

Process control uses POSIX signals (nerd-dictation:1171-1179):
- `SIGUSR1` / `SIGTSTP` - suspend recording and pause process
- `SIGCONT` - resume recording
- `SIGHUP` - reload user configuration
- Suspend closes audio recording subprocess, stops VOSK processing

### Audio Recording Pipeline

Three input methods supported via external commands:
- `PAREC` (default) - PulseAudio recording
- `SOX` - Alternative audio system
- `PW-CAT` - PipeWire recording

Audio subprocess output is made non-blocking (nerd-dictation:94-99) and read in chunks to feed VOSK in real-time.

### Text Processing Pipeline

1. **VOSK Recognition** (nerd-dictation:928-1266) - Returns lowercase text
2. **Number Conversion** (nerd-dictation:359-799) - Complex words-to-digits system
3. **Basic Processing** (nerd-dictation:826-859) - Capitalization, newline removal
4. **User Configuration** (nerd-dictation:806-823) - Custom Python script processing
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

## Development Commands

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

Run number conversion tests:
```bash
./tests/from_words_to_digits.py
```

Run tests with auto-reloading on file change (Linux with inotifywait):
```bash
bash -c 'while true; do inotifywait -e close_write nerd-dictation tests/from_words_to_digits.py ; tests/from_words_to_digits.py ; done'
```

### Manual Testing

Basic test sequence:
```bash
./nerd-dictation begin --vosk-model-dir=./model &
# Speak something
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

VOSK import is delayed until after audio recording starts (nerd-dictation:965) to minimize latency between user activation and recording start. This prevents missing the beginning of speech.

### Message Output

All informational messages go to `stderr` (hacking.rst:40-43). Only transcribed text goes to `stdout`. This allows piping output: `nerd-dictation begin --output=STDOUT --timeout=1.0`

### File Paths

Default paths:
- Model: `~/.config/nerd-dictation/model`
- Config: `~/.config/nerd-dictation/nerd-dictation.py`
- Cookie: `/tmp/nerd-dictation.cookie`

Uses `XDG_CONFIG_HOME` if set, otherwise `~/.config` (nerd-dictation:307-320).

## Code Style Conventions

- Python 3.6+ compatibility (typed as strings for Py3.6: nerd-dictation:216, 872, 955)
- Type hints required (checked with `mypy --strict`)
- Single file, only built-in modules except `vosk`
- Functions prefixed with subsystem comments (e.g., "# Simulate Input: XDOTOOL")
- Global state avoided except for DOTOOL subprocess reference (nerd-dictation:216)

## Contributing Notes

From hacking.rst:
- Personal features should go in user configuration, not the main script
- Open an issue if unsure whether a feature belongs in core
- Ensure recording starts as quickly as possible (critical for UX)
