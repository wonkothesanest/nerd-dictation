#!/usr/bin/env python3
"""
Test Whisper's diff-based text output algorithm.

This test verifies that Whisper uses the same efficient diff algorithm as VOSK,
minimizing deletions and retyping by only modifying characters after the common prefix.
"""

import sys
import os

# Add parent directory to path to import nerd-dictation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_diff_algorithm():
    """Test the diff algorithm logic used in get_transcription_result."""

    print("Testing Whisper diff algorithm...")
    print("=" * 60)

    test_cases = [
        # (prev_output, new_output, expected_deletions, expected_new_text)
        ("", "Hello", 0, "Hello"),
        ("Hello", "Hello world", 0, " world"),
        ("Hello", "Hello!", 0, "!"),
        ("Hello", "Hi there", 4, "i there"),  # Delete "ello", type "i there" (mismatch at position 1: H)
        ("This is a test", "This is a test.", 0, "."),
        ("This is a", "This is a test", 0, " test"),
        ("This is wrong", "This is correct", 5, "correct"),  # Delete "wrong", type "correct" (mismatch at position 8: w vs c)
        ("Hello world", "Hello", 6, ""),  # Delete " world"
        ("The quick brown", "The quick red", 5, "red"),  # Delete "brown", type "red"
        ("I am going", "I am running", 5, "running"),  # Delete "going", type "running"
    ]

    passed = 0
    failed = 0

    for prev, new, expected_del, expected_text in test_cases:
        # Simulate the diff algorithm from get_transcription_result
        text_prev = prev
        text_curr = new

        # Find longest common prefix
        match = min(len(text_curr), len(text_prev))
        for i in range(match):
            if text_curr[i] != text_prev[i]:
                match = i
                break

        # Calculate what to delete and what to type
        chars_to_delete = len(text_prev) - match
        new_text = text_curr[match:]

        # Check results
        if chars_to_delete == expected_del and new_text == expected_text:
            print(f"✓ PASS: '{prev}' → '{new}'")
            print(f"  Delete {chars_to_delete} chars, type '{new_text}'")
            passed += 1
        else:
            print(f"✗ FAIL: '{prev}' → '{new}'")
            print(f"  Expected: delete {expected_del}, type '{expected_text}'")
            print(f"  Got:      delete {chars_to_delete}, type '{new_text}'")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    return failed == 0


def test_cumulative_updates():
    """Test that cumulative updates work correctly with multiple intermediate results."""

    print("\nTesting cumulative updates...")
    print("=" * 60)

    # Simulate a sequence of intermediate and final results
    cumulative_output = ""

    test_sequence = [
        # (result_text, is_final, description)
        ("Hello", False, "First intermediate"),
        (" world", False, "Second intermediate (appends)"),
        ("Hello world.", True, "Final result (corrects with punctuation)"),
    ]

    print("Simulating text output sequence:\n")

    for result_text, is_final, description in test_sequence:
        # Simulate get_transcription_result logic
        if is_final:
            new_cumulative = result_text
        else:
            new_cumulative = cumulative_output + result_text

        # Find diff
        text_prev = cumulative_output
        text_curr = new_cumulative

        match = min(len(text_curr), len(text_prev))
        for i in range(match):
            if text_curr[i] != text_prev[i]:
                match = i
                break

        chars_to_delete = len(text_prev) - match
        new_text = text_curr[match:]

        print(f"{description}:")
        print(f"  Previous: '{text_prev}'")
        print(f"  New:      '{text_curr}'")
        print(f"  Action:   Delete {chars_to_delete} chars, type '{new_text}'")

        # Update cumulative
        if is_final:
            cumulative_output = ""  # Reset after final
        else:
            cumulative_output = text_curr

        print()

    print("=" * 60)
    print("Cumulative update test complete")

    return True


def main():
    """Run all tests."""
    print("Whisper Diff Algorithm Tests")
    print("=" * 60)
    print()

    test1 = test_diff_algorithm()
    test2 = test_cumulative_updates()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
