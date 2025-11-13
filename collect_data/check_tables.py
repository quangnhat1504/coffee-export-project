#!/usr/bin/env python3
"""Check all tables in database"""
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", "3306"))
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")

url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

try:
    engine = create_engine(url + "?ssl_disabled=true", pool_pre_ping=True)
    print("✅ Connected to database")
    
    # Get all table names
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📊 Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
        
        # Get columns for each table
        columns = inspector.get_columns(table)
        print(f"    Columns: {[col['name'] for col in columns[:5]]}")  # First 5 columns
        
        # Get row count
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"    Rows: {count}")
        print()
        
except Exception as e:
    print(f"❌ Error: {e}")
