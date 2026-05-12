"""Pure transformations for daily coffee price CSV files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ALLOWED_REGIONS = {"DakLak", "DakNong", "GiaLai", "LamDong"}


def load_price_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    required = {"date", "region", "price_vnd_per_kg", "scraped_at"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path.name} missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["region"] = df["region"].astype(str).str.strip()
    df["price_vnd_per_kg"] = pd.to_numeric(df["price_vnd_per_kg"], errors="coerce")
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")
    if "source" not in df.columns:
        df["source"] = "csv_import"
    df["source"] = df["source"].fillna("csv_import").astype(str)

    df = df.dropna(subset=["date", "region", "price_vnd_per_kg"]).copy()
    df = df[df["region"].isin(ALLOWED_REGIONS)]
    df["price_vnd_per_kg"] = df["price_vnd_per_kg"].astype(int)
    return df[["date", "region", "price_vnd_per_kg", "scraped_at", "source"]].drop_duplicates(
        subset=["date", "region"],
        keep="last",
    )
