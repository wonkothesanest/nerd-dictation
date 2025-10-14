###################################
Using Whisper with nerd-dictation
###################################

Overview
========

nerd-dictation supports OpenAI's Whisper speech recognition engine as an alternative to VOSK.
Whisper generally provides better transcription quality, proper punctuation, and capitalization compared to VOSK.

**Key Differences from VOSK:**

✓ **Better Accuracy**: Higher quality transcriptions
✓ **Proper Punctuation**: Automatically adds periods, commas, etc.
✓ **Proper Capitalization**: No need for post-processing
✓ **Multi-language**: Superior support for multiple languages
✓ **LLM-Ready**: Foundation for future LLM integration

✗ **No Progressive Typing**: Must use deferred output mode (types all text at once when done)
✗ **Higher Memory**: Larger models use more RAM than VOSK
✗ **Slower Startup**: Model loading takes longer than VOSK


Installation
============

Install faster-whisper (the recommended Whisper implementation):

.. code-block:: sh

   pip3 install faster-whisper

That's it! The Whisper models will be automatically downloaded on first use.


Quick Start
===========

Basic usage with the tiny model:

.. code-block:: sh

   # Start recording (speak into your microphone)
   nerd-dictation begin --stt-engine WHISPER --whisper-model tiny

   # Stop recording and transcribe
   nerd-dictation end

The tiny model is fast but less accurate. For better quality, use the ``base`` or ``small`` models:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER --whisper-model base


Command-Line Arguments
======================

Core Whisper Options
--------------------

``--stt-engine {VOSK,WHISPER}``
   Speech-to-text engine to use. Default is ``VOSK``.

   Set to ``WHISPER`` to enable Whisper transcription.

``--whisper-model {tiny,base,small,medium,large,turbo}``
   Whisper model to use. Default: ``base``

   **Model Comparison:**

   ========== ========= ============ ==============
   Model      Memory    Speed        Accuracy
   ========== ========= ============ ==============
   tiny       ~150 MB   Very Fast    Good
   base       ~300 MB   Fast         Better
   small      ~600 MB   Medium       Very Good
   medium     ~1.5 GB   Slower       Excellent
   large      ~3 GB     Slow         Best
   turbo      ~800 MB   Fast         Very Good
   ========== ========= ============ ==============

   **Recommendation:** Start with ``base`` for a good balance of speed and accuracy.

``--whisper-model-dir DIR``
   Directory to store Whisper models.

   Default: ``~/.config/nerd-dictation/whisper-models/``

   Models are automatically downloaded and cached here on first use.


Advanced Whisper Options
-------------------------

``--whisper-language LANG``
   Language code for transcription (e.g., ``en``, ``es``, ``fr``, ``de``, ``ja``).

   Default: Auto-detect

   Example for Spanish:

   .. code-block:: sh

      nerd-dictation begin --stt-engine WHISPER --whisper-language es

``--whisper-temperature FLOAT``
   Temperature for Whisper sampling (0.0 to 1.0). Default: ``0.0``

   - ``0.0`` = Deterministic (most accurate, recommended)
   - ``0.2`` = Slightly creative
   - ``0.5`` = More variety (less accurate)
   - ``1.0`` = Maximum randomness (not recommended)

   Example:

   .. code-block:: sh

      nerd-dictation begin --stt-engine WHISPER --whisper-temperature 0.2

``--whisper-initial-prompt TEXT``
   Initial prompt to guide Whisper's transcription style.

   This helps Whisper understand the context and improve accuracy for specific domains.

   Examples:

   .. code-block:: sh

      # Technical documentation
      nerd-dictation begin --stt-engine WHISPER \
          --whisper-initial-prompt "Technical documentation with proper punctuation."

      # Code dictation
      nerd-dictation begin --stt-engine WHISPER \
          --whisper-initial-prompt "Python code with variable names in snake_case."

      # Formal writing
      nerd-dictation begin --stt-engine WHISPER \
          --whisper-initial-prompt "Formal business communication."

``--whisper-compute-type {float16,float32,int8}``
   Compute precision for Whisper inference. Default: ``float16``

   - ``float16`` = Fastest (GPU/special CPU required, auto-falls back to int8 on unsupported systems)
   - ``float32`` = Most accurate (slower, more memory)
   - ``int8`` = Fastest on CPU (good balance)

   **Note:** The system automatically falls back to ``int8`` if ``float16`` is not supported.

``--whisper-silence-duration SECONDS``
   Duration of continuous silence (in seconds) to trigger transcription. Default: ``0.5``

   When this much silence is detected after speech, Whisper transcribes the utterance.

   - Lower values (``0.3``) = More responsive, may cut off speech
   - Higher values (``1.0``) = More patient, waits longer for pauses

   Example:

   .. code-block:: sh

      nerd-dictation begin --stt-engine WHISPER --whisper-silence-duration 1.0

