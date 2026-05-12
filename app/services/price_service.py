"""Daily coffee price data access."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text


PROVINCE_NAMES = {
    "DakLak": "Dak Lak",
    "GiaLai": "Gia Lai",
    "DakNong": "Dak Nong",
    "LamDong": "Lam Dong",
}


def get_recent_prices(engine: Engine, days: int = 7) -> dict:
    days = max(1, min(int(days), 30))

    with engine.connect() as conn:
        max_date = conn.execute(text("""
            SELECT MAX(date)
            FROM daily_coffee_prices
            WHERE region IN ('DakLak', 'GiaLai', 'DakNong', 'LamDong')
        """)).scalar()

    if not max_date:
        return {"success": True, "days": days, "provinces": [], "count": 0}

    query = text("""
        SELECT region, date, price_vnd_per_kg
        FROM daily_coffee_prices
        WHERE date > DATE_SUB(:max_date, INTERVAL :days DAY)
          AND date <= :max_date
          AND region IN ('DakLak', 'GiaLai', 'DakNong', 'LamDong')
        ORDER BY date ASC, region ASC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"max_date": max_date, "days": days})

    provinces = []
    for region, group in df.groupby("region"):
        prices = [
            {"date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
             "price": float(row["price_vnd_per_kg"])}
            for _, row in group.iterrows()
        ]
        values = [item["price"] for item in prices]
        current = values[-1] if values else None
        previous = values[0] if len(values) > 1 else None
        change = current - previous if current is not None and previous is not None else None

        provinces.append({
            "name": region,
            "display_name": PROVINCE_NAMES.get(region, region),
            "prices": prices,
            "current_price": current,
            "avg_price": round(sum(values) / len(values), 0) if values else None,
            "min_price": min(values) if values else None,
            "max_price": max(values) if values else None,
            "price_change": change,
            "price_change_percent": round(change / previous * 100, 2) if previous not in (None, 0) and change is not None else None,
        })

    return {"success": True, "days": days, "max_date": max_date.isoformat(), "provinces": provinces, "count": len(provinces)}
