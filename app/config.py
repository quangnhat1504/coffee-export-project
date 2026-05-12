"""Application configuration for the rebuilt Coffee Data Portal backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def load_environment() -> None:
    """Load environment variables from the project-level .env file."""
    load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    db_host: str | None
    db_port: str
    db_user: str | None
    db_password: str | None
    db_name: str
    db_ca_cert: str | None
    ai_base_url: str
    ai_api_key: str | None
    ai_model: str
    flask_host: str
    flask_port: int
    debug: bool

    @property
    def has_database_config(self) -> bool:
        return all([self.db_host, self.db_user, self.db_password, self.db_name])

    @property
    def has_ai_config(self) -> bool:
        return bool(self.ai_base_url and self.ai_api_key and self.ai_model)


def get_settings() -> Settings:
    load_environment()

    return Settings(
        db_host=os.getenv("HOST"),
        db_port=os.getenv("PORT", "3306"),
        db_user=os.getenv("USER"),
        db_password=os.getenv("PASSWORD"),
        db_name=os.getenv("DB", "defaultdb"),
        db_ca_cert=os.getenv("CA_CERT") or os.getenv("CA_PEM"),
        ai_base_url=os.getenv("AI_BASE_URL", "http://localhost:20128/v1").rstrip("/"),
        ai_api_key=os.getenv("AI_API_KEY"),
        ai_model=os.getenv("AI_MODEL", "coding-main"),
        flask_host=os.getenv("FLASK_HOST", "0.0.0.0"),
        flask_port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"},
    )
