"""Database helper for ETL scripts."""

from __future__ import annotations

import sys

from sqlalchemy import Engine

from app.config import get_settings
from app.db import create_database_engine


def get_engine() -> Engine:
    settings = get_settings()
    if not settings.has_database_config:
        raise RuntimeError("Database env is incomplete. Required: HOST, PORT, USER, PASSWORD, DB")
    engine = create_database_engine(settings)
    if engine is None:
        raise RuntimeError("Database engine could not be initialized")
    return engine


def configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
