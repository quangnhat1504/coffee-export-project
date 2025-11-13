"""
Script to scrape CURRENT daily coffee prices from chogia.vn
This should be run daily to collect real-time data
"""

import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Optional
import re

# Add parent directory to path to import db_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web', 'backend'))
try:
    from db_utils import create_database_engine, get_db_connection
    USE_SQLALCHEMY = True
except ImportError:
    USE_SQLALCHEMY = False
    from sqlalchemy import create_engine, text


class DailyCoffeePriceScraper:
    """Scraper for daily coffee prices from chogia.vn"""
    
    def __init__(self):
        self.url = "https://chogia.vn/gia-ca-phe/"
        load_dotenv()
        self.db_config = {
            'host': os.getenv('HOST'),
            'user': os.getenv('USER'),
            'password': os.getenv('PASSWORD'),
            'database': os.getenv('DB'),
            'port': int(os.getenv('PORT', 3306))
        }
        
        # Region mapping for normalization
        self.region_map = {
            'Đắk Lắk': 'DakLak',
            'Dak Lak': 'DakLak',
            'Đắk Nông': 'DakNong',
            'Dak Nong': 'DakNong',
            'Gia Lai': 'GiaLai',
            'Lâm Đồng': 'LamDong',
            'Lam Dong': 'LamDong'
        }
    
    def scrape_current_prices(self) -> Dict[str, int]:
        """Scrape current coffee prices from the website"""
        try:
            print(f"🌐 Fetching data from {self.url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            prices: Dict[str, int] = {}
            
            print("🔍 Looking for price data...")
            
            # Method 1: Look for specific price patterns in text
            text_content = soup.get_text()
            
            # Try to find prices in format like "Đắk Lắk: 119,000"
            for region_display, region_code in self.region_map.items():
                pattern = rf'{re.escape(region_display)}[:\s]+([0-9,]+)'
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    price_str = matches[0].replace(',', '').replace('.', '')
                    try:
                        price = int(price_str)
                        # Sanity check: prices should be between 50,000 and 200,000 VND/kg
                        if 50000 <= price <= 200000:
                            prices[region_code] = price
                            print(f"   ✅ Found {region_code}: {price:,} VND/kg")
                    except ValueError:
                        continue
            
            if not prices:
                print("⚠️  Could not find prices using regex, trying HTML table parsing...")
                # Method 2: Try to find table structures
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            cell_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                            for region_display, region_code in self.region_map.items():
                                if region_display.lower() in cell_text.lower():
                                    # Try to extract price from the row
                                    price_match = re.search(r'([0-9,]+)', cell_text)
                                    if price_match:
                                        try:
                                            price = int(price_match.group(1).replace(',', '').replace('.', ''))
                                            if 50000 <= price <= 200000:
                                                prices[region_code] = price
                                                print(f"   ✅ Found {region_code}: {price:,} VND/kg")
                                        except ValueError:
                                            continue
            
            return prices
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error scraping: {e}")
            return {}
    
    def save_to_database(self, prices: Dict[str, int]) -> bool:
        """Save prices to database"""
        if not prices:
            print("⚠️  No prices to save")
            return False
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().isoformat()
        
        print(f"\n💾 Saving to database...")
        
        try:
            if USE_SQLALCHEMY:
                # Use SQLAlchemy connection
                engine = create_database_engine(
                    host=self.db_config['host'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    port=str(self.db_config['port']),
                    database=self.db_config['database']
                )
                
                insert_query = text("""
                    INSERT INTO daily_coffee_prices 
                    (date, region, price_vnd_per_kg, scraped_at, source)
                    VALUES (:date, :region, :price, :scraped_at, :source)
                    ON DUPLICATE KEY UPDATE
                        price_vnd_per_kg = VALUES(price_vnd_per_kg),
                        scraped_at = VALUES(scraped_at)
                """)
                
                with engine.connect() as conn:
                    for region, price in prices.items():
                        conn.execute(insert_query, {
                            'date': current_date,
                            'region': region,
                            'price': price,
                            'scraped_at': current_time,
                            'source': 'chogia.vn'
                        })
                        print(f"   ✅ {region}: {price:,} VND/kg")
                    conn.commit()
            else:
                # Fallback to mysql.connector
                conn = mysql.connector.connect(**self.db_config)
                cursor = conn.cursor()
                
                query = """
                INSERT INTO daily_coffee_prices 
                (date, region, price_vnd_per_kg, scraped_at, source)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    price_vnd_per_kg = VALUES(price_vnd_per_kg),
                    scraped_at = VALUES(scraped_at)
                """
                
                for region, price in prices.items():
                    cursor.execute(query, (current_date, region, price, current_time, 'chogia.vn'))
                    print(f"   ✅ {region}: {price:,} VND/kg")
                
                conn.commit()
                cursor.close()
                conn.close()
            
            print(f"\n✨ Successfully saved {len(prices)} prices for {current_date}")
            return True
            
        except Error as e:
            print(f"❌ Database error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def run(self):
        """Main execution"""
        print("=" * 70)
        print("DAILY COFFEE PRICE SCRAPER")
        print("=" * 70)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        prices = self.scrape_current_prices()
        
        if prices:
            self.save_to_database(prices)
        else:
            print("\n⚠️  No prices scraped. Please check:")
            print("   1. Website is accessible")
            print("   2. Website structure hasn't changed")
            print("   3. Network connection is working")

if __name__ == "__main__":
    scraper = DailyCoffeePriceScraper()
    scraper.run()
