"""Tests for pronunciation evaluation (BEE-45 acceptance criteria).

Run with:  python -m pytest tests/ -v
"""

import pytest
from pronunciation import normalise, split_words, evaluate_pronunciation, PronunciationResult


def strip_none(result: PronunciationResult) -> dict:
    """Serialise helper (pytest does not call .model_dump on dataclasses)."""
    return {
        "wer": result.wer,
        "missing_words": result.missing_words,
        "extra_words": result.extra_words,
        "target_word_count": result.target_word_count,
        "transcript_word_count": result.transcript_word_count,
        "accuracy": result.accuracy,
        "is_valid": result.is_valid,
    }


# -------------------- normalisation --------------------

class TestNormalise:
    """Normalisation must ignore case and punctuation for MVP."""

    @pytest.mark.parametrize(
        "input,expected",
        [
            ("", ""),
            ("Hello world.", "hello world"),
            ("WHAT?!?!  about  that?", "what about that"),
            ("It's a test.", "it s a test"),
            ("  spaces   everywhere  ", "spaces everywhere"),
        ],
    )
    def test_normalise(self, input: str, expected: str) -> None:
        assert normalise(input) == expected