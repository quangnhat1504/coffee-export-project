"""Weather data access."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text

from .production_service import PROVINCE_NAMES
from ..utils.serialization import records_from_frame


def get_weather_for_province(engine: Engine, province: str, aggregate: str = "recent12", year: int | None = None) -> dict:
    if province not in PROVINCE_NAMES:
        return {"success": False, "error": "Invalid province", "status_code": 400}

    if aggregate == "yearly" and year is None:
        query = text("""
            SELECT year,
                   AVG(temperature_mean) AS temperature_mean,
                   SUM(precipitation_sum) AS precipitation_sum,
                   AVG(humidity_mean) AS humidity_mean
            FROM weather_data_monthly
            WHERE province = :province
            GROUP BY year
            ORDER BY year ASC
        """)
        params = {"province": province}
    elif year is not None:
        query = text("""
            SELECT year, month, temperature_mean, precipitation_sum, humidity_mean
            FROM weather_data_monthly
            WHERE province = :province AND year = :year
            ORDER BY month ASC
        """)
        params = {"province": province, "year": year}
    elif aggregate == "recent12":
        query = text("""
            SELECT year, month, temperature_mean, precipitation_sum, humidity_mean
            FROM (
                SELECT year, month, temperature_mean, precipitation_sum, humidity_mean
                FROM weather_data_monthly
                WHERE province = :province
                ORDER BY year DESC, month DESC
                LIMIT 12
            ) recent
            ORDER BY year ASC, month ASC
        """)
        params = {"province": province}
    else:
        query = text("""
            SELECT year, month, temperature_mean, precipitation_sum, humidity_mean
            FROM weather_data_monthly
            WHERE province = :province
            ORDER BY year ASC, month ASC
        """)
        params = {"province": province}

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=params)

    stats = {}
    if not df.empty:
        stats = {
            "temperature": _series_stats(df["temperature_mean"]),
            "precipitation": _series_stats(df["precipitation_sum"]),
            "humidity": _series_stats(df["humidity_mean"]),
        }

    return {
        "success": True,
        "province": province,
        "province_display": PROVINCE_NAMES[province],
        "data": records_from_frame(df),
        "count": len(df),
        "stats": stats,
    }


def _series_stats(series: pd.Series) -> dict:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return {"current": None, "avg": None, "min": None, "max": None}
    return {
        "current": round(float(clean.iloc[-1]), 2),
        "avg": round(float(clean.mean()), 2),
        "min": round(float(clean.min()), 2),
        "max": round(float(clean.max()), 2),
    }
