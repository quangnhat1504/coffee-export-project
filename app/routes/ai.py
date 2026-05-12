"""AI insight endpoints."""

from __future__ import annotations

from flask import Blueprint, request

from ._helpers import get_settings, service_response
from ..services.ai_service import create_insight


bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@bp.post("/insight")
def ai_insight():
    payload = request.get_json(silent=True) or {}
    return service_response(create_insight(get_settings(), payload))
