"""Tests for weak_point_service extraction logic."""

from __future__ import annotations

import pytest

from app.services.weak_point_service import (
    WER_THRESHOLD,
    MISSING_WORDS_THRESHOLD,
    extract_weak_points,
)


class TestWERThreshold:
    """WER-based weak point extraction."""

    def test_wer_above_threshold(self, sample_unique_session_id):
        """WER > 0.3 → weak point."""
        phrase = f"wer-test-above-{sample_unique_session_id}"
        utter = {"target_text": phrase, "transcript": "x", "wer": 0.5, "feedback_json": None}
        result = extract_weak_points([utter], sample_unique_session_id)
        assert len(result) >= 1

    def test_wer_at_threshold(self, sample_unique_session_id):
        """WER == threshold → NOT a weak point (strictly greater required)."""
        utter = {"target_text": "hello", "transcript": "hello", "wer": WER_THRESHOLD, "feedback_json": None}
        result = extract_weak_points([utter], sample_unique_session_id)
        assert len(result) == 0

    def test_wer_below_threshold(self, sample_unique_session_id):
        """WER < threshold → NOT a weak point."""
        utter = {"target_text": "hello", "transcript": "hello", "wer": 0.1, "feedback_json": None}
        result = extract_weak_points([utter], sample_unique_session_id)
        assert len(result) == 0


class TestMissingWordsThreshold:
    """Missing words-based weak point extraction."""

    def test_missing_words_below_threshold(self, sample_unique_session_id):
        """missing_words < 2 → NOT a weak point."""
        utter = {"target_text": "hello", "transcript": "hello", "wer": None, "feedback_json": '{"missing_words": ["w1"]}'}
        result = extract_weak_points([utter], sample_unique_session_id)
        assert len(result) == 0

    def test_missing_words_at_threshold(self, sample_unique_session_id):
        """missing_words == 2 → weak point."""
        phrase = f"mw-test-at-{sample_unique_session_id}"
        utter = {
            "target_text": phrase,
            "transcript": "x",
            "wer": None,
            "feedback_json": '{"missing_words": ["w1", "w2"]}',
        }
        result = extract_weak_points([utter], sample_unique_session_id)
        assert len(result) >= 1

    def test_missing_words_above_threshold(self, sample_unique_session_id):
        """missing_words > 2 → weak point."""
        phrase = f"mw-test-above-{sample_unique_session_id}"
        utter = {
            "target_text": phrase,
            "transcript": "x",
            "wer": None,
            "feedback_json": '{"missing_words": ["w1", "w2", "w3"]}',
        }
        result = extract_weak_points([utter], sample_unique_session_id)
        assert len(result) >= 1

    def test_invalid_feedback_json(self, sample_unique_session_id):
        """Broken JSON in feedback_json → gracefully skipped."""
        utter = {"target_text": "hello", "transcript": "hello", "wer": None, "feedback_json": "not json"}
        result = extract_weak_points([utter], sample_unique_session_id)
        assert result == []


class TestEdgeCases:
    """Edge case handling."""

    def test_no_target_text(self, sample_unique_session_id):
        """No target_text → skipped."""
        utter = {"target_text": "", "transcript": "hello", "wer": 0.5, "feedback_json": None}
        result = extract_weak_points([utter], sample_unique_session_id)
        assert len(result) == 0

    def test_deduplication(self, sample_unique_session_id):
        """Same normalised phrase → deduplicated."""
        phrase = f"dedup-test-{sample_unique_session_id}"
        utter1 = {"target_text": phrase, "transcript": "hello", "wer": 0.5, "feedback_json": None}
        utter2 = {"target_text": phrase, "transcript": "hello", "wer": 0.6, "feedback_json": None}
        result = extract_weak_points([utter1, utter2], sample_unique_session_id)
        phrases = [r["phrase"] for r in result]
        assert len(phrases) == len(set(phrases))

    def test_issue_type_missing_preferred_over_misrecognized(self, sample_unique_session_id):
        """Both WER and missing_words → issue_type is 'missing'."""
        phrase = f"pref-test-{sample_unique_session_id}"
        utter = {
            "target_text": phrase,
            "transcript": "x",
            "wer": 0.5,
            "feedback_json": '{"missing_words": ["w1", "w2"]}',
        }
        result = extract_weak_points([utter], sample_unique_session_id)
        assert all(r["issue_type"] == "missing" for r in result)


# --- Fixtures ---

_unique_id_counter = [0]


@pytest.fixture
def sample_unique_session_id():
    """Return a unique session ID so each test creates unique data."""
    _unique_id_counter[0] += 1
    return f"unique-sess-{_unique_id_counter[0]}"
