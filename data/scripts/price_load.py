"""Database DDL and upsert logic for daily coffee prices."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text


DDL = """
CREATE TABLE IF NOT EXISTS daily_coffee_prices (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  date DATE NOT NULL,
  region VARCHAR(50) NOT NULL,
  price_vnd_per_kg INT NOT NULL,
  scraped_at DATETIME NULL,
  source VARCHAR(100) NULL,
  UNIQUE KEY uq_price_date_region (date, region),
  INDEX idx_price_date (date),
  INDEX idx_price_region (region)
) CHARACTER SET utf8mb4
"""


def load_price_data(engine: Engine, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    with engine.begin() as conn:
        conn.execute(text(DDL))
        clean_df = df.astype(object).where(pd.notna(df), None)
        records = clean_df.to_dict("records")
        conn.execute(
            text("""
                INSERT INTO daily_coffee_prices
                    (date, region, price_vnd_per_kg, scraped_at, source)
                VALUES
                    (:date, :region, :price_vnd_per_kg, :scraped_at, :source)
                ON DUPLICATE KEY UPDATE
                    price_vnd_per_kg = VALUES(price_vnd_per_kg),
                    scraped_at = VALUES(scraped_at),
                    source = VALUES(source)
            """),
            records,
        )
    return len(df)
