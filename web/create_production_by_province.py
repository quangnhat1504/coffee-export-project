"""
Script to create production_by_province table with sample data for 5 coffee provinces
Based on scatterplot_production.ipynb interpolation method
"""

import pymysql
import pandas as pd
from dotenv import load_dotenv
import os
import numpy as np

# Load environment variables
load_dotenv(dotenv_path='../.env')

DB_HOST = os.getenv('HOST')
DB_USER = os.getenv('USER')
DB_PASSWORD = os.getenv('PASSWORD')
DB_PORT = int(os.getenv('PORT', 19034))
DB_NAME = os.getenv('DB', 'defaultdb')

print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}")

# Create database connection
connection = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    ssl={'ssl_disabled': True}
)

cursor = connection.cursor()

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

cursor.execute(create_table_sql)
connection.commit()
print("✓ Table created successfully")

# Generate sample data for 5 provinces with realistic proportions
# Based on actual coffee production distribution in Vietnam
provinces = {
    'DakLak': 0.45,      # 45% of national production (largest)
    'GiaLai': 0.20,      # 20% 
    'DakNong': 0.15,     # 15%
    'LamDong': 0.12,     # 12%
    'KonTum': 0.08       # 8% (smallest)
}

# Get national data to base provincial data on
print("\n=== Fetching national production data ===")
cursor.execute("SELECT year, area_thousand_ha, output_tons, export_tons FROM production ORDER BY year")
national_data = cursor.fetchall()
print(f"✓ Found {len(national_data)} years of national data")

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
        # Missing data for early years (2005-2006) for some provinces
        if year in [2005, 2006] and province in ['DakNong', 'KonTum']:
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
print("\n=== Inserting data into database ===")
insert_sql = """
INSERT INTO production_by_province (province, year, area_thousand_ha, output_tons, export_tons)
VALUES (%(province)s, %(year)s, %(area_thousand_ha)s, %(output_tons)s, %(export_tons)s)
ON DUPLICATE KEY UPDATE
    area_thousand_ha = VALUES(area_thousand_ha),
    output_tons = VALUES(output_tons),
    export_tons = VALUES(export_tons)
"""

cursor.executemany(insert_sql, provincial_records)
connection.commit()
print(f"✓ Inserted {len(provincial_records)} records")

# Verify data
print("\n=== Verifying data ===")
for province in provinces.keys():
    cursor.execute("""
        SELECT COUNT(*) as count, 
               MIN(year) as min_year, 
               MAX(year) as max_year,
               SUM(CASE WHEN area_thousand_ha IS NULL THEN 1 ELSE 0 END) as null_area,
               SUM(CASE WHEN output_tons IS NULL THEN 1 ELSE 0 END) as null_output,
               SUM(CASE WHEN export_tons IS NULL THEN 1 ELSE 0 END) as null_export
        FROM production_by_province
        WHERE province = %s
    """, (province,))
    
    result = cursor.fetchone()
    print(f"\n{province}:")
    print(f"  Records: {result['count']}")
    print(f"  Years: {result['min_year']}-{result['max_year']}")
    print(f"  Missing values: area={result['null_area']}, output={result['null_output']}, export={result['null_export']}")

# Sample data preview
print("\n=== Sample data (DakLak 2020-2024) ===")
cursor.execute("""
    SELECT year, area_thousand_ha, output_tons, export_tons
    FROM production_by_province
    WHERE province = 'DakLak' AND year >= 2020
    ORDER BY year
""")
sample = cursor.fetchall()
for row in sample:
    print(f"  {row['year']}: Area={row['area_thousand_ha']}K ha, Output={row['output_tons']} tons, Export={row['export_tons']} tons")

print("\n=== Complete! ===")
print(f"Total records created: {len(provincial_records)}")
print("Missing data will be handled via interpolation in the API endpoint")

cursor.close()
connection.close()
