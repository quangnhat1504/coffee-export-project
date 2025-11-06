"""
Script to rename coffee_summary table to export_performance
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

print("=== Renaming Table: coffee_summary -> export_performance ===")
print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}\n")

try:
    with engine.begin() as conn:
        # Check if coffee_summary exists
        check_old = "SHOW TABLES LIKE 'coffee_summary'"
        result = conn.execute(text(check_old))
        old_exists = result.fetchone() is not None
        
        # Check if export_performance already exists
        check_new = "SHOW TABLES LIKE 'export_performance'"
        result = conn.execute(text(check_new))
        new_exists = result.fetchone() is not None
        
        if not old_exists and new_exists:
            print("✓ Table 'export_performance' already exists!")
            print("  No action needed.\n")
        elif old_exists and new_exists:
            print("⚠ Both tables exist!")
            print("  Dropping old 'coffee_summary' table...")
            conn.execute(text("DROP TABLE coffee_summary"))
            print("✓ Dropped 'coffee_summary'\n")
        elif old_exists:
            print("Renaming table 'coffee_summary' to 'export_performance'...")
            conn.execute(text("RENAME TABLE coffee_summary TO export_performance"))
            print("✓ Table renamed successfully!\n")
        else:
            print("❌ Table 'coffee_summary' does not exist!")
            print("  Creating 'export_performance' table from scratch...\n")
            
            # Create export_performance table
            ddl_export_performance = """
            CREATE TABLE IF NOT EXISTS export_performance (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              year INT NOT NULL,
              area_thousand_ha DECIMAL(10,1) NULL COMMENT 'Diện tích trồng (nghìn ha)',
              production_tons DECIMAL(14,2) NULL COMMENT 'Tổng sản lượng (tấn)',
              export_tons DECIMAL(14,2) NULL COMMENT 'Tổng xuất khẩu (tấn)',
              export_value_million_usd DECIMAL(16,2) NULL COMMENT 'Kim ngạch xuất khẩu (triệu USD)',
              price_world_usd_per_ton DECIMAL(12,2) NULL COMMENT 'Giá thế giới (USD/tấn)',
              price_vn_usd_per_ton DECIMAL(12,2) NULL COMMENT 'Giá Việt Nam (USD/tấn)',
              UNIQUE KEY uq_export_perf_year (year)
            ) CHARACTER SET utf8mb4 COMMENT 'Export Performance - Bảng tổng hợp hiệu suất xuất khẩu cà phê 2005-2024';
            """
            
            conn.execute(text(ddl_export_performance))
            print("✓ Created 'export_performance' table\n")
            
            # Populate data
            insert_data = """
            INSERT INTO export_performance (
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
            
            result = conn.execute(text(insert_data))
            print(f"✓ Populated {result.rowcount} rows\n")
        
        # Verify the new table
        print("=== Verifying export_performance table ===")
        verify_query = """
        SELECT 
          COUNT(*) as total_rows,
          MIN(year) as min_year,
          MAX(year) as max_year
        FROM export_performance;
        """
        
        result = conn.execute(text(verify_query))
        stats = result.fetchone()
        
        print(f"✓ Table: export_performance")
        print(f"  Total rows: {stats[0]}")
        print(f"  Year range: {stats[1]} - {stats[2]}")
        
        # Show sample data
        print("\n=== Sample Data ===")
        sample_query = """
        SELECT year, production_tons, export_tons, export_value_million_usd
        FROM export_performance
        ORDER BY year
        LIMIT 5;
        """
        result = conn.execute(text(sample_query))
        rows = result.fetchall()
        
        print(f"{'Year':<6} {'Production':<15} {'Export':<15} {'Revenue($M)':<15}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<6} {str(row[1]):<15} {str(row[2]):<15} {str(row[3]):<15}")
        
        print("\n" + "="*60)
        print("✓ SUCCESS!")
        print("  Table 'export_performance' is ready to use")
        print("="*60)
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease check:")
    print("  1. Database connection settings in .env file")
    print("  2. Database user has RENAME and CREATE permissions")

finally:
    engine.dispose()