``--whisper-silence-threshold FLOAT``
   RMS energy threshold for silence detection (0.0 to 1.0). Default: ``0.01``

   Audio with energy below this is considered silence.

   - Lower values (``0.005``) = More sensitive (detects quieter speech)
   - Higher values (``0.02``) = Less sensitive (ignores quiet sounds)

   Adjust if speech is not being detected or background noise triggers transcription:

   .. code-block:: sh

      # More sensitive (for quiet microphone)
      nerd-dictation begin --stt-engine WHISPER --whisper-silence-threshold 0.005

      # Less sensitive (for noisy environment)
      nerd-dictation begin --stt-engine WHISPER --whisper-silence-threshold 0.02


Usage Examples
==============

Basic Dictation
---------------

Simple dictation with automatic transcription:

.. code-block:: sh

   # Start recording
   nerd-dictation begin --stt-engine WHISPER --whisper-model base

   # Speak: "Hello world. This is a test."
   # (pause for 0.5 seconds - automatic transcription happens)
   # Keep speaking: "Whisper adds punctuation automatically."

   # Stop and type everything
   nerd-dictation end

Output with Timeout
-------------------

Record for up to 10 seconds or until no speech for 3 seconds:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER --timeout 3

Capture to Variable
-------------------

Store transcription in a shell variable instead of typing:

.. code-block:: sh

   SPEECH="$(nerd-dictation begin --stt-engine WHISPER \
                --whisper-model base \
                --timeout 3 \
                --output STDOUT)"

   echo "You said: $SPEECH"

Multi-language Dictation
------------------------

Dictate in Spanish:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER \
       --whisper-model base \
       --whisper-language es

Technical Documentation
-----------------------

Optimize for technical writing:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER \
       --whisper-model small \
       --whisper-temperature 0.0 \
       --whisper-initial-prompt "Technical documentation with code terms."

Verbose Mode
------------

See detailed information about the transcription process:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER \
       --whisper-model tiny \
       --verbose 1

   # Output:
   # Loading Whisper model (tiny)...
   # Whisper model loaded (compute type: int8).
   # Transcribing 5.2s of audio...
   # Transcription complete: "Your transcribed text here."


Performance Tips
================

Model Selection
---------------

Choose the right model for your needs:

**For Speed (Real-time Use):**
   Use ``tiny`` or ``base`` models on modern hardware.

**For Accuracy (Final Transcription):**
   Use ``small``, ``medium``, or ``large`` models.

**For Development/Testing:**
   Always start with ``tiny`` to iterate quickly.

Memory Considerations
---------------------

If you encounter out-of-memory errors:

1. Use a smaller model (``tiny`` or ``base``)
2. Use ``--whisper-compute-type int8``
3. Close other memory-intensive applications

Example:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER \
       --whisper-model tiny \
       --whisper-compute-type int8

Startup Time
------------

The first run downloads the model (~1-5 minutes depending on size).
Subsequent runs load from cache (~2-10 seconds depending on model size).

To keep the process loaded for multiple uses:

.. code-block:: sh

   # Start and suspend immediately
   nerd-dictation begin --stt-engine WHISPER \
       --whisper-model base \
       --suspend-on-start

   # In your keyboard shortcuts:
   # Resume: nerd-dictation resume
   # Suspend: nerd-dictation suspend
   # End: nerd-dictation end


Troubleshooting
===============

Whisper hallucinations (repeating text)
----------------------------------------

**Problem:** Whisper outputs repetitive nonsense like "get a chance to get a chance to..."

**Cause:** No audio input or very quiet audio.

**Solutions:**

1. Check microphone input:

   .. code-block:: sh

      pactl list sources  # Find your microphone

      # Test with parec
      parec --rate=16000 --channels=1 | aplay

2. Increase silence threshold (less sensitive):

   .. code-block:: sh

      nerd-dictation begin --stt-engine WHISPER \
          --whisper-silence-threshold 0.02

3. Use ``--verbose 2`` to see audio energy levels:

   .. code-block:: sh

      nerd-dictation begin --stt-engine WHISPER \
          --verbose 2

      # Check stderr for: "Audio energy: 0.XXXX"

Float16 not supported error
----------------------------

**Problem:**

.. code-block::

   ValueError: Requested float16 compute type, but the target device or
   backend do not support efficient float16 computation.

**Solution:** This is automatically handled! The system falls back to ``int8``.

If you still see this error, manually specify:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER \
       --whisper-compute-type int8

Model download fails
--------------------

**Problem:** Model download interrupted or fails.

**Solutions:**

1. Check internet connection
2. Manually download model:

   .. code-block:: sh

      python3 -c "from faster_whisper import WhisperModel; \
                  WhisperModel('base', download_root='~/.config/nerd-dictation/whisper-models')"

