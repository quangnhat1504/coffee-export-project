"""JSON serialization helpers for pandas/SQL results."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if pd.isna(value):
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def records_from_frame(df: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in df.to_dict("records"):
        records.append({key: clean_value(value) for key, value in row.items()})
    return records
