"""Pure transformations for the core coffee CSV inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class CoreDataFrames:
    coffee_long: pd.DataFrame
    weather: pd.DataFrame
    production: pd.DataFrame
    coffee_export: pd.DataFrame
    export_performance: pd.DataFrame
    market_trade: pd.DataFrame


def load_core_data(main_csv: Path, market_csv: Path) -> CoreDataFrames:
    raw = pd.read_csv(main_csv, encoding="utf-8-sig")
    market_trade = _load_market_trade(market_csv)
    coffee_long = _to_long(raw)
    weather = _pivot_weather(coffee_long)
    production = _pivot_production(coffee_long)
    coffee_export = _pivot_export(coffee_long)
    export_performance = _build_export_performance(production, coffee_export)

    return CoreDataFrames(
        coffee_long=coffee_long,
        weather=weather,
        production=production,
        coffee_export=coffee_export,
        export_performance=export_performance,
        market_trade=market_trade,
    )


def _to_long(df: pd.DataFrame) -> pd.DataFrame:
    id_col = "Hang_muc"
    year_cols = [col for col in df.columns if str(col).isdigit()]
    if id_col not in df.columns:
        raise ValueError("Data_coffee.csv must contain Hang_muc column")
    if not year_cols:
        raise ValueError("Data_coffee.csv does not contain year columns")

    long_df = df.melt(id_vars=[id_col], value_vars=year_cols, var_name="year", value_name="value")
    long_df = long_df.rename(columns={id_col: "hang_muc"})
    long_df["year"] = pd.to_numeric(long_df["year"], errors="coerce").astype("Int64")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df = long_df.dropna(subset=["year", "hang_muc"]).copy()
    long_df["year"] = long_df["year"].astype(int)
    long_df["hang_muc"] = long_df["hang_muc"].astype(str).str.strip()
    long_df = long_df[~long_df["hang_muc"].isin({"", "nan", "NaN", "Hang_muc", "hang_muc"})]
    long_df = long_df[~(long_df["value"].notna() & (long_df["value"] == long_df["year"]))]
    long_df = long_df.drop_duplicates(subset=["hang_muc", "year"], keep="first")
    return long_df[["hang_muc", "year", "value"]].sort_values(["hang_muc", "year"]).reset_index(drop=True)


def _find_metric_value(df: pd.DataFrame, year: int, patterns: tuple[str, ...]) -> Optional[float]:
    rows = df[df["year"] == year]
    for pattern in patterns:
        matched = rows[rows["hang_muc"].str.contains(pattern, case=False, regex=False, na=False)]
        if not matched.empty:
            value = matched["value"].dropna()
            if not value.empty:
                return float(value.iloc[0])
    return None


def _pivot_weather(coffee_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in sorted(coffee_long["year"].unique()):
        rows.append({
            "year": int(year),
            "temperature": _find_metric_value(coffee_long, year, ("Nhiet_do_trung_binh",)),
            "humidity": _find_metric_value(coffee_long, year, ("Do_am_trung_binh",)),
            "rain": _find_metric_value(coffee_long, year, ("Tong_luong_mua",)),
        })
    return pd.DataFrame(rows)


def _pivot_production(coffee_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in sorted(coffee_long["year"].unique()):
        rows.append({
            "year": int(year),
            "area_thousand_ha": _find_metric_value(coffee_long, year, ("Area (Thousand ha)",)),
            "output_tons": _find_metric_value(coffee_long, year, ("San luong ca phe san xuat",)),
            "export_tons": _find_metric_value(coffee_long, year, ("San luong ca phe xuat khau",)),
        })
    return pd.DataFrame(rows)


def _pivot_export(coffee_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in sorted(coffee_long["year"].unique()):
        rows.append({
            "year": int(year),
            "export_value_million_usd": _find_metric_value(coffee_long, year, ("Kim_Ngach(millionUSD)", "Kim Ngach", "Kim_Ngach")),
            "price_world_usd_per_ton": _find_metric_value(coffee_long, year, ("coffee_price_usd_per_ton(world)",)),
            "price_vn_usd_per_ton": _find_metric_value(coffee_long, year, ("coffee_price_usd_per_ton(vietnam)",)),
        })
    return pd.DataFrame(rows)


def _build_export_performance(production: pd.DataFrame, coffee_export: pd.DataFrame) -> pd.DataFrame:
    df = production.merge(coffee_export, on="year", how="left")
    df = df.rename(columns={"output_tons": "production_tons"})
    return df[
        [
            "year",
            "area_thousand_ha",
            "production_tons",
            "export_tons",
            "export_value_million_usd",
            "price_world_usd_per_ton",
            "price_vn_usd_per_ton",
        ]
    ]


def _load_market_trade(market_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(market_csv, encoding="utf-8-sig")
    df = df.rename(columns=lambda col: str(col).strip())
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    required = {"Year", "Importer", "Trade Value(million_USD)", "Quantity(tons)"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Thi_phan_3_thi_truong_chinh.csv missing columns: {sorted(missing)}")

    df["year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["importer"] = df["Importer"].astype(str).str.strip()
    df["trade_value_million_usd"] = pd.to_numeric(df["Trade Value(million_USD)"], errors="coerce")
    df["quantity_tons"] = pd.to_numeric(df["Quantity(tons)"], errors="coerce")
    df = df.dropna(subset=["year", "importer"]).copy()
    df["year"] = df["year"].astype(int)
    return df[["importer", "year", "trade_value_million_usd", "quantity_tons"]].drop_duplicates(
        subset=["importer", "year"],
        keep="last",
    )
