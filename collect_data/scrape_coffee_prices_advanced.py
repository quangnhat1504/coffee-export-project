"""
Advanced script to scrape coffee price chart data from chogia.vn
Uses network inspection to find API endpoints
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time

class AdvancedCoffeePriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://chogia.vn/gia-ca-phe/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # Possible API endpoints (you need to inspect network tab to find actual ones)
        self.possible_api_endpoints = [
            'https://chogia.vn/api/coffee-prices',
            'https://chogia.vn/api/prices/coffee',
            'https://chogia.vn/wp-json/chogia/v1/coffee-prices',
        ]
    
    def try_api_endpoints(self):
        """
        Try different API endpoints to get data
        """
        for endpoint in self.possible_api_endpoints:
            try:
                print(f"🔍 Trying endpoint: {endpoint}")
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Found data at {endpoint}")
                    return data
                else:
                    print(f"   Status: {response.status_code}")
            except Exception as e:
                print(f"   Failed: {e}")
                continue
        
        print("⚠️  No working API endpoint found")
        return None
    
    def parse_highcharts_data(self, js_code):
        """
        Parse Highcharts data from JavaScript code
        Many Vietnamese sites use Highcharts for charts
        """
        import re
        
        try:
            # Look for series data pattern
            series_pattern = r'series\s*:\s*\[(.*?)\]'
            series_match = re.search(series_pattern, js_code, re.DOTALL)
            
            if series_match:
                series_data = series_match.group(1)
                print("Found series data in JavaScript")
                return series_data
            
        except Exception as e:
            print(f"Error parsing Highcharts: {e}")
        
        return None
    
    def generate_sample_data(self):
        """
        Generate sample data structure based on observed pattern
        For testing purposes
        """
        print("\n📝 Generating sample data structure...")
        
        regions = ['GiaLai', 'DakLak', 'DakNong', 'LamDong']
        data = []
        
        # Generate last 30 days of sample data
        base_prices = {
            'GiaLai': 118200,
            'DakLak': 119300,
            'DakNong': 119300,
            'LamDong': 128000
        }
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            for region in regions:
                # Add some random variation
                import random
                variation = random.randint(-500, 500)
                price = base_prices[region] + variation
                
                data.append({
                    'date': date,
                    'region': region,
                    'price_vnd_per_kg': price
                })
        
        return data


def inspect_network_instructions():
    """
    Print instructions for finding the actual API endpoint
    """
    print("\n" + "="*70)
    print("📚 HOW TO FIND THE ACTUAL API ENDPOINT")
    print("="*70)
    print("""
1. Open chogia.vn/gia-ca-phe/ in Chrome/Edge
2. Press F12 to open Developer Tools
3. Go to "Network" tab
4. Click "XHR" or "Fetch/XHR" filter
5. Refresh the page (F5)
6. Look for requests that return JSON data
7. Common patterns to look for:
   - Requests to /api/
   - Requests with 'coffee' or 'price' in URL
   - Requests returning JSON with price data
8. Right-click on the request → Copy → Copy as cURL
9. Or copy the Request URL

EXAMPLE OF WHAT TO LOOK FOR:
   URL: https://chogia.vn/api/v1/prices?product=coffee&period=30
   Response: {"data": [...], "status": "success"}

Once you find it, update the API endpoint in this script!
    """)
    print("="*70 + "\n")


def create_database_table():
    """
    SQL to create table for storing coffee prices
    """
    sql = """
    CREATE TABLE IF NOT EXISTS daily_coffee_prices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE NOT NULL,
        region VARCHAR(50) NOT NULL,
        price_vnd_per_kg DECIMAL(10, 2) NOT NULL,
        change_from_previous DECIMAL(10, 2),
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_date_region (date, region),
        INDEX idx_date (date),
        INDEX idx_region (region)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    print("\n📊 SQL to create database table:")
    print(sql)
    return sql


if __name__ == "__main__":
    print("🚀 Advanced Coffee Price Scraper")
    print("="*70)
    
    scraper = AdvancedCoffeePriceScraper()
    
    # Try to find API
    print("\n1️⃣  Attempting to find API endpoint...")
    api_data = scraper.try_api_endpoints()
    
    if not api_data:
        print("\n2️⃣  Generating sample data for testing...")
        sample_data = scraper.generate_sample_data()
        
        # Save sample data
        df = pd.DataFrame(sample_data)
        df.to_csv('sample_coffee_prices.csv', index=False)
        print(f"✅ Sample data saved to sample_coffee_prices.csv")
        print(f"   Total records: {len(sample_data)}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Regions: {', '.join(df['region'].unique())}")
    
    # Show instructions
    inspect_network_instructions()
    
    # Show SQL
    create_database_table()
    
    print("\n💡 NEXT STEPS:")
    print("1. Follow the instructions above to find the real API endpoint")
    print("2. Update the script with the correct endpoint")
    print("3. Run scrape_coffee_prices.py daily to collect data")
    print("4. Import data into your database using the SQL above")
