"""Database DDL and upsert logic for core coffee data."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import Engine, text

from .core_transform import CoreDataFrames


DDL = [
    """
    CREATE TABLE IF NOT EXISTS coffee_long (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      hang_muc VARCHAR(255) NOT NULL,
      year INT NOT NULL,
      value DECIMAL(18,4) NULL,
      UNIQUE KEY uniq_hangmuc_year (hang_muc, year)
    ) CHARACTER SET utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS weather (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      year INT NOT NULL,
      temperature DECIMAL(5,2) NULL,
      humidity DECIMAL(5,2) NULL,
      rain DECIMAL(10,1) NULL,
      UNIQUE KEY uq_weather_year (year)
    ) CHARACTER SET utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS production (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      year INT NOT NULL,
      area_thousand_ha DECIMAL(10,1) NULL,
      output_tons DECIMAL(14,2) NULL,
      export_tons DECIMAL(14,2) NULL,
      UNIQUE KEY uq_prod_year (year)
    ) CHARACTER SET utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS coffee_export (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      year INT NOT NULL,
      export_value_million_usd DECIMAL(16,2) NULL,
      price_world_usd_per_ton DECIMAL(12,2) NULL,
      price_vn_usd_per_ton DECIMAL(12,2) NULL,
      UNIQUE KEY uq_trade_year (year)
    ) CHARACTER SET utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS export_performance (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      year INT NOT NULL,
      area_thousand_ha DECIMAL(10,1) NULL,
      production_tons DECIMAL(14,2) NULL,
      export_tons DECIMAL(14,2) NULL,
      export_value_million_usd DECIMAL(16,2) NULL,
      price_world_usd_per_ton DECIMAL(12,2) NULL,
      price_vn_usd_per_ton DECIMAL(12,2) NULL,
      UNIQUE KEY uq_export_perf_year (year)
    ) CHARACTER SET utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS market_trade (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      importer VARCHAR(100) NOT NULL,
      year INT NOT NULL,
      trade_value_million_usd DECIMAL(16,2) NULL,
      quantity_tons DECIMAL(16,2) NULL,
      UNIQUE KEY uq_importer_year (importer, year)
    ) CHARACTER SET utf8mb4
    """,
]


@dataclass(frozen=True)
class LoadSummary:
    coffee_long: int
    weather: int
    production: int
    coffee_export: int
    export_performance: int
    market_trade: int


def load_core_data(engine: Engine, frames: CoreDataFrames) -> LoadSummary:
    with engine.begin() as conn:
        for ddl in DDL:
            conn.execute(text(ddl))

        coffee_long_count = _upsert_frame(
            conn,
            "coffee_long",
            frames.coffee_long,
            ["hang_muc", "year", "value"],
            ["hang_muc", "year"],
        )
        weather_count = _upsert_frame(conn, "weather", frames.weather, ["year", "temperature", "humidity", "rain"], ["year"])
        production_count = _upsert_frame(
            conn,
            "production",
            frames.production,
            ["year", "area_thousand_ha", "output_tons", "export_tons"],
            ["year"],
        )
        coffee_export_count = _upsert_frame(
            conn,
            "coffee_export",
            frames.coffee_export,
            ["year", "export_value_million_usd", "price_world_usd_per_ton", "price_vn_usd_per_ton"],
            ["year"],
        )
        export_performance_count = _upsert_frame(
            conn,
            "export_performance",
            frames.export_performance,
            [
                "year",
                "area_thousand_ha",
                "production_tons",
                "export_tons",
                "export_value_million_usd",
                "price_world_usd_per_ton",
                "price_vn_usd_per_ton",
            ],
            ["year"],
        )
        market_trade_count = _upsert_frame(
            conn,
            "market_trade",
            frames.market_trade,
            ["importer", "year", "trade_value_million_usd", "quantity_tons"],
            ["importer", "year"],
        )

    return LoadSummary(
        coffee_long=coffee_long_count,
        weather=weather_count,
        production=production_count,
        coffee_export=coffee_export_count,
        export_performance=export_performance_count,
        market_trade=market_trade_count,
    )


def _upsert_frame(conn, table: str, df: pd.DataFrame, columns: list[str], key_columns: list[str]) -> int:
    if df.empty:
        return 0

    insert_cols = ", ".join(columns)
    placeholders = ", ".join([f":{col}" for col in columns])
    update_cols = [col for col in columns if col not in key_columns]
    updates = ", ".join([f"{col} = VALUES({col})" for col in update_cols])
    sql = text(f"""
        INSERT INTO {table} ({insert_cols})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates}
    """)

    clean_df = df[columns].astype(object).where(pd.notna(df[columns]), None)
    records = clean_df.to_dict("records")
    conn.execute(sql, records)
    return len(records)
