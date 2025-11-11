"""
Script to scrape historical coffee price data from chogia.vn chart
Uses Selenium to extract JavaScript chart data
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import time
import re

class HistoricalCoffeePriceScraper:
    def __init__(self):
        self.url = "https://chogia.vn/gia-ca-phe/"
        self.setup_driver()
        
        # Load environment variables
        load_dotenv()
        self.db_config = {
            'host': os.getenv('HOST', 'localhost'),
            'user': os.getenv('USER', 'root'),
            'password': os.getenv('PASSWORD', ''),
            'database': os.getenv('DB', 'coffee_db'),
            'port': int(os.getenv('PORT', 3306))
        }
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        print("🔧 Setting up Chrome driver...")
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            print("✅ Chrome driver ready")
        except Exception as e:
            print(f"❌ Error setting up driver: {e}")
            print("💡 Installing selenium and webdriver-manager...")
            print("   Run: pip install selenium webdriver-manager")
            raise
    
    def extract_chart_data(self):
        """Extract chart data from page JavaScript"""
        try:
            print(f"🌐 Loading {self.url}...")
            self.driver.get(self.url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Try to find chart canvas or container
            print("🔍 Looking for chart data...")
            
            # Method 1: Execute JavaScript to get chart data
            chart_data = self.driver.execute_script("""
                // Try to find Highcharts instance
                if (typeof Highcharts !== 'undefined' && Highcharts.charts) {
                    for (let chart of Highcharts.charts) {
                        if (chart && chart.series) {
                            let data = {};
                            chart.series.forEach(series => {
                                if (series.name && series.data) {
                                    data[series.name] = series.data.map(point => ({
                                        x: point.x || point.category,
                                        y: point.y
                                    }));
                                }
                            });
                            return data;
                        }
                    }
                }
                
                // Try window variables
                if (window.chartData) return window.chartData;
                if (window.priceData) return window.priceData;
                
                return null;
            """)
            
            if chart_data:
                print(f"✅ Found chart data with {len(chart_data)} series")
                
                # Parse and save the data
                self.parse_and_save_chart_data(chart_data)
                
                return chart_data
            
            # Method 2: Extract from script tags
            print("🔍 Trying to extract from script tags...")
            scripts = self.driver.find_elements(By.TAG_NAME, 'script')
            
            for script in scripts:
                script_content = script.get_attribute('innerHTML')
                if script_content and ('series' in script_content or 'data' in script_content):
                    # Look for data patterns
                    if 'Lâm Đồng' in script_content or 'Đắk Lắk' in script_content:
                        print("✅ Found potential data in script")
                        # Try to extract the data
                        return self.parse_script_data(script_content)
            
            print("⚠️  Could not find chart data automatically")
            return None
            
        except Exception as e:
            print(f"❌ Error extracting data: {e}")
            return None
    
    def parse_and_save_chart_data(self, chart_data):
        """Parse chart data and save to CSV"""
        try:
            all_data = []
            
            print(f"\n📊 Processing chart data...")
            
            for region_name, data_points in chart_data.items():
                print(f"   Processing {region_name}: {len(data_points)} points")
                
                # Map region names - skip non-coffee data
                region_map = {
                    'Gia Lai': 'GiaLai',
                    'Đắk Lắk': 'DakLak',
                    'Dak Lak': 'DakLak',
                    'Đắk Nông': 'DakNong',
                    'Dak Nong': 'DakNong',
                    'Lâm Đồng': 'LamDong',
                    'Lam Dong': 'LamDong'
                }
                
                region = region_map.get(region_name)
                if not region:
                    # Skip non-coffee data (USD/VND, Giá tiêu, etc.)
                    continue
                
                for idx, point in enumerate(data_points):
                    try:
                        x_value = point.get('x', '')
                        y_value = point.get('y', 0)
                        
                        if not y_value:
                            continue
                        
                        # Parse date from x_value (timestamp in milliseconds)
                        # x_value is typically a timestamp, convert to date
                        if isinstance(x_value, (int, float)):
                            # Convert from milliseconds to seconds
                            actual_date = datetime.fromtimestamp(x_value / 1000)
                        else:
                            # If x_value is a string, try to parse it
                            try:
                                # Try parsing MM-DD format with current year
                                current_year = datetime.now().year
                                actual_date = datetime.strptime(f"{current_year}-{x_value}", '%Y-%m-%d')
                            except:
                                # Skip if we can't parse the date
                                print(f"⚠️  Could not parse date: {x_value}")
                                continue
                        
                        date_str = actual_date.strftime('%Y-%m-%d')
                        
                        all_data.append({
                            'date': date_str,
                            'region': region,
                            'price_vnd_per_kg': int(y_value),
                            'scraped_at': datetime.now().isoformat(),
                            'source': 'chart_data'
                        })
                        
                    except Exception as e:
                        continue
            
            if all_data:
                # Create DataFrame and save
                df = pd.DataFrame(all_data)
                df = df.sort_values(['date', 'region'])
                
                output_file = 'coffee_prices_historical.csv'
                df.to_csv(output_file, index=False)
                
                print(f"\n✅ Saved {len(all_data)} records to {output_file}")
                print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
                print(f"   Regions: {', '.join(df['region'].unique())}")
                print(f"\n📊 Sample data:")
                print(df.groupby('region')['price_vnd_per_kg'].agg(['min', 'max', 'mean']).round(0))
                
                # Also save as JSON
                json_file = 'coffee_prices_historical.json'
                df.to_json(json_file, orient='records', force_ascii=False, indent=2)
                print(f"✅ Also saved to {json_file}")
                
                # Save to database
                self.save_to_database(df)
                
                return df
            
        except Exception as e:
            print(f"❌ Error parsing chart data: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def save_to_database(self, df):
        """Save scraped data to MySQL database"""
        try:
            print(f"\n💾 Connecting to database...")
            connection = mysql.connector.connect(**self.db_config)
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                # Create table if not exists
                create_table_query = """
                CREATE TABLE IF NOT EXISTS daily_coffee_prices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    region VARCHAR(50) NOT NULL,
                    price_vnd_per_kg INT NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(50) DEFAULT 'chart_data',
                    UNIQUE KEY unique_date_region (date, region)
                )
                """
                cursor.execute(create_table_query)
                print(f"✅ Table 'daily_coffee_prices' ready")
                
                # Insert or update data
                insert_query = """
                INSERT INTO daily_coffee_prices (date, region, price_vnd_per_kg, scraped_at, source)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    price_vnd_per_kg = VALUES(price_vnd_per_kg),
                    scraped_at = VALUES(scraped_at),
                    source = VALUES(source)
                """
                
                # Prepare data for insertion
                data_to_insert = []
                for _, row in df.iterrows():
                    data_to_insert.append((
                        row['date'],
                        row['region'],
                        row['price_vnd_per_kg'],
                        row['scraped_at'],
                        row['source']
                    ))
                
                # Execute batch insert
                cursor.executemany(insert_query, data_to_insert)
                connection.commit()
                
                print(f"✅ Saved {cursor.rowcount} records to database")
                print(f"   Table: daily_coffee_prices")
                
                cursor.close()
                connection.close()
                
        except Error as e:
            print(f"❌ Database error: {e}")
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
    
    def parse_script_data(self, script_content):
        """Parse data from script content"""
        try:
            # Look for series array
            series_match = re.search(r'series\s*:\s*(\[.*?\])', script_content, re.DOTALL)
            if series_match:
                series_text = series_match.group(1)
                print("Found series data")
                # This would need more sophisticated parsing
                # For now, return indicator that we found something
                return {'raw': series_text[:500]}  # First 500 chars as sample
        except Exception as e:
            print(f"Error parsing script: {e}")
        return None
    
    def get_page_source_with_data(self):
        """Get page source to manually inspect"""
        try:
            self.driver.get(self.url)
            time.sleep(5)
            
            # Save page source for inspection
            page_source = self.driver.page_source
            
            output_file = 'chogia_page_source.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            print(f"✅ Page source saved to {output_file}")
            print("💡 Open this file to inspect the chart structure")
            
            # Also try to get network requests
            print("\n🌐 Network requests:")
            logs = self.driver.get_log('performance')
            for entry in logs[-20:]:  # Last 20 requests
                try:
                    log = json.loads(entry['message'])['message']
                    if 'Network.response' in log['method']:
                        url = log['params']['response']['url']
                        if 'api' in url.lower() or 'data' in url.lower() or 'price' in url.lower():
                            print(f"  📡 {url}")
                except:
                    pass
                    
        except Exception as e:
            print(f"Error: {e}")
        
        return page_source
    
    def cleanup(self):
        """Close browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("✅ Browser closed")


