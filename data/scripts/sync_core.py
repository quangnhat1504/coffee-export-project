"""Sync core CSV data into MySQL using idempotent upserts."""

from __future__ import annotations

import argparse
from dataclasses import asdict

from .core_load import load_core_data
from .core_transform import load_core_data as transform_core_data
from .db import configure_stdout, get_engine
from .paths import resolve_data_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync core coffee CSV data into database tables.")
    parser.add_argument("--main-csv", default="Data_coffee.csv", help="Main wide-format coffee CSV filename or path.")
    parser.add_argument("--market-csv", default="Thi_phan_3_thi_truong_chinh.csv", help="Market trade CSV filename or path.")
    parser.add_argument("--dry-run", action="store_true", help="Transform and report counts without writing to database.")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    args = build_parser().parse_args(argv)

    main_csv = resolve_data_file(args.main_csv)
    market_csv = resolve_data_file(args.market_csv)
    frames = transform_core_data(main_csv, market_csv)

    print("Core ETL input:")
    print(f"  main_csv:   {main_csv}")
    print(f"  market_csv: {market_csv}")
    print("Transformed rows:")
    print(f"  coffee_long:        {len(frames.coffee_long)}")
    print(f"  weather:            {len(frames.weather)}")
    print(f"  production:         {len(frames.production)}")
    print(f"  coffee_export:      {len(frames.coffee_export)}")
    print(f"  export_performance: {len(frames.export_performance)}")
    print(f"  market_trade:       {len(frames.market_trade)}")

    if args.dry_run:
        print("Dry run complete. No database writes performed.")
        return 0

    engine = get_engine()
    summary = load_core_data(engine, frames)
    print("Database upsert complete:")
    for key, value in asdict(summary).items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
