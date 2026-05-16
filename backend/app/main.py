from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.routers import config, health


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    whisper_base_url: str = "http://localhost:8080"
    tts_base_url: str = "http://localhost:5000"
    data_dir: str = "./data"
    recordings_dir: str = "./recordings"
    database_url: str = "sqlite:///./data/speaknest.db"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = AppSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings  # ensure settings are initialized (loads .env)
    yield


app = FastAPI(title="SpeakNest API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(config.router)
