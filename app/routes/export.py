"""Export endpoints."""

from __future__ import annotations

from flask import Blueprint, request

from ._helpers import require_engine, service_response
from ..services.export_service import get_export_countries, get_export_overview


bp = Blueprint("export", __name__, url_prefix="/api/export")


@bp.get("/overview")
def export_overview():
    engine, error = require_engine()
    if error:
        return error
    return service_response(get_export_overview(engine))


@bp.get("/countries")
def export_countries():
    engine, error = require_engine()
    if error:
        return error
    year = request.args.get("year", type=int)
    limit = request.args.get("limit", default=9, type=int)
    return service_response(get_export_countries(engine, year=year, limit=limit))


@bp.get("")
def legacy_export_overview():
    return export_overview()
