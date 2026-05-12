"""Weather endpoints."""

from __future__ import annotations

from flask import Blueprint, request

from ._helpers import require_engine, service_response
from ..services.production_service import PROVINCE_NAMES
from ..services.weather_service import get_weather_for_province


bp = Blueprint("weather", __name__, url_prefix="/api/weather")


@bp.get("/provinces")
def weather_provinces():
    return {"success": True, "provinces": [{"value": key, "label": value} for key, value in PROVINCE_NAMES.items()]}


@bp.get("/province/<province>")
def weather_by_province(province: str):
    engine, error = require_engine()
    if error:
        return error
    aggregate = request.args.get("aggregate", "recent12")
    year = request.args.get("year", type=int)
    return service_response(get_weather_for_province(engine, province=province, aggregate=aggregate, year=year))
