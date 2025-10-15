#!/usr/bin/env bash
# Test script for threaded Whisper implementation

echo "Testing Whisper with threading..."
echo ""
echo "This will test:"
echo "1. Short pause (0.5s) - intermediate transcription"
echo "2. Long pause (2.0s) - final re-transcription"
echo ""
echo "Instructions:"
echo "1. Speak a sentence, then pause for 0.5s"
echo "2. Speak another sentence, then pause for 0.5s"
echo "3. Speak a third sentence, then pause for 2.0s"
echo ""
echo "Expected output:"
echo "- First sentence appears"
echo "- Second sentence appends"
echo "- Third sentence appends"
echo "- All text is erased and replaced with properly formatted version"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Run with verbose output and tiny model for speed
./nerd-dictation begin \
  --stt-engine=WHISPER \
  --whisper-model=tiny \
  --whisper-silence-duration=0.5 \
  --whisper-silence-finalize=2.0 \
  --output=STDOUT \
  --verbose=1 \
  --timeout=10.0
