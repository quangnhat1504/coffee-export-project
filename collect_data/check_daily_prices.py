"""
Quick script to check daily_coffee_prices table
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('HOST'),
    user=os.getenv('USER'),
    password=os.getenv('PASSWORD'),
    database=os.getenv('DB'),
    port=int(os.getenv('PORT', 3306))
)

cursor = conn.cursor()

# Total records and date range
cursor.execute('SELECT COUNT(*) as total, MIN(date) as start, MAX(date) as end FROM daily_coffee_prices')
total, start, end = cursor.fetchone()
print(f"📊 Database: daily_coffee_prices")
print(f"   Total records: {total}")
print(f"   Date range: {start} to {end}")

# Records per region
cursor.execute('SELECT region, COUNT(*) as count FROM daily_coffee_prices GROUP BY region')
print(f"\n📍 Records per region:")
for region, count in cursor.fetchall():
    print(f"   {region}: {count} records")

# Latest 10 records
cursor.execute('SELECT date, region, price_vnd_per_kg FROM daily_coffee_prices ORDER BY date DESC, region LIMIT 10')
print(f"\n🕐 Latest records:")
for date, region, price in cursor.fetchall():
    print(f"   {date} | {region:10s} | {price:,} VND/kg")

# Sample prices for today
cursor.execute("SELECT date, region, price_vnd_per_kg FROM daily_coffee_prices WHERE date = (SELECT MAX(date) FROM daily_coffee_prices) ORDER BY region")
print(f"\n💰 Latest prices:")
for date, region, price in cursor.fetchall():
    print(f"   {region:10s}: {price:,} VND/kg")

conn.close()
