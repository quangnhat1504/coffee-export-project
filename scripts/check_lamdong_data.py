#!/usr/bin/env python3
"""Check LamDong data specifically in database"""

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
    ssl_disabled=True,
    cursorclass=pymysql.cursors.DictCursor
)

cur = conn.cursor()

print("\n" + "=" * 70)
print("🔍 CHECKING LAMDONG DATA IN DATABASE")
print("=" * 70)

# Check all LamDong data
print("\n📊 All LamDong records in database:")
cur.execute("""
    SELECT date, price_vnd_per_kg, scraped_at
    FROM daily_coffee_prices
    WHERE region = 'LamDong'
    ORDER BY date DESC
    LIMIT 20
""")

results = cur.fetchall()
print(f"\nTotal LamDong records: {len(results)}")
print("\nDate       | Price     | Scraped At")
print("-" * 60)
for row in results:
    print(f"{row['date']} | {row['price_vnd_per_kg']:>9,.0f} | {row['scraped_at']}")

# Check specifically for dates 11/5, 11/6, 11/7
print("\n" + "=" * 70)
print("🔍 Checking specific dates (11/5, 11/6, 11/7):")
print("=" * 70)

for date_str in ['2025-11-05', '2025-11-06', '2025-11-07']:
    cur.execute("""
        SELECT region, price_vnd_per_kg, scraped_at
        FROM daily_coffee_prices
        WHERE date = %s
        ORDER BY region
    """, (date_str,))
    
    results = cur.fetchall()
    print(f"\n📅 {date_str}:")
    if results:
        for row in results:
            lamdong_marker = " ← LAMDONG!" if row['region'] == 'LamDong' else ""
            print(f"   {row['region']:15} | {row['price_vnd_per_kg']:>9,.0f}{lamdong_marker}")
    else:
        print(f"   ❌ NO DATA for this date!")

# Check date range query (same as API)
print("\n" + "=" * 70)
print("🔍 Simulating API query (DATE_SUB(CURDATE(), INTERVAL 7 DAY)):")
print("=" * 70)

cur.execute("""
    SELECT region, date, price_vnd_per_kg
    FROM daily_coffee_prices
    WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        AND region = 'LamDong'
    ORDER BY date DESC
""")

results = cur.fetchall()
print(f"\nLamDong records in last 7 days: {len(results)}")
print("\nDate       | Price")
print("-" * 30)
for row in results:
    print(f"{row['date']} | {row['price_vnd_per_kg']:>9,.0f}")

conn.close()

print("\n" + "=" * 70)
print("✅ Check complete!")
print("=" * 70 + "\n")
