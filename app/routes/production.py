"""Production endpoints."""

from __future__ import annotations

from flask import Blueprint

from ._helpers import require_engine, service_response
from ..services.production_service import PROVINCE_NAMES, get_production_overview, get_province_production


bp = Blueprint("production", __name__, url_prefix="/api/production")


@bp.get("")
def production_overview():
    engine, error = require_engine()
    if error:
        return error
    return service_response(get_production_overview(engine))


@bp.get("/provinces")
def production_provinces():
    return {"success": True, "provinces": [{"value": key, "label": value} for key, value in PROVINCE_NAMES.items()]}


@bp.get("/province/<province>")
def production_by_province(province: str):
    engine, error = require_engine()
    if error:
        return error
    return service_response(get_province_production(engine, province))
