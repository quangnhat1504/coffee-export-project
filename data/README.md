# Data Pipeline

ETL commands live in `data/scripts/`. Source files are stored in `data/raw/`.

## Commands

Dry-run all transforms without writing to the database:

```bash
npm run etl:dry-run
```

Sync core annual CSV data:

```bash
npm run etl:core
```

Sync daily province price CSV data:

```bash
npm run etl:prices
```

Run all ETL jobs:

```bash
npm run etl:all
```

Fetch and sync public-source datasets:

```bash
npm run etl:public
```

Dry-run the public-source pipeline:

```bash
npm run etl:public:dry-run
```

## Inputs

The scripts read CSV inputs from `data/raw/` unless an explicit path is passed.

Current inputs:

```text
Data_coffee.csv
Thi_phan_3_thi_truong_chinh.csv
coffee_prices_historical.csv
```

Public-source jobs cache downloaded files in `data/raw/`:

```text
faostat_qcl_asia.zip
world_bank_cmo_historical_annual.xlsx
```

## Database Writes

All loaders use `CREATE TABLE IF NOT EXISTS` and `ON DUPLICATE KEY UPDATE`. They do not drop existing tables.

Created or updated tables:

```text
coffee_long
weather
production
coffee_export
export_performance
market_trade
daily_coffee_prices
faostat_coffee_production
world_coffee_prices
export_country
```

Public sources:

- FAOSTAT QCL bulk data: Vietnam coffee area harvested and production.
- World Bank Pink Sheet annual history: Arabica and Robusta world prices.
- WITS/World Bank Comtrade HTML: Vietnam coffee exports by partner country, HS `090111`.
