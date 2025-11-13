"""
Script to create production_by_province table with sample data for 5 coffee provinces
Based on scatterplot_production.ipynb interpolation method
"""

import sys
import os
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add parent directory to path to import db_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
try:
    from db_utils import create_database_engine
except ImportError:
    create_database_engine = None

# Load environment variables
load_dotenv(dotenv_path='../../.env')

DB_HOST = os.getenv('HOST')
DB_USER = os.getenv('USER')
DB_PASSWORD = os.getenv('PASSWORD')
DB_PORT = os.getenv('PORT', '19034')
DB_NAME = os.getenv('DB', 'defaultdb')
CA_CERT = os.getenv('CA_CERT')

print(f"🔌 Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}")

# Create database connection
if create_database_engine:
    try:
        engine = create_database_engine(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            ca_cert=CA_CERT
        )
        print("✅ Connected to MySQL database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
else:
    # Fallback
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(url, connect_args={"ssl_disabled": True})
    print("✅ Connected (fallback mode)")

# Connection will be used via engine.connect()

# Create production_by_province table
print("\n=== Creating production_by_province table ===")
create_table_sql = """
CREATE TABLE IF NOT EXISTS production_by_province (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    province VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    area_thousand_ha DECIMAL(10,2),
    output_tons DECIMAL(14,2),
    export_tons DECIMAL(14,2),
    UNIQUE KEY unique_province_year (province, year),
    INDEX idx_province (province),
    INDEX idx_year (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

with engine.connect() as conn:
    conn.execute(text(create_table_sql))
    conn.commit()
print("✅ Table created successfully")

# Generate sample data for 4 provinces with realistic proportions
# Based on actual coffee production distribution in Vietnam
provinces = {
    'DakLak': 0.45,      # 45% of national production (largest)
    'GiaLai': 0.20,      # 20% 
    'DakNong': 0.15,     # 15%
    'LamDong': 0.20      # 20%
}

# Get national data to base provincial data on
print("\n📊 Fetching national production data...")
with engine.connect() as conn:
    query = text("SELECT year, area_thousand_ha, output_tons, export_tons FROM production ORDER BY year")
    df_national = pd.read_sql(query, conn)
    
# Convert to list of dicts for compatibility
national_data = df_national.to_dict('records')
print(f"✅ Found {len(national_data)} years of national data")

# Generate provincial data
print("\n=== Generating provincial data ===")
provincial_records = []

for province, proportion in provinces.items():
    print(f"\nProcessing {province} ({proportion*100:.0f}% of national)...")
    
    for record in national_data:
        year = record['year']
        
        # Calculate provincial values based on proportion
        # Add some random variation (±5%) to make it more realistic
        variation = 1 + (np.random.random() - 0.5) * 0.1  # ±5% variation
        
        area = float(record['area_thousand_ha']) * proportion * variation if record['area_thousand_ha'] else None
        output = float(record['output_tons']) * proportion * variation if record['output_tons'] else None
        export = float(record['export_tons']) * proportion * variation if record['export_tons'] else None
        
        # Intentionally create some missing data (like in the notebook example)
        # Missing data for early years (2005-2006) for DakNong
        if year in [2005, 2006] and province == 'DakNong':
            area = None
            export = None
        
        provincial_records.append({
            'province': province,
            'year': year,
            'area_thousand_ha': round(area, 2) if area else None,
            'output_tons': round(output, 2) if output else None,
            'export_tons': round(export, 2) if export else None
        })
    
    print(f"  ✓ Generated {len([r for r in provincial_records if r['province'] == province])} records")

# Insert data into database
print("\n💾 Inserting data into database...")
insert_sql = text("""
    INSERT INTO production_by_province (province, year, area_thousand_ha, output_tons, export_tons)
    VALUES (:province, :year, :area_thousand_ha, :output_tons, :export_tons)
    ON DUPLICATE KEY UPDATE
        area_thousand_ha = VALUES(area_thousand_ha),
        output_tons = VALUES(output_tons),
        export_tons = VALUES(export_tons)
""")

with engine.connect() as conn:
    for record in provincial_records:
        conn.execute(insert_sql, record)
    conn.commit()
print(f"✅ Inserted {len(provincial_records)} records")

# Verify data
print("\n🔍 Verifying data...")
with engine.connect() as conn:
    for province in provinces.keys():
        query = text("""
            SELECT COUNT(*) as count, 
                   MIN(year) as min_year, 
                   MAX(year) as max_year,
                   SUM(CASE WHEN area_thousand_ha IS NULL THEN 1 ELSE 0 END) as null_area,
                   SUM(CASE WHEN output_tons IS NULL THEN 1 ELSE 0 END) as null_output,
                   SUM(CASE WHEN export_tons IS NULL THEN 1 ELSE 0 END) as null_export
            FROM production_by_province
            WHERE province = :province
        """)
        result = conn.execute(query, {"province": province}).fetchone()
        
        print(f"\n{province}:")
        print(f"  Records: {result[0]}")
        print(f"  Years: {result[1]}-{result[2]}")
        print(f"  Missing values: area={result[3]}, output={result[4]}, export={result[5]}")

# Sample data preview
print("\n📋 Sample data (DakLak 2020-2024):")
with engine.connect() as conn:
    query = text("""
        SELECT year, area_thousand_ha, output_tons, export_tons
        FROM production_by_province
        WHERE province = 'DakLak' AND year >= 2020
        ORDER BY year
    """)
    sample_df = pd.read_sql(query, conn)
    for _, row in sample_df.iterrows():
        print(f"  {row['year']}: Area={row['area_thousand_ha']}K ha, Output={row['output_tons']} tons, Export={row['export_tons']} tons")

print("\n" + "=" * 60)
print("✅ Complete!")
print(f"Total records created: {len(provincial_records)}")
print("Missing data will be handled via interpolation in the API endpoint")
