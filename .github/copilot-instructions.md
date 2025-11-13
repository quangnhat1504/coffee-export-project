## Quick orientation for AI coding agents

This repo is the "Vietnam Coffee Data Portal": a small full-stack project combining a Flask API, static frontend (Chart.js), and Python data collection/processing that syncs CSVs into MySQL.

Keep changes small and focused. Edit these files when you change behavior: `web/backend/api.py`, `collect_data/sync_coffee.py`, and files under `collect_data/` and `visualize/`.

Core facts (do NOT guess):
- API server: `web/backend/api.py` (Flask). It creates a SQLAlchemy engine from values in `.env` and expects `HOST/USER/PASSWORD/PORT/DB`.
- Data sync: `collect_data/sync_coffee.py` reads `collect_data/Data_coffee.csv` and `Thi_phan_3_thi_truong_chinh.csv`, normalizes to `coffee_long`, then pivots into tables `weather`, `production`, `coffee_export`, `market_trade`.
- Dev entrypoint: `npm run dev` (runs `web/backend/api.py`). See `package.json` scripts for other commands.
- Environment: sensitive credentials live in `.env` and an example exists as `.env.example`. Never add secrets to git.

What to change and how (concrete patterns)
- When you add or change API endpoints, update `web/backend/api.py` and add a matching route in `README.md` / `docs/PROJECT_STRUCTURE.md`.
- Use the existing `safe_db_operation` decorator for DB-backed endpoints to get consistent error payloads and status codes.
- Cache responses with `@cache.cached(timeout=...)` for read-heavy endpoints (see `get_weather_by_province`). Follow the existing pattern: cache + decorator + pandas read_sql.
- DB connections: prefer `engine = create_db_engine()` pattern from `api.py` or reuse the connection logic in `collect_data/sync_coffee.py` when writing scripts. Respect SSL vs non-SSL fallback logic.

Developer commands and verification (copy-paste safe)
- Install deps: `pip install -r requirements.txt` and `npm install`.
- Start dev stack (API + frontend): `npm run dev` (runs `web/backend/api.py` on port 5000).
- API health check: GET `http://localhost:5000/api/health` (or `npm run test:api`).
- Run data sync locally: `python collect_data/sync_coffee.py` (requires `.env` configured and CSVs present).

Conventions and gotchas found in the codebase
- Paths: many scripts load `.env` with a relative path (e.g., `load_dotenv(dotenv_path='../.env')` or `../../.env`). Prefer running scripts from repository root or adjust working directory in CI tasks.
- Encoding: scripts attempt to set stdout to UTF-8 and read CSVs with `utf-8-sig` — preserve this when adding I/O.
- Column names: `sync_coffee.py` expects specific CSV column names (e.g., "Hang_muc", year columns as digits, and in market CSV: `Year`, `Importer`, `Trade Value(million_USD)`, `Quantity(tons)`). Changes to CSV format must update the cleaning logic.
- DB schema management: `sync_coffee.py` drops and recreates tables during each run (intentional). If adding migrations, avoid destructive behavior or add a flag to keep existing tables.

Integration points to be careful with
- MySQL/Aiven: the code tries SSL first (via `CA_CERT`), then falls back to non-SSL. Tests and CI should provide a test MySQL instance or mock DB calls.
- Selenium scrapers: some collectors use Selenium and WebDriver; these need Chrome available in CI or use alternate scraping strategies.

Files to inspect when debugging or extending features
- API behavior & DB patterns: `web/backend/api.py`
- Data ETL & schema: `collect_data/sync_coffee.py`
- Scrapers & data sources: files under `collect_data/` (e.g., coffee scrapers and `weather_data_sync.py`).
- Frontend wiring: `web/templates/index.html` and `web/static/js/script.js` (Chart.js usage).
- Docs & quick-start: `README.md`, `docs/QUICK_START.md`, `docs/PROJECT_STRUCTURE.md` — keep these in sync with code changes.

When proposing edits or PRs
- Provide a short summary: what changed, why (bugfix/feature), files edited, and a manual verification checklist (e.g., "Run `npm run dev`, hit `/api/health`, run `python collect_data/sync_coffee.py`").
- If DB changes are required, include SQL DDL or migration steps and a non-destructive dev path (local test DB details).

If anything in this file is unclear or you need more examples from the repo, ask and I'll expand the instructions with exact code snippets and test commands.
