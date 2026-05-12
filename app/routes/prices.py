"""Daily coffee price endpoints."""

from __future__ import annotations

from flask import Blueprint, request

from ._helpers import require_engine, service_response
from ..services.price_service import get_recent_prices


bp = Blueprint("prices", __name__, url_prefix="/api/prices")


@bp.get("/recent")
def recent_prices():
    engine, error = require_engine()
    if error:
        return error
    days = request.args.get("days", default=7, type=int)
    return service_response(get_recent_prices(engine, days=days))
