"""Learning-history and review API endpoints.

GET /history/sessions          – sessions list (page-paginated, descending)
GET /history/sessions/{id}    – session detail with utterances
GET /history/weak-points      – weak phrase list (count descending)
GET /history/review/next      – next review problem
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from app.db.repository import (
    get_session,
    list_sessions,
    list_utterances,
    list_weak_points,
    pick_next_review,
)

router = APIRouter(prefix="/history", tags=["history"])

#
# Request / response models
#


class SessionDetailResponse(BaseModel):
    session: dict
    utterances: List[dict]


class WeakPointItem(BaseModel):
    id: str
    phrase: str
    issue_type: Optional[str] = None
    count: int
    last_seen_at: Optional[str] = None


class ReviewProblemResponse(BaseModel):
    """Next review problem (target phrase + metadata)."""
    weak_point: WeakPointItem


class SessionListItem(BaseModel):
    id: str
    mode: str
    scenario: Optional[str] = None
    level: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    avg_score: Optional[float] = None


class SessionsListResponse(BaseModel):
    sessions: List[SessionListItem]
    total: int


#
# Endpoints
#


@router.get(
    "/sessions",
    response_model=SessionsListResponse,
    summary="List learning sessions",
)
async def get_sessions(
    mode: Optional[str] = Query(None, description="Filter by mode (conversation / shadowing)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
):
    offset = (page - 1) * page_size
    result = list_sessions(mode=mode, limit=page_size, offset=offset)

    items: List[SessionListItem] = []
    for sess in result["items"]:
        # Compute average score from utterances
        utter_list = list_utterances(sess["id"])
        scores = [u["score"] for u in utter_list if u.get("score") is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        items.append(
            SessionListItem(
                id=sess["id"],
                mode=sess["mode"],
                scenario=sess["scenario"],
                level=sess["level"],
                started_at=sess["started_at"],
                ended_at=sess["ended_at"],
                avg_score=avg_score,
            )
        )

    return SessionsListResponse(sessions=items, total=result["total"])


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session detail including utterances",
)
async def get_session_detail(session_id: str):
    sess = get_session(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # No side effects on read-only GET
    utterances = list_utterances(session_id)
    return SessionDetailResponse(session=sess, utterances=utterances)


@router.get(
    "/weak-points",
    response_model=List[WeakPointItem],
    summary="List weak phrases ordered by frequency",
)
async def get_weak_points(
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
):
    items = list_weak_points(limit=limit)
    return [WeakPointItem(**item) for item in items]


@router.get(
    "/review/next",
    response_model=ReviewProblemResponse,
    summary="Get the next review problem",
)
async def get_next_review():
    wp = pick_next_review()
    if wp is None:
        raise HTTPException(status_code=404, detail="No weak points available for review")
    return ReviewProblemResponse(weak_point=WeakPointItem(**wp))
