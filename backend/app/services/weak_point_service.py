"""Weak-point extraction service.

Given utterances from a session, scans each ``PronunciationResult``
(computed at session creation time) and inserts a ``WeakPoint`` row for
every phrase whose WER exceeds the configured threshold or has too many
missing words.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.repository import upsert_weak_point
from app.pronunciation.eval import normalise

# -------
# Thresholds (confirmed in the issue comment history)
# -------

WER_THRESHOLD = 0.3
"""WER above which an utterance is considered a weak point."""

MISSING_WORDS_THRESHOLD = 2
"""Number of missing words above which an utterance is a weak point."""

# -------
# Data model
# -------


@dataclass
class WeakPointCandidate:
    """An utterance that qualifies as a weak point."""

    phrase: str          # target_text or the core phrase
    issue_type: str      # missing | misrecognized
    wer: float
    session_id: str


# -------
# Public helpers
# -------


def extract_weak_points(
    utterances: List[Dict],
    session_id: str,
) -> List[Dict]:
    """Scan *utterances* and persist weak points.

    Returns the list of persisted weak point dicts.
    """
    persisted: List[Dict] = []
    seen: set = set()

    for utter in utterances:
        wer = utter.get("wer")
        feedback = utter.get("feedback_json")
        target = utter.get("target_text") or ""
        transcript = utter.get("transcript") or ""

        if not target:
            continue

        missing_count = 0
        issue_type: str | None = None

        # --- WER threshold ---
        if wer is not None and wer > WER_THRESHOLD:
            issue_type = "misrecognized"

        # --- missing-words threshold ---
        if isinstance(feedback, str):
            import json
            try:
                fb = json.loads(feedback)
                missing_count = len(fb.get("missing_words", []))
            except (json.JSONDecodeError, TypeError):
                pass

        if missing_count >= MISSING_WORDS_THRESHOLD:
            issue_type = "missing"

        # Only one issue_type; prefer "missing" (more informative)
        if issue_type is None:
            continue

        # Normalise the phrase for deduplication
        phrase = normalise(target)
        if phrase in seen:
            continue
        seen.add(phrase)

        persisted.append(
            upsert_weak_point(
                phrase=phrase,
                session_id=session_id,
                issue_type=issue_type,
                last_seen_at=datetime.now(timezone.utc),
            )
        )

    return persisted
