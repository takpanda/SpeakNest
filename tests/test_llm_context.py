"""LLM feedback context builder tests (BEE-45 acceptance criteria)."""

import pytest
from pronunciation import evaluate_pronunciation, build_llm_feedback_context, build_llm_feedback_context_dict


class TestLlmContext:
    def test_build_llm_feedback_context(self):
        result = evaluate_pronunciation("Hello world", "Hello")
        ctx = build_llm_feedback_context("Hello world", result)
        assert "wer:" in ctx
        assert "missing_words:" in ctx
        assert "hello" not in ctx  # missing should be the word "world"
        assert "world" in ctx

    def test_build_llm_feedback_context_no_missing(self):
        result = evaluate_pronunciation("Hello world", "Hello world")
        ctx = build_llm_feedback_context("Hello world", result)
        assert "missing_words:" not in ctx
        assert "extra_words:" not in ctx
        assert "wer: 0." in ctx

    def test_build_llm_feedback_context_dict(self):
        result = evaluate_pronunciation("Hello world", "Hello")
        ctx_dict = build_llm_feedback_context_dict("Hello world", result)
        assert ctx_dict["wer"] > 0.0
        assert "world" in ctx_dict["missing_words"]
        assert isinstance(ctx_dict["accuracy"], (int, float))
