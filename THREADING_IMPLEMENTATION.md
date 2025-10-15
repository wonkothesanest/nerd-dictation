# Whisper Threading Implementation

## Summary

The WhisperEngine has been completely refactored to support non-blocking, threaded transcription with a two-tier silence detection system. This solves the blocking transcription problem where audio could be missed while Whisper was processing.

## Key Changes

### 1. Threading Architecture

**Before:**
- Single-threaded, blocking transcription
- Main loop would freeze during transcription (1-5 seconds)
- Missed audio and silence detection during transcription
- Always one utterance behind during continuous speech

**After:**
- Background worker thread handles transcription
- Main loop continues reading audio and detecting silence
- Queue-based task system with coalescing optimization
- Responsive to continuous speech patterns

### 2. Two-Tier Silence Detection

**Short Pause (--whisper-silence-duration, default: 0.5s)**
- Transcribes **delta** (new audio since last transcription)
- Appends result to output
- Fast feedback for continuous speech

**Long Pause (--whisper-silence-finalize, default: 2.0s)**
- Re-transcribes **entire buffer** from beginning
- Deletes all intermediate outputs
- Replaces with properly formatted result (better punctuation/capitalization)
- Clears buffer for next utterance

### 3. Output Pattern

**User Experience with 3 Utterances:**

```
T=0s:   Speak "sentence one" → pause 0.5s
T=2.5s: Output: "Sentence one"

T=3s:   Speak "sentence two" → pause 0.5s
T=5.5s: Output: "Sentence one Sentence two"

T=6s:   Speak "sentence three" → pause 2.0s
T=8.5s: Output: "Sentence one Sentence two Sentence three"
T=10.5s: [Delete 45 chars] → Output: "Sentence one. Sentence two. Sentence three."
```

Key insight: Intermediate transcriptions are independent (delta), final transcription gets full context.

## Implementation Details

### WhisperEngine Class Changes

**New State Variables:**
```python
self.last_transcribed_index = 0          # Track position for delta transcription
self.short_silence_timer = 0.0           # Timer for intermediate (0.5s)
self.long_silence_timer = 0.0            # Timer for finalization (2.0s)
self.transcription_queue = Queue()       # Task queue
self.worker_thread = Thread(...)         # Background worker
self.pending_result = None               # Completed transcription result
self.intermediate_outputs = []           # Track outputs for final erase
```

**New Methods:**
- `_transcription_worker()` - Background thread that processes queue
- `get_transcription_result()` - Check for completed results, returns (text, is_final, chars_to_delete)
- `shutdown()` - Clean shutdown of worker thread

**Modified Methods:**
- `initialize()` - Now starts worker thread
- `process_audio_chunk()` - Two-tier silence detection, queues transcription tasks
- `supports_progressive()` - Now returns `True` (progressive-like via threading)

### Main Loop Changes

**Added Whisper Result Checking:**
```python
# After processing audio chunk
if isinstance(stt_engine, WhisperEngine):
    whisper_result = stt_engine.get_transcription_result()
    if whisper_result is not None:
        text, is_final, chars_to_delete = whisper_result
        if chars_to_delete > 0:
            # Final: delete and replace
            handle_fn(chars_to_delete, processed_text)
        else:
            # Intermediate: append
            handle_fn(0, processed_text)
```

### Queue Coalescing Optimization

If user speaks faster than transcription speed, the worker intelligently skips obsolete intermediate transcriptions:

```python
# In worker thread
while not transcription_queue.empty():
    next_task = transcription_queue.get_nowait()
    task = next_task  # Skip current, use newer one
```

This prevents wasting CPU on stale audio.

## New CLI Parameter

**--whisper-silence-finalize SECONDS**
- Duration of silence to trigger finalization (default: 2.0)
- Should be longer than `--whisper-silence-duration`
- Controls when buffer is cleared and re-transcribed

## Benefits

1. **No Missed Audio:** Main loop always reading, even during transcription
2. **Responsive:** Quick feedback on short pauses (0.5s)
3. **High Quality:** Final output has full sentence context for better formatting
4. **Efficient:** Queue coalescing prevents wasting CPU on obsolete transcriptions
5. **Natural UX:** Intermediate outputs → polished final output feels intuitive

## Testing

Run the test script:
```bash
./test_whisper_threading.sh
```

Or manually:
```bash
./nerd-dictation begin \
  --stt-engine=WHISPER \
  --whisper-model=tiny \
  --whisper-silence-duration=0.5 \
  --whisper-silence-finalize=2.0 \
  --verbose=1

# Speak 3 sentences with pauses, observe output pattern
```

## Technical Considerations

### Thread Safety
- `threading.Lock` protects shared result variables
- `queue.Queue` is thread-safe by design
- Only worker modifies `pending_result`, main thread only reads

### Graceful Shutdown
- Worker thread is daemon (auto-exits with main process)
- Explicit `shutdown()` sends None to queue to stop worker
- 2-second timeout prevents hanging on exit

### Progressive Mode
- WhisperEngine now reports `supports_progressive() = True`
- Removed the warning about progressive mode not working
- Output handling uses character deletion (like VOSK backspacing)

## Future Enhancements

Possible improvements:
1. GPU support (change `device="cpu"` to `device="cuda"`)
2. Configurable queue size limits
3. Priority queue (finalization tasks jump queue)
4. Audio compression in queue (reduce memory if queue backs up)
5. Parallel transcription (multiple workers, risky but faster)

## Known Limitations

1. Delta transcription lacks context (fixable with overlapping windows)
2. Worker shutdown timeout can cause 2s delay on exit
3. No visual indicator during transcription (could add progress bar)
4. Queue coalescing may skip too aggressively (could be configurable)
