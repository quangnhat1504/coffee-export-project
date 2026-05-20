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

Below is the structured directory tree of the project with a brief description of each component:

```text
Project_ADY_201m/
├── app/                      👉 BACKEND (Flask Application Core)
│   ├── routes/               │   ├── API endpoint routes serving frontend data requests
│   ├── services/             │   ├── Business logic processors (AI, Weather, Price, Production)
│   ├── utils/                │   ├── Helper utilities (serialization, timeseries processing)
│   ├── config.py             │   ├── App settings loaded from environmental variables
│   ├── db.py                 │   └── SQL connection pool & engine setup for Aiven MySQL
│   └── __init__.py           └── Flask factory, register blueprints & error handlers
│
├── frontend/                 👉 FRONTEND (Dashboard Interface)
│   ├── static/               │   ├── Client assets: custom CSS and modular vanilla JS scripts
│   └── index.html            └── Single Page Dashboard containing KPI nodes & Chart containers
│
├── api/                      👉 VERCEL INTEGRATION
│   └── index.py              └── Entrypoint wrapper exposing WSGI Flask app for Serverless
│
├── data/                     👉 DATA INGESTION & ETL PIPELINES
│   ├── raw/                  │   ├── Source spreadsheets (.csv, .xlsx, .zip)
│   ├── processed/            │   ├── Output directory for parsed local data (tracked via .gitkeep)
│   └── scripts/              └── Core, price, and public source ETL ingestion scripts
│
├── tests/                    👉 TESTING SUITE
│   └── e2e/                  └── E2E Web integration tests built with Playwright
│
├── scripts/                  👉 OPERATIONAL UTILITIES
│   └── auto_update_data.py   └── Service scripts (e.g. daily cron to fetch province coffee prices)
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

The project uses Flask as both the API server and the static dashboard server. For Vercel, `api/index.py` exposes the Flask `app`, and `vercel.json` rewrites all requests to that serverless entrypoint.

### 1. Vercel Project Settings
In the Vercel Project dashboard, set:
* **Root Directory**: `Project_ADY_201m`

### 2. Environment Variables
Add the following Environment Variables in **Vercel Settings -> Environment Variables** (Vercel does not read your local `.env` file):

```env
HOST=your-database-host.com
PORT=3306
USER=your-username
PASSWORD=your-password
DB=your-database-name
CA_CERT=-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----
```

> [!TIP]
> **CA Certificate Configuration:**
> * You can use either `CA_CERT` or `CA_PEM` as the key.
> * When pasting the certificate value, copy the entire block including `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----`.
> * The backend is designed to handle both actual newlines and literal escaped newlines (`\n` or `\\n`) robustly.

### 3. Database Firewall (Crucial for Aiven/Cloud DBs)
Since Vercel uses dynamic IP addresses, you **must allow connections from all IPs** in your database firewall settings:
* In your **Aiven Console** (or other DB provider), go to **IP Allowlist** / **Allowed IP Addresses**.
* Add the rule `0.0.0.0/0` (with a description like `Vercel Serverless`).
* Without this, Vercel will time out trying to connect and return `503 Service Unavailable`.

### 4. Verification
After deploying/redeploying, verify your setup by visiting:
```text
https://your-app.vercel.app/api/health
```

* **If `database.connected` is `true`**: Deployment is fully successful!
* **If `database.connected` is `false`**: Check the `database.message` in the JSON response or view Vercel's **Runtime Logs** for the connection error trace.
* **If `/api/health` returns `404`**: Vercel is not using the correct project root directory or the Flask entrypoint.

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
