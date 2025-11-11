"""
Weather Data Collector - DAILY VERSION
Fetches historical daily weather data from Open-Meteo API and stores in Aiven MySQL database
"""

import requests
import pandas as pd
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import time

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

load_dotenv()

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", "3306"))
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")
CA_CERT = os.getenv("CA_CERT", "")

if not all([HOST, PORT, USER, PASSWORD, DB]):
    raise SystemExit("Missing env vars. Set HOST, PORT, USER, PASSWORD, DB in .env")

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

engine = create_engine(
    url,
    connect_args={"ssl_disabled": True},
    pool_pre_ping=True,
    pool_recycle=1800,
)

print("Connected to Aiven MySQL")

# ============================================================================
# CONFIGURATION
# ============================================================================

locations = {
    "DakLak": (12.6663, 108.0383),
    "GiaLai": (13.9833, 108.0),
    "DakNong": (12.0086, 107.6907),
    "KonTum": (14.3545, 108.0076),
    "LamDong": (11.5475, 107.8070)
}

# Daily weather variables
daily_vars = "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean"

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def init_database():
    """Create weather_data_daily table if not exists"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS weather_data_daily (
        id INT AUTO_INCREMENT PRIMARY KEY,
        province VARCHAR(100) NOT NULL,
        date DATE NOT NULL,
        temperature_mean DECIMAL(5, 2),
        temperature_max DECIMAL(5, 2),
        temperature_min DECIMAL(5, 2),
        precipitation_sum DECIMAL(7, 2),
        humidity_mean DECIMAL(5, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_province_date (province, date),
        INDEX idx_province_date (province, date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("Table 'weather_data_daily' ready")


def get_last_date_in_db(province):
    """Get the last date we have data for a specific province"""
    query = """
    SELECT MAX(date) as last_date
    FROM weather_data_daily 
    WHERE province = :province
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {"province": province}).fetchone()
    
    if result and result[0]:
        return result[0]  # Returns date object
    else:
        return date(2004, 12, 31)  # Will start from 2005-01-01


def fetch_weather_data_daily(province, lat, lon, start_date, end_date):
    """Fetch daily weather data from Open-Meteo API"""
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily={daily_vars}"
        f"&timezone=Asia%2FBangkok"
    )
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {province}: {e}")
        return None


def save_to_database(province, daily_data):
    """Save daily weather data to MySQL database, skip duplicates"""
    if not daily_data or 'daily' not in daily_data:
        print(f"No data to save for {province}")
        return 0
    
    df = pd.DataFrame(daily_data['daily'])
    
    print(f"  Preparing {len(df)} daily records...")
    
    insert_query = """
    INSERT IGNORE INTO weather_data_daily 
    (province, date, temperature_mean, temperature_max, temperature_min, 
     precipitation_sum, humidity_mean)
    VALUES (:province, :date, :temperature_mean, :temperature_max, :temperature_min,
            :precipitation_sum, :humidity_mean)
    """
    
    with engine.connect() as conn:
        count_before = conn.execute(
            text("SELECT COUNT(*) FROM weather_data_daily WHERE province = :prov"),
            {"prov": province}
        ).scalar()
        
        for _, row in df.iterrows():
            conn.execute(text(insert_query), {
                'province': province,
                'date': row['time'],
                'temperature_mean': row.get('temperature_2m_mean'),
                'temperature_max': row.get('temperature_2m_max'),
                'temperature_min': row.get('temperature_2m_min'),
                'precipitation_sum': row.get('precipitation_sum'),
                'humidity_mean': row.get('relative_humidity_2m_mean')
            })
        
        conn.commit()
        
        count_after = conn.execute(
            text("SELECT COUNT(*) FROM weather_data_daily WHERE province = :prov"),
            {"prov": province}
        ).scalar()
    
    inserted_count = count_after - count_before
    duplicate_count = len(df) - inserted_count
    
    print(f"  ✓ {inserted_count} new records, {duplicate_count} duplicates skipped")
    return inserted_count


# ============================================================================
# MAIN UPDATE FUNCTION
# ============================================================================

