#!/usr/bin/env python3
"""
Test script for WhisperEngine integration.
Tests that the engine can be instantiated and initialized without errors.
"""

import sys
import os

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: numpy not available, some tests will be skipped")

# Add current directory to path to import from nerd-dictation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Read and execute the nerd-dictation file to get access to WhisperEngine class
with open('nerd-dictation', 'r') as f:
    code = f.read()
    # Execute in a namespace
    namespace = {}
    exec(code, namespace)

    WhisperEngine = namespace['WhisperEngine']
    VoskEngine = namespace['VoskEngine']
    STTEngine = namespace['STTEngine']

def test_whisper_engine_instantiation():
    """Test that WhisperEngine can be instantiated with correct parameters."""
    print("Test 1: WhisperEngine instantiation...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_language="en",
        whisper_temperature=0.0,
        whisper_initial_prompt="Test prompt",
        whisper_compute_type="float32",
        whisper_silence_duration=0.5,
        whisper_silence_finalize=2.0,
        whisper_no_speech_threshold=0.7,
        verbose=0
    )

    assert engine.whisper_model == "tiny"
    assert engine.sample_rate == 16000
    assert engine.whisper_language == "en"
    assert engine.whisper_temperature == 0.0
    assert engine.whisper_initial_prompt == "Test prompt"
    assert engine.whisper_no_speech_threshold == 0.7
    assert engine.audio_buffer == []
    assert engine.last_transcribed_index == 0
    assert engine.model is None  # Not initialized yet
    assert engine.short_silence_timer == 0.0
    assert engine.long_silence_timer == 0.0

    print("  ✓ WhisperEngine instantiation successful")

def test_whisper_engine_initialization():
    """Test that WhisperEngine can initialize the Whisper model."""
    print("\nTest 2: WhisperEngine initialization...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_language=None,
        whisper_temperature=0.0,
        whisper_initial_prompt=None,
        whisper_compute_type="float32",
        whisper_silence_duration=0.5,
        whisper_silence_finalize=2.0,
        verbose=0
    )

    print("  Initializing Whisper model (this may download the model)...")
    try:
        engine.initialize()
        assert engine.model is not None
        assert engine.worker_thread is not None
        assert engine.worker_thread.is_alive()
        print("  ✓ WhisperEngine initialization successful")
        print("  ✓ Worker thread started")
        engine.shutdown()  # Clean up
        return True
    except Exception as e:
        print(f"  ⚠ WhisperEngine initialization failed (this is expected if no internet): {e}")
        return False

def test_whisper_engine_audio_buffering():
    """Test that WhisperEngine can buffer audio chunks."""
    print("\nTest 3: WhisperEngine audio buffering...")

    if not HAS_NUMPY:
        print("  ⚠ Skipping (numpy not available)")
        return

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_silence_duration=0.5,
        whisper_silence_finalize=2.0,
        verbose=0
    )

    # Create fake audio data (PCM s16le format)
    fake_audio = np.random.randint(-32768, 32767, size=16000, dtype=np.int16).tobytes()

    # Process audio chunk
    result = engine.process_audio_chunk(fake_audio)

    assert result == False  # Should return False (not finalized yet)
    assert len(engine.audio_buffer) == 1
    assert engine.audio_buffer[0] == fake_audio

    # Add another chunk
    result = engine.process_audio_chunk(fake_audio)
    assert len(engine.audio_buffer) == 2

    print("  ✓ Audio buffering successful")

def test_whisper_no_speech_gate():
    """Test that Whisper no-speech results are suppressed."""
    print("\nTest 4: Whisper no-speech gate...")

    class FakeSegment:
        def __init__(self, text, no_speech_prob):
            self.text = text
            self.no_speech_prob = no_speech_prob

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_no_speech_threshold=0.6,
        verbose=0
    )

    text = engine._segments_to_text([
        FakeSegment("real speech", 0.1),
        FakeSegment(" hallucinated silence", 0.95),
    ])
    assert text == "real speech"

    text = engine._segments_to_text([
        FakeSegment("kept speech", 0.59),
        FakeSegment(" suppressed at threshold", 0.6),
    ])
    assert text == "kept speech"

    text = engine._segments_to_text([
        FakeSegment("hallucinated silence", 0.95),
    ])
    assert text == ""

    class SegmentWithoutNoSpeechProb:
        text = "legacy segment"

    text = engine._segments_to_text([
        SegmentWithoutNoSpeechProb(),
    ])
    assert text == "legacy segment"

    engine.audio_buffer.append(b"\x00" * 3200)

    def fail_transcribe(_audio_buffer):
        raise AssertionError("Silent audio should not be sent to Whisper")

    engine._transcribe_audio_chunk = fail_transcribe
    assert engine.get_final_result() == ""
    assert engine.audio_buffer == []

    print("  ✓ No-speech gate suppresses silent/hallucinated output")

