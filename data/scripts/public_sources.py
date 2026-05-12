"""Shared helpers for public coffee data sources."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from .paths import RAW_DATA_DIR


USER_AGENT = "vietnam-coffee-data-portal/1.0 (+research; contact: local)"


def ensure_raw_dir() -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return RAW_DATA_DIR


def fetch_bytes(url: str, timeout: int = 120) -> bytes:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.content


def read_csv_cached(url: str, cache_name: str, force: bool = False, **kwargs) -> pd.DataFrame:
    cache_path = ensure_raw_dir() / cache_name
    if force or not cache_path.exists():
        cache_path.write_bytes(fetch_bytes(url))
    return pd.read_csv(cache_path, **kwargs)


def read_excel_cached(url: str, cache_name: str, force: bool = False, **kwargs) -> pd.DataFrame:
    cache_path = ensure_raw_dir() / cache_name
    if force or not cache_path.exists():
        cache_path.write_bytes(fetch_bytes(url))
    return pd.read_excel(cache_path, **kwargs)


def to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )
