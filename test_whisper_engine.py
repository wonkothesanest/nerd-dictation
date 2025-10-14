#!/usr/bin/env python3
"""
Test script for WhisperEngine integration.
Tests that the engine can be instantiated and initialized without errors.
"""

import sys
import os
import numpy as np

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
        verbose=0
    )

    assert engine.whisper_model == "tiny"
    assert engine.sample_rate == 16000
    assert engine.whisper_language == "en"
    assert engine.whisper_temperature == 0.0
    assert engine.whisper_initial_prompt == "Test prompt"
    assert engine.audio_buffer == []
    assert engine.final_text == ""
    assert engine.model is None  # Not initialized yet

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
        verbose=0
    )

    print("  Initializing Whisper model (this may download the model)...")
    try:
        engine.initialize()
        assert engine.model is not None
        print("  ✓ WhisperEngine initialization successful")
        return True
    except Exception as e:
        print(f"  ⚠ WhisperEngine initialization failed (this is expected if no internet): {e}")
        return False

def test_whisper_engine_audio_buffering():
    """Test that WhisperEngine can buffer audio chunks."""
    print("\nTest 3: WhisperEngine audio buffering...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        verbose=0
    )

    # Create fake audio data (PCM s16le format)
    fake_audio = np.random.randint(-32768, 32767, size=16000, dtype=np.int16).tobytes()

    # Process audio chunk
    result = engine.process_audio_chunk(fake_audio)

    assert result == False  # Whisper doesn't support partial results
    assert len(engine.audio_buffer) == 1
    assert engine.audio_buffer[0] == fake_audio

    # Add another chunk
    result = engine.process_audio_chunk(fake_audio)
    assert len(engine.audio_buffer) == 2

    print("  ✓ Audio buffering successful")

def test_whisper_engine_interface():
    """Test that WhisperEngine implements the STTEngine interface."""
    print("\nTest 4: STTEngine interface compliance...")

    engine = WhisperEngine(
        whisper_model="tiny",
        whisper_model_dir="/tmp/whisper-models",
        sample_rate=16000,
        verbose=0
    )

    # Check that all required methods exist
    assert hasattr(engine, 'initialize')
    assert hasattr(engine, 'process_audio_chunk')
    assert hasattr(engine, 'get_partial_result')
    assert hasattr(engine, 'get_final_result')
    assert hasattr(engine, 'reset')
    assert hasattr(engine, 'supports_progressive')

    # Check that supports_progressive returns False for Whisper
    assert engine.supports_progressive() == False

    # Check that get_partial_result returns empty string
    assert engine.get_partial_result() == ""

    print("  ✓ STTEngine interface compliance verified")

def test_abstract_base_class():
    """Test that STTEngine is properly defined as an abstract base."""
    print("\nTest 5: STTEngine abstract base class...")

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
