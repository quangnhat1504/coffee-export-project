"""Sync daily coffee price CSV data into MySQL using idempotent upserts."""

from __future__ import annotations

import argparse

from .db import configure_stdout, get_engine
from .paths import resolve_data_file
from .price_load import load_price_data as load_prices_to_db
from .price_transform import load_price_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync daily coffee price CSV data into database.")
    parser.add_argument(
        "--csv",
        default="coffee_prices_historical.csv",
        help="Price CSV filename or path. Defaults to historical data.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Transform and report counts without writing to database.")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    args = build_parser().parse_args(argv)
    csv_path = resolve_data_file(args.csv)
    df = load_price_data(csv_path)

    print("Price ETL input:")
    print(f"  csv: {csv_path}")
    print(f"  rows: {len(df)}")
    if not df.empty:
        print(f"  date_range: {df['date'].min()} -> {df['date'].max()}")
        print(f"  regions: {', '.join(sorted(df['region'].unique()))}")

    if args.dry_run:
        print("Dry run complete. No database writes performed.")
        return 0

    count = load_prices_to_db(get_engine(), df)
    print(f"Database upsert complete: daily_coffee_prices={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
