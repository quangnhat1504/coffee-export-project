"""Time-series preparation utilities used by API services and models."""

from __future__ import annotations

from typing import Any

import pandas as pd


def interpolate_series(df: pd.DataFrame, column: str, method: str = "polynomial", order: int = 2) -> pd.Series:
    series = pd.to_numeric(df[column], errors="coerce")

    if series.notna().sum() < 2:
        return series

    try:
        if method == "polynomial" and series.notna().sum() > order:
            series = series.interpolate(method="polynomial", order=order, limit_direction="both")
        else:
            series = series.interpolate(method="linear", limit_direction="both")
    except Exception:
        series = series.interpolate(method="linear", limit_direction="both")

    return series.ffill().bfill()


def add_growth_fields(df: pd.DataFrame, value_column: str) -> dict[str, Any]:
    if df.empty or value_column not in df:
        return {"current": None, "previous": None, "change": None, "change_percent": None}

    series = pd.to_numeric(df[value_column], errors="coerce").dropna()
    if series.empty:
        return {"current": None, "previous": None, "change": None, "change_percent": None}

    current = float(series.iloc[-1])
    previous = float(series.iloc[-2]) if len(series) > 1 else None
    change = current - previous if previous is not None else None
    change_percent = (change / previous * 100) if previous not in (None, 0) else None

    return {
        "current": round(current, 2),
        "previous": round(previous, 2) if previous is not None else None,
        "change": round(change, 2) if change is not None else None,
        "change_percent": round(change_percent, 2) if change_percent is not None else None,
    }
