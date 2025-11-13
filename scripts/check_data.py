#!/usr/bin/env python3
"""Check database data for all provinces"""

import pymysql
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env
load_dotenv(Path(__file__).parent.parent / '.env')

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", "3306"))
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")

# Connect
conn = pymysql.connect(
    host=HOST,
    port=PORT,
    user=USER,
    password=PASSWORD,
    database=DB,
    ssl_disabled=True
)

cur = conn.cursor()

# Get data from Nov 5 onwards
print("\n📊 Data in database (Nov 5 - Nov 13):")
print("=" * 60)
cur.execute("""
    SELECT region, date, price_vnd_per_kg 
    FROM daily_coffee_prices 
    WHERE date >= '2025-11-05' 
    ORDER BY date, region
""")

results = cur.fetchall()
for region, date, price in results:
    print(f"{str(region):15} | {date} | {price:,}")

print("\n" + "=" * 60)
print("\n📈 Count by province:")
cur.execute("""
    SELECT region, COUNT(*) as count, MIN(date) as first_date, MAX(date) as last_date
    FROM daily_coffee_prices 
    WHERE date >= '2025-11-05'
    GROUP BY region
    ORDER BY region
""")

results = cur.fetchall()
for region, count, first_date, last_date in results:
    print(f"{str(region):15} | Count: {count:2} | {first_date} → {last_date}")

conn.close()