3. Use a smaller model that may be cached: ``--whisper-model tiny``

Transcription too slow
----------------------

**Problem:** Long delay after speaking.

**Solutions:**

1. Use a smaller model (``tiny`` or ``base``)
2. Use ``int8`` compute type
3. Reduce audio length with ``--timeout``

Example:

.. code-block:: sh

   nerd-dictation begin --stt-engine WHISPER \
       --whisper-model tiny \
       --whisper-compute-type int8 \
       --timeout 5

Speech not detected
-------------------

**Problem:** You speak but nothing is transcribed.

**Solutions:**

1. Lower the silence threshold (more sensitive):

   .. code-block:: sh

      nerd-dictation begin --stt-engine WHISPER \
          --whisper-silence-threshold 0.005

2. Check microphone volume (increase if needed)
3. Use ``--verbose 2`` to debug:

   .. code-block:: sh

      nerd-dictation begin --stt-engine WHISPER --verbose 2
      # Look for "Audio energy: X.XXXX" in stderr


Whisper vs VOSK Comparison
===========================

When to use Whisper:
--------------------

✓ You need proper punctuation and capitalization
✓ Accuracy is more important than speed
✓ You're dictating complete sentences or paragraphs
✓ You're working in multiple languages
✓ You have sufficient RAM (>1GB available)

When to use VOSK:
-----------------

✓ You need progressive typing (seeing text as you speak)
✓ Speed/responsiveness is critical
✓ You're on a low-memory system
✓ You have custom grammars or vocabularies
✓ You need the fastest possible startup time

Side-by-side Example
--------------------

**VOSK Output:**

.. code-block::

   hello world this is a test of the speech recognition system

**Whisper Output:**

.. code-block::

   Hello world. This is a test of the speech recognition system.

Notice Whisper adds:
- Capital letters
- Proper sentence punctuation


Configuration Examples
======================

Whisper works with nerd-dictation's configuration system. Here's a configuration that works well with Whisper:

``~/.config/nerd-dictation/nerd-dictation.py``

.. code-block:: python

   def nerd_dictation_process(text):
       """
       Post-process Whisper output.
       Whisper already provides punctuation and capitalization,
       so this is mainly for custom replacements.
       """

       # Fix common project-specific terms
       text = text.replace("nerd dictation", "nerd-dictation")
       text = text.replace("Whisper API", "faster-whisper")

       # Custom commands
       if text.strip().lower() == "new line":
           return "\n"
       if text.strip().lower() == "new paragraph":
           return "\n\n"

       return text


For more configuration examples, see the ``examples/`` directory.


Technical Details
=================

Audio Format
------------

- Sample Rate: 44100 Hz (default) or user-specified with ``--sample-rate``
- Format: PCM s16le (signed 16-bit little-endian)
- Channels: Mono (1 channel)

Whisper prefers 16kHz, but faster-whisper handles resampling automatically.

Processing Flow
---------------

1. Audio recording begins (parec/sox/pw-cat)
2. Whisper model loads in parallel
3. Audio chunks buffered in memory
4. Silence detection monitors RMS energy levels
5. After configured silence duration, transcription triggered
6. Whisper transcribes buffered audio
7. Text processed (user config, number parsing, etc.)
8. Output simulated as keystrokes or printed to stdout

Differences from VOSK
---------------------

**VOSK Pipeline:**

.. code-block::

   Audio → Stream Processing → Partial Results → Progressive Typing

**Whisper Pipeline:**

.. code-block::

   Audio → Buffer → Silence Detection → Batch Transcription → Output

This means:
- VOSK can type as you speak
- Whisper types everything at once when finished
- Whisper is more accurate but less "live"


Known Limitations
=================

1. **No Progressive Typing**: Whisper cannot type as you speak. The ``--defer-output`` flag is implied.

2. **Higher Memory Usage**: Especially with larger models (medium/large use 1.5-3GB RAM).

3. **Startup Delay**: First-time model download can take several minutes. Subsequent loads take 2-10 seconds.

4. **Silence Detection**: May need tuning for your microphone and environment.

5. **Hallucinations on Silence**: Whisper may generate nonsense if no audio is detected. This is a known Whisper behavior.


Further Reading
===============

- `Whisper Model Card <https://github.com/openai/whisper>`__
- `faster-whisper Documentation <https://github.com/guillaumekln/faster-whisper>`__
- `nerd-dictation Repository <https://github.com/ideasman42/nerd-dictation>`__


Getting Help
============

If you encounter issues:

1. Check this documentation's Troubleshooting section
2. Run with ``--verbose 2`` to see detailed logs
3. Test with the ``tiny`` model first
4. Open an issue on GitHub with:
   - Your command
   - Full error message
   - Output of ``--verbose 2``
   - Your system info (OS, RAM, CPU)
