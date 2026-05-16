"""Edge-case tests for pronunciation evaluation (BEE-45 acceptance criteria)."""

import pytest
from pronunciation import evaluate_pronunciation, PronunciationResult
from pronunciation.eval import normalise, split_words


class TestEdgeCases:
    def test_empty_target(self) -> None:
        result = evaluate_pronunciation("", "Hello")
        assert result.target_word_count == 0
        assert result.wer == 1.0
        assert not result.is_valid

    def test_empty_transcript(self) -> None:
        result = evaluate_pronunciation("Hello", "")
        assert result.wer == 1.0
        assert result.missing_words == ["hello"]
        assert result.extra_words == []
        assert result.transcript_word_count == 0
        assert not result.is_valid

    def test_both_blank(self) -> None:
        result = evaluate_pronunciation("", "")
        assert result.wer == 1.0
        assert result.target_word_count == 0
        assert result.transcript_word_count == 0
        assert not result.is_valid

    def test_full_mismatch(self) -> None:
        result = evaluate_pronunciation("Hello", "Goodbye")
        assert result.wer == 1.0
        assert "hello" in result.missing_words
        assert "goodbye" in result.extra_words

    def test_all_missing(self) -> None:
        target = "One two three four"
        result = evaluate_pronunciation(target, "One two")
        assert result.wer > 0.0
        assert "three" in result.missing_words
        assert "four" in result.missing_words
        assert len(result.missing_words) == 2
        assert result.extra_words == []


class TestSentenceMode:
    def test_sentence_mode_skips_free(self) -> None:
        """sentence_mode=True + no sentence-ending punctuation → is_valid=False."""
        result = evaluate_pronunciation("what is your name", "what is", sentence_mode=True)
        assert not result.is_valid
        assert result.wer == 1.0

    def test_sentence_mode_passes(self):
        """sentence_mode=True + sentence-ending punctuation → is_valid=True."""
        result = evaluate_pronunciation("What is your name?", "What is", sentence_mode=True)
        assert result.is_valid
        assert result.wer > 0.0
