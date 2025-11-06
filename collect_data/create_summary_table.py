"""
Script to create a summary table combining production and export data
For visualization: total production, total export, and revenue from 2005-2024
"""

import pymysql
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DB_HOST = os.getenv('HOST')
DB_USER = os.getenv('USER')
DB_PASSWORD = os.getenv('PASSWORD')
DB_PORT = int(os.getenv('PORT', 3306))
DB_NAME = os.getenv('DB', 'defaultdb')

# Create SQLAlchemy engine
connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string, echo=True)

print("=== Creating Coffee Summary Table ===")
print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}\n")

# SQL to create summary table
ddl_summary = """
CREATE TABLE IF NOT EXISTS coffee_summary (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  area_thousand_ha DECIMAL(10,1) NULL COMMENT 'Diện tích trồng (nghìn ha)',
  production_tons DECIMAL(14,2) NULL COMMENT 'Tổng sản lượng (tấn)',
  export_tons DECIMAL(14,2) NULL COMMENT 'Tổng xuất khẩu (tấn)',
  export_value_million_usd DECIMAL(16,2) NULL COMMENT 'Kim ngạch xuất khẩu (triệu USD)',
  price_world_usd_per_ton DECIMAL(12,2) NULL COMMENT 'Giá thế giới (USD/tấn)',
  price_vn_usd_per_ton DECIMAL(12,2) NULL COMMENT 'Giá Việt Nam (USD/tấn)',
  UNIQUE KEY uq_summary_year (year)
) CHARACTER SET utf8mb4 COMMENT 'Bảng tổng hợp dữ liệu cà phê 2005-2024';
"""

# SQL to populate summary table from existing tables
insert_summary = """
INSERT INTO coffee_summary (
  year, 
  area_thousand_ha, 
  production_tons, 
  export_tons, 
  export_value_million_usd,
  price_world_usd_per_ton,
  price_vn_usd_per_ton
)
SELECT 
  p.year,
  p.area_thousand_ha,
  p.output_tons AS production_tons,
  p.export_tons,
  e.export_value_million_usd,
  e.price_world_usd_per_ton,
  e.price_vn_usd_per_ton
FROM production p
LEFT JOIN coffee_export e ON p.year = e.year
WHERE p.year >= 2005 AND p.year <= 2024
ON DUPLICATE KEY UPDATE
  area_thousand_ha = VALUES(area_thousand_ha),
  production_tons = VALUES(production_tons),
  export_tons = VALUES(export_tons),
  export_value_million_usd = VALUES(export_value_million_usd),
  price_world_usd_per_ton = VALUES(price_world_usd_per_ton),
  price_vn_usd_per_ton = VALUES(price_vn_usd_per_ton);
"""

try:
    with engine.begin() as conn:
        # Create table
        print("Creating coffee_summary table...")
        conn.execute(text(ddl_summary))
        print("✓ Table created successfully\n")
        
        # Populate data
        print("Populating data from production and coffee_export tables...")
        result = conn.execute(text(insert_summary))
        print(f"✓ Inserted/Updated {result.rowcount} rows\n")
        
        # Verify data
        print("=== Verifying Data ===")
        verify_query = """
        SELECT 
          year,
          area_thousand_ha,
          production_tons,
          export_tons,
          export_value_million_usd,
          price_world_usd_per_ton,
          price_vn_usd_per_ton
        FROM coffee_summary
        ORDER BY year;
        """
        
        result = conn.execute(text(verify_query))
        rows = result.fetchall()
        
        print(f"\nTotal rows: {len(rows)}")
        print("\nSample data (first 5 rows):")
        print("-" * 120)
        print(f"{'Year':<6} {'Area(ha)':<12} {'Production(t)':<15} {'Export(t)':<15} {'Revenue($M)':<15} {'Price(W)':<12} {'Price(VN)':<12}")
        print("-" * 120)
        
        for i, row in enumerate(rows[:5]):
            print(f"{row[0]:<6} {str(row[1]):<12} {str(row[2]):<15} {str(row[3]):<15} {str(row[4]):<15} {str(row[5]):<12} {str(row[6]):<12}")
        
        if len(rows) > 5:
            print("...")
            print("\nLast 5 rows:")
            print("-" * 120)
            for row in rows[-5:]:
                print(f"{row[0]:<6} {str(row[1]):<12} {str(row[2]):<15} {str(row[3]):<15} {str(row[4]):<15} {str(row[5]):<12} {str(row[6]):<12}")
        
        print("-" * 120)
        print("\n✓ Coffee summary table created and populated successfully!")
        print("\nYou can now use this table for visualization from 2005 to 2024")
        print("Table name: coffee_summary")
        print("\nColumns:")
        print("  - year: Năm")
        print("  - area_thousand_ha: Diện tích trồng (nghìn ha)")
        print("  - production_tons: Tổng sản lượng (tấn)")
        print("  - export_tons: Tổng xuất khẩu (tấn)")
        print("  - export_value_million_usd: Kim ngạch xuất khẩu (triệu USD)")
        print("  - price_world_usd_per_ton: Giá thế giới (USD/tấn)")
        print("  - price_vn_usd_per_ton: Giá Việt Nam (USD/tấn)")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease check:")
    print("  1. Database connection settings in .env file")
    print("  2. Tables 'production' and 'coffee_export' exist")
    print("  3. Database user has CREATE and INSERT permissions")

finally:
    engine.dispose()
