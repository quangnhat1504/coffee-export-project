"""Health and readiness endpoints."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify

from ..db import check_database


bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health_check():
    settings = current_app.config["SETTINGS"]
    engine = current_app.config.get("DB_ENGINE")
    db_ok, db_message = check_database(engine)
    if not db_ok and current_app.config.get("DB_INIT_ERROR"):
        db_message = current_app.config["DB_INIT_ERROR"]

    return jsonify({
        "success": True,
        "status": "healthy" if db_ok else "degraded",
        "api": "running",
        "database": {"connected": db_ok, "message": db_message},
        "ai": {"configured": settings.has_ai_config, "model": settings.ai_model},
        "timestamp": datetime.now().isoformat(),
    }), 200 if db_ok else 503
