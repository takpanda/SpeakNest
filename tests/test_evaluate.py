"""Core evaluation tests for pronunciation evaluation (BEE-45 acceptance criteria)."""

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
    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("", ""),
            ("Hello world.", "hello world"),
            ("WHAT?!?!  about  that?", "what about that"),
            ("It's a test.", "it s a test"),
            ("  spaces   everywhere  ", "spaces everywhere"),
        ],
    )
    def test_normalise(self, input_str: str, expected: str) -> None:
        assert normalise(input_str) == expected


class TestSplitWords:
    def test_simple(self) -> None:
        assert split_words("Hello World") == ["hello", "world"]


# -------------------- evaluation (normal / happy path) --------------------

class TestEvaluate:
    def test_perfect_match(self) -> None:
        target = "Hello world."
        result = evaluate_pronunciation(target, "Hello world")
        assert result.wer == 0.0
        assert result.missing_words == []
        assert result.extra_words == []
        assert result.target_word_count == 2
        assert result.transcript_word_count == 2
        assert result.is_valid

    def test_case_insensitive(self) -> None:
        """Case differences should not increase WER."""
        result = evaluate_pronunciation("HELLO WORLD", "hello world")
        assert result.wer == 0.0

    def test_one_word_missing(self) -> None:
        target = "What is your name"
        result = evaluate_pronunciation(target, "What is")
        assert result.wer > 0.0
        assert "name" in result.missing_words
        assert "your" in result.missing_words
        assert len(result.missing_words) == 2

    def test_extra_word(self) -> None:
        """Extra transcript words appear in extra_words."""
        result = evaluate_pronunciation("Hello", "Hello world")
        assert "world" in result.extra_words
        assert result.wer > 0.0

    class TestPunctuation:
        def test_punctuation_diff_no_effect(self):
            """MVP: sentence-level punctuation on target must not cause penalty."""
            result = evaluate_pronunciation("What is your name?", "What is your name")
            assert result.wer == 0.0

        def test_multiple_punct_marks(self):
            """Different punctuation should not affect WER."""
            r1 = evaluate_pronunciation("Hello!", "Hello")
            r2 = evaluate_pronunciation("Hello?", "Hello")
            r3 = evaluate_pronunciation("Hello.", "Hello")
            assert r1.wer == r2.wer == r3.wer
