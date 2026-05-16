from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.services.ollama_service import generate_conversation
from app.services.stt_service import transcribe_audio
from app.schemas import ChatRequest, ConversationResponse
from app.config import UPLOAD_DIR, ensure_dirs, ollama_available, stt_available

ensure_dirs()


CONVERSATION_PROMPT = Path(__file__).parent.parent / "prompts" / "conversation.md"
FEEDBACK_PROMPT = Path(__file__).parent.parent / "prompts" / "feedback.md"


def load_prompt(path: Path) -> str:
    """Load prompt text from file, return empty string if missing."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


conversation_template = load_prompt(CONVERSATION_PROMPT)
feedback_template = load_prompt(FEEDBACK_PROMPT)


async def process_conversation(req: ChatRequest, audio_path: str | None = None) -> ConversationResponse:
    """
    Process voice input: STT -> Ollama conversation + feedback.

    If audio_path is provided, transcribe it first.
    If transcript is already given, skip STT.
    """
    # 1. STT
    transcript = req.transcript
    if transcript is None:
        if audio_path is None:
            raise ValueError("Either transcript or audio file must be provided")

        try:
            transcript = await transcribe_audio(audio_path)
        except Exception as e:
            raise ServiceUnavailableError(f"STT service failed: {e}") from e

    if not transcript.strip():
        raise ValueError("Transcription returned empty text")

    # 2. Check Ollama availability
    if not ollama_available():
        raise ServiceUnavailableError("Ollama is not available. Please start Ollama first.")

    # 3. Generate conversation reply
    try:
        conv_prompt = conversation_template.format(
            level=req.level,
            scenario=req.scenario,
            user_utterance=transcript,
            conversation_prompt=conversation_template if conversation_template else "",
            feedback_prompt=feedback_template if feedback_template else "",
        ) if conversation_template else None

        response = await generate_conversation(conv_prompt)
    except Exception as e:
        raise ServiceUnavailableError(f"Ollama generation failed: {e}") from e

    return ConversationResponse(
        transcript=transcript,
        reply_en=response.get("reply_en", ""),
        reply_ja=response.get("reply_ja", ""),
        feedback_ja=response.get("feedback_ja", ""),
        next_practice=response.get("next_practice", ""),
    )


class ServiceUnavailableError(Exception):
    pass
