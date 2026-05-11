"""Runtime configuration loaded from env (.env via pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: Literal["anthropic", "openai", "mock"] = "mock"
    llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_frames: str = "vitaporta/frames"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    chroma_persist_dir: str = str(REPO_ROOT / ".chroma")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    gait_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    skin_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    respiration_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
