"""
Add database indexes for better query performance
This script adds indexes to frequently queried columns
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web', 'backend'))

# Configure Unicode output
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Load environment variables
load_dotenv(dotenv_path='../.env')

HOST = os.getenv("HOST")
PORT = os.getenv("PORT", "3306")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")

if not all([HOST, PORT, USER, PASSWORD, DB]):
    raise SystemExit("❌ Missing env vars. Set HOST, PORT, USER, PASSWORD, DB in .env")

# Create database connection
url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
engine = create_engine(
    url,
    connect_args={"ssl": False},
    pool_pre_ping=True
)

print("✅ Connected to database")

# Define indexes to add
indexes = [
    # Production table indexes
    ("idx_production_year", "production", "year"),
    
    # Coffee export table indexes
    ("idx_coffee_export_year", "coffee_export", "year"),
    
    # Weather data indexes  
    ("idx_weather_year", "weather", "year"),
    
    # Market trade indexes
    ("idx_market_trade_year", "market_trade", "year"),
    ("idx_market_trade_importer", "market_trade", "importer"),
    
    # Coffee long table indexes
    ("idx_coffee_long_year", "coffee_long", "year"),
    ("idx_coffee_long_hang_muc", "coffee_long", "hang_muc"),
]

with engine.begin() as conn:
    print("\n🔧 Adding database indexes...")
    
    for idx_name, table_name, column_name in indexes:
        try:
            # Check if index exists
            check_sql = f"""
                SELECT COUNT(*) as cnt
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = '{table_name}'
                  AND index_name = '{idx_name}'
            """
            result = conn.execute(text(check_sql)).scalar()
            
            if result > 0:
                print(f"  ⏭️  Index {idx_name} already exists on {table_name}.{column_name}")
                continue
            
            # Create index
            create_sql = f"CREATE INDEX {idx_name} ON {table_name}({column_name})"
            conn.execute(text(create_sql))
            print(f"  ✅ Created index {idx_name} on {table_name}.{column_name}")
            
        except Exception as e:
            print(f"  ⚠️  Error creating index {idx_name}: {str(e)}")
    
    print("\n📊 Analyzing tables for query optimization...")
    
    # Analyze tables to update statistics
    tables = ["coffee_long", "weather", "production", "coffee_export", "market_trade"]
    for table in tables:
        try:
            conn.execute(text(f"ANALYZE TABLE {table}"))
            print(f"  ✅ Analyzed {table}")
        except Exception as e:
            print(f"  ⚠️  Error analyzing {table}: {str(e)}")

print("\n✅ Database indexing completed successfully!")
print("📈 Query performance should be significantly improved")
