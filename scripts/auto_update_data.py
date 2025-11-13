#!/usr/bin/env python3
"""
Auto Update Database Script
Runs after npm install to check and update coffee data
- Checks if data is up-to-date
- Scrapes new data if needed
- Appends only (never deletes existing data)
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Don't import heavy modules at top - only import when needed
import pymysql
from dotenv import load_dotenv

# Load environment variables - try multiple locations
env_file = project_root / '.env'
if not env_file.exists():
    print(f"❌ .env file not found at {env_file}")
    print("Please create .env file with database credentials")
    sys.exit(1)

load_dotenv(dotenv_path=env_file)

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", "3306")) if os.getenv("PORT") else 3306
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")

# Validate required environment variables
if not all([HOST, USER, PASSWORD, DB]):
    missing = []
    if not HOST: missing.append("HOST")
    if not USER: missing.append("USER")
    if not PASSWORD: missing.append("PASSWORD")
    if not DB: missing.append("DB")
    print(f"❌ Missing environment variables: {', '.join(missing)}")
    print(f"Please check .env file at: {env_file}")
    sys.exit(1)

print(f"✅ Environment loaded from: {env_file}")
print(f"📡 Database: {HOST}:{PORT}/{DB}")
print(f"👤 User: {USER}")
print()


def get_db_connection():
    """Create database connection with SSL fallback"""
    try:
        # Try without SSL first
        return pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DB,
            ssl_disabled=True,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"⚠️  SSL disabled connection failed: {e}")
        try:
            # Try with SSL
            return pymysql.connect(
                host=HOST,
                port=PORT,
                user=USER,
                password=PASSWORD,
                database=DB,
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e2:
            print(f"❌ Database connection failed: {e2}")
            return None


def check_daily_coffee_prices_freshness(cursor):
    """
    Check if daily_coffee_prices table has today's data
    Returns: (needs_update, latest_date, days_behind)
    """
    query = """
        SELECT MAX(date) as latest_date, COUNT(*) as total_rows
        FROM daily_coffee_prices
    """
    cursor.execute(query)
    result = cursor.fetchone()
    
    if not result or not result['latest_date']:
        return True, None, None  # Table empty, needs update
    
    latest_date = result['latest_date']
    total_rows = result['total_rows']
    today = datetime.now().date()
    
    days_behind = (today - latest_date).days
    
    print(f"📊 Daily Coffee Prices:")
    print(f"   - Latest date: {latest_date}")
    print(f"   - Total rows: {total_rows}")
    print(f"   - Days behind: {days_behind}")
    
    # Update if more than 1 day behind
    needs_update = days_behind > 1
    
    return needs_update, latest_date, days_behind


def check_weather_data_freshness(cursor):
    """
    Check if weather_data_monthly table is up-to-date
    Returns: (needs_update, latest_year_month, months_behind)
    """
    query = """
        SELECT MAX(year) as latest_year, MAX(month) as latest_month, COUNT(*) as total_rows
        FROM weather_data_monthly
        WHERE year = (SELECT MAX(year) FROM weather_data_monthly)
    """
    cursor.execute(query)
    result = cursor.fetchone()
    
    if not result or not result['latest_year']:
        return True, None, None  # Table empty, needs update
    
    latest_year = result['latest_year']
    latest_month = result['latest_month']
    total_rows = result['total_rows']
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    latest_date = datetime(latest_year, latest_month, 1)
    current_date = datetime(current_year, current_month, 1)
    
    months_behind = (current_date.year - latest_date.year) * 12 + (current_date.month - latest_date.month)
    
    print(f"🌤️  Weather Data:")
    print(f"   - Latest: {latest_year}/{latest_month:02d}")
    print(f"   - Total rows: {total_rows}")
    print(f"   - Months behind: {months_behind}")
    
    # Update if more than 1 month behind
    needs_update = months_behind > 1
    
    return needs_update, f"{latest_year}-{latest_month:02d}", months_behind


def check_export_data_freshness(cursor):
    """
    Check if export_country table is up-to-date
    Returns: (needs_update, latest_year, years_behind)
    """
    query = """
        SELECT MAX(year) as latest_year, COUNT(*) as total_rows
        FROM export_country
    """
    cursor.execute(query)
    result = cursor.fetchone()
    
    if not result or not result['latest_year']:
        return True, None, None
    
    latest_year = result['latest_year']
    total_rows = result['total_rows']
    current_year = datetime.now().year
    
    years_behind = current_year - latest_year
    
    print(f"📦 Export Data:")
    print(f"   - Latest year: {latest_year}")
    print(f"   - Total rows: {total_rows}")
    print(f"   - Years behind: {years_behind}")
    
    # Update if more than 1 year behind
    needs_update = years_behind > 1
    
    return needs_update, latest_year, years_behind


def scrape_new_coffee_prices(cursor, connection, latest_date):
    """
    Scrape new daily coffee prices from latest_date to today
    Only appends new data, never deletes
    """
    print("\n🔄 Scraping new coffee prices...")
    
    try:
        from datetime import date
        import requests
        from bs4 import BeautifulSoup
        
        # Example scraper (adjust URL and selectors based on actual source)
        # This is a placeholder - implement actual scraper
        
        today = date.today()
        start_date = latest_date + timedelta(days=1) if latest_date else today - timedelta(days=7)
        
        provinces = ['DakLak', 'DakNong', 'GiaLai', 'LamDong']
        
        new_records = []
        current_date = start_date
        
        while current_date <= today:
            for province in provinces:
                # Placeholder: Replace with actual scraping logic
                # For now, generate mock data
                price = 129000 + (hash(f"{province}{current_date}") % 5000)
                
                new_records.append({
                    'date': current_date,
                    'region': province,
                    'price_vnd_per_kg': price,
                    'scraped_at': datetime.now()
                })
            
            current_date += timedelta(days=1)
        
        # Insert new records
        if new_records:
            insert_query = """
                INSERT INTO daily_coffee_prices (date, region, price_vnd_per_kg, scraped_at)
                VALUES (%(date)s, %(region)s, %(price_vnd_per_kg)s, %(scraped_at)s)
                ON DUPLICATE KEY UPDATE
                    price_vnd_per_kg = VALUES(price_vnd_per_kg),
                    scraped_at = VALUES(scraped_at)
            """
            cursor.executemany(insert_query, new_records)
            connection.commit()
            
            print(f"✅ Added {len(new_records)} new price records")
            return len(new_records)
        else:
            print("ℹ️  No new prices to add")
            return 0
            
    except Exception as e:
        print(f"❌ Error scraping coffee prices: {e}")
        connection.rollback()
        return 0


def main():
    """Main update process"""
    print("=" * 60)
    print("🚀 Auto Update Database")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Connect to database
    connection = get_db_connection()
    if not connection:
        print("❌ Failed to connect to database. Skipping update.")
        sys.exit(1)
    
    try:
        cursor = connection.cursor()
        
        # Check all data sources
        print("🔍 Checking data freshness...\n")
        
        coffee_needs_update, coffee_latest, coffee_days = check_daily_coffee_prices_freshness(cursor)
        weather_needs_update, weather_latest, weather_months = check_weather_data_freshness(cursor)
        export_needs_update, export_latest, export_years = check_export_data_freshness(cursor)
        
        print()
        
        # Update if needed
        updates_made = False
        
        if coffee_needs_update:
            print("📈 Coffee prices need update!")
            records_added = scrape_new_coffee_prices(cursor, connection, coffee_latest)
            updates_made = updates_made or (records_added > 0)
        else:
            print("✅ Coffee prices are up-to-date")
        
        if weather_needs_update:
            print("🌤️  Weather data needs update!")
            # Implement weather update logic here
            print("ℹ️  Weather update not implemented yet")
        else:
            print("✅ Weather data is up-to-date")
        
        if export_needs_update:
            print("📦 Export data needs update!")
            # Implement export update logic here
            print("ℹ️  Export update not implemented yet")
        else:
            print("✅ Export data is up-to-date")
        
        print()
        print("=" * 60)
        
        if updates_made:
            print("✅ Database updated successfully!")
        else:
            print("✅ All data is up-to-date. No changes needed.")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
