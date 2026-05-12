"""Route helper functions."""

from __future__ import annotations

from flask import current_app, jsonify
from sqlalchemy import Engine


def get_engine() -> Engine | None:
    return current_app.config.get("DB_ENGINE")


def get_settings():
    return current_app.config["SETTINGS"]


def require_engine():
    engine = get_engine()
    if engine is None:
        return None, (jsonify({"success": False, "error": "Database is not configured"}), 503)
    return engine, None


def service_response(result: dict):
    status_code = int(result.pop("status_code", 200))
    return jsonify(result), status_code
