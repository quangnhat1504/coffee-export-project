"""Run all public-source coffee data sync jobs."""

from __future__ import annotations

import argparse

from . import sync_export_country, sync_faostat_production, sync_world_prices
from .db import configure_stdout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run public-source coffee data sync jobs.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch/transform only; do not write to database.")
    parser.add_argument("--force-download", action="store_true", help="Refresh cached World Bank/FAOSTAT files.")
    parser.add_argument("--start-year", type=int, default=2005)
    parser.add_argument("--end-year", type=int, default=2024)
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    args = build_parser().parse_args(argv)
    dry_run = ["--dry-run"] if args.dry_run else []
    force = ["--force-download"] if args.force_download else []

    sync_faostat_production.main([*dry_run, *force])
    print()
    sync_world_prices.main([*dry_run, *force])
    print()
    sync_export_country.main(
        [
            *dry_run,
            "--start-year",
            str(args.start_year),
            "--end-year",
            str(args.end_year),
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
