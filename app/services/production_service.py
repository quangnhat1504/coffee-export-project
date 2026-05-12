"""Production data access and shaping."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text

from ..utils.serialization import records_from_frame
from ..utils.timeseries import add_growth_fields, interpolate_series


PROVINCE_NAMES = {
    "DakLak": "Dak Lak",
    "GiaLai": "Gia Lai",
    "DakNong": "Dak Nong",
    "LamDong": "Lam Dong",
}


def get_production_overview(engine: Engine) -> dict:
    query = text("""
        SELECT year, area_thousand_ha, output_tons, export_tons
        FROM production
        ORDER BY year ASC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        return {"success": True, "data": [], "count": 0, "stats": {}}

    numeric_cols = ["area_thousand_ha", "output_tons", "export_tons"]
    for col in numeric_cols:
        df[col] = interpolate_series(df, col)

    df["output_million_tons"] = (df["output_tons"] / 1_000_000).round(2)
    df["export_million_tons"] = (df["export_tons"] / 1_000_000).round(2)
    df["yield_tons_per_ha"] = (df["output_tons"] / (df["area_thousand_ha"] * 1000)).round(2)

    return {
        "success": True,
        "data": records_from_frame(df),
        "count": len(df),
        "years": [int(year) for year in df["year"].tolist()],
        "stats": {
            "production": add_growth_fields(df, "output_tons"),
            "area": add_growth_fields(df, "area_thousand_ha"),
            "export": add_growth_fields(df, "export_tons"),
            "yield": add_growth_fields(df, "yield_tons_per_ha"),
        },
        "metadata": {"interpolated": True, "source": "production"},
    }


def get_province_production(engine: Engine, province: str) -> dict:
    if province not in PROVINCE_NAMES:
        return {"success": False, "error": "Invalid province", "status_code": 400}

    query = text("""
        SELECT year, area_thousand_ha, output_tons, export_tons
        FROM production_by_province
        WHERE province = :province
        ORDER BY year ASC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"province": province})

    if df.empty:
        return {"success": False, "error": "No production data found", "status_code": 404}

    for col in ["area_thousand_ha", "output_tons", "export_tons"]:
        df[col] = interpolate_series(df, col, method="linear")

    df["output_million_tons"] = (df["output_tons"] / 1_000_000).round(2)
    df["export_million_tons"] = (df["export_tons"] / 1_000_000).round(2)
    df["yield_tons_per_ha"] = (df["output_tons"] / (df["area_thousand_ha"] * 1000)).round(2)

    return {
        "success": True,
        "province": province,
        "province_display": PROVINCE_NAMES[province],
        "data": records_from_frame(df),
        "count": len(df),
        "metadata": {"interpolated": True, "source": "production_by_province"},
    }
