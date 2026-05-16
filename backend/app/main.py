from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import health as health_router
from app.routers import chat as chat_router
from app.routers import audio as audio_router

app.include_router(health_router.router)
app.include_router(chat_router.router)
app.include_router(audio_router.router)

@app.on_event("startup")
async def startup() -> None:
    from app.config import ensure_dirs
    ensure_dirs()

    print(f"SpeakNest backend starting...")
    print(f"  Ollama:    {settings.ollama_base_url}")
    print(f"  STT:       {settings.stt_base_url}")
    print(f"  Upload:    {settings.upload_dir}")
    print(f"  Debug:     {settings.debug}")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }
