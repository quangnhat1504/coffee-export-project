"""Shared fixtures for the test suite.

Provides mock engine, test settings, Flask app/client, and sample DataFrame helpers.
All fixtures are isolated and require no external services.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy import Engine

from app.config import Settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings() -> Settings:
    """Return a Settings dataclass with hardcoded safe defaults (no env reads)."""
    return Settings(
        db_host="localhost",
        db_port="3306",
        db_user="test",
        db_password="test",
        db_name="testdb",
        db_ca_cert=None,
        ai_base_url="http://localhost:9999/v1",
        ai_api_key="test-key",
        ai_model="test-model",
        flask_host="127.0.0.1",
        flask_port=5000,
        debug=False,
    )


@pytest.fixture
def mock_engine():
    """Return a tuple of (MagicMock(spec=Engine), mock_connection).

    The engine's connect() is configured as a context manager that yields
    the mock connection object.
    """
    engine = MagicMock(spec=Engine)
    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=conn)
    ctx.__exit__ = MagicMock(return_value=False)
    engine.connect.return_value = ctx
    return engine, conn


@pytest.fixture
def app(mock_engine):
    """Create a Flask app with the database engine mocked out."""
    engine, _conn = mock_engine
    with patch("app.create_database_engine", return_value=engine):
        from app import create_app

        application = create_app()
    return application


@pytest.fixture
def client(app):
    """Return a Flask test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Helper functions for generating sample DataFrames
# ---------------------------------------------------------------------------


def make_production_df(rows: int = 5, has_nulls: bool = False) -> pd.DataFrame:
    """Create a sample production DataFrame.

    Columns: year, area_thousand_ha, output_tons, export_tons
    """
    data = {
        "year": list(range(2018, 2018 + rows)),
        "area_thousand_ha": [600.0 + i * 10 for i in range(rows)],
        "output_tons": [1_500_000.0 + i * 100_000 for i in range(rows)],
        "export_tons": [1_200_000.0 + i * 80_000 for i in range(rows)],
    }
    if has_nulls and rows > 2:
        data["output_tons"][2] = None
    return pd.DataFrame(data)


def make_price_df(
    provinces: tuple[str, ...] = ("DakLak", "GiaLai"),
    days: int = 7,
) -> pd.DataFrame:
    """Create a sample daily prices DataFrame.

    Columns: region, date, price_vnd_per_kg
    """
    rows: list[dict] = []
    base_date = date(2024, 1, 1)
    for province in provinces:
        base_price = 95_000.0 if province == "DakLak" else 93_000.0
        for d in range(days):
            rows.append(
                {
                    "region": province,
                    "date": base_date + timedelta(days=d),
                    "price_vnd_per_kg": base_price + d * 500,
                }
            )
    return pd.DataFrame(rows)


def make_weather_df(months: int = 12) -> pd.DataFrame:
    """Create a sample weather DataFrame.

    Columns: year, month, temperature_mean, precipitation_sum, humidity_mean
    """
    data = {
        "year": [2023] * months,
        "month": list(range(1, months + 1)),
        "temperature_mean": [22.0 + (i % 6) for i in range(months)],
        "precipitation_sum": [100.0 + i * 20 for i in range(months)],
        "humidity_mean": [70.0 + (i % 4) for i in range(months)],
    }
    return pd.DataFrame(data)
