"""Tests for app factory (create_app) and configuration (Settings, get_settings).

Covers Requirements 10.1–10.8:
- create_app returns Flask with all 6 blueprints
- create_app handles DB connection failure gracefully
- get_settings loads from environment variables
- get_settings uses defaults when env vars are missing
- has_database_config property logic
- has_ai_config property logic
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.config import Settings, get_settings


# ---------------------------------------------------------------------------
# create_app tests
# ---------------------------------------------------------------------------


class TestCreateApp:
    """Tests for the create_app application factory."""

    def test_create_app_returns_flask_instance_with_all_blueprints(self):
        """Requirement 10.1: create_app returns Flask with 6 blueprints registered."""
        engine = MagicMock()
        # Make the engine's connect() work as a context manager for the health check
        conn = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=conn)
        ctx.__exit__ = MagicMock(return_value=False)
        engine.connect.return_value = ctx

        with patch("app.create_database_engine", return_value=engine):
            from app import create_app

            app = create_app()

        assert isinstance(app, Flask)

        # Verify all 6 blueprints are registered
        expected_blueprints = {"health", "production", "export", "prices", "weather", "ai"}
        registered = set(app.blueprints.keys())
        assert expected_blueprints.issubset(registered), (
            f"Missing blueprints: {expected_blueprints - registered}"
        )

    def test_create_app_db_connection_failure_sets_engine_none_and_error(self):
        """Requirement 10.2: DB failure sets DB_ENGINE=None and DB_INIT_ERROR."""
        error_msg = "Unable to connect to database: connection refused"

        with patch("app.create_database_engine", side_effect=RuntimeError(error_msg)):
            from app import create_app

            app = create_app()

        assert app.config["DB_ENGINE"] is None
        assert app.config["DB_INIT_ERROR"] == error_msg


# ---------------------------------------------------------------------------
# get_settings tests
# ---------------------------------------------------------------------------


class TestGetSettings:
    """Tests for the get_settings function."""

    def test_get_settings_loads_from_environment_variables(self, monkeypatch):
        """Requirement 10.3: get_settings loads values from env vars."""
        monkeypatch.setenv("HOST", "myhost.example.com")
        monkeypatch.setenv("PORT", "3307")
        monkeypatch.setenv("USER", "admin")
        monkeypatch.setenv("PASSWORD", "secret123")
        monkeypatch.setenv("DB", "coffee_db")
        monkeypatch.setenv("AI_BASE_URL", "https://api.example.com/v1/")
        monkeypatch.setenv("AI_API_KEY", "sk-test-key")
        monkeypatch.setenv("AI_MODEL", "gpt-4")
        monkeypatch.setenv("FLASK_HOST", "127.0.0.1")
        monkeypatch.setenv("FLASK_PORT", "8080")
        monkeypatch.setenv("FLASK_DEBUG", "true")

        # Patch load_dotenv to prevent .env file from interfering
        with patch("app.config.load_dotenv"):
            settings = get_settings()

        assert settings.db_host == "myhost.example.com"
        assert settings.db_port == "3307"
        assert settings.db_user == "admin"
        assert settings.db_password == "secret123"
        assert settings.db_name == "coffee_db"
        assert settings.ai_base_url == "https://api.example.com/v1"  # trailing slash stripped
        assert settings.ai_api_key == "sk-test-key"
        assert settings.ai_model == "gpt-4"
        assert settings.flask_host == "127.0.0.1"
        assert settings.flask_port == 8080
        assert settings.debug is True

    def test_get_settings_uses_defaults_when_env_vars_missing(self, monkeypatch):
        """Requirement 10.4: get_settings uses defaults when env vars are missing."""
        # Clear all relevant env vars to ensure defaults are used
        for var in ("HOST", "PORT", "USER", "PASSWORD", "DB", "CA_CERT", "CA_PEM",
                    "AI_BASE_URL", "AI_API_KEY", "AI_MODEL",
                    "FLASK_HOST", "FLASK_PORT", "FLASK_DEBUG"):
            monkeypatch.delenv(var, raising=False)

        with patch("app.config.load_dotenv"):
            settings = get_settings()

        assert settings.db_host is None
        assert settings.db_port == "3306"
        assert settings.db_user is None
        assert settings.db_password is None
        assert settings.db_name == "defaultdb"
        assert settings.flask_port == 5000
        assert settings.flask_host == "0.0.0.0"
        assert settings.ai_base_url == "http://localhost:20128/v1"
        assert settings.ai_model == "coding-main"
        assert settings.debug is False


# ---------------------------------------------------------------------------
# has_database_config tests
# ---------------------------------------------------------------------------


class TestHasDatabaseConfig:
    """Tests for the Settings.has_database_config property."""

    def test_returns_true_when_all_db_fields_populated(self):
        """Requirement 10.5: True when all DB fields populated."""
        settings = Settings(
            db_host="localhost",
            db_port="3306",
            db_user="user",
            db_password="pass",
            db_name="mydb",
            db_ca_cert=None,
            ai_base_url="http://localhost/v1",
            ai_api_key="key",
            ai_model="model",
            flask_host="0.0.0.0",
            flask_port=5000,
            debug=False,
        )
        assert settings.has_database_config is True

    @pytest.mark.parametrize("missing_field", ["db_host", "db_user", "db_password"])
    def test_returns_false_when_any_db_field_is_none(self, missing_field):
        """Requirement 10.6: False when any DB field is None."""
        kwargs = {
            "db_host": "localhost",
            "db_port": "3306",
            "db_user": "user",
            "db_password": "pass",
            "db_name": "mydb",
            "db_ca_cert": None,
            "ai_base_url": "http://localhost/v1",
            "ai_api_key": "key",
            "ai_model": "model",
            "flask_host": "0.0.0.0",
            "flask_port": 5000,
            "debug": False,
        }
        kwargs[missing_field] = None
        settings = Settings(**kwargs)
        assert settings.has_database_config is False


# ---------------------------------------------------------------------------
# has_ai_config tests
# ---------------------------------------------------------------------------


class TestHasAiConfig:
    """Tests for the Settings.has_ai_config property."""

    def test_returns_true_when_all_ai_fields_non_empty(self):
        """Requirement 10.7: True when all AI fields are non-empty."""
        settings = Settings(
            db_host="localhost",
            db_port="3306",
            db_user="user",
            db_password="pass",
            db_name="mydb",
            db_ca_cert=None,
            ai_base_url="http://api.example.com/v1",
            ai_api_key="sk-key-123",
            ai_model="gpt-4",
            flask_host="0.0.0.0",
            flask_port=5000,
            debug=False,
        )
        assert settings.has_ai_config is True

    @pytest.mark.parametrize(
        "field,value",
        [
            ("ai_base_url", ""),
            ("ai_api_key", None),
            ("ai_api_key", ""),
            ("ai_model", ""),
        ],
    )
    def test_returns_false_when_any_ai_field_missing_or_empty(self, field, value):
        """Requirement 10.8: False when any AI field is missing/empty."""
        kwargs = {
            "db_host": "localhost",
            "db_port": "3306",
            "db_user": "user",
            "db_password": "pass",
            "db_name": "mydb",
            "db_ca_cert": None,
            "ai_base_url": "http://api.example.com/v1",
            "ai_api_key": "sk-key-123",
            "ai_model": "gpt-4",
            "flask_host": "0.0.0.0",
            "flask_port": 5000,
            "debug": False,
        }
        kwargs[field] = value
        settings = Settings(**kwargs)
        assert settings.has_ai_config is False
