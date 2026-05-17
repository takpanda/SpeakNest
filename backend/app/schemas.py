from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    level: str = Field(default="A2", description="CEFR learner level (A1, A2, B1, B2, C1, C2)")
    scenario: str = Field(default="カフェで注文する", description="Conversation scenario")
    transcript: Optional[str] = Field(default=None, description="Pre-transcribed text (optional if audio file provided)")


class ConversationResponse(BaseModel):
    transcript: str
    reply_en: str
    reply_ja: str
    feedback_ja: str
    next_practice: str


class HealthResponse(BaseModel):
    status: str
    ollama: str
    stt: str
    upload_dir: str