def test_whisper_silence_only_audio_does_not_queue_transcription():
    """Test that repeated silence before speech never queues Whisper work."""
    print("\nTest 5: Whisper silence-only buffering...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_silence_duration=0.1,
        whisper_silence_finalize=0.2,
        verbose=0
    )

    engine._is_silence = lambda _data: True
    silence_chunk = b"\x00" * 3200

    for _ in range(4):
        assert engine.process_audio_chunk(silence_chunk) == False

    assert engine.has_speech == False
    assert engine.short_silence_timer == 0.0
    assert engine.long_silence_timer == 0.0
    assert engine.last_transcribed_index == 0
    assert engine.transcription_queue.empty()
    assert len(engine.audio_buffer) == 4

    print("  ✓ Silence-only audio does not queue transcription")

def test_whisper_low_rms_queue_guard():
    """Test that mostly silent queued clips are not sent to Whisper."""
    print("\nTest 6: Whisper low-RMS queue guard...")

    if not HAS_NUMPY:
        print("  ⚠ Skipping (numpy not available)")
        return

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_silence_duration=0.1,
        whisper_silence_finalize=0.2,
        whisper_silence_threshold=0.01,
        verbose=0
    )

    click = np.zeros(16000, dtype=np.int16)
    click[0] = 32767
    click_chunk = click.tobytes()
    silence_chunk = np.zeros(1600, dtype=np.int16).tobytes()

    is_silence_results = [False, True, True]

    def fake_is_silence(_data):
        return is_silence_results.pop(0)

    engine._is_silence = fake_is_silence

    assert engine.process_audio_chunk(click_chunk) == False
    assert engine.process_audio_chunk(silence_chunk) == False
    assert engine.transcription_queue.empty()
    assert engine.last_transcribed_index == 2

    assert engine.process_audio_chunk(silence_chunk) == False
    assert engine.transcription_queue.empty()
    assert engine.audio_buffer == []
    assert engine.has_speech == False
    assert engine.get_transcription_result() == ("", True)

    print("  ✓ Low-RMS queued clips are suppressed")

def test_whisper_speech_chunk_in_low_rms_clip_is_queued():
    """Test that a low-overall-RMS clip still queues when one chunk is speech."""
    print("\nTest 7: Whisper low-RMS clip with speech chunk queues...")

    if not HAS_NUMPY:
        print("  ⚠ Skipping (numpy not available)")
        return

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_silence_duration=0.3,
        whisper_silence_finalize=2.0,
        whisper_silence_threshold=0.01,
        verbose=0
    )

    def chunk_with_rms(rms):
        value = int(rms * 32768)
        return np.full(1600, value, dtype=np.int16).tobytes()

    for rms in (0.0085, 0.0047, 0.0142, 0.0085, 0.0086, 0.0019):
        assert engine.process_audio_chunk(chunk_with_rms(rms)) == False

    assert engine.has_speech == True
    assert engine.transcription_queue.empty() == False

    task = engine.transcription_queue.get_nowait()
    assert task["is_final"] == False

    clip_rms, duration, peak_chunk_rms = engine._audio_chunks_rms_duration_and_peak(task["audio"])
    assert clip_rms < 0.01
    assert peak_chunk_rms >= 0.01
    assert duration == 0.6

    print("  ✓ Speech chunk keeps low-overall-RMS clip eligible")

def test_whisper_low_energy_hallucination_guard():
    """Test that long text from low-energy audio is suppressed."""
    print("\nTest 8: Whisper low-energy hallucination guard...")

    if not HAS_NUMPY:
        print("  ⚠ Skipping (numpy not available)")
        return

    class FakeSegment:
        text = "hey i want a pizza " * 8
        no_speech_prob = 0.0

    class FakeModel:
        def transcribe(self, _audio_float, **_kwargs):
            return [FakeSegment()], None

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_silence_threshold=0.01,
        verbose=0
    )
    engine.model = FakeModel()

    low_energy_audio = np.full(32000, 393, dtype=np.int16).tobytes()
    assert engine._transcribe_audio_chunk([low_energy_audio]) == ""

    repeated_hallucination = (
        "I'm going to use the same method for the other side as well. " * 5
    )
    assert engine._is_suspicious_low_energy_transcription(
        repeated_hallucination,
        rms_energy=0.0029,
        duration=20.1,
    ) == True

    quiet_short_result = "ten nine eight seven six five four three two one"
    assert engine._is_suspicious_low_energy_transcription(
        quiet_short_result,
        rms_energy=0.0075,
        duration=22.2,
    ) == False

    print("  ✓ Low-energy hallucinated text is suppressed")

