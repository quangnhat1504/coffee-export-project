"""Database engine and small query helpers."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, Connection

from .config import Settings


def _build_url(settings: Settings) -> URL:
    return URL.create(
        "mysql+pymysql",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=int(settings.db_port),
        database=settings.db_name,
    )


def create_database_engine(settings: Settings) -> Engine | None:
    """Create a SQLAlchemy engine; return None when DB env is incomplete."""
    if not settings.has_database_config:
        return None

    url = _build_url(settings)
    common_options = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 10,
        "echo": False,
    }

    strategies: list[dict] = [
        {"connect_args": {"ssl": False, "connect_timeout": 10, "read_timeout": 30, "write_timeout": 30}},
        {"connect_args": {"connect_timeout": 20}},
    ]

    cert_file: str | None = None
    if settings.db_ca_cert:
        ca_value = settings.db_ca_cert.strip()
        if "BEGIN CERTIFICATE" in ca_value:
            normalized_ca = ca_value.replace("\\n", "\n")
            with NamedTemporaryFile(mode="w", delete=False, suffix=".pem", encoding="utf-8") as tmp:
                tmp.write(normalized_ca)
                cert_file = tmp.name
        else:
            try:
                if len(ca_value) < 260 and Path(ca_value).exists():
                    cert_file = ca_value
            except Exception:
                pass
        if cert_file:
            strategies.insert(1, {"connect_args": {"ssl": {"ca": cert_file}, "connect_timeout": 20}})

    last_error: Exception | None = None
    for strategy in strategies:
        try:
            engine = create_engine(url, **common_options, **strategy)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception as exc:  # pragma: no cover - depends on external DB
            last_error = exc

    raise RuntimeError(f"Unable to connect to database: {last_error}")


@contextmanager
def db_connection(engine: Engine) -> Iterator[Connection]:
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_database(engine: Engine | None) -> tuple[bool, str]:
    if engine is None:
        return False, "Database engine is not configured"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connected"
    except Exception as exc:
        return False, str(exc)


def table_exists(engine: Engine, table_name: str) -> bool:
    query = text("SHOW TABLES LIKE :table_name")
    with engine.connect() as conn:
        return conn.execute(query, {"table_name": table_name}).first() is not None
