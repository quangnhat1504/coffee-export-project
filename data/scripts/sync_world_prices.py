"""Sync annual world coffee prices from World Bank Pink Sheet history."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import pandas as pd
from sqlalchemy import Engine, text

from .db import configure_stdout, get_engine
from .public_sources import read_excel_cached, to_number


PINK_SHEET_ANNUAL_URL = (
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/"
    "related/CMO-Historical-Data-Annual.xlsx"
)


@dataclass(frozen=True)
class WorldPriceSummary:
    rows: int
    first_year: int | None
    last_year: int | None


def fetch_world_prices(force: bool = False) -> pd.DataFrame:
    raw = read_excel_cached(
        PINK_SHEET_ANNUAL_URL,
        "world_bank_cmo_historical_annual.xlsx",
        force=force,
        sheet_name="Annual Prices (Nominal)",
        header=None,
    )
    return transform_world_prices(raw)


def transform_world_prices(raw: pd.DataFrame) -> pd.DataFrame:
    header_row = _find_header_row(raw)
    if header_row is None:
        raise ValueError("Could not locate year header row in Pink Sheet workbook")

    df = raw.iloc[header_row + 1 :].copy()
    df.columns = raw.iloc[header_row].tolist()
    year_col = df.columns[0]
    df = df.rename(columns={year_col: "year"})
    df["year"] = to_number(df["year"])
    df = df[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)

    robusta_col = _find_column(df.columns, ["robusta"])
    arabica_col = _find_column(df.columns, ["arabica"])
    if not robusta_col and not arabica_col:
        raise ValueError("Could not locate coffee robusta/arabica columns in Pink Sheet workbook")

    output = pd.DataFrame({"year": df["year"]})
    output["coffee_robusta_usd_per_kg"] = to_number(df[robusta_col]) if robusta_col else None
    output["coffee_arabica_usd_per_kg"] = to_number(df[arabica_col]) if arabica_col else None
    output["coffee_robusta_usd_per_ton"] = output["coffee_robusta_usd_per_kg"] * 1000
    output["coffee_arabica_usd_per_ton"] = output["coffee_arabica_usd_per_kg"] * 1000
    output["source"] = "World Bank Pink Sheet"
    return output.dropna(subset=["coffee_robusta_usd_per_kg", "coffee_arabica_usd_per_kg"], how="all")


def load_world_prices(engine: Engine, df: pd.DataFrame) -> WorldPriceSummary:
    ddl = """
    CREATE TABLE IF NOT EXISTS world_coffee_prices (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      year INT NOT NULL,
      coffee_robusta_usd_per_kg DECIMAL(12,6) NULL,
      coffee_arabica_usd_per_kg DECIMAL(12,6) NULL,
      coffee_robusta_usd_per_ton DECIMAL(14,4) NULL,
      coffee_arabica_usd_per_ton DECIMAL(14,4) NULL,
      source VARCHAR(80) NOT NULL,
      UNIQUE KEY uq_world_coffee_prices_year (year)
    ) CHARACTER SET utf8mb4
    """
    sql = text("""
        INSERT INTO world_coffee_prices (
          year, coffee_robusta_usd_per_kg, coffee_arabica_usd_per_kg,
          coffee_robusta_usd_per_ton, coffee_arabica_usd_per_ton, source
        )
        VALUES (
          :year, :coffee_robusta_usd_per_kg, :coffee_arabica_usd_per_kg,
          :coffee_robusta_usd_per_ton, :coffee_arabica_usd_per_ton, :source
        )
        ON DUPLICATE KEY UPDATE
          coffee_robusta_usd_per_kg = VALUES(coffee_robusta_usd_per_kg),
          coffee_arabica_usd_per_kg = VALUES(coffee_arabica_usd_per_kg),
          coffee_robusta_usd_per_ton = VALUES(coffee_robusta_usd_per_ton),
          coffee_arabica_usd_per_ton = VALUES(coffee_arabica_usd_per_ton),
          source = VALUES(source)
    """)
    records = df.astype(object).where(pd.notna(df), None).to_dict("records")
    with engine.begin() as conn:
        conn.execute(text(ddl))
        if records:
            conn.execute(sql, records)
    return summarize(df)


def summarize(df: pd.DataFrame) -> WorldPriceSummary:
    if df.empty:
        return WorldPriceSummary(rows=0, first_year=None, last_year=None)
    return WorldPriceSummary(rows=len(df), first_year=int(df["year"].min()), last_year=int(df["year"].max()))


def _find_header_row(raw: pd.DataFrame) -> int | None:
    for idx, row in raw.iterrows():
        values = [str(value).strip().lower() for value in row.tolist()]
        if any("coffee" in value for value in values):
            return int(idx)
    return None


def _find_column(columns, needles: list[str]) -> str | None:
    for column in columns:
        key = str(column).lower()
        if "coffee" in key and all(needle in key for needle in needles):
            return column
    for column in columns:
        key = str(column).lower()
        if all(needle in key for needle in needles):
            return column
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync annual world coffee prices from World Bank Pink Sheet.")
    parser.add_argument("--force-download", action="store_true", help="Refresh cached Excel file in data/raw.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    args = build_parser().parse_args(argv)

    df = fetch_world_prices(force=args.force_download)
    summary = summarize(df)
    print("World Bank Pink Sheet sync:")
    print(f"  rows:       {summary.rows}")
    print(f"  year range: {summary.first_year}-{summary.last_year}")

    if args.dry_run:
        print("Dry run complete. No database writes performed.")
        return 0

    load_summary = load_world_prices(get_engine(), df)
    print(f"Database upsert complete: {load_summary.rows} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
