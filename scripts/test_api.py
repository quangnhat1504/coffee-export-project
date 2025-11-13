#!/usr/bin/env python3
"""Test API endpoint"""

import requests
import json

url = "http://localhost:5000/api/coffee-prices/recent?days=7"

try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}\n")
    data = response.json()
    
    if data.get('success') and 'provinces' in data:
        print("=" * 70)
        print(f"📊 Provinces returned: {data['count']}")
        print(f"📅 Days requested: {data['days']}")
        print(f"📝 Total records: {data['metadata']['total_records']}")
        print(f"📆 Unique dates: {data['metadata']['unique_dates']}")
        print("=" * 70)
        
        for province in data['provinces']:
            print(f"\n{province['name']}:")
            print(f"  Total prices: {len(province['prices'])}")
            
            # Extract dates and prices
            dates = [p['date'] for p in province['prices']]
            prices = [p['price'] for p in province['prices']]
            
            print(f"  Date range: {dates[-1]} → {dates[0]}")  # API returns DESC
            print(f"  Dates: {sorted(dates)}")  # Show sorted (ASC)
            print(f"  Prices: {[province['prices'][i]['price'] for i, d in enumerate(sorted(dates, reverse=True))]}")
            
except Exception as e:
    print(f"Error: {e}")
