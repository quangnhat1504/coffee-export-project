"""
Coffee Data Synchronization Script
Syncs CSV data to MySQL database: CSV -> coffee_long (long format) -> pivot to domain tables
"""
import os
import sys
import math
from typing import List, Tuple, Optional
import pandas as pd
from sqlalchemy import create_engine, text, Engine
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path to import db_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web', 'backend'))
try:
    from db_utils import create_database_engine
except ImportError:
    create_database_engine = None

# Configure Unicode output for Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

<<<<<<< HEAD
# ===== 0) Load .env =====
# Find .env in parent directory (project root)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
=======
# ===== Load Environment Variables =====
load_dotenv(dotenv_path='../.env')
>>>>>>> origin/main
HOST = os.getenv("HOST")
PORT = os.getenv("PORT", "3306")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DB = os.getenv("DB")
CA_CERT = os.getenv("CA_CERT")

if not all([HOST, PORT, USER, PASSWORD, DB]):
    raise SystemExit("❌ Missing env vars. Set HOST, PORT, USER, PASSWORD, DB in .env")

# ===== Database Connection =====
engine: Optional[Engine] = None

if create_database_engine:
    try:
        engine = create_database_engine(
            host=HOST,
            user=USER,
            password=PASSWORD,
            port=PORT,
            database=DB,
            ca_cert=CA_CERT
        )
        print("✅ Connected to MySQL database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
else:
    # Fallback to simple connection
    url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
    try:
        if CA_CERT and CA_CERT.strip():
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                f.write(CA_CERT)
                cert_file = f.name
            
            engine = create_engine(
                url,
                connect_args={"ssl": {"ca": cert_file}},
                pool_pre_ping=True,
                pool_recycle=1800,
            )
            print("✅ Connected with SSL (fallback mode)")
        else:
            raise Exception("No SSL certificate provided")
    except Exception as e:
        print(f"⚠️  SSL connection failed ({e}), trying without SSL...")
        engine = create_engine(
            url + "?ssl_disabled=true",
            pool_pre_ping=True,
            pool_recycle=1800,
        )
        print("✅ Connected without SSL (fallback mode)")

# ===== 2) Đọc CSV =====
# Use relative paths from current script location
script_dir = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(script_dir, "Data_coffee.csv")
CSV_PATH_MT = os.path.join(script_dir, "Thi_phan_3_thi_truong_chinh.csv")

print(f"📁 Looking for CSV files in: {script_dir}")
print(f"📄 Main CSV: {CSV_PATH}")
print(f"📄 Market CSV: {CSV_PATH_MT}")

if not os.path.exists(CSV_PATH):
    raise SystemExit(f"❌ Data_coffee.csv not found at: {CSV_PATH}")
if not os.path.exists(CSV_PATH_MT):
    raise SystemExit(f"❌ Thi_phan_3_thi_truong_chinh.csv not found at: {CSV_PATH_MT}")

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# ===== 2b) Đọc CSV thị trường ('.' là thập phân) =====
mt = pd.read_csv(CSV_PATH_MT, encoding="utf-8-sig")

# Làm sạch cột
mt = mt.rename(columns=lambda c: str(c).strip())
if "Unnamed: 0" in mt.columns:
    mt = mt.drop(columns=["Unnamed: 0"])

# Bắt buộc phải có các cột sau (đúng tên trong file của bạn)
required_cols = {"Year", "Importer", "Trade Value(million_USD)", "Quantity(tons)"}
missing = required_cols - set(mt.columns)
if missing:
    raise SystemExit(f"Thi_phan_3_thi_truong_chinh.csv thiếu cột: {missing}")

# Chuẩn hoá kiểu dữ liệu
mt["Importer"] = mt["Importer"].astype(str).str.strip()
mt["Year"] = pd.to_numeric(mt["Year"], errors="coerce").astype("Int64")
mt["Trade Value(million_USD)"] = pd.to_numeric(mt["Trade Value(million_USD)"], errors="coerce")
mt["Quantity(tons)"] = pd.to_numeric(mt["Quantity(tons)"], errors="coerce")

mt = mt.dropna(subset=["Year", "Importer"]).copy()
mt["Year"] = mt["Year"].astype(int)

# Chuẩn hoá tên cột đích (mapping sang tên “đẹp” để đẩy vào DB)
mt = mt.rename(columns={
    "Trade Value(million_USD)": "trade_value_million_usd",
    "Quantity(tons)": "quantity_tons"
})[["Importer", "Year", "trade_value_million_usd", "quantity_tons"]]

# ===== 3) Melt wide -> long =====
id_col = "Hang_muc"
year_cols = [c for c in df.columns if str(c).isdigit()]
if not year_cols:
    raise SystemExit("No year columns detected in CSV header.")
long_df = df.melt(id_vars=[id_col], value_vars=year_cols, var_name="year", value_name="value")
long_df = long_df.rename(columns={id_col: "hang_muc"})

# ===== 4) Clean =====
long_df["year"]  = pd.to_numeric(long_df["year"], errors="coerce").astype("Int64")
long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
long_df = long_df.dropna(subset=["year"]).copy()
long_df["year"] = long_df["year"].astype(int)

# chuẩn hoá nhãn
long_df["hang_muc"] = long_df["hang_muc"].astype(object)          # giữ None/str
long_df = long_df[long_df["hang_muc"].notna()]
long_df["hang_muc"] = long_df["hang_muc"].map(lambda s: str(s).strip())

# loại nhãn rác
bad_labels = {"nan", "NaN", "hang_muc", "Hang_muc", ""}
long_df = long_df[~long_df["hang_muc"].isin(bad_labels)]

# loại dòng header lặp: value == year (vd 2005)
long_df = long_df[~(long_df["value"].notna() & (long_df["value"] == long_df["year"]))]

# dedup trong dataframe
long_df = long_df.drop_duplicates(subset=["hang_muc", "year"], keep="first").reset_index(drop=True)

# NaN -> None (để MySQL nhận NULL)
long_df["value"] = long_df["value"].astype(object)
long_df.loc[pd.isna(long_df["value"]), "value"] = None

# ===== 5) DDL các bảng =====
ddl_coffee_long = """
CREATE TABLE IF NOT EXISTS coffee_long (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  hang_muc VARCHAR(255) NOT NULL,
  year INT NOT NULL,
  value DECIMAL(18,4) NULL,
  UNIQUE KEY uniq_hangmuc_year (hang_muc, year)
) CHARACTER SET utf8mb4;
"""

ddl_weather = """
CREATE TABLE IF NOT EXISTS weather (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  temperature DECIMAL(5,2) NULL,
  humidity    DECIMAL(5,2) NULL,
  rain        DECIMAL(10,1) NULL,
  UNIQUE KEY uq_weather_year (year)
) CHARACTER SET utf8mb4;
"""

ddl_production = """
CREATE TABLE IF NOT EXISTS production (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  area_thousand_ha DECIMAL(10,1) NULL,
  output_tons      DECIMAL(14,2) NULL,
  export_tons      DECIMAL(14,2) NULL,
  UNIQUE KEY uq_prod_year (year)
) CHARACTER SET utf8mb4;
"""

ddl_export = """
CREATE TABLE IF NOT EXISTS coffee_export (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  export_value_million_usd        DECIMAL(16,2) NULL,
  price_world_usd_per_ton DECIMAL(12,2) NULL,
  price_vn_usd_per_ton    DECIMAL(12,2) NULL,
  UNIQUE KEY uq_trade_year (year)
) CHARACTER SET utf8mb4;
"""

ddl_market_trade = """
CREATE TABLE IF NOT EXISTS market_trade (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  importer VARCHAR(100) NOT NULL,
  year INT NOT NULL,
  trade_value_million_usd DECIMAL(16,2) NULL,
  quantity_tons           DECIMAL(16,2) NULL,
  UNIQUE KEY uq_importer_year (importer, year)
) CHARACTER SET utf8mb4;
"""

# ===== 6) UPSERT coffee_long =====
upsert_sql = """
INSERT INTO coffee_long (hang_muc, year, value)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE value = VALUES(value);
"""

def none_if_nan(v: Optional[float]) -> Optional[float]:
    """Convert NaN values to None for database insertion"""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v

# Prepare rows for batch insertion
rows: List[Tuple[str, int, Optional[float]]] = [
    (str(hm), int(y), none_if_nan(v))
    for hm, y, v in long_df[["hang_muc", "year", "value"]].itertuples(index=False, name=None)
]

# ===== Main Data Sync Process =====
with engine.begin() as conn:
    print("🗑️  Dropping existing tables (if any)...")
    # Drop tables if they exist (for fresh start)
    conn.execute(text("DROP TABLE IF EXISTS weather"))
    conn.execute(text("DROP TABLE IF EXISTS production"))
    conn.execute(text("DROP TABLE IF EXISTS coffee_export"))
    conn.execute(text("DROP TABLE IF EXISTS market_trade"))
    conn.execute(text("DROP TABLE IF EXISTS coffee_long"))

    print("📋 Creating tables...")
    # Create tables
    conn.execute(text(ddl_coffee_long))
    conn.execute(text(ddl_weather))
    conn.execute(text(ddl_production))
    conn.execute(text(ddl_export))
    conn.execute(text(ddl_market_trade))
    print("✅ Tables created successfully")

    # Upsert coffee_long (using raw cursor for fast executemany)
    if rows:
        print(f"📥 Inserting {len(rows)} records into coffee_long in batches...")
        raw = conn.connection
        batch_size = 1000  # Process in batches for better performance
        total_batches = (len(rows) + batch_size - 1) // batch_size
        
        with raw.cursor() as cur:
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                cur.executemany(upsert_sql, batch)
                batch_num = (i // batch_size) + 1
                if batch_num % 5 == 0 or batch_num == total_batches:
                    print(f"  Progress: {batch_num}/{total_batches} batches completed")
        print("✅ coffee_long data inserted")

    # ===== Pivot to Domain Tables =====
    print("🔄 Pivoting data to domain tables...")
    
    # a) weather
    print("  → Processing weather data...")
    conn.execute(text("""
        INSERT INTO weather (year, temperature, humidity, rain)
        SELECT y.year,
               MAX(CASE WHEN c.hang_muc LIKE 'Nhiet_do_trung_binh%' THEN c.value END) AS temperature,
               MAX(CASE WHEN c.hang_muc LIKE 'Do_am_trung_binh%'   THEN c.value END) AS humidity,
               MAX(CASE WHEN c.hang_muc LIKE 'Tong_luong_mua%'     THEN c.value END) AS rain
        FROM (SELECT DISTINCT year FROM coffee_long) y
        LEFT JOIN coffee_long c ON c.year = y.year
        GROUP BY y.year
        ON DUPLICATE KEY UPDATE
          temperature = VALUES(temperature),
          humidity    = VALUES(humidity),
          rain        = VALUES(rain);
    """))

    # b) production
    print("  → Processing production data...")
    conn.execute(text("""
        INSERT INTO production (year, area_thousand_ha, output_tons, export_tons)
        SELECT y.year,
               MAX(CASE WHEN c.hang_muc LIKE 'Area (Thousand ha)%'         THEN c.value END) AS area_thousand_ha,
               MAX(CASE WHEN c.hang_muc LIKE 'San luong ca phe san xuat%'  THEN c.value END) AS output_tons,
               MAX(CASE WHEN c.hang_muc LIKE 'San luong ca phe xuat khau%' THEN c.value END) AS export_tons
        FROM (SELECT DISTINCT year FROM coffee_long) y
        LEFT JOIN coffee_long c ON c.year = y.year
        GROUP BY y.year
        ON DUPLICATE KEY UPDATE
          area_thousand_ha = VALUES(area_thousand_ha),
          output_tons      = VALUES(output_tons),
          export_tons      = VALUES(export_tons);
    """))

    # c) coffee_export
    print("  → Processing export data...")
    conn.execute(text("""
        INSERT INTO coffee_export (year, export_value_million_usd, price_world_usd_per_ton, price_vn_usd_per_ton)
        SELECT y.year,
               MAX(CASE 
                     WHEN c.hang_muc LIKE 'Kim_Ngach(millionUSD)%'
                          OR c.hang_muc LIKE 'Kim Ngach%'
                          OR c.hang_muc LIKE 'Kim_Ngach%'
                     THEN c.value 
                   END) AS export_value_million_usd,
               MAX(CASE WHEN c.hang_muc LIKE 'coffee_price_usd_per_ton(world)%'   THEN c.value END) AS price_world_usd_per_ton,
               MAX(CASE WHEN c.hang_muc LIKE 'coffee_price_usd_per_ton(vietnam)%' THEN c.value END) AS price_vn_usd_per_ton
        FROM (SELECT DISTINCT year FROM coffee_long) y
        LEFT JOIN coffee_long c ON c.year = y.year
        GROUP BY y.year
        ON DUPLICATE KEY UPDATE
          export_value_million_usd = VALUES(export_value_million_usd),
          price_world_usd_per_ton  = VALUES(price_world_usd_per_ton),
          price_vn_usd_per_ton     = VALUES(price_vn_usd_per_ton);
    """))

    # d) market_trade: upsert from market trade CSV
    print("  → Processing market trade data...")
    upsert_mt_sql = """
        INSERT INTO market_trade
          (importer, year, trade_value_million_usd, quantity_tons)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          trade_value_million_usd = VALUES(trade_value_million_usd),
          quantity_tons           = VALUES(quantity_tons);
    """
    mt_rows: List[Tuple[str, int, Optional[float], Optional[float]]] = [
        (
            str(row.Importer),
            int(row.Year),
            None if pd.isna(row.trade_value_million_usd) else float(row.trade_value_million_usd),
            None if pd.isna(row.quantity_tons) else float(row.quantity_tons)
        )
        for row in mt.itertuples(index=False)
    ]
    if mt_rows:
        raw3 = conn.connection
        batch_size = 500  # Batch size for market trade data
        total_batches = (len(mt_rows) + batch_size - 1) // batch_size
        
        with raw3.cursor() as cur:
            for i in range(0, len(mt_rows), batch_size):
                batch = mt_rows[i:i + batch_size]
                cur.executemany(upsert_mt_sql, batch)
        print(f"  ✅ Inserted {len(mt_rows)} market trade records")


    # ===== Final Report =====
    print("\n📊 Data Sync Summary:")
    print("=" * 60)
    
    total_long = conn.execute(text("SELECT COUNT(*) FROM coffee_long")).scalar()
    total_w = conn.execute(text("SELECT COUNT(*) FROM weather")).scalar()
    total_p = conn.execute(text("SELECT COUNT(*) FROM production")).scalar()
    total_e = conn.execute(text("SELECT COUNT(*) FROM coffee_export")).scalar()
    total_mt = conn.execute(text("SELECT COUNT(*) FROM market_trade")).scalar()
    
    print(f"✅ coffee_long:     {total_long:,} rows")
    print(f"✅ weather:         {total_w:,} rows")
    print(f"✅ production:      {total_p:,} rows")
    print(f"✅ coffee_export:   {total_e:,} rows")
    print(f"✅ market_trade:    {total_mt:,} rows")
    
    print("\n📋 Sample Data:")
    print("\nWeather (first 3 records):")
    for r in conn.execute(text("SELECT * FROM weather ORDER BY year LIMIT 3")):
        print(f"  {r}")
    
    print("\nMarket Trade (first 3 records):")
    for r in conn.execute(text("SELECT * FROM market_trade ORDER BY year, importer LIMIT 3")):
        print(f"  {r}")
    
    print("\n" + "=" * 60)
    print("✅ Data synchronization completed successfully!")


