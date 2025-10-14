# Product Requirements Document: Whisper Integration for nerd-dictation

## Document Information
- **Version**: 1.0
- **Date**: 2025-10-13
- **Author**: Code Analysis
- **Status**: Draft for Review

## Executive Summary

This PRD outlines the requirements for integrating OpenAI's Whisper speech recognition engine as an alternative to VOSK in nerd-dictation. This will enable users to choose between offline (VOSK) and potentially higher-accuracy recognition (Whisper), while maintaining the tool's core philosophy of simplicity, hackability, and zero background overhead.

The maintainer has expressed interest in using LLMs for "accurate translation and accurate punctuation" with the ability to "supply a prompt for the engine and temperature" (readme.rst:8). Whisper can be a first step toward this goal.

---

## Background & Motivation

### Current State
- nerd-dictation currently uses VOSK-API exclusively for speech-to-text
- VOSK integration is deeply embedded in the main processing loop (nerd-dictation:928-1266)
- All text from VOSK is lowercase, requiring post-processing (readme.rst:404)
- VOSK provides streaming recognition with partial results

### Why Whisper?
1. **Higher Accuracy**: Whisper generally provides better transcription quality than VOSK
2. **Better Punctuation & Capitalization**: Whisper returns properly formatted text with punctuation
3. **Multilingual Support**: Superior multi-language capabilities
4. **Foundation for LLM Integration**: Opens path to LLM-based post-processing (maintainer's stated goal)
5. **Active Development**: OpenAI Whisper is actively maintained and improved

### Challenges
1. **Batch vs Streaming**: Whisper processes complete audio files, not streaming data
2. **Latency**: Model loading and inference can be slower than VOSK
3. **Memory Usage**: Whisper models (especially large ones) use significant memory
4. **No Partial Results**: Cannot provide progressive typing like VOSK
5. **API vs Local**: Must decide between local whisper.cpp/faster-whisper or OpenAI API

---

## Goals & Non-Goals

### Goals
1. Add Whisper as an alternative STT engine alongside VOSK (not replacing it)
2. Maintain backward compatibility - all existing VOSK functionality must continue to work
3. Support both local Whisper (faster-whisper/whisper.cpp) and OpenAI API
4. Preserve the single-file architecture where possible
5. Maintain zero background process overhead
6. Support suspend/resume for Whisper models
7. Enable configuration for model size, language, temperature, and prompts

### Non-Goals
1. Remove or deprecate VOSK support
2. Implement real-time streaming transcription with Whisper (technical limitation)
3. Support all Whisper variants (focus on faster-whisper and optionally OpenAI API)
4. Implement progressive typing mode for Whisper (deferred output only)
5. Support Whisper grammar constraints (doesn't have this feature)

---

## Technical Analysis

### Current VOSK Integration Points

#### 1. Core Function: `text_from_vosk_pipe()` (lines 928-1266)
**What it does:**
- Loads VOSK model from directory
- Creates `KaldiRecognizer` with optional grammar file
- Reads audio chunks from recording subprocess (non-blocking)
- Calls `rec.AcceptWaveform(data)` for each chunk
- Gets partial results (`rec.PartialResult()`) and final results (`rec.FinalResult()`)
- Returns JSON with `{"text": "..."}` or `{"partial": "..."}`
- Supports progressive typing via diff algorithm

**Key VOSK-specific calls:**
```python
import vosk
vosk.SetLogLevel(-1)
model = vosk.Model(vosk_model_dir)
rec = vosk.KaldiRecognizer(model, sample_rate, grammar_json)
rec.AcceptWaveform(data)  # streaming chunks
rec.PartialResult()        # partial transcription
rec.FinalResult()          # final transcription
rec.Reset()                # on suspend
```

#### 2. Argument Parsing (lines 1565-1586)
- `--vosk-model-dir`: Path to model
- `--vosk-grammar-file`: Optional grammar constraints

#### 3. Main Entry Point: `main_begin()` (lines 1269-1277)
- Calls `text_from_vosk_pipe()` with all parameters

### Whisper Architecture Differences

| Feature | VOSK | Whisper |
|---------|------|---------|
| **Processing** | Streaming chunks | Batch (complete audio) |
| **Partial Results** | Yes | No |
| **Output Format** | Lowercase JSON | Formatted text with punctuation |
| **Model Loading** | Directory with files | Single model file or API |
| **Grammar Support** | Yes (JSON grammar) | No |
| **Progressive Typing** | Possible | Not practical |
| **Memory** | Lower | Higher (especially large models) |
| **Setup/Teardown** | Minimal | Model load can be slow |

---

## Architecture Design

### Option 1: Abstraction Layer (Recommended)

Create an abstraction layer that handles both VOSK and Whisper through a common interface.

**Pros:**
- Clean separation of concerns
- Easier to add future engines
- Better testability
- Maintains single-file architecture

**Cons:**
- More initial refactoring
- Slightly more complex

**Implementation:**
```python
# New abstract class/protocol
class STTEngine:
    def __init__(self, model_path, sample_rate, **kwargs): ...
    def process_audio_chunk(self, data: bytes) -> dict: ...
    def get_partial_result(self) -> Optional[str]: ...
    def get_final_result(self) -> str: ...
    def reset(self) -> None: ...
    def supports_streaming(self) -> bool: ...

class VoskEngine(STTEngine):
    # Current VOSK implementation

class WhisperEngine(STTEngine):
    # New Whisper implementation
```

### Option 2: Separate Function (Alternative)

Create `text_from_whisper_pipe()` parallel to `text_from_vosk_pipe()`.

**Pros:**
- Less refactoring
- VOSK code untouched
- Simpler to understand

**Cons:**
- Code duplication (signal handling, suspend/resume, timeout logic)
- Harder to maintain consistency
- Larger file

---

## Detailed Requirements

### 1. Command-Line Interface

#### New Arguments (all optional)
```bash
--stt-engine {VOSK,WHISPER,WHISPER_API}
    Default: VOSK

--whisper-model {tiny,base,small,medium,large,turbo}
    Default: base
    Path to model file or model size

--whisper-model-dir DIR
    Default: ~/.config/nerd-dictation/whisper-models/
    Where to store/find Whisper models

--whisper-language LANG
    Default: auto-detect
    Two-letter language code (en, es, fr, etc.)

--whisper-task {transcribe,translate}
    Default: transcribe

--whisper-temperature FLOAT
    Default: 0.0
    Temperature for sampling (0.0-1.0)
    Addresses maintainer's request for temperature control

--whisper-initial-prompt TEXT
    Default: None
    Prompt to guide transcription style
    Addresses maintainer's request for prompt control

--whisper-api-key KEY
    For WHISPER_API engine
    Can also use OPENAI_API_KEY environment variable

--whisper-compute-type {float16,float32,int8}
    Default: float16
    Precision for faster-whisper
```

#### Backward Compatibility
- `--vosk-model-dir` and `--vosk-grammar-file` remain unchanged
- Default engine is VOSK, so existing scripts work unchanged
- If `--whisper-*` args provided without `--stt-engine`, auto-select WHISPER

### 2. Whisper Implementation Details

#### Local Whisper: faster-whisper (Recommended)
**Why faster-whisper:**
- CTranslate2 backend for fast inference
- Lower memory usage than openai-whisper
- Maintains quality
- Easy pip install: `pip install faster-whisper`

**Implementation:**
```python
def text_from_whisper_pipe(
    *,
    whisper_model: str,           # model size or path
    whisper_model_dir: str,       # where to store models
    whisper_language: Optional[str],
    whisper_temperature: float,
    whisper_initial_prompt: Optional[str],
    whisper_compute_type: str,
    exit_fn: Callable[..., int],
    process_fn: Callable[[str], str],
    handle_fn: Callable[[int, str], None],
    timeout: float,
    sample_rate: int,
    input_method: str,
    pulse_device_name: str = "",
    suspend_on_start: bool = False,
    verbose: int = 0,
) -> bool:
    import tempfile
    from faster_whisper import WhisperModel

    # Start audio recording
    # Save audio to temporary WAV file
    # When end signal received:
    #   - Stop recording
    #   - Transcribe complete audio file
    #   - Output text in one shot
    # Progressive mode not supported - always deferred
```

#### Key Differences in Implementation:

**Audio Buffering:**
- Must save audio to temporary file (WAV format)
- Use tempfile module for atomic operations
- Clean up on exit/cancel/error

**No Progressive Typing:**
- Whisper doesn't support partial results
- Must force `progressive=False` mode
- Output all text at once when transcription complete
- Warn user if `--defer-output` not used with Whisper

**Model Loading:**
- Download model on first use (like VOSK)
- Cache in `~/.config/nerd-dictation/whisper-models/`
- Load model after recording starts (to minimize latency)

**Suspend/Resume:**
- On suspend: save audio buffer, unload model
- On resume: reload model, continue recording

### 3. Processing Flow Changes

#### Shared Components (keep as-is)
1. Audio recording subprocess (parec/sox/pw-cat)
2. Signal handling (SIGUSR1, SIGCONT, SIGHUP, SIGTSTP)
3. Cookie-based IPC
4. User configuration system
5. Number parsing
6. Input simulation

#### Engine-Specific Components

**VOSK Pipeline:**
```
Audio chunks → AcceptWaveform() → PartialResult/FinalResult → Progressive output
```

**Whisper Pipeline:**
```
Audio chunks → Buffer to file → Transcribe complete file → Single output
```

### 4. Audio Format Considerations

**Current:**
- Raw PCM s16le format from recording subprocesses
- 16-bit signed integer, little-endian
- Mono channel
- Sample rate: 44100 Hz (default) or user-specified

**Whisper Needs:**
- Prefers 16kHz sample rate (but accepts others)
- Can handle raw PCM or WAV files
- faster-whisper can transcribe numpy arrays directly

**Solution:**
- Save to temporary WAV file using `wave` module (built-in)
- Or use numpy to convert to array and pass directly to faster-whisper
- Allow user to override sample rate for Whisper (recommend 16000)

### 5. Error Handling

#### Whisper-Specific Errors
1. **Model download failures**
   - Provide clear error message with model URL
   - Suggest manual download location

2. **Out of memory**
   - Catch OOM errors
   - Suggest smaller model (tiny, base instead of large)

3. **Audio file too short**
   - Whisper has minimum audio length
   - Warn if recording < 1 second

4. **API Key issues** (for WHISPER_API)
   - Check for key before recording
   - Clear error messages for invalid/missing keys

### 6. Configuration File Support

Allow Whisper settings in user config:

```python
# ~/.config/nerd-dictation/nerd-dictation.py

# Whisper-specific configuration
WHISPER_MODEL = "base"
WHISPER_LANGUAGE = "en"
WHISPER_TEMPERATURE = 0.2
WHISPER_INITIAL_PROMPT = "Technical dictation with proper punctuation."

def nerd_dictation_process(text):
    # Post-process Whisper output
    return text
```

### 7. Output Format Differences

**VOSK Output:**
- All lowercase
- No punctuation
- JSON format: `{"text": "hello world"}`

**Whisper Output:**
- Proper capitalization
- Includes punctuation
- Plain string: `"Hello world."`

**Implications:**
- Number parsing may need adjustment (Whisper might output "42" instead of "forty two")
- User configs expecting lowercase may break
- `--full-sentence` flag less relevant with Whisper
- `--numbers-as-digits` flag less useful

**Solution:**
- Add flag `--whisper-lowercase` to optionally convert to lowercase
- Detect when number parsing conflicts with Whisper's output
- Document behavioral differences in help text

---

## Implementation Plan

### Phase 1: Foundation (Core Refactoring)
**Goal:** Abstract STT engine interface without breaking anything

**Tasks:**
1. Create STT engine abstraction/protocol
2. Refactor `text_from_vosk_pipe()` to use abstraction
3. Extract shared logic (signal handling, timeout, exit control)
4. Add unit tests for abstraction
5. Verify VOSK still works identically

**Files Changed:**
- `nerd-dictation` (main file)

**Deliverable:** Working code with no new features but cleaner architecture

---

### Phase 2: Whisper Integration (Local)
**Goal:** Add faster-whisper support

**Tasks:**
1. Implement `WhisperEngine` class
2. Add audio buffering to temporary WAV file
3. Integrate faster-whisper library
4. Add command-line arguments
5. Implement model downloading/caching
6. Handle deferred-only output mode
7. Test with various model sizes

**Files Changed:**
- `nerd-dictation` (main file)
- `package/python/setup.py` (add optional dependency)

**New Dependencies:**
```python
install_requires=["vosk"],  # existing
extras_require={
    "whisper": ["faster-whisper>=1.0.0", "numpy"],
}
```

**Deliverable:** Working Whisper transcription with `--stt-engine WHISPER`

---

### Phase 3: Enhanced Features
**Goal:** Add temperature, prompt, and advanced options

**Tasks:**
1. Implement temperature control
2. Implement initial prompt support
3. Add language selection
4. Add compute type selection
5. Implement proper error messages for Whisper-specific issues
6. Add verbose logging for Whisper operations

**Files Changed:**
- `nerd-dictation` (main file)

**Deliverable:** Full feature parity with Whisper capabilities

---

### Phase 4: OpenAI API Support (Optional)
**Goal:** Support cloud-based Whisper API

**Tasks:**
1. Implement `WhisperAPIEngine` class
2. Add API key handling
3. Implement file upload to API
4. Handle API rate limits and errors
5. Add cost warnings (API is paid)

**Files Changed:**
- `nerd-dictation` (main file)

**New Dependencies:**
```python
extras_require={
    "whisper": ["faster-whisper>=1.0.0", "numpy"],
    "whisper-api": ["openai>=1.0.0"],
}
```

**Deliverable:** Cloud-based Whisper option

---

### Phase 5: Documentation & Polish
**Goal:** Complete the feature

**Tasks:**
1. Update README with Whisper installation instructions
2. Create example configurations for Whisper
3. Add troubleshooting guide
4. Update CLAUDE.md with Whisper architecture
5. Add performance comparison documentation
6. Create migration guide for VOSK users

**Files Changed:**
- `readme.rst`
- `CLAUDE.md`
- New: `readme-whisper.rst`
- New: `examples/whisper/nerd-dictation.py`

**Deliverable:** Complete, documented feature

---

## Testing Strategy

### Unit Tests
1. Engine abstraction interface compliance
2. Audio buffering to WAV file
3. Model path resolution
4. Configuration parsing

### Integration Tests
1. End-to-end transcription with tiny model
2. Suspend/resume with Whisper
3. Timeout behavior
4. Cancel during transcription
5. Multiple consecutive recordings

### Manual Tests
1. Various model sizes (tiny, base, small, medium)
2. Different languages
3. Long recordings (>1 minute)
4. Very short recordings (<1 second)
5. Temperature variations
6. Initial prompt effectiveness
7. Memory usage with large models

### Compatibility Tests
1. All existing VOSK tests still pass
2. Existing user configurations still work
3. Command-line scripts unchanged (default VOSK)

---

## Migration & Compatibility

### For Existing Users
- **No changes required** - VOSK remains default
- All existing scripts work unchanged
- Can gradually adopt Whisper per use-case

### For Package Maintainers
- `vosk` remains required dependency
- `faster-whisper` is optional extra: `pip install nerd-dictation[whisper]`
- Document optional dependencies

### Breaking Changes
**None.** This is purely additive.

---

## Performance Considerations

### Model Loading Time
- **VOSK**: 1-3 seconds (small-medium models)
- **Whisper tiny**: ~2 seconds
- **Whisper base**: ~3 seconds
- **Whisper small**: ~5 seconds
- **Whisper medium**: ~10 seconds
- **Whisper large**: ~20 seconds

**Mitigation:** Use suspend/resume for long sessions

### Memory Usage
- **VOSK small**: ~50 MB
- **Whisper tiny**: ~150 MB
- **Whisper base**: ~300 MB
- **Whisper small**: ~600 MB
- **Whisper medium**: ~1.5 GB
- **Whisper large**: ~3 GB

**Recommendation:** Default to `base` model, document memory requirements

### Transcription Latency
- **VOSK**: Real-time (streaming)
- **Whisper**: ~0.5-2x audio duration (depending on model and hardware)

**User Impact:** Brief delay after speaking before text appears

---

## Open Questions

1. **Should we support whisper.cpp as well as faster-whisper?**
   - whisper.cpp has better CPU performance
   - faster-whisper has simpler Python API
   - **Recommendation:** Start with faster-whisper, add whisper.cpp later if requested

2. **Should temperature and prompt be global args or per-recording?**
   - Global: easier CLI, set once per session
   - Per-recording: more flexible but complex
   - **Recommendation:** Global args with user config override

3. **Should we auto-detect when Whisper is better than VOSK?**
   - Could analyze language, context, etc.
   - **Recommendation:** No, leave choice to user

4. **Should progressive mode with Whisper re-transcribe partial audio?**
   - Could simulate progressive typing by re-running on growing buffer
   - Would be very slow and inaccurate
   - **Recommendation:** No, force deferred mode

5. **Should we add VAD (voice activity detection) to improve Whisper performance?**
   - Could use silero-vad to detect speech boundaries
   - Would reduce processing time and improve accuracy
   - **Recommendation:** Future enhancement, not MVP

---

## Success Metrics

1. **Adoption Rate**: % of users who try Whisper within 3 months
2. **Accuracy Improvement**: User-reported quality vs VOSK
3. **Performance**: Latency < 3 seconds for typical 10-second recording with base model
4. **Stability**: No crashes or memory leaks in 100+ consecutive recordings
5. **Compatibility**: Zero breakage of existing VOSK functionality

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Large models cause OOM | High | Medium | Default to small model, clear docs |
| Slow transcription frustrates users | Medium | High | Set expectations, optimize loading |
| API costs surprise users | High | Low | Require explicit opt-in, show warnings |
| Breaking VOSK in refactor | High | Low | Extensive testing, gradual refactoring |
| Single-file size becomes unwieldy | Low | High | Accept as tradeoff, consider split if >3000 lines |

---

## Future Enhancements (Out of Scope)

1. **LLM Post-Processing**: Use GPT-4/Claude to improve Whisper output (maintainer's goal)
2. **Speaker Diarization**: Identify different speakers
3. **Timestamps**: Word-level or segment timestamps
4. **Streaming Whisper**: Use whisper-streaming or similar projects
5. **Custom Model Fine-Tuning**: Support for user-trained models
6. **VAD Integration**: Automatic speech boundary detection
7. **Audio Enhancement**: Noise reduction preprocessing

---

## Appendix A: Code Structure

### Proposed File Organization (within single file)

```python
#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

# ... existing imports and constants ...

# -----------------------------------------------------------------------------
# Speech-To-Text Engine Abstraction
#

class STTEngine:
    """Abstract base for speech-to-text engines."""
    def process(...): ...

class VoskEngine(STTEngine):
    """VOSK implementation (existing code refactored)."""
    ...

class WhisperEngine(STTEngine):
    """Whisper implementation using faster-whisper."""
    ...

# -----------------------------------------------------------------------------
# Text Processing (existing functions)
#

def text_from_stt_engine(...):
    """Main processing loop (refactored from text_from_vosk_pipe)."""
    ...

# ... rest of existing code ...
```

### Estimated Line Count
- Current file: ~1984 lines
- Added for Whisper: ~400-600 lines
- Refactoring impact: ~100 lines moved/changed
- **Total**: ~2400-2700 lines (still manageable single file)

---

## Appendix B: Example Usage

### Basic Whisper Usage
```bash
# Install with Whisper support
pip3 install vosk faster-whisper

# Use Whisper with base model (default)
./nerd-dictation begin --stt-engine WHISPER &
# Speak...
./nerd-dictation end

# Use specific model
./nerd-dictation begin --stt-engine WHISPER --whisper-model small

# With language and prompt
./nerd-dictation begin \
    --stt-engine WHISPER \
    --whisper-language en \
    --whisper-initial-prompt "Technical documentation with proper punctuation." \
    --whisper-temperature 0.0
```

### OpenAI API Usage
```bash
export OPENAI_API_KEY=sk-...
./nerd-dictation begin --stt-engine WHISPER_API
```

### Configuration File
```python
# ~/.config/nerd-dictation/nerd-dictation.py

def nerd_dictation_process(text):
    # Whisper provides capitalization and punctuation
    # Just do any custom replacements
    text = text.replace("nerd dictation", "nerd-dictation")
    return text
```

---

## Appendix C: Dependencies

### Required (existing)
- `vosk` - VOSK speech recognition

### Optional (new)
- `faster-whisper>=1.0.0` - Local Whisper inference
- `numpy` - Array operations for audio
- `openai>=1.0.0` - For WHISPER_API mode (optional)

### System (existing)
- Python 3.6+
- Audio recording tool (parec/sox/pw-cat)
- Input simulation tool (xdotool/ydotool/dotool/wtype)

---

## Approval & Sign-off

This PRD requires review and approval from:
- [ ] Repository maintainer (ideasman42)
- [ ] Technical review completed
- [ ] Community feedback gathered (issue/discussion)
- [ ] Implementation approach agreed

Once approved, development can proceed in phases as outlined above.
