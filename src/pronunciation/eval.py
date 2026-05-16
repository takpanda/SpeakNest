"""Pronunciation evaluation module.

Compares a target sentence with an auto-transcribed transcript and returns
simple pronunciation feedback for the MVP scope:
  - Word Error Rate (WER)
  - missing_words (target words that appear to be mispronounced or omitted)
  - extra_words (words in the transcript that do not appear in the target)

MVP scope (BEE-45) intentionally avoids:
  - phoneme-level evaluation
  - forced alignment
  - pitch/intonation/ silence analysis
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PronunciationResult:
    """Simple pronunciation evaluation payload."""

    wer: float
    """Word Error Rate in range [0.0, 1.0], or 1.0 when transcript is empty."""

    missing_words: List[str]
    """Words present in the target but missing (not matched) in the transcript."""

    extra_words: List[str]
    """Words present in the transcript but not in the target."""

    target_word_count: int
    """Number of tokens in the normalised target sentence."""

    transcript_word_count: int
    """Number of tokens in the normalised transcript."""

    # Helper fields consumed by the LLM-annotation prompt builder
    accuracy: float = field(init=False)

    def __post_init__(self) -> None:
        denom = max(self.target_word_count, 1)
        self.accuracy = 1.0 - self.wer  # intentionally not clamped; let caller handle

    @property
    def is_valid(self) -> bool:
        """True when both target and transcript contain at least one word."""
        return self.target_word_count > 0 and self.transcript_word_count > 0


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_SENTENCE_SPLIT = re.compile(r"\s+")
_WORD_TOKENISE = re.compile(r"[']+|\w+(?:['][\w]+)*")
_PUNCT_STRIP = re.compile(rf"[{re.escape(string.punctuation)}]")


def normalise(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation, trim.

    Designed so that differences in case and punctuation do not trigger
    excessive WER penalties in the MVP.
    """
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Strip punctuation (keep apostrophes inside words)
    text = _PUNCT_STRIP.sub(" ", text)
    # Collapse whitespace
    text = _SENTENCE_SPLIT.sub(" ", text)
    # Trim
    return text.strip()


def split_words(text: str) -> List[str]:
    """Split *text* into lowercase word tokens (post-normalisation)."""
    if not text:
        return []
    return _WORD_TOKENISE.findall(normalise(text))


def is_sentence(text: str) -> bool:
    """Return True when *text* contains an explicit sentence-ending punctuation (' . ! ? ')."""
    return bool(re.search(r"[.!?]", text))


# ---------------------------------------------------------------------------
# Core evaluation logic
# ---------------------------------------------------------------------------


def evaluate_pronunciation(
    target_sentence: str,
    transcript: str,
    *,
    sentence_mode: bool = False,
) -> PronunciationResult:
    """Evaluate pronunciation similarity between *target_sentence* and *transcript*.

    Parameters
    ----------
    target_sentence : str
        The reference text the learner was asked to read.
    transcript : str
        The Whisper / STT transcription of the learner's utterance.
    sentence_mode : bool, default ``False``
        When True, evaluate the target only if it ends with a sentence-ending
        punctuation mark (``.`` ``!`` ``?``).  This lets callers gate the
        evaluation to sentence-level practice and skip free-conversation
        fallback.

    Returns
    -------
    PronunciationResult

    Edge cases
    ----------
    * target is blank →WER = 1.0, missing = [], extra = []
    * transcript is blank →WER = 1.0, missing = all target words, extra = []
    * both identical (after normalisation) →WER = 0.0
    - target has fewer words than transcript → all missing_words are empty
    """

    # ---- guard: no-target → return empty / invalid result ----
    if not target_sentence or not normalise(target_sentence):
        return PronunciationResult(
            wer=1.0,
            missing_words=[],
            extra_words=[],
            target_word_count=0,
            transcript_word_count=0,
        )

    # ---- guard: sentence_mode gate (MVP note: free conversation = skip) ----
    if sentence_mode and not is_sentence(target_sentence):
        return PronunciationResult(
            wer=1.0,
            missing_words=[],
            extra_words=[],
            target_word_count=0,
            transcript_word_count=0,
        )

    target_words = split_words(target_sentence)
    transcript_words = split_words(transcript)

    target_count = len(target_words)
    transcript_count = len(transcript_words)

    # ---- guard: both blank after normalisation ----
    if target_count == 0 and transcript_count == 0:
        return PronunciationResult(
            wer=1.0,
            missing_words=[],
            extra_words=[],
            target_word_count=0,
            transcript_word_count=0,
        )

    # ---- guard: transcript is empty → everything is missing ----
    if transcript_count == 0:
        return PronunciationResult(
            wer=1.0,
            missing_words=list(target_words),
            extra_words=[],
            target_word_count=target_count,
            transcript_word_count=0,
        )

    # ---- WER via minimal edit distance (Levenshtein) using word-level ----
    # For MVP we use a simple DP approach (no external dependency).
    wer, missing, extra = _wer_with_diff(target_words, transcript_words)

    return PronunciationResult(
        wer=wer,
        missing_words=missing,
        extra_words=extra,
        target_word_count=target_count,
        transcript_word_count=transcript_count,
    )


