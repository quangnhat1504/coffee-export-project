"""Rebuilt Flask application package."""

from __future__ import annotations

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_compress import Compress

from .config import PROJECT_ROOT, get_settings
from .db import create_database_engine
from .routes import ai, export, health, prices, production, weather


def create_app() -> Flask:
    settings = get_settings()

    frontend_dir = PROJECT_ROOT / "frontend"
    app = Flask(
        __name__,
        static_folder=str(frontend_dir / "static"),
        static_url_path="/static",
    )
    app.config["SETTINGS"] = settings
    try:
        app.config["DB_ENGINE"] = create_database_engine(settings)
        app.config["DB_INIT_ERROR"] = None
    except Exception as exc:  # pragma: no cover - depends on external DB availability
        app.config["DB_ENGINE"] = None
        app.config["DB_INIT_ERROR"] = str(exc)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    Compress(app)

    app.register_blueprint(health.bp)
    app.register_blueprint(production.bp)
    app.register_blueprint(export.bp)
    app.register_blueprint(prices.bp)
    app.register_blueprint(weather.bp)
    app.register_blueprint(ai.bp)

    @app.get("/")
    def frontend_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/<path:path>")
    def frontend_fallback(path: str):
        if path.startswith("api/"):
            return jsonify({"success": False, "error": "Endpoint not found"}), 404
        return send_from_directory(frontend_dir, "index.html")

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(Exception)
    def internal_error(error):
        app.logger.exception("Unhandled error")
        return jsonify({"success": False, "error": str(error)}), 500

    return app
