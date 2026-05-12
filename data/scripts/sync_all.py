"""Run all clean ETL sync jobs."""

from __future__ import annotations

import argparse

from . import sync_core, sync_prices


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run all clean ETL jobs.")
    parser.add_argument("--dry-run", action="store_true", help="Transform and report counts without writing to database.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    core_args = ["--dry-run"] if args.dry_run else []
    price_args = ["--dry-run"] if args.dry_run else []

    sync_core.main(core_args)
    print()
    sync_prices.main(price_args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
