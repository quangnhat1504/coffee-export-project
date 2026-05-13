# Vietnam Coffee Data Portal

Dashboard and API for Vietnam coffee production, export, province prices, weather impact, and AI-generated market insight.

## Current Stack

- Backend: Flask app in `app/`
- Frontend: static dashboard in `frontend/`, served by Flask
- Charts: Chart.js loaded from CDN
- Database: MySQL-compatible database through SQLAlchemy/PyMySQL
- ETL: Python scripts in `data/scripts/`
- Tests: Playwright e2e tests in `tests/e2e/`

## Quick Start

Prerequisites:

- Python 3.10+
- Node.js 18+
- MySQL-compatible database credentials

Install dependencies:

```bash
pip install -r requirements.txt
npm install
```

Create local environment config:

```bash
cp .env.example .env
```

Fill in `.env` with your database credentials and optional AI settings.

Run the app:

```bash
npm run dev
```

Open:

```text
http://127.0.0.1:5000/
```

Health check:

```bash
npm run health
```

## Main Commands

```bash
npm run dev                 # Start Flask backend and frontend
npm run test:e2e            # Run Playwright tests
npm run etl:dry-run         # Validate ETL transforms without DB writes
npm run etl:core            # Sync annual coffee, weather, and export CSV data
npm run etl:prices          # Sync daily province price CSV data
npm run etl:public          # Sync public FAOSTAT, World Bank, and WITS sources
npm run etl:all             # Run core and price ETL
npm run update:data         # Check and append fresh daily price records
```

## Project Layout

```text
app/                    Flask application, routes, services, DB setup
frontend/               Dashboard HTML, CSS, and browser JavaScript
data/raw/               Source CSV/cache files for ETL
data/scripts/           Clean ETL pipeline
scripts/                Operational helper scripts
tests/e2e/              Playwright API and UI tests
```

## Required Data Files

The ETL pipeline expects these files in `data/raw/`:

```text
Data_coffee.csv
Thi_phan_3_thi_truong_chinh.csv
coffee_prices_historical.csv
```

Public-source ETL jobs cache downloaded files in `data/raw/`.

## Environment Variables

Required:

```env
HOST=your-database-host.com
PORT=3306
USER=your-username
PASSWORD=your-password
DB=your-database-name
```

Optional:

```env
CA_PEM=C:\path\to\ca.pem
AI_BASE_URL=http://localhost:20128/v1
AI_API_KEY=your-ai-api-key
AI_MODEL=coding-main
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=0
```

## Vercel Deployment

The project uses Flask as both the API server and the static dashboard server. For
Vercel, `api/index.py` exposes the Flask `app`, and `vercel.json` rewrites all
requests to that serverless entrypoint.

In Vercel Project Settings:

```text
Root Directory: Project_ADY_201m
```

Add the same required database variables from `.env` to Vercel Environment
Variables. Vercel does not read your local `.env` file:

```env
HOST=...
PORT=3306
USER=...
PASSWORD=...
DB=...
CA_PEM=...     # only if your database requires a CA certificate
```

After redeploying, verify:

```text
https://your-app.vercel.app/api/health
```

If `database.connected` is `false`, the API is deployed but the Vercel database
environment is missing or cannot connect to the database. If `/api/health` is
`404`, Vercel is not using this project root or the Flask serverless entrypoint.

## API Surface

Base URL:

```text
http://127.0.0.1:5000/api
```

Key endpoints:

```text
GET  /api/health
GET  /api/production
GET  /api/export/overview
GET  /api/export/countries?limit=9
GET  /api/prices/recent?days=7
GET  /api/weather/province/DakLak?aggregate=recent12
POST /api/ai/insight
```

## Notes

- `.env` and certificates are ignored by Git.
- The app serves the dashboard and API from the same Flask server on port `5000`.
- Legacy `web/`, notebook, and old collection-script folders were removed after the rebuilt stack passed e2e tests.
