# Whisper Configuration Examples

This directory contains example configurations for using nerd-dictation with Whisper.

## Setup

Copy the example configuration to your config directory:

```bash
mkdir -p ~/.config/nerd-dictation
cp nerd-dictation.py ~/.config/nerd-dictation/
```

## What's Included

### `nerd-dictation.py`

A comprehensive example configuration showing:

- **Voice Commands**: Speak "new line" to insert line breaks
- **Code Formatting**: Convert spoken code terms to symbols
- **Project-Specific Terms**: Fix common misrecognitions
- **Markdown Support**: Voice commands for headings and formatting
- **Context-Aware Processing**: Different behavior per application (commented example)

## Key Differences from VOSK Configurations

Unlike VOSK, Whisper already provides:

- ✓ Proper capitalization ("Hello" not "hello")
- ✓ Punctuation ("Hello. How are you?" not "hello how are you")
- ✓ Better grammar ("I'm" not "i am")

This means your Whisper configuration should focus on:

1. **Voice commands** for special actions
2. **Project-specific terms** that Whisper might mishear
3. **Code formatting** helpers
4. **Context-aware behavior** for different applications

## Quick Test

Test your configuration with:

```bash
# Start dictation
nerd-dictation begin --stt-engine WHISPER --whisper-model base

# Say: "test new line test"
# Expected output: "test" (line break) "test"

# Stop dictation
nerd-dictation end
```

## Reloading Configuration

Reload without restarting:

```bash
# Method 1: Send SIGHUP signal
kill -HUP $(cat /tmp/nerd-dictation.cookie)

# Method 2: Suspend and resume
nerd-dictation suspend
nerd-dictation resume
```

## Debugging

See what Whisper transcribed before processing:

```bash
nerd-dictation begin --stt-engine WHISPER --verbose 1 --output STDOUT
```

Add debug prints to your configuration:

```python
import sys

def nerd_dictation_process(text):
    print(f"DEBUG: Received: {text!r}", file=sys.stderr)
    # ... your processing ...
    print(f"DEBUG: Returning: {processed!r}", file=sys.stderr)
    return processed
```

## Common Use Cases

### Programming

```python
# In nerd_dictation_process():
if text_lower == "arrow function":
    return "() => {}"
if text_lower == "console log":
    return "console.log();"
```

### Markdown Writing

```python
# In nerd_dictation_process():
if text_lower.startswith("heading one "):
    return "# " + text[12:]
if text_lower.startswith("bullet point "):
    return "- " + text[13:]
```

### Terminal Commands

```python
# In nerd_dictation_process():
# Force lowercase for commands
if "Terminal" in get_active_window():
    return text.lower()
```

## More Examples

See also:
- `examples/default/nerd-dictation.py` - VOSK-focused examples (many apply to Whisper too)
- `examples/begin_end_commands/nerd-dictation.py` - Start/finish command examples
- `readme-whisper.rst` - Full Whisper documentation

## Tips

1. **Start Simple**: Begin with a few voice commands you'll actually use
2. **Test Incrementally**: Add one feature at a time and test it
3. **Use Verbose Mode**: `--verbose 1` helps debug issues
4. **Check Transcription**: Make sure Whisper hears you correctly before blaming the config
5. **Reload Often**: Use SIGHUP to test changes without restarting

## Getting Help

If your configuration isn't working:

1. Test with an empty configuration first (move your config file temporarily)
2. Check for Python syntax errors: `python3 -m py_compile ~/.config/nerd-dictation/nerd-dictation.py`
3. Add debug prints to see what text you're receiving
4. Run with `--verbose 2` to see detailed processing logs

For more help, see the main documentation: `readme-whisper.rst`
