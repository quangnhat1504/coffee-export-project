# Vietnam Coffee Data Portal 🌱☕

A comprehensive coffee data collection, analysis, and visualization system for Vietnam coffee export market. This project includes a Flask API backend, interactive web dashboard with Chart.js visualizations, and automated data collection tools.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- pip & npm

### Installation & Run

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node.js dependencies
npm install

# 3. Run the development server (API + Frontend)
npm run dev
```

The application will automatically:
- ✅ Start Flask API on `http://localhost:5000`
- ✅ Start Frontend on `http://localhost:8080`
- ✅ Open your browser

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Components](#components)
- [Database Schema](#database-schema)
- [Data Sources](#data-sources)
- [API Documentation](#api-documentation)
- [Requirements](#requirements)
- [Contributing](#contributing)

## Project Overview

This project provides a complete solution for:
- **Web Dashboard**: Interactive data visualization with Chart.js
- **REST API**: Flask-based API for coffee export data
- **Web Scraping**: Automated collection of coffee prices from various online sources
- **Data Processing**: Transforming raw CSV data into structured database formats
- **Database Management**: Storing and managing coffee data in MySQL (Aiven Cloud)
- **Data Analysis**: Exploratory data analysis and visualization using Jupyter notebooks

## ✨ Features

### Web Dashboard
- 📊 Interactive charts with Chart.js (line charts, pie charts, dual Y-axis)
- 🌍 Real-time export data visualization (2005-2024)
- 💰 Market overview with export values and price trends
- 🌦️ Weather & climate impact analysis
- 🗺️ Export insights by country
- 📈 Time series forecasting

### Backend API
- 🔌 RESTful API with Flask
- 🗄️ MySQL database integration (Aiven Cloud)
- 📡 Real-time data endpoints
- 🔄 Automatic data interpolation for missing values
- ⚡ CORS-enabled for cross-origin requests

### Data Collection
- 🕷️ Multiple web scraping approaches (Beautiful Soup, Selenium)
- 🔄 Automated data synchronization with MySQL database
- 📊 Data processing and transformation pipelines
- 🛡️ Error handling and data validation
- 🇻🇳 Support for Vietnamese coffee market data

## 📁 Project Structure

```
coffee-export-project/
├── package.json                    # Node.js configuration & npm scripts
├── requirements.txt                # Python dependencies
├── README.md                       # Main documentation
│
├── web/                           # Web application
│   ├── backend/
│   │   └── api.py                 # Flask API with caching & compression
│   ├── scripts/
│   │   ├── data_generator.py      # Production data generator
│   │   └── news_updater.py        # News content updater
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css         # Main styles
│   │   │   └── contact-modern.css # Contact page styles
│   │   └── js/
│   │       └── script.js          # Frontend JavaScript (Chart.js + lazy loading)
│   └── templates/
│       ├── index.html             # Main dashboard
│       └── news_content.html      # News page
│
├── collect_data/                  # Data collection tools
│   ├── Data_coffee.csv            # Main coffee data
│   ├── coffee_data_sync.py        # Coffee data sync to MySQL
│   ├── weather_data_sync.py       # Weather data sync to MySQL
│   └── Thi_phan_3_thi_truong_chinh.csv
│
├── visualize/                     # Data visualization & analysis
│   ├── charts_generator.py        # Chart generation scripts
│   ├── production_analysis.ipynb  # Production scatter plot analysis
│   └── time_series_analysis.ipynb # Time series forecasting
│
└── docs/                          # Documentation
    ├── QUICK_START.md
    ├── PROJECT_STRUCTURE.md
    ├── PERFORMANCE_OPTIMIZATIONS.md
    └── ...
│
├── visualize/                     # Data visualization
│   └── scatterplot_production.ipynb
│
└── Time_Series.ipynb              # Time series analysis
```

## 🛠️ Setup & Installation

### Prerequisites

- **Python 3.8+**
- **Node.js 18+** 
- **npm** or **yarn**
- **MySQL/MariaDB database** (or Aiven Cloud MySQL)
- **Google Chrome** (for Selenium scrapers)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coffee-export-project
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **⚠️ IMPORTANT: Configure environment variables**
   
   **NEVER commit sensitive data to Git!** Follow these steps:

   a. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```
   
   b. **Edit `.env` with your actual credentials:**
   ```env
   # Database Configuration
   HOST=your-actual-database-host.aivencloud.com
   PORT=3306
   USER=your-actual-username
   PASSWORD=your-actual-password
   DB=your-database-name
   CA_PEM=C:\path\to\your\ca.pem
   
   # File Paths
   CSV_PATH=C:\Users\YourName\path\to\Data_coffee.csv
   CSV_PATH_MT=C:\Users\YourName\path\to\Thi_phan_3_thi_truong_chinh.csv
   ```

   c. **Verify `.env` is in `.gitignore`:**
   ```bash
   git status
   # .env should NOT appear in the list of files to commit
   ```

   > Security Note: The `.env` file contains sensitive credentials and is automatically ignored by Git. Only commit `.env.example` which contains template values.

5. **Verify setup**
   
   Check that the environment variables are loaded correctly:
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('.env loaded!' if os.getenv('HOST') else '.env not found')"
   ```

## 🚀 Usage

### Running the Web Application

#### Option 1: Full Stack (Recommended)
```bash
npm run dev
```
This command will:
- ✅ Start Flask API backend on port 5000
- ✅ Start frontend web server on port 8080
- ✅ Automatically open browser

#### Option 2: API Only
```bash
npm run start-api
# Or directly:
cd wed && python api.py
```

#### Option 3: Frontend Only
```bash
npm run start-frontend
# Or directly:
cd wed && npx http-server -p 8080
```

### Available npm Scripts

| Command | Description |
|---------|-------------|
| `npm install` | Install all Node.js dependencies |
| `npm run dev` | Start both API and frontend servers |
| `npm start` | Same as `npm run dev` |
| `npm run start-api` | Start Flask API only |
| `npm run start-frontend` | Start frontend server only |
| `npm run install-python` | Install Python dependencies |

### Web Scraping

#### Option 1: Simple Scraper (Beautiful Soup)
```bash
python coffee_price_scraper.py
```

#### Option 2: Selenium Scraper (for Cloudflare-protected sites)
```bash
python coffee_price_scraper_selenium.py
```

#### Option 3: Complete Scraper with Fallback
```bash
python coffee_price_scraper_final.py
```

This will:
- Attempt to scrape coffee prices from giacaphe.com
- Save results to a CSV file with timestamp
- Generate fallback data if scraping fails

### Database Synchronization

#### Using Python Script
```bash
python sync_coffee.py
```

#### Using Jupyter Notebook
```bash
jupyter notebook main_coffee.ipynb
```

The sync process will:
1. Read CSV files (`Data_coffee.csv` and `Thi_phan_3_thi_truong_chinh.csv`)
2. Transform data from wide to long format
3. Create/update database tables
4. Upsert data into MySQL database

### Data Analysis

Open and run notebooks for analysis:
```bash
jupyter notebook eda_data_coffee.ipynb
jupyter notebook main_coffee.ipynb
```

## 🧩 Components

### 1. Coffee Price Scrapers

#### `coffee_price_scraper_final.py`
- Most complete implementation
- Handles HTTP errors and Cloudflare protection
- Generates fallback data automatically
- Saves data with timestamps

#### `coffee_price_scraper_selenium.py`
- Uses Selenium WebDriver
- Bypasses Cloudflare bot protection
- Auto-manages ChromeDriver

### 2. Data Processing

#### `sync_coffee.py`
Main synchronization script that:
- Reads raw CSV data
- Transforms wide format to long format
- Creates normalized database tables
- Handles upserts for data updates

Key transformations:
- **Weather data**: Temperature, humidity, rainfall
- **Production data**: Area, output, exports
- **Export data**: Trade value, prices (world & Vietnam)
- **Market trade**: Importer countries, quantities

#### `main_coffee.ipynb`
Interactive notebook for:
- Database connection and setup
- Data transformation
- SQL query execution
- Quick data validation

### 3. Database Schema

The system creates and manages the following tables:

#### `coffee_long`
Raw data in long format (hang_muc, year, value)

#### `weather`
- Year, temperature, humidity, rain

#### `production`
- Year, area_thousand_ha, output_tons, export_tons

#### `coffee_export`
- Year, export_value_million_usd, price_world_usd_per_ton, price_vn_usd_per_ton

#### `market_trade`
- Importer, year, trade_value_million_usd, quantity_tons

## Data Sources

1. **Coffee Price Data**: 
   - Web scraping from giacaphe.com
   - Demo/fallback data for testing

2. **Production & Weather Data**: 
   - `Data_coffee.csv` - Historical coffee production, weather, and export statistics

3. **Market Trade Data**: 
   - `Thi_phan_3_thi_truong_chinh.csv` - International trade data by importer country

## Requirements

### Core Dependencies
```
pandas>=1.5.0
pymysql>=1.0.0
sqlalchemy>=2.0.0
beautifulsoup4>=4.11.0
selenium>=4.0.0
requests>=2.28.0
webdriver-manager>=3.8.0
python-dotenv>=0.19.0
```

### For Jupyter Notebooks
```
jupyter>=1.0.0
ipykernel>=6.0.0
```

Install all requirements:
```bash
pip install -r requirements.txt
```

## � Security Best Practices

### Protecting Sensitive Data

This project uses environment variables to keep credentials secure. Follow these guidelines:

1. **NEVER commit `.env` file** - It's already in `.gitignore`
2. **Always use `.env.example`** as a template
3. **Store credentials securely** - Don't share passwords in chat/email
4. **Rotate credentials** if accidentally exposed
5. **Use different passwords** for dev/staging/production

### Before Every Commit

Check what you're about to commit:
```bash
git status
git diff
```

Verify `.env` is NOT listed. If it appears, run:
```bash
git rm --cached .env
git add .gitignore
git commit -m "Remove .env from tracking"
```

### Team Collaboration

When a new team member joins:

1. They clone the repo
2. They copy `.env.example` to `.env`
3. Team lead shares credentials securely (NOT via Git)
4. They update `.env` with actual values
5. They verify with `git status` that `.env` is ignored

## Configuration

### Database Connection

Update connection settings in:
- `sync_coffee.py` - Uses `.env` file (RECOMMENDED - Secure)
- `main_coffee.ipynb` - May have hardcoded credentials (Update to use .env)

### File Paths

Update CSV file paths in `.env`:
```env
CSV_PATH=C:\path\to\Data_coffee.csv
CSV_PATH_MT=C:\path\to\Thi_phan_3_thi_truong_chinh.csv
```

Or update directly in scripts:
- `sync_coffee.py` (lines ~35, ~39)
- `main_coffee.ipynb` (line ~7, ~10)
- `unprocessing_sql.py` (line ~105)

### Selenium Settings

For Selenium scrapers, ChromeDriver is auto-managed. Optionally configure:
- Headless mode
- Timeout settings
- User agent strings

## � API Documentation

The Flask API provides RESTful endpoints for accessing coffee export data.

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### 1. Health Check
```http
GET /api/health
```
Returns API status.

**Response:**
```json
{
  "status": "healthy",
  "message": "Vietnam Coffee Data Portal API"
}
```

#### 2. Export Data (Time Series)
```http
GET /api/export
```
Returns coffee export values and prices from 2005-2024.

**Response:**
```json
{
  "success": true,
  "count": 20,
  "data": [
    {
      "year": 2023,
      "export_value_million_usd": 3500.5,
      "price_world_usd_per_ton": 4500,
      "price_vn_usd_per_ton": 4280
    }
  ],
  "metadata": {
    "interpolated": true,
    "method": "linear + backward fill for leading NaNs",
    "latest_actual_year": 2023
  }
}
```

#### 3. Production Data
```http
GET /api/production
```
Returns coffee production and export volumes by year.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "year": 2023,
      "output_tons": 1500000,
      "export_tons": 1200000
    }
  ]
}
```

#### 4. Top Export Countries
```http
GET /api/exports/top-countries?year=2024
```
Returns top coffee importing countries.

**Query Parameters:**
- `year` (optional): Filter by year, default is current year

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "country": "Germany",
      "quantity_tons": 250000,
      "percentage": 20.5
    }
  ]
}
```

#### 5. Weather Data
```http
GET /api/weather/province/{province}?aggregate=recent12
```
Returns weather data for coffee-growing provinces.

**Path Parameters:**
- `province`: Province name (e.g., `DakLak`, `GiaLai`, `LamDong`)

**Query Parameters:**
- `aggregate`: Aggregation type (`recent12` for 12-month average)

**Response:**
```json
{
  "success": true,
  "data": {
    "avg_temperature": 24.5,
    "avg_rainfall": 150.3,
    "avg_humidity": 75.2
  }
}
```

### Usage Examples

#### cURL
```bash
# Get export data
curl http://localhost:5000/api/export

# Get top countries for 2023
curl http://localhost:5000/api/exports/top-countries?year=2023

# Get weather data
curl http://localhost:5000/api/weather/province/DakLak?aggregate=recent12
```

#### JavaScript (Fetch)
```javascript
// Get export data
const response = await fetch('http://localhost:5000/api/export');
const data = await response.json();
console.log(data);
```

#### Python (requests)
```python
import requests

# Get production data
response = requests.get('http://localhost:5000/api/production')
data = response.json()
print(data)
```

## �🐛 Troubleshooting

### Web Scraping Issues

**Problem**: 403 Forbidden errors
- **Solution**: Use Selenium-based scrapers (`coffee_price_scraper_selenium.py`)

**Problem**: Cloudflare protection
- **Solution**: Ensure ChromeDriver is updated, or use fallback data mode

### Database Issues

**Problem**: Connection timeout
- **Solution**: Check SSL certificate path (`CA_PEM` in `.env`)
- **Solution**: Verify network connectivity to Aiven Cloud

**Problem**: UTF-8 encoding errors
- **Solution**: Ensure database uses `utf8mb4` charset
- **Solution**: Use `encoding='utf-8-sig'` when reading CSV files

## 📝 Notes

- The website `giacaphe.com` uses Cloudflare protection - Selenium is required
- Database credentials are hardcoded in some files - consider using environment variables
- Some scripts have hardcoded file paths - update according to your system
- SSL certificate required for Aiven Cloud MySQL connections

## 🤝 Contributing

This is an academic project for ADY 201 (Semester 3). For contributions:
1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📄 License

Educational project - use as reference or learning material.

## 👥 Authors

ADY 201 - Team 7

---

**Note**: This project is part of Academic Data Science coursework. Some data sources may require proper attribution or permission for commercial use.
