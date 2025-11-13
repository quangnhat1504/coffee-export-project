"""
Script to scrape daily coffee prices from chọgia.vn
Collects prices for different regions: Gia Lai, Đắk Lắk, Đắk Nông, Lâm Đồng
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import re

class CoffeePriceScraper:
    def __init__(self):
        self.base_url = "https://chogia.vn/gia-ca-phe/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://chogia.vn/',
        }
        
    def get_current_prices(self):
        """
        Scrape current coffee prices from the main page
        """
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            prices = []
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Try to find price table
            price_tables = soup.find_all('table')
            
            if price_tables:
                for table in price_tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 2:
                            region_cell = cols[0].get_text(strip=True)
                            price_cell = cols[1].get_text(strip=True)
                            
                            # Extract price (remove non-numeric characters except dot/comma)
                            price_match = re.search(r'[\d,.]+', price_cell)
                            if price_match:
                                price_str = price_match.group().replace(',', '').replace('.', '')
                                try:
                                    price = int(price_str)
                                    
                                    # Map region names
                                    region_map = {
                                        'Gia Lai': 'GiaLai',
                                        'Đắk Lắk': 'DakLak',
                                        'Dak Lak': 'DakLak',
                                        'Đắk Nông': 'DakNong',
                                        'Dak Nong': 'DakNong',
                                        'Lâm Đồng': 'LamDong',
                                        'Lam Dong': 'LamDong'
                                    }
                                    
                                    for key, value in region_map.items():
                                        if key.lower() in region_cell.lower():
                                            prices.append({
                                                'date': current_date,
                                                'region': value,
                                                'price_vnd_per_kg': price,
                                                'scraped_at': datetime.now().isoformat()
                                            })
                                            break
                                except ValueError:
                                    continue
            
            print(f"✅ Scraped {len(prices)} price entries for {current_date}")
            return prices
            
        except requests.RequestException as e:
            print(f"❌ Error fetching data: {e}")
            return []
        except Exception as e:
            print(f"❌ Error parsing data: {e}")
            return []
    
    def get_historical_chart_data(self):
        """
        Try to extract data from the chart on the page
        This might require analyzing JavaScript or making additional API calls
        """
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for embedded chart data in script tags
            scripts = soup.find_all('script')
            chart_data = []
            
            for script in scripts:
                script_text = script.string
                if script_text and ('chart' in script_text.lower() or 'data' in script_text.lower()):
                    # Try to extract JSON data
                    # This is a simplified example - you may need to adjust based on actual page structure
                    try:
                        # Look for patterns like: data: [...] or series: [...]
                        data_matches = re.findall(r'data\s*:\s*(\[.*?\])', script_text, re.DOTALL)
                        if data_matches:
                            print(f"Found potential chart data in script")
                            # Further processing needed based on actual data format
                    except:
                        continue
            
            return chart_data
            
        except Exception as e:
            print(f"❌ Error extracting chart data: {e}")
            return []
    
    def save_to_csv(self, data, filename='coffee_prices.csv'):
        """
        Save scraped data to CSV file
        """
        if not data:
            print("⚠️  No data to save")
            return
        
        df = pd.DataFrame(data)
        
        # Check if file exists to append or create new
        try:
            existing_df = pd.read_csv(filename)
            # Combine and remove duplicates
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date', 'region'], keep='last')
            combined_df.to_csv(filename, index=False)
            print(f"✅ Data appended to {filename}")
        except FileNotFoundError:
            df.to_csv(filename, index=False)
            print(f"✅ Data saved to {filename}")
    
    def scrape_and_save(self):
        """
        Main method to scrape and save data
        """
        print(f"🔍 Scraping coffee prices from {self.base_url}")
        
        # Get current prices
        current_prices = self.get_current_prices()
        
        if current_prices:
            # Save to CSV
            self.save_to_csv(current_prices)
            
            # Also save to JSON for backup
            json_filename = f"coffee_prices_{datetime.now().strftime('%Y%m%d')}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(current_prices, f, ensure_ascii=False, indent=2)
            print(f"✅ Data also saved to {json_filename}")
        else:
            print("⚠️  No data scraped")


def main():
    scraper = CoffeePriceScraper()
    scraper.scrape_and_save()
    
    print("\n📊 Summary:")
    print("This script scrapes current coffee prices from chogia.vn")
    print("Run this daily (e.g., via cron job) to build historical data")
    print("\n💡 Tip: Use Windows Task Scheduler to run this script daily:")
    print("   1. Open Task Scheduler")
    print("   2. Create Basic Task")
    print("   3. Set trigger: Daily at specific time (e.g., 9 AM)")
    print("   4. Action: Start a program")
    print("   5. Program: python")
    print(f"   6. Arguments: {__file__}")
    print(f"   7. Start in: {os.path.dirname(__file__)}")


if __name__ == "__main__":
    import os
    main()