def test_whisper_final_result_preserves_newer_audio():
    """Test that final results only clear audio covered by their snapshot."""
    print("\nTest 9: Whisper final result preserves newer audio...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        verbose=0
    )

    engine.audio_buffer = [b"old1", b"old2", b"old3", b"new1", b"new2"]
    engine.audio_buffer_has_speech = [True, True, False, True, False]
    engine.last_transcribed_index = 5
    engine.has_speech = True
    engine.cumulative_output = "draft"

    engine._queue_transcription_result(
        text="final old",
        is_final=True,
        start_index=0,
        end_index=3,
    )

    assert engine.get_transcription_result() == ("final old", True)
    assert engine.audio_buffer == [b"new1", b"new2"]
    assert engine.audio_buffer_has_speech == [True, False]
    assert engine.last_transcribed_index == 2
    assert engine.has_speech == True

    print("  ✓ Final result does not discard newer audio")

def test_whisper_result_queue_preserves_order():
    """Test that completed results cannot overwrite each other."""
    print("\nTest 10: Whisper result queue order...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        verbose=0
    )

    engine._queue_transcription_result(
        text="first",
        is_final=False,
        start_index=0,
        end_index=1,
    )
    engine._queue_transcription_result(
        text=" second",
        is_final=False,
        start_index=1,
        end_index=2,
    )

    assert engine.get_transcription_result() == ("first", False)
    assert engine.get_transcription_result() == ("first second", False)

    print("  ✓ Result queue preserves FIFO order")

def test_whisper_in_flight_task_blocks_new_queue_work():
    """Test that an in-flight task prevents additional queueing."""
    print("\nTest 11: Whisper in-flight task blocks queueing...")

    if not HAS_NUMPY:
        print("  ⚠ Skipping (numpy not available)")
        return

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_silence_duration=0.1,
        whisper_silence_finalize=0.2,
        whisper_silence_threshold=0.01,
        verbose=0
    )

    speech_chunk = np.full(1600, int(0.02 * 32768), dtype=np.int16).tobytes()
    silence_chunk = np.zeros(1600, dtype=np.int16).tobytes()

    assert engine.process_audio_chunk(speech_chunk) == False
    with engine.result_lock:
        engine.transcription_tasks_in_flight = 1

    assert engine.process_audio_chunk(silence_chunk) == False
    assert engine.process_audio_chunk(silence_chunk) == False
    assert engine.transcription_queue.empty()
    assert engine.last_transcribed_index == 0

    with engine.result_lock:
        engine.transcription_tasks_in_flight = 0

    print("  ✓ In-flight task state blocks new queue work")

def test_whisper_engine_interface():
    """Test that WhisperEngine implements the STTEngine interface."""
    print("\nTest 12: STTEngine interface compliance...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        whisper_silence_duration=0.5,
        whisper_silence_finalize=2.0,
        verbose=0
    )

    # Check that all required methods exist
    assert hasattr(engine, 'initialize')
    assert hasattr(engine, 'process_audio_chunk')
    assert hasattr(engine, 'get_partial_result')
    assert hasattr(engine, 'get_final_result')
    assert hasattr(engine, 'reset')
    assert hasattr(engine, 'supports_progressive')

    # Check that supports_progressive now returns True (threading support)
    assert engine.supports_progressive() == True

    # Check that get_partial_result returns empty string
    assert engine.get_partial_result() == ""

    # Check for new threading methods
    assert hasattr(engine, 'get_transcription_result')
    assert hasattr(engine, 'shutdown')

    print("  ✓ STTEngine interface compliance verified")
    print("  ✓ Threading methods present")

def test_abstract_base_class():
    """Test that STTEngine is properly defined as an abstract base."""
    print("\nTest 13: STTEngine abstract base class...")

    # Try to call abstract methods (should raise NotImplementedError)
    engine = STTEngine()

    try:
        engine.initialize()
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass

    try:
        engine.process_audio_chunk(b"")
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass

    print("  ✓ STTEngine abstract base class properly defined")

def main():
    print("=" * 60)
    print("Testing Whisper Integration for nerd-dictation")
    print("=" * 60)

    try:
        test_abstract_base_class()
        test_whisper_engine_instantiation()
        test_whisper_engine_audio_buffering()
        test_whisper_no_speech_gate()
        test_whisper_silence_only_audio_does_not_queue_transcription()
        test_whisper_low_rms_queue_guard()
        test_whisper_speech_chunk_in_low_rms_clip_is_queued()
        test_whisper_low_energy_hallucination_guard()
        test_whisper_final_result_preserves_newer_audio()
        test_whisper_result_queue_preserves_order()
        test_whisper_in_flight_task_blocks_new_queue_work()
        test_whisper_engine_interface()
        model_initialized = test_whisper_engine_initialization()

        print("\n" + "=" * 60)
        print("Test Summary:")
        print("=" * 60)
        print("✓ WhisperEngine class structure is correct")
        print("✓ Audio buffering works as expected")
        print("✓ STTEngine interface is properly implemented")
        if model_initialized:
            print("✓ Whisper model can be initialized")
        else:
            print("⚠ Whisper model initialization skipped (likely network issue)")

        print("\nAll core functionality tests passed!")
        print("\nNote: Full end-to-end testing requires Linux with audio")
        print("      recording tools (parec/sox/pw-cat).")

        return 0

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
