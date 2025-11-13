#!/usr/bin/env python3
"""Check daily_coffee_prices table structure and data"""
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", "3306"))
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")

url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
engine = create_engine(url + "?ssl_disabled=true", pool_pre_ping=True)

print("✅ Connected to database\n")

# Get latest 7 days data
query = text("""
SELECT 
    date,
    region,
    price_vnd_per_kg,
    scraped_at
FROM daily_coffee_prices
ORDER BY date DESC
LIMIT 50
""")

with engine.connect() as conn:
    df = pd.read_sql(query, conn)
    
print("📊 Latest data (first 50 rows):")
print(df.to_string())

print("\n\n📍 Unique regions:")
regions = df['region'].unique()
print(regions)

print(f"\n📅 Date range: {df['date'].min()} to {df['date'].max()}")
print(f"📊 Total rows: {len(df)}")
