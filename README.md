# Coffee Database Project (ADY 201)

A comprehensive coffee data collection, processing, and analysis system. This project includes web scraping tools for coffee price data, data processing pipelines, and MySQL database integration for storing and analyzing coffee market information.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [🔐 Security](#security)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Components](#components)
- [Database Schema](#database-schema)
- [Data Sources](#data-sources)
- [Requirements](#requirements)
- [Contributing](#contributing)

## Project Overview

This project provides a complete solution for:
- **Web Scraping**: Automated collection of coffee prices from various online sources
- **Data Processing**: Transforming raw CSV data into structured database formats
- **Database Management**: Storing and managing coffee data in MySQL (Aiven Cloud)
- **Data Analysis**: Exploratory data analysis and visualization using Jupyter notebooks

## Features

- Multiple web scraping approaches (Beautiful Soup, Selenium)
- Automated data synchronization with MySQL database
- Data processing and transformation pipelines
- Fallback data generation for testing
- Exploratory data analysis capabilities
- Error handling and data validation
- Support for Vietnamese coffee market data
- **🔐 Secure credential management using environment variables**

## 🔐 Security

**IMPORTANT:** This project uses environment variables to protect sensitive information like database passwords and API keys.

### Key Security Features:
- ✅ All credentials stored in `.env` file (not committed to Git)
- ✅ `.env.example` template provided for setup guidance
- ✅ `.gitignore` configured to exclude sensitive files
- ✅ SSL/TLS support for database connections
- ✅ No hardcoded passwords or API keys in source code

### Quick Security Check:
```powershell
# Verify .env is ignored by Git
git check-ignore -v .env
# Should output: .gitignore:5:*.env    .env

# Verify .env is not tracked
git status
# .env should NOT appear in the list
```

📖 **For detailed security guidelines, see [SECURITY.md](SECURITY.md)**

## Project Structure

```
coffee_dabase/
├── Data Files
│   ├── Data_coffee.csv                           # Main coffee data (production, weather, export)
│   ├── Thi_phan_3_thi_truong_chinh.csv          # Market trade data
│   ├── coffee_prices_demo.csv                    # Demo coffee price data
│   └── processed_coffee_data.csv                 # Processed data output
│
├── Web Scrapers
│   ├── coffee_price_scraper.py                   # Basic Beautiful Soup scraper
│   ├── coffee_price_scraper_selenium.py         # Selenium-based scraper (bypass Cloudflare)
│   ├── coffee_price_scraper_final.py            # Complete scraper with error handling
│   ├── coffee_price_scraper_simple.py           # Simplified scraper
│   ├── real_scraper.py                          # Production scraper
│   ├── simple_scraper.py                        # Minimal scraper implementation
│   └── coffee_price_demo.py                     # Demo scraper with sample data
│
├── Database Sync
│   ├── sync_coffee.py                           # Main data synchronization script
│   ├── main_coffee.ipynb                        # Notebook for database operations
│   └── unprocessing_sql.py                      # Raw data processing script
│
├── Analysis Notebooks
│   ├── main_coffee.ipynb                        # Main analysis notebook
│   ├── eda_data_coffee.ipynb                    # Exploratory data analysis
│   └── beautiful_soup_4_demo.ipynb              # Beautiful Soup demonstration
│
├── Testing
│   ├── test_scraper.py                          # Scraper tests
│   ├── test_selenium.py                         # Selenium tests
│   └── test.py                                  # General tests
│
└── Documentation
    ├── README.md                                 # This file
    └── HUONG_DAN_SU_DUNG_COFFEE_SCRAPER.md     # Vietnamese scraper guide
```

## Setup & Installation

### Prerequisites

- Python 3.8+
- MySQL/MariaDB database (or Aiven Cloud MySQL)
- Google Chrome (for Selenium scrapers)
- ChromeDriver (auto-installed with webdriver-manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coffee-export-project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **⚠️ IMPORTANT: Configure environment variables**
   
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

4. **Verify setup**
   
   Check that the environment variables are loaded correctly:
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('.env loaded!' if os.getenv('HOST') else '.env not found')"
   ```

## Usage

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

## 🐛 Troubleshooting

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
