"""Sync Vietnam coffee area and production from FAOSTAT bulk data."""

from __future__ import annotations

import argparse
import zipfile
from dataclasses import dataclass

import pandas as pd
from sqlalchemy import Engine, text

from .db import configure_stdout, get_engine
from .public_sources import fetch_bytes, to_number


FAOSTAT_QCL_ASIA_URL = "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_Asia.zip"


@dataclass(frozen=True)
class FaostatProductionSummary:
    rows: int
    first_year: int | None
    last_year: int | None


def fetch_faostat_production(force: bool = False) -> pd.DataFrame:
    from .paths import RAW_DATA_DIR

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = RAW_DATA_DIR / "faostat_qcl_asia.zip"
    if force or not cache_path.exists():
        cache_path.write_bytes(fetch_bytes(FAOSTAT_QCL_ASIA_URL, timeout=180))

    with zipfile.ZipFile(cache_path) as archive:
        csv_names = [
            name
            for name in archive.namelist()
            if name.endswith("_Asia_NOFLAG.csv") or name.endswith("_Asia.csv")
        ]
        if not csv_names:
            raise ValueError("FAOSTAT zip did not contain an Asia data CSV file")
        data_name = next((name for name in csv_names if name.endswith("_Asia_NOFLAG.csv")), csv_names[0])
        with archive.open(data_name) as handle:
            raw = pd.read_csv(handle, low_memory=False)
    return transform_faostat_production(raw)


def transform_faostat_production(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"Area", "Item", "Element", "Unit"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"FAOSTAT data missing columns: {sorted(missing)}")

    df = raw[
        raw["Area"].astype(str).str.casefold().eq("viet nam")
        & raw["Item"].astype(str).str.casefold().isin(["coffee, green", "coffee, green beans"])
        & raw["Element"].astype(str).str.casefold().isin(["area harvested", "production"])
    ].copy()

    if df.empty:
        return pd.DataFrame(columns=_columns())

    year_cols = [col for col in df.columns if isinstance(col, str) and col.startswith("Y") and col[1:].isdigit()]
    if not year_cols:
        raise ValueError("FAOSTAT data did not include year columns like Y2024")

    long_df = df.melt(
        id_vars=["Area", "Item", "Element", "Unit"],
        value_vars=year_cols,
        var_name="year",
        value_name="value",
    )
    long_df["year"] = long_df["year"].str.removeprefix("Y").astype(int)
    long_df["value"] = to_number(long_df["value"])
    long_df = long_df[long_df["value"].notna()]
    pivot = long_df.pivot_table(index="year", columns="Element", values="value", aggfunc="first").reset_index()

    output = pd.DataFrame({"year": pivot["year"].astype(int)})
    output["area_thousand_ha"] = pivot.get("Area harvested") / 1000.0
    output["production_tons"] = pivot.get("Production")
    output["source"] = "FAOSTAT QCL"
    return output[_columns()].sort_values("year")


def load_faostat_production(engine: Engine, df: pd.DataFrame) -> FaostatProductionSummary:
    ddl = """
    CREATE TABLE IF NOT EXISTS faostat_coffee_production (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      year INT NOT NULL,
      area_thousand_ha DECIMAL(12,4) NULL,
      production_tons DECIMAL(16,4) NULL,
      source VARCHAR(60) NOT NULL,
      UNIQUE KEY uq_faostat_coffee_year (year)
    ) CHARACTER SET utf8mb4
    """
    sql = text("""
        INSERT INTO faostat_coffee_production (year, area_thousand_ha, production_tons, source)
        VALUES (:year, :area_thousand_ha, :production_tons, :source)
        ON DUPLICATE KEY UPDATE
          area_thousand_ha = VALUES(area_thousand_ha),
          production_tons = VALUES(production_tons),
          source = VALUES(source)
    """)
    records = df.astype(object).where(pd.notna(df), None).to_dict("records")
    with engine.begin() as conn:
        conn.execute(text(ddl))
        if records:
            conn.execute(sql, records)
    return summarize(df)


def summarize(df: pd.DataFrame) -> FaostatProductionSummary:
    if df.empty:
        return FaostatProductionSummary(rows=0, first_year=None, last_year=None)
    return FaostatProductionSummary(rows=len(df), first_year=int(df["year"].min()), last_year=int(df["year"].max()))


def _columns() -> list[str]:
    return ["year", "area_thousand_ha", "production_tons", "source"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Vietnam coffee area and production from FAOSTAT.")
    parser.add_argument("--force-download", action="store_true", help="Refresh cached FAOSTAT zip in data/raw.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    args = build_parser().parse_args(argv)

    df = fetch_faostat_production(force=args.force_download)
    summary = summarize(df)
    print("FAOSTAT coffee production sync:")
    print(f"  rows:       {summary.rows}")
    print(f"  year range: {summary.first_year}-{summary.last_year}")

    if args.dry_run:
        print("Dry run complete. No database writes performed.")
        return 0

    load_summary = load_faostat_production(get_engine(), df)
    print(f"Database upsert complete: {load_summary.rows} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
