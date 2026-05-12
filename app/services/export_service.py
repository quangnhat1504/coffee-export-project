"""Export data access and shaping."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text

from ..db import table_exists
from ..utils.serialization import records_from_frame
from ..utils.timeseries import add_growth_fields, interpolate_series


def get_export_overview(engine: Engine) -> dict:
    if table_exists(engine, "export_performance"):
        query = text("""
            SELECT year, area_thousand_ha, production_tons, export_tons,
                   export_value_million_usd, price_world_usd_per_ton, price_vn_usd_per_ton
            FROM export_performance
            ORDER BY year ASC
        """)
    else:
        query = text("""
            SELECT ce.year,
                   p.area_thousand_ha,
                   p.output_tons AS production_tons,
                   p.export_tons,
                   ce.export_value_million_usd,
                   ce.price_world_usd_per_ton,
                   ce.price_vn_usd_per_ton
            FROM coffee_export ce
            LEFT JOIN production p ON p.year = ce.year
            ORDER BY ce.year ASC
        """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        return {"success": True, "data": [], "count": 0, "stats": {}}

    numeric_cols = [
        "area_thousand_ha",
        "production_tons",
        "export_tons",
        "export_value_million_usd",
        "price_world_usd_per_ton",
        "price_vn_usd_per_ton",
    ]
    for col in numeric_cols:
        if col in df:
            df[col] = interpolate_series(df, col)

    return {
        "success": True,
        "data": records_from_frame(df),
        "count": len(df),
        "years": [int(year) for year in df["year"].tolist()],
        "stats": {
            "export_value": add_growth_fields(df, "export_value_million_usd"),
            "world_price": add_growth_fields(df, "price_world_usd_per_ton"),
            "vn_price": add_growth_fields(df, "price_vn_usd_per_ton"),
            "export_volume": add_growth_fields(df, "export_tons"),
        },
        "metadata": {"interpolated": True, "source": "export_performance_or_join"},
    }


def get_export_countries(engine: Engine, year: int | None = None, limit: int = 9) -> dict:
    with engine.connect() as conn:
        max_year = conn.execute(text("SELECT MAX(year) FROM export_country")).scalar()

    selected_year = int(year or max_year)
    query = text("""
        SELECT partner AS country,
               quantity AS export_volume,
               trade_value_1000usd AS export_value_1000usd
        FROM export_country
        WHERE year = :year AND partner != 'World'
        ORDER BY quantity DESC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"year": selected_year})

    if df.empty:
        return {
            "success": True,
            "year": selected_year,
            "countries": [],
            "others": {"volume": 0, "percentage": 0},
            "total": 0,
            "count": 0,
        }

    total_volume = float(df["export_volume"].sum())
    top = df.head(limit).copy()
    top["percentage"] = (top["export_volume"] / total_volume * 100).round(1) if total_volume else 0

    countries = [
        {
            "name": row["country"],
            "volume": float(row["export_volume"]),
            "value_1000usd": float(row["export_value_1000usd"]) if pd.notna(row["export_value_1000usd"]) else None,
            "percentage": float(row["percentage"]),
        }
        for _, row in top.iterrows()
    ]

    others_volume = float(df.iloc[limit:]["export_volume"].sum()) if len(df) > limit else 0.0
    others_percentage = round(others_volume / total_volume * 100, 1) if total_volume else 0

    return {
        "success": True,
        "year": selected_year,
        "countries": countries,
        "others": {"volume": others_volume, "percentage": others_percentage},
        "total": total_volume,
        "count": len(countries),
        "metadata": {"max_available_year": int(max_year) if max_year else None},
    }
