"""Sync Vietnam coffee exports by partner country from WITS HTML tables."""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from io import StringIO

import pandas as pd
import requests
from sqlalchemy import Engine, text

from .db import configure_stdout, get_engine
from .public_sources import USER_AGENT, to_number


WITS_URL = (
    "https://wits.worldbank.org/trade/comtrade/en/country/VNM/year/{year}/"
    "tradeflow/Exports/partner/ALL/product/{product}"
)


@dataclass(frozen=True)
class ExportCountrySummary:
    rows: int
    years: int
    partners: int


def fetch_year(year: int, product: str) -> pd.DataFrame:
    url = WITS_URL.format(year=year, product=product)
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=90)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))
    candidates = [_normalize_table(table, year) for table in tables]
    candidates = [table for table in candidates if not table.empty]
    if not candidates:
        return pd.DataFrame(columns=_columns())

    return max(candidates, key=len)


def fetch_range(start_year: int, end_year: int, product: str, sleep_seconds: float = 0.4) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        try:
            frame = fetch_year(year, product)
        except Exception as exc:
            print(f"  {year}: skipped ({exc})")
            continue

        print(f"  {year}: {len(frame)} rows")
        if not frame.empty:
            frames.append(frame)
        time.sleep(sleep_seconds)

    if not frames:
        return pd.DataFrame(columns=_columns())
    return pd.concat(frames, ignore_index=True).drop_duplicates(["year", "partner"])


def load_export_country(engine: Engine, df: pd.DataFrame) -> ExportCountrySummary:
    ddl = """
    CREATE TABLE IF NOT EXISTS export_country (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      year INT NOT NULL,
      partner VARCHAR(255) NOT NULL,
      trade_value_1000usd DECIMAL(18,2) NULL,
      trade_value_million_usd DECIMAL(18,6) NULL,
      quantity_tons DECIMAL(18,4) NULL,
      quantity_unit VARCHAR(50) NULL,
      source VARCHAR(40) NOT NULL DEFAULT 'WITS',
      UNIQUE KEY uq_export_country_year_partner (year, partner)
    ) CHARACTER SET utf8mb4
    """
    sql = text("""
        INSERT INTO export_country (
          year, partner, trade_value_1000usd, trade_value_million_usd,
          quantity_tons, quantity_unit, source
        )
        VALUES (
          :year, :partner, :trade_value_1000usd, :trade_value_million_usd,
          :quantity_tons, :quantity_unit, :source
        )
        ON DUPLICATE KEY UPDATE
          trade_value_1000usd = VALUES(trade_value_1000usd),
          trade_value_million_usd = VALUES(trade_value_million_usd),
          quantity_tons = VALUES(quantity_tons),
          quantity_unit = VALUES(quantity_unit),
          source = VALUES(source)
    """)

    clean = df.astype(object).where(pd.notna(df), None)
    records = clean.to_dict("records")
    with engine.begin() as conn:
        conn.execute(text(ddl))
        _ensure_export_country_schema(conn)
        if records:
            conn.execute(sql, records)

    return summarize(df)


def _ensure_export_country_schema(conn) -> None:
    columns = {
        row[0]
        for row in conn.execute(
            text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'export_country'
            """)
        )
    }

    migrations = {
        "trade_value_million_usd": "ALTER TABLE export_country ADD COLUMN trade_value_million_usd DECIMAL(18,6) NULL AFTER trade_value_1000usd",
        "quantity_tons": "ALTER TABLE export_country ADD COLUMN quantity_tons DECIMAL(18,4) NULL AFTER trade_value_million_usd",
        "source": "ALTER TABLE export_country ADD COLUMN source VARCHAR(40) NOT NULL DEFAULT 'WITS' AFTER quantity_unit",
    }

    for column, ddl in migrations.items():
        if column not in columns:
            conn.execute(text(ddl))


def summarize(df: pd.DataFrame) -> ExportCountrySummary:
    if df.empty:
        return ExportCountrySummary(rows=0, years=0, partners=0)
    return ExportCountrySummary(
        rows=len(df),
        years=df["year"].nunique(),
        partners=df["partner"].nunique(),
    )


def _normalize_table(table: pd.DataFrame, year: int) -> pd.DataFrame:
    df = table.copy()
    if all(isinstance(col, int) for col in df.columns) and not df.empty:
        df.columns = df.iloc[0].tolist()
        df = df.iloc[1:].reset_index(drop=True)
    df.columns = [_flatten_column(col) for col in df.columns]
    colmap = {_key(col): col for col in df.columns}

    partner_col = _first(colmap, ["partner", "importer", "country"])
    value_col = _first(colmap, ["trade value 1000usd", "trade value", "value"])
    quantity_col = _first(colmap, ["quantity"])
    unit_col = _first(colmap, ["quantity unit", "unit"])
    year_col = _first(colmap, ["year"])

    if not partner_col or not value_col:
        return pd.DataFrame(columns=_columns())

    output = pd.DataFrame()
    output["year"] = to_number(df[year_col]).fillna(year).astype(int) if year_col else year
    output["partner"] = df[partner_col].astype(str).str.strip()
    output["trade_value_1000usd"] = to_number(df[value_col])
    output["trade_value_million_usd"] = output["trade_value_1000usd"] / 1000.0
    output["quantity_unit"] = df[unit_col].astype(str).str.strip() if unit_col else None

    if quantity_col:
        quantity = to_number(df[quantity_col])
        unit_text = output["quantity_unit"].fillna("").astype(str).str.lower()
        output["quantity_tons"] = quantity.where(~unit_text.str.contains("kg|kilogram"), quantity / 1000.0)
    else:
        output["quantity_tons"] = None

    output["source"] = "WITS"
    output = output[output["partner"].notna() & (output["partner"] != "nan")]
    output = output[~output["partner"].str.lower().isin(["world", "all"])]
    return output[_columns()]


def _flatten_column(column) -> str:
    if isinstance(column, tuple):
        parts = [str(part) for part in column if str(part) and not str(part).startswith("Unnamed")]
        return " ".join(parts).strip()
    return str(column).strip()


def _key(value: str) -> str:
    return " ".join(value.lower().replace("\n", " ").split())


def _first(colmap: dict[str, str], needles: list[str]) -> str | None:
    for needle in needles:
        needle_key = _key(needle)
        for key, original in colmap.items():
            if needle_key in key:
                return original
    return None


def _columns() -> list[str]:
    return [
        "year",
        "partner",
        "trade_value_1000usd",
        "trade_value_million_usd",
        "quantity_tons",
        "quantity_unit",
        "source",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Vietnam coffee exports by country from WITS.")
    parser.add_argument("--start-year", type=int, default=2005)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--product", default="090111", help="HS product code. Default is coffee, not roasted/decaf.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    args = build_parser().parse_args(argv)

    print("WITS export-country sync:")
    print(f"  years:   {args.start_year}-{args.end_year}")
    print(f"  product: {args.product}")
    df = fetch_range(args.start_year, args.end_year, args.product)
    summary = summarize(df)
    print(f"Transformed rows: {summary.rows} ({summary.years} years, {summary.partners} partners)")

    if args.dry_run:
        print("Dry run complete. No database writes performed.")
        return 0

    load_summary = load_export_country(get_engine(), df)
    print(f"Database upsert complete: {load_summary.rows} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
