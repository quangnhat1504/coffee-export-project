# Re-implementation Plan

This document tracks the clean rebuild path. The legacy `web/` app is kept in place until the replacement is verified.

## Phase 1 - Clean Backend Skeleton

Status: complete

New backend package:

```text
app/
├── config.py
├── db.py
├── main.py
├── routes/
├── services/
└── utils/
```

Canonical API surface:

```text
GET  /api/health
GET  /api/production
GET  /api/production/provinces
GET  /api/production/province/<province>
GET  /api/export
GET  /api/export/overview
GET  /api/export/countries?year=2024&limit=9
GET  /api/prices/recent?days=7
GET  /api/weather/provinces
GET  /api/weather/province/<province>?aggregate=recent12
POST /api/ai/insight
```

Run the new backend:

```bash
npm run dev:new
```

## Next Phases

## Phase 2 - Clean Frontend Shell

Status: complete

New frontend package:

```text
frontend/
├── index.html
└── static/
    ├── css/app.css
    └── js/
        ├── api.js
        ├── charts.js
        └── main.js
```

The rebuilt Flask app now serves:

```text
GET /                 -> frontend/index.html
GET /static/css/app.css
GET /static/js/main.js
```

Verification:

```text
GET  /                         200
GET  /static/js/main.js         200
POST /api/ai/insight            200
```

Current caveat: database-backed dashboard panels show degraded/empty states while the local machine cannot resolve the configured Aiven host.

## Next Phases

## Phase 3 - Clean Data Pipeline

Status: complete

New ETL package:

```text
data/
├── README.md
├── raw/
├── processed/
└── scripts/
    ├── core_transform.py
    ├── core_load.py
    ├── price_transform.py
    ├── price_load.py
    ├── sync_core.py
    ├── sync_prices.py
    └── sync_all.py
```

Commands:

```bash
npm run etl:dry-run
npm run etl:core
npm run etl:prices
npm run etl:all
```

Phase 3 ETL behavior:

```text
- Prefer inputs in data/raw/
- Fall back to legacy collect_data/
- Use CREATE TABLE IF NOT EXISTS
- Use ON DUPLICATE KEY UPDATE
- Never drop existing tables
```

Dry-run verification:

```text
core:
  coffee_long:        180
  weather:            20
  production:         20
  coffee_export:      20
  export_performance: 20
  market_trade:       57

prices:
  daily_coffee_prices rows: 2360
  date range: 2024-12-01 -> 2026-07-13
  regions: DakLak, DakNong, GiaLai, LamDong
```

Current caveat: database write verification is blocked while the local machine cannot resolve the configured Aiven host.

## Phase 4 - Public Source Ingestion

Status: in progress

Implemented:

```text
data/scripts/sync_faostat_production.py
data/scripts/sync_world_prices.py
data/scripts/sync_export_country.py
data/scripts/sync_public_sources.py
```

Commands:

```bash
npm run etl:public
npm run etl:public:dry-run
```

Public-source tables:

```text
faostat_coffee_production
world_coffee_prices
export_country
```

Dry-run verification:

```text
FAOSTAT:          64 rows, 1961-2024
World Bank:       65 rows, 1960-2024
WITS 2005-2023:   1,415 rows, 19 years, 141 partners
```

Current caveat: WITS currently returns no HS `090111` partner table for 2024, so the script skips 2024 instead of failing.

## Next Phases

1. Package the coffee prediction notebook logic into `models/`.
2. Add API smoke tests and frontend checks.
3. Replace the legacy `web/` app after the rebuilt stack is verified end-to-end.
