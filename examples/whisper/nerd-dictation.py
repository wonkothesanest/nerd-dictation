#!/usr/bin/env python3
"""
Example configuration for using Whisper with nerd-dictation.

Location: ~/.config/nerd-dictation/nerd-dictation.py

Whisper provides automatic punctuation and capitalization, so this configuration
focuses on post-processing and custom commands specific to your needs.
"""


def nerd_dictation_process(text):
    """
    Process text from Whisper before typing.

    Args:
        text: The transcribed text from Whisper (already has punctuation and capitalization)

    Returns:
        The processed text to be typed
    """

    # -------------------------------------------------------------------------
    # Custom Voice Commands
    # -------------------------------------------------------------------------
    # These detect specific phrases and replace them with special actions

    text_lower = text.strip().lower()

    # Line break commands
    if text_lower == "new line":
        return "\n"
    if text_lower == "new paragraph":
        return "\n\n"

    # Tab command
    if text_lower == "tab key":
        return "\t"

    # Common programming commands
    if text_lower == "arrow function":
        return "() => {}"
    if text_lower == "console log":
        return "console.log();"

    # -------------------------------------------------------------------------
    # Project-Specific Term Corrections
    # -------------------------------------------------------------------------
    # Fix terms that Whisper might transcribe incorrectly

    # Software names and technical terms
    text = text.replace("nerd dictation", "nerd-dictation")
    text = text.replace("Whisper API", "faster-whisper")
    text = text.replace("Vosk API", "VOSK-API")
    text = text.replace("Python 3", "Python3")

    # Programming language terms
    text = text.replace("async await", "async/await")
    text = text.replace("if else", "if/else")

    # -------------------------------------------------------------------------
    # Code Formatting
    # -------------------------------------------------------------------------
    # Useful for dictating code

    # Convert spoken symbols to actual symbols
    replacements = {
        " dot ": ".",
        " arrow ": "->",
        " double arrow ": "=>",
        " equals equals ": "==",
        " not equals ": "!=",
        " less than or equal ": "<=",
        " greater than or equal ": ">=",
        " plus equals ": "+=",
        " minus equals ": "-=",
    }

    for spoken, symbol in replacements.items():
        text = text.replace(spoken, symbol)

    # -------------------------------------------------------------------------
    # Custom Abbreviations
    # -------------------------------------------------------------------------
    # Expand common abbreviations you might say

    # Only expand at word boundaries to avoid false positives
    import re

    # Example: "btw" -> "by the way" (case-insensitive)
    # text = re.sub(r'\bbtw\b', 'by the way', text, flags=re.IGNORECASE)

    # -------------------------------------------------------------------------
    # Markdown Formatting
    # -------------------------------------------------------------------------
    # Useful for dictating markdown documents

    # Heading commands
    if text_lower.startswith("heading one "):
        return "# " + text[12:]  # Remove "heading one " prefix
    if text_lower.startswith("heading two "):
        return "## " + text[12:]
    if text_lower.startswith("heading three "):
        return "### " + text[14:]

    # Markdown formatting
    if text_lower.startswith("code block "):
        lang = ""  # You could extract language from voice command
        return f"```{lang}\n\n```"
    if text_lower.startswith("bullet point "):
        return "- " + text[13:]
    if text_lower.startswith("numbered point "):
        return "1. " + text[15:]

    # -------------------------------------------------------------------------
    # Remove Filler Words (Optional)
    # -------------------------------------------------------------------------
    # Uncomment to remove common filler words

    # filler_words = ["um", "uh", "like", "you know"]
    # for filler in filler_words:
    #     text = re.sub(r'\b' + filler + r'\b', '', text, flags=re.IGNORECASE)
    #
    # # Clean up multiple spaces
    # text = re.sub(r'\s+', ' ', text).strip()

    # -------------------------------------------------------------------------
    # Return processed text
    # -------------------------------------------------------------------------
    return text


# -----------------------------------------------------------------------------
# Advanced Example: Context-Aware Processing
# -----------------------------------------------------------------------------
# Uncomment this version if you want to change behavior based on active window

# def nerd_dictation_process(text):
#     """
#     Context-aware text processing based on active window.
#     """
#     import subprocess
#
#     # Get active window title (requires xdotool or similar)
#     try:
#         window_title = subprocess.check_output(
#             ["xdotool", "getactivewindow", "getwindowname"],
#             text=True
#         ).strip()
#     except:
#         window_title = ""
#
#     # Different processing for different applications
#     if "Visual Studio Code" in window_title or "vim" in window_title:
#         # In code editor: apply programming-focused processing
#         text = text.replace("new line", "\n")
#         # Add more code-specific replacements
#
#     elif "Firefox" in window_title or "Chrome" in window_title:
#         # In browser: apply web-focused processing
#         pass
#
#     elif "Terminal" in window_title:
#         # In terminal: apply command-focused processing
#         text = text.lower()  # Commands are usually lowercase
#
#     # Apply general replacements
#     text = text.replace("nerd dictation", "nerd-dictation")
#
#     return text


# -----------------------------------------------------------------------------
# Notes
# -----------------------------------------------------------------------------
#
# 1. Unlike VOSK, Whisper already provides:
#    - Proper capitalization (e.g., "Hello World" not "hello world")
#    - Punctuation (e.g., "Hello. How are you?" not "hello how are you")
#    - Better grammar (e.g., "I'm" not "i am")
#
# 2. This means your configuration can focus on:
#    - Voice commands (e.g., "new line" -> "\n")
#    - Project-specific terms (e.g., "nerd dictation" -> "nerd-dictation")
#    - Code formatting (e.g., "arrow function" -> "() => {}")
#    - Context-aware behavior (different processing per application)
#
# 3. Common use cases:
#    - Programming: Add code snippets and symbol shortcuts
#    - Writing: Add markdown formatting commands
#    - General: Fix common misrecognitions for your accent/terminology
#
# 4. Testing your configuration:
#    - Start dictation: nerd-dictation begin --stt-engine WHISPER
#    - Say: "test new line test"
#    - Expected: "test\ntest" (with actual line break)
#
# 5. Reloading configuration without restart:
#    - Send SIGHUP signal: kill -HUP $(cat /tmp/nerd-dictation.cookie)
#    - Or use: nerd-dictation suspend && nerd-dictation resume
#
# 6. Debugging:
#    - Use --verbose 1 to see transcription before processing
#    - Add print() statements (they go to stderr)
#    - Example: print(f"DEBUG: Received text: {text!r}", file=sys.stderr)