def generate_historical_data_from_current():
    """
    Generate sample historical data based on current prices
    This is a fallback if we can't scrape historical data
    """
    print("\n📊 Generating sample historical data (last 90 days)...")
    
    # Base prices from current scrape
    base_prices = {
        'GiaLai': 118200,
        'DakLak': 119000,
        'DakNong': 119300,
        'LamDong': 118200
    }
    
    data = []
    
    # Generate 90 days of data
    for days_ago in range(90, -1, -1):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        for region, base_price in base_prices.items():
            # Add realistic variation (+/- 5%)
            import random
            variation = random.uniform(-0.05, 0.05)
            price = int(base_price * (1 + variation))
            
            # Round to nearest 100
            price = round(price / 100) * 100
            
            data.append({
                'date': date,
                'region': region,
                'price_vnd_per_kg': price,
                'scraped_at': datetime.now().isoformat(),
                'source': 'generated'
            })
    
    # Save to CSV
    df = pd.DataFrame(data)
    df.to_csv('coffee_prices_historical_generated.csv', index=False)
    
    print(f"✅ Generated {len(data)} records")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Regions: {', '.join(df['region'].unique())}")
    print(f"   Saved to: coffee_prices_historical_generated.csv")
    
    return df


def main():
    print("="*70)
    print("🚀 Historical Coffee Price Scraper")
    print("="*70)
    
    scraper = None
    try:
        scraper = HistoricalCoffeePriceScraper()
        
        # Try to extract chart data
        chart_data = scraper.extract_chart_data()
        
        if chart_data:
            print("\n✅ Successfully extracted chart data!")
            print(json.dumps(chart_data, indent=2, ensure_ascii=False)[:500])
        else:
            print("\n⚠️  Could not automatically extract chart data")
            print("\n📝 Saving page source for manual inspection...")
            scraper.get_page_source_with_data()
            
            print("\n" + "="*70)
            print("💡 ALTERNATIVE: Generating sample historical data")
            print("="*70)
            generate_historical_data_from_current()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Falling back to generating sample data...")
        generate_historical_data_from_current()
        
    finally:
        if scraper:
            scraper.cleanup()
    
    print("\n" + "="*70)
    print("📚 MANUAL METHOD TO GET HISTORICAL DATA:")
    print("="*70)
    print("""
1. Open Chrome DevTools (F12) on https://chogia.vn/gia-ca-phe/
2. Go to Console tab
3. Run this JavaScript:

   // For Highcharts
   Highcharts.charts[0].series.forEach(s => {
       console.log(s.name);
       console.table(s.data.map(p => ({date: p.category, price: p.y})));
   });

4. Copy the data and save it
5. Or right-click on chart → "View data table" (if available)
    """)


if __name__ == "__main__":
    main()