# ---------------------------------------------------------------------------
# Edit-distance based WER with diff extraction
# ---------------------------------------------------------------------------


def _wer_with_diff(
    target: List[str], transcript: List[str]
):
    """Compute WER and extract missing / extra words.

    Uses a standard Levenshtein DP.
    Returns (wer, missing_words, extra_words).
    """
    n = len(target)
    m = len(transcript)
    if n == 0 or m == 0:
        return (1.0, list(target), list(transcript))

    # DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if target[i - 1] == transcript[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    wer = dp[n][m] / max(n, m)

    # Back-track to extract substitutions / deletions / insertions
    missing: List[str] = []
    extra: List[str] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            if target[i - 1] == transcript[j - 1]:
                # match: advance both
                i -= 1
                j -= 1
            elif dp[i][j] == dp[i - 1][j - 1] + 1:
                # substitution (cost=1 because words differ)
                missing.append(target[i - 1])
                extra.append(transcript[j - 1])
                i -= 1
                j -= 1
            elif dp[i][j] == dp[i - 1][j] + 1:
                # deletion (word in target, absent from transcript)
                missing.append(target[i - 1])
                i -= 1
            else:
                # insertion (word in transcript, absent from target)
                extra.append(transcript[j - 1])
                j -= 1
        else:
            # i > 0, j == 0: remaining target words are all missing
            missing.append(target[i - 1])
            i -= 1

    return wer, missing, extra


# ---------------------------------------------------------------------------
# LLM prompt helper
# ---------------------------------------------------------------------------


def build_llm_feedback_context(
    target_sentence: str,
    result: PronunciationResult,
) -> str:
    """Return a short, structured text block for the LLM annotation prompt.

    This is *not* the prompt itself — it is the structured evaluation data
    that the LLM needs to produce human-readable feedback.
    """
    lines = [
        f"- target: `{target_sentence}`",
        f"- pronunciation_wer: {result.wer:.4f}",
        f"- accuracy: {result.accuracy:.4f}",
        f"- target_word_count: {result.target_word_count}",
        f"- transcript_word_count: {result.transcript_word_count}",
    ]
    if result.missing_words:
        lines.insert(-1, f"- missing_words: {result.missing_words}")
    if result.extra_words:
        lines.append(f"- extra_words: {result.extra_words}")
    return "\n".join(lines)


def build_llm_feedback_context_dict(
    target_sentence: str,
    result: PronunciationResult,
) -> dict:
    """Same as :func:`build_llm_feedback_context` but as a Python dict."""
    ctx: dict = {
        "target": target_sentence,
        "wer": round(result.wer, 4),
        "accuracy": round(result.accuracy, 4),
        "target_word_count": result.target_word_count,
        "transcript_word_count": result.transcript_word_count,
    }
    if result.missing_words:
        ctx["missing_words"] = result.missing_words
    if result.extra_words:
        ctx["extra_words"] = result.extra_words
    return ctx