def update_weather_data():
    """Main function to update daily weather data"""
    print("Starting DAILY weather data collection...")
    print("=" * 70)
    
    init_database()
    
    today = date.today()
    # Don't fetch today's data (incomplete)
    end_date = today - timedelta(days=1)
    
    total_new_records = 0
    total_provinces = len(locations)
    current = 0
    
    for province, (lat, lon) in locations.items():
        current += 1
        print(f"\n[{current}/{total_provinces}] Processing: {province}")
        
        last_date = get_last_date_in_db(province)
        start_date = last_date + timedelta(days=1)
        
        if start_date > end_date:
            print(f"  Already up to date (last: {last_date})")
            continue
        
        print(f"  Last date in DB: {last_date}")
        print(f"  Fetching from {start_date} to {end_date}...")
        
        # Fetch in yearly chunks to avoid timeout
        current_start = start_date
        
        while current_start <= end_date:
            # Fetch 1 year at a time
            chunk_end = min(
                current_start + timedelta(days=365),
                end_date
            )
            
            days_in_chunk = (chunk_end - current_start).days + 1
            print(f"  → Fetching {days_in_chunk} days ({current_start} to {chunk_end})...")
            
            # Fetch daily data
            data = fetch_weather_data_daily(
                province, lat, lon, 
                current_start.strftime('%Y-%m-%d'),
                chunk_end.strftime('%Y-%m-%d')
            )
            
            if data:
                new_records = save_to_database(province, data)
                total_new_records += new_records
            else:
                print(f"  Failed to fetch data")
                break
            
            # Move to next chunk
            current_start = chunk_end + timedelta(days=1)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print(f"✓ Update complete. Total new daily records: {total_new_records}")
    return total_new_records


# ============================================================================
# QUERY FUNCTIONS
# ============================================================================

def view_data_summary():
    """View summary statistics of daily weather data"""
    query = """
    SELECT 
        province,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records,
        ROUND(AVG(temperature_mean), 2) as avg_temp,
        ROUND(AVG(temperature_max), 2) as avg_temp_max,
        ROUND(AVG(temperature_min), 2) as avg_temp_min,
        ROUND(AVG(precipitation_sum), 2) as avg_precip,
        ROUND(AVG(humidity_mean), 2) as avg_humid
    FROM weather_data_daily
    GROUP BY province
    ORDER BY province
    """
    
    return pd.read_sql(query, engine)


def view_recent_data(province=None, limit=30):
    """View recent daily weather data"""
    if province:
        query = """
        SELECT province, date, temperature_mean, temperature_max, temperature_min,
               precipitation_sum, humidity_mean
        FROM weather_data_daily
        WHERE province = :province
        ORDER BY date DESC
        LIMIT :limit
        """
        return pd.read_sql(query, engine, params={"province": province, "limit": limit})
    else:
        query = f"""
        SELECT province, date, temperature_mean, temperature_max, temperature_min,
               precipitation_sum, humidity_mean
        FROM weather_data_daily
        ORDER BY date DESC, province
        LIMIT {limit}
        """
        return pd.read_sql(query, engine)


def get_total_records():
    """Get total number of daily records"""
    query = "SELECT COUNT(*) as total FROM weather_data_daily"
    result = pd.read_sql(query, engine)
    return result['total'][0]


if __name__ == "__main__":
    import sys
    
    # Check if user wants to clear data first
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        print("⚠ Clearing all existing daily data...")
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM weather_data_daily"))
            conn.commit()
            print(f"✓ Deleted {result.rowcount} records")
        print()
    
    # Run the update
    update_weather_data()
    
    # Show summary
    print("\n" + "=" * 70)
    print("DAILY DATA SUMMARY:")
    print("=" * 70)
    print(view_data_summary().to_string(index=False))
    
    print(f"\nTotal daily records: {get_total_records()}")
    
    print("\n" + "=" * 70)
    print("Recent Daily Records (10):")
    print("=" * 70)
    print(view_recent_data(limit=10).to_string(index=False))
