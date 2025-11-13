"""
Weather Data Collector for Coffee Growing Regions
Fetches historical weather data from Open-Meteo API and stores in Aiven MySQL database
Automatically continues from the last date in database to avoid duplicates
"""

import requests
import pandas as pd
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

# Find .env in parent directory (project root)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

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

# Disable SSL verification for simplicity
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
    "LamDong": (11.5475, 107.8070)
}

daily_vars = "temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean"

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def init_database():
    """Create weather_data_monthly table if not exists"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS weather_data_monthly (
        id INT AUTO_INCREMENT PRIMARY KEY,
        province VARCHAR(100) NOT NULL,
        year INT NOT NULL,
        month INT NOT NULL,
        temperature_mean DECIMAL(5, 2),
        precipitation_sum DECIMAL(7, 2),
        humidity_mean DECIMAL(5, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_province_year_month (province, year, month),
        INDEX idx_province_date (province, year, month)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("Table 'weather_data_monthly' ready")


def clear_all_data():
    """Delete all data from weather_data_monthly table"""
    query = "DELETE FROM weather_data_monthly"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        conn.commit()
        print(f"Deleted {result.rowcount} records from weather_data_monthly")


def get_last_month_in_db(province):
    """Get the last year-month we have data for a specific province"""
    query = """
    SELECT MAX(year) as last_year, MAX(month) as last_month
    FROM weather_data_monthly 
    WHERE province = :province
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {"province": province}).fetchone()
    
    if result and result[0]:
        return result[0], result[1]  # (year, month)
    else:
        return 2004, 12  # Will start from January 2005 (next month)


def fetch_weather_data_monthly(province, lat, lon, start_date, end_date):
    """Fetch monthly weather data from Open-Meteo API"""
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


def aggregate_to_monthly(daily_data):
    """Aggregate daily data to monthly averages"""
    if not daily_data or 'daily' not in daily_data:
        return []
    
    df = pd.DataFrame(daily_data['daily'])
    df['time'] = pd.to_datetime(df['time'])
    df['year'] = df['time'].dt.year
    df['month'] = df['time'].dt.month
    
    # Group by year-month and aggregate
    monthly = df.groupby(['year', 'month']).agg({
        'temperature_2m_mean': 'mean',
        'precipitation_sum': 'sum',
        'relative_humidity_2m_mean': 'mean'
    }).reset_index()
    
    return monthly.to_dict('records')


def save_to_database(province, monthly_records):
    """Save monthly weather data to MySQL database, skip duplicates"""
    if not monthly_records:
        print(f"No data to save for {province}")
        return 0
    
    print(f"  Preparing {len(monthly_records)} monthly records...")
    print(f"  Inserting to database...")
    
    insert_query = """
    INSERT IGNORE INTO weather_data_monthly 
    (province, year, month, temperature_mean, precipitation_sum, humidity_mean)
    VALUES (:province, :year, :month, :temperature_mean, :precipitation_sum, :humidity_mean)
    """
    
    with engine.connect() as conn:
        count_before = conn.execute(
            text("SELECT COUNT(*) FROM weather_data_monthly WHERE province = :prov"),
            {"prov": province}
        ).scalar()
        
        for record in monthly_records:
            conn.execute(text(insert_query), {
                'province': province,
                'year': int(record['year']),
                'month': int(record['month']),
                'temperature_mean': record.get('temperature_2m_mean'),
                'precipitation_sum': record.get('precipitation_sum'),
                'humidity_mean': record.get('relative_humidity_2m_mean')
            })
        
        conn.commit()
        
        count_after = conn.execute(
            text("SELECT COUNT(*) FROM weather_data_monthly WHERE province = :prov"),
            {"prov": province}
        ).scalar()
    
    inserted_count = count_after - count_before
    duplicate_count = len(monthly_records) - inserted_count
    
    print(f"{province}: {inserted_count} new records, {duplicate_count} duplicates skipped")
    return inserted_count


# ============================================================================
# MAIN UPDATE FUNCTION
# ============================================================================

