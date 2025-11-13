#!/usr/bin/env python3
"""Simulate API endpoint logic to debug data issue"""

import pymysql
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime, timedelta

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

days = 7  # Changed from 9 to 7 to match frontend

# Same query as API
query = """
    SELECT 
        region,
        date,
        price_vnd_per_kg,
        scraped_at
    FROM daily_coffee_prices
    WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    ORDER BY date DESC, region ASC
"""

cur.execute(query, (days,))
data = cur.fetchall()

print(f"\n📊 Simulating API /coffee-prices/recent?days={days}")
print("=" * 70)
print(f"Total records returned: {len(data)}")
print()

# Group data by province (same as API)
provinces_data = {}
all_dates = set()

for row in data:
    region = row['region']
    date_val = row['date']
    price = float(row['price_vnd_per_kg']) if row['price_vnd_per_kg'] else None
    
    # Convert date to string
    date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)
    all_dates.add(date_str)
    
    if region not in provinces_data:
        provinces_data[region] = {
            'name': region,
            'prices': []
        }
    
    provinces_data[region]['prices'].append({
        'date': date_str,
        'price': price
    })

print(f"Unique dates found: {sorted(all_dates)}\n")
print("=" * 70)

# Print each province's data
for region in sorted(provinces_data.keys()):
    data = provinces_data[region]
    print(f"\n{region}:")
    print(f"  Total prices: {len(data['prices'])}")
    
    # Sort by date
    data['prices'].sort(key=lambda x: x['date'])
    
    dates = [p['date'] for p in data['prices']]
    print(f"  Date range: {dates[0]} → {dates[-1]}")
    print(f"  Dates: {dates}")
    print(f"  Prices: {[p['price'] for p in data['prices']]}")

conn.close()