def update_weather_data():
    """Main function to update monthly weather data"""
    print("Starting monthly weather data update...")
    print("=" * 60)
    
    init_database()
    
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    total_new_records = 0
    total_provinces = len(locations)
    current = 0
    
    for province, (lat, lon) in locations.items():
        current += 1
        print(f"\n[{current}/{total_provinces}] Processing: {province}")
        
        last_year, last_month = get_last_month_in_db(province)
        
        # Calculate next month to fetch
        if last_month == 12:
            start_year = last_year + 1
            start_month = 1
        else:
            start_year = last_year
            start_month = last_month + 1
        
        # Don't fetch current month (incomplete data)
        if start_year > current_year or (start_year == current_year and start_month >= current_month):
            print(f"  Already up to date (last: {last_year}-{last_month:02d})")
            continue
        
        # Fetch data in yearly chunks
        while start_year < current_year or (start_year == current_year and start_month < current_month):
            # Fetch up to 12 months (1 year) at a time
            end_year = start_year
            end_month = min(start_month + 11, 12)
            
            # Don't go past current month
            if end_year == current_year and end_month >= current_month:
                end_month = current_month - 1
            
            start_date_str = f"{start_year}-{start_month:02d}-01"
            
            # Get last day of end month
            if end_month == 12:
                end_date_str = f"{end_year}-12-31"
            else:
                import calendar
                last_day = calendar.monthrange(end_year, end_month)[1]
                end_date_str = f"{end_year}-{end_month:02d}-{last_day}"
            
            months_in_chunk = (end_year - start_year) * 12 + (end_month - start_month + 1)
            print(f"  Fetching {months_in_chunk} months ({start_date_str} to {end_date_str})...")
            
            # Fetch daily data
            data = fetch_weather_data_monthly(province, lat, lon, start_date_str, end_date_str)
            
            if data:
                # Aggregate to monthly
                monthly_records = aggregate_to_monthly(data)
                if monthly_records:
                    new_records = save_to_database(province, monthly_records)
                    total_new_records += new_records
            else:
                print(f"  Failed to fetch data")
                break
            
            # Move to next chunk
            if end_month == 12:
                start_year = end_year + 1
                start_month = 1
            else:
                start_year = end_year
                start_month = end_month + 1
    
    print("\n" + "=" * 60)
    print(f"Update complete. Total new monthly records: {total_new_records}")
    return total_new_records


# ============================================================================
# QUERY FUNCTIONS
# ============================================================================

def view_data_summary():
    """View summary statistics of monthly weather data"""
    query = """
    SELECT 
        province,
        MIN(CONCAT(year, '-', LPAD(month, 2, '0'))) as earliest_month,
        MAX(CONCAT(year, '-', LPAD(month, 2, '0'))) as latest_month,
        COUNT(*) as total_records,
        AVG(temperature_mean) as avg_temp,
        AVG(precipitation_sum) as avg_precip,
        AVG(humidity_mean) as avg_humid
    FROM weather_data_monthly
    GROUP BY province
    ORDER BY province
    """
    
    return pd.read_sql(query, engine)


def view_recent_data(province=None, limit=100):
    """View recent monthly weather data"""
    if province:
        query = """
        SELECT province, year, month, temperature_mean, precipitation_sum, humidity_mean
        FROM weather_data_monthly
        WHERE province = :province
        ORDER BY year DESC, month DESC
        LIMIT :limit
        """
        return pd.read_sql(query, engine, params={"province": province, "limit": limit})
    else:
        query = f"""
        SELECT province, year, month, temperature_mean, precipitation_sum, humidity_mean
        FROM weather_data_monthly
        ORDER BY year DESC, month DESC
        LIMIT {limit}
        """
        return pd.read_sql(query, engine)


def check_duplicates():
    """Check for any duplicate monthly records"""
    query = """
    SELECT province, year, month, COUNT(*) as count
    FROM weather_data_monthly
    GROUP BY province, year, month
    HAVING count > 1
    """
    
    df = pd.read_sql(query, engine)
    if len(df) == 0:
        print("No duplicates found")
    else:
        print(f"Found {len(df)} duplicate entries")
    return df


if __name__ == "__main__":
    import sys
    
    # Check if user wants to clear data first
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        print("Clearing all existing data...")
        clear_all_data()
        print()
    
    update_weather_data()
    
    print("\nMonthly Data Summary:")
    print(view_data_summary())
    
    print("\nRecent Monthly Records (10):")
    print(view_recent_data(limit=10))
    
    print("\nChecking for duplicates:")
    check_duplicates()

    print(view_recent_data(limit=10))
    
    print("\nChecking for duplicates:")
    check_duplicates()
